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
性能测试 - 集成测试
测试上传下载性能指标
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


class TestUploadPerformance(object):
    """上传性能测试"""

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

    def test_small_file_upload_speed(self):
        """测试场景: 小文件上传速度"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-perf-small-' + str(int(time.time()))

        # 1MB 文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (1024 * 1024))

        try:
            start_time = time.time()
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file
            )
            end_time = time.time()

            assert resp.status == 200

            elapsed = end_time - start_time
            throughput = (1024 * 1024) / elapsed / 1024 / 1024  # MB/s

            print(f"\n小文件上传性能: {throughput:.2f} MB/s, 耗时: {elapsed:.2f}s")

            # 性能应该在合理范围内
            assert elapsed < 30  # 不应该超过 30 秒

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_medium_file_upload_speed(self):
        """测试场景: 中等文件上传速度"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-perf-medium-' + str(int(time.time()))

        # 10MB 文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))

        try:
            start_time = time.time()
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=5 * 1024 * 1024,
                taskNum=3
            )
            end_time = time.time()

            assert resp.status == 200

            elapsed = end_time - start_time
            throughput = (10 * 1024 * 1024) / elapsed / 1024 / 1024  # MB/s

            print(f"\n中等文件上传性能: {throughput:.2f} MB/s, 耗时: {elapsed:.2f}s")

            # 性能检查
            assert elapsed < 60  # 不应该超过 60 秒

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_multipart_upload_performance(self):
        """测试场景: 多段上传性能"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-perf-multipart-' + str(int(time.time()))

        # 20MB 文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (20 * 1024 * 1024))

        try:
            start_time = time.time()
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=5 * 1024 * 1024,
                taskNum=5,
                isAttachCrc64=True
            )
            end_time = time.time()

            assert resp.status == 200

            elapsed = end_time - start_time
            throughput = (20 * 1024 * 1024) / elapsed / 1024 / 1024  # MB/s

            print(f"\n多段上传性能: {throughput:.2f} MB/s, 耗时: {elapsed:.2f}s")

            # 性能检查
            assert elapsed < 120  # 不应该超过 2 分钟

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass


class TestAsyncUploadPerformance(object):
    """异步上传性能测试"""

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

            assert startup_time < 1.0  # 应该在 1 秒内返回
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
                enableCheckpoint=True,
                checkpointFile=checkpoint_file
            )

            # 等待上传开始
            time.sleep(0.5)

            # 测试暂停延迟
            pause_start = time.time()
            task.pause()
            pause_end = time.time()
            pause_latency = pause_end - pause_start

            print(f"\n暂停操作延迟: {pause_latency:.3f}s")
            assert pause_latency < 1.0  # 应该很快

            time.sleep(0.5)

            # 测试恢复延迟
            resume_start = time.time()
            task.resume()
            resume_end = time.time()
            resume_latency = resume_end - resume_start

            print(f"恢复操作延迟: {resume_latency:.3f}s")
            assert resume_latency < 1.0  # 应该很快

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


class TestConcurrentPerformance(object):
    """并发性能测试"""

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
                    resp = client.uploadFile(
                        bucket_name,
                        object_key,
                        test_file,
                        taskNum=1
                    )
                    results.append((object_key, resp.status, time.time()))
                except Exception as e:
                    results.append((object_key, str(e), time.time()))

            for test_file, object_key in files_and_keys:
                t = threading.Thread(target=upload_worker, args=(test_file, object_key))
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=120)

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


class TestScalabilityPerformance(object):
    """扩展性性能测试"""

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
                resp = client.uploadFile(
                    bucket_name,
                    object_key,
                    test_file,
                    partSize=2 * 1024 * 1024,
                    taskNum=thread_count
                )
                end_time = time.time()

                assert resp.status == 200

                elapsed = end_time - start_time
                throughput = (10 * 1024 * 1024) / elapsed / 1024 / 1024
                results.append((thread_count, elapsed, throughput))

                self.cleanup_object(client, bucket_name, object_key)

            print(f"\n线程扩展性测试结果:")
            for thread_count, elapsed, throughput in results:
                print(f"  {thread_count} 线程: {throughput:.2f} MB/s, 耗时: {elapsed:.2f}s")

            # 更多线程应该更快或至少不慢太多
            assert results[0][1] >= results[1][1] * 0.5  # 3线程不应该比1线程慢2倍以上

        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_part_size_scalability(self):
        """测试场景: 分片大小扩展性"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        # 20MB 文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (20 * 1024 * 1024))

        try:
            part_sizes = [1 * 1024 * 1024, 5 * 1024 * 1024, 10 * 1024 * 1024]
            results = []

            for part_size in part_sizes:
                object_key = 'test-perf-partsize-%d-%d' % (part_size // (1024*1024), int(time.time()))

                start_time = time.time()
                resp = client.uploadFile(
                    bucket_name,
                    object_key,
                    test_file,
                    partSize=part_size,
                    taskNum=3
                )
                end_time = time.time()

                assert resp.status == 200

                elapsed = end_time - start_time
                throughput = (20 * 1024 * 1024) / elapsed / 1024 / 1024
                results.append((part_size, elapsed, throughput))

                self.cleanup_object(client, bucket_name, object_key)

            print(f"\n分片大小扩展性测试结果:")
            for part_size, elapsed, throughput in results:
                print(f"  {part_size // (1024*1024)}MB 分片: {throughput:.2f} MB/s, 耗时: {elapsed:.2f}s")

        finally:
            try:
                os.remove(test_file)
            except Exception:
                pass


class TestProgressPerformance(object):
    """进度性能测试"""

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

    def test_progress_callback_overhead(self):
        """测试场景: 进度回调开销"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-perf-progress-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (5 * 1024 * 1024))  # 5MB

        progress_count = [0]

        def progress_callback(transferred_amount, total_amount, total_seconds):
            progress_count[0] += 1

        try:
            # 带进度回调
            start_time = time.time()
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                progressCallback=progress_callback
            )
            time_with_callback = time.time() - start_time

            assert resp.status == 200
            self.cleanup_object(client, bucket_name, object_key)

            # 不带进度回调
            start_time = time.time()
            resp = client.uploadFile(
                bucket_name,
                object_key + '-2',
                test_file
            )
            time_without_callback = time.time() - start_time

            assert resp.status == 200

            print(f"\n进度回调性能影响:")
            print(f"  带回调: {time_with_callback:.2f}s")
            print(f"  不带回调: {time_without_callback:.2f}s")
            print(f"  回调次数: {progress_count[0]}")
            print(f"  开销: {((time_with_callback / time_without_callback - 1) * 100):.1f}%")

            # 回调开销不应该太大
            assert time_with_callback < time_without_callback * 2  # 开销不超过 100%

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            self.cleanup_object(client, bucket_name, object_key + '-2')
            try:
                os.remove(test_file)
            except Exception:
                pass
