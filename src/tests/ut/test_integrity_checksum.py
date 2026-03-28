#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# 数据完整性校验单元测试
# 测试 CRC64、SHA256、MD5 等校验功能

import pytest
import os
import tempfile
import hashlib


class TestCrc64Checksum(object):
    """CRC64 校验测试"""

    def test_calculate_empty_file_crc64(self):
        """测试空文件的 CRC64"""
        from obs import util

        # 创建空文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            test_file = f.name

        try:
            crc = util.calculate_file_crc64(test_file)
            assert crc == 0
        finally:
            os.remove(test_file)

    def test_calculate_small_file_crc64(self):
        """测试小文件的 CRC64"""
        from obs import util

        test_data = b'Hello, World!'

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(test_data)
            test_file = f.name

        try:
            crc = util.calculate_file_crc64(test_file)
            assert crc is not None
            assert isinstance(crc, int)
            assert crc != 0  # 非空文件应该有非零 CRC
        finally:
            os.remove(test_file)

    def test_calculate_large_file_crc64(self):
        """测试大文件的 CRC64"""
        from obs import util

        # 创建 1MB 文件
        test_data = b'X' * (1024 * 1024)

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(test_data)
            test_file = f.name

        try:
            crc = util.calculate_file_crc64(test_file)
            assert crc is not None
            assert isinstance(crc, int)
        finally:
            os.remove(test_file)

    def test_calculate_content_crc64(self):
        """测试内容的 CRC64"""
        from obs import util

        content = b'Test content for CRC64 calculation'

        crc = util.calculate_content_crc64(content)
        assert crc is not None
        assert isinstance(crc, int)

    def test_crc64_with_offset(self):
        """测试带偏移量的 CRC64 计算"""
        from obs import util

        test_data = b'0123456789' * 100

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(test_data)
            test_file = f.name

        try:
            # 从偏移量 10 开始计算
            crc = util.calculate_file_crc64(test_file, offset=10, totalCount=500)
            assert crc is not None
        finally:
            os.remove(test_file)

    def test_calc_obj_crc_from_parts(self):
        """测试从分片计算对象 CRC64"""
        from obs import util
        from obs.model import CompletePart

        # 模拟多个分片的 CRC64
        part1 = CompletePart(partNum=1, etag='etag1', crc64=12345, size=1000)
        part2 = CompletePart(partNum=2, etag='etag2', crc64=67890, size=2000)
        part3 = CompletePart(partNum=3, etag='etag3', crc64=11111, size=1500)

        parts = [part1, part2, part3]

        obj_crc = util.calc_obj_crc_from_parts(parts)
        assert obj_crc is not None
        assert isinstance(obj_crc, int)

    def test_crc64_combine_same_data(self):
        """测试相同数据的 CRC64 合并结果一致"""
        from obs import util

        data = b'Test data for CRC64 combination'

        # 计算整体 CRC64
        crc1 = util.calculate_content_crc64(data)

        # 分段计算后合并
        half = len(data) // 2
        crc_part1 = util.calculate_content_crc64(data[:half])
        crc_obj = util.Crc64()
        combined_crc = crc_obj.combine(crc_part1, util.calculate_content_crc64(data[half:]), len(data[half:]))

        # 验证合并结果与整体计算结果一致
        assert crc1 == combined_crc


class TestSha256Checksum(object):
    """SHA256 校验测试"""

    def test_sha256_file_encode(self):
        """测试文件 SHA256 编码"""
        from obs import util

        test_data = b'Test data for SHA256'

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(test_data)
            test_file = f.name

        try:
            # 使用 Python 标准库计算预期值
            sha256_hash = hashlib.sha256()
            with open(test_file, 'rb') as f:
                sha256_hash.update(f.read())
            expected_sha256 = sha256_hash.digest()

            # 使用 SDK 的函数计算
            actual_sha256 = util.sha256_file_encode_by_size_offset(
                file_path=test_file,
                size=len(test_data),
                offset=0
            )

            assert actual_sha256 == expected_sha256
        finally:
            os.remove(test_file)

    def test_sha256_with_size_offset(self):
        """测试带大小和偏移量的 SHA256"""
        from obs import util

        test_data = b'0123456789' * 100

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(test_data)
            test_file = f.name

        try:
            # 计算中间 100 字节的 SHA256
            offset = 50
            size = 100

            sha256_from_sdk = util.sha256_file_encode_by_size_offset(
                file_path=test_file,
                size=size,
                offset=offset
            )

            # 验证
            assert sha256_from_sdk is not None
            assert len(sha256_from_sdk) == 32  # SHA256 输出 32 字节
        finally:
            os.remove(test_file)


class TestMd5Checksum(object):
    """MD5 校验测试"""

    def test_md5_encode(self):
        """测试 MD5 编码"""
        from obs import util

        test_data = b'Test data for MD5 encoding'

        # 使用 Python 标准库计算预期值
        expected_md5 = hashlib.md5(test_data).digest()

        # 使用 SDK 的函数计算
        actual_md5 = util.md5_encode(test_data)

        assert actual_md5 == expected_md5

    def test_md5_file_encode(self):
        """测试文件 MD5 编码"""
        from obs import util

        test_data = b'Test file content for MD5'

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(test_data)
            test_file = f.name

        try:
            # 使用 Python 标准库计算预期值
            expected_md5 = hashlib.md5()
            with open(test_file, 'rb') as f:
                expected_md5.update(f.read())

            # 使用 SDK 的函数计算
            actual_md5 = util.md5_file_encode_by_size_offset(
                file_path=test_file,
                size=len(test_data),
                offset=0
            )

            assert actual_md5 == expected_md5.digest()
        finally:
            os.remove(test_file)

    def test_md5_file_with_offset(self):
        """测试带偏移量的文件 MD5"""
        from obs import util

        test_data = b'0123456789' * 100

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(test_data)
            test_file = f.name

        try:
            # 从偏移量 100 开始，计算 200 字节
            md5_result = util.md5_file_encode_by_size_offset(
                file_path=test_file,
                size=200,
                offset=100
            )

            # 验证
            assert md5_result is not None
            assert len(md5_result) == 16  # MD5 输出 16 字节
        finally:
            os.remove(test_file)


class TestChecksumConsistency(object):
    """校验一致性测试"""

    def test_same_file_same_checksum(self):
        """测试同一文件多次计算得到相同校验和"""
        from obs import util

        test_data = b'Consistent test data' * 1000

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(test_data)
            test_file = f.name

        try:
            # 计算 CRC64
            crc1 = util.calculate_file_crc64(test_file)
            crc2 = util.calculate_file_crc64(test_file)
            assert crc1 == crc2

            # 计算 SHA256
            sha1 = util.sha256_file_encode_by_size_offset(test_file, len(test_data), 0)
            sha2 = util.sha256_file_encode_by_size_offset(test_file, len(test_data), 0)
            assert sha1 == sha2

        finally:
            os.remove(test_file)

    def test_different_files_different_checksums(self):
        """测试不同文件得到不同校验和"""
        from obs import util

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b'File 1 content')
            file1 = f.name

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b'File 2 content')
            file2 = f.name

        try:
            crc1 = util.calculate_file_crc64(file1)
            crc2 = util.calculate_file_crc64(file2)

            assert crc1 != crc2
        finally:
            os.remove(file1)
            os.remove(file2)

    def test_checksum_changes_with_content_modification(self):
        """测试内容修改后校验和变化"""
        from obs import util

        original_data = b'Original content'

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(original_data)
            test_file = f.name

        try:
            crc_original = util.calculate_file_crc64(test_file)

            # 修改文件内容
            with open(test_file, 'r+b') as f:
                f.seek(0)
                f.write(b'Modified')

            crc_modified = util.calculate_file_crc64(test_file)

            assert crc_original != crc_modified
        finally:
            os.remove(test_file)


class TestChecksumErrorHandling(object):
    """校验错误处理测试"""

    def test_nonexistent_file_handling(self):
        """测试不存在的文件处理"""
        from obs import util

        with pytest.raises(Exception):
            util.calculate_file_crc64('/nonexistent/file/path.dat')

    def test_empty_content_crc64(self):
        """测试空内容的 CRC64"""
        from obs import util

        crc = util.calculate_content_crc64(b'')
        assert crc == 0

    def test_zero_size_crc64(self):
        """测试零大小的 CRC64"""
        from obs import util

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            test_file = f.name

        try:
            crc = util.calculate_file_crc64(test_file, totalCount=0)
            assert crc == 0
        finally:
            os.remove(test_file)
