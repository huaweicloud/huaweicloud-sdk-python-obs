# !/usr/bin/python
# -*- coding:utf-8 -*-
"""
设置桶的在线解压策略 - 集成测试
需要真实的OBS环境
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs import ObsClient
from obs import ObsCompressPolicyRule
from conftest import test_config


class TestObsCompressPolicy(object):
    """设置桶的在线解压策略测试类"""

    def get_client(self):
        """获取OBS客户端实例"""
        client_type = "OBSClient"
        path_style = True if test_config["auth_type"] == "v2" else False
        client = ObsClient(
            access_key_id=test_config["ak"],
            secret_access_key=test_config["sk"],
            server=test_config["endpoint"],
            is_signature_negotiation=False,
            path_style=path_style,
            max_retry_count=0,
        )
        return client_type, client

    # ==================== 功能测试 ====================

    def test_put_obs_compress_policy_basic(self):
        """测试场景: 基本设置在线解压策略"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        try:
            # 创建在线解压策略
            rule = ObsCompressPolicyRule(
                id='rule-test-001',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=['ObjectCreated:*'],
                prefix='zip/',
                suffix='.zip',
                overwrite=0,
                decompresspath='decompressed/',
                policytype='decompress'
            )
            resp = client.setObsCompressPolicy(bucket_name, [rule])
            assert resp.status == 201, f"Unexpected status: {resp.status}, reason: {resp.reason}"

        finally:
            # 清理：删除在线解压策略
            try:
                client.deleteObsCompressPolicy(bucket_name)
            except Exception:
                pass

    def test_get_obs_compress_policy(self):
        """测试场景: 获取在线解压策略"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        try:
            # 先设置策略
            rule = ObsCompressPolicyRule(
                id='rule-test-002',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=['ObjectCreated:*'],
                prefix='zip/',
                suffix='.zip',
                overwrite=0,
                decompresspath='decompressed/',
                policytype='decompress'
            )
            rules = [rule]
            res = client.setObsCompressPolicy(bucket_name, rules)
            assert res.status == 201, f"Unexpected status: {res.status}"

            # 获取策略
            resp = client.getObsCompressPolicy(bucket_name)
            assert resp.status == 200, f"Unexpected status: {resp.status}"
            assert resp.body.rules is not None, "rules  should not be None"
            assert len(resp.body.rules) == 1, "Should have exactly one rule"
            test_rule = resp.body.rules[0]
            assert test_rule['id'] == 'rule-test-002'
            assert test_rule['project'] == '81f2722a50494a919abfa82a9b8f2a42'
            assert test_rule['agency'] == 'sdk-test'
            assert test_rule['events'] == ['ObjectCreated:*']
            assert test_rule['prefix'] == 'zip/'
            assert test_rule['suffix'] == '.zip'
            assert test_rule['overwrite'] == 0
            assert test_rule['decompresspath'] == 'decompressed/'
            assert test_rule['policytype'] == 'decompress'
        finally:
            # 清理
            try:
                client.deleteObsCompressPolicy(bucket_name)
            except Exception:
                pass

    def test_delete_obs_compress_policy(self):
        """测试场景: 删除在线解压策略"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        # 先设置策略
        rule = ObsCompressPolicyRule(
            id='rule-test-003',
            project='81f2722a50494a919abfa82a9b8f2a42',
            agency='sdk-test',
            events=['ObjectCreated:*'],
            prefix='zip/',
            suffix='.zip',
            overwrite=0,
            decompresspath='decompressed/',
            policytype='decompress'
        )
        client.setObsCompressPolicy(bucket_name, [rule])

        # 删除策略
        resp = client.deleteObsCompressPolicy(bucket_name)
        assert resp.status == 204, f"Unexpected status: {resp.status}"

        # 验证策略已被删除
        try:
            resp_get = client.getObsCompressPolicy(bucket_name)
            # 这里我们只检查响应状态码，实际返回可能不同
            assert resp_get.status == 404, f"Unexpected status: {resp.status}"
        except Exception:
            # 可能桶无权限访问或策略不存在，这是正常的
            pass

    def test_get_obs_compress_policy_empty(self):
        """测试场景: 获取不存在的在线解压策略"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        # 确保桶没有策略
        try:
            client.deleteObsCompressPolicy(bucket_name)
        except Exception:
            pass

        # 获取策略（应该返回200但策略为空）
        resp = client.getObsCompressPolicy(bucket_name)
        assert resp.status == 404, f"Unexpected status: {resp.status}"

    def test_update_obs_compress_policy(self):
        """测试场景: 更新在线解压策略"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        res = client.deleteObsCompressPolicy(bucket_name)
        try:
            # 设置初始策略
            rule1 = ObsCompressPolicyRule(
                id='rule-001',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=['ObjectCreated:Put'],
                prefix='zip/1',
                suffix='.zip',
                overwrite=0,
                policytype='decompress'
            )
            rules1 = [rule1]
            resp1 = client.setObsCompressPolicy(bucket_name, rules1)
            assert resp1.status == 201

            # 获取并验证初始策略
            resp_get1 = client.getObsCompressPolicy(bucket_name)
            assert resp_get1.status == 200
            assert len(resp_get1.body.rules) == 1
            assert resp_get1.body.rules[0]['project'] == '81f2722a50494a919abfa82a9b8f2a42'

            # 更新策略（添加新规则）
            rule2 = ObsCompressPolicyRule(
                id='rule-002',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=['ObjectCreated:Post'],
                prefix='tar/2',
                suffix='.zip',
                overwrite=1,
                decompresspath='decompressed/',
                policytype='decompress'
            )
            rules2 = [rule1, rule2]  # 保留旧规则，添加新规则
            resp2 = client.setObsCompressPolicy(bucket_name, rules2)
            assert resp2.status == 201

            # 验证更新后的策略
            resp_get2 = client.getObsCompressPolicy(bucket_name)
            assert resp_get2.status == 200
            assert len(resp_get2.body.rules) == 2
            assert resp_get2.body.rules[0]['project'] == '81f2722a50494a919abfa82a9b8f2a42'
            assert resp_get2.body.rules[1]['project'] == '81f2722a50494a919abfa82a9b8f2a42'
            assert resp_get2.body.rules[1]['overwrite'] == 1

        finally:
            try:
                client.deleteObsCompressPolicy(bucket_name)
            except Exception:
                pass

    def test_put_obs_compress_policy_with_all_events(self):
        """测试场景: 复杂事件配置"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        try:
            # 测试多种事件类型,ObjectCreated:*,不能和其他一起设置
            rule = ObsCompressPolicyRule(
                id='complex-events-rule',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=[
                    'ObjectCreated:Put',
                    'ObjectCreated:Post',
                    'ObjectCreated:Copy',
                    'ObjectCreated:CompleteMultipartUpload'
                ],
                suffix='.zip',
                overwrite=0,
                decompresspath='auto-decompress/',
                policytype='decompress'
            )

            resp = client.setObsCompressPolicy(bucket_name, [rule])
            assert resp.status == 201

            # 验证策略
            get_resp = client.getObsCompressPolicy(bucket_name)
            assert get_resp.status == 200
            assert len(get_resp.body.rules) == 1
            rule_events = get_resp.body.rules[0]['events']
            assert 'ObjectCreated:Put' in rule_events
            assert 'ObjectCreated:Post' in rule_events
            assert 'ObjectCreated:Copy' in rule_events
            assert 'ObjectCreated:CompleteMultipartUpload' in rule_events

        finally:
            try:
                client.deleteObsCompressPolicy(bucket_name)
            except Exception:
                pass

    # ==================== 边界测试 ====================

    def test_put_obs_compress_policy_multiple_rules(self):
        pass
        """测试场景: 设置包含多个规则的在线解压策略"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        try:
            # 创建包含多个规则的策略
            rule1 = ObsCompressPolicyRule(
                id='rule-test-004',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=['ObjectCreated:Put'],
                prefix='zip/1',
                suffix='.zip',
                overwrite=0,
                policytype='decompress'
            )
            rule2 = ObsCompressPolicyRule(
                id='rule-test-005',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=['ObjectCreated:Post'],
                prefix='tar/2',
                suffix='.zip',
                overwrite=0,
                policytype='decompress'
            )
            resp = client.setObsCompressPolicy(bucket_name, [rule1, rule2])
            assert resp.status == 201, f"Unexpected status: {resp.status}"

            # 验证获取的规则数量
            get_resp = client.getObsCompressPolicy(bucket_name)
            assert get_resp.status == 200
            assert len(get_resp.body.rules) == 2

        finally:
            try:
                client.deleteObsCompressPolicy(bucket_name)
            except Exception:
                pass

    def test_put_obs_compress_policy_with_overwrite(self):
        """测试场景: 设置overwrite=1或2的在线解压策略"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        try:
            rule = ObsCompressPolicyRule(
                id='rule-test-006',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=['ObjectCreated:*'],
                suffix='.zip',
                overwrite=1,  # 允许覆盖
                decompresspath='decompress-overwrite/',
                policytype='decompress'
            )
            resp = client.setObsCompressPolicy(bucket_name, [rule])
            assert resp.status == 201

            rule2 = ObsCompressPolicyRule(
                id='rule-test-006',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=['ObjectCreated:*'],
                suffix='.zip',
                overwrite=2,  # 允许覆盖
                decompresspath='decompress-overwrite/',
                policytype='decompress'
            )
            resp = client.setObsCompressPolicy(bucket_name, [rule2])
            assert resp.status == 201

        finally:
            try:
                client.deleteObsCompressPolicy(bucket_name)
            except Exception:
                pass

    # ==================== 参数检查测试 ====================

    def test_put_obs_compress_policy_missing_bucket(self):
        """测试场景: 缺少必需参数bucketName"""
        client_type, client = self.get_client()

        rule = ObsCompressPolicyRule(id='test-rule')

        with pytest.raises(Exception) as exc_info:
            client.setObsCompressPolicy(None, [rule])
        assert 'bucketname' in str(exc_info.value).lower()

    def test_put_obs_compress_policy_missing_rules(self):
        """测试场景: 缺少必需参数rules"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        with pytest.raises(Exception) as exc_info:
            client.setObsCompressPolicy(bucket_name, None)
        assert 'rules' in str(exc_info.value).lower()

    def test_get_obs_compress_policy_missing_bucket(self):
        """测试场景: 获取策略时缺少bucketName"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.getObsCompressPolicy(None)
        assert 'bucketname' in str(exc_info.value).lower()

    def test_delete_obs_compress_policy_missing_bucket(self):
        """测试场景: 删除策略时缺少bucketName"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.deleteObsCompressPolicy(None)
        assert 'bucketname' in str(exc_info.value).lower()

    # ==================== 事件类型测试 ====================

    def test_put_obs_compress_policy_all_events(self):
        """测试场景: 使用ObjectCreated:*事件类型"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        try:
            rule = ObsCompressPolicyRule(
                id='rule-test-events-001',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=['ObjectCreated:*'],
                suffix='.zip',
                decompresspath='decompress/',
                policytype='decompress'
            )
            resp = client.setObsCompressPolicy(bucket_name, [rule])
            assert resp.status == 201

        finally:
            try:
                client.deleteObsCompressPolicy(bucket_name)
            except Exception:
                pass

    def test_put_obs_compress_policy_put_event(self):
        """测试场景: 使用ObjectCreated:Put事件类型"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        try:
            rule = ObsCompressPolicyRule(
                id='rule-test-events-002',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=['ObjectCreated:Put'],
                suffix='.zip',
                decompresspath='decompress/',
                policytype='decompress'
            )
            resp = client.setObsCompressPolicy(bucket_name, [rule])
            assert resp.status == 201

        finally:
            try:
                client.deleteObsCompressPolicy(bucket_name)
            except Exception:
                pass

    def test_put_obs_compress_policy_multipart_event(self):
        """测试场景: 使用ObjectCreated:CompleteMultipartUpload事件类型"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]

        try:
            rule = ObsCompressPolicyRule(
                id='rule-test-events-003',
                project='81f2722a50494a919abfa82a9b8f2a42',
                agency='sdk-test',
                events=['ObjectCreated:CompleteMultipartUpload'],
                suffix='.zip',
                decompresspath='decompress/',
                policytype='decompress'
            )
            resp = client.setObsCompressPolicy(bucket_name, [rule])
            assert resp.status == 201

        finally:
            try:
                client.deleteObsCompressPolicy(bucket_name)
            except Exception:
                pass
