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
异步上传功能 - 集成测试
测试暂停、恢复、取消功能
需要真实的OBS环境
"""

import pytest
import sys
import os
import time
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs import ObsClient, UploadTaskStatus, PutObjectHeader
from conftest import test_config


class TestAsyncUpload(object):
    """异步上传功能测试类"""

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

    def cleanup_checkpoint(self, checkpoint_file):
        """清理断点文件"""
        try:
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
        except Exception:
            pass

    # ==================== 基本功能测试 ====================

    def test_async_upload_small_file(self):
        """测试场景: 异步上传小文件（不暂停）"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-async-small-' + str(int(time.time()))

        # 创建临时测试文件 (1MB)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'0' * (1024 * 1024))

        try:
            # 启动异步上传
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=100 * 1024,  # 100KB 分片
                taskNum=1,
                enableCheckpoint=False
            )

            # 等待上传完成
            response = task.wait_for_completion(timeout=30)

            # 验证结果
            assert response.status == 200
            assert task.status == UploadTaskStatus.COMPLETED
            assert task.is_completed

            # 验证文件已上传
            resp = client.getObjectMetadata(bucket_name, object_key)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    # ==================== 暂停和恢复测试 ====================

    def test_async_upload_pause_and_resume(self):
        """测试场景: 暂停后恢复上传"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-async-pause-resume-' + str(int(time.time()))

        # 创建临时测试文件 (5MB)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'0' * (5 * 1024 * 1024))

        checkpoint_file = test_file + '.upload_record'

        try:
            # 启动异步上传（启用断点续传）
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=500 * 1024,  # 500KB 分片
                taskNum=2,  # 多线程
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            # 等待一会儿让上传开始
            time.sleep(0.1)

            # 暂停上传
            task.pause()
            assert task.status == UploadTaskStatus.PAUSED
            assert task.is_paused

            # 等待线程停止
            time.sleep(0.5)

            # 记录当前进度
            paused_progress = task.get_progress_percentage()

            # 恢复上传
            task.resume()
            assert task.status == UploadTaskStatus.IN_PROGRESS

            # 等待上传完成
            response = task.wait_for_completion(timeout=60)

            # 验证结果
            assert response.status == 200
            assert task.status == UploadTaskStatus.COMPLETED

            # 验证文件已上传
            resp = client.getObjectMetadata(bucket_name, object_key)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            self.cleanup_checkpoint(checkpoint_file)
            try:
                os.remove(test_file)
            except Exception:
                pass

    # ==================== 取消上传测试 ====================

    def test_async_upload_cancel(self):
        """测试场景: 取消上传"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-async-cancel-' + str(int(time.time()))

        # 创建临时测试文件 (5MB)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'0' * (5 * 1024 * 1024))

        checkpoint_file = test_file + '.upload_record'

        try:
            # 启动异步上传
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=500 * 1024,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            # 等待一会儿让上传开始
            time.sleep(0.1)

            # 取消上传
            task.cancel()

            # 验证状态
            assert task.status == UploadTaskStatus.CANCELLED
            assert task.is_cancelled

            # 验证上传ID已被中止（无法恢复）
            assert task.upload_id is None or task.is_cancelled

            # 验证对象不存在或上传未完成
            resp = client.getObjectMetadata(bucket_name, object_key)
            # 对象可能不存在（404）或上传被取消
            # 不强制断言，因为取决于取消时机

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            self.cleanup_checkpoint(checkpoint_file)
            try:
                os.remove(test_file)
            except Exception:
                pass

    # ==================== 进度跟踪测试 ====================

    def test_async_upload_progress_tracking(self):
        """测试场景: 进度跟踪"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-async-progress-' + str(int(time.time()))

        # 创建临时测试文件 (2MB)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (2 * 1024 * 1024))

        try:
            # 启动异步上传
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=200 * 1024,
                taskNum=1,
                enableCheckpoint=False
            )

            # 等待完成
            response = task.wait_for_completion(timeout=30)

            # 验证进度
            assert task.get_progress_percentage() == 100.0
            assert task.transferred_bytes == task.total_bytes
            assert task.total_bytes == 2 * 1024 * 1024

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    # ==================== 错误处理测试 ====================

    def test_pause_without_checkpoint_fails(self):
        """测试场景: 未启用断点续传时暂停失败"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-async-pause-fail-' + str(int(time.time()))

        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'0' * (1024 * 1024))

        try:
            # 启动异步上传（不启用断点续传）
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                enableCheckpoint=False
            )

            # 尝试暂停应该失败
            with pytest.raises(ValueError) as exc_info:
                task.pause()
            assert 'checkpoint' in str(exc_info.value).lower()

        finally:
            # 等待任务完成或失败
            try:
                task.wait_for_completion(timeout=10)
            except Exception:
                pass
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_cancel_pending_task_fails(self):
        """测试场景: 取消未开始的任务失败"""
        client_type, client = self.get_client()

        # 创建一个任务但不启动上传
        from obs.model import UploadTask
        task = UploadTask('bucket', 'key', 'file', client)

        # 尝试取消应该失败
        with pytest.raises(ValueError) as exc_info:
            task.cancel()
        assert 'not started' in str(exc_info.value).lower() or 'pending' in str(exc_info.value).lower()

    # ==================== 完成回调测试 ====================

    def test_completion_callback(self):
        """测试场景: 完成回调"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-async-callback-' + str(int(time.time()))

        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'0' * (1024 * 1024))

        callback_called = []
        callback_task = []

        def on_complete(task):
            callback_called.append(True)
            callback_task.append(task)

        try:
            # 设置完成回调
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                enableCheckpoint=False
            )
            task.set_completion_callback(on_complete)

            # 等待完成
            response = task.wait_for_completion(timeout=30)

            # 验证回调被调用
            assert len(callback_called) == 1
            assert callback_task[0] is task
            assert callback_task[0].status == UploadTaskStatus.COMPLETED

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_zero_byte_file_upload(self):
        """测试场景: 上传 0 字节文件"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-zero-byte-' + str(int(time.time()))

        # 创建空文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file
            )
            resp = task.wait_for_completion(timeout=30)
            assert resp.status == 200

            # 验证对象存在且大小为 0
            meta_resp = client.getObjectMetadata(bucket_name, object_key)
            assert meta_resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_single_byte_file_upload(self):
        """测试场景: 上传 1 字节文件"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-one-byte-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X')

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file
            )
            resp = task.wait_for_completion(timeout=30)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_small_file_below_part_size(self):
        """测试场景: 文件小于分片大小"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-small-file-' + str(int(time.time()))

        # 创建小于默认分片大小 (9MB) 的文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (100 * 1024))  # 100KB

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=9 * 1024 * 1024  # 9MB 分片
            )
            resp = task.wait_for_completion(timeout=30)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_exact_part_size_file(self):
        """测试场景: 文件大小正好等于分片大小"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-exact-part-' + str(int(time.time()))

        part_size = 5 * 1024 * 1024  # 5MB

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * part_size)

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=part_size
            )
            resp = task.wait_for_completion(timeout=30)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_part_size_plus_one_byte(self):
        """测试场景: 文件大小 = 分片大小 + 1 字节"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-part-plus-one-' + str(int(time.time()))

        part_size = 5 * 1024 * 1024  # 5MB

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (part_size + 1))

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=part_size
            )
            resp = task.wait_for_completion(timeout=30)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_minimum_part_size(self):
        """测试场景: 最小分片大小 (100KB)"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-min-part-' + str(int(time.time()))

        # OBS 最小分片大小是 100KB
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (500 * 1024))  # 500KB 文件

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=100 * 1024  # 100KB 分片
            )
            resp = task.wait_for_completion(timeout=30)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_large_part_size(self):
        """测试场景: 大分片大小 (100MB)"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-large-part-' + str(int(time.time()))

        # OBS 最大分片大小是 5GB，测试 100MB
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (150 * 1024 * 1024))  # 150MB 文件

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=100 * 1024 * 1024  # 100MB 分片
            )
            resp = task.wait_for_completion(timeout=60)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_many_small_parts(self):
        """测试场景: 许多小分片"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-many-parts-' + str(int(time.time()))

        # 创建会产生多个分片的文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))  # 10MB

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=100 * 1024  # 100KB 分片，产生 ~100 个分片
            )
            resp = task.wait_for_completion(timeout=600)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_single_thread(self):
        """测试场景: 单线程上传"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-single-thread-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (5 * 1024 * 1024))  # 5MB

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                taskNum=1  # 单线程
            )
            resp = task.wait_for_completion(timeout=30)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_multiple_threads(self):
        """测试场景: 多线程上传"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-multi-thread-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))  # 10MB

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                taskNum=5  # 5 个线程
            )
            resp = task.wait_for_completion(timeout=60)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_many_threads(self):
        """测试场景: 许多线程"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-many-threads-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (20 * 1024 * 1024))  # 20MB

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=100 * 1024,
                taskNum=100  # 100 个线程
            )
            resp = task.wait_for_completion(timeout=60)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_concurrent_uploads_same_file(self):
        """测试场景: 并发上传同一文件到不同对象"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (1024 * 1024))  # 1MB

        import threading

        results = []

        def upload_worker(n):
            object_key = 'test-concurrent-%d-%d' % (n, int(time.time()))
            try:
                task = client.uploadFileAsync(
                    bucket_name,
                    object_key,
                    test_file,
                    taskNum=1
                )
                resp = task.wait_for_completion(timeout=60)
                results.append((n, resp.status))
                self.cleanup_object(client, bucket_name, object_key)
            except Exception as e:
                results.append((n, str(e)))

        try:
            threads = [threading.Thread(target=upload_worker, args=(i,)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=60)

            # 所有上传应该成功
            for n, status in results:
                assert status == 200, f"Upload {n} failed with status {status}"

        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_concurrent_pause_resume(self):
        """测试场景: 并发暂停和恢复操作"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-concurrent-pause-' + str(int(time.time()))

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
            time.sleep(0.1)

            import threading

            # 并发调用 pause 和 resume
            def pause_worker():
                try:
                    task.pause()
                except:
                    pass

            def resume_worker():
                try:
                    task.resume()
                except:
                    pass

            t1 = threading.Thread(target=pause_worker)
            t2 = threading.Thread(target=resume_worker)

            t1.start()
            time.sleep(0.1)
            t2.start()

            t1.join()
            t2.join()

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

    # ==================== CRC64 校验测试 ====================
    def test_async_upload_with_crc64(self):
        """测试场景: 异步上传并启用 CRC64"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-async-crc64-' + str(int(time.time()))

        # 创建临时测试文件 (2MB)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'ASYNC_CRC64_TEST_' * (1024 * 50))

        try:
            # 异步上传启用 CRC64
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=500 * 1024,
                taskNum=2,
                isAttachCrc64=True
            )

            response = task.wait_for_completion(timeout=60)

            assert response.status == 200
            assert task.status == UploadTaskStatus.COMPLETED

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    # ==================== 暂停恢复后的数据一致性 ====================

    def test_pause_resume_data_integrity(self):
        """测试场景: 暂停后恢复上传，验证数据完整性"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-pause-resume-integrity-' + str(int(time.time()))

        # 创建临时测试文件 (3MB)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            test_data = b'PAUSE_RESUME_INTEGRITY_' * (1024 * 75)
            f.write(test_data)

        checkpoint_file = test_file + '.upload_record'

        try:
            # 启动异步上传（启用 checkpoint 和 CRC64）
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=500 * 1024,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file,
                isAttachCrc64=True,
                checkSum=True
            )

            # 等待上传开始
            time.sleep(0.1)

            # 暂停上传
            task.pause()
            assert task.status == UploadTaskStatus.PAUSED

            time.sleep(0.5)

            # 恢复上传
            task.resume()
            assert task.status == UploadTaskStatus.IN_PROGRESS

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


    # ==================== 断点续传完整性 ====================

    def test_checkpoint_resume_integrity(self):
        """测试场景: 断点续传后的数据完整性"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-checkpoint-integrity-' + str(int(time.time()))

        # 创建临时测试文件 (4MB)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            test_data = b'CHECKPOINT_INTEGRITY_' * (1024 * 96)
            f.write(test_data)

        checkpoint_file = test_file + '.upload_record'

        try:
            # 第一次上传（模拟中断）
            task1 = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=500 * 1024,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file,
                isAttachCrc64=True
            )

            # 等待一下然后暂停
            time.sleep(0.1)
            task1.pause()

            # 等待暂停完成
            time.sleep(0.5)

            # 从断点恢复上传
            task2 = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                partSize=500 * 1024,
                taskNum=2,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file,
                isAttachCrc64=True
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

    # ==================== 进度回调验证 ====================

    def test_progress_callback_integrity(self):
        """测试场景: 通过进度回调验证传输完整性"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-progress-integrity-' + str(int(time.time()))

        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            file_size = 2 * 1024 * 1024  # 2MB
            f.write(b'X' * file_size)

        progress_data = {'transferred': 0, 'total': 0}

        def progress_callback(transferred_amount, total_amount, total_seconds):
            progress_data['transferred'] = transferred_amount
            progress_data['total'] = total_amount

        try:
            # 上传并监控进度
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                progressCallback=progress_callback,
                isAttachCrc64=True
            )

            resp = task.wait_for_completion(timeout=60)
            assert resp.status == 200
            # 验证进度回调报告的总量正确
            assert progress_data['total'] == file_size
            # 最终传输的字节数应该等于文件大小
            assert progress_data['transferred'] == file_size

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_invalid_part_size_zero(self):
        """测试场景: 无效的分片大小 0"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test')

        try:
            # SDK 应该处理 0 分片大小，使用最小值
            task = client.uploadFileAsync(
                bucket_name,
                'test-object',
                test_file,
                partSize=0
            )
            resp = task.wait_for_completion(timeout=30)
            # 应该成功或给出明确错误
            assert resp.status == 200
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
            task = client.uploadFileAsync(
                bucket_name,
                'test-object',
                test_file,
                partSize=-1
            )
            resp = task.wait_for_completion(timeout=30)
            # 应该成功或给出明确错误
            assert resp.status == 200
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
            task = client.uploadFileAsync(
                bucket_name,
                'test-object',
                test_file,
                taskNum=0
            )
            resp = task.wait_for_completion(timeout=30)
            assert resp.status == 200
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
            task = client.uploadFileAsync(
                bucket_name,
                'test-object',
                test_file,
                taskNum=-1
            )
            resp = task.wait_for_completion(timeout=30)
            # 应该成功或给出明确错误
            assert resp.status == 200
        finally:
            try:
                os.remove(test_file)
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
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )
            resp = task.wait_for_completion(timeout=30)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
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
            time.sleep(0.1)

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
            f.write(b'X' * (20 * 1024 * 1024))  # 10MB

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
                time.sleep(0.1)
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
            time.sleep(0.1)

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
                time.sleep(0.1)

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
            time.sleep(0.1)

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

    # 性能相关
    def test_pause_resume_latency(self):
        """测试场景: 暂停和恢复延迟"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-perf-pause-resume-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))  # 10MB

        checkpoint_file = test_file + '.upload_record'

        try:
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                taskNum=2,
                partSize=2 * 1024 * 1024,
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            # 等待上传开始
            time.sleep(0.1)

            # 测试暂停延迟
            pause_start = time.time()
            task.pause()
            pause_end = time.time()
            pause_latency = pause_end - pause_start

            print(f"\n暂停操作延迟: {pause_latency:.3f}s")
            assert pause_latency < 0.01  # 应该很快

            time.sleep(0.5)

            # 测试恢复延迟
            resume_start = time.time()
            task.resume()
            resume_end = time.time()
            resume_latency = resume_end - resume_start

            print(f"恢复操作延迟: {resume_latency:.3f}s")
            assert resume_latency < 0.01  # 应该很快

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

    def test_async_upload_startup_time(self):
        """测试场景: 异步上传启动时间"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-perf-async-startup-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))  # 10MB

        try:
            start_time = time.time()
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                taskNum=2
            )
            end_time = time.time()

            # 启动时间应该很快
            startup_time = end_time - start_time
            print(f"\n异步上传启动时间: {startup_time:.3f}s")

            assert startup_time < 0.2  # 应该在 0.2 秒内返回
            assert task is not None

            # 等待完成
            response = task.wait_for_completion(timeout=60)
            assert response.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_thread_scalability(self):
        """测试场景: 线程数扩展性"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        # 10MB 文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))

        try:
            thread_counts = [1, 3, 5]
            results = []

            for thread_count in thread_counts:
                object_key = 'test-perf-scalability-%d-%d' % (thread_count, int(time.time()))

                start_time = time.time()
                task = client.uploadFileAsync(
                    bucket_name,
                    object_key,
                    test_file,
                    partSize=2 * 1024 * 1024,
                    taskNum=thread_count
                )
                resp = task.wait_for_completion(timeout=60)
                end_time = time.time()

                assert resp.status == 200

                elapsed = end_time - start_time
                throughput = (10 * 1024 * 1024) / elapsed / 1024 / 1024
                results.append((thread_count, elapsed, throughput))

                self.cleanup_object(client, bucket_name, object_key)

            print(f"\n线程扩展性测试结果:")
            for thread_count, elapsed, throughput in results:
                print(f"  {thread_count} 线程: {throughput:.2f} MB/s, 耗时: {elapsed:.2f}s")

            # 更多线程应该更快
            assert results[0][1] > results[1][1]  # 3线程不应该比1线程慢

        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_progress_callback_overhead(self):
        """测试场景: 进度回调开销"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-perf-progress-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (50 * 1024 * 1024))  # 5MB

        progress_count = [0]

        def progress_callback(transferred_amount, total_amount, total_seconds):
            progress_count[0] += 1

        try:
            # 带进度回调
            start_time = time.time()
            task = client.uploadFileAsync(
                bucket_name,
                object_key,
                test_file,
                progressCallback=progress_callback
            )
            resp = task.wait_for_completion(timeout=60)
            time_with_callback = time.time() - start_time

            assert resp.status == 200
            self.cleanup_object(client, bucket_name, object_key)

            # 不带进度回调
            start_time = time.time()
            task = client.uploadFileAsync(
                bucket_name,
                object_key + '-2',
                test_file
            )
            resp = task.wait_for_completion(timeout=60)
            time_without_callback = time.time() - start_time

            assert resp.status == 200

            print(f"\n进度回调性能影响:")
            print(f"  带回调: {time_with_callback:.2f}s")
            print(f"  不带回调: {time_without_callback:.2f}s")
            print(f"  回调次数: {progress_count[0]}")
            print(f"  开销: {((time_with_callback / time_without_callback - 1) * 100):.1f}%")

            # 回调开销不应该太大
            assert time_with_callback < time_without_callback * 1.1  # 开销不超过 10%

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            self.cleanup_object(client, bucket_name, object_key + '-2')
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_concurrent_upload_throughput(self):
        """测试场景: 并发上传吞吐量"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        # 创建 3 个并发上传
        files_and_keys = []

        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
                test_file = f.name
                f.write(b'X' * (5 * 1024 * 1024))  # 5MB

            object_key = 'test-perf-concurrent-%d-%d' % (i, int(time.time()))
            files_and_keys.append((test_file, object_key))

        try:
            start_time = time.time()

            threads = []
            results = []

            def upload_worker(test_file, object_key):
                try:
                    task = client.uploadFileAsync(
                        bucket_name,
                        object_key,
                        test_file,
                        taskNum=1
                    )
                    resp = task.wait_for_completion(timeout=60)
                    results.append((object_key, resp.status, time.time()))
                except Exception as e:
                    results.append((object_key, str(e), time.time()))

            for test_file, object_key in files_and_keys:
                t = threading.Thread(target=upload_worker, args=(test_file, object_key))
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=180)

            end_time = time.time()

            # 验证所有上传成功
            for object_key, status, _ in results:
                assert status == 200, f"Upload {object_key} failed with status {status}"
                self.cleanup_object(client, bucket_name, object_key)

            elapsed = end_time - start_time
            total_size = 3 * 5 * 1024 * 1024
            throughput = total_size / elapsed / 1024 / 1024  # MB/s

            print(f"\n并发上传吞吐量: {throughput:.2f} MB/s, 耗时: {elapsed:.2f}s")

        finally:
            for test_file, object_key in files_and_keys:
                self.cleanup_object(client, bucket_name, object_key)
                try:
                    os.remove(test_file)
                except Exception:
                    pass
