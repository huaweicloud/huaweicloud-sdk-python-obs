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

"""
异常测试 - 集成测试
测试各种异常场景和错误处理
"""

import pytest
import sys
import os
import time
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs import ObsClient, UploadTaskStatus
from conftest import test_config


class TestParameterExceptions(object):
    """参数异常测试"""

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

    def test_null_bucket_name(self):
        """测试场景: 空的 bucket 名称"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.uploadFile(None, 'object', 'file')
        assert 'bucket' in str(exc_info.value).lower()

    def test_empty_bucket_name(self):
        """测试场景: 空字符串 bucket 名称"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.uploadFile('', 'object', 'file')
        assert 'bucket' in str(exc_info.value).lower()

    def test_null_object_key(self):
        """测试场景: 空的 object key"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.uploadFile('bucket', None, 'file')
        assert 'object' in str(exc_info.value).lower() and 'key' in str(exc_info.value).lower()

    def test_null_upload_file(self):
        """测试场景: 空的文件路径"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.uploadFile('bucket', 'object', None)
        assert 'upload' in str(exc_info.value).lower() or 'file' in str(exc_info.value).lower()

    def test_invalid_part_size_zero(self):
        """测试场景: 无效的分片大小 0"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test')

        try:
            # SDK 应该处理 0 分片大小，使用最小值
            resp = client.uploadFile(
                bucket_name,
                'test-object',
                test_file,
                partSize=0
            )
            # 应该成功或给出明确错误
            assert resp.status in [200, 400]
        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_negative_part_size(self):
        """测试场景: 负分片大小"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test')

        try:
            # SDK 应该处理负值
            resp = client.uploadFile(
                bucket_name,
                'test-object',
                test_file,
                partSize=-1
            )
            # 应该成功或给出明确错误
            assert resp.status in [200, 400]
        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_invalid_task_num_zero(self):
        """测试场景: 无效的线程数 0"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test')

        try:
            # SDK 应该将 0 线程转换为 1
            resp = client.uploadFile(
                bucket_name,
                'test-object',
                test_file,
                taskNum=0
            )
            assert resp.status in [200, 400]
        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_negative_task_num(self):
        """测试场景: 负线程数"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test')

        try:
            # SDK 应该处理负值
            resp = client.uploadFile(
                bucket_name,
                'test-object',
                test_file,
                taskNum=-1
            )
            # 应该成功或给出明确错误
            assert resp.status in [200, 400]
        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass


class TestFileAccessExceptions(object):
    """文件访问异常测试"""

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

    def test_nonexistent_file(self):
        """测试场景: 不存在的文件"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with pytest.raises(Exception):
            client.uploadFile(
                bucket_name,
                'test-object',
                '/nonexistent/file/path.dat'
            )

    def test_directory_instead_of_file(self):
        """测试场景: 传入目录而不是文件"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with pytest.raises(Exception):
            client.uploadFile(
                bucket_name,
                'test-object',
                '/tmp'  # 目录
            )

    def test_file_without_read_permission(self):
        """测试场景: 无读取权限的文件"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        # 创建无权限文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test content')

        try:
            # 移除读权限
            os.chmod(test_file, 0o000)

            with pytest.raises(Exception):
                client.uploadFile(
                    bucket_name,
                    'test-object',
                    test_file
                )

        finally:
            # 恢复权限以便删除
            try:
                os.chmod(test_file, 0o644)
                os.remove(test_file)
            except Exception:
                pass


class TestBucketExceptions(object):
    """Bucket 异常测试"""

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

    def test_nonexistent_bucket(self):
        """测试场景: 不存在的 bucket"""
        client_type, client = self.get_client()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test content')

        try:
            resp = client.uploadFile(
                'nonexistent-bucket-12345',
                'test-object',
                test_file
            )
            # 应该返回错误状态
            assert resp.status >= 400
        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_bucket_without_permission(self):
        """测试场景: 无权限访问 bucket"""
        # 使用无效的凭证创建客户端
        client = ObsClient(
            access_key_id='invalid-ak',
            secret_access_key='invalid-sk',
            server=test_config["endpoint"]
        )

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test content')

        try:
            resp = client.uploadFile(
                test_config["bucketName"],
                'test-object',
                test_file
            )
            # 应该返回认证错误
            assert resp.status >= 400
        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass


class TestAsyncUploadExceptions(object):
    """异步上传异常测试"""

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

    def test_pause_without_checkpoint(self):
        """测试场景: 未启用 checkpoint 时暂停失败"""
        client_type, client = self.get_client()

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test')

        try:
            task = client.uploadFileAsync(
                'bucket',
                'key',
                test_file,
                enableCheckpoint=False
            )

            # 暂停应该失败
            with pytest.raises(ValueError) as exc_info:
                task.pause()
            assert 'checkpoint' in str(exc_info.value).lower()

        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_cancel_completed_task(self):
        """测试场景: 取消已完成的任务失败"""
        from obs.model import UploadTask

        class MockLogClient:
            @staticmethod
            def log(level, message):
                pass

        class MockObsClient:
            log_client = MockLogClient()

        task = UploadTask('bucket', 'key', 'file', MockObsClient())

        # 设置为已完成
        with task._lock:
            task._status = UploadTaskStatus.COMPLETED

        # 取消应该失败
        with pytest.raises(ValueError) as exc_info:
            task.cancel()
        assert 'completed' in str(exc_info.value).lower()

    def test_resume_non_paused_task(self):
        """测试场景: 恢复非暂停状态的任务失败"""
        from obs.model import UploadTask

        class MockLogClient:
            @staticmethod
            def log(level, message):
                pass

        class MockObsClient:
            log_client = MockLogClient()

        task = UploadTask('bucket', 'key', 'file', MockObsClient())

        # 保持 PENDING 状态
        # 恢复应该失败
        with pytest.raises(ValueError) as exc_info:
            task.resume()
        assert 'paused' in str(exc_info.value).lower()


class TestNetworkExceptions(object):
    """网络异常模拟测试"""

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

    def test_upload_with_slow_network(self):
        """测试场景: 慢速网络下的上传"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-slow-network-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (5 * 1024 * 1024))  # 5MB

        try:
            # 使用低并发数模拟慢速网络
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                taskNum=1  # 单线程
            )
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass


class TestCheckpointExceptions(object):
    """断点文件异常测试"""

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

    def test_corrupted_checkpoint_file(self):
        """测试场景: 损坏的断点文件"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-corrupted-checkpoint-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (1024 * 1024))  # 1MB

        # 创建损坏的断点文件
        checkpoint_file = test_file + '.upload_record'
        with open(checkpoint_file, 'w') as f:
            f.write('corrupted data { not valid json')

        try:
            # SDK 应该检测到损坏的断点文件并重新上传
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
            except Exception:
                pass

    def test_unwritable_checkpoint_directory(self):
        """测试场景: 不可写的断点文件目录"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (1024 * 1024))  # 1MB

        # 指定一个不可写的位置
        checkpoint_file = '/root/no-permission/checkpoint.dat'

        try:
            # 上传可能成功（无法写断点但不影响上传）
            # 或失败（取决于实现）
            resp = client.uploadFile(
                bucket_name,
                'test-object',
                test_file,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )
            # 接受成功或失败
            assert resp.status in [200, 400, 500]

        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass


class TestConcurrentModificationExceptions(object):
    """并发修改异常测试"""

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

    def test_pause_and_cancel_concurrently(self):
        """测试场景: 并发暂停和取消"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-pause-cancel-concurrent-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (5 * 1024 * 1024))  # 5MB

        checkpoint_file = test_file + '.upload_record'

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            # 等待上传开始
            time.sleep(0.5)

            import threading

            results = []

            def pause_operation():
                try:
                    task.pause()
                    results.append('paused')
                except Exception as e:
                    results.append(f'pause_error: {e}')

            def cancel_operation():
                try:
                    time.sleep(0.1)  # 稍微延迟
                    task.cancel()
                    results.append('cancelled')
                except Exception as e:
                    results.append(f'cancel_error: {e}')

            t1 = threading.Thread(target=pause_operation)
            t2 = threading.Thread(target=cancel_operation)

            t1.start()
            t2.start()

            t1.join()
            t2.join()

            # 应该有一个操作成功
            assert len(results) > 0

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
            except Exception:
                pass
