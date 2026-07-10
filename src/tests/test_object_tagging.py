#!/usr/bin/python
# -*- coding:utf-8 -*-
# Copyright 2019 Huawei Technologies Co.,Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# CONDITIONS OF ANY KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations under the License.

"""
对象标签管理功能 - 集成测试
需要真实的OBS环境
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs import ObsClient, Tag
from conftest import test_config


class TestObjectTagging(object):
    """对象标签功能测试类"""

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

    def test_set_object_tagging_with_list_format(self):
        """测试场景: 使用List格式设置对象标签"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-list-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            tags = [
                {'key': 'project', 'value': 'demo'},
                {'key': 'env', 'value': 'production'},
                {'key': 'owner', 'value': 'test-team'}
            ]
            set_resp = client.setObjectTagging(bucket_name, object_key, tags)
            assert set_resp.status == 200

            get_resp = client.getObjectTagging(bucket_name, object_key)
            assert get_resp.status == 200
            assert len(get_resp.body.tags) == 3

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_with_dict_format(self):
        """测试场景: 使用Dict格式设置对象标签"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-dict-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            tags = {
                'project': 'demo',
                'env': 'production',
                'owner': 'test-team'
            }
            set_resp = client.setObjectTagging(bucket_name, object_key, tags)
            assert set_resp.status == 200

            get_resp = client.getObjectTagging(bucket_name, object_key)
            assert get_resp.status == 200
            assert len(get_resp.body.tags) == 3

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_with_tag_objects(self):
        """测试场景: 使用Tag对象列表设置标签"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-obj-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            tags = [Tag('key1', 'value1'), Tag('key2', 'value2')]
            set_resp = client.setObjectTagging(bucket_name, object_key, tags)
            assert set_resp.status == 200

            get_resp = client.getObjectTagging(bucket_name, object_key)
            assert get_resp.status == 200
            assert len(get_resp.body.tags) == 2

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_overwrite_tags(self):
        """测试场景: 重新设置标签覆盖旧标签"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-overwrite-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            initial_tags = {'old-key1': 'old-value1', 'old-key2': 'old-value2'}
            set_resp1 = client.setObjectTagging(bucket_name, object_key, initial_tags)
            assert set_resp1.status == 200

            get_resp1 = client.getObjectTagging(bucket_name, object_key)
            assert len(get_resp1.body.tags) == 2

            new_tags = {'new-key1': 'new-value1', 'new-key2': 'new-value2', 'new-key3': 'new-value3'}
            set_resp2 = client.setObjectTagging(bucket_name, object_key, new_tags)
            assert set_resp2.status == 200

            get_resp2 = client.getObjectTagging(bucket_name, object_key)
            assert len(get_resp2.body.tags) == 3
            tag_dict = {tag.key: tag.value for tag in get_resp2.body.tags}
            assert 'new-key1' in tag_dict
            assert 'old-key1' not in tag_dict

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_get_object_tagging_no_tags(self):
        """测试场景: 获取没有标签的对象"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-none-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            get_resp = client.getObjectTagging(bucket_name, object_key)
            assert get_resp.status in [200, 404]

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_delete_object_tagging(self):
        """测试场景: 删除对象的标签"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-del-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            tags = {'key1': 'value1', 'key2': 'value2'}
            set_resp = client.setObjectTagging(bucket_name, object_key, tags)
            assert set_resp.status == 200

            del_resp = client.deleteObjectTagging(bucket_name, object_key)
            assert del_resp.status == 204

            get_resp = client.getObjectTagging(bucket_name, object_key)
            assert get_resp.status in [200, 404]

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_delete_object_tagging_no_tags(self):
        """测试场景: 删除没有标签的对象"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-del-none-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            del_resp = client.deleteObjectTagging(bucket_name, object_key)
            assert del_resp.status == 204

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    # ==================== 边界测试 ====================

    def test_set_object_tagging_empty_list(self):
        """测试场景: 设置空标签列表"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-empty-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            client.setObjectTagging(bucket_name, object_key, {'key': 'value'})

            set_resp = client.setObjectTagging(bucket_name, object_key, [])
            assert set_resp.status == 200

            get_resp = client.getObjectTagging(bucket_name, object_key)
            assert get_resp.status in [200, 404]

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_single_tag(self):
        """测试场景: 设置单个标签(最小边界)"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-single-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            set_resp = client.setObjectTagging(bucket_name, object_key, {'key': 'value'})
            assert set_resp.status == 200

            get_resp = client.getObjectTagging(bucket_name, object_key)
            assert get_resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_max_tags(self):
        """测试场景: 设置10个标签(最大值)"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-max-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            tags = {f'key{i}': f'value{i}' for i in range(10)}
            set_resp = client.setObjectTagging(bucket_name, object_key, tags)
            assert set_resp.status == 200

            get_resp = client.getObjectTagging(bucket_name, object_key)
            assert get_resp.status == 200
            assert len(get_resp.body.tags) == 10

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_min_key_length(self):
        """测试场景: 键长度为1个字符"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-minkey-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            set_resp = client.setObjectTagging(bucket_name, object_key, {'a': 'value'})
            assert set_resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_max_key_length(self):
        """测试场景: 键长度为128个字符"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-maxkey-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            max_key = 'a' * 128
            set_resp = client.setObjectTagging(bucket_name, object_key, {max_key: 'value'})
            assert set_resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_empty_value(self):
        """测试场景: 标签值为空字符串"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-emptyval-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            set_resp = client.setObjectTagging(bucket_name, object_key, {'key': ''})
            assert set_resp.status == 200

            get_resp = client.getObjectTagging(bucket_name, object_key)
            assert get_resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_max_value_length(self):
        """
        测试场景: 标签值为255个字符(OBS实际限制)
        """
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-maxval-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            max_value = 'a' * 255
            set_resp = client.setObjectTagging(bucket_name, object_key, {'key': max_value})
            assert set_resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_special_characters(self):
        """测试场景: 键名包含允许的特殊字符"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-special-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            tags = {
                'test.key': 'value1',
                'test-key': 'value2',
                'test+key': 'value3',
                'test_key': 'value4',
                'test=key': 'value5'
            }
            set_resp = client.setObjectTagging(bucket_name, object_key, tags)
            assert set_resp.status == 200

            get_resp = client.getObjectTagging(bucket_name, object_key)
            assert get_resp.status == 200
            assert len(get_resp.body.tags) == 5

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_case_sensitive(self):
        """测试场景: 标签键大小写敏感性"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-case-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            tags = {
                'Key': 'value1',
                'KEY': 'value2',
                'key': 'value3'
            }
            set_resp = client.setObjectTagging(bucket_name, object_key, tags)
            assert set_resp.status == 200

            get_resp = client.getObjectTagging(bucket_name, object_key)
            assert get_resp.status == 200
            assert len(get_resp.body.tags) == 3

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    # ==================== 参数检查测试 ====================

    def test_set_object_tagging_missing_bucket_name(self):
        """测试场景: bucketName为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.setObjectTagging(None, 'object-key', {'key': 'value'})
        assert 'bucketName' in str(exc_info.value).lower() or 'empty' in str(exc_info.value).lower()

    def test_set_object_tagging_missing_object_key(self):
        """测试场景: objectKey为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.setObjectTagging('bucket-name', None, {'key': 'value'})
        assert 'objectKey' in str(exc_info.value).lower() or 'empty' in str(exc_info.value).lower()

    def test_set_object_tagging_missing_tags(self):
        """测试场景: tags为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.setObjectTagging('bucket-name', 'object-key', None)
        assert 'tags' in str(exc_info.value).lower() or 'empty' in str(exc_info.value).lower()

    def test_get_object_tagging_missing_bucket_name(self):
        """测试场景: getObjectTagging的bucketName为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.getObjectTagging(None, 'object-key')
        assert 'bucketName' in str(exc_info.value).lower() or 'empty' in str(exc_info.value).lower()

    def test_delete_object_tagging_missing_bucket_name(self):
        """测试场景: deleteObjectTagging的bucketName为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.deleteObjectTagging(None, 'object-key')
        assert 'bucketName' in str(exc_info.value).lower() or 'empty' in str(exc_info.value).lower()

    # ==================== 边界失败测试 ====================

    def test_set_object_tagging_key_too_long(self):
        """测试场景: 设置键长度为129个字符的标签失败"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-longkey-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            # Key length exceeds the maximum allowed (128 characters)
            long_key = 'a' * 129
            set_resp = client.setObjectTagging(bucket_name, object_key, {long_key: 'value'})
            assert set_resp.status == 400

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_value_too_long(self):
        """测试场景: 设置标签值为256个字符的标签失败"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-longvalue-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            # Value length exceeds the maximum allowed (250 characters)
            long_value = 'a' * 256
            set_resp = client.setObjectTagging(bucket_name, object_key, {'key': long_value})
            assert set_resp.status == 400

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_too_many_tags(self):
        """测试场景: 设置11个标签（过大值）失败"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-tag-many-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            # Exceeds the maximum number of tags (10)
            tags = {f'key{i}': f'value{i}' for i in range(11)}
            set_resp = client.setObjectTagging(bucket_name, object_key, tags)
            assert set_resp.status == 400

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    def test_set_object_tagging_parallel_filesystem(self):
        """测试场景: 并行文件系统设置对象标签失败"""
        client_type, client = self.get_client()
        bucket_name = 'python-sdk-posix-set-object-tagging-test'
        import time
        from obs import CreateBucketHeader
        # 创建posix桶
        cre_resp =client.createBucket(bucket_name, CreateBucketHeader(isPFS=True))
        assert cre_resp.status == 200

        object_key = 'test-tag-parallel-' + str(int(time.time()))

        try:
            put_resp = client.putContent(bucket_name, object_key, 'test content')
            assert put_resp.status == 200

            tags = {'project': 'demo', 'env': 'production'}
            set_resp = client.setObjectTagging(bucket_name, object_key, tags)
            # Parallel filesystem may not support object tagging, expect failure
            # This test verifies the SDK handles the error properly
            assert set_resp.status == 405

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            del_resp = client.deleteBucket(bucket_name)
            assert del_resp.status == 204
