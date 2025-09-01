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

import os
import conftest
from conftest import test_config

from obs import (
    ObsClient,
    AppendObjectContent,
)


class TestUseHttpConns(object):
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

    def test_appendObject_use_http_conns(self):

        obsClient = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                              server=test_config["endpoint"],
                              is_signature_negotiation=False, use_http_conns=True)
        # 创建桶
        bucket_name = "test-append-object-use-http-conns-python-esdk"

        cre_result = obsClient.createBucket(bucket_name)
        assert cre_result.status == 200

        # 追加上传文本对象
        content = AppendObjectContent()
        content.content = 'Hello OBS'
        content.position = 0
        append_result = obsClient.appendObject(bucket_name, 'obj1', content)
        assert append_result.status == 200

        # 追加上传文件对象
        content = AppendObjectContent()
        if not os.path.exists('testFile'):
            conftest.gen_random_file('testFile', 15 * 1024)
        content.isFile = True
        content.content = 'testFile'
        content.position = 9
        append_result = obsClient.appendObject(bucket_name, 'obj1', content)
        assert append_result.status == 200

        self.delete_bucket(obsClient, bucket_name)

    def test_putFile_use_http_conns(self):
        obsClient = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                              server=test_config["endpoint"],
                              is_signature_negotiation=False, use_http_conns=True)
        # 创建桶
        bucket_name = "test-put-file-use-http-conns-python-esdk"
        cre_result = obsClient.createBucket(bucket_name)
        assert cre_result.status == 200
        # 上传文件对象
        if not os.path.exists('testFile'):
            conftest.gen_random_file('testFile', 15 * 1024)
        put_result = obsClient.putFile(bucket_name, 'obj1', 'testFile')
        assert put_result.status == 200

        self.delete_bucket(obsClient, bucket_name)

    def test_putContent_use_http_conns(self):
        obsClient = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                              server=test_config["endpoint"],
                              is_signature_negotiation=False, use_http_conns=True)
        # 创建桶
        bucket_name = "test-put-file-use-http-conns-python-esdk"
        cre_result = obsClient.createBucket(bucket_name)
        assert cre_result.status == 200
        # 上传文本对象
        put_result = obsClient.putContent(bucket_name, 'obj1', 'Hollow OBS')
        assert put_result.status == 200
        # 上传可读流
        if not os.path.exists('testFile'):
            conftest.gen_random_file('testFile', 15 * 1024)
        with open('testFile', 'rb') as file:
            put_result = obsClient.putContent(bucket_name, 'obj1', file)
            assert put_result.status == 200

        self.delete_bucket(obsClient, bucket_name)

    def test_uploadFile_use_http_conns(self):
        obsClient = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                              server=test_config["endpoint"],
                              is_signature_negotiation=False, use_http_conns=True)
        # 创建桶
        bucket_name = "test-put-file-use-http-conns-python-esdk"
        cre_result = obsClient.createBucket(bucket_name)
        assert cre_result.status == 200
        # 上传文件对象
        if not os.path.exists('testFile'):
            conftest.gen_random_file('testFile', 15 * 1024)
        put_result = obsClient.uploadFile(bucket_name, 'obj1', 'testFile', taskNum=5)
        assert put_result.status == 200

        self.delete_bucket(obsClient, bucket_name)

    def test_use_http_conns_and_change_pool_size(self):
        obsClient = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                              server=test_config["endpoint"],
                              is_signature_negotiation=False, use_http_conns=True, pool_size=20)
        # 创建桶
        bucket_name = "test-put-file-use-http-conns-python-esdk"
        cre_result = obsClient.createBucket(bucket_name)
        assert cre_result.status == 200
        # 上传文件对象
        if not os.path.exists('testFile'):
            conftest.gen_random_file('testFile', 15 * 1024)
        put_result = obsClient.uploadFile(bucket_name, 'obj1', 'testFile', taskNum=30, partSize=500)
        assert put_result.status == 200

        self.delete_bucket(obsClient, bucket_name)

    def test_use_http_conns_and_change_trust_env(self):
        obsClient = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                              server=test_config["endpoint"],
                              is_signature_negotiation=False, use_http_conns=True, trust_env=True)
        # 创建桶
        bucket_name = "test-put-file-use-http-conns-python-esdk"
        cre_result = obsClient.createBucket(bucket_name)
        assert cre_result.status == 200
        # 上传文件对象
        if not os.path.exists('testFile'):
            conftest.gen_random_file('testFile', 15 * 1024)
        put_result = obsClient.uploadFile(bucket_name, 'obj1', 'testFile')
        assert put_result.status == 200

        self.delete_bucket(obsClient, bucket_name)
