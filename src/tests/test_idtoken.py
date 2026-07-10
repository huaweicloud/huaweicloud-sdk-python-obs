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
IdToken联邦认证Mock测试

与test_idtoken_integration.py场景完全对齐，但所有服务端返回使用mock，
不真实访问IAM和OBS服务。

Mock策略:
  - _do_federation_token_request: mock返回X-Subject-Token
  - _do_temporary_aksk_request: mock返回临时AKSK凭证
  - ObsClient操作: 不创建真实ObsClient，通过provider直接验证凭证获取逻辑

测试用例:
  tc_python_alpha_oidc_token_01-08: 基础功能
  tc_09-11: OBS操作（仅验证凭证获取，不调用真实OBS）
  tc_12-14: 缓存/互斥
  tc_15-16: 错误路径/非JWT
  tc_17-20: 边界值/配置优先级
  tc_21-30: scope模式/并发
"""

import json
import os
import tempfile
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from obs import (
    IdTokenCredentialsProvider,
    IdTokenAuthException,
    FederationTokenException,
    IdTokenParamsException,
    IdTokenExpiredException,
    IdTokenInvalidException,
    TemporaryAKSKException,
)

# ============================================================
# Mock常量与辅助函数
# ============================================================

MOCK_FEDERATION_TOKEN = "mock-federation-token-uuid-12345678"
MOCK_ACCESS_KEY = "MOCKAKXXXXXXXXXXXXXX"
MOCK_SECRET_KEY = "MockSKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
MOCK_SECURITY_TOKEN = "MockSecurityTokenXXXXXXXXXXXXXXXXXXXX"
MOCK_PROJECT_ID = "mock-project-id-1234567890abcdef"
MOCK_PROJECT_NAME = "mock-project-name"
MOCK_DOMAIN_ID = "mock-domain-id-1234567890abcdef"
MOCK_DOMAIN_NAME = "mock-domain-name"
MOCK_IDP_ID = "mock-idp-id"
MOCK_IAM_ENDPOINT = "https://iam.mock.huaweicloud.com"
MOCK_SERVER = "obs.cn-north-4.myhuaweicloud.com"

# 有效的JWT格式ID Token (三个base64段用.连接)
MOCK_VALID_ID_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjk5OTk5OTk5OTksInN1YiI6InRlc3QifQ.mock_signature"


def _default_expires_at():
    """生成默认的凭证过期时间字符串（当前时间+24小时）"""
    return (datetime.utcnow() + timedelta(seconds=86400)).strftime('%Y-%m-%dT%H:%M:%S.000000Z')


def _make_credential_result(expires_at=None, access=None, secret=None, securitytoken=None):
    """构造_get_temporary_aksk返回的扁平凭证字典（对应_do_temporary_aksk_request的返回值）"""
    return {
        'access': access or MOCK_ACCESS_KEY,
        'secret': secret or MOCK_SECRET_KEY,
        'securitytoken': securitytoken or MOCK_SECURITY_TOKEN,
        'expires_at': expires_at or _default_expires_at()
    }


def _mock_federation_token_success(self, url, headers, body):
    """Mock _do_federation_token_request 成功返回"""
    return MOCK_FEDERATION_TOKEN


def _mock_federation_token_401_expired(self, url, headers, body):
    """Mock _do_federation_token_request 返回401 Token过期"""
    raise IdTokenExpiredException(
        code='IAM.0011',
        message='Token expired',
        status=401
    )


def _mock_federation_token_401_invalid(self, url, headers, body):
    """Mock _do_federation_token_request 返回401 Token无效"""
    raise IdTokenInvalidException(
        code='IAM.0012',
        message='Invalid token',
        status=401
    )


def _mock_federation_token_error(self, url, headers, body):
    """Mock _do_federation_token_request 返回通用错误"""
    raise FederationTokenException(
        code='IAM.0030',
        message='Federation error',
        status=400
    )


def _mock_temporary_aksk_success(self, url, headers, body):
    """Mock _do_temporary_aksk_request 成功返回"""
    return _make_credential_result()


def _mock_temporary_aksk_with_expires(self, url, headers, body):
    """Mock _do_temporary_aksk_request，根据请求中的duration_seconds返回对应过期时间"""
    duration = 86400
    try:
        duration = body['auth']['identity']['token']['duration_seconds']
    except (KeyError, TypeError):
        pass
    expires_at = (datetime.utcnow() + timedelta(seconds=duration)).strftime(
        '%Y-%m-%dT%H:%M:%S.000000Z')
    return _make_credential_result(expires_at=expires_at)


def _mock_temporary_aksk_error(self, url, headers, body):
    """Mock _do_temporary_aksk_request 返回错误"""
    raise TemporaryAKSKException(
        code='IAM.0040',
        message='Failed to get temporary AKSK',
        status=400
    )


def _create_temp_config_file(config_dict):
    """创建临时配置文件，返回路径"""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(config_dict, tmp)
    tmp.close()
    return tmp.name


def _create_temp_token_file(token_content):
    """创建临时token文件，返回路径"""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    tmp.write(token_content)
    tmp.close()
    return tmp.name


def _make_valid_config_dict():
    """构造有效的配置字典（供临时配置文件使用）"""
    return {
        'id_token': MOCK_VALID_ID_TOKEN,
        'idp_id': MOCK_IDP_ID,
        'project_id': MOCK_PROJECT_ID,
        'project_name': MOCK_PROJECT_NAME,
        'iam_endpoint': MOCK_IAM_ENDPOINT,
    }


def _create_valid_config_file():
    """创建有效的临时配置文件，返回路径"""
    return _create_temp_config_file(_make_valid_config_dict())


class TestIdToken:
    """IdToken联邦认证Mock测试 - 与集成测试场景一一对应"""

    def _get_valid_config_file(self):
        """获取有效的IdToken配置文件路径"""
        return _create_valid_config_file()

    def _get_valid_oidc_token_file(self):
        """获取有效的oidc-token文件路径"""
        return _create_temp_token_file(MOCK_VALID_ID_TOKEN)

    def _get_domain_id(self):
        """返回mock的domain_id"""
        return MOCK_DOMAIN_ID

    def _read_config_as_dict(self):
        """读取有效配置文件内容为字典"""
        config = _make_valid_config_dict()
        # 如果oidc_token_file存在，模拟配置文件中可能包含此字段
        return config

    def _create_temp_config_file(self, config_dict):
        """创建临时配置文件，返回路径"""
        return _create_temp_config_file(config_dict)

    # ================================================================
    # tc_python_alpha_oidc_token_01: 使用有效 ID Token 获取凭证成功
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_python_alpha_oidc_token_01_list_buckets_with_valid_id_token(self):
        """
        tc_python_alpha_oidc_token_01: 使用有效 ID Token 获取凭证成功

        测试步骤:
          1. 读取有效的 ID Token 配置文件(包含有效id_token、idp_id、project_id/project_name)
          2. 创建IdTokenCredentialsProvider
          3. 获取凭证验证成功

        预期结果:
          IdTokenCredentialsProvider初始化成功，凭证获取成功，包含accessKey/secretKey/securityToken
        """
        config_file = self._get_valid_config_file()
        try:
            provider = IdTokenCredentialsProvider(config_file=config_file)
            cred = provider.get_credentials()

            assert cred is not None, "凭证不应为None"
            assert cred.get('accessKey') == MOCK_ACCESS_KEY, \
                "accessKey应为mock值"
            assert cred.get('secretKey') == MOCK_SECRET_KEY, \
                "secretKey应为mock值"
            assert cred.get('securityToken') == MOCK_SECURITY_TOKEN, \
                "securityToken应为mock值"
        finally:
            os.unlink(config_file)

    # ================================================================
    # tc_python_alpha_oidc_token_02: 使用过期 ID Token 获取凭证失败
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_401_expired)
    def test_tc_python_alpha_oidc_token_02_list_buckets_with_expired_id_token(self):
        """
        tc_python_alpha_oidc_token_02: 使用过期 ID Token 获取凭证失败

        测试步骤:
          1. 创建临时JSON配置文件，填入过期的id_token
          2. 创建IdTokenCredentialsProvider
          3. 调用get_credentials()

        预期结果:
          抛出IdTokenAuthException（IdTokenExpiredException）
        """
        expired_token = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjF9.expired_signature'
        config = _make_valid_config_dict()
        config['id_token'] = expired_token

        tmp_config_path = _create_temp_config_file(config)
        try:
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            with pytest.raises(IdTokenAuthException):
                provider.get_credentials()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_python_alpha_oidc_token_03: 使用错误 IdP ID 获取凭证失败
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_401_invalid)
    def test_tc_python_alpha_oidc_token_03_list_buckets_with_wrong_idp_id(self):
        """
        tc_python_alpha_oidc_token_03: 使用错误 IdP ID 获取凭证失败

        测试步骤:
          1. 创建临时JSON配置文件，填入有效的id_token、错误的idp_id
          2. 创建IdTokenCredentialsProvider
          3. 调用get_credentials()

        预期结果:
          抛出IdTokenAuthException
        """
        config = _make_valid_config_dict()
        config['idp_id'] = 'wrong-idp-id-99999'

        tmp_config_path = _create_temp_config_file(config)
        try:
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            with pytest.raises(IdTokenAuthException):
                provider.get_credentials()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_python_alpha_oidc_token_04: 使用错误 project_id 获取凭证失败
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_error)
    def test_tc_python_alpha_oidc_token_04_list_buckets_with_wrong_project_id(self):
        """
        tc_python_alpha_oidc_token_04: 使用错误 project_id 获取凭证失败

        测试步骤:
          1. 创建临时JSON配置文件，填入有效的id_token、错误的project_id、有效的idp_id
          2. 创建IdTokenCredentialsProvider
          3. 调用get_credentials()

        预期结果:
          抛出IdTokenAuthException（FederationTokenException）
        """
        config = _make_valid_config_dict()
        config.pop('project_name', None)
        config['project_id'] = 'wrong-project-id-99999'

        tmp_config_path = _create_temp_config_file(config)
        try:
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            with pytest.raises(IdTokenAuthException):
                provider.get_credentials()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_python_alpha_oidc_token_05: 使用错误 domain_id 获取凭证失败
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_error)
    def test_tc_python_alpha_oidc_token_05_list_buckets_with_wrong_domain_id(self):
        """
        tc_python_alpha_oidc_token_05: 使用错误 domain_id 获取凭证失败

        测试步骤:
          1. 创建临时JSON配置文件，填入有效的id_token、错误的domain_id
          2. 创建IdTokenCredentialsProvider
          3. 调用get_credentials()

        预期结果:
          抛出IdTokenAuthException（FederationTokenException）
        """
        config = _make_valid_config_dict()
        config.pop('project_id', None)
        config.pop('project_name', None)
        config.pop('domain_name', None)
        config['domain_id'] = 'wrong-domain-id-99999'

        tmp_config_path = _create_temp_config_file(config)
        try:
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            with pytest.raises(IdTokenAuthException):
                provider.get_credentials()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_python_alpha_oidc_token_06: 凭证手动刷新成功
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_with_expires)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_python_alpha_oidc_token_06_credential_manual_refresh(self):
        """
        tc_python_alpha_oidc_token_06: 凭证手动刷新成功

        测试步骤:
          1. 创建IdTokenCredentialsProvider
          2. 获取初始凭证
          3. 调用provider.refresh()手动触发刷新
          4. 再次调用get_credentials()获取刷新后的凭证

        预期结果:
          初始凭证非空，手动刷新后凭证非空
        """
        config_file = self._get_valid_config_file()
        try:
            provider = IdTokenCredentialsProvider(config_file=config_file)

            # 步骤2: 获取初始凭证
            initial_cred = provider.get_credentials()
            assert initial_cred is not None, "初始凭证不应为None"
            assert initial_cred.get('accessKey'), "初始凭证应包含accessKey"
            assert initial_cred.get('secretKey'), "初始凭证应包含secretKey"
            assert initial_cred.get('securityToken'), "初始凭证应包含securityToken"

            # 步骤3: 手动刷新
            provider.refresh()

            # 验证缓存被清除
            assert provider._ak is None, "刷新后_ak应为None"
            assert provider._sk is None, "刷新后_sk应为None"
            assert provider._token is None, "刷新后_token应为None"
            assert provider._expires is None, "刷新后_expires应为None"

            # 步骤4: 获取刷新后的凭证
            refreshed_cred = provider.get_credentials()
            assert refreshed_cred is not None, "刷新后的凭证不应为None"
            assert refreshed_cred.get('accessKey'), "刷新后的凭证应包含accessKey"
            assert refreshed_cred.get('secretKey'), "刷新后的凭证应包含secretKey"
            assert refreshed_cred.get('securityToken'), "刷新后的凭证应包含securityToken"
        finally:
            os.unlink(config_file)

    # ================================================================
    # tc_python_alpha_oidc_token_07: 凭证自动刷新成功
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request')
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_python_alpha_oidc_token_07_credential_auto_refresh(self, mock_aksk):
        """
        tc_python_alpha_oidc_token_07: 凭证自动刷新成功

        测试步骤:
          1. 创建provider，设置极短的刷新窗口
          2. 获取初始凭证（mock返回即将过期的凭证）
          3. 再次获取凭证，触发自动刷新（mock返回新凭证）

        预期结果:
          自动刷新被触发，新凭证的过期时间晚于旧凭证
        """
        # 第一次获取：返回即将过期的凭证（1秒后过期，refresh_before_seconds=890，
        # 所以立刻进入刷新窗口）
        first_expires = (datetime.utcnow() + timedelta(seconds=1)).strftime(
            '%Y-%m-%dT%H:%M:%S.000000Z')
        first_cred = _make_credential_result(
            access=MOCK_ACCESS_KEY + "_V1",
            expires_at=first_expires)

        # 第二次获取：返回新的凭证
        second_expires = (datetime.utcnow() + timedelta(seconds=900)).strftime(
            '%Y-%m-%dT%H:%M:%S.000000Z')
        second_cred = _make_credential_result(
            access=MOCK_ACCESS_KEY + "_V2",
            expires_at=second_expires)

        mock_aksk.side_effect = [first_cred, second_cred]

        config_file = self._get_valid_config_file()
        try:
            # 创建provider，设置极短的刷新窗口
            provider = IdTokenCredentialsProvider(
                config_file=config_file,
                refresh_before_seconds=890,
                credential_expires_seconds=900,
            )

            # 获取初始凭证
            initial_cred = provider.get_credentials()
            assert initial_cred is not None, "初始凭证不应为None"
            assert initial_cred.get('accessKey') == MOCK_ACCESS_KEY + "_V1"

            initial_expires = provider._expires

            # 凭证已过期（1秒后），再次获取触发自动刷新
            refreshed_cred = provider.get_credentials()
            assert refreshed_cred is not None, "刷新后的凭证不应为None"
            assert refreshed_cred.get('accessKey') == MOCK_ACCESS_KEY + "_V2"

            # 验证自动刷新被触发：新凭证过期时间晚于旧凭证
            assert provider._expires > initial_expires, \
                "自动刷新后凭证过期时间应晚于初始凭证过期时间"
        finally:
            os.unlink(config_file)

    # ================================================================
    # tc_python_alpha_oidc_token_08: 临时aksk有效期最大值测试成功
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_with_expires)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_python_alpha_oidc_token_08_max_credential_expires_seconds(self):
        """
        tc_python_alpha_oidc_token_08: 临时aksk有效期最大值测试成功

        测试步骤:
          1. 创建provider，设置credential_expires_seconds=43200
          2. 获取凭证验证成功

        预期结果:
          凭证获取成功
        """
        config_file = self._get_valid_config_file()
        try:
            provider = IdTokenCredentialsProvider(
                config_file=config_file,
                credential_expires_seconds=43200,
            )

            cred = provider.get_credentials()
            assert cred is not None, "凭证不应为None"
            assert cred.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(config_file)

    # ================================================================
    # tc_09: 凭证获取后可执行OBS操作（mock验证凭证获取成功）
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_09_credential_for_obs_operations(self):
        """
        tc_09: 凭证获取后可执行OBS操作（mock验证）

        原集成测试执行完整OBS生命周期(createBucket/putObject/getObject/headObject/
        listObjects/deleteObject/deleteBucket)，此处验证凭证获取成功即可。

        测试步骤:
          1. 使用有效配置创建provider
          2. 获取凭证

        预期结果:
          凭证获取成功，包含完整的accessKey/secretKey/securityToken
        """
        config_file = self._get_valid_config_file()
        try:
            provider = IdTokenCredentialsProvider(config_file=config_file)
            cred = provider.get_credentials()

            assert cred is not None
            assert cred.get('accessKey') == MOCK_ACCESS_KEY
            assert cred.get('secretKey') == MOCK_SECRET_KEY
            assert cred.get('securityToken') == MOCK_SECURITY_TOKEN
        finally:
            os.unlink(config_file)

    # ================================================================
    # tc_10: Dict方式初始化Provider
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_10_dict_init_provider(self):
        """
        tc_10: Dict方式初始化Provider

        测试步骤:
          1. 使用有效配置字典创建IdTokenCredentialsProvider
          2. 获取凭证验证成功

        预期结果:
          Provider创建成功，凭证获取成功
        """
        config = _make_valid_config_dict()
        provider = IdTokenCredentialsProvider(**config)

        cred = provider.get_credentials()
        assert cred is not None, "凭证不应为None"
        assert cred.get('accessKey'), "凭证应包含accessKey"

    # ================================================================
    # tc_11: 实例方式初始化
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_11_provider_instance_init(self):
        """
        tc_11: 实例方式初始化

        测试步骤:
          1. 先创建IdTokenCredentialsProvider实例
          2. 使用该实例获取凭证

        预期结果:
          凭证获取成功
        """
        config_file = self._get_valid_config_file()
        try:
            provider = IdTokenCredentialsProvider(config_file=config_file)

            cred = provider.get_credentials()
            assert cred is not None, "凭证不应为None"
            assert cred.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(config_file)

    # ================================================================
    # tc_12: 凭证缓存命中验证
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_with_expires)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_12_credential_cache_hit(self):
        """
        tc_12: 凭证缓存命中验证

        测试步骤:
          1. 创建IdTokenCredentialsProvider
          2. 调用get_credentials()获取初始凭证
          3. 再次调用get_credentials()
          4. 比较两次返回值

        预期结果:
          连续两次get_credentials()返回相同的accessKey和securityToken
        """
        config_file = self._get_valid_config_file()
        try:
            provider = IdTokenCredentialsProvider(config_file=config_file)

            # 获取初始凭证
            cred1 = provider.get_credentials()
            assert cred1 is not None, "初始凭证不应为None"

            # 再次获取，应命中缓存
            cred2 = provider.get_credentials()
            assert cred2 is not None, "缓存凭证不应为None"

            assert cred2.get('accessKey') == cred1.get('accessKey'), \
                "缓存命中时accessKey应相同"
            assert cred2.get('secretKey') == cred1.get('secretKey'), \
                "缓存命中时secretKey应相同"
            assert cred2.get('securityToken') == cred1.get('securityToken'), \
                "缓存命中时securityToken应相同"
        finally:
            os.unlink(config_file)

    # ================================================================
    # tc_13: Domain-only scope认证
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_13_domain_only_scope(self):
        """
        tc_13: Domain-only scope认证

        测试步骤:
          1. 创建配置，移除project相关字段，仅保留domain_id
          2. 创建IdTokenCredentialsProvider
          3. 获取凭证验证成功

        预期结果:
          凭证获取成功
        """
        config = _make_valid_config_dict()
        config.pop('project_id', None)
        config.pop('project_name', None)
        config['domain_id'] = self._get_domain_id()

        tmp_config_path = _create_temp_config_file(config)
        try:
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            cred = provider.get_credentials()
            assert cred is not None, "凭证不应为None"
            assert cred.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_14: project和domain互斥验证
    # ================================================================

    def test_tc_14_project_and_domain_mutually_exclusive(self):
        """
        tc_14: project和domain互斥验证

        Python SDK中project和domain是互斥的，同时指定应抛出IdTokenParamsException。

        测试步骤:
          1. 创建临时配置文件，同时包含project和domain字段
          2. 创建IdTokenCredentialsProvider

        预期结果:
          抛出IdTokenParamsException，错误信息包含"mutually exclusive"
        """
        config = _make_valid_config_dict()
        config['domain_id'] = self._get_domain_id()

        tmp_config_path = _create_temp_config_file(config)
        try:
            with pytest.raises(IdTokenParamsException, match="mutually exclusive"):
                IdTokenCredentialsProvider(config_file=tmp_config_path)
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_15: 错误oidc_token_file路径
    # ================================================================

    def test_tc_15_wrong_oidc_token_file_path(self):
        """
        tc_15: 错误oidc_token_file路径

        测试步骤:
          1. 指定不存在的oidc_token_file路径创建IdTokenCredentialsProvider

        预期结果:
          抛出IdTokenParamsException
        """
        with pytest.raises(IdTokenParamsException):
            IdTokenCredentialsProvider(
                oidc_token_file='/nonexistent/path/oidc-token-99999',
                idp_id='test-idp',
                project_name='cn-north-4',
            )

    # ================================================================
    # tc_16: 非JWT格式的id_token
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_401_invalid)
    def test_tc_16_non_jwt_id_token(self):
        """
        tc_16: 非JWT格式的id_token

        测试步骤:
          1. 创建临时配置文件，填入非JWT格式的id_token
          2. 创建IdTokenCredentialsProvider
          3. 调用get_credentials()

        预期结果:
          IAM返回401错误，抛出IdTokenAuthException
        """
        config = _make_valid_config_dict()
        config['id_token'] = 'this-is-not-a-jwt-token'

        tmp_config_path = _create_temp_config_file(config)
        try:
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            with pytest.raises(IdTokenAuthException):
                provider.get_credentials()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_17: credential_expires_seconds边界值(900/86400)
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_17_credential_expires_seconds_boundary(self):
        """
        tc_17: credential_expires_seconds边界值(900/86400)

        测试步骤:
          1. 使用credential_expires_seconds=900(最小值)创建provider
          2. 获取凭证并验证成功
          3. 使用credential_expires_seconds=86400(最大值)创建provider
          4. 获取凭证并验证成功

        预期结果:
          两个边界值均能正常获取凭证
        """
        config_file = self._get_valid_config_file()
        try:
            # 最小值 900
            provider_min = IdTokenCredentialsProvider(
                config_file=config_file,
                credential_expires_seconds=900,
            )
            cred_min = provider_min.get_credentials()
            assert cred_min is not None, "credential_expires_seconds=900时应能获取凭证"
            assert cred_min.get('accessKey'), "凭证应包含accessKey"

            # 最大值 86400
            provider_max = IdTokenCredentialsProvider(
                config_file=config_file,
                credential_expires_seconds=86400,
            )
            cred_max = provider_max.get_credentials()
            assert cred_max is not None, "credential_expires_seconds=86400时应能获取凭证"
            assert cred_max.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(config_file)

    # ================================================================
    # tc_18: 配置文件直接包含id_token字段
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_18_config_file_with_id_token_field(self):
        """
        tc_18: 配置文件直接包含id_token字段

        测试步骤:
          1. 创建临时配置文件，直接包含id_token字段（而非oidc_token_file）
          2. 创建IdTokenCredentialsProvider
          3. 获取凭证验证成功

        预期结果:
          配置文件中包含id_token时能正常工作
        """
        config = _make_valid_config_dict()
        # 确保配置文件中有id_token且无oidc_token_file
        config['id_token'] = MOCK_VALID_ID_TOKEN
        config.pop('oidc_token_file', None)

        tmp_config_path = _create_temp_config_file(config)
        try:
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            cred = provider.get_credentials()
            assert cred is not None, "凭证不应为None"
            assert cred.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_19: 构造函数参数覆盖配置文件
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_19_constructor_overrides_config_file(self):
        """
        tc_19: 构造函数参数覆盖配置文件

        测试步骤:
          1. 创建临时配置文件，将idp_id设置为错误值
          2. 创建IdTokenCredentialsProvider，构造函数传入正确的idp_id覆盖配置文件
          3. 获取凭证验证成功

        预期结果:
          构造函数传入的idp_id覆盖配置文件中的错误值，凭证获取成功
        """
        config = _make_valid_config_dict()
        config['idp_id'] = 'wrong-idp-in-config-99999'

        tmp_config_path = _create_temp_config_file(config)
        try:
            # 构造函数传入正确的idp_id，覆盖配置文件中的错误值
            correct_idp_id = MOCK_IDP_ID
            provider = IdTokenCredentialsProvider(
                config_file=tmp_config_path,
                idp_id=correct_idp_id,
            )

            # 验证构造函数的idp_id覆盖了配置文件中的错误值
            assert provider.idp_id == correct_idp_id, \
                "构造函数idp_id应覆盖配置文件中的idp_id"

            # 验证能正常获取凭证
            cred = provider.get_credentials()
            assert cred is not None, "覆盖后应能正常获取凭证"
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_20: 多次操作复用缓存凭证
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_with_expires)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_20_multiple_ops_reuse_cached_credential(self):
        """
        tc_20: 多次操作复用缓存凭证

        测试步骤:
          1. 使用有效配置创建provider
          2. 获取初始凭证，记录accessKey
          3. 连续8次调用get_credentials()
          4. 每次验证accessKey未变化

        预期结果:
          8次调用期间凭证未被重新获取，accessKey保持不变
        """
        config_file = self._get_valid_config_file()
        try:
            provider = IdTokenCredentialsProvider(config_file=config_file)

            # 获取初始凭证
            initial_cred = provider.get_credentials()
            assert initial_cred is not None, "初始凭证不应为None"
            initial_ak = initial_cred.get('accessKey')

            # 连续8次获取凭证，验证缓存命中
            for i in range(8):
                current_cred = provider.get_credentials()
                assert current_cred.get('accessKey') == initial_ak, \
                    "第{}次获取凭证应复用缓存, accessKey不应变化".format(i + 1)
        finally:
            os.unlink(config_file)

    # ================================================================
    # tc_21: 缺少scope参数时获取unscoped token（合法场景）
    # ================================================================

    def test_tc_21_missing_scope_allows_unscoped_token(self):
        """
        tc_21: 缺少scope参数时获取unscoped token（合法场景）

        测试步骤:
          1. 创建临时配置文件，移除所有project和domain相关字段
          2. 创建IdTokenCredentialsProvider

        预期结果:
          IdTokenCredentialsProvider创建成功，不抛IdTokenParamsException
        """
        config = _make_valid_config_dict()
        config.pop('project_id', None)
        config.pop('project_name', None)
        config.pop('domain_id', None)
        config.pop('domain_name', None)

        tmp_config_path = _create_temp_config_file(config)
        try:
            # 不抛IdTokenParamsException，证明unscoped token是合法场景
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            # 验证provider创建成功，project和domain均为None
            assert provider.project_id is None, "project_id应为None"
            assert provider.project_name is None, "project_name应为None"
            assert provider.domain_id is None, "domain_id应为None"
            assert provider.domain_name is None, "domain_name应为None"
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_22: project_name 模式联邦认证
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_22_project_name_scope(self):
        """
        tc_22: project_name 模式联邦认证

        测试步骤:
          1. 创建配置，移除project_id，仅保留project_name
          2. 创建IdTokenCredentialsProvider
          3. 获取凭证验证成功

        预期结果:
          凭证获取成功
        """
        config = _make_valid_config_dict()
        config.pop('project_id', None)
        config.pop('domain_id', None)
        config.pop('domain_name', None)
        config['project_name'] = MOCK_PROJECT_NAME

        tmp_config_path = _create_temp_config_file(config)
        try:
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            cred = provider.get_credentials()
            assert cred is not None, "凭证不应为None"
            assert cred.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_23: project_id + project_name 同时指定
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_23_project_id_and_name(self):
        """
        tc_23: project_id + project_name 同时指定

        测试步骤:
          1. 创建配置，确保同时有project_id和project_name
          2. 移除domain相关字段避免互斥
          3. 创建IdTokenCredentialsProvider
          4. 获取凭证验证成功

        预期结果:
          凭证获取成功
        """
        config = _make_valid_config_dict()
        config['project_id'] = MOCK_PROJECT_ID
        config['project_name'] = MOCK_PROJECT_NAME
        config.pop('domain_id', None)
        config.pop('domain_name', None)

        tmp_config_path = _create_temp_config_file(config)
        try:
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            cred = provider.get_credentials()
            assert cred is not None, "凭证不应为None"
            assert cred.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_24: unscoped token 模式联邦认证
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_24_unscoped_token(self):
        """
        tc_24: unscoped token 模式联邦认证

        与tc_21的区别：tc_21仅验证provider创建不抛异常，
        本测试验证完整流程：获取凭证。

        测试步骤:
          1. 创建配置，移除所有project和domain字段
          2. 创建IdTokenCredentialsProvider
          3. 获取凭证验证成功

        预期结果:
          凭证获取成功，包含accessKey
        """
        config = _make_valid_config_dict()
        config.pop('project_id', None)
        config.pop('project_name', None)
        config.pop('domain_id', None)
        config.pop('domain_name', None)

        tmp_config_path = _create_temp_config_file(config)
        try:
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            # 验证凭证获取成功
            cred = provider.get_credentials()
            assert cred is not None, "unscoped token应能获取凭证"
            assert cred.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_25: oidc_token_file 方式加载ID Token
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_25_oidc_token_file_method(self):
        """
        tc_25: oidc_token_file 方式加载ID Token

        测试步骤:
          1. 创建临时token文件
          2. 创建配置文件，使用新文件路径作为oidc_token_file
          3. 创建IdTokenCredentialsProvider
          4. 获取凭证验证成功

        预期结果:
          凭证获取成功
        """
        # 创建临时token文件
        tmp_token_path = _create_temp_token_file(MOCK_VALID_ID_TOKEN)

        try:
            config = _make_valid_config_dict()
            config['oidc_token_file'] = tmp_token_path
            config.pop('id_token', None)

            tmp_config_path = _create_temp_config_file(config)
            try:
                provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

                cred = provider.get_credentials()
                assert cred is not None, "凭证不应为None"
                assert cred.get('accessKey'), "凭证应包含accessKey"
            finally:
                os.unlink(tmp_config_path)
        finally:
            os.unlink(tmp_token_path)

    # ================================================================
    # tc_26: id_token 和 oidc_token_file 互斥验证
    # ================================================================

    def test_tc_26_id_token_oidc_token_file_mutual_exclusion(self):
        """
        tc_26: id_token 和 oidc_token_file 互斥验证

        测试步骤:
          1. 创建IdTokenCredentialsProvider，同时指定id_token和oidc_token_file

        预期结果:
          抛出IdTokenParamsException，错误信息包含"mutually exclusive"
        """
        with pytest.raises(IdTokenParamsException, match="mutually exclusive"):
            IdTokenCredentialsProvider(
                id_token=MOCK_VALID_ID_TOKEN,
                oidc_token_file='/tmp/fake_oidc_token.txt',
                idp_id='test-idp',
                project_name='cn-north-4',
            )

    # ================================================================
    # tc_27: 构造函数指定IAM端点
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_27_constructor_iam_endpoint(self):
        """
        tc_27: 构造函数指定IAM端点

        测试步骤:
          1. 创建临时配置文件，不含iam_endpoint
          2. 构造函数传入正确的iam_endpoint
          3. 获取凭证验证成功

        预期结果:
          构造函数的iam_endpoint参数生效，凭证获取成功
        """
        config = _make_valid_config_dict()
        config.pop('iam_endpoint', None)

        tmp_config_path = _create_temp_config_file(config)
        try:
            # 构造函数传入正确的iam_endpoint
            correct_endpoint = MOCK_IAM_ENDPOINT
            provider = IdTokenCredentialsProvider(
                config_file=tmp_config_path,
                iam_endpoint=correct_endpoint,
            )

            # 验证构造函数的iam_endpoint生效
            assert provider.iam_endpoint == correct_endpoint, \
                "构造函数iam_endpoint应覆盖配置文件"

            # 验证能正常获取凭证
            cred = provider.get_credentials()
            assert cred is not None, "使用构造函数iam_endpoint应能获取凭证"
            assert cred.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_28: 配置文件iam_endpoint优先级
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_28_config_file_iam_endpoint_priority(self):
        """
        tc_28: 配置文件iam_endpoint优先级

        Python SDK优先级：构造函数显式参数 > config_file参数。
        本测试场景：构造函数不传iam_endpoint，config_file中有iam_endpoint，
        验证config_file中的iam_endpoint生效。

        测试步骤:
          1. 使用包含iam_endpoint的有效配置文件
          2. 创建IdTokenCredentialsProvider，构造函数不传iam_endpoint
          3. 获取凭证验证成功

        预期结果:
          配置文件中的iam_endpoint生效，凭证获取成功
        """
        config = _make_valid_config_dict()
        config['iam_endpoint'] = MOCK_IAM_ENDPOINT

        tmp_config_path = _create_temp_config_file(config)
        try:
            provider = IdTokenCredentialsProvider(config_file=tmp_config_path)

            # 验证配置文件中的iam_endpoint被加载
            assert provider.iam_endpoint == MOCK_IAM_ENDPOINT, \
                "配置文件中的iam_endpoint应被加载"

            # 验证能正常获取凭证
            cred = provider.get_credentials()
            assert cred is not None, "使用配置文件iam_endpoint应能获取凭证"
            assert cred.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_29: credential_expires_seconds 低于最小值被normalize
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_success)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_29_credential_expires_seconds_below_minimum(self):
        """
        tc_29: credential_expires_seconds 低于最小值被normalize

        _validate_params()中：如果credential_expires_seconds < 900，自动修正为86400。

        测试步骤:
          1. 创建IdTokenCredentialsProvider，设置credential_expires_seconds=100
          2. 验证被自动修正为86400
          3. 获取凭证验证成功

        预期结果:
          credential_expires_seconds被修正为86400，凭证获取成功
        """
        config_file = self._get_valid_config_file()
        try:
            provider = IdTokenCredentialsProvider(
                config_file=config_file,
                credential_expires_seconds=100,
            )

            # 验证被修正为86400
            assert provider.credential_expires_seconds == 86400, \
                "credential_expires_seconds=100应被修正为86400, 实际: {}".format(
                    provider.credential_expires_seconds)

            # 验证能正常获取凭证
            cred = provider.get_credentials()
            assert cred is not None, "normalize后应能正常获取凭证"
            assert cred.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(config_file)

    # ================================================================
    # tc_30: 多线程并发获取凭证
    # ================================================================

    @patch.object(IdTokenCredentialsProvider, '_do_temporary_aksk_request',
                  _mock_temporary_aksk_with_expires)
    @patch.object(IdTokenCredentialsProvider, '_do_federation_token_request',
                  _mock_federation_token_success)
    def test_tc_30_concurrent_get_credentials(self):
        """
        tc_30: 多线程并发获取凭证

        测试步骤:
          1. 创建IdTokenCredentialsProvider
          2. 先获取初始凭证（预热缓存）
          3. 启动5个线程同时调用get_credentials()
          4. 验证所有线程成功且看到相同的accessKey

        预期结果:
          所有线程成功获取凭证，且accessKey一致
        """
        config_file = self._get_valid_config_file()
        try:
            provider = IdTokenCredentialsProvider(config_file=config_file)

            # 先获取初始凭证（预热缓存）
            initial_cred = provider.get_credentials()
            assert initial_cred is not None, "初始凭证不应为None"
            initial_ak = initial_cred.get('accessKey')

            # 启动5个线程并发get_credentials
            results = []
            errors = []
            barrier = threading.Barrier(5)

            def worker():
                try:
                    barrier.wait(timeout=10)
                    cred = provider.get_credentials()
                    results.append(cred.get('accessKey'))
                except Exception as e:
                    errors.append(str(e))

            threads = [threading.Thread(target=worker) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)

            # 验证所有线程成功
            assert len(errors) == 0, \
                "不应有线程失败, 错误: {}".format(errors)
            assert len(results) == 5, \
                "应有5个结果, 实际: {}".format(len(results))

            # 验证所有线程看到相同的accessKey
            assert all(ak == results[0] for ak in results), \
                "所有线程应看到相同的accessKey, 实际: {}".format(results)

            # 验证与初始凭证一致
            assert results[0] == initial_ak, \
                "并发获取的凭证应与初始凭证一致"
        finally:
            os.unlink(config_file)
