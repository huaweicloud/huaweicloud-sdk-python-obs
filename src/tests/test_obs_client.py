#!/usr/bin/python
# -*- coding:utf-8 -*-
# Copyright 2019 Huawei Technologies Co.,Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations under the License.

import io
import os
import random
import time
from datetime import datetime
import sys, os
# 添加当前目录到 Python 路径，确保可以导入 conftest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pytest

import conftest
from obs import CreateBucketHeader, GetObjectHeader, ObsClient, UploadFileHeader, \
    Expiration, NoncurrentVersionExpiration, AbortIncompleteMultipartUpload, DateTime, \
    Rule, Lifecycle, PutObjectHeader, AppendObjectHeader, AppendObjectContent, util, CompleteMultipartUploadRequest, \
    CompletePart, CopyObjectHeader, SetObjectMetadataHeader, HeadPermission

from conftest import test_config

from obs.const import IS_PYTHON2

if IS_PYTHON2:
    chr = unichr


class TestOBSClient(object):
    def get_client(self):
        client_type = "OBSClient"
        path_style = True if test_config["auth_type"] == "v2" else False
        uploadClient = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                                 server=test_config["endpoint"],
                                 is_signature_negotiation=False, path_style=path_style)
        downloadClient = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                                   server=test_config["endpoint"],
                                   is_signature_negotiation=False, path_style=path_style)
        return client_type, uploadClient, downloadClient

    def delete_bucket(self, obsClinet, bucketName):
        get_resp = obsClinet.getBucketVersioning(bucketName)
        assert get_resp.status == 200
        if get_resp.body == 'Enabled':
            resp = obsClinet.listVersions(bucketName)
            assert resp.status == 200
            for version in resp.body.versions:
                obsClinet.deleteObject(bucketName, version.key, version.versionId)
            for marker in resp.body.markers:
                obsClinet.deleteObject(bucketName, marker.key, marker.versionId)
        else:
            resp = obsClinet.listObjects(bucketName)
            assert resp.status == 200
            for content in resp.body.contents:
                obsClinet.deleteObject(bucketName, content.key)
        del_resp = obsClinet.deleteBucket(bucketName)
        assert del_resp.status == 204

    def test_create_PFS_bucket(self, delete_bucket_after_test):
        _, uploadClient, _ = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "create-pfs-001"
        delete_bucket_after_test["client"] = uploadClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)
        create_bucket_header = CreateBucketHeader(isPFS=True)
        create_result = uploadClient.createBucket(bucket_name, header=create_bucket_header,
                                                  location=test_config["location"])
        assert create_result.status == 200

        bucket_metadata = uploadClient.getBucketMetadata(bucket_name)
        assert bucket_metadata.status == 200
        assert ("fs-file-interface", 'Enabled') in bucket_metadata.header

    def test_delete_posix_folder(self):
        client_type, uploadClient, deleteClient = self.get_client()
        bucket_name = test_config["bucketName"]
        file1 = test_config["path_prefix"] + "file-001"
        file2 = test_config["path_prefix"] + "file-002"
        upload_result1 = uploadClient.putContent(bucket_name, file1, content='Hello OBS')
        assert upload_result1.status == 200
        upload_result2 = uploadClient.putContent(bucket_name, file2, content='Hello OBS')
        assert upload_result2.status == 200
        delete_list, error_list = deleteClient.deletePosixFloder(bucket_name, test_config["path_prefix"])
        assert len(delete_list) == 3
        assert len(error_list) == 0

    def test_create_object_bucket(self, delete_bucket_after_test):
        _, uploadClient, _ = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "create-pfs-002"
        delete_bucket_after_test["client"] = uploadClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)
        create_bucket_header = CreateBucketHeader(isPFS=False)
        create_result = uploadClient.createBucket(bucket_name, header=create_bucket_header,
                                                  location=test_config["location"])
        assert create_result.status == 200

        bucket_metadata = uploadClient.getBucketMetadata(bucket_name)
        assert bucket_metadata.status == 200
        assert ("fs-file-interface", 'Enabled') not in bucket_metadata.header

        list_bucket_result = uploadClient.listBuckets(bucketType="OBJECT")
        assert list_bucket_result.status == 200
        all_object_buckets = [i["name"] for i in list_bucket_result.body["buckets"]]
        assert bucket_name in all_object_buckets

    def test_list_buckets(self, delete_bucket_after_test):
        _, uploadClient, _ = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "list-pfs-001"
        delete_bucket_after_test["client"] = uploadClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)
        create_bucket_header = CreateBucketHeader(isPFS=True)
        create_result = uploadClient.createBucket(bucket_name, header=create_bucket_header,
                                                  location=test_config["location"])
        assert create_result.status == 200
        bucket_name2 = test_config["bucket_prefix"] + "list-pfs-002"
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name2)
        create_result2 = uploadClient.createBucket(bucket_name2, location=test_config["location"])
        assert create_result2.status == 200

        list_bucket_result = uploadClient.listBuckets(bucketType="POSIX")
        assert list_bucket_result.status == 200
        all_pfs_buckets = [i["name"] for i in list_bucket_result.body["buckets"]]
        assert bucket_name in all_pfs_buckets
        assert bucket_name2 not in all_pfs_buckets

        list_bucket_result2 = uploadClient.listBuckets()
        all_buckets = [i["name"] for i in list_bucket_result2.body["buckets"]]
        assert bucket_name in all_buckets
        assert bucket_name2 in all_buckets

        list_bucket_result3 = uploadClient.listBuckets(bucketType="OBJECT")
        assert list_bucket_result3.status == 200
        all_object_buckets = [i["name"] for i in list_bucket_result3.body["buckets"]]
        assert bucket_name not in all_object_buckets
        assert bucket_name2 in all_object_buckets

        list_bucket_result4 = uploadClient.listBuckets(bucketType="Wrong_Value")
        all_buckets2 = [i["name"] for i in list_bucket_result4.body["buckets"]]
        assert bucket_name in all_buckets2
        assert bucket_name2 in all_buckets2

    def test_uploadFile_and_getObject_to_file(self, gen_test_file):
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = client_type + "test_uploadFile_and_getObject_to_file_" + gen_test_file
        upload_result = uploadClient.uploadFile(test_config["bucketName"], object_name,
                                                test_config["path_prefix"] + gen_test_file, taskNum=10)
        assert upload_result.status == 200
        download_result = downloadClient.getObject(test_config["bucketName"], object_name,
                                                   downloadPath=test_config["path_prefix"] + object_name)
        assert download_result.status == 200
        assert conftest.compare_sha256(test_config["path_prefix"] + gen_test_file,
                                       test_config["path_prefix"] + object_name)
        os.remove(test_config["path_prefix"] + object_name)
        uploadClient.deleteObject(test_config["bucketName"], object_name)

    def test_putFile_and_downloadFile(self, gen_test_file):
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = client_type + "test_putFile_and_downloadFile_" + gen_test_file
        upload_result = uploadClient.putFile(test_config["bucketName"], object_name,
                                             test_config["path_prefix"] + gen_test_file)
        assert upload_result.status == 200
        assert conftest.download_and_check(downloadClient, test_config["bucketName"], object_name,
                                           test_config["path_prefix"] + object_name,
                                           test_config["path_prefix"] + gen_test_file)

    def test_putContent_with_file_stream(self, gen_test_file):
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = client_type + "test_putContent_with_file_stream" + gen_test_file
        upload_result = uploadClient.putContent(test_config["bucketName"], object_name,
                                                open(test_config["path_prefix"] + gen_test_file, "rb"))
        assert upload_result.status == 200
        assert conftest.download_and_check(downloadClient, test_config["bucketName"], object_name,
                                           test_config["path_prefix"] + object_name,
                                           test_config["path_prefix"] + gen_test_file)

    def test_putContent_with_network_stream(self, gen_test_file):
        client_type, uploadClient, downloadClient = self.get_client()
        object_for_upload = ""
        try:
            object_for_upload = client_type + "test_putContent_with_stream_from_getObject_upload_" + gen_test_file
            object_for_verify = client_type + "test_putContent_with_stream_from_getObject_verify_" + gen_test_file
            upload_result = uploadClient.uploadFile(test_config["bucketName"], object_for_upload,
                                                    test_config["path_prefix"] + gen_test_file, taskNum=10)
            assert upload_result.status == 200
            resp = downloadClient.getObject(test_config["bucketName"], object_for_upload, loadStreamInMemory=False)
            upload_result2 = uploadClient.putContent(test_config["bucketName"], object_for_verify, resp.body.response)

            assert upload_result2.status == 200
            assert conftest.download_and_check(downloadClient, test_config["bucketName"], object_for_verify,
                                               test_config["path_prefix"] + object_for_verify,
                                               test_config["path_prefix"] + gen_test_file)
        finally:
            uploadClient.deleteObject(test_config["bucketName"], object_for_upload)

    def test_getObject_to_memory(self, gen_test_file):
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = client_type + "test_uploadFile_and_getObject_to_file_" + gen_test_file
        upload_result = uploadClient.uploadFile(test_config["bucketName"], object_name,
                                                test_config["path_prefix"] + gen_test_file, taskNum=10)
        assert upload_result.status == 200
        resp = downloadClient.getObject(test_config["bucketName"], object_name, loadStreamInMemory=True)
        bytes_io = io.BytesIO(resp.body.buffer)
        assert conftest.compare_sha256(test_config["path_prefix"] + gen_test_file,
                                       bytes_io, False)
        uploadClient.deleteObject(test_config["bucketName"], object_name)

    def test_putContent_with_string_and_range_get_object(self):
        client_type, uploadClient, downloadClient = self.get_client()
        test_string = "".join(chr(random.randint(10000, 40000)) for _ in range(341))
        object_name = client_type + "test_range_get_object"
        header = GetObjectHeader()
        header.range = "60-119"
        upload_result = uploadClient.putContent(test_config["bucketName"], object_name, test_string)
        assert upload_result.status == 200
        resp = downloadClient.getObject(test_config["bucketName"], object_name, headers=header, loadStreamInMemory=True)
        assert resp.body.buffer == test_string[20:40].encode("UTF-8")
        uploadClient.deleteObject(test_config["bucketName"], object_name)

    def test_appendObject(self):
        pass

    def test_initiateMultipartUpload_and_uploadPart_and_copyPart(self):
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = client_type + "test_uploadPart"
        init_result = uploadClient.initiateMultipartUpload(test_config["bucketName"], object_name)
        assert init_result.status == 200
        assert "uploadId" in init_result.body
        upload_result = uploadClient.uploadPart(test_config["bucketName"], object_name, 1,
                                                init_result.body["uploadId"],
                                                object="test_initiateMultipartUpload_and_uploadPart")
        assert upload_result.status == 200
        # 生成一个大于 100k 的对象
        test_string = "".join(chr(random.randint(10000, 40000)) for _ in range(342))
        test_100k = "".join([test_string] * 100)
        uploadClient.putContent(test_config["bucketName"], "test_copyPart", test_100k)
        uploadClient.copyPart(test_config["bucketName"], object_name, 2, init_result.body["uploadId"], "test_copyPart")
        uploadClient.abortMultipartUpload(test_config["bucketName"], object_name, init_result.body["uploadId"])

    def test_uploadFile_part_size_less_than_100k(self):
        pass

    def test_uploadFile_part_num_more_than_10000(self):
        conftest.gen_random_file("test_uploadFile_part_num_more_than_10000", 1024 * 1024)
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = "test_uploadFile_part_num_more_than_10000"
        upload_result = uploadClient.uploadFile(test_config["bucketName"], object_name,
                                                test_config["path_prefix"] + object_name,
                                                partSize=100 * 1024, taskNum=50)
        assert upload_result.status == 200
        object_metadata = uploadClient.getObjectMetadata(test_config["bucketName"], object_name)
        assert dict(object_metadata.header)["etag"].endswith("-10000\"")
        uploadClient.deleteObject(test_config["bucketName"], object_name)
        os.remove(test_config["path_prefix"] + object_name)

    def test_downloadFile_part_num_more_than_10000(self):
        conftest.gen_random_file("test_downloadFile_part_num_more_than_10000", 1024 * 1024)
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = "test_downloadFile_part_num_more_than_10000"
        upload_result = uploadClient.uploadFile(test_config["bucketName"], object_name,
                                                test_config["path_prefix"] + object_name, taskNum=50)
        assert upload_result.status == 200

        download_result = downloadClient.downloadFile(test_config["bucketName"], object_name,
                                                      test_config["path_prefix"]
                                                      + "test_downloadFile_part_num_more_than_10000_download",
                                                      taskNum=50)
        assert download_result.status == 200
        assert conftest.compare_sha256(test_config["path_prefix"] + object_name,
                                       test_config["path_prefix"]
                                       + "test_downloadFile_part_num_more_than_10000_download")
        uploadClient.deleteObject(test_config["bucketName"], object_name)
        os.remove(test_config["path_prefix"] + object_name)
        os.remove(test_config["path_prefix"] + "test_downloadFile_part_num_more_than_10000_download")

    def test_downloadFile_with_lastModify(self):
        has_exception = False
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = "test_downloadFile_with_lastModify"
        upload_result = uploadClient.putContent(test_config["bucketName"], object_name, "test OBS")
        assert upload_result.status == 200
        time.sleep(30)
        download_headers = GetObjectHeader()
        download_headers.if_modified_since = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        try:
            downloadClient.downloadFile(test_config["bucketName"], object_name,
                                        test_config["path_prefix"]
                                        + "test_downloadFile_with_lastModify", header=download_headers,
                                        taskNum=50)
        except Exception as e:
            has_exception = True
            assert "response from server is something wrong." in str(e)
        assert has_exception

    def test_uploadFile_with_checksum(self):
        conftest.gen_random_file("test_uploadFile_with_checksum", 1024 * 1024)
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = "test_uploadFile_with_checksum"
        upload_result = uploadClient.uploadFile(test_config["bucketName"], object_name,
                                                test_config["path_prefix"] + object_name,
                                                checkSum=True, taskNum=50, partSize=1024 * 1024)
        assert upload_result.status == 200
        object_metadata = uploadClient.getObjectMetadata(test_config["bucketName"], object_name)
        assert dict(object_metadata.header)["etag"].endswith("-1024\"")
        uploadClient.deleteObject(test_config["bucketName"], object_name)
        os.remove(test_config["path_prefix"] + object_name)

    def test_uploadFile_with_storage_type(self):
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = "test_uploadFile_with_storage_type"
        conftest.gen_random_file(object_name, 1024)
        for i in ["WARM", "COLD"]:
            upload_header = UploadFileHeader()
            upload_header.storageClass = i
            upload_result = uploadClient.uploadFile(test_config["bucketName"], object_name,
                                                    test_config["path_prefix"] + object_name, headers=upload_header,
                                                    checkSum=True, taskNum=10)
            assert upload_result.status == 200
            object_metadata = uploadClient.getObjectMetadata(test_config["bucketName"], object_name)
            if i == "WARM":
                assert dict(object_metadata.header)["storage-class"] in (i, "STANDARD_IA")
            else:
                assert dict(object_metadata.header)["storage-class"] in (i, "GLACIER")
            uploadClient.deleteObject(test_config["bucketName"], object_name)
        os.remove(test_config["path_prefix"] + object_name)

    def test_downloadFile_with_if_match(self):
        has_exception = False
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = "test_downloadFile_with_if_match"
        upload_result = uploadClient.putContent(test_config["bucketName"], object_name, "test OBS")
        assert upload_result.status == 200
        download_headers = GetObjectHeader()
        download_headers.if_match = "Wrong etag"
        try:
            downloadClient.downloadFile(test_config["bucketName"], object_name,
                                        test_config["path_prefix"]
                                        + "test_downloadFile_with_lastModify", header=download_headers,
                                        taskNum=50)
        except Exception as e:
            has_exception = True
            assert "PreconditionFailed" in str(e)
        assert has_exception

    def test_downloadFile_with_if_none_match(self):
        has_exception = False
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = "test_downloadFile_with_if_none_match"
        upload_result = uploadClient.putContent(test_config["bucketName"], object_name, "test OBS")
        assert upload_result.status == 200
        download_headers = GetObjectHeader()
        download_headers.if_none_match = '64a58230c3d4db2fe8fcb83c0f45c50b'
        try:
            downloadClient.downloadFile(test_config["bucketName"], object_name,
                                        test_config["path_prefix"]
                                        + "test_downloadFile_with_lastModify", header=download_headers,
                                        taskNum=50)
        except Exception:
            has_exception = True
        assert has_exception

    def test_downloadFile_with_wrong_version_id(self):
        has_exception = False
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = "test_downloadFile_with_wrong_version_id"
        upload_result = uploadClient.putContent(test_config["bucketName"], object_name, "test OBS")
        assert upload_result.status == 200
        try:
            downloadClient.downloadFile(test_config["bucketName"], object_name,
                                        test_config["path_prefix"]
                                        + "test_downloadFile_with_lastModify", versionId="Wrong Version ID",
                                        taskNum=50)
        except Exception:
            has_exception = True
        assert has_exception

    def test_downloadFile_with_unmodified_since(self):
        has_exception = False
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = "test_downloadFile_with_if_match"
        upload_result = uploadClient.putContent(test_config["bucketName"], object_name, "test OBS")
        assert upload_result.status == 200
        download_headers = GetObjectHeader()
        download_headers.if_unmodified_since = "Tue, 02 Jul 2018 08:28:00 GMT"
        try:
            downloadClient.downloadFile(test_config["bucketName"], object_name,
                                        test_config["path_prefix"]
                                        + "test_downloadFile_with_lastModify", header=download_headers,
                                        taskNum=50)
        except Exception as e:
            has_exception = True
            assert "PreconditionFailed" in str(e)
        assert has_exception

    def test_uploadFile_with_metadata(self):
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = "test_uploadFile_with_metadata"
        conftest.gen_random_file(object_name, 1024)
        metadata = {"content_type": "text/plain",
                    "expires": 1,
                    "meta_key1": "value1",
                    "meta_key-2": "value-2"}
        upload_result = uploadClient.uploadFile(test_config["bucketName"], object_name,
                                                test_config["path_prefix"] + object_name, metadata=metadata,
                                                checkSum=True, taskNum=10)
        assert upload_result.status == 200
        object_metadata = uploadClient.getObjectMetadata(test_config["bucketName"], object_name)
        meta_dict = dict(object_metadata.header)
        assert meta_dict["content_type"] == "text/plain"
        assert meta_dict["expires"] == '1'
        assert meta_dict["meta_key1"] == "value1"
        assert meta_dict["meta_key-2"] == "value-2"

    def test_putFile_with_content_type(self):
        # 测试使用putFile上传文件夹content-Type是否前后一致
        client_type, uploadClient, downloadClient = self.get_client()
        object_list = ['test.pdf', 'test.png', 'test.txt']
        old_content_list = ['application/pdf', 'image/png', 'text/plain']
        folder_name = "test_putFile_with_content_type"
        folder = test_config["path_prefix"] + folder_name
        if not os.path.exists(folder):
            os.makedirs(folder)
        for f in object_list:
            object_name = folder_name + '/' + f
            conftest.gen_random_file(object_name, 1024)

        put_result = uploadClient.putFile(test_config["bucketName"], folder_name, folder)
        for res in put_result:
            assert res[1].status == 200
            object_metadata = uploadClient.getObjectMetadata(test_config["bucketName"], res[0])
            assert object_metadata.body.contentType in old_content_list

    def test_setBucketLifecycle_and_getBucketLifecycle_success(self):
        client_type, bucketLifecycleClient, obsClient = self.get_client()
        rule1 = Rule(id='rule1', prefix='prefix1', status='Enabled', expiration=Expiration(days=60),
                     noncurrentVersionExpiration=NoncurrentVersionExpiration(10))
        rule2 = Rule(id='rule2', prefix='prefix2', status='Enabled', expiration=Expiration(date=DateTime(2023, 12, 31)),
                     abortIncompleteMultipartUpload=AbortIncompleteMultipartUpload(10))
        lifecycle = Lifecycle(rule=[rule1, rule2])
        set_rul_result = bucketLifecycleClient.setBucketLifecycle(test_config["bucketName"], lifecycle)
        assert set_rul_result.status == 200
        get_rul_result = bucketLifecycleClient.getBucketLifecycle(test_config["bucketName"])
        assert get_rul_result.status == 200
        assert get_rul_result.body.lifecycleConfig.rule[1].abortIncompleteMultipartUpload.daysAfterInitiation == 10

    def test_setAccessLabel_success(self):
        client_type, accessLabelClient, obsClient = self.get_client()
        accessLabelList = ['role_label_01', 'role_label_02']
        obsClient.putContent('accesslabel-posix-bucket', 'dir1/')
        set_al_result = accessLabelClient.setAccessLabel('accesslabel-posix-bucket', 'dir1', accessLabelList)
        assert set_al_result.status == 204
        obsClient.deleteObject('accesslabel-posix-bucket', 'dir1/')

    def test_setAccessLabel_fail(self):
        client_type, accessLabelClient, obsClient = self.get_client()
        obsClient.putContent('accesslabel-posix-bucket', 'dir1/')
        obsClient.putContent('accesslabel-posix-bucket', 'file1', content='123')
        set_al_result1 = accessLabelClient.setAccessLabel('accesslabel-posix-bucket', 'dir1', ['role-label-01'])
        assert set_al_result1.status == 400
        set_al_result2 = accessLabelClient.setAccessLabel('accesslabel-posix-bucket', 'dir1',
                                                          ['abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ'])
        assert set_al_result2.status == 400
        set_al_result3 = accessLabelClient.setAccessLabel('accesslabel-posix-bucket', 'dir1',
                                                          ["role_label_" + str(i + 1) for i in range(513)])
        assert set_al_result3.status == 405
        set_al_result4 = accessLabelClient.setAccessLabel('accesslabel-posix-bucket', 'file1',
                                                          ['role_label_01', 'role_label_02'])
        assert set_al_result4.status == 405
        obsClient.deleteObject('accesslabel-posix-bucket', 'dir1/')
        obsClient.deleteObject('accesslabel-posix-bucket', 'file1')

    def test_getAccessLabel_success(self):
        client_type, accessLabelClient, obsClient = self.get_client()
        obsClient.putContent('accesslabel-posix-bucket', 'dir1/')
        obsClient.putContent('accesslabel-posix-bucket', 'dir2/')
        obsClient.putContent('accesslabel-posix-bucket', 'dir3/')
        obsClient.putContent('accesslabel-posix-bucket', 'dir4/')
        accessLabelClient.setAccessLabel('accesslabel-posix-bucket', 'dir1', ['role_label_01', 'role_label_02'])
        get_al_result1 = accessLabelClient.getAccessLabel('accesslabel-posix-bucket', 'dir1')
        assert get_al_result1.status == 200
        assert get_al_result1.body['accesslabel'] == ['role_label_01', 'role_label_02']
        accessLabelClient.setAccessLabel('accesslabel-posix-bucket', 'dir2',
                                         ['abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'])
        get_al_result2 = accessLabelClient.getAccessLabel('accesslabel-posix-bucket', 'dir2')
        assert get_al_result2.status == 200
        assert get_al_result2.body['accesslabel'] == ['abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ']
        accessLabelClient.setAccessLabel('accesslabel-posix-bucket', 'dir3',
                                         ["role_label_" + str(i + 1) for i in range(512)])
        get_al_result3 = accessLabelClient.getAccessLabel('accesslabel-posix-bucket', 'dir3')
        assert get_al_result3.status == 200
        assert get_al_result3.body['accesslabel'] == ["role_label_" + str(i + 1) for i in range(512)]
        accessLabelClient.setAccessLabel('accesslabel-posix-bucket', 'dir4',
                                         ["abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVW" + str(i + 1) for i in
                                          range(512)])
        get_al_result4 = accessLabelClient.getAccessLabel('accesslabel-posix-bucket', 'dir4')
        assert get_al_result4.status == 200
        assert get_al_result4.body['accesslabel'] == ["abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVW" + str(i + 1)
                                                      for
                                                      i in range(512)]
        obsClient.deleteObject('accesslabel-posix-bucket', 'dir1/')
        obsClient.deleteObject('accesslabel-posix-bucket', 'dir2/')
        obsClient.deleteObject('accesslabel-posix-bucket', 'dir3/')
        obsClient.deleteObject('accesslabel-posix-bucket', 'dir4/')

    def test_getAccessLabel_fail(self):
        client_type, accessLabelClient, obsClient = self.get_client()
        obsClient.putContent('accesslabel-posix-bucket', 'dir1/')
        get_al_result = accessLabelClient.getAccessLabel('accesslabel-posix-bucket', 'dir1')
        assert get_al_result.status == 404
        obsClient.deleteObject('accesslabel-posix-bucket', 'dir1/')

    def test_deleteAccessLabel_success(self):
        client_type, accessLabelClient, obsClient = self.get_client()
        obsClient.putContent('accesslabel-posix-bucket', 'dir1/')
        obsClient.putContent('accesslabel-posix-bucket', 'dir2/')
        accessLabelClient.setAccessLabel('accesslabel-posix-bucket', 'dir1', ['role_label_01', 'role_label_02'])
        del_al_result1 = accessLabelClient.deleteAccessLabel('accesslabel-posix-bucket', 'dir1')
        del_al_result2 = accessLabelClient.deleteAccessLabel('accesslabel-posix-bucket', 'dir2')
        del_al_result3 = accessLabelClient.deleteAccessLabel('accesslabel-posix-bucket', 'dir3')
        assert del_al_result1.status == 204
        assert del_al_result2.status == 204
        assert del_al_result3.status == 204
        obsClient.deleteObject('accesslabel-posix-bucket', 'dir1/')
        obsClient.deleteObject('accesslabel-posix-bucket', 'dir2/')

    def test_deleteAccessLabel_fail(self):
        client_type, accessLabelClient, obsClient = self.get_client()
        obsClient.putContent('accesslabel-posix-bucket', 'file1', content='123')
        del_al_result1 = accessLabelClient.deleteAccessLabel('accesslabel-posix-bucket', 'file1')
        assert del_al_result1.status == 405
        obsClient.deleteObject('accesslabel-posix-bucket', 'file1')

    def test_putObject_with_crc64(self):
        client_type, crc64Client, obsClient = self.get_client()
        object_name = "test_crc64_object"
        conftest.gen_random_file(object_name, 1024)
        crc64 = util.calculate_file_crc64(test_config["path_prefix"] + object_name)
        headers = PutObjectHeader()
        headers.isAttachCrc64 = True
        put_result = crc64Client.putFile(test_config["bucketName"], object_name,
                                         test_config["path_prefix"] + object_name,
                                         headers=headers)
        assert put_result.status == 200
        get_result = crc64Client.getObject(test_config["bucketName"], object_name)
        assert int(get_result.body.crc64) == crc64
        wrong_crc64 = 123456789
        headers.crc64 = wrong_crc64
        wrong_crc64_result = crc64Client.putFile(test_config["bucketName"], object_name,
                                                 test_config["path_prefix"] + object_name, headers=headers)
        assert wrong_crc64_result.status == 400
        obsClient.deleteObject(test_config["bucketName"], object_name)

    def test_putEmptyObject_with_crc64(self):
        client_type, crc64Client, obsClient = self.get_client()
        object_name = "test_empty_crc64_object"
        content = ""
        headers = PutObjectHeader()
        headers.isAttachCrc64 = True
        put_result = crc64Client.putContent(test_config["bucketName"], object_name, content,
                                            headers=headers)
        assert put_result.status == 200
        get_result = crc64Client.getObject(test_config["bucketName"], object_name)
        assert get_result.body.crc64 == '0'
        obsClient.deleteObject(test_config["bucketName"], object_name)

    def test_putObject_to_posixBucket_with_crc64(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucketName = 'accesslabel-posix-bucket'
        object_name = "test_crc64_object"
        conftest.gen_random_file(object_name, 1024)
        headers = PutObjectHeader()
        headers.isAttachCrc64 = True
        put_result = crc64Client.putFile(bucketName, object_name, test_config["path_prefix"] + object_name,
                                         headers=headers)
        assert put_result.status == 405

    def test_uploadPart_with_crc64(self):
        client_type, crc64Client, obsClient = self.get_client()
        object_name = "test_crc64_object"
        conftest.gen_random_file(object_name, 1024)
        crc64 = util.calculate_file_crc64(test_config["path_prefix"] + object_name)

        init_result = crc64Client.initiateMultipartUpload(test_config["bucketName"], object_name)
        uploadId = init_result.body.uploadId
        wrong_crc64_result = crc64Client.uploadPart(test_config["bucketName"], object_name, 1, uploadId,
                                                    test_config["path_prefix"] + object_name, True, 1024 * 1024,
                                                    crc64=123456789)
        assert wrong_crc64_result.status == 400

        put_result = crc64Client.uploadPart(test_config["bucketName"], object_name, 1, uploadId,
                                            test_config["path_prefix"] + object_name, True, 1024 * 1024,
                                            isAttachCrc64=True)
        assert put_result.status == 200
        part1 = CompletePart(partNum=1, etag=put_result.body.etag, crc64=put_result.body.crc64, size=1024 * 1024)
        completeMultipartUploadRequest = CompleteMultipartUploadRequest(parts=[part1])
        complete_result = crc64Client.completeMultipartUpload(test_config["bucketName"], object_name, uploadId,
                                                              completeMultipartUploadRequest, isAttachCrc64=True)
        assert int(complete_result.body.crc64) == crc64
        get_result = crc64Client.getObject(test_config["bucketName"], object_name)
        assert int(get_result.body.crc64) == crc64
        obsClient.deleteObject(test_config["bucketName"], object_name)

    def test_appendObject_with_crc64(self):
        client_type, crc64Client, obsClient = self.get_client()
        object_name = "test_crc64_object"
        object_name2 = "test_crc64_object2"
        headers = AppendObjectHeader()
        headers.isAttachCrc64 = True
        content = AppendObjectContent()
        content.content = b'Hello OBS'
        content.position = 0
        crc64 = util.calculate_content_crc64(content.content)
        put_result = crc64Client.appendObject(test_config["bucketName"], object_name,
                                              content, headers=headers)
        assert put_result.status == 200
        get_result = crc64Client.getObject(test_config["bucketName"], object_name)
        assert int(get_result.body.crc64) == crc64
        wrong_crc64 = 123456789
        headers.crc64 = wrong_crc64
        wrong_crc64_result = crc64Client.appendObject(test_config["bucketName"], object_name2,
                                                      content, headers=headers)
        assert wrong_crc64_result.status == 400
        obsClient.deleteObject(test_config["bucketName"], object_name)

    def test_getObjectMetadata_crc64(self):
        client_type, crc64Client, obsClient = self.get_client()
        object_name = "test_crc64_object"
        conftest.gen_random_file(object_name, 1024)
        crc64 = util.calculate_file_crc64(test_config["path_prefix"] + object_name)
        headers = PutObjectHeader()
        headers.isAttachCrc64 = True
        put_result = crc64Client.putFile(test_config["bucketName"], object_name,
                                         test_config["path_prefix"] + object_name, headers=headers)
        assert put_result.status == 200
        get_result = crc64Client.getObjectMetadata(test_config["bucketName"], object_name)
        assert int(get_result.body.crc64) == crc64

        obsClient.deleteObject(test_config["bucketName"], object_name)

    def test_getRangeObject_crc64(self):
        client_type, crc64Client, obsClient = self.get_client()
        object_name = "test_crc64_object"
        conftest.gen_random_file(object_name, 1024)
        crc64 = util.calculate_file_crc64(test_config["path_prefix"] + object_name)
        headers = PutObjectHeader()
        headers.isAttachCrc64 = True
        put_result = crc64Client.putFile(test_config["bucketName"], object_name,
                                         test_config["path_prefix"] + object_name, headers=headers)
        assert put_result.status == 200
        get_headers = GetObjectHeader()
        get_headers.range = '0-512'
        get_result = crc64Client.getObject(test_config["bucketName"], object_name, headers=get_headers)
        assert int(get_result.body.crc64) == crc64

        obsClient.deleteObject(test_config["bucketName"], object_name)

    def test_uploadFile_with_crc64(self):
        client_type, crc64Client, obsClient = self.get_client()
        object_name = "test_crc64_object"
        conftest.gen_random_file(object_name, 15 * 1024)
        crc64 = util.calculate_file_crc64(test_config["path_prefix"] + object_name)
        put_result = obsClient.uploadFile(test_config["bucketName"], object_name,
                                          test_config["path_prefix"] + object_name, 5 * 1024 * 1024, 2, True,
                                          isAttachCrc64=True)
        assert put_result.status == 200
        get_result = crc64Client.getObject(test_config["bucketName"], object_name)
        assert int(get_result.body.crc64) == crc64
        obsClient.deleteObject(test_config["bucketName"], object_name)

    def test_createBucket_with_intelligent_tiering(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-intelligent-tiering-bucket-sdk"
        header = CreateBucketHeader(storageClass='INTELLIGENT_TIERING')
        result = obsClient.createBucket(bucket_name, header=header)
        assert result.status == 200
        get_result = obsClient.getBucketMetadata(bucket_name)
        assert get_result.body.storageClass == 'INTELLIGENT_TIERING'
        self.delete_bucket(obsClient, bucket_name)

    def test_setBucketStoragePolicy_with_intelligent_tiering(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-set-bucket-storage-policy-sdk"
        header = CreateBucketHeader(storageClass='STANDARD')
        result = obsClient.createBucket(bucket_name, header=header)
        assert result.status == 200
        put_result = obsClient.putContent(bucket_name, 'test_obj1', 'Hello OBS')
        assert put_result.status == 200
        get_result = obsClient.getObjectMetadata(bucket_name, 'test_obj1')
        assert get_result.body.storageClass == None
        set_resp = obsClient.setBucketStoragePolicy(bucket_name, 'INTELLIGENT_TIERING')
        assert set_resp.status == 200
        put_result = obsClient.putContent(bucket_name, 'test_obj1', 'Hello OBS')
        assert put_result.status == 200
        get_result2 = obsClient.getObject(bucket_name, 'test_obj1')
        assert get_result2.body.storageClass == 'INTELLIGENT_TIERING'
        self.delete_bucket(obsClient, bucket_name)

    def test_putObject_with_intelligent_tiering(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-set-bucket-storage-policy-sdk"
        object_name = 'test_obj1'
        # 标准桶上传智能分级对象
        header = CreateBucketHeader(storageClass='STANDARD')
        cre_result1 = obsClient.createBucket(bucket_name, header=header)
        assert cre_result1.status == 200
        put_result1 = obsClient.putContent(bucket_name, object_name, 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='INTELLIGENT_TIERING'))
        assert put_result1.status == 200
        get_result1 = obsClient.getObject(bucket_name, object_name)
        assert get_result1.body.storageClass == 'INTELLIGENT_TIERING'
        self.delete_bucket(obsClient, bucket_name)
        # 温桶上传智能分级对象
        header = CreateBucketHeader(storageClass='WARM')
        cre_result2 = obsClient.createBucket(bucket_name, header=header)
        assert cre_result2.status == 200
        put_result2 = obsClient.putContent(bucket_name, object_name, 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='INTELLIGENT_TIERING'))
        assert put_result2.status == 200
        get_result2 = obsClient.getObject(bucket_name, object_name)
        assert get_result2.body.storageClass == 'INTELLIGENT_TIERING'
        self.delete_bucket(obsClient, bucket_name)
        # 冷桶上传智能分级对象
        header = CreateBucketHeader(storageClass='COLD')
        cre_result3 = obsClient.createBucket(bucket_name, header=header)
        assert cre_result3.status == 200
        put_result3 = obsClient.putContent(bucket_name, object_name, 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='INTELLIGENT_TIERING'))
        assert put_result3.status == 200
        get_result3 = obsClient.getObject(bucket_name, object_name)
        assert get_result3.body.storageClass == 'INTELLIGENT_TIERING'
        self.delete_bucket(obsClient, bucket_name)
        # 深度归档桶上传智能分级对象
        header = CreateBucketHeader(storageClass='DEEP_ARCHIVE')
        cre_result4 = obsClient.createBucket(bucket_name, header=header)
        assert cre_result4.status == 200
        put_result4 = obsClient.putContent(bucket_name, object_name, 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='INTELLIGENT_TIERING'))
        assert put_result4.status == 200
        get_result4 = obsClient.getObject(bucket_name, object_name)
        assert get_result4.body.storageClass == 'INTELLIGENT_TIERING'
        self.delete_bucket(obsClient, bucket_name)

    def test_copyObject_with_intelligent_tiering(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-set-bucket-storage-policy-sdk"
        # 创建标准桶
        header = CreateBucketHeader(storageClass='STANDARD')
        cre_result1 = obsClient.createBucket(bucket_name, header=header)
        assert cre_result1.status == 200
        # 上传各类别对象
        put_result1 = obsClient.putContent(bucket_name, 'object_STANDARD', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='STANDARD'))
        assert put_result1.status == 200
        put_result2 = obsClient.putContent(bucket_name, 'object_WARM', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='WARM'))
        assert put_result2.status == 200
        put_result3 = obsClient.putContent(bucket_name, 'object_COLD', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='COLD'))
        assert put_result3.status == 200
        put_result4 = obsClient.putContent(bucket_name, 'object_DEEP_ARCHIVE', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='DEEP_ARCHIVE'))
        assert put_result4.status == 200
        # 复制各类对象为智能分级对象
        cop_result1 = obsClient.copyObject(bucket_name, 'object_STANDARD', bucket_name, 'INTELLIGENT_TIERING/obj1',
                                           headers=CopyObjectHeader(directive='REPLACE',
                                                                    storageClass='INTELLIGENT_TIERING'))
        assert cop_result1.status == 200
        cop_result2 = obsClient.copyObject(bucket_name, 'object_WARM', bucket_name, 'INTELLIGENT_TIERING/obj2',
                                           headers=CopyObjectHeader(directive='REPLACE',
                                                                    storageClass='INTELLIGENT_TIERING'))
        assert cop_result2.status == 200
        cop_result3 = obsClient.copyObject(bucket_name, 'object_COLD', bucket_name, 'INTELLIGENT_TIERING/obj3',
                                           headers=CopyObjectHeader(directive='REPLACE',
                                                                    storageClass='INTELLIGENT_TIERING'))
        assert cop_result3.status == 403
        cop_result4 = obsClient.copyObject(bucket_name, 'object_DEEP_ARCHIVE', bucket_name, 'INTELLIGENT_TIERING/obj4',
                                           headers=CopyObjectHeader(directive='REPLACE',
                                                                    storageClass='INTELLIGENT_TIERING'))
        assert cop_result4.status == 403
        list_result1 = obsClient.listObjects(bucket_name, 'INTELLIGENT_TIERING/')
        assert list_result1.status == 200
        assert len(list_result1.body.contents) == 2
        for content in list_result1.body.contents:
            assert content.storageClass == 'INTELLIGENT_TIERING'

        # 复制智能分级对象为各类别对象
        cop_result5 = obsClient.copyObject(bucket_name, 'INTELLIGENT_TIERING/obj1', bucket_name,
                                           'other/object_STANDARD',
                                           headers=CopyObjectHeader(directive='REPLACE',
                                                                    storageClass='STANDARD'))
        assert cop_result5.status == 200
        cop_result6 = obsClient.copyObject(bucket_name, 'INTELLIGENT_TIERING/obj1', bucket_name, 'other/object_WARM',
                                           headers=CopyObjectHeader(directive='REPLACE',
                                                                    storageClass='WARM'))
        assert cop_result6.status == 200
        cop_result7 = obsClient.copyObject(bucket_name, 'INTELLIGENT_TIERING/obj1', bucket_name, 'other/object_COLD',
                                           headers=CopyObjectHeader(directive='REPLACE',
                                                                    storageClass='COLD'))
        assert cop_result7.status == 200
        cop_result8 = obsClient.copyObject(bucket_name, 'INTELLIGENT_TIERING/obj1', bucket_name,
                                           'other/object_DEEP_ARCHIVE',
                                           headers=CopyObjectHeader(directive='REPLACE',
                                                                    storageClass='DEEP_ARCHIVE'))
        assert cop_result8.status == 200
        list_result2 = obsClient.listObjects(bucket_name, 'other/')
        assert list_result2.status == 200
        assert len(list_result2.body.contents) == 4
        for content in list_result2.body.contents:
            assert content.storageClass != 'INTELLIGENT_TIERING'
        self.delete_bucket(obsClient, bucket_name)

    def test_setObjectMetadata_with_intelligent_tiering(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-set-bucket-storage-policy-sdk"
        # 创建标准桶
        header = CreateBucketHeader(storageClass='STANDARD')
        cre_result1 = obsClient.createBucket(bucket_name, header=header)
        assert cre_result1.status == 200
        # 上传各类别对象
        put_result1 = obsClient.putContent(bucket_name, 'object_STANDARD', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='STANDARD'))
        assert put_result1.status == 200
        put_result2 = obsClient.putContent(bucket_name, 'object_WARM', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='WARM'))
        assert put_result2.status == 200
        put_result3 = obsClient.putContent(bucket_name, 'object_COLD', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='COLD'))
        assert put_result3.status == 200
        put_result4 = obsClient.putContent(bucket_name, 'object_DEEP_ARCHIVE', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='DEEP_ARCHIVE'))
        assert put_result4.status == 200
        it_obj_list = ['INTELLIGENT_TIERING/obj1', 'INTELLIGENT_TIERING/obj2', 'INTELLIGENT_TIERING/obj3',
                       'INTELLIGENT_TIERING/obj4']
        for obj in it_obj_list:
            put_result = obsClient.putContent(bucket_name, obj, 'Hello OBS',
                                              headers=PutObjectHeader(storageClass='INTELLIGENT_TIERING'))
            assert put_result.status == 200
        # 修改各类对象为智能分级对象
        set_result1 = obsClient.setObjectMetadata(bucket_name, 'object_STANDARD',
                                                  headers=SetObjectMetadataHeader(storageClass='INTELLIGENT_TIERING'))
        assert set_result1.status == 200
        get_result = obsClient.getObjectMetadata(bucket_name, 'object_STANDARD')
        assert get_result.body.storageClass == 'INTELLIGENT_TIERING'
        set_result2 = obsClient.setObjectMetadata(bucket_name, 'object_WARM',
                                                  headers=SetObjectMetadataHeader(storageClass='INTELLIGENT_TIERING'))
        assert set_result2.status == 200
        get_result = obsClient.getObjectMetadata(bucket_name, 'object_WARM')
        assert get_result.body.storageClass == 'INTELLIGENT_TIERING'
        set_result3 = obsClient.setObjectMetadata(bucket_name, 'object_COLD',
                                                  headers=SetObjectMetadataHeader(storageClass='INTELLIGENT_TIERING'))
        assert set_result3.status == 403
        get_result = obsClient.getObjectMetadata(bucket_name, 'object_COLD')
        assert get_result.body.storageClass == 'COLD'
        set_result4 = obsClient.setObjectMetadata(bucket_name, 'object_DEEP_ARCHIVE',
                                                  headers=SetObjectMetadataHeader(storageClass='INTELLIGENT_TIERING'))
        assert set_result4.status == 403
        get_result = obsClient.getObjectMetadata(bucket_name, 'object_DEEP_ARCHIVE')
        assert get_result.body.storageClass == 'DEEP_ARCHIVE'

        # 修改智能分级对象为各类别对象
        set_result1 = obsClient.setObjectMetadata(bucket_name, 'INTELLIGENT_TIERING/obj1',
                                                  headers=SetObjectMetadataHeader(storageClass='STANDARD'))
        assert set_result1.status == 200
        get_result = obsClient.getObjectMetadata(bucket_name, 'INTELLIGENT_TIERING/obj1')
        assert get_result.body.storageClass == None
        set_result2 = obsClient.setObjectMetadata(bucket_name, 'INTELLIGENT_TIERING/obj2',
                                                  headers=SetObjectMetadataHeader(storageClass='WARM'))
        assert set_result2.status == 200
        get_result = obsClient.getObjectMetadata(bucket_name, 'INTELLIGENT_TIERING/obj2')
        assert get_result.body.storageClass == 'WARM'
        set_result3 = obsClient.setObjectMetadata(bucket_name, 'INTELLIGENT_TIERING/obj3',
                                                  headers=SetObjectMetadataHeader(storageClass='COLD'))
        assert set_result3.status == 200
        get_result = obsClient.getObjectMetadata(bucket_name, 'INTELLIGENT_TIERING/obj3')
        assert get_result.body.storageClass == 'COLD'
        set_result4 = obsClient.setObjectMetadata(bucket_name, 'INTELLIGENT_TIERING/obj4',
                                                  headers=SetObjectMetadataHeader(storageClass='DEEP_ARCHIVE'))
        assert set_result4.status == 200
        get_result = obsClient.getObjectMetadata(bucket_name, 'INTELLIGENT_TIERING/obj4')
        assert get_result.body.storageClass == 'DEEP_ARCHIVE'
        self.delete_bucket(obsClient, bucket_name)

    def test_multipart_with_intelligent_tiering(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-multipart-with-intelligent-tiering-sdk"
        object_name = 'multipart_obj1'
        # 创建标准桶
        header = CreateBucketHeader(storageClass='STANDARD')
        cre_result = obsClient.createBucket(bucket_name, header=header)
        assert cre_result.status == 200
        # 上传各类别对象
        put_result1 = obsClient.putContent(bucket_name, 'object_STANDARD', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='STANDARD'))
        assert put_result1.status == 200
        put_result2 = obsClient.putContent(bucket_name, 'object_WARM', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='WARM'))
        assert put_result2.status == 200
        put_result3 = obsClient.putContent(bucket_name, 'object_COLD', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='COLD'))
        assert put_result3.status == 200
        put_result4 = obsClient.putContent(bucket_name, 'object_DEEP_ARCHIVE', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='DEEP_ARCHIVE'))
        assert put_result4.status == 200
        # 初始化分段任务
        mult_resp = obsClient.initiateMultipartUpload(bucket_name, object_name, storageClass='INTELLIGENT_TIERING')
        assert mult_resp.status == 200
        upload_id = mult_resp.body.uploadId
        lis_resp = obsClient.listMultipartUploads(bucket_name)
        assert lis_resp.status == 200
        for obj in lis_resp.body.upload:
            if obj != object_name:
                continue
            else:
                assert obj.storageClass == 'INTELLIGENT_TIERING'
        part_resp = obsClient.uploadPart(bucket_name, object_name, 1, upload_id, 'Hello OBS')
        assert part_resp.status == 200
        # 复制各存储类别段
        cop_result1 = obsClient.copyPart(bucket_name, object_name, 2, upload_id,
                                         'test-multipart-with-intelligent-tiering-sdk/object_STANDARD')
        assert cop_result1.status == 200
        cop_result2 = obsClient.copyPart(bucket_name, object_name, 3, upload_id,
                                         'test-multipart-with-intelligent-tiering-sdk/object_WARM')
        assert cop_result2.status == 200
        cop_result3 = obsClient.copyPart(bucket_name, object_name, 4, upload_id,
                                         'test-multipart-with-intelligent-tiering-sdk/object_COLD')
        assert cop_result3.status == 403
        cop_result4 = obsClient.copyPart(bucket_name, object_name, 5, upload_id,
                                         'test-multipart-with-intelligent-tiering-sdk/object_DEEP_ARCHIVE')
        assert cop_result4.status == 403
        lis_resp2 = obsClient.listParts(bucket_name, object_name, upload_id)
        assert lis_resp2.status == 200
        assert lis_resp2.body.storageClass == 'INTELLIGENT_TIERING'
        del_resp = obsClient.abortMultipartUpload(bucket_name, object_name, upload_id)
        assert del_resp.status == 204
        self.delete_bucket(obsClient, bucket_name)

    def test_listObjects_with_intelligent_tiering(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-list-objects-with-intelligent-tiering-sdk"
        # 创建标准桶
        header = CreateBucketHeader(storageClass='INTELLIGENT_TIERING')
        cre_result = obsClient.createBucket(bucket_name, header=header)
        assert cre_result.status == 200
        # 上传对象
        put_result1 = obsClient.putContent(bucket_name, 'intelligent_tiering_obj1', 'Hello OBS')
        assert put_result1.status == 200
        put_result2 = obsClient.putContent(bucket_name, 'intelligent_tiering_obj2', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='INTELLIGENT_TIERING'))
        assert put_result2.status == 200
        list_result1 = obsClient.listObjects(bucket_name)
        assert list_result1.status == 200
        assert len(list_result1.body.contents) == 2
        for content in list_result1.body.contents:
            assert content.storageClass == 'INTELLIGENT_TIERING'
        # 开启桶的多版本状态
        set_resp = obsClient.setBucketVersioning(bucket_name, status='Enabled')
        assert set_resp.status == 200
        time.sleep(5)
        # 上传对象
        put_result1 = obsClient.putContent(bucket_name, 'intelligent_tiering_obj1', 'Hello OBS')
        assert put_result1.status == 200
        put_result2 = obsClient.putContent(bucket_name, 'intelligent_tiering_obj2', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='INTELLIGENT_TIERING'))
        assert put_result2.status == 200
        list_result2 = obsClient.listVersions(bucket_name)
        assert list_result2.status == 200
        assert len(list_result2.body.versions) == 4
        for version in list_result2.body.versions:
            assert version.storageClass == 'INTELLIGENT_TIERING'
        self.delete_bucket(obsClient, bucket_name)

    def test_posixbucket_with_intelligent_tiering(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-list-objects-with-intelligent-tiering-sdk"
        # 创建标准桶
        header = CreateBucketHeader(isPFS=True, storageClass='INTELLIGENT_TIERING')
        cre_result = obsClient.createBucket(bucket_name, header=header)
        assert cre_result.status == 405
        header = CreateBucketHeader(isPFS=True)
        cre_result = obsClient.createBucket(bucket_name, header=header)
        assert cre_result.status == 200
        put_result1 = obsClient.putContent(bucket_name, 'intelligent_tiering_obj1', 'Hello OBS',
                                           headers=PutObjectHeader(storageClass='INTELLIGENT_TIERING'))
        assert put_result1.status == 405
        self.delete_bucket(obsClient, bucket_name)

    def test_bpa_001(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-bpa-python-esdk"
        # 创建标准桶
        cre_result = obsClient.createBucket(bucket_name)
        assert cre_result.status == 200
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        # assert get_result.body.blockPublicAcls
        # assert get_result.body.ignorePublicAcls
        # assert get_result.body.blockPublicPolicy
        # assert get_result.body.restrictPublicBuckets
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls='false', ignorePublicAcls='FALSE',
                                                          blockPublicPolicy='FaLsE', restrictPublicBuckets='faLSE')
        assert put_result.status == 200
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.blockPublicAcls
        assert not get_result.body.ignorePublicAcls
        assert not get_result.body.blockPublicPolicy
        assert not get_result.body.restrictPublicBuckets
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls='true', ignorePublicAcls='TRUE',
                                                          blockPublicPolicy='TrUe', restrictPublicBuckets='trUE')
        assert put_result.status == 200
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert get_result.body.blockPublicAcls
        assert get_result.body.ignorePublicAcls
        assert get_result.body.blockPublicPolicy
        assert get_result.body.restrictPublicBuckets
        del_result = obsClient.deleteBucketPublicAccessBlock(bucket_name)
        assert del_result.status == 204
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.blockPublicAcls
        assert not get_result.body.ignorePublicAcls
        assert not get_result.body.blockPublicPolicy
        assert not get_result.body.restrictPublicBuckets
        self.delete_bucket(obsClient, bucket_name)

    def test_bpa_002(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-bpa-python-esdk"
        header = CreateBucketHeader(isPFS=True)
        # 创建标准桶
        cre_result = obsClient.createBucket(bucket_name, header)
        assert cre_result.status == 200
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.blockPublicAcls
        assert not get_result.body.ignorePublicAcls
        assert not get_result.body.blockPublicPolicy
        assert not get_result.body.restrictPublicBuckets
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls=True, ignorePublicAcls=True,
                                                          blockPublicPolicy=True, restrictPublicBuckets=True)
        assert put_result.status == 200
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert get_result.body.blockPublicAcls
        assert get_result.body.ignorePublicAcls
        assert get_result.body.blockPublicPolicy
        assert get_result.body.restrictPublicBuckets
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls=True)
        assert put_result.status == 200
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert get_result.body.blockPublicAcls
        assert not get_result.body.ignorePublicAcls
        assert not get_result.body.blockPublicPolicy
        assert not get_result.body.restrictPublicBuckets
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicPolicy=True)
        assert put_result.status == 200
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.blockPublicAcls
        assert not get_result.body.ignorePublicAcls
        assert get_result.body.blockPublicPolicy
        assert not get_result.body.restrictPublicBuckets
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, ignorePublicAcls=True)
        assert put_result.status == 200
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.blockPublicAcls
        assert get_result.body.ignorePublicAcls
        assert not get_result.body.blockPublicPolicy
        assert not get_result.body.restrictPublicBuckets
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, restrictPublicBuckets=True)
        assert put_result.status == 200
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.blockPublicAcls
        assert not get_result.body.ignorePublicAcls
        assert not get_result.body.blockPublicPolicy
        assert get_result.body.restrictPublicBuckets
        del_result = obsClient.deleteBucketPublicAccessBlock(bucket_name)
        assert del_result.status == 204
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.blockPublicAcls
        assert not get_result.body.ignorePublicAcls
        assert not get_result.body.blockPublicPolicy
        assert not get_result.body.restrictPublicBuckets
        self.delete_bucket(obsClient, bucket_name)

    def test_bpa_003(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-bpa-python-esdk"
        # 创建标准桶
        cre_result = obsClient.createBucket(bucket_name)
        assert cre_result.status == 200
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls='false', ignorePublicAcls='false',
                                                          blockPublicPolicy='false', restrictPublicBuckets='fal se')
        assert put_result.status == 200
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls='false', ignorePublicAcls='false12',
                                                          blockPublicPolicy='false', restrictPublicBuckets='false')
        assert put_result.status == 200
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls='false', ignorePublicAcls='false',
                                                          blockPublicPolicy='fa#lse', restrictPublicBuckets='false')
        assert put_result.status == 200
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.blockPublicAcls
        assert not get_result.body.ignorePublicAcls
        assert not get_result.body.blockPublicPolicy
        assert not get_result.body.restrictPublicBuckets
        self.delete_bucket(obsClient, bucket_name)

    def test_bpa_004(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-bpa-python-esdk"
        # 创建标准桶
        cre_result = obsClient.createBucket(bucket_name)
        assert cre_result.status == 200
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls=True, ignorePublicAcls=True,
                                                          blockPublicPolicy=True, restrictPublicBuckets=True)
        assert put_result.status == 200
        acl_resp = obsClient.setBucketAcl(bucket_name, aclControl=HeadPermission.PUBLIC_READ_WRITE)
        assert acl_resp.status == 403
        pol_resp = obsClient.setBucketPolicy(bucket_name, '{"Statement":[{"Sid":"44d8","Effect":"Allow","Principal":{"ID":["*"]},"Action":["*"],"Resource":["test-bpa-python-esdk","test-bpa-python-esdk/*"]}]}')
        assert pol_resp.status == 403
        get_result = obsClient.getBucketPublicStatus(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.status
        pol_resp = obsClient.setBucketPolicy(bucket_name, '{ "Statement":[{"Sid":"private-policy", "Effect":"Deny", "Principal":{"ID":["*"]}, "Action":["PutObject"], "Resource":["test-bpa-python-esdk", "test-bpa-python-esdk/*"]}]}')
        assert pol_resp.status == 204
        get_result = obsClient.getBucketPublicStatus(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.status
        self.delete_bucket(obsClient, bucket_name)

    def test_bpa_005(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-bpa-python-esdk"
        # 创建标准桶
        cre_result = obsClient.createBucket(bucket_name)
        assert cre_result.status == 200
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls=True, ignorePublicAcls=True,
                                                          blockPublicPolicy=True, restrictPublicBuckets=True)
        assert put_result.status == 200
        acl_resp = obsClient.setBucketAcl(bucket_name, aclControl=HeadPermission.PUBLIC_READ_WRITE)
        assert acl_resp.status == 403
        pol_resp = obsClient.setBucketPolicy(bucket_name, '{"Statement":[{"Sid":"44d8","Effect":"Allow","Principal":{"ID":["*"]},"Action":["*"],"Resource":["test-bpa-python-esdk","test-bpa-python-esdk/*"]}]}')
        assert pol_resp.status == 403
        get_result = obsClient.getBucketPolicyPublicStatus(bucket_name)
        assert get_result.status == 404
        pol_resp = obsClient.setBucketPolicy(bucket_name, '{"Statement":[{"Sid":"private-policy", "Effect":"Deny", "Principal":{"ID":["*"]}, "Action":["PutObject"], "Resource":["test-bpa-python-esdk", "test-bpa-python-esdk/*"]}]}')
        assert pol_resp.status == 204
        get_result = obsClient.getBucketPolicyPublicStatus(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.status
        self.delete_bucket(obsClient, bucket_name)

    def test_bpa_006(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-bpa-python-esdk"
        header = CreateBucketHeader(isPFS=True)
        # 创建标准桶
        cre_result = obsClient.createBucket(bucket_name, header)
        assert cre_result.status == 200
        acl_resp = obsClient.setBucketAcl(bucket_name, aclControl=HeadPermission.PUBLIC_READ_WRITE)
        assert acl_resp.status == 200
        pol_resp = obsClient.setBucketPolicy(bucket_name, '{"Statement":[{"Sid":"44d8","Effect":"Allow","Principal":{"ID":["*"]},"Action":["*"],"Resource":["test-bpa-python-esdk","test-bpa-python-esdk/*"]}]}')
        assert pol_resp.status == 204
        get_result = obsClient.getBucketPublicStatus(bucket_name)
        assert get_result.status == 200
        assert get_result.body.status
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls=True, ignorePublicAcls=True,
                                                          blockPublicPolicy=True, restrictPublicBuckets=True)
        assert put_result.status == 200
        acl_resp = obsClient.setBucketAcl(bucket_name, aclControl=HeadPermission.PUBLIC_READ_WRITE)
        assert acl_resp.status == 403
        pol_resp = obsClient.setBucketPolicy(bucket_name, '{"Statement":[{"Sid":"44d8","Effect":"Allow","Principal":{"ID":["*"]},"Action":["*"],"Resource":["test-bpa-python-esdk","test-bpa-python-esdk/*"]}]}')
        assert pol_resp.status == 403
        get_result = obsClient.getBucketPublicStatus(bucket_name)
        assert get_result.status == 200
        assert get_result.body.status
        acl_resp = obsClient.setBucketAcl(bucket_name, aclControl=HeadPermission.PRIVATE)
        assert acl_resp.status == 200
        get_result = obsClient.getBucketPublicStatus(bucket_name)
        assert get_result.status == 200
        assert get_result.body.status
        pol_resp = obsClient.setBucketPolicy(bucket_name, '{"Statement":[{"Sid":"private-policy", "Effect":"Deny", "Principal":{"ID":["*"]}, "Action":["PutObject"], "Resource":["test-bpa-python-esdk", "test-bpa-python-esdk/*"]}]}')
        assert pol_resp.status == 204
        get_result = obsClient.getBucketPolicyPublicStatus(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.status
        get_result = obsClient.getBucketAcl(bucket_name)
        assert get_result.status == 200
        get_result = obsClient.getBucketPolicy(bucket_name)
        assert get_result.status == 200
        self.delete_bucket(obsClient, bucket_name)

    def test_bpa_007(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-bpa-python-esdk"
        # 创建标准桶
        cre_result = obsClient.createBucket(bucket_name)
        assert cre_result.status == 200
        del_result = obsClient.deleteBucketPublicAccessBlock(bucket_name)
        assert del_result.status == 204
        acl_resp = obsClient.setBucketAcl(bucket_name, aclControl=HeadPermission.PUBLIC_READ_WRITE)
        assert acl_resp.status == 200
        pol_resp = obsClient.setBucketPolicy(bucket_name, '{"Statement":[{"Sid":"44d8","Effect":"Allow","Principal":{"ID":["*"]},"Action":["*"],"Resource":["test-bpa-python-esdk","test-bpa-python-esdk/*"]}]}')
        assert pol_resp.status == 204
        get_result = obsClient.getBucketPublicStatus(bucket_name)
        assert get_result.status == 200
        assert get_result.body.status
        get_result = obsClient.getBucketPolicyPublicStatus(bucket_name)
        assert get_result.status == 200
        assert get_result.body.status
        pol_resp = obsClient.setBucketPolicy(bucket_name, '{"Statement":[{"Sid":"private-policy", "Effect":"Deny", "Principal":{"ID":["*"]}, "Action":["PutObject"], "Resource":["test-bpa-python-esdk", "test-bpa-python-esdk/*"]}]}')
        assert pol_resp.status == 204
        get_result = obsClient.getBucketPublicStatus(bucket_name)
        assert get_result.status == 200
        assert get_result.body.status
        get_result = obsClient.getBucketPolicyPublicStatus(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.status
        acl_resp = obsClient.setBucketAcl(bucket_name, aclControl=HeadPermission.PRIVATE)
        assert acl_resp.status == 200
        get_result = obsClient.getBucketPublicStatus(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.status
        get_result = obsClient.getBucketPolicyPublicStatus(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.status
        self.delete_bucket(obsClient, bucket_name)

    def test_bpa_008(self):
        client_type, crc64Client, obsClient = self.get_client()
        bucket_name = "test-bpa-python-esdk"
        header = CreateBucketHeader(isPFS=True)
        # 创建标准桶
        cre_result = obsClient.createBucket(bucket_name, header)
        assert cre_result.status == 200
        # 模拟打开bpa开关
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls=True, ignorePublicAcls=True,
                                                          blockPublicPolicy=True, restrictPublicBuckets=True)
        assert put_result.status == 200
        # 查询bpa配置
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert get_result.body.blockPublicAcls
        assert get_result.body.ignorePublicAcls
        assert get_result.body.blockPublicPolicy
        assert get_result.body.restrictPublicBuckets
        # 删除bpa配置
        del_result = obsClient.deleteBucketPublicAccessBlock(bucket_name)
        assert del_result.status == 204
        # 查询bpa配置
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.blockPublicAcls
        assert not get_result.body.ignorePublicAcls
        assert not get_result.body.blockPublicPolicy
        assert not get_result.body.restrictPublicBuckets
        # 设置bpa配置
        put_result = obsClient.putBucketPublicAccessBlock(bucket_name, blockPublicAcls=True, ignorePublicAcls=True,
                                                          blockPublicPolicy=True, restrictPublicBuckets=True)
        assert put_result.status == 200
        # 查询bpa配置
        get_result = obsClient.getBucketPublicAccessBlock(bucket_name)
        assert get_result.status == 200
        assert get_result.body.blockPublicAcls
        assert get_result.body.ignorePublicAcls
        assert get_result.body.blockPublicPolicy
        assert get_result.body.restrictPublicBuckets
        # 设置桶公开acl和策略
        acl_resp = obsClient.setBucketAcl(bucket_name, aclControl=HeadPermission.PUBLIC_READ_WRITE)
        assert acl_resp.status == 403
        pol_resp = obsClient.setBucketPolicy(bucket_name, '{"Statement":[{"Sid":"44d8","Effect":"Allow","Principal":{"ID":["*"]},"Action":["*"],"Resource":["test-bpa-python-esdk","test-bpa-python-esdk/*"]}]}')
        assert pol_resp.status == 403
        get_result = obsClient.getBucketPublicStatus(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.status
        get_result = obsClient.getBucketPolicyPublicStatus(bucket_name)
        assert get_result.status == 404
        # 设置桶非公开acl和策略
        acl_resp = obsClient.setBucketAcl(bucket_name, aclControl=HeadPermission.PRIVATE)
        assert acl_resp.status == 200
        pol_resp = obsClient.setBucketPolicy(bucket_name, '{"Statement":[{"Sid":"private-policy", "Effect":"Deny", "Principal":{"ID":["*"]}, "Action":["PutObject"], "Resource":["test-bpa-python-esdk", "test-bpa-python-esdk/*"]}]}')
        assert pol_resp.status == 204
        get_result = obsClient.getBucketPublicStatus(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.status
        get_result = obsClient.getBucketPolicyPublicStatus(bucket_name)
        assert get_result.status == 200
        assert not get_result.body.status
        self.delete_bucket(obsClient, bucket_name)

    def test_alpha_python_sdk_imdsv2_001(self):
        obsClient = ObsClient(security_provider_policy="ECS", server=test_config["endpoint"])
        lis_result = obsClient.listBuckets()
        assert lis_result.status == 200

    def test_create_bucket_006(self):
        obsClient = ObsClient(access_key_id=test_config["ak"],
                                                        secret_access_key=test_config["sk"],
                                                        server=test_config["endpoint"], path_style=True)
        invalid_bucket_name = 'abcdefghijklmnopqrstuvwxyz1206abcdefghijklmnopqrstuvwxyz1206aaaa'
        result = obsClient.createBucket(invalid_bucket_name)
        assert result.status == 400
        assert result.errorCode == 'InvalidBucketName'

    def test_create_bucket_007(self):
        obsClient = ObsClient(access_key_id=test_config["ak"],
                                                        secret_access_key=test_config["sk"],
                                                        server=test_config["endpoint"], path_style=True)
        invalid_bucket_name = 'bucket001.'
        result = obsClient.createBucket(invalid_bucket_name)
        assert result.status == 400
        assert result.errorCode == 'InvalidBucketName'

    def test_create_bucket_008(self):
        obsClient = ObsClient(access_key_id=test_config["ak"],
                                                        secret_access_key=test_config["sk"],
                                                        server=test_config["endpoint"], path_style=True)
        invalid_bucket_name = 'bucket..001'
        result = obsClient.createBucket(invalid_bucket_name)
        assert result.status == 400
        assert result.errorCode == 'InvalidBucketName'


if __name__ == "__main__":
    pytest.main(["-v", 'test_obs_client.py::TestOBSClient::test_uploadFile_with_metadata'])
