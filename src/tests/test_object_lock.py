#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
SetBucketObjectLock (WORM) integration tests
Requires real OBS environment
"""
import time

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs import ObsClient
from obs import ObjectLockRule, ObjectLockConfiguration
from conftest import test_config

BUCKET_NAME = "pythonsdktestbucket-worm"
class TestObjectLock(object):
    """ObjectLock (WORM) policy test class"""

    def get_client(self):
        """Get OBS client instance"""
        client_type = "ObsClient"
        path_style = True if test_config["auth_type"] == "v2" else False
        client = ObsClient(
            access_key_id=test_config["ak"],
            secret_access_key=test_config["sk"],
            server=test_config["endpoint"],
            is_signature_negotiation=False,
            path_style=path_style
        )
        return client_type, client

    def setup_versioning(self, client):
        """Enable versioning on bucket (required for Object Lock)"""
        try:
            client.setBucketVersioning(BUCKET_NAME, status='Enabled')
        except Exception:
            pass

    def cleanup_versioning(self, client):
        """Suspend versioning after tests"""
        try:
            client.setBucketVersioning(BUCKET_NAME, status='Suspended')
        except Exception:
            pass

    # ==================== Feature Tests ====================

    def test_set_bucket_object_lock_basic(self):
        """Test: Set Object Lock policy"""
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME

        try:
            self.setup_versioning(client)
            rule = ObjectLockRule(
                days=30
            )
            config = ObjectLockConfiguration("Enabled", rule)
            resp = client.setBucketObjectLock(bucket_name, config)
            assert resp.status in [200, 201], f"Unexpected status: {resp.status}, reason: {resp.reason}"
        finally:
            self.cleanup_versioning(client)

    def test_get_bucket_object_lock(self):
        """Test: Get Object Lock policy"""
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME

        try:
            self.setup_versioning(client)
            rule = ObjectLockRule(
                days=60,
            )
            config = ObjectLockConfiguration("Enabled", rule)

            client.setBucketObjectLock(bucket_name, config)

            resp = client.getBucketObjectLock(bucket_name)
            assert resp.status == 200, f"Unexpected status: {resp.status}"
            assert resp.body is not None, "objectLockConfiguration should not be None"
            assert resp.body.rule is not None, "Should have a rule"
        finally:
            self.cleanup_versioning(client)

    # ==================== Boundary Tests ====================

    def test_set_bucket_object_lock_without_config(self):
        """Test: Set Object Lock policy without config"""
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME

        try:
            self.setup_versioning(client)
            rule = ObjectLockRule(days=30)
            config = ObjectLockConfiguration("Enabled", rule)
            resp = client.setBucketObjectLock(bucket_name, config)
            assert resp.status in [200, 201]
            resp = client.getBucketObjectLock(bucket_name)
            assert resp.status == 200, f"Unexpected status: {resp.status}"
            assert resp.body is not None, "objectLockConfiguration should not be None"
            assert resp.body.rule is not None, "Should have a rule"
            resp = client.setBucketObjectLock(bucket_name)
            assert resp.status in [200, 201]
            resp = client.getBucketObjectLock(bucket_name)
            assert resp.status == 200, f"Unexpected status: {resp.status}"
            assert resp.body is not None, "objectLockConfiguration should not be None"
            assert resp.body.rule is None, "Should not have a rule"
        finally:
            self.cleanup_versioning(client)


    # ==================== Parameter Validation Tests ====================

    def test_set_bucket_object_lock_missing_bucket(self):
        """Test: Missing required bucketName parameter"""
        client_type, client = self.get_client()

        rule = ObjectLockRule(days=30)
        config = ObjectLockConfiguration("Enabled", rule)

        with pytest.raises(Exception) as exc_info:
            client.setBucketObjectLock(None, config)
        assert 'bucketname' in str(exc_info.value).lower()

    def test_set_bucket_object_lock_with_wrong_days(self):
        """Test: With_wrong_days"""
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME

        # 最大值
        rule = ObjectLockRule(days=36500)
        config = ObjectLockConfiguration("Enabled", rule)
        resp = client.setBucketObjectLock(bucket_name, config)
        assert resp.status in [200, 201]
        # 最小值
        rule = ObjectLockRule(days=1)
        config = ObjectLockConfiguration("Enabled", rule)
        resp = client.setBucketObjectLock(bucket_name, config)
        assert resp.status in [200, 201]
        # 过大值
        rule = ObjectLockRule(days=36501)
        config = ObjectLockConfiguration("Enabled", rule)
        resp = client.setBucketObjectLock(bucket_name, config)
        assert resp.status == 400
        # 过小值
        rule = ObjectLockRule(days=0)
        config = ObjectLockConfiguration("Enabled", rule)
        resp = client.setBucketObjectLock(bucket_name, config)
        assert resp.status == 400


    def test_set_bucket_object_lock_with_wrong_years(self):
        """Test: With_wrong_years"""
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME

        # 最大值
        rule = ObjectLockRule(years=100)
        config = ObjectLockConfiguration("Enabled", rule)
        resp = client.setBucketObjectLock(bucket_name, config)
        assert resp.status in [200, 201]
        # 最小值
        rule = ObjectLockRule(years=1)
        config = ObjectLockConfiguration("Enabled", rule)
        resp = client.setBucketObjectLock(bucket_name, config)
        assert resp.status in [200, 201]
        # 过大值
        rule = ObjectLockRule(years=101)
        config = ObjectLockConfiguration("Enabled", rule)
        resp = client.setBucketObjectLock(bucket_name, config)
        assert resp.status == 400
        # 过小值
        rule = ObjectLockRule(years=0)
        config = ObjectLockConfiguration("Enabled", rule)
        resp = client.setBucketObjectLock(bucket_name, config)
        assert resp.status == 400

    def test_set_bucket_object_lock_with_wrong_objectLockEnabled(self):
        """Test: With_wrong_objectLockEnabled"""
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME

        rule = ObjectLockRule(years=1)
        config = ObjectLockConfiguration("Disabled", rule)
        resp = client.setBucketObjectLock(bucket_name, config)
        assert resp.status == 400
    # ==================== Lifecycle Tests ====================

    def test_object_lock_lifecycle(self):
        """Test: Complete Object Lock policy lifecycle"""
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME

        try:
            self.setup_versioning(client)
            # Create policy
            rule = ObjectLockRule(
                days=30,
            )
            config = ObjectLockConfiguration("Enabled", rule)

            create_resp = client.setBucketObjectLock(bucket_name, config)
            assert create_resp.status in [200, 201]

            # Get and verify policy
            get_resp = client.getBucketObjectLock(bucket_name)
            assert get_resp.status == 200
            assert get_resp.body is not None
            assert get_resp.body.rule is not None

            # Update policy
            rule_updated = ObjectLockRule(
                days=60,
            )
            config_updated = ObjectLockConfiguration("Enabled", rule_updated)

            update_resp = client.setBucketObjectLock(bucket_name, config_updated)
            assert update_resp.status in [200, 201]
        finally:
            self.cleanup_versioning(client)

    # ==================== object retention Tests ====================

    def test_put_object_retention_sucess(self):
        # 测试不带versionId成功添加对象保留策略
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME
        object_name = 'test-object-lock'
        try:
            self.setup_versioning(client)
            # 设置桶worm规则
            rule = ObjectLockRule(
                days=30,
            )
            config = ObjectLockConfiguration("Enabled", rule)

            resp = client.setBucketObjectLock(bucket_name, config)
            assert resp.status in [200, 201], f"Unexpected status: {resp.status}"
            # 上传对象
            put_resp = client.putContent(bucket_name, object_name, 'test')
            assert put_resp.status == 200, f"Unexpected status: {resp.status}"

            re_resp = client.putObjectRetention(bucket_name, object_name, 'COMPLIANCE', (int(time.time()) + 6048000)*1000)
            assert re_resp.status == 200, f"Unexpected status: {resp.status}"
        finally:
            self.cleanup_versioning(client)

    def test_put_version_object_retention_sucess(self):
        # 测试带versionId成功添加对象保留策略
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME
        object_name = 'test-object-lock-version'
        try:
            self.setup_versioning(client)
            # 设置桶worm规则
            rule = ObjectLockRule(
                days=30,
            )
            config = ObjectLockConfiguration("Enabled", rule)

            resp = client.setBucketObjectLock(bucket_name, config)
            assert resp.status in [200, 201], f"Unexpected status: {resp.status}"
            # 上传对象
            put_resp = client.putContent(bucket_name, object_name, 'test')
            assert put_resp.status == 200, f"Unexpected status: {resp.status}"

            re_resp = client.putObjectRetention(bucket_name, object_name, 'COMPLIANCE', (int(time.time()) + 6048000)*1000, put_resp.body['versionId'])
            assert re_resp.status == 200, f"Unexpected status: {resp.status}"
        finally:
            self.cleanup_versioning(client)

    def test_put_object_retention_faile_with_wrong_mode(self):
        # 测试带错误mode添加对象保留策略失败
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME
        object_name = 'test-object-lock-version'
        try:
            self.setup_versioning(client)
            # 设置桶worm规则
            rule = ObjectLockRule(
                days=30,
            )
            config = ObjectLockConfiguration("Enabled", rule)

            resp = client.setBucketObjectLock(bucket_name, config)
            assert resp.status in [200, 201], f"Unexpected status: {resp.status}"
            # 上传对象
            put_resp = client.putContent(bucket_name, object_name, 'test')
            assert put_resp.status == 200, f"Unexpected status: {resp.status}"
            re_resp = client.putObjectRetention(bucket_name, object_name, 'wrong_mode', (int(time.time()) + 6048000)*1000, put_resp.body['versionId'])

            assert re_resp.status == 400, f"Unexpected status: {resp.status}"
            assert re_resp.errorMessage == 'The XML you provided was not well-formed or did not validate against our published schema', f"Unexpected errorMeassage: {resp.errorMeassage}"

        finally:
            self.cleanup_versioning(client)

    def test_put_object_retention_faile_with_wrong_retainUntilDate(self):
        # 测试带错误retainUntilDate添加对象保留策略失败
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME
        object_name = 'test-object-lock-version'
        try:
            self.setup_versioning(client)
            # 设置桶worm规则
            rule = ObjectLockRule(
                days=30,
            )
            config = ObjectLockConfiguration("Enabled", rule)

            resp = client.setBucketObjectLock(bucket_name, config)
            assert resp.status in [200, 201], f"Unexpected status: {resp.status}"
            # 上传对象
            put_resp = client.putContent(bucket_name, object_name, 'test')
            assert put_resp.status == 200, f"Unexpected status: {resp.status}"
            re_resp = client.putObjectRetention(bucket_name, object_name, 'COMPLIANCE', (int(time.time()) + 604800)*1000, put_resp.body['versionId'])

            assert re_resp.status == 400, f"Unexpected status: {resp.status}"
            assert re_resp.errorMessage == 'The retention period date must be later than the current or the configured date.', f"Unexpected errorMeassage: {resp.errorMeassage}"

        finally:
            self.cleanup_versioning(client)

    def test_get_object_retention_success(self):
        """Test: Get object WORM policy successfully"""
        client_type, client = self.get_client()
        bucket_name = BUCKET_NAME
        object_name = 'test-object-lock-get-retention'

        try:
            # Step 1: Enable versioning on bucket
            versioning_resp = client.setBucketVersioning(bucket_name, status='Enabled')
            assert versioning_resp.status == 200, f"Enable versioning failed: {versioning_resp.status}"

            # Step 2: Set bucket WORM policy with days=30
            rule = ObjectLockRule(days=30)
            config = ObjectLockConfiguration("Enabled", rule)
            worm_resp = client.setBucketObjectLock(bucket_name, config)
            assert worm_resp.status in [200, 201], f"Set bucket WORM policy failed: {worm_resp.status}"

            # Step 3: Upload object
            put_resp = client.putContent(bucket_name, object_name, 'test content')
            assert put_resp.status == 200, f"Upload object failed: {put_resp.status}"

            # Get the versionId
            version_id = put_resp.body.get('versionId')

            # Step 4: Set object WORM retention policy with retainUntilDate > 30 days
            retain_until_date = (int(time.time()) + 60 * 60 * 24 * 31) * 1000  # Current time + 31 days (in milliseconds)
            retention_resp = client.putObjectRetention(
                bucket_name,
                object_name,
                'COMPLIANCE',
                retain_until_date,
                version_id
            )
            assert retention_resp.status == 200, f"Set object retention failed: {retention_resp.status}"

            # Step 5: Get object WORM retention policy via getObjectMetadata
            get_metadata_resp = client.getObjectMetadata(bucket_name, object_name, versionId=version_id)
            assert get_metadata_resp.status == 200, f"Get object metadata failed: {get_metadata_resp.status}"

            # Verify the object-lock-retain-until-date from response headers
            # header is a list, convert to dict to get the value
            headers_dict = dict(get_metadata_resp.header)
            retain_until_header = headers_dict.get('object-lock-retain-until-date')
            assert retain_until_header is not None, "object-lock-retain-until-date should not be None in headers"

            # The header value is in ISO 8601 format, parse it to compare
            # Convert to timestamp for comparison
            from datetime import datetime, timezone
            # Handle both formats: with microseconds and without
            try:
                retain_until_dt = datetime.strptime(retain_until_header, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                retain_until_dt = datetime.strptime(retain_until_header, '%Y-%m-%dT%H:%M:%SZ')
            # Convert to UTC timestamp
            retain_until_dt_utc = retain_until_dt.replace(tzinfo=timezone.utc)
            retain_until_timestamp = int(retain_until_dt_utc.timestamp() * 1000)

            # Check that the retainUntilDate is approximately current time + 31 days
            expected_retain_until = int(time.time()) * 1000 + 60 * 60 * 24 * 31 * 1000
            # Allow some tolerance (within 1 hour to handle timezone differences)
            assert abs(retain_until_timestamp == expected_retain_until), \
                f"object-lock-retain-until-date mismatch: expected ~{expected_retain_until}, got {retain_until_timestamp}"

        finally:
            # Cleanup: delete object and suspend versioning
            try:
                client.deleteObject(bucket_name, object_name)
            except Exception:
                pass
            self.cleanup_versioning(client)
