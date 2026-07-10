#!/usr/bin/python
# -*- coding:utf-8 -*-
# Copyright 2024 Huawei Technologies Co.,Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.  See the License for
# specific language governing permissions and limitations under the License.

"""
DIS Policy integration tests
Integration tests for DIS notification policy functionality
"""

import sys, os
# 添加当前目录到 Python 路径，确保可以导入 conftest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from obs import (
    ObsClient,
    DisPolicy,
    DisPolicyRule,
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


class TestDisPolicyIntegration(TestOBSClient):
    """Integration tests for DIS Policy functionality"""

    def test_set_bucket_dis_policy_with_single_rule(self, delete_bucket_after_test):
        """Test setting DIS policy with single rule"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-001"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Arrange - Create DIS policy with single rule
        rule1 = DisPolicyRule(
            id='rule1',
            stream="dis-SQgy",
            project="81f2722a50494a919abfa82a9b8f2a42",
            events=['ObjectCreated:*'],
            agency="distoobs"
        )
        dis_policy = DisPolicy(rules=[rule1])

        # Act - Set DIS policy
        set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy)
        assert set_result.status == 200 or set_result.status == 201

        # Assert - Verify by getting the policy
        get_result = obsClient.getBucketDisPolicy(bucket_name)
        assert get_result.status == 200
        assert get_result.body is not None
        assert get_result.body.rules is not None
        assert len(get_result.body.rules) == 1
        assert get_result.body.rules[0]['id'] == 'rule1'

        # Cleanup - Delete DIS policy
        delete_result = obsClient.deleteBucketDisPolicy(bucket_name)
        assert delete_result.status == 204

    def test_set_bucket_dis_policy_with_multiple_rules(self, delete_bucket_after_test):
        """Test setting DIS policy with multiple rules"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-002"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Arrange - Create DIS policy with multiple rules
        rule1 = DisPolicyRule(id='rule1', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectCreated:*'], agency="distoobs", prefix='rule1')
        rule2 = DisPolicyRule(id='rule2', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectRemoved:*'], agency="distoobs", prefix='rule2')
        rule3 = DisPolicyRule(id='rule3', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectCreated:Put'], agency="distoobs", prefix='rule3')
        dis_policy = DisPolicy(rules=[rule1, rule2, rule3])

        # Act - Set DIS policy
        set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy)
        assert set_result.status == 200 or set_result.status == 201

        # Assert - Verify by getting the policy
        get_result = obsClient.getBucketDisPolicy(bucket_name)
        assert get_result.status == 200
        assert get_result.body is not None
        assert len(get_result.body.rules) == 3

        # Cleanup
        delete_result = obsClient.deleteBucketDisPolicy(bucket_name)
        assert delete_result.status == 204

    def test_set_bucket_dis_policy_with_all_parameters(self, delete_bucket_after_test):
        """Test setting DIS policy with all optional parameters"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-003"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Arrange - Create DIS policy with all parameters
        rule = DisPolicyRule(
            id='rule1',
            stream="dis-SQgy",
            project="81f2722a50494a919abfa82a9b8f2a42",
            events=['ObjectCreated:*', 'ObjectRemoved:*'],
            prefix='test/',
            suffix='.txt',
            agency="distoobs"
        )
        dis_policy = DisPolicy(rules=[rule])

        # Act - Set DIS policy
        set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy)
        assert set_result.status == 200 or set_result.status == 201

        # Assert
        get_result = obsClient.getBucketDisPolicy(bucket_name)
        assert get_result.status == 200
        assert get_result.body.rules[0]['prefix'] == 'test/'
        assert get_result.body.rules[0]['suffix'] == '.txt'

        # Cleanup
        delete_result = obsClient.deleteBucketDisPolicy(bucket_name)
        assert delete_result.status == 204

    def test_get_bucket_dis_policy_when_not_set(self, delete_bucket_after_test):
        """Test getting DIS policy when not set"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-004"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket without DIS policy
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Act & Assert - Get DIS policy should fail
        get_result = obsClient.getBucketDisPolicy(bucket_name)
        # Policy not set yet, expect failure
        assert get_result.status != 200

    def test_update_bucket_dis_policy(self, delete_bucket_after_test):
        """Test updating existing DIS policy"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-005"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket and initial policy
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        rule1 = DisPolicyRule(id='rule1', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectCreated:*'], agency="distoobs", prefix="rule1")
        dis_policy = DisPolicy(rules=[rule1])
        set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy)
        assert set_result.status == 200 or set_result.status == 201

        # Act - Update with new policy
        rule2 = DisPolicyRule(id='rule2', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectRemoved:*'], agency="distoobs", prefix="rule2")
        dis_policy = DisPolicy(rules=[rule2])
        update_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy)
        assert update_result.status == 200 or update_result.status == 201

        # Assert
        get_result = obsClient.getBucketDisPolicy(bucket_name)
        assert get_result.status == 200
        assert get_result.body.rules[0]['id'] == 'rule2'

        # Cleanup
        delete_result = obsClient.deleteBucketDisPolicy(bucket_name)
        assert delete_result.status == 204

    def test_delete_bucket_dis_policy(self, delete_bucket_after_test):
        """Test deleting DIS policy"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-006"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket and set policy
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        rule = DisPolicyRule(id='rule1', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                             events=['ObjectCreated:*'], agency="distoobs")
        dis_policy = DisPolicy(rules=[rule])
        set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy)
        assert set_result.status == 200 or set_result.status == 201

        # Act - Delete DIS policy
        delete_result = obsClient.deleteBucketDisPolicy(bucket_name)
        assert delete_result.status == 204

        # Assert - Verify policy is deleted
        get_result = obsClient.getBucketDisPolicy(bucket_name)
        # Policy should not exist after deletion
        assert get_result.status != 200

    def test_set_bucket_dis_policy_via_bucket_client(self, delete_bucket_after_test):
        """Test setting DIS policy via BucketClient"""
        _, obsClient = self.get_client()
        from obs.bucket import BucketClient
        bucket_name = test_config["bucket_prefix"] + "dis-policy-007"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange
        bucketClient = BucketClient(obsClient, bucket_name)
        create_result = bucketClient.createBucket(location=test_config["location"])
        assert create_result.status == 200

        rule = DisPolicyRule(id='rule1', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                             events=['ObjectCreated:*'], agency="distoobs")
        dis_policy = DisPolicy(rules=[rule])

        # Act - Set DIS policy via BucketClient
        set_result = bucketClient.setBucketDisPolicy(dis_policy)
        assert set_result.status == 200 or set_result.status == 201

        # Assert
        get_result = bucketClient.getBucketDisPolicy()
        assert get_result.status == 200
        assert get_result.body.rules[0]['id'] == 'rule1'

        # Cleanup
        delete_result = bucketClient.deleteBucketDisPolicy()
        assert delete_result.status == 204

    def test_get_bucket_dis_policy_via_bucket_client(self, delete_bucket_after_test):
        """Test getting DIS policy via BucketClient"""
        _, obsClient = self.get_client()
        from obs.bucket import BucketClient
        bucket_name = test_config["bucket_prefix"] + "dis-policy-008"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange
        bucketClient = BucketClient(obsClient, bucket_name)
        create_result = bucketClient.createBucket(location=test_config["location"])
        assert create_result.status == 200

        rule = DisPolicyRule(id='rule1', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                             events=['ObjectCreated:*'], agency="distoobs")
        dis_policy = DisPolicy(rules=[rule])
        bucketClient.setBucketDisPolicy(dis_policy)

        # Act - Get DIS policy via BucketClient
        get_result = bucketClient.getBucketDisPolicy()
        assert get_result.status == 200
        assert get_result.body is not None
        assert get_result.body.rules is not None
        assert len(get_result.body.rules) == 1

        # Cleanup
        bucketClient.deleteBucketDisPolicy()

    def test_delete_bucket_dis_policy_via_bucket_client(self, delete_bucket_after_test):
        """Test deleting DIS policy via BucketClient"""
        _, obsClient = self.get_client()
        from obs.bucket import BucketClient
        bucket_name = test_config["bucket_prefix"] + "dis-policy-009"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange
        bucketClient = BucketClient(obsClient, bucket_name)
        create_result = bucketClient.createBucket(location=test_config["location"])
        assert create_result.status == 200

        rule = DisPolicyRule(id='rule1', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                             events=['ObjectCreated:*'], agency="distoobs")
        dis_policy = DisPolicy(rules=[rule])
        bucketClient.setBucketDisPolicy(dis_policy)

        # Act - Delete DIS policy via BucketClient
        delete_result = bucketClient.deleteBucketDisPolicy()
        assert delete_result.status == 204

        # Assert
        get_result = bucketClient.getBucketDisPolicy()
        assert get_result.status != 200

    def test_dis_policy_with_extension_headers(self, delete_bucket_after_test):
        """Test DIS policy operations with extension headers"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-010"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        rule = DisPolicyRule(id='rule1', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                             events=['ObjectCreated:*'], agency="distoobs")
        dis_policy = DisPolicy(rules=[rule])
        extension_headers = {
            'x-obs-test-header': 'test-value'
        }

        # Act - Set with extension headers
        set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy, extensionHeaders=extension_headers)
        assert set_result.status == 200 or set_result.status == 201

        # Get with extension headers
        get_result = obsClient.getBucketDisPolicy(bucket_name, extensionHeaders=extension_headers)
        assert get_result.status == 200

        # Delete with extension headers
        delete_result = obsClient.deleteBucketDisPolicy(bucket_name, extensionHeaders=extension_headers)
        assert delete_result.status == 204

    def test_dis_policy_concurrent_operations(self, delete_bucket_after_test):
        """Test concurrent DIS policy operations on different buckets"""
        _, obsClient = self.get_client()
        bucket_name1 = test_config["bucket_prefix"] + "dis-policy-011"
        bucket_name2 = test_config["bucket_prefix"] + "dis-policy-012"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].extend([bucket_name1, bucket_name2])

        # Arrange - Create two buckets
        for bucket_name in [bucket_name1, bucket_name2]:
            create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
            assert create_result.status == 200

        rule1 = DisPolicyRule(id='rule1', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectCreated:*'], agency="distoobs")
        rule2 = DisPolicyRule(id='rule2', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectRemoved:*'], agency="distoobs")
        dis_policy1 = DisPolicy(rules=[rule1])
        dis_policy2 = DisPolicy(rules=[rule2])

        # Act - Set policies concurrently
        set_result1 = obsClient.setBucketDisPolicy(bucket_name1, dis_policy1)
        set_result2 = obsClient.setBucketDisPolicy(bucket_name2, dis_policy2)
        assert set_result1.status == 200 or set_result1.status == 201
        assert set_result2.status == 200 or set_result2.status == 201

        # Assert - Get policies
        get_result1 = obsClient.getBucketDisPolicy(bucket_name1)
        get_result2 = obsClient.getBucketDisPolicy(bucket_name2)
        assert get_result1.status == 200
        assert get_result2.status == 200
        assert get_result1.body.rules[0]['id'] == 'rule1'
        assert get_result2.body.rules[0]['id'] == 'rule2'

        # Cleanup
        delete_result1 = obsClient.deleteBucketDisPolicy(bucket_name1)
        delete_result2 = obsClient.deleteBucketDisPolicy(bucket_name2)
        assert delete_result1.status == 204
        assert delete_result2.status == 204

    def test_dis_policy_with_different_event_types(self, delete_bucket_after_test):
        """Test DIS policy with different event types"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-013"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Test different event types
        event_types = [
            ['ObjectCreated:*'],
            ['ObjectCreated:Put'],
            ['ObjectCreated:Post'],
            ['ObjectCreated:Copy'],
            ['ObjectCreated:CompleteMultipartUpload'],
            ['ObjectRemoved:*'],
            ['ObjectRemoved:Delete'],
            ['ObjectCreated:*', 'ObjectRemoved:*']
        ]

        for idx, events in enumerate(event_types):
            rule = DisPolicyRule(
                id=f'rule{idx}',
                stream="dis-SQgy",
                project="81f2722a50494a919abfa82a9b8f2a42",
                events=events,
                agency="distoobs"
            )
            dis_policy = DisPolicy(rules=[rule])

            # Act - Set DIS policy
            set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy)
            assert set_result.status == 200 or set_result.status == 201

            # Assert - Verify
            get_result = obsClient.getBucketDisPolicy(bucket_name)
            assert get_result.status == 200
            assert get_result.body.rules[0]['id'] == f'rule{idx}'

            # Cleanup - Delete before next iteration
            delete_result = obsClient.deleteBucketDisPolicy(bucket_name)
            assert delete_result.status == 204

    def test_dis_policy_with_prefix_and_suffix_filtering(self, delete_bucket_after_test):
        """Test DIS policy with prefix and suffix filtering"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-014"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Test different prefix and suffix combinations
        test_cases = [
            ('images/', '.jpg'),
            ('documents/', '.pdf'),
            ('data/', '.json'),
            ('logs/', '.log'),
            ('/', '/'),
        ]

        for idx, (prefix, suffix) in enumerate(test_cases):
            rule = DisPolicyRule(
                id=f'rule{idx}',
                stream="dis-SQgy",
                project="81f2722a50494a919abfa82a9b8f2a42",
                events=['ObjectCreated:*'],
                prefix=prefix,
                suffix=suffix,
                agency="distoobs"
            )
            dis_policy = DisPolicy(rules=[rule])

            # Act - Set DIS policy
            set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy)
            assert set_result.status == 200 or set_result.status == 201

            # Assert - Verify prefix and suffix
            get_result = obsClient.getBucketDisPolicy(bucket_name)
            assert get_result.status == 200
            assert get_result.body.rules[0]['prefix'] == prefix
            assert get_result.body.rules[0]['suffix'] == suffix

            # Cleanup - Delete before next iteration
            delete_result = obsClient.deleteBucketDisPolicy(bucket_name)
            assert delete_result.status == 204

    def test_dis_policy_with_special_characters(self, delete_bucket_after_test):
        """Test DIS policy with special characters in parameters"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-015"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Test with special characters
        rule = DisPolicyRule(
            id='rule-1_speciaL123',
            stream="dis-SQgy",
            project="81f2722a50494a919abfa82a9b8f2a42",
            events=['ObjectCreated:*'],
            prefix='test/path/with/slashes/',
            suffix='.test-file',
            agency="distoobs"
        )
        dis_policy = DisPolicy(rules=[rule])

        # Act - Set DIS policy
        set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy)
        assert set_result.status == 200 or set_result.status == 201

        # Assert - Verify special characters are preserved
        get_result = obsClient.getBucketDisPolicy(bucket_name)
        assert get_result.status == 200
        assert get_result.body.rules[0]['id'] == 'rule-1_speciaL123'
        assert get_result.body.rules[0]['stream'] == "dis-SQgy"
        assert get_result.body.rules[0]['prefix'] == 'test/path/with/slashes/'
        assert get_result.body.rules[0]['suffix'] == '.test-file'

        # Cleanup
        delete_result = obsClient.deleteBucketDisPolicy(bucket_name)
        assert delete_result.status == 204

    def test_dis_policy_replace_entire_policy(self, delete_bucket_after_test):
        """Test replacing entire DIS policy (not incremental update)"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-016"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Set initial policy with 3 rules
        rule1 = DisPolicyRule(id='rule1', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectCreated:*'], agency="distoobs", prefix='rule1')
        rule2 = DisPolicyRule(id='rule2', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectRemoved:*'], agency="distoobs", prefix='rule2')
        rule3 = DisPolicyRule(id='rule3', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectCreated:Put'], agency="distoobs", prefix='rule3')
        dis_policy = DisPolicy(rules=[rule1, rule2, rule3])
        set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy)
        assert set_result.status == 200 or set_result.status == 201

        # Act - Replace with new policy (single rule)
        rule_new = DisPolicyRule(id='rule-new', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                                 events=['ObjectCreated:*'], agency="distoobs")
        dis_policy_new = DisPolicy(rules=[rule_new])
        set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy_new)
        assert set_result.status == 200 or set_result.status == 201

        # Assert - Only new rule exists
        get_result = obsClient.getBucketDisPolicy(bucket_name)
        assert get_result.status == 200
        assert len(get_result.body.rules) == 1
        assert get_result.body.rules[0]['id'] == 'rule-new'

        # Cleanup
        delete_result = obsClient.deleteBucketDisPolicy(bucket_name)
        assert delete_result.status == 204

    def test_dis_policy_set_get_delete_cycle(self, delete_bucket_after_test):
        """Test complete cycle of set, get, and delete operations"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-017"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Act 1 - Set policy
        rule = DisPolicyRule(id='cycle-rule', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                             events=['ObjectCreated:*'], agency="distoobs")
        dis_policy = DisPolicy(rules=[rule])
        set_result = obsClient.setBucketDisPolicy(bucket_name, dis_policy)
        assert set_result.status == 200 or set_result.status == 201

        # Act 2 - Get policy
        get_result = obsClient.getBucketDisPolicy(bucket_name)
        assert get_result.status == 200
        assert get_result.body.rules[0]['id'] == 'cycle-rule'

        # Act 3 - Delete policy
        delete_result = obsClient.deleteBucketDisPolicy(bucket_name)
        assert delete_result.status == 204

        # Act 4 - Verify policy is gone
        get_result = obsClient.getBucketDisPolicy(bucket_name)
        assert get_result.status != 200

    def test_dis_policy_with_bucket_client_set_get_delete_cycle(self, delete_bucket_after_test):
        """Test complete cycle using BucketClient"""
        _, obsClient = self.get_client()
        from obs.bucket import BucketClient
        bucket_name = test_config["bucket_prefix"] + "dis-policy-018"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange
        bucketClient = BucketClient(obsClient, bucket_name)
        bucketClient.createBucket(location=test_config["location"])

        # Act 1 - Set policy
        rule = DisPolicyRule(id='bucket-cycle-rule', stream="dis-SQgy",
                             project="81f2722a50494a919abfa82a9b8f2a42", events=['ObjectCreated:*'],
                             agency="distoobs")
        dis_policy = DisPolicy(rules=[rule])
        set_result = bucketClient.setBucketDisPolicy(dis_policy)
        assert set_result.status == 200 or set_result.status == 201

        # Act 2 - Get policy
        get_result = bucketClient.getBucketDisPolicy()
        assert get_result.status == 200
        assert get_result.body.rules[0]['id'] == 'bucket-cycle-rule'

        # Act 3 - Delete policy
        delete_result = bucketClient.deleteBucketDisPolicy()
        assert delete_result.status == 204

        # Act 4 - Verify policy is gone
        get_result = bucketClient.getBucketDisPolicy()
        assert get_result.status != 200

    def test_dis_policy_multiple_operations_same_bucket(self, delete_bucket_after_test):
        """Test multiple DIS policy operations on the same bucket"""
        _, obsClient = self.get_client()
        bucket_name = test_config["bucket_prefix"] + "dis-policy-019"
        delete_bucket_after_test["client"] = obsClient
        delete_bucket_after_test["need_delete_buckets"].append(bucket_name)

        # Arrange - Create bucket
        create_result = obsClient.createBucket(bucket_name, location=test_config["location"])
        assert create_result.status == 200

        # Operation 1 - Set policy
        rule1 = DisPolicyRule(id='rule1', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectCreated:*'], agency="distoobs")
        dis_policy1 = DisPolicy(rules=[rule1])
        result = obsClient.setBucketDisPolicy(bucket_name, dis_policy1)
        assert result.status == 200 or result.status == 201

        # Operation 2 - Get policy
        result = obsClient.getBucketDisPolicy(bucket_name)
        assert result.status == 200

        # Operation 3 - Update policy
        rule2 = DisPolicyRule(id='rule2', stream="dis-SQgy", project="81f2722a50494a919abfa82a9b8f2a42",
                              events=['ObjectRemoved:*'], agency="distoobs")
        dis_policy2 = DisPolicy(rules=[rule2])
        result = obsClient.setBucketDisPolicy(bucket_name, dis_policy2)
        assert result.status == 200 or result.status == 201

        # Operation 4 - Get updated policy
        result = obsClient.getBucketDisPolicy(bucket_name)
        assert result.status == 200
        assert result.body.rules[0]['id'] == 'rule2'

        # Operation 5 - Delete policy
        result = obsClient.deleteBucketDisPolicy(bucket_name)
        assert result.status == 204

        # Operation 6 - Verify deletion
        result = obsClient.getBucketDisPolicy(bucket_name)
        assert result.status != 200