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


import pytest
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import test_config
from obs import ObsClient
from obs import CreateBucketHeader


class TestModifyTruncateIntegration(object):
    """
    集成测试：modifyFile 和 truncateFile 方法
    使用真实OBS服务进行端到端测试
    """

    def get_client(self):
        """获取OBS客户端实例"""
        client_type = "ObsClient"
        path_style = True if test_config["auth_type"] == "v2" else False
        client = ObsClient(
            access_key_id=test_config["ak"],
            secret_access_key=test_config["sk"],
            server=test_config["endpoint"],
            is_signature_negotiation=False,
            path_style=path_style
        )
        return client_type, client


    def _get_content_from_response(self, get_result):
        """从getObject响应中获取实际内容"""
        if hasattr(get_result, 'body') and get_result.body:
            body = get_result.body
            return body.buffer.decode('utf-8')
        return ""

    def setup_posix_bucket(self, client):
        """创建POSIX桶用于测试"""
        bucket_name = f"test-posix-bucket-{int(time.time())}"
        create_resp = client.createBucket(bucket_name, CreateBucketHeader(isPFS=True))
        assert create_resp.status == 200, f"Create POSIX bucket failed: {create_resp.status}"
        return bucket_name

    def cleanup_posix_bucket(self, client, bucket_name):
        """清理POSIX桶"""
        try:
            # 先删除桶内所有对象
            list_resp = client.listObjects(bucket_name)
            if list_resp.status == 200 and list_resp.body.contents:
                for obj in list_resp.body.contents:
                    client.deleteObject(bucket_name, obj.key)
            # 删除桶
            delete_resp = client.deleteBucket(bucket_name)
            assert delete_resp.status == 204, f"Delete bucket failed: {delete_resp.status}"
        except Exception:
            pass

    def test_modifyFile_integration_with_string_content(self):
        """测试modifyFile方法 - 字符串内容"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 首先上传初始文件
            test_content = 'Test content'
            put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"

            # 执行modify操作
            position = 5
            content_to_insert = 'MODIFIED'

            result = client.modifyFile(
                bucketName=bucket_name,
                objectKey=object_key,
                position=position,
                content=content_to_insert
            )

            # 验证结果
            assert result.status == 200, f"Unexpected status: {result.status}"
            assert result.requestId is not None

            # 验证修改后的内容
            get_result = client.getObject(
                bucketName=bucket_name,
                objectKey=object_key,
                loadStreamInMemory=True
            )
            assert get_result.status == 200

            decoded_content = self._get_content_from_response(get_result)
            expected_content = 'Test MODIFIED'
            assert decoded_content == expected_content, f"Expected '{expected_content}', got '{decoded_content}'"
        except Exception as e:
            raise e
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    def test_modifyFile_integration_with_file_content(self):
        """测试modifyFile方法 - 文件对象内容"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 首先上传初始文件
            test_content = 'Test content'
            put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"

            # 创建要插入的临时文件
            temp_insert_file = os.path.join('./', 'insert_content.txt')
            with open(temp_insert_file, 'wb') as f:
                f.write('FILE_CONTENT'.encode('utf-8'))

            # 执行modify操作
            position = 5

            with open(temp_insert_file, 'rb') as f:
                result = client.modifyFile(
                    bucketName=bucket_name,
                    objectKey=object_key,
                    position=position,
                    content=f
                )

            # 验证结果
            assert result.status == 200, f"Unexpected status: {result.status}"
            assert result.body.etag is not None

            # 验证修改后的内容
            get_result = client.getObject(
                bucketName=bucket_name,
                objectKey=object_key,
                loadStreamInMemory=True
            )
            assert get_result.status == 200

            decoded_content = self._get_content_from_response(get_result)
            expected_content = 'Test FILE_CONTENT'
            assert decoded_content == expected_content, f"Expected '{expected_content}', got '{decoded_content}'"
        finally:
            # 清理临时文件
            if os.path.exists(temp_insert_file):
                os.remove(temp_insert_file)
            self.cleanup_posix_bucket(client, bucket_name)

    def test_modifyFile_integration_with_progress_callback(self):
        """测试modifyFile方法 - 进度回调"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 首先上传初始文件
            test_content = 'Test content for progress callback'
            put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"

            # 创建要插入的临时文件
            temp_insert_file = os.path.join('./', 'insert_content.txt')
            with open(temp_insert_file, 'wb') as f:
                f.write('FILE_CONTENT'.encode('utf-8'))

            progress_events = []
            # 定义进度回调函数
            def callback(transferredAmount, totalAmount, totalSeconds):
                # 获取上传进度百分比
                progress_events.append(transferredAmount * 100.0 / totalAmount)

            # 执行modify操作
            position = 10
            with open(temp_insert_file, 'rb') as f:
                result = client.modifyFile(
                    bucketName=bucket_name,
                    objectKey=object_key,
                    position=position,
                    content=f,
                    headers={'contentLength':12},
                    progressCallback=callback
                )

            # 验证结果
            assert result.status == 200, f"Unexpected status: {result.status}"
            assert len(progress_events) > 0, "Progress callback should have been called"
        except Exception as e:
            raise e
        finally:
            #     # 清理临时文件
            if os.path.exists(temp_insert_file):
                os.remove(temp_insert_file)
            self.cleanup_posix_bucket(client, bucket_name)
    def test_modifyFile_integration_with_headers(self):
        """测试modifyFile方法 - 自定义头信息"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 首先上传初始文件
            test_content = 'Test content with headers'
            put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"
            time.sleep(1)

            # 执行modify操作
            position = 0
            content = 'NEW_HEADER'
            headers = {
                'Content-Type': 'text/plain',
                'Content-Encoding': 'gzip'
            }

            result = client.modifyFile(
                bucketName=bucket_name,
                objectKey=object_key,
                position=position,
                content=content,
                headers=headers
            )

            # 验证结果
            assert result.status == 200, f"Unexpected status: {result.status}"
            assert result.body.etag is not None

            # 验证头信息被应用
            get_result = client.getObject(
                bucketName=bucket_name,
                objectKey=object_key,
                loadStreamInMemory=True
            )
            assert get_result.status == 200
        except Exception as e:
            raise e
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    def test_truncateFile_integration_normal(self):
        """测试truncateFile方法 - 正常情况"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 首先上传一个长文件
            test_content = 'Test content LONG CONTENT that exceeds truncate length maximum limit'
            put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"

            # 执行truncate操作
            length = 20

            result = client.truncateFile(
                bucketName=bucket_name,
                objectKey=object_key,
                length=length
            )

            # 验证结果
            assert result.status == 204, f"Unexpected status: {result.status}"
            # 验证截断后的内容
            get_result = client.getObject(
                bucketName=bucket_name,
                objectKey=object_key,
                loadStreamInMemory=True
            )
            assert get_result.status == 200
            decoded_content = self._get_content_from_response(get_result)
            assert len(decoded_content) == length, f"Expected length {length}, got {len(decoded_content)}"
        except Exception as e:
            raise e
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    def test_truncateFile_integration_with_extension_headers(self):
        """测试truncateFile方法 - 扩展头信息"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 首先上传初始文件
            test_content = 'Test content for truncate with extension headers'
            put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"

            # 执行truncate操作
            length = 30
            extension_headers = {
                'x-amz-meta-test': 'truncate-test-value'
            }

            result = client.truncateFile(
                bucketName=bucket_name,
                objectKey=object_key,
                length=length,
                extensionHeaders=extension_headers
            )

            # 验证结果
            assert result.status == 204, f"Unexpected status: {result.status}"

            # 验证截断后的内容和元数据
            get_result = client.getObjectMetadata(
                bucketName=bucket_name,
                objectKey=object_key
            )
            assert get_result.status == 200
        except Exception as e:
            raise e
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    def test_modifyFile_integration_with_extension_headers(self):
        """测试modifyFile方法 - 扩展头信息"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 首先上传初始文件
            test_content = 'Test content for modify with extension headers'
            put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"

            # 执行modify操作
            position = 0
            content = 'EXTENDED_HEADERS'
            extension_headers = {
                'x-amz-meta-modify': 'modify-test-value',
                'x-amz-storage-class': 'STANDARD'
            }

            result = client.modifyFile(
                bucketName=bucket_name,
                objectKey=object_key,
                position=position,
                content=content,
                extensionHeaders=extension_headers
            )

            # 验证结果
            assert result.status == 200, f"Unexpected status: {result.status}"
            assert result.body.etag is not None
        except Exception as e:
            raise e
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    # ==================== Boundary Tests ====================

    def test_modifyFile_integration_at_end_of_file(self):
        """测试modifyFile方法 - 在文件末尾修改"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 首先上传初始文件
            test_content = 'Test content for modify and truncate operations'
            put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"

            # 获取文件长度
            get_result = client.getObject(
                bucketName=bucket_name,
                objectKey=object_key,
                loadStreamInMemory=True
            )
            assert get_result.status == 200
            file_length = len(self._get_content_from_response(get_result))

            # 在文件末尾插入内容
            content_to_insert = 'APPENDED_AT_END'

            result = client.modifyFile(
                bucketName=bucket_name,
                objectKey=object_key,
                position=file_length,
                content=content_to_insert
            )

            # 验证结果
            assert result.status == 200, f"Unexpected status: {result.status}"

            # 验证最终内容
            final_get_result = client.getObject(
                bucketName=bucket_name,
                objectKey=object_key,
                loadStreamInMemory=True
            )
            assert final_get_result.status == 200

            decoded_content = self._get_content_from_response(final_get_result)
            expected_content = f'Test content for modify and truncate operations{content_to_insert}'
            assert decoded_content == expected_content, f"Expected '{expected_content}', got '{decoded_content}'"
        except Exception as e:
            raise e
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    # ==================== Parameter Validation Tests ====================

    def test_truncateFile_integration_to_zero_length(self):
        """测试truncateFile方法 - 截断到零长度"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 首先上传初始文件
            test_content = 'Test content for truncate to zero length'
            put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"

            # 截断到零长度
            result = client.truncateFile(
                bucketName=bucket_name,
                objectKey=object_key,
                length=0
            )

            # 验证结果
            assert result.status == 204, f"Unexpected status: {result.status}"

            # 验证文件被清空
            get_result = client.getObject(
                bucketName=bucket_name,
                objectKey=object_key,
                loadStreamInMemory=True
            )
            assert get_result.status == 200

            assert get_result.body.buffer is None, f"Expected empty content, got '{self._get_content_from_response(get_result)}'"
        except Exception as e:
            raise e
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    def test_truncateFile_integration_larger_than_original(self):
        """测试truncateFile方法 - 截断文件到大于原文件大小的长度"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # Step 1: Upload initial file with length 3
            test_content = 'abc'
            put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"

            # Step 2: Execute truncate operation with length 10 (larger than original)
            length = 10
            result = client.truncateFile(
                bucketName=bucket_name,
                objectKey=object_key,
                length=length
            )

            # Step 3: Verify the file
            get_result = client.getObject(
                bucketName=bucket_name,
                objectKey=object_key,
                loadStreamInMemory=True
            )
            assert get_result.status == 200, f"Get object failed: {get_result.status}"

            decoded_content = self._get_content_from_response(get_result)
            assert get_result.body.size == length, f"Expected length {length}, got {get_result.body.size}"
            # Verify original content is preserved and padded with null characters
            assert decoded_content[:3] == 'abc', f"Original content should be preserved"

        except Exception as e:
            raise e
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    def test_modifyFile_integration_large_content(self):
        """测试modifyFile方法 - 大量内容修改"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 首先上传初始文件
            test_content = 'Test content for modify and truncate operations'
            put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"

            # 插入大量内容
            large_content = 'X' * 1024  # 1KB内容
            position = 0

            start_time = time.time()
            result = client.modifyFile(
                bucketName=bucket_name,
                objectKey=object_key,
                position=position,
                content=large_content
            )
            end_time = time.time()

            # 验证结果
            assert result.status == 200, f"Unexpected status: {result.status}"
            assert result.body.etag is not None

            # 验证性能（应该在合理时间内完成）
            assert end_time - start_time < 30, f"Operation took too long: {end_time - start_time} seconds"

            # 验证最终内容
            get_result = client.getObject(
                bucketName=bucket_name,
                objectKey=object_key,
                loadStreamInMemory=True
            )
            assert get_result.status == 200

            decoded_content = self._get_content_from_response(get_result)
            assert decoded_content == large_content, f"Expected '{large_content}', got '{decoded_content}'"
        except Exception as e:
            raise e
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    # ==================== Lifecycle Tests ====================

    def test_multiple_operations_sequence(self):
        """测试多次modify和truncate操作的序列"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 初始化文件
            initial_content = 'INITIAL'
            put_resp = client.putObject(
                bucketName=bucket_name,
                objectKey=object_key,
                content=initial_content.encode('utf-8')
            )
            assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"
            time.sleep(1)

            # 第一次modify
            result1 = client.modifyFile(
                bucketName=bucket_name,
                objectKey=object_key,
                position=3,
                content='_MOD1_'
            )
            assert result1.status == 200, f"Unexpected status: {result1.status}"
            time.sleep(0.5)

            # 第二次modify
            result2 = client.modifyFile(
                bucketName=bucket_name,
                objectKey=object_key,
                position=8,
                content='_MOD2_'
            )
            assert result2.status == 200, f"Unexpected status: {result2.status}"
            time.sleep(0.5)

            # truncate操作
            result3 = client.truncateFile(
                bucketName=bucket_name,
                objectKey=object_key,
                length=15
            )
            assert result3.status == 204, f"Unexpected status: {result3.status}"

            # 验证最终结果
            final_get_result = client.getObject(
                bucketName=bucket_name,
                objectKey=object_key,
                loadStreamInMemory=True
            )
            assert final_get_result.status == 200

            final_content = self._get_content_from_response(final_get_result)
            assert len(final_content) == 15, f"Expected length 15, got {len(final_content)}"
        except Exception as e:
            raise e
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    def test_parameter_validation_real_error(self):
        """测试参数验证 - 真实错误场景"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        object_key = f"test_modify_truncate_{int(time.time())}"

        try:
            # 测试无效的bucket名称
            with pytest.raises(Exception) as exc_info:
                client.modifyFile(
                    bucketName='',
                    objectKey=object_key,
                    position=0,
                    content='test'
                )
            assert 'bucketname' in str(exc_info.value).lower(), f"Expected error about bucketname, got: {exc_info.value}"

            # 测试无效的object key
            with pytest.raises(Exception) as exc_info:
                client.modifyFile(
                    bucketName=bucket_name,
                    objectKey='',
                    position=0,
                    content='test'
                )
            assert 'objectkey' in str(exc_info.value).lower(), f"Expected error about objectkey, got: {exc_info.value}"

            # 测试无效的position
            with pytest.raises(Exception) as exc_info:
                client.modifyFile(
                    bucketName=bucket_name,
                    objectKey=object_key,
                    position=None,
                    content='test'
                )
            assert 'position' in str(exc_info.value).lower(), f"Expected error about position, got: {exc_info.value}"

            # 测试truncateFile的参数验证
            with pytest.raises(Exception) as exc_info:
                client.truncateFile(
                    bucketName='',
                    objectKey=object_key,
                    length=0
                )
            assert 'bucketname' in str(exc_info.value).lower(), f"Expected error about bucketname, got: {exc_info.value}"

            with pytest.raises(Exception) as exc_info:
                client.truncateFile(
                    bucketName=bucket_name,
                    objectKey='',
                    length=0
                )
            assert 'objectkey' in str(exc_info.value).lower(), f"Expected error about objectkey, got: {exc_info.value}"

            with pytest.raises(Exception) as exc_info:
                client.truncateFile(
                    bucketName=bucket_name,
                    objectKey=object_key,
                    length=None
                )
            assert 'length' in str(exc_info.value).lower(), f"Expected error about length, got: {exc_info.value}"
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    # ==================== Error Handling Tests ====================

    def test_nonexistent_object_operations(self):
        """测试对不存在对象的操作"""
        client_type, client = self.get_client()
        bucket_name = self.setup_posix_bucket(client)
        nonexistent_key = f"test_nonexistent_{int(time.time())}"
        try:
            # 测试对不存在对象的modify操作
            result = client.modifyFile(
                bucketName=bucket_name,
                objectKey=nonexistent_key,
                position=0,
                content='test'
            )
            assert result.status == 404
            # 测试对不存在对象的truncate操作
            result = client.truncateFile(
                bucketName=bucket_name,
                objectKey=nonexistent_key,
                length=100
            )
            assert result.status == 404
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

    def test_object_bucket_operations(self):
        """测试对对象桶的对象操作"""
        client_type, client = self.get_client()
        bucket_name = 'python-sdk-test-modify-truncate-with-object-bucket'
        cre_resp = client.createBucket(bucket_name)
        assert cre_resp.status == 200
        object_key = f"test_object_{int(time.time())}"
        # 首先上传初始文件
        test_content = 'Test content for modify and truncate operations'
        put_resp = client.putObject(bucketName=bucket_name, objectKey=object_key, content=test_content.encode('utf-8'))
        assert put_resp.status == 200, f"Unexpected status: {put_resp.status}"
        try:
            result = client.modifyFile(
                bucketName=bucket_name,
                objectKey=object_key,
                position=0,
                content='test'
            )
            assert result.status == 405
            result = client.truncateFile(
                bucketName=bucket_name,
                objectKey=object_key,
                length=100
            )
            assert result.status == 405
        finally:
            self.cleanup_posix_bucket(client, bucket_name)

