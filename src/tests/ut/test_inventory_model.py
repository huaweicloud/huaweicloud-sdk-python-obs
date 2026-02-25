#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# Inventory(桶清单)模型类单元测试
# 对应集成测试: TestBucketInventory

import pytest
from obs import (
    InventoryConfiguration,
    InventoryFormat,
    InventoryFrequency,
    InventoryIncludedObjectVersions,
    InventoryOptionalFields,
    InventoryFilter,
    InventoryDestination,
    InventoryBucketDestination,
    PutBucketInventoryResponse,
    GetBucketInventoryResponse,
    DeleteBucketInventoryResponse,
    ListBucketInventoryResponse
)


class TestInventoryConfiguration(object):
    """InventoryConfiguration模型类单元测试"""

    def test_inventory_configuration_creation_default(self):
        """测试默认创建InventoryConfiguration"""
        config = InventoryConfiguration()
        assert config is not None
        assert config.inventoryId is None
        assert config.isEnabled is None
        assert config.objectVersion is None

    def test_inventory_configuration_with_params(self):
        """测试带参数创建InventoryConfiguration"""
        destination = InventoryDestination(
            bucket='target-bucket',
            format=InventoryFormat.CSV,
            prefix='inventory/'
        )
        config = InventoryConfiguration(
            inventoryId='test-inventory',
            isEnabled=True,
            objectVersion=InventoryIncludedObjectVersions.All,
            frequency=InventoryFrequency.Daily,
            destination=destination
        )
        assert config.inventoryId == 'test-inventory'
        assert config.isEnabled is True
        assert config.objectVersion == InventoryIncludedObjectVersions.All
        assert config.frequency == InventoryFrequency.Daily
        assert config.destination is not None

    def test_inventory_configuration_with_filter(self):
        """测试带filter的InventoryConfiguration"""
        filter_rule = InventoryFilter(prefix='prefix/')
        destination = InventoryDestination(
            bucket='target-bucket',
            format=InventoryFormat.CSV
        )
        config = InventoryConfiguration(
            inventoryId='test-inventory',
            isEnabled=True,
            objectVersion=InventoryIncludedObjectVersions.All,
            frequency=InventoryFrequency.Daily,
            filter=filter_rule,
            destination=destination
        )
        assert config.filter is not None
        assert config.filter.prefix == 'prefix/'

    def test_inventory_configuration_with_optional_fields(self):
        """测试带optionalFields的InventoryConfiguration"""
        optional_fields = [
            InventoryOptionalFields.Size,
            InventoryOptionalFields.LastModifiedDate,
            InventoryOptionalFields.ETag
        ]
        destination = InventoryDestination(
            bucket='target-bucket',
            format=InventoryFormat.CSV
        )
        config = InventoryConfiguration(
            inventoryId='test-inventory',
            isEnabled=True,
            objectVersion=InventoryIncludedObjectVersions.All,
            frequency=InventoryFrequency.Daily,
            optionalFields=optional_fields,
            destination=destination
        )
        assert config.optionalFields is not None
        assert len(config.optionalFields) == 3


class TestInventoryDestination(object):
    """InventoryDestination模型类单元测试"""

    def test_inventory_destination_creation(self):
        """测试创建InventoryDestination"""
        dest = InventoryDestination(
            bucket='target-bucket',
            format=InventoryFormat.CSV,
            prefix='inventory/',
            accountId='123456789'
        )
        assert dest.bucket == 'target-bucket'
        assert dest.format == InventoryFormat.CSV
        assert dest.prefix == 'inventory/'
        assert dest.accountId == '123456789'


class TestInventoryFilter(object):
    """InventoryFilter模型类单元测试"""

    def test_inventory_filter_creation(self):
        """测试创建InventoryFilter"""
        filter_rule = InventoryFilter(prefix='test-prefix/')
        assert filter_rule.prefix == 'test-prefix/'


class TestPutBucketInventoryResponse(object):
    """PutBucketInventoryResponse模型类单元测试"""

    def test_put_inventory_response_creation(self):
        """测试创建PutBucketInventoryResponse"""
        resp = PutBucketInventoryResponse(body='test', headers={})
        assert resp is not None
        assert resp.body == 'test'


class TestGetBucketInventoryResponse(object):
    """GetBucketInventoryResponse模型类单元测试"""

    def test_get_inventory_response_creation(self):
        """测试创建GetBucketInventoryResponse"""
        config = InventoryConfiguration(inventoryId='test-id')
        resp = GetBucketInventoryResponse(body=config, headers={})
        assert resp is not None
        assert resp.body.inventoryId == 'test-id'


class TestDeleteBucketInventoryResponse(object):
    """DeleteBucketInventoryResponse模型类单元测试"""

    def test_delete_inventory_response_creation(self):
        """测试创建DeleteBucketInventoryResponse"""
        resp = DeleteBucketInventoryResponse(body='test', headers={})
        assert resp is not None


class TestListBucketInventoryResponse(object):
    """ListBucketInventoryResponse模型类单元测试"""

    def test_list_inventory_response_creation(self):
        """测试创建ListBucketInventoryResponse"""
        configurations = [
            InventoryConfiguration(inventoryId='id1'),
            InventoryConfiguration(inventoryId='id2')
        ]
        resp = ListBucketInventoryResponse(
            configurations=configurations,
            isTruncated=False
        )
        assert resp is not None
        assert len(resp.configurations) == 2
        assert resp.isTruncated is False

    def test_list_inventory_response_with_truncated(self):
        """测试带isTruncated的ListBucketInventoryResponse"""
        resp = ListBucketInventoryResponse(
            configurations=[InventoryConfiguration(inventoryId='id1')],
            isTruncated=True,
            nextInventoryId='id2'
        )
        assert resp.isTruncated is True
        assert resp.nextInventoryId == 'id2'
