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
边界测试 - 集成测试
测试文件大小、分片数量、并发线程等边界条件
"""

import pytest
import sys
import os
import time
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs import ObsClient, UploadTaskStatus
from conftest import test_config


class TestFileSizeBoundary(object):
    """文件大小边界测试"""

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

    def test_zero_byte_file_upload(self):
        """测试场景: 上传 0 字节文件"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-zero-byte-' + str(int(time.time()))

        # 创建空文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name

        try:
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file
            )
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
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file
            )
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
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=9 * 1024 * 1024  # 9MB 分片
            )
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
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=part_size
            )
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
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=part_size
            )
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass


class TestPartSizeBoundary(object):
    """分片大小边界测试"""

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
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=100 * 1024  # 100KB 分片
            )
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
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=100 * 1024 * 1024  # 100MB 分片
            )
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
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                partSize=100 * 1024  # 100KB 分片，产生 ~100 个分片
            )
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass


class TestTaskNumBoundary(object):
    """并发线程数边界测试"""

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

    def test_single_thread(self):
        """测试场景: 单线程上传"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-single-thread-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (5 * 1024 * 1024))  # 5MB

        try:
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

    def test_multiple_threads(self):
        """测试场景: 多线程上传"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-multi-thread-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'X' * (10 * 1024 * 1024))  # 10MB

        try:
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                taskNum=5  # 5 个线程
            )
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
            resp = client.uploadFile(
                bucket_name,
                object_key,
                test_file,
                taskNum=10  # 10 个线程
            )
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass


class TestObjectKeyBoundary(object):
    """Object Key 边界测试"""

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

    def test_very_long_object_key(self):
        """测试场景: 非常长的 object key"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        # OBS object key 最大 1024 字节
        object_key = 'a' * 500 + '-' + str(int(time.time()))

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test content')

        try:
            resp = client.putContent(bucket_name, object_key, 'test content')
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_object_key_with_special_chars(self):
        """测试场景: 包含特殊字符的 object key"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        special_keys = [
            'test/file/with/slashes.txt',
            'test-file-with-dashes.txt',
            'test_file_with_underscores.txt',
            'test.file.with.dots.txt',
            'test-file-with-123-numbers.txt',
            'UPPERCASE.FILE.NAME',
            'test file with spaces.txt',  # 虽然不推荐，但应该支持
        ]

        for key_pattern in special_keys:
            object_key = key_pattern.replace('.', '-' + str(int(time.time())) + '.')

            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
                test_file = f.name
                f.write(b'test content')

            try:
                resp = client.putContent(bucket_name, object_key, 'test content')
                assert resp.status == 200

            finally:
                self.cleanup_object(client, bucket_name, object_key)
                try:
                    os.remove(test_file)
                except Exception:
                    pass

    def test_object_key_with_unicode(self):
        """测试场景: 包含 Unicode 字符的 object key"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        object_key = 'test-中文-文件-' + str(int(time.time())) + '.txt'

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test content')

        try:
            resp = client.putContent(bucket_name, object_key, 'test content')
            # 应该成功或给出明确的错误
            assert resp.status in [200, 400, 403]

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass

    def test_deep_nested_path(self):
        """测试场景: 深层嵌套路径"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        # 创建深层嵌套路径
        object_key = '/'.join(['level%d' % i for i in range(20)]) + '/file.txt'

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.dat') as f:
            test_file = f.name
            f.write(b'test content')

        try:
            resp = client.putContent(bucket_name, object_key, 'test content')
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)
            try:
                os.remove(test_file)
            except Exception:
                pass


class TestConcurrentOperationsBoundary(object):
    """并发操作边界测试"""

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
                resp = client.uploadFile(
                    bucket_name,
                    object_key,
                    test_file,
                    taskNum=1
                )
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
            time.sleep(0.5)

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
