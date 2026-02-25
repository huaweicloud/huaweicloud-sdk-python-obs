#!/usr/bin/python
# -*- coding:utf-8 -*-
# Copyright 2019 Huawei Technologies Co.,Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

"""
对象软链接功能 - 集成测试
需要真实的OBS环境
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs import ObsClient
from conftest import test_config


class TestObjectSymlink(object):
    """对象软链接功能测试类"""

    def get_client(self):
        """获取OBS客户端实例"""
        client_type = "OBSClient"
        path_style = True if test_config["auth_type"] == "v2" else False
        client = ObsClient(
            access_key_id=test_config["ak"],
            secret_access_key=test_config["sk"],
            server=test_config["endpoint"],
            is_signature_negotiation=False,
            path_style=path_style
        )
        return client_type, client

    def cleanup_object(self, client, bucket_name, object_key):
        """清理测试对象"""
        try:
            client.deleteObject(bucket_name, object_key)
        except Exception:
            pass

    # ==================== 功能测试 ====================

    def test_create_symlink_basic(self):
        """测试场景: 创建基本的软链接"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        timestamp = str(int(time.time()))
        target_key = 'test-target-' + timestamp
        symlink_key = 'test-symlink-' + timestamp

        try:
            # 先创建目标对象
            put_resp = client.putContent(bucket_name, target_key, 'test content')
            assert put_resp.status == 200

            # 创建软链接
            symlink_resp = client.putObjectSymlink(bucket_name, symlink_key, target_key)
            assert symlink_resp.status == 200

            # 获取软链接信息
            get_resp = client.getObjectSymlink(bucket_name, symlink_key)
            assert get_resp.status == 200
            assert get_resp.symlinkTarget == target_key

        finally:
            self.cleanup_object(client, bucket_name, symlink_key)
            self.cleanup_object(client, bucket_name, target_key)

    def test_create_symlink_with_metadata(self):
        """测试场景: 创建带元数据的软链接"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        timestamp = str(int(time.time()))
        target_key = 'test-target-meta-' + timestamp
        symlink_key = 'test-symlink-meta-' + timestamp

        try:
            # 先创建目标对象
            put_resp = client.putContent(bucket_name, target_key, 'test content')
            assert put_resp.status == 200

            # 创建带元数据的软链接
            metadata = {'custom-key': 'custom-value', 'description': 'test symlink'}
            symlink_resp = client.putObjectSymlink(
                bucket_name, symlink_key, target_key, metadata=metadata
            )
            assert symlink_resp.status == 200

            # 获取软链接信息
            get_resp = client.getObjectSymlink(bucket_name, symlink_key)
            assert get_resp.status == 200
            assert get_resp.symlinkTarget == target_key

        finally:
            self.cleanup_object(client, bucket_name, symlink_key)
            self.cleanup_object(client, bucket_name, target_key)

    def test_create_symlink_with_acl(self):
        """测试场景: 创建带ACL的软链接"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        timestamp = str(int(time.time()))
        target_key = 'test-target-acl-' + timestamp
        symlink_key = 'test-symlink-acl-' + timestamp

        try:
            # 先创建目标对象
            put_resp = client.putContent(bucket_name, target_key, 'test content')
            assert put_resp.status == 200

            # 创建带ACL的软链接
            symlink_resp = client.putObjectSymlink(
                bucket_name, symlink_key, target_key, acl='public-read'
            )
            assert symlink_resp.status == 200

            # 获取软链接信息
            get_resp = client.getObjectSymlink(bucket_name, symlink_key)
            assert get_resp.status == 200
            assert get_resp.symlinkTarget == target_key

        finally:
            self.cleanup_object(client, bucket_name, symlink_key)
            self.cleanup_object(client, bucket_name, target_key)

    def test_create_symlink_nested_path(self):
        """测试场景: 创建指向嵌套路径的软链接"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        timestamp = str(int(time.time()))
        target_key = 'path/to/target-' + timestamp
        symlink_key = 'symlink-nested-' + timestamp

        try:
            # 先创建目标对象
            put_resp = client.putContent(bucket_name, target_key, 'test content')
            assert put_resp.status == 200

            # 创建软链接
            symlink_resp = client.putObjectSymlink(bucket_name, symlink_key, target_key)
            assert symlink_resp.status == 200

            # 获取软链接信息
            get_resp = client.getObjectSymlink(bucket_name, symlink_key)
            assert get_resp.status == 200
            assert get_resp.symlinkTarget == target_key

        finally:
            self.cleanup_object(client, bucket_name, symlink_key)
            self.cleanup_object(client, bucket_name, target_key)

    def test_update_symlink_target(self):
        """测试场景: 更新软链接指向不同的目标"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        timestamp = str(int(time.time()))
        target_key1 = 'test-target1-' + timestamp
        target_key2 = 'test-target2-' + timestamp
        symlink_key = 'test-symlink-update-' + timestamp

        try:
            # 创建两个目标对象
            put_resp1 = client.putContent(bucket_name, target_key1, 'content1')
            assert put_resp1.status == 200
            put_resp2 = client.putContent(bucket_name, target_key2, 'content2')
            assert put_resp2.status == 200

            # 创建软链接指向第一个目标
            symlink_resp1 = client.putObjectSymlink(bucket_name, symlink_key, target_key1)
            assert symlink_resp1.status == 200

            # 验证指向第一个目标
            get_resp1 = client.getObjectSymlink(bucket_name, symlink_key)
            assert get_resp1.symlinkTarget == target_key1

            # 更新软链接指向第二个目标（重新创建软链接）
            symlink_resp2 = client.putObjectSymlink(bucket_name, symlink_key, target_key2)
            assert symlink_resp2.status == 200

            # 验证指向第二个目标
            get_resp2 = client.getObjectSymlink(bucket_name, symlink_key)
            assert get_resp2.symlinkTarget == target_key2

        finally:
            self.cleanup_object(client, bucket_name, symlink_key)
            self.cleanup_object(client, bucket_name, target_key1)
            self.cleanup_object(client, bucket_name, target_key2)

    def test_delete_symlink(self):
        """测试场景: 删除软链接"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        timestamp = str(int(time.time()))
        target_key = 'test-target-del-' + timestamp
        symlink_key = 'test-symlink-del-' + timestamp

        try:
            # 先创建目标对象
            put_resp = client.putContent(bucket_name, target_key, 'test content')
            assert put_resp.status == 200

            # 创建软链接
            symlink_resp = client.putObjectSymlink(bucket_name, symlink_key, target_key)
            assert symlink_resp.status == 200

            # 删除软链接
            del_resp = client.deleteObject(bucket_name, symlink_key)
            assert del_resp.status == 204

            # 验证软链接已删除
            get_resp = client.getObjectSymlink(bucket_name, symlink_key)
            assert get_resp.status == 404

            # 目标对象应该仍然存在
            target_resp = client.headObject(bucket_name, target_key)
            assert target_resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, symlink_key)
            self.cleanup_object(client, bucket_name, target_key)

    def test_get_symlink_metadata(self):
        """测试场景: 获取软链接的元数据"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        timestamp = str(int(time.time()))
        target_key = 'test-target-meta2-' + timestamp
        symlink_key = 'test-symlink-meta2-' + timestamp

        try:
            # 先创建目标对象
            put_resp = client.putContent(bucket_name, target_key, 'test content')
            assert put_resp.status == 200

            # 创建带内容类型的软链接
            symlink_resp = client.putObjectSymlink(
                bucket_name, symlink_key, target_key,
                contentType='text/plain'
            )
            assert symlink_resp.status == 200

            # 获取软链接元数据
            get_resp = client.getObjectSymlink(bucket_name, symlink_key)
            assert get_resp.status == 200
            assert get_resp.symlinkTarget == target_key
            assert get_resp.contentType == 'text/plain'
            assert get_resp.etag is not None

        finally:
            self.cleanup_object(client, bucket_name, symlink_key)
            self.cleanup_object(client, bucket_name, target_key)

    # ==================== 边界测试 ====================

    def test_create_symlink_to_nonexistent_target(self):
        """测试场景: 创建指向不存在的目标的软链接"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        timestamp = str(int(time.time()))
        target_key = 'nonexistent-target-' + timestamp
        symlink_key = 'test-symlink-nonexist-' + timestamp

        try:
            # 创建指向不存在对象的软链接（OBS应该允许）
            symlink_resp = client.putObjectSymlink(bucket_name, symlink_key, target_key)
            assert symlink_resp.status == 200

            # 获取软链接信息
            get_resp = client.getObjectSymlink(bucket_name, symlink_key)
            assert get_resp.status == 200
            assert get_resp.symlinkTarget == target_key

        finally:
            self.cleanup_object(client, bucket_name, symlink_key)

    def test_create_symlink_empty_metadata(self):
        """测试场景: 创建空元数据的软链接"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        timestamp = str(int(time.time()))
        target_key = 'test-target-empty-' + timestamp
        symlink_key = 'test-symlink-empty-' + timestamp

        try:
            # 先创建目标对象
            put_resp = client.putContent(bucket_name, target_key, 'test content')
            assert put_resp.status == 200

            # 创建空元数据的软链接
            symlink_resp = client.putObjectSymlink(
                bucket_name, symlink_key, target_key,
                metadata={}
            )
            assert symlink_resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, symlink_key)
            self.cleanup_object(client, bucket_name, target_key)

    # ==================== 参数检查测试 ====================

    def test_put_symlink_missing_bucket_name(self):
        """测试场景: bucketName为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.putObjectSymlink(None, 'symlink-key', 'target-key')
        assert 'bucketName' in str(exc_info.value).lower() or 'empty' in str(exc_info.value).lower()

    def test_put_symlink_missing_object_key(self):
        """测试场景: objectKey为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.putObjectSymlink('bucket-name', None, 'target-key')
        assert 'objectKey' in str(exc_info.value).lower() or 'empty' in str(exc_info.value).lower()

    def test_put_symlink_missing_symlink_target(self):
        """测试场景: symlinkTarget为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.putObjectSymlink('bucket-name', 'symlink-key', None)
        assert 'symlinkTarget' in str(exc_info.value).lower() or 'empty' in str(exc_info.value).lower()

    def test_get_symlink_missing_bucket_name(self):
        """测试场景: getObjectSymlink的bucketName为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.getObjectSymlink(None, 'symlink-key')
        assert 'bucketName' in str(exc_info.value).lower() or 'empty' in str(exc_info.value).lower()

    def test_get_symlink_missing_object_key(self):
        """测试场景: getObjectSymlink的objectKey为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.getObjectSymlink('bucket-name', None)
        assert 'objectKey' in str(exc_info.value).lower() or 'empty' in str(exc_info.value).lower()
