#!/usr/bin/python
# -*- coding:utf-8 -*-
# Copyright 2019 Huawei Technologies Co.,Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# CONDITIONS OF ANY KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations under the License.

"""
桶清单(Bucket Inventory)管理功能 - 集成测试
需要真实的OBS环境
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs import ObsClient
from obs import (
    InventoryConfiguration,
    InventoryDestination,
    InventoryFilter,
    InventoryFormat,
    InventoryFrequency,
    InventoryIncludedObjectVersions,
    InventoryOptionalFields
)
from conftest import test_config


class TestBucketInventory(object):
    """桶清单功能测试类"""

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

    def cleanup_inventory(self, client, bucket_name, inventory_id):
        """清理测试清单配置"""
        try:
            client.deleteBucketInventory(bucket_name, inventory_id)
        except Exception:
            pass

    # ==================== 功能测试 ====================

    def test_put_inventory_basic(self):
        """测试场景: 创建基本桶清单配置"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        inventory_id = 'test-inventory-basic-' + str(int(time.time()))

        try:
            destination = InventoryDestination(
                bucket=bucket_name,
                format=InventoryFormat.CSV,
                prefix='inventory/'
            )
            config = InventoryConfiguration(
                inventoryId=inventory_id,
                isEnabled=True,
                objectVersion=InventoryIncludedObjectVersions.All,
                frequency=InventoryFrequency.Daily,
                destination=destination
            )

            resp = client.putBucketInventory(bucket_name, inventory_id, config)
            assert resp.status == 200

        finally:
            self.cleanup_inventory(client, bucket_name, inventory_id)

    def test_put_inventory_with_filter(self):
        """测试场景: 创建带过滤器的桶清单配置"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        inventory_id = 'test-inventory-filter-' + str(int(time.time()))

        try:
            filter_rule = InventoryFilter(prefix='test-prefix/')
            destination = InventoryDestination(
                bucket=bucket_name,
                format=InventoryFormat.CSV
            )
            config = InventoryConfiguration(
                inventoryId=inventory_id,
                isEnabled=True,
                objectVersion=InventoryIncludedObjectVersions.Current,
                frequency=InventoryFrequency.Weekly,
                filter=filter_rule,
                destination=destination
            )

            resp = client.putBucketInventory(bucket_name, inventory_id, config)
            assert resp.status == 200

        finally:
            self.cleanup_inventory(client, bucket_name, inventory_id)

    def test_put_inventory_with_optional_fields(self):
        """测试场景: 创建带可选字段的桶清单配置"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        inventory_id = 'test-inventory-fields-' + str(int(time.time()))

        try:
            optional_fields = [
                InventoryOptionalFields.Size,
                InventoryOptionalFields.LastModifiedDate,
                InventoryOptionalFields.ETag
            ]
            destination = InventoryDestination(
                bucket=bucket_name,
                format=InventoryFormat.CSV
            )
            config = InventoryConfiguration(
                inventoryId=inventory_id,
                isEnabled=True,
                objectVersion=InventoryIncludedObjectVersions.All,
                frequency=InventoryFrequency.Daily,
                optionalFields=optional_fields,
                destination=destination
            )

            resp = client.putBucketInventory(bucket_name, inventory_id, config)
            assert resp.status == 200

        finally:
            self.cleanup_inventory(client, bucket_name, inventory_id)

    def test_put_inventory_with_dict(self):
        """测试场景: 使用字典格式创建桶清单配置"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        inventory_id = 'test-inventory-dict-' + str(int(time.time()))

        try:
            config_dict = {
                'inventoryId': inventory_id,
                'isEnabled': True,
                'objectVersion': InventoryIncludedObjectVersions.All,
                'frequency': InventoryFrequency.Daily,
                'destination': {
                    'bucket': bucket_name,
                    'format': InventoryFormat.CSV,
                    'prefix': 'inventory/'
                }
            }

            resp = client.putBucketInventory(bucket_name, inventory_id, config_dict)
            assert resp.status == 200

        finally:
            self.cleanup_inventory(client, bucket_name, inventory_id)

    def test_get_inventory(self):
        """测试场景: 获取桶清单配置"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        inventory_id = 'test-inventory-get-' + str(int(time.time()))

        try:
            # First create an inventory configuration
            destination = InventoryDestination(
                bucket=bucket_name,
                format=InventoryFormat.CSV,
                prefix='inventory/'
            )
            config = InventoryConfiguration(
                inventoryId=inventory_id,
                isEnabled=True,
                objectVersion=InventoryIncludedObjectVersions.All,
                frequency=InventoryFrequency.Daily,
                destination=destination
            )
            put_resp = client.putBucketInventory(bucket_name, inventory_id, config)
            assert put_resp.status == 200

            # Then get the inventory configuration
            get_resp = client.getBucketInventory(bucket_name, inventory_id)
            assert get_resp.status == 200
            assert get_resp.body.configuration.inventoryId == inventory_id
            assert get_resp.body.configuration.isEnabled is True
            assert get_resp.body.configuration.objectVersion == InventoryIncludedObjectVersions.All
            assert get_resp.body.configuration.frequency == InventoryFrequency.Daily

        finally:
            self.cleanup_inventory(client, bucket_name, inventory_id)

    def test_list_inventory(self):
        """测试场景: 列举桶的所有清单配置"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        inventory_id = 'test-inventory-list-' + str(int(time.time()))

        try:
            # Create one inventory configuration
            destination = InventoryDestination(
                bucket=bucket_name,
                format=InventoryFormat.CSV,
                prefix='list-test/'
            )
            config = InventoryConfiguration(
                inventoryId=inventory_id,
                isEnabled=True,
                objectVersion=InventoryIncludedObjectVersions.All,
                frequency=InventoryFrequency.Daily,
                destination=destination
            )
            resp = client.putBucketInventory(bucket_name, inventory_id, config)
            assert resp.status == 200

            # List all inventory configurations
            list_resp = client.listBucketInventory(bucket_name)
            assert list_resp.status == 200
            assert len(list_resp.body.configurations) >= 1
            # Verify our configuration is in the list
            found = any(c.inventoryId == inventory_id for c in list_resp.body.configurations)
            assert found is True

        finally:
            self.cleanup_inventory(client, bucket_name, inventory_id)

    def test_delete_inventory(self):
        """测试场景: 删除桶清单配置"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        inventory_id = 'test-inventory-delete-' + str(int(time.time()))

        try:
            # First create an inventory configuration
            destination = InventoryDestination(
                bucket=bucket_name,
                format=InventoryFormat.CSV
            )
            config = InventoryConfiguration(
                inventoryId=inventory_id,
                isEnabled=True,
                objectVersion=InventoryIncludedObjectVersions.All,
                frequency=InventoryFrequency.Daily,
                destination=destination
            )
            put_resp = client.putBucketInventory(bucket_name, inventory_id, config)
            assert put_resp.status == 200

            # Then delete the inventory configuration
            del_resp = client.deleteBucketInventory(bucket_name, inventory_id)
            assert del_resp.status == 204

        finally:
            self.cleanup_inventory(client, bucket_name, inventory_id)

    def test_update_inventory(self):
        """测试场景: 更新桶清单配置"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        inventory_id = 'test-inventory-update-' + str(int(time.time()))

        try:
            # Create initial configuration
            destination = InventoryDestination(
                bucket=bucket_name,
                format=InventoryFormat.CSV
            )
            config = InventoryConfiguration(
                inventoryId=inventory_id,
                isEnabled=True,
                objectVersion=InventoryIncludedObjectVersions.All,
                frequency=InventoryFrequency.Daily,
                destination=destination
            )
            put_resp1 = client.putBucketInventory(bucket_name, inventory_id, config)
            assert put_resp1.status == 200

            # Update the configuration
            filter_rule = InventoryFilter(prefix='updated/')
            updated_config = InventoryConfiguration(
                inventoryId=inventory_id,
                isEnabled=False,
                objectVersion=InventoryIncludedObjectVersions.Current,
                frequency=InventoryFrequency.Weekly,
                filter=filter_rule,
                destination=destination
            )
            put_resp2 = client.putBucketInventory(bucket_name, inventory_id, updated_config)
            assert put_resp2.status == 200

            # Verify the update
            get_resp = client.getBucketInventory(bucket_name, inventory_id)
            assert get_resp.status == 200
            assert get_resp.body.configuration.isEnabled is False
            assert get_resp.body.configuration.objectVersion == InventoryIncludedObjectVersions.Current
            assert get_resp.body.configuration.frequency == InventoryFrequency.Weekly

        finally:
            self.cleanup_inventory(client, bucket_name, inventory_id)

    # ==================== 边界测试 ====================

    def test_inventory_disabled(self):
        """测试场景: 创建禁用的清单配置"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        inventory_id = 'test-inventory-disabled-' + str(int(time.time()))

        try:
            destination = InventoryDestination(
                bucket=bucket_name,
                format=InventoryFormat.CSV
            )
            config = InventoryConfiguration(
                inventoryId=inventory_id,
                isEnabled=False,
                objectVersion=InventoryIncludedObjectVersions.Current,
                frequency=InventoryFrequency.Daily,
                destination=destination
            )

            resp = client.putBucketInventory(bucket_name, inventory_id, config)
            assert resp.status == 200

        finally:
            self.cleanup_inventory(client, bucket_name, inventory_id)

    def test_inventory_current_version_only(self):
        """测试场景: 仅包含当前对象版本"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        inventory_id = 'test-inventory-current-' + str(int(time.time()))

        try:
            destination = InventoryDestination(
                bucket=bucket_name,
                format=InventoryFormat.CSV
            )
            config = InventoryConfiguration(
                inventoryId=inventory_id,
                isEnabled=True,
                objectVersion=InventoryIncludedObjectVersions.Current,
                frequency=InventoryFrequency.Daily,
                destination=destination
            )

            resp = client.putBucketInventory(bucket_name, inventory_id, config)
            assert resp.status == 200

        finally:
            self.cleanup_inventory(client, bucket_name, inventory_id)

    def test_inventory_weekly_frequency(self):
        """测试场景: 每周频率清单配置"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        inventory_id = 'test-inventory-weekly-' + str(int(time.time()))

        try:
            destination = InventoryDestination(
                bucket=bucket_name,
                format=InventoryFormat.CSV
            )
            config = InventoryConfiguration(
                inventoryId=inventory_id,
                isEnabled=True,
                objectVersion=InventoryIncludedObjectVersions.All,
                frequency=InventoryFrequency.Weekly,
                destination=destination
            )

            resp = client.putBucketInventory(bucket_name, inventory_id, config)
            assert resp.status == 200

        finally:
            self.cleanup_inventory(client, bucket_name, inventory_id)

    # ==================== 参数检查测试 ====================

    def test_put_inventory_missing_bucket_name(self):
        """测试场景: bucketName为None"""
        client_type, client = self.get_client()

        from obs import InventoryDestination, InventoryFormat
        destination = InventoryDestination(
            bucket='test-bucket',
            format=InventoryFormat.CSV
        )
        config = InventoryConfiguration(
            inventoryId='test-id',
            isEnabled=True,
            objectVersion=InventoryIncludedObjectVersions.All,
            frequency=InventoryFrequency.Daily,
            destination=destination
        )

        with pytest.raises(Exception) as exc_info:
            client.putBucketInventory(None, 'test-id', config)
        assert 'bucketname' in str(exc_info.value).lower()

    def test_put_inventory_missing_inventory_id(self):
        """测试场景: inventoryId为None"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        from obs import InventoryDestination, InventoryFormat
        destination = InventoryDestination(
            bucket='test-bucket',
            format=InventoryFormat.CSV
        )
        config = InventoryConfiguration(
            inventoryId='test-id',
            isEnabled=True,
            objectVersion=InventoryIncludedObjectVersions.All,
            frequency=InventoryFrequency.Daily,
            destination=destination
        )

        with pytest.raises(Exception) as exc_info:
            client.putBucketInventory(bucket_name, None, config)
        assert 'inventoryid' in str(exc_info.value).lower()

    def test_put_inventory_missing_configuration(self):
        """测试场景: inventoryConfiguration为None"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with pytest.raises(Exception) as exc_info:
            client.putBucketInventory(bucket_name, 'test-id', None)
        assert 'inventoryconfiguration' in str(exc_info.value).lower()

    def test_get_inventory_missing_bucket_name(self):
        """测试场景: getBucketInventory的bucketName为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.getBucketInventory(None, 'test-id')
        assert 'bucketname' in str(exc_info.value).lower()

    def test_get_inventory_missing_inventory_id(self):
        """测试场景: getBucketInventory的inventoryId为None"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with pytest.raises(Exception) as exc_info:
            client.getBucketInventory(bucket_name, None)
        assert 'inventoryid' in str(exc_info.value).lower()

    def test_delete_inventory_missing_bucket_name(self):
        """测试场景: deleteBucketInventory的bucketName为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.deleteBucketInventory(None, 'test-id')
        assert 'bucketname' in str(exc_info.value).lower()

    def test_delete_inventory_missing_inventory_id(self):
        """测试场景: deleteBucketInventory的inventoryId为None"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with pytest.raises(Exception) as exc_info:
            client.deleteBucketInventory(bucket_name, None)
        assert 'inventoryid' in str(exc_info.value).lower()

    def test_list_inventory_missing_bucket_name(self):
        """测试场景: listBucketInventory的bucketName为None"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.listBucketInventory(None)
        assert 'bucketname' in str(exc_info.value).lower()
