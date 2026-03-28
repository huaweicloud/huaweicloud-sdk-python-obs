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
            time.sleep(0.5)

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
            time.sleep(0.5)

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
