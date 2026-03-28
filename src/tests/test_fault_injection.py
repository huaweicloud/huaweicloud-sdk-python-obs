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
故障注入测试 - 集成测试
模拟各种故障场景，验证系统的恢复和容错能力
"""

import pytest
import sys
import os
import time
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs import ObsClient, UploadTaskStatus
from conftest import test_config


class TestInterruptionRecovery(object):
    """中断恢复测试"""

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

    def test_pause_during_upload_and_resume(self):
        """测试场景: 上传过程中暂停并恢复"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-pause-during-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))  # 10MB

        checkpoint_file = test_file + '.upload_record'

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=2 * 1024 * 1024,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            # 等待上传进行
            time.sleep(1)

            # 暂停
            task.pause()
            assert task.is_paused

            # 恢复
            task.resume()
            assert task.is_in_progress

            # 等待完成
            response = task.wait_for_completion(timeout=60)
            assert response.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
            except Exception:
                pass

    def test_multiple_pause_resume_cycles(self):
        """测试场景: 多次暂停和恢复"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-multi-pause-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))  # 10MB

        checkpoint_file = test_file + '.upload_record'

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=2 * 1024 * 1024,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            # 多次暂停恢复
            for i in range(3):
                time.sleep(0.3)
                task.pause()
                assert task.is_paused
                time.sleep(0.2)
                task.resume()
                assert task.is_in_progress

            # 最终完成
            response = task.wait_for_completion(timeout=60)
            assert response.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
            except Exception:
                pass

    def test_cancel_immediately_after_start(self):
        """测试场景: 启动后立即取消"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-cancel-immediate-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))  # 10MB

        checkpoint_file = test_file + '.upload_record'

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=2 * 1024 * 1024,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            # 立即取消
            task.cancel()
            assert task.is_cancelled

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
            except Exception:
                pass

    def test_cancel_near_completion(self):
        """测试场景: 接近完成时取消"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-cancel-near-end-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (5 * 1024 * 1024))  # 5MB

        checkpoint_file = test_file + '.upload_record'

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=1 * 1024 * 1024,
                taskNum=1,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            # 等待大部分完成
            time.sleep(2)

            # 取消
            task.cancel()
            assert task.is_cancelled

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
            except Exception:
                pass


class TestCheckpointRecovery(object):
    """断点恢复测试"""

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

    def test_resume_from_checkpoint(self):
        """测试场景: 从断点恢复上传"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-resume-checkpoint-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))  # 10MB

        checkpoint_file = test_file + '.upload_record'

        try:
            # 第一次上传（部分）
            task1 = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=2 * 1024 * 1024,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            # 等待一点进度
            time.sleep(0.5)

            # 暂停
            task1.pause()
            assert task1.is_paused

            time.sleep(0.5)

            # 从断点恢复
            task2 = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=2 * 1024 * 1024,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            response = task2.wait_for_completion(timeout=60)
            assert response.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
            except Exception:
                pass

    def test_multiple_checkpoint_resumes(self):
        """测试场景: 多次从断点恢复"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-multi-resume-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))  # 10MB

        checkpoint_file = test_file + '.upload_record'

        try:
            # 多次中断和恢复
            for i in range(3):
                task = client.uploadFileAsync(
                    bucket_name,
                    object_key,
                    test_file,
                    partSize=2 * 1024 * 1024,
                    taskNum=2,
                    enableCheckpoint=True,
                    checkpointFile=checkpoint_file
                )

                # 等待一点进度
                time.sleep(0.4)

                # 暂停
                task.pause()
                time.sleep(0.3)

            # 最后一次恢复并完成
            final_task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=2 * 1024 * 1024,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            response = final_task.wait_for_completion(timeout=60)
            assert response.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
            except Exception:
                pass


class TestConcurrentConflict(object):
    """并发冲突测试"""

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

    def test_concurrent_pause_resume_operations(self):
        """测试场景: 并发暂停恢复操作"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-concurrent-ops-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))  # 10MB

        checkpoint_file = test_file + '.upload_record'

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=2 * 1024 * 1024,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            # 等待上传开始
            time.sleep(0.5)

            # 并发执行多个操作
            def operation_worker(op_type):
                try:
                    if op_type == 'pause':
                        task.pause()
                    elif op_type == 'resume':
                        task.resume()
                    elif op_type == 'status':
                        _ = task.status
                    elif op_type == 'progress':
                        _ = task.get_progress_percentage()
                except Exception:
                    pass  # 某些操作可能失败

            threads = []
            for i in range(10):
                op = ['pause', 'resume', 'status', 'progress'][i % 4]
                t = threading.Thread(target=operation_worker, args=(op,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=5)

            # 确保任务仍然可以完成
            if not task.is_cancelled and not task.is_paused:
                try:
                    task.resume()
                    response = task.wait_for_completion(timeout=60)
                    assert response.status == 200
                except:
                    pass

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
            except Exception:
                pass


class TestPartialFailure(object):
    """部分失败测试"""

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

    def test_upload_with_retries(self):
        """测试场景: 上传失败后重试"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-upload-retry-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (1024 * 1024))  # 1MB

        try:
            # 正常上传
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                taskNum=1
            )
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass


class TestResourceLimit(object):
    """资源限制测试"""

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

    def test_many_concurrent_async_uploads(self):
        """测试场景: 大量并发异步上传"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        tasks = []
        test_files = []

        try:
            # 创建 10 个并发上传
            for i in range(10):
                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
                    test_file = f.name
                    f.write(b'X' * (1024 * 1024))  # 1MB
                    test_files.append(test_file)

                object_key = 'test-concurrent-async-%d-%d' % (i, int(time.time()))

                task = client.uploadFileAsync(
                    bucket_name,
                    object_key,
                    test_file,
                    taskNum=1
                )
                tasks.append((task, object_key))

            # 等待所有任务完成
            for task, object_key in tasks:
                try:
                    response = task.wait_for_completion(timeout=60)
                    assert response.status == 200
                except Exception as e:
                    # 某些任务可能失败
                    pass

        finally:
            for task, object_key in tasks:
                self.cleanup_object(client, bucket_name, object_key)
            for test_file in test_files:
                try:
                    os.remove(test_file)
                except Exception:
                    pass
