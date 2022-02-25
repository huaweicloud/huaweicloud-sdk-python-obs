# coding:utf-8
import io
import os
import random
import time
from datetime import datetime

import pytest

import conftest
from obs import CreateBucketHeader, GetObjectHeader, ObsClient, UploadFileHeader
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
            assert "response from server is something wrong." in e.message
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
            assert "PreconditionFailed" in e.message
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
            assert "PreconditionFailed" in e.message
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


if __name__ == "__main__":
    pytest.main(["-v", 'test_obs_client.py::TestOBSClient::test_uploadFile_with_metadata'])
