#!/usr/bin/python
# -*- coding:utf-8 -*-
# Copyright 2024 Huawei Technologies Co.,Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations under the License.

"""
Direct Cold Access integration tests
Integration tests for Direct Cold Access (归档直读) functionality
"""

import sys, os
# 添加当前目录到 Python 路径，确保可以导入 conftest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from obs import (
    ObsClient,
    DirectColdAccessConfiguration,
    GetBucketDirectColdAccessResponse,
)
from conftest import test_config


class TestOBSClient(object):
    def get_client(self):
        client_type = "OBSClient"
        obsClient = ObsClient(
            access_key_id=test_config["ak"],
            secret_access_key=test_config["sk"],
            server=test_config["endpoint"],
            is_signature_negotiation=False,
        )
        return client_type, obsClient


class TestDirectColdAccessIntegration(TestOBSClient):
    """Integration tests for Direct Cold Access functionality"""

    def test_set_bucket_direct_cold_access_with_enabled(self, delete_bucket_after_test):
        """Test setting Direct Cold Access with Enabled status"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "direct-cold-001"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Arrange - Create Direct Cold Access configuration
        config = DirectColdAccessConfiguration(status='Enabled')

        # Act - Set Direct Cold Access configuration
        set_result = obsClient.setBucketDirectColdAccess(bucket_name, config)
        assert set_result.status == 200

        # Assert - Verify by getting the configuration
        get_result = obsClient.getBucketDirectColdAccess(bucket_name)
        assert get_result.status == 200
        assert get_result.body is not None
        assert get_result.body.status == 'Enabled'

        # Cleanup - Delete Direct Cold Access configuration
        delete_result = obsClient.deleteBucketDirectColdAccess(bucket_name)
        assert delete_result.status == 204

    def test_get_bucket_direct_cold_access_without_config(self, delete_bucket_after_test):
        """Test getting Direct Cold Access when not configured"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "direct-cold-002"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Act - Get Direct Cold Access configuration when not set
        get_result = obsClient.getBucketDirectColdAccess(bucket_name)

        # Assert - Should return 200 but body may have no status
        assert get_result.status == 200
        assert get_result.body.status is None

    def test_update_bucket_direct_cold_access(self, delete_bucket_after_test):
        """Test updating Direct Cold Access configuration"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "direct-cold-003"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Arrange - Set Direct Cold Access with Enabled
        config = DirectColdAccessConfiguration(status='Enabled')
        set_result = obsClient.setBucketDirectColdAccess(bucket_name, config)
        assert set_result.status == 200

        # Assert - Verify
        get_result = obsClient.getBucketDirectColdAccess(bucket_name)
        assert get_result.status == 200
        assert get_result.body.status == 'Enabled'

        # Act - Update to Disabled
        config_disabled = DirectColdAccessConfiguration(status='Disabled')
        update_result = obsClient.setBucketDirectColdAccess(bucket_name, config_disabled)
        assert update_result.status == 200 or update_result.status == 201

        # Assert - Verify the update
        get_result = obsClient.getBucketDirectColdAccess(bucket_name)
        assert get_result.status == 200
        assert get_result.body.status == 'Disabled'

        # Cleanup
        delete_result = obsClient.deleteBucketDirectColdAccess(bucket_name)
        assert delete_result.status == 204

    def test_delete_bucket_direct_cold_access(self, delete_bucket_after_test):
        """Test deleting Direct Cold Access configuration"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "direct-cold-004"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Arrange - Set Direct Cold Access
        config = DirectColdAccessConfiguration(status='Enabled')
        set_result = obsClient.setBucketDirectColdAccess(bucket_name, config)
        assert set_result.status == 200

        # Assert - Verify
        get_result = obsClient.getBucketDirectColdAccess(bucket_name)
        assert get_result.status == 200
        assert get_result.body.status == 'Enabled'

        # Act - Delete Direct Cold Access configuration
        delete_result = obsClient.deleteBucketDirectColdAccess(bucket_name)
        assert delete_result.status == 204

        # Assert - Verify deletion by getting configuration
        get_result = obsClient.getBucketDirectColdAccess(bucket_name)
        assert get_result.status == 200
        assert get_result.body.status is None
        # After deletion, status should be None or not present

    def test_full_lifecycle_direct_cold_access(self, delete_bucket_after_test):
        """Test full lifecycle: set -> get -> delete"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "direct-cold-005"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Step 1: Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Step 2: Set Direct Cold Access configuration
        config = DirectColdAccessConfiguration(status='Enabled')
        set_result = obsClient.setBucketDirectColdAccess(bucket_name, config)
        assert set_result.status == 200

        # Step 3: Get and verify configuration
        get_result = obsClient.getBucketDirectColdAccess(bucket_name)
        assert get_result.status == 200
        assert get_result.body.status == 'Enabled'

        # Step 4: Delete configuration
        delete_result = obsClient.deleteBucketDirectColdAccess(bucket_name)
        assert delete_result.status == 204

        # Step 5: Verify deletion
        get_result_after_delete = obsClient.getBucketDirectColdAccess(bucket_name)
        assert get_result_after_delete.status == 200
        assert get_result_after_delete.body.status is None

    def test_bucket_client_direct_cold_access(self, delete_bucket_after_test):
        """Test using BucketClient to manage Direct Cold Access"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "direct-cold-006"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Arrange - Get BucketClient
        bucket_client = obsClient.bucketClient(bucket_name)

        # Act - Set Direct Cold Access using BucketClient
        config = DirectColdAccessConfiguration(status='Enabled')
        set_result = bucket_client.setBucketDirectColdAccess(config)
        assert set_result.status == 200

        # Assert - Get using BucketClient
        get_result = bucket_client.getBucketDirectColdAccess()
        assert get_result.status == 200
        assert get_result.body.status == 'Enabled'

        # Cleanup - Delete using BucketClient
        delete_result = bucket_client.deleteBucketDirectColdAccess()
        assert delete_result.status == 204

    def test_set_bucket_direct_cold_access_with_invalid_status(self, delete_bucket_after_test):
        """Test setting Direct Cold Access with invalid status value"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "direct-cold-007"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Step 1: Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Step 2: Set Direct Cold Access with invalid status
        config = DirectColdAccessConfiguration(status='ErrorStatus')
        set_result = obsClient.setBucketDirectColdAccess(bucket_name, config)

        # Assert - Should fail with 400
        assert set_result.status == 400
