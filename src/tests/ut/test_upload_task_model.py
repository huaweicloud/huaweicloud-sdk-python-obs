#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# UploadTask 模型类单元测试
# TDD Red 阶段 - 测试先行

import pytest
import threading
import time


class TestUploadTaskStatus(object):
    """UploadTaskStatus 枚举类单元测试"""

    def test_status_enum_exists(self):
        """测试状态枚举存在"""
        from obs.model import UploadTaskStatus

        assert hasattr(UploadTaskStatus, 'PENDING')
        assert hasattr(UploadTaskStatus, 'IN_PROGRESS')
        assert hasattr(UploadTaskStatus, 'PAUSED')
        assert hasattr(UploadTaskStatus, 'COMPLETED')
        assert hasattr(UploadTaskStatus, 'CANCELLED')
        assert hasattr(UploadTaskStatus, 'FAILED')

    def test_status_enum_values(self):
        """测试状态枚举值"""
        from obs.model import UploadTaskStatus

        assert UploadTaskStatus.PENDING == 'pending'
        assert UploadTaskStatus.IN_PROGRESS == 'in_progress'
        assert UploadTaskStatus.PAUSED == 'paused'
        assert UploadTaskStatus.COMPLETED == 'completed'
        assert UploadTaskStatus.CANCELLED == 'cancelled'
        assert UploadTaskStatus.FAILED == 'failed'


class TestUploadTaskCreation(object):
    """UploadTask 创建测试"""

    def setup_method(self):
        """设置测试环境"""
        # Mock ObsClient
        class MockLogClient:
            @staticmethod
            def log(level, message):
                pass

        class MockObsClient:
            log_client = MockLogClient()

        self.MockObsClient = MockObsClient

    def test_basic_creation(self):
        """测试基本创建"""
        from obs.model import UploadTask

        task = UploadTask('test-bucket', 'test-key', '/path/to/file', self.MockObsClient())

        assert task is not None
        assert task.bucket_name == 'test-bucket'
        assert task.object_key == 'test-key'
        assert task.upload_file == '/path/to/file'

    def test_default_status(self):
        """测试默认状态"""
        from obs.model import UploadTask, UploadTaskStatus

        task = UploadTask('bucket', 'key', 'file', self.MockObsClient())

        assert task.status == UploadTaskStatus.PENDING
        assert task.upload_id is None
        assert task.transferred_bytes == 0
        assert task.total_bytes == 0

    def test_status_properties(self):
        """测试状态属性"""
        from obs.model import UploadTask, UploadTaskStatus

        task = UploadTask('bucket', 'key', 'file', self.MockObsClient())

        assert task.is_pending is True
        assert task.is_in_progress is False
        assert task.is_paused is False
        assert task.is_completed is False
        assert task.is_cancelled is False
        assert task.is_failed is False


class TestUploadTaskPause(object):
    """UploadTask 暂停功能测试"""

    def setup_method(self):
        """设置测试环境"""
        class MockLogClient:
            @staticmethod
            def log(level, message):
                pass

        class MockObsClient:
            log_client = MockLogClient()

        self.MockObsClient = MockObsClient

    def test_pause_pending_task_fails(self):
        """测试 PENDING 状态不能暂停"""
        from obs.model import UploadTask

        task = UploadTask('bucket', 'key', 'file', self.MockObsClient())

        with pytest.raises(ValueError) as exc_info:
            task.pause()
        assert 'not started' in str(exc_info.value).lower() or 'pending' in str(exc_info.value).lower()

    def test_pause_without_checkpoint_fails(self):
        """测试没有 checkpoint 时不能暂停"""
        from obs.model import UploadTask, UploadTaskStatus

        task = UploadTask('bucket', 'key', 'file', self.MockObsClient())

        # 模拟设置为 IN_PROGRESS 状态但没有 enable_checkpoint
        with task._lock:
            task._status = UploadTaskStatus.IN_PROGRESS

        with pytest.raises(ValueError) as exc_info:
            task.pause()
        assert 'checkpoint' in str(exc_info.value).lower()


class TestUploadTaskCancel(object):
    """UploadTask 取消功能测试"""

    def setup_method(self):
        """设置测试环境"""
        class MockLogClient:
            @staticmethod
            def log(level, message):
                pass

        class MockObsClient:
            log_client = MockLogClient()

        self.MockObsClient = MockObsClient

    def test_cancel_pending_task_fails(self):
        """测试 PENDING 状态不能取消"""
        from obs.model import UploadTask

        task = UploadTask('bucket', 'key', 'file', self.MockObsClient())

        with pytest.raises(ValueError) as exc_info:
            task.cancel()
        assert 'not started' in str(exc_info.value).lower() or 'pending' in str(exc_info.value).lower()


class TestUploadTaskProgress(object):
    """UploadTask 进度跟踪测试"""

    def setup_method(self):
        """设置测试环境"""
        class MockLogClient:
            @staticmethod
            def log(level, message):
                pass

        class MockObsClient:
            log_client = MockLogClient()

        self.MockObsClient = MockObsClient

    def test_progress_percentage(self):
        """测试进度百分比计算"""
        from obs.model import UploadTask

        task = UploadTask('bucket', 'key', 'file', self.MockObsClient())

        # 模拟进度更新
        with task._lock:
            task._transferred_bytes = 500
            task._total_bytes = 1000

        assert task.transferred_bytes == 500
        assert task.total_bytes == 1000
        assert task.get_progress_percentage() == 50.0

    def test_progress_zero_bytes(self):
        """测试零字节进度"""
        from obs.model import UploadTask

        task = UploadTask('bucket', 'key', 'file', self.MockObsClient())

        assert task.get_progress_percentage() == 0.0


class TestUploadTaskThreadSafety(object):
    """UploadTask 线程安全测试"""

    def setup_method(self):
        """设置测试环境"""
        class MockLogClient:
            @staticmethod
            def log(level, message):
                pass

        class MockObsClient:
            log_client = MockLogClient()

        self.MockObsClient = MockObsClient

    def test_concurrent_status_access(self):
        """测试并发状态访问"""
        from obs.model import UploadTask

        task = UploadTask('bucket', 'key', 'file', self.MockObsClient())

        def access_status():
            for _ in range(100):
                _ = task.status

        threads = [threading.Thread(target=access_status) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 应该没有异常抛出
        assert True

    def test_concurrent_progress_update(self):
        """测试并发进度更新"""
        from obs.model import UploadTask

        task = UploadTask('bucket', 'key', 'file', self.MockObsClient())

        def update_progress():
            for _ in range(100):
                with task._lock:
                    task._transferred_bytes += 1

        threads = [threading.Thread(target=update_progress) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert task.transferred_bytes == 500


class TestUploadTaskWaitCompletion(object):
    """UploadTask 等待完成测试"""

    def setup_method(self):
        """设置测试环境"""
        class MockLogClient:
            @staticmethod
            def log(level, message):
                pass

        class MockObsClient:
            log_client = MockLogClient()

        self.MockObsClient = MockObsClient

    def test_wait_timeout(self):
        """测试等待超时"""
        from obs.model import UploadTask

        task = UploadTask('bucket', 'key', 'file', self.MockObsClient())

        with pytest.raises(TimeoutError):
            task.wait_for_completion(timeout=0.1)
