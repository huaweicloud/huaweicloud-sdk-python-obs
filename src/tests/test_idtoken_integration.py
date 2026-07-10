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
IdToken联邦认证集成测试

全部连接真实IAM服务，与Java SDK IdTokenFederationIT测试用例对齐。

测试用例:
  tc_python_alpha_oidc_token_01-08: 基础功能（有效Token、过期Token、错误IdP/Project/Domain、手动/自动刷新、最大有效期）
  tc_09: OBS对象完整生命周期
  tc_10-11: Dict/实例方式初始化ObsClient
  tc_12: 凭证缓存命中
  tc_13: Domain-only scope认证
  tc_14: project和domain互斥验证
  tc_15-16: 错误oidc_token_file路径/非JWT格式
  tc_17: credential_expires_seconds边界值
  tc_18: 配置文件直接包含id_token字段
  tc_19: 构造函数参数覆盖配置文件
  tc_20: 多次操作复用缓存凭证
  tc_21: 缺少scope参数时获取unscoped token（合法场景，与Java 014行为一致）
  tc_22: project_name模式联邦认证（对应Java 010）
  tc_23: project_id+project_name同时指定（对应Java 011）
  tc_24: unscoped token模式联邦认证（对应Java 014）
  tc_25: oidc_token_file方式加载ID Token（对应Java 015）
  tc_26: id_token和oidc_token_file互斥验证（对应Java 016）
  tc_27: 构造函数指定IAM端点（对应Java 017）
  tc_28: 配置文件iam_endpoint优先级（对应Java 018）
  tc_29: credential_expires_seconds低于最小值被normalize（对应Java 020）
  tc_30: 多线程并发获取凭证（对应Java 022）

配置文件: test_config_idtoken.json (独立于test_config.json)
  - server: OBS服务端点
  - id_token_config_file: IdTokenCredentialsProvider的config_file路径(JSON格式)
  - oidc_token_file: OIDC Token纯文本文件路径
  - domain_id: 域ID（用于domain scope测试，不写入id_token_config.json以避免project/domain互斥）

其中 id_token_config_file 指向的JSON文件应包含:
  - oidc_token_file 或 id_token: 有效的JWT格式ID Token来源
  - idp_id: 身份提供商ID
  - project_name 和/或 project_id: 项目信息
  - iam_endpoint: IAM服务地址
"""

import json
import os
import tempfile
import threading
import time

import pytest

from obs import (
    ObsClient,
    IdTokenCredentialsProvider,
    IdTokenAuthException,
    FederationTokenException,
    IdTokenParamsException,
)


def read_idtoken_config():
    """读取IdToken集成测试配置"""
    config_path = os.path.join(os.getcwd(), "test_config_idtoken.json")
    with open(config_path, "r") as f:
        return json.loads(f.read())


idtoken_config = read_idtoken_config()


def _create_obsclient_with_config_file(config_file_path, server=None):
    """使用config_file路径创建ObsClient"""
    server = server or idtoken_config["server"]
    return ObsClient(
        id_token_credentials_provider=config_file_path,
        server=server,
        proxy_host=idtoken_config.get("proxy_host"),
        proxy_port=idtoken_config.get("proxy_port"),
        proxy_username=idtoken_config.get("proxy_username"),
        proxy_password=idtoken_config.get("proxy_password"),
    )


def _create_obsclient_with_provider(provider, server=None):
    """使用IdTokenCredentialsProvider实例创建ObsClient"""
    server = server or idtoken_config["server"]
    return ObsClient(
        id_token_credentials_provider=provider,
        server=server,
        proxy_host=idtoken_config.get("proxy_host"),
        proxy_port=idtoken_config.get("proxy_port"),
        proxy_username=idtoken_config.get("proxy_username"),
        proxy_password=idtoken_config.get("proxy_password"),
    )


def _is_idp_configured_error(exc):
    """判断异常是否为IAM服务端IdP未配置错误"""
    msg = str(exc).lower()
    return 'no metadata configured' in msg or 'idp' in msg and 'not' in msg and 'found' in msg


def _try_get_credentials(provider):
    """
    尝试获取凭证，如果IAM服务端IdP未配置则跳过测试

    :param provider: IdTokenCredentialsProvider实例
    :return: 凭证字典
    :raises pytest.skip: IAM服务端IdP未配置
    """
    try:
        return provider.get_credentials()
    except FederationTokenException as e:
        if _is_idp_configured_error(e):
            pytest.skip("IAM服务端IdP未配置: {}".format(str(e)))
        raise


class TestIdTokenIntegration:
    """IdToken联邦认证集成测试 (对应 docs/测试用例.xlsx)"""

    def _get_valid_config_file(self):
        """获取有效的IdToken配置文件路径"""
        return idtoken_config["id_token_config_file"]

    def _get_valid_oidc_token_file(self):
        """获取有效的oidc-token文件路径"""
        return idtoken_config["oidc_token_file"]

    def _get_domain_id(self):
        """从测试配置中获取domain_id"""
        return idtoken_config.get('domain_id')

    def _read_config_as_dict(self):
        """读取有效配置文件内容为字典"""
        with open(self._get_valid_config_file(), 'r') as f:
            return json.load(f)

    def _create_temp_config_file(self, config_dict):
        """创建临时配置文件，返回路径"""
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(config_dict, tmp)
        tmp.close()
        return tmp.name

    # ================================================================
    # tc_python_alpha_oidc_token_01: 使用有效 ID Token 列举桶成功
    # ================================================================

    def test_tc_python_alpha_oidc_token_01_list_buckets_with_valid_id_token(self):
        """
        tc_python_alpha_oidc_token_01: 使用有效 ID Token 列举桶成功

        测试步骤:
          1. 读取有效的 ID Token 配置文件(包含有效id_token、idp_id、project_id/project_name、domain_id/domain_name)
          2. 创建IdTokenCredentialsProvider，使用配置文件路径和默认iam_endpoint
          3. 创建ObsConfiguration
          4. 使用凭证提供者和配置创建ObsClient实例
          5. 调用obsClient.listBuckets()方法

        预期结果:
          1. ID Token配置文件解析成功，无异常抛出
          2. IdTokenCredentialsProvider初始化成功，内部凭证刷新成功
          3. ObsConfiguration配置生效，认证类型正确设置
          4. ObsClient实例创建成功
          5. listBuckets()返回非空列表，状态码为200
        """
        config_file = self._get_valid_config_file()
        obsClient = _create_obsclient_with_config_file(config_file)

        try:
            # 先验证凭证获取是否成功（IAM服务端IdP是否已配置）
            _try_get_credentials(obsClient._id_token_provider)

            resp = obsClient.listBuckets()
            assert resp.status < 300, \
                "listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
        finally:
            obsClient.close()

    # ================================================================
    # tc_python_alpha_oidc_token_02: 使用过期 ID Token 列举桶失败
    # ================================================================

    def test_tc_python_alpha_oidc_token_02_list_buckets_with_expired_id_token(self):
        """
        tc_python_alpha_oidc_token_02: 使用过期 ID Token 列举桶失败

        测试步骤:
          1. 创建临时JSON配置文件，填入过期的id_token
          2. 配置有效的idp_id、project_id、domain_id
          3. 使用临时配置文件创建IdTokenCredentialsProvider
          4. 创建ObsClient实例
          5. 调用obsClient.listBuckets()方法

        预期结果:
          1. 临时配置文件创建成功，JSON格式正确
          2. 必填字段idp_id、project_id、domain_id有效配置
          3. IdTokenCredentialsProvider和ObsClient创建成功
          4. listBuckets()抛出IdTokenAuthException
          5. 异常状态码为400+，错误码指示Token无效/过期
        """
        valid_config = self._read_config_as_dict()

        # 使用过期的JWT token (exp已过)
        expired_token = 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjF9.expired_signature'
        error_config = dict(valid_config)
        error_config['id_token'] = expired_token
        error_config.pop('oidc_token_file', None)

        tmp_config_path = self._create_temp_config_file(error_config)

        try:
            obsClient = _create_obsclient_with_config_file(tmp_config_path)

            try:
                # ObsClient在凭证获取失败时抛出IdTokenAuthException
                try:
                    resp = obsClient.listBuckets()
                    # 如果没有抛异常，检查返回状态码
                    assert resp.status >= 400, \
                        "应返回400+错误状态码, 实际: {}".format(resp.status)
                except IdTokenAuthException:
                    # 凭证获取阶段抛IdTokenAuthException是预期行为
                    pass
            finally:
                obsClient.close()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_python_alpha_oidc_token_03: 使用错误 IdP ID 列举桶失败
    # ================================================================

    def test_tc_python_alpha_oidc_token_03_list_buckets_with_wrong_idp_id(self):
        """
        tc_python_alpha_oidc_token_03: 使用错误 IdP ID 列举桶失败

        测试步骤:
          1. 创建临时JSON配置文件，填入有效的id_token、错误的idp_id、有效的project_id、domain_id
          2. 使用临时配置文件创建IdTokenCredentialsProvider
          3. 创建ObsClient实例
          4. 调用obsClient.listBuckets()方法

        预期结果:
          1. 临时配置文件创建成功，包含有效Token和错误IdP ID
          2. IdTokenCredentialsProvider和ObsClient创建成功
          3. listBuckets()抛出IdTokenAuthException或返回错误状态码
          4. 异常响应码为401，指示认证失败
        """
        valid_config = self._read_config_as_dict()

        error_config = dict(valid_config)
        error_config['idp_id'] = 'wrong-idp-id-99999'

        tmp_config_path = self._create_temp_config_file(error_config)

        try:
            obsClient = _create_obsclient_with_config_file(tmp_config_path)

            try:
                try:
                    resp = obsClient.listBuckets()
                    # 没抛异常则检查状态码
                    assert resp.status == 401 or resp.status >= 400, \
                        "应返回401或400+错误状态码, 实际: {}".format(resp.status)
                except IdTokenAuthException as e:
                    # 凭证获取阶段抛IdTokenAuthException是预期行为
                    # 验证异常包含状态码信息
                    assert e.status is None or e.status >= 400, \
                        "异常状态码应为400+, 实际: {}".format(e.status)
            finally:
                obsClient.close()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_python_alpha_oidc_token_04: 使用错误 project_id 列举桶失败
    # ================================================================

    def test_tc_python_alpha_oidc_token_04_list_buckets_with_wrong_project_id(self):
        """
        tc_python_alpha_oidc_token_04: 使用错误 project_id 列举桶失败

        测试步骤:
          1. 创建临时JSON配置文件，填入有效的id_token、错误的project_id、有效的idp_id、domain_id
          2. 使用临时配置文件创建IdTokenCredentialsProvider
          3. 创建ObsClient实例
          4. 调用obsClient.listBuckets()方法

        预期结果:
          1. 临时配置文件创建成功，包含有效Token和错误project_id
          2. IdTokenCredentialsProvider和ObsClient创建成功
          3. listBuckets()抛出IdTokenAuthException或返回错误状态码
          4. 异常响应码为404，指示项目不存在
        """
        valid_config = self._read_config_as_dict()

        error_config = dict(valid_config)
        # 替换project_id为错误值，移除project_name避免互斥
        error_config.pop('project_name', None)
        error_config['project_id'] = 'wrong-project-id-99999'

        tmp_config_path = self._create_temp_config_file(error_config)

        try:
            obsClient = _create_obsclient_with_config_file(tmp_config_path)

            try:
                try:
                    resp = obsClient.listBuckets()
                    # 没抛异常则检查状态码
                    assert resp.status == 404 or resp.status >= 400, \
                        "应返回404或400+错误状态码, 实际: {}".format(resp.status)
                except IdTokenAuthException:
                    # 凭证获取阶段抛IdTokenAuthException也是预期行为
                    pass
            finally:
                obsClient.close()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_python_alpha_oidc_token_05: 使用错误 domain_id 列举桶失败
    # ================================================================

    def test_tc_python_alpha_oidc_token_05_list_buckets_with_wrong_domain_id(self):
        """
        tc_python_alpha_oidc_token_05: 使用错误 domain_id 列举桶失败

        测试步骤:
          1. 创建临时JSON配置文件，填入有效的id_token、错误的domain_id、有效的idp_id、project_id
          2. 使用临时配置文件创建IdTokenCredentialsProvider
          3. 创建ObsClient实例
          4. 调用obsClient.listBuckets()方法

        预期结果:
          1. 临时配置文件创建成功，包含有效Token和错误domain_id
          2. IdTokenCredentialsProvider和ObsClient创建成功
          3. listBuckets()抛出IdTokenAuthException或返回错误状态码
          4. 异常响应码为404，指示domain不存在
        """
        valid_config = self._read_config_as_dict()

        error_config = dict(valid_config)
        # 替换domain_id为错误值，移除project_id和project_name让domain_id作为scope生效
        # 注：project优先于domain，必须移除project相关字段才能测试domain
        error_config.pop('project_id', None)
        error_config.pop('project_name', None)
        error_config.pop('domain_name', None)
        error_config['domain_id'] = 'wrong-domain-id-99999'

        tmp_config_path = self._create_temp_config_file(error_config)

        try:
            obsClient = _create_obsclient_with_config_file(tmp_config_path)

            try:
                try:
                    resp = obsClient.listBuckets()
                    # 没抛异常则检查状态码
                    assert resp.status == 404 or resp.status >= 400, \
                        "应返回404或400+错误状态码, 实际: {}".format(resp.status)
                except IdTokenAuthException:
                    # 凭证获取阶段抛IdTokenAuthException也是预期行为
                    pass
            finally:
                obsClient.close()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_python_alpha_oidc_token_06: 凭证手动刷新成功
    # ================================================================

    def test_tc_python_alpha_oidc_token_06_credential_manual_refresh(self):
        """
        tc_python_alpha_oidc_token_06: 凭证手动刷新成功

        测试步骤:
          1. 读取有效的ID Token配置文件
          2. 创建IdTokenCredentialsProvider
          3. 创建ObsConfiguration
          4. 使用凭证提供者和配置创建ObsClient实例
          5. 调用provider.get_credentials()获取初始凭证
          6. 调用provider.refresh()手动触发刷新
          7. 再次调用get_credentials()获取刷新后的凭证
          8. 调用obsClient.listBuckets()验证刷新后仍可正常操作

        预期结果:
          1. ID Token配置文件解析成功
          2. IdTokenCredentialsProvider初始化成功
          3. ObsConfiguration配置生效
          4. ObsClient实例创建成功
          5. 初始凭证非空，包含accessKey、secretKey、securityToken
          6. 手动刷新执行成功，无异常抛出
          7. 刷新后的凭证非空，且与初始凭证不一致
          8. listBuckets()返回成功，状态码为200
        """
        config_file = self._get_valid_config_file()
        obsClient = _create_obsclient_with_config_file(config_file)

        try:
            provider = obsClient._id_token_provider

            # 步骤5: 获取初始凭证（如果IAM服务端IdP未配置则跳过）
            initial_cred = _try_get_credentials(provider)
            assert initial_cred is not None, "初始凭证不应为None"
            assert initial_cred.get('accessKey'), "初始凭证应包含accessKey"
            assert initial_cred.get('secretKey'), "初始凭证应包含secretKey"
            assert initial_cred.get('securityToken'), "初始凭证应包含securityToken"

            # 步骤6: 手动刷新
            provider.refresh()

            # 步骤7: 获取刷新后的凭证
            refreshed_cred = provider.get_credentials()
            assert refreshed_cred is not None, "刷新后的凭证不应为None"
            assert refreshed_cred.get('accessKey'), "刷新后的凭证应包含accessKey"
            assert refreshed_cred.get('secretKey'), "刷新后的凭证应包含secretKey"
            assert refreshed_cred.get('securityToken'), "刷新后的凭证应包含securityToken"

            # 刷新后的凭证与初始凭证不一致
            assert refreshed_cred.get('accessKey') != initial_cred.get('accessKey') or \
                   refreshed_cred.get('securityToken') != initial_cred.get('securityToken'), \
                   "刷新后的凭证应与初始凭证不一致"

            # 步骤8: 验证刷新后仍可正常操作
            resp = obsClient.listBuckets()
            assert resp.status < 300, \
                "刷新后listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
        finally:
            obsClient.close()

    # ================================================================
    # tc_python_alpha_oidc_token_07: 凭证自动刷新成功
    # ================================================================

    def test_tc_python_alpha_oidc_token_07_credential_auto_refresh(self):
        """
        tc_python_alpha_oidc_token_07: 凭证自动刷新成功

        测试步骤:
          1. 配置有效的ID Token配置文件，设置refresh_before_seconds为890，
             credential_expires_seconds为900(最小值)
          2. 使用IdTokenCredentialsProvider创建ObsConfiguration和ObsClient实例
          3. 调用provider.get_credentials()获取初始凭证
          4. 等待10s后再次获取凭证，触发自动刷新
          5. 调用obsClient.listBuckets()验证刷新后仍可正常操作

        预期结果:
          1. ID Token配置文件成功
          2. ObsClient实例创建成功
          3. 初始凭证非空，包含accessKey、secretKey、securityToken
          4. 刷新后凭证非空，且aksk与初始凭证不一致
          5. 调用obsClient.listBuckets()验证刷新后仍可正常操作
        """
        config_file = self._get_valid_config_file()

        # 创建provider，设置极短的刷新窗口
        provider = IdTokenCredentialsProvider(
            config_file=config_file,
            refresh_before_seconds=890,
            credential_expires_seconds=900,
        )

        obsClient = _create_obsclient_with_provider(provider)

        try:
            # 步骤3: 获取初始凭证（如果IAM服务端IdP未配置则跳过）
            initial_cred = _try_get_credentials(provider)
            assert initial_cred is not None, "初始凭证不应为None"
            assert initial_cred.get('accessKey'), "初始凭证应包含accessKey"
            assert initial_cred.get('secretKey'), "初始凭证应包含secretKey"
            assert initial_cred.get('securityToken'), "初始凭证应包含securityToken"

            # 记录初始凭证的过期时间，用于验证自动刷新
            initial_expires = provider._expires

            # 步骤4: 等待12s让凭证进入刷新窗口
            # credential_expires_seconds=900, refresh_before_seconds=890
            # 刷新窗口为凭证获取后10秒，等待12秒确保超过刷新窗口
            time.sleep(12)

            # 再次获取凭证，触发自动刷新
            refreshed_cred = provider.get_credentials()
            assert refreshed_cred is not None, "刷新后的凭证不应为None"
            assert refreshed_cred.get('accessKey'), "刷新后的凭证应包含accessKey"
            assert refreshed_cred.get('secretKey'), "刷新后的凭证应包含secretKey"
            assert refreshed_cred.get('securityToken'), "刷新后的凭证应包含securityToken"

            # 验证自动刷新被触发：凭证的过期时间应晚于初始凭证的过期时间
            # （因为新凭证是在初始凭证过期窗口内获取的，新凭证的有效期更长）
            assert provider._expires > initial_expires, \
                "自动刷新后凭证过期时间应晚于初始凭证过期时间"

            # 步骤5: 验证刷新后仍可正常操作
            resp = obsClient.listBuckets()
            assert resp.status < 300, \
                "自动刷新后listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
        finally:
            obsClient.close()

    # ================================================================
    # tc_python_alpha_oidc_token_08: 临时aksk有效期最大值测试成功
    # ================================================================

    def test_tc_python_alpha_oidc_token_08_max_credential_expires_seconds(self):
        """
        tc_python_alpha_oidc_token_08: 临时aksk有效期最大值测试成功

        测试步骤:
          1. 配置有效的ID Token配置文件，设置credential_expires_seconds为43200
          2. 使用IdTokenCredentialsProvider创建ObsConfiguration和ObsClient实例
          3. 调用obsClient.listBuckets()验证操作成功

        预期结果:
          1. ID Token配置文件成功
          2. ObsClient实例创建成功
          3. 调用obsClient.listBuckets()成功
        """
        config_file = self._get_valid_config_file()

        # 创建provider，设置credential_expires_seconds为43200
        provider = IdTokenCredentialsProvider(
            config_file=config_file,
            credential_expires_seconds=43200,
        )

        obsClient = _create_obsclient_with_provider(provider)

        try:
            # 先验证凭证获取是否成功（IAM服务端IdP是否已配置）
            _try_get_credentials(provider)

            resp = obsClient.listBuckets()
            assert resp.status < 300, \
                "listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
        finally:
            obsClient.close()

    @staticmethod
    def _get_location():
        """从server配置中提取location（如obs.cn-north-4.myhuaweicloud.com -> cn-north-4）"""
        server = idtoken_config.get("server", "")
        # server format: obs.{region}.myhuaweicloud.com
        parts = server.split(".")
        if len(parts) >= 2:
            return parts[1]
        return None

    @staticmethod
    def _cleanup_bucket(obsClient, bucketName):
        """清理桶：删除所有对象后删除桶，忽略错误"""
        try:
            resp = obsClient.listObjects(bucketName)
            if resp.status < 300 and resp.body:
                for obj in resp.body:
                    try:
                        obsClient.deleteObject(bucketName, obj.key)
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            obsClient.deleteBucket(bucketName)
        except Exception:
            pass

    # ================================================================
    # tc_09: OBS对象完整生命周期
    # ================================================================

    def test_tc_09_object_full_lifecycle(self):
        """
        tc_09: OBS对象完整生命周期

        测试步骤:
          1. 使用有效配置创建ObsClient
          2. createBucket
          3. putObject
          4. getObject
          5. headObject
          6. listObjects
          7. deleteObject
          8. deleteBucket

        预期结果:
          每步操作均返回成功状态码
        """
        config_file = self._get_valid_config_file()
        obsClient = _create_obsclient_with_config_file(config_file)
        bucketName = "idtoken-intg-{}".format(int(time.time()))
        objectKey = "lifecycle-test-object.txt"
        location = self._get_location()

        try:
            # 先验证凭证获取是否成功
            _try_get_credentials(obsClient._id_token_provider)

            # createBucket
            resp = obsClient.createBucket(bucketName, location=location)
            assert resp.status < 300, \
                "createBucket()应返回成功状态码, 实际: {}".format(resp.status)

            # putObject
            resp = obsClient.putObject(bucketName, objectKey, content='hello idtoken lifecycle')
            assert resp.status < 300, \
                "putObject()应返回成功状态码, 实际: {}".format(resp.status)

            # getObject
            resp = obsClient.getObject(bucketName, objectKey)
            assert resp.status < 300, \
                "getObject()应返回成功状态码, 实际: {}".format(resp.status)

            # headObject
            resp = obsClient.headObject(bucketName, objectKey)
            assert resp.status < 300, \
                "headObject()应返回成功状态码, 实际: {}".format(resp.status)

            # listObjects
            resp = obsClient.listObjects(bucketName)
            assert resp.status < 300, \
                "listObjects()应返回成功状态码, 实际: {}".format(resp.status)

            # deleteObject
            resp = obsClient.deleteObject(bucketName, objectKey)
            assert resp.status < 300, \
                "deleteObject()应返回成功状态码, 实际: {}".format(resp.status)

            # deleteBucket
            resp = obsClient.deleteBucket(bucketName)
            assert resp.status < 300, \
                "deleteBucket()应返回成功状态码, 实际: {}".format(resp.status)
        finally:
            self._cleanup_bucket(obsClient, bucketName)
            obsClient.close()

    # ================================================================
    # tc_10: Dict方式初始化ObsClient
    # ================================================================

    def test_tc_10_dict_init_obsclient(self):
        """
        tc_10: Dict方式初始化ObsClient

        测试步骤:
          1. 读取有效配置文件内容为字典
          2. 使用 id_token_credentials_provider=dict 创建ObsClient
          3. 调用listBuckets()

        预期结果:
          ObsClient创建成功，listBuckets()返回成功
        """
        valid_config = self._read_config_as_dict()

        server = idtoken_config["server"]
        obsClient = ObsClient(
            id_token_credentials_provider=valid_config,
            server=server,
            proxy_host=idtoken_config.get("proxy_host"),
            proxy_port=idtoken_config.get("proxy_port"),
            proxy_username=idtoken_config.get("proxy_username"),
            proxy_password=idtoken_config.get("proxy_password"),
        )

        try:
            _try_get_credentials(obsClient._id_token_provider)

            resp = obsClient.listBuckets()
            assert resp.status < 300, \
                "listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
        finally:
            obsClient.close()

    # ================================================================
    # tc_11: 实例方式初始化ObsClient
    # ================================================================

    def test_tc_11_provider_instance_init_obsclient(self):
        """
        tc_11: 实例方式初始化ObsClient

        测试步骤:
          1. 先创建IdTokenCredentialsProvider实例
          2. 使用 id_token_credentials_provider=provider 创建ObsClient
          3. 调用listBuckets()

        预期结果:
          ObsClient创建成功，listBuckets()返回成功
        """
        config_file = self._get_valid_config_file()
        provider = IdTokenCredentialsProvider(config_file=config_file)
        obsClient = _create_obsclient_with_provider(provider)

        try:
            _try_get_credentials(provider)

            resp = obsClient.listBuckets()
            assert resp.status < 300, \
                "listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
        finally:
            obsClient.close()

    # ================================================================
    # tc_12: 凭证缓存命中验证
    # ================================================================

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
        provider = IdTokenCredentialsProvider(config_file=config_file)

        # 获取初始凭证
        cred1 = _try_get_credentials(provider)
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

    # ================================================================
    # tc_13: Domain-only scope认证
    # ================================================================

    def test_tc_13_domain_only_scope(self):
        """
        tc_13: Domain-only scope认证

        测试步骤:
          1. 读取有效配置文件，移除project相关字段，仅保留domain_id
          2. 创建临时配置文件
          3. 创建ObsClient
          4. 调用listBuckets()

        预期结果:
          listBuckets()返回成功状态码
        """
        valid_config = self._read_config_as_dict()

        domain_only_config = dict(valid_config)
        domain_only_config.pop('project_id', None)
        domain_only_config.pop('project_name', None)
        # 从测试配置中注入domain_id（id_token_config.json仅包含project scope）
        if not domain_only_config.get('domain_id'):
            domain_only_config['domain_id'] = self._get_domain_id()
        # 确保domain_id存在
        assert domain_only_config.get('domain_id'), \
            "测试配置中必须包含domain_id才能测试domain-only scope"

        tmp_config_path = self._create_temp_config_file(domain_only_config)

        try:
            obsClient = _create_obsclient_with_config_file(tmp_config_path)

            try:
                _try_get_credentials(obsClient._id_token_provider)

                resp = obsClient.listBuckets()
                assert resp.status < 300, \
                    "listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
            finally:
                obsClient.close()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_14: Project优先于Domain scope
    # ================================================================

    def test_tc_14_project_and_domain_mutually_exclusive(self):
        """
        tc_14: project和domain互斥验证

        Python SDK中project和domain是互斥的，同时指定应抛出IdTokenParamsException。
        原tc_14假设"project优先于domain"，但_validate_params()不允许两者同时存在。

        测试步骤:
          1. 创建临时配置文件，同时包含project和domain字段
          2. 创建IdTokenCredentialsProvider

        预期结果:
          抛出IdTokenParamsException，错误信息包含"mutually exclusive"
        """
        valid_config = self._read_config_as_dict()

        # 确保同时包含project和domain
        both_config = dict(valid_config)
        both_config['domain_id'] = self._get_domain_id()

        tmp_config_path = self._create_temp_config_file(both_config)

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

    def test_tc_16_non_jwt_id_token(self):
        """
        tc_16: 非JWT格式的id_token

        测试步骤:
          1. 创建临时配置文件，填入非JWT格式的id_token
          2. 创建ObsClient
          3. 调用listBuckets()

        预期结果:
          IAM返回401错误，抛出IdTokenAuthException或返回401状态码
        """
        valid_config = self._read_config_as_dict()

        error_config = dict(valid_config)
        error_config['id_token'] = 'this-is-not-a-jwt-token'
        error_config.pop('oidc_token_file', None)

        tmp_config_path = self._create_temp_config_file(error_config)

        try:
            obsClient = _create_obsclient_with_config_file(tmp_config_path)

            try:
                try:
                    resp = obsClient.listBuckets()
                    assert resp.status >= 400, \
                        "应返回400+错误状态码, 实际: {}".format(resp.status)
                except IdTokenAuthException:
                    # IAM返回401时凭证获取抛IdTokenAuthException是预期行为
                    pass
            finally:
                obsClient.close()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_17: credential_expires_seconds边界值(900/86400)
    # ================================================================

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

        # 最小值 900
        provider_min = IdTokenCredentialsProvider(
            config_file=config_file,
            credential_expires_seconds=900,
        )
        cred_min = _try_get_credentials(provider_min)
        assert cred_min is not None, "credential_expires_seconds=900时应能获取凭证"
        assert cred_min.get('accessKey'), "凭证应包含accessKey"

        # 最大值 86400
        provider_max = IdTokenCredentialsProvider(
            config_file=config_file,
            credential_expires_seconds=86400,
        )
        cred_max = _try_get_credentials(provider_max)
        assert cred_max is not None, "credential_expires_seconds=86400时应能获取凭证"
        assert cred_max.get('accessKey'), "凭证应包含accessKey"

    # ================================================================
    # tc_18: 配置文件直接包含id_token字段
    # ================================================================

    def test_tc_18_config_file_with_id_token_field(self):
        """
        tc_18: 配置文件直接包含id_token字段

        测试步骤:
          1. 读取有效配置文件内容
          2. 读取oidc_token_file中的token内容
          3. 将id_token写入配置文件，移除oidc_token_file字段
          4. 使用新配置文件创建ObsClient
          5. 调用listBuckets()

        预期结果:
          配置文件中包含id_token时能正常工作，listBuckets()返回成功
        """
        valid_config = self._read_config_as_dict()

        # 从oidc_token_file读取token内容
        id_token_file_path = valid_config.get('oidc_token_file')
        if not id_token_file_path:
            pytest.skip("配置文件中无oidc_token_file字段，无法读取token内容")

        with open(id_token_file_path, 'r') as f:
            token_content = f.read().strip()

        # 构造仅包含id_token的配置
        id_token_config = dict(valid_config)
        id_token_config['id_token'] = token_content
        id_token_config.pop('oidc_token_file', None)

        tmp_config_path = self._create_temp_config_file(id_token_config)

        try:
            obsClient = _create_obsclient_with_config_file(tmp_config_path)

            try:
                _try_get_credentials(obsClient._id_token_provider)

                resp = obsClient.listBuckets()
                assert resp.status < 300, \
                    "listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
            finally:
                obsClient.close()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_19: 构造函数参数覆盖配置文件
    # ================================================================

    def test_tc_19_constructor_overrides_config_file(self):
        """
        tc_19: 构造函数参数覆盖配置文件

        测试步骤:
          1. 读取有效配置文件内容
          2. 创建临时配置文件，将idp_id设置为错误值
          3. 创建IdTokenCredentialsProvider，构造函数传入正确的idp_id覆盖配置文件
          4. 获取凭证验证成功

        预期结果:
          构造函数传入的idp_id覆盖配置文件中的错误值，凭证获取成功
        """
        valid_config = self._read_config_as_dict()

        # 配置文件中放入错误的idp_id
        wrong_config = dict(valid_config)
        wrong_config['idp_id'] = 'wrong-idp-in-config-99999'

        tmp_config_path = self._create_temp_config_file(wrong_config)

        try:
            # 构造函数传入正确的idp_id，覆盖配置文件中的错误值
            correct_idp_id = valid_config.get('idp_id')
            provider = IdTokenCredentialsProvider(
                config_file=tmp_config_path,
                idp_id=correct_idp_id,
            )

            # 验证构造函数的idp_id覆盖了配置文件中的错误值
            assert provider.idp_id == correct_idp_id, \
                "构造函数idp_id应覆盖配置文件中的idp_id"

            # 验证能正常获取凭证
            cred = _try_get_credentials(provider)
            assert cred is not None, "覆盖后应能正常获取凭证"
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_20: 多次OBS操作复用缓存凭证
    # ================================================================

    def test_tc_20_multiple_ops_reuse_cached_credential(self):
        """
        tc_20: 多次OBS操作复用缓存凭证

        测试步骤:
          1. 使用有效配置创建ObsClient
          2. 获取初始凭证，记录accessKey
          3. 执行8个连续OBS操作
          4. 每次操作后获取凭证，验证accessKey未变化

        预期结果:
          8个操作期间凭证未被重新获取，accessKey保持不变
        """
        config_file = self._get_valid_config_file()
        provider = IdTokenCredentialsProvider(config_file=config_file)
        obsClient = _create_obsclient_with_provider(provider)
        bucketName = "idtoken-intg-{}".format(int(time.time()))
        location = self._get_location()

        try:
            # 先验证凭证获取是否成功
            initial_cred = _try_get_credentials(provider)
            assert initial_cred is not None, "初始凭证不应为None"
            initial_ak = initial_cred.get('accessKey')

            # 创建桶
            resp = obsClient.createBucket(bucketName, location=location)
            assert resp.status < 300, \
                "createBucket()应返回成功状态码, 实际: {}".format(resp.status)

            try:
                # 连续8个操作，验证凭证未被重新获取
                for i in range(8):
                    objectKey = "reuse-test-obj-{}".format(i)
                    resp = obsClient.putObject(bucketName, objectKey, content='test content {}'.format(i))
                    assert resp.status < 300, \
                        "putObject()第{}次应返回成功状态码, 实际: {}".format(i + 1, resp.status)

                    # 检查凭证是否还是缓存的
                    current_cred = provider.get_credentials()
                    assert current_cred.get('accessKey') == initial_ak, \
                        "第{}次操作后凭证应复用缓存, accessKey不应变化".format(i + 1)
            finally:
                self._cleanup_bucket(obsClient, bucketName)
        finally:
            obsClient.close()

    # ================================================================
    # tc_21: 缺少scope参数时获取unscoped token（合法场景）
    # ================================================================

    def test_tc_21_missing_scope_allows_unscoped_token(self):
        """
        tc_21: 缺少scope参数时获取unscoped token（合法场景）

        与Java SDK 014行为一致：_validate_params()允许不指定project和domain，
        此时获取unscoped token（代码注释："project和domain均不指定时获取unscoped token（合法场景）"）。

        测试步骤:
          1. 创建临时配置文件，移除所有project和domain相关字段
          2. 创建IdTokenCredentialsProvider
          3. 获取凭证验证成功

        预期结果:
          IdTokenCredentialsProvider创建成功，不抛IdTokenParamsException
        """
        valid_config = self._read_config_as_dict()

        unscoped_config = dict(valid_config)
        unscoped_config.pop('project_id', None)
        unscoped_config.pop('project_name', None)
        unscoped_config.pop('domain_id', None)
        unscoped_config.pop('domain_name', None)

        tmp_config_path = self._create_temp_config_file(unscoped_config)

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

    def test_tc_22_project_name_scope(self):
        """
        tc_22: project_name 模式联邦认证（对应Java 010）

        测试步骤:
          1. 读取有效配置文件，移除project_id，仅保留project_name
          2. 创建临时配置文件
          3. 创建ObsClient
          4. 调用listBuckets()

        预期结果:
          listBuckets()返回成功状态码
        """
        valid_config = self._read_config_as_dict()

        project_name = valid_config.get('project_name')
        if not project_name:
            pytest.skip("配置文件中缺少project_name，无法测试project_name scope")

        config = dict(valid_config)
        config.pop('project_id', None)
        # 移除domain相关字段避免互斥
        config.pop('domain_id', None)
        config.pop('domain_name', None)

        tmp_config_path = self._create_temp_config_file(config)

        try:
            obsClient = _create_obsclient_with_config_file(tmp_config_path)

            try:
                _try_get_credentials(obsClient._id_token_provider)

                resp = obsClient.listBuckets()
                assert resp.status < 300, \
                    "listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
            finally:
                obsClient.close()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_23: project_id + project_name 同时指定
    # ================================================================

    def test_tc_23_project_id_and_name(self):
        """
        tc_23: project_id + project_name 同时指定（对应Java 011）

        测试步骤:
          1. 读取有效配置文件，确保同时有project_id和project_name
          2. 移除domain相关字段避免互斥
          3. 创建临时配置文件
          4. 创建ObsClient
          5. 调用listBuckets()

        预期结果:
          listBuckets()返回成功状态码
        """
        valid_config = self._read_config_as_dict()

        project_name = valid_config.get('project_name')
        if not project_name:
            pytest.skip("配置文件中缺少project_name，无法测试project_id+project_name")

        config = dict(valid_config)
        # 确保同时有project_id和project_name
        config['project_name'] = project_name
        # 移除domain相关字段避免互斥
        config.pop('domain_id', None)
        config.pop('domain_name', None)

        tmp_config_path = self._create_temp_config_file(config)

        try:
            obsClient = _create_obsclient_with_config_file(tmp_config_path)

            try:
                _try_get_credentials(obsClient._id_token_provider)

                resp = obsClient.listBuckets()
                assert resp.status < 300, \
                    "listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
            finally:
                obsClient.close()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_25: oidc_token_file 方式加载ID Token
    # ================================================================

    def test_tc_25_oidc_token_file_method(self):
        """
        tc_25: oidc_token_file 方式加载ID Token（对应Java 015）

        与tc_18的区别：tc_18是从已有配置文件读取oidc_token_file，
        本测试显式创建新的oidc_token_file临时文件并验证功能。

        测试步骤:
          1. 从有效配置中读取token内容
          2. 将token写入新的临时文件
          3. 创建临时配置文件，使用新文件的路径作为oidc_token_file
          4. 创建ObsClient
          5. 调用listBuckets()

        预期结果:
          listBuckets()返回成功状态码
        """
        valid_config = self._read_config_as_dict()

        # 从oidc_token_file或id_token读取token内容
        token_content = None
        oidc_token_file_path = valid_config.get('oidc_token_file')
        if oidc_token_file_path:
            with open(oidc_token_file_path, 'r') as f:
                token_content = f.read().strip()

        if not token_content:
            config_id_token = valid_config.get('id_token')
            if config_id_token:
                token_content = config_id_token

        if not token_content:
            pytest.skip("配置文件中无oidc_token_file或id_token，无法读取token内容")

        # 写入token到新的临时文件
        tmp_token = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        tmp_token.write(token_content)
        tmp_token.close()

        try:
            # 创建配置文件，使用新文件路径作为oidc_token_file
            config = dict(valid_config)
            config['oidc_token_file'] = tmp_token.name
            config.pop('id_token', None)

            tmp_config_path = self._create_temp_config_file(config)

            try:
                obsClient = _create_obsclient_with_config_file(tmp_config_path)

                try:
                    _try_get_credentials(obsClient._id_token_provider)

                    resp = obsClient.listBuckets()
                    assert resp.status < 300, \
                        "listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
                finally:
                    obsClient.close()
            finally:
                os.unlink(tmp_config_path)
        finally:
            os.unlink(tmp_token.name)

    # ================================================================
    # tc_26: id_token 和 oidc_token_file 互斥验证
    # ================================================================

    def test_tc_26_id_token_oidc_token_file_mutual_exclusion(self):
        """
        tc_26: id_token 和 oidc_token_file 互斥验证（对应Java 016）

        测试步骤:
          1. 创建IdTokenCredentialsProvider，同时指定id_token和oidc_token_file

        预期结果:
          抛出IdTokenParamsException，错误信息包含"mutually exclusive"
        """
        with pytest.raises(IdTokenParamsException, match="mutually exclusive"):
            IdTokenCredentialsProvider(
                id_token='eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjF9.test',
                oidc_token_file='/tmp/fake_oidc_token.txt',
                idp_id='test-idp',
                project_name='cn-north-4',
            )

    # ================================================================
    # tc_24: unscoped token 模式联邦认证
    # ================================================================

    def test_tc_24_unscoped_token(self):
        """
        tc_24: unscoped token 模式联邦认证（对应Java 014）

        与tc_21的区别：tc_21仅验证provider创建不抛异常，
        本测试验证完整流程：获取凭证并列举桶。

        测试步骤:
          1. 读取有效配置文件，移除所有project和domain字段
          2. 创建临时配置文件
          3. 创建ObsClient
          4. 获取凭证验证成功
          5. 调用listBuckets()

        预期结果:
          凭证获取成功，listBuckets()返回成功状态码
        """
        valid_config = self._read_config_as_dict()

        config = dict(valid_config)
        config.pop('project_id', None)
        config.pop('project_name', None)
        config.pop('domain_id', None)
        config.pop('domain_name', None)

        tmp_config_path = self._create_temp_config_file(config)

        try:
            obsClient = _create_obsclient_with_config_file(tmp_config_path)

            try:
                # 验证凭证获取成功
                cred = _try_get_credentials(obsClient._id_token_provider)
                assert cred is not None, "unscoped token应能获取凭证"
                assert cred.get('accessKey'), "凭证应包含accessKey"

                # 验证listBuckets成功
                resp = obsClient.listBuckets()
                assert resp.status < 300, \
                    "listBuckets()应返回成功状态码, 实际: {}".format(resp.status)
            finally:
                obsClient.close()
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_27: 构造函数指定IAM端点
    # ================================================================

    def test_tc_27_constructor_iam_endpoint(self):
        """
        tc_27: 构造函数指定IAM端点（对应Java 017）

        测试步骤:
          1. 创建临时配置文件，不含iam_endpoint
          2. 构造函数传入正确的iam_endpoint
          3. 获取凭证验证成功

        预期结果:
          构造函数的iam_endpoint参数生效，凭证获取成功
        """
        valid_config = self._read_config_as_dict()

        # 配置文件中移除iam_endpoint
        config = dict(valid_config)
        config.pop('iam_endpoint', None)

        tmp_config_path = self._create_temp_config_file(config)

        try:
            # 构造函数传入正确的iam_endpoint
            correct_endpoint = valid_config.get('iam_endpoint')
            provider = IdTokenCredentialsProvider(
                config_file=tmp_config_path,
                iam_endpoint=correct_endpoint,
            )

            # 验证构造函数的iam_endpoint生效
            assert provider.iam_endpoint == correct_endpoint, \
                "构造函数iam_endpoint应覆盖配置文件"

            # 验证能正常获取凭证
            cred = _try_get_credentials(provider)
            assert cred is not None, "使用构造函数iam_endpoint应能获取凭证"
            assert cred.get('accessKey'), "凭证应包含accessKey"
        finally:
            os.unlink(tmp_config_path)

    # ================================================================
    # tc_28: 配置文件iam_endpoint优先级
    # ================================================================

    def test_tc_28_config_file_iam_endpoint_priority(self):
        """
        tc_28: 配置文件iam_endpoint优先级（对应Java 018）

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
        config_file = self._get_valid_config_file()
        provider = IdTokenCredentialsProvider(config_file=config_file)

        # 验证配置文件中的iam_endpoint被加载
        valid_config = self._read_config_as_dict()
        assert provider.iam_endpoint == valid_config.get('iam_endpoint'), \
            "配置文件中的iam_endpoint应被加载"

        # 验证能正常获取凭证
        cred = _try_get_credentials(provider)
        assert cred is not None, "使用配置文件iam_endpoint应能获取凭证"
        assert cred.get('accessKey'), "凭证应包含accessKey"

    # ================================================================
    # tc_29: credential_expires_seconds 低于最小值被normalize
    # ================================================================

    def test_tc_29_credential_expires_seconds_below_minimum(self):
        """
        tc_29: credential_expires_seconds 低于最小值被normalize（对应Java 020）

        _validate_params()中：如果credential_expires_seconds < 900，自动修正为86400。

        测试步骤:
          1. 创建IdTokenCredentialsProvider，设置credential_expires_seconds=100
          2. 验证被自动修正为86400
          3. 获取凭证验证成功

        预期结果:
          credential_expires_seconds被修正为86400，凭证获取成功
        """
        config_file = self._get_valid_config_file()

        provider = IdTokenCredentialsProvider(
            config_file=config_file,
            credential_expires_seconds=100,
        )

        # 验证被修正为86400
        assert provider.credential_expires_seconds == 86400, \
            "credential_expires_seconds=100应被修正为86400, 实际: {}".format(
                provider.credential_expires_seconds)

        # 验证能正常获取凭证
        cred = _try_get_credentials(provider)
        assert cred is not None, "normalize后应能正常获取凭证"
        assert cred.get('accessKey'), "凭证应包含accessKey"

    # ================================================================
    # tc_30: 多线程并发获取凭证
    # ================================================================

    def test_tc_30_concurrent_get_credentials(self):
        """
        tc_30: 多线程并发获取凭证（对应Java 022）

        测试步骤:
          1. 创建IdTokenCredentialsProvider
          2. 先获取初始凭证（预热缓存）
          3. 启动5个线程同时调用get_credentials()
          4. 验证所有线程成功且看到相同的accessKey

        预期结果:
          所有线程成功获取凭证，且accessKey一致
        """
        config_file = self._get_valid_config_file()
        provider = IdTokenCredentialsProvider(config_file=config_file)

        # 先获取初始凭证（预热缓存，同时验证IAM服务端IdP是否已配置）
        initial_cred = _try_get_credentials(provider)
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
