#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# Symlink模型类单元测试
# 对应集成测试: TestObjectSymlink

import pytest
from obs import PutObjectSymlinkHeader, GetObjectSymlinkResponse


class TestPutObjectSymlinkHeader(object):
    """PutObjectSymlinkHeader模型类单元测试"""

    def test_header_creation_default(self):
        """测试默认创建PutObjectSymlinkHeader"""
        header = PutObjectSymlinkHeader()
        assert header is not None

    def test_header_with_symlink_target(self):
        """测试带目标对象的PutObjectSymlinkHeader"""
        header = PutObjectSymlinkHeader(
            symlinkTarget='target/object.jpg'
        )
        assert header.symlinkTarget == 'target/object.jpg'

    def test_header_with_all_params(self):
        """测试带所有参数的PutObjectSymlinkHeader"""
        header = PutObjectSymlinkHeader(
            symlinkTarget='target/object.jpg',
            contentType='text/plain',
            metadata={'custom-key': 'custom-value'}
        )
        assert header.symlinkTarget == 'target/object.jpg'
        assert header.contentType == 'text/plain'
        assert header.metadata == {'custom-key': 'custom-value'}


class TestGetObjectSymlinkResponse(object):
    """GetObjectSymlinkResponse模型类单元测试"""

    def test_response_creation(self):
        """测试GetObjectSymlinkResponse创建"""
        response = GetObjectSymlinkResponse()
        assert response is not None

    def test_response_with_symlink_target(self):
        """测试带目标对象的GetObjectSymlinkResponse"""
        headers = [
            ('x-obs-symlink-target', 'target/object.jpg')
        ]
        response = GetObjectSymlinkResponse(body=None, headers=headers)
        # Should extract symlink target from headers
        assert response.symlinkTarget == 'target/object.jpg'

    def test_response_status_code(self):
        """测试响应状态码"""
        response = GetObjectSymlinkResponse(status=200)
        # Status is inherited from GetResult
        assert response.status == 200

    def test_response_with_metadata(self):
        """测试带元数据的响应"""
        headers = [
            ('x-obs-symlink-target', 'path/to/target'),
            ('Content-Type', 'text/plain'),
            ('ETag', '"abc123"'),
            ('Last-Modified', 'Wed, 21 Oct 2015 07:28:00 GMT')
        ]
        response = GetObjectSymlinkResponse(body=None, headers=headers, status=200)
        assert response.symlinkTarget == 'path/to/target'
        assert response.contentType == 'text/plain'
        assert response.etag == '"abc123"'
        assert response.lastModified == 'Wed, 21 Oct 2015 07:28:00 GMT'
        assert response.status == 200

    def test_response_with_content_length(self):
        """测试带Content-Length的响应"""
        headers = [
            ('x-obs-symlink-target', 'path/to/target'),
            ('Content-Length', '1024')
        ]
        response = GetObjectSymlinkResponse(body=None, headers=headers)
        assert response.contentLength == 1024

    def test_response_with_storage_class(self):
        """测试带存储类型的响应"""
        headers = [
            ('x-obs-symlink-target', 'path/to/target'),
            ('x-obs-storage-class', 'STANDARD')
        ]
        response = GetObjectSymlinkResponse(body=None, headers=headers)
        assert response.storageClass == 'STANDARD'

    def test_response_with_version_id(self):
        """测试带版本ID的响应"""
        headers = [
            ('x-obs-symlink-target', 'path/to/target'),
            ('x-obs-version-id', 'version-id-123')
        ]
        response = GetObjectSymlinkResponse(body=None, headers=headers)
        assert response.versionId == 'version-id-123'
