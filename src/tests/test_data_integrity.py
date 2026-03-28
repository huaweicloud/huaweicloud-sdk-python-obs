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
数据完整性校验 - 集成测试
测试上传/下载过程中的数据完整性验证
"""

import pytest
import sys
import os
import time
import tempfile
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs import ObsClient, UploadTaskStatus
from conftest import test_config


class TestDataIntegrity(object):
    """数据完整性校验测试类"""

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

    def calculate_file_sha256(self, file_path):
        """计算文件的 SHA256 哈希值"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        return sha256_hash.digest()

    def calculate_file_md5(self, file_path):
        """计算文件的 MD5 哈希值"""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.digest()

    # ==================== CRC64 校验测试 ====================

    def test_upload_with_crc64(self):
        """测试场景: 使用 CRC64 上传文件"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-crc64-upload-' + str(int(time.time()))

        # 创建临时测试文件 (2MB)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            # 使用特定模式的数据便于验证
            f.write(b'CRC64_TEST_DATA_' * (1024 * 60))  # ~2MB

        original_sha256 = self.calculate_file_sha256(test_file)

        try:
            # 使用 CRC64 上传
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=500 * 1024,
                taskNum=2,
                isAttachCrc64=True  # 启用 CRC64
            )

            assert resp.status == 200
            # 响应中可能包含 CRC64
            if hasattr(resp, 'body') and hasattr(resp.body, 'crc64'):
                assert resp.body.crc64 is not None

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

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

    # ==================== SHA256 校验测试 ====================

    def test_upload_with_checksum(self):
        """测试场景: 使用 SHA256 校验和上传"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-checksum-upload-' + str(int(time.time()))

        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            test_data = b'CHECKSUM_TEST_DATA_' * (1024 * 50)
            f.write(test_data)

        original_sha256 = hashlib.sha256(test_data).digest()

        try:
            # 使用 checkSum 参数启用校验
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=500 * 1024,
                checkSum=True,  # 启用 SHA256 校验
                enableCheckpoint=True
            )

            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    # ==================== 上传下载一致性测试 ====================

    def test_upload_download_integrity(self):
        """测试场景: 上传后下载验证数据完整性"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-integrity-' + str(int(time.time()))

        # 创建临时测试文件 (1MB)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            test_data = b'INTEGRITY_TEST_' * (1024 * 60)
            f.write(test_data)

        original_sha256 = hashlib.sha256(test_data).digest()
        original_md5 = hashlib.md5(test_data).digest()

        try:
            # 上传文件
            upload_resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                isAttachCrc64=True
            )
            assert upload_resp.status == 200

            # 下载文件
            download_file = test_file + '.downloaded'
            download_resp = client.downloadFile(
                bucket_name,
                object_key,
                download_file,
                isAttachCrc64=True
            )
            assert download_resp.status == 200

            # 验证下载文件的完整性
            downloaded_sha256 = self.calculate_file_sha256(download_file)
            downloaded_md5 = self.calculate_file_md5(download_file)

            assert downloaded_sha256 == original_sha256, "SHA256 mismatch after download"
            assert downloaded_md5 == original_md5, "MD5 mismatch after download"

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                os.remove(test_file + '.downloaded')
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

        original_sha256 = self.calculate_file_sha256(test_file)
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
            time.sleep(0.5)

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

            # 下载并验证数据完整性
            download_file = test_file + '.downloaded'
            download_resp = client.downloadFile(
                bucket_name,
                object_key,
                download_file,
                isAttachCrc64=True
            )
            assert download_resp.status == 200

            downloaded_sha256 = self.calculate_file_sha256(download_file)
            assert downloaded_sha256 == original_sha256, "Data corrupted after pause/resume"

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                os.remove(download_file)
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
            except Exception:
                pass

    # ==================== 多段上传完整性 ====================

    def test_multipart_upload_integrity(self):
        """测试场景: 多段上传的数据完整性"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-multipart-integrity-' + str(int(time.time()))

        # 创建临时测试文件 (6MB，确保分成多段)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            test_data = b'MULTIPART_INTEGRITY_' * (1024 * 144)
            f.write(test_data)

        original_sha256 = self.calculate_file_sha256(test_file)

        try:
            # 使用小分片大小确保多段上传
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=1 * 1024 * 1024,  # 1MB 分片
                taskNum=3,
                isAttachCrc64=True
            )

            assert resp.status == 200

            # 下载并验证
            download_file = test_file + '.downloaded'
            download_resp = client.downloadFile(
                bucket_name,
                object_key,
                download_file,
                isAttachCrc64=True
            )
            assert download_resp.status == 200

            downloaded_sha256 = self.calculate_file_sha256(download_file)
            assert downloaded_sha256 == original_sha256, "Multipart upload data corrupted"

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                os.remove(download_file)
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

        original_sha256 = self.calculate_file_sha256(test_file)
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
            time.sleep(0.5)
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

            # 验证数据完整性
            download_file = test_file + '.downloaded'
            download_resp = client.downloadFile(
                bucket_name,
                object_key,
                download_file,
                isAttachCrc64=True
            )
            assert download_resp.status == 200

            downloaded_sha256 = self.calculate_file_sha256(download_file)
            assert downloaded_sha256 == original_sha256, "Checkpoint resume data corrupted"

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                os.remove(download_file)
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
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                progressCallback=progress_callback,
                isAttachCrc64=True
            )

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

    # ==================== 大文件完整性 ====================

    def test_large_file_integrity(self):
        """测试场景: 大文件上传下载的完整性"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-large-file-integrity-' + str(int(time.time()))

        # 创建较大的测试文件 (10MB)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            # 使用模式生成可验证的数据
            for i in range(1024 * 2560):
                f.write(b'LARGE_FILE_TEST_%04d' % (i % 10000))

        original_sha256 = self.calculate_file_sha256(test_file)

        try:
            # 上传大文件
            upload_resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=2 * 1024 * 1024,  # 2MB 分片
                taskNum=3,
                isAttachCrc64=True,
                enableCheckpoint=True
            )
            assert upload_resp.status == 200

            # 下载大文件
            download_file = test_file + '.downloaded'
            download_resp = client.downloadFile(
                bucket_name,
                object_key,
                download_file,
                partSize=2 * 1024 * 1024,
                taskNum=3,
                isAttachCrc64=True
            )
            assert download_resp.status == 200

            # 验证完整性
            downloaded_sha256 = self.calculate_file_sha256(download_file)
            assert downloaded_sha256 == original_sha256, "Large file data corrupted"

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
                os.remove(download_file)
            except Exception:
                pass
