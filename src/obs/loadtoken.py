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

import os
import re
from json import JSONDecodeError

from obs import const
import threading
import json
from obs.ilog import ERROR, NoneLogClient, WARNING
import time

if const.IS_PYTHON2:
    import httplib
    from urlparse import urlparse
else:
    import http.client as httplib
    from urllib.parse import urlparse

from datetime import datetime
from datetime import timedelta

log_client = NoneLogClient()


class NoneTokenException(Exception):
    def __init__(self, errorInfo):
        super(NoneTokenException, self).__init__(errorInfo)
        self.errorInfo = errorInfo

    def __str__(self):
        return self.errorInfo


class ENV(object):

    @staticmethod
    def search():
        reAccessKey = 'OBS_ACCESS_KEY_ID'
        reSecretKey = 'OBS_SECRET_ACCESS_KEY'
        reSecurityToken = 'OBS_SECURITY_TOKEN'

        accessKey = os.environ.get(reAccessKey)
        secretKey = os.environ.get(reSecretKey)
        securityToken = os.environ.get(reSecurityToken)

        if accessKey is None or secretKey is None:
            raise NoneTokenException('get token failed')

        return {'accessKey': accessKey,
                'secretKey': secretKey,
                'securityToken': securityToken}

class RetryExhaustedException(Exception):
    """Raised when maximum retry attempts are exhausted"""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code  # Preserve last known status code


def retry_mechanism(max_retry, base_wait=0.1, log_prefix=""):
    """
    Decorator to implement retry logic with exponential backoff
    Args:
        max_retry: Maximum number of retry attempts
        base_wait: Base waiting time in seconds for exponential backoff
        log_prefix: Prefix for log messages
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            last_status_code = None  # Track the last error status code

            for retry_count in range(max_retry):
                try:
                    result = func(*args, **kwargs, retry_count=retry_count)
                    # Handle functions returning (should_retry, result_value) tuples
                    should_retry, result_value = result
                    if not should_retry:
                        return result_value

                except Exception as e:
                    # Capture status code if exception provides it
                    last_status_code = getattr(e, 'status_code', None)

                    # Wait before next retry (except after last attempt)
                    if retry_count < max_retry - 1:
                        sleep_time = (2 ** retry_count) * base_wait
                        time.sleep(sleep_time)

                    # Log retry attempt
                    log_client.log(WARNING,
                                   "{0} Retry {1}/{2}: {3}.".format(
                                       log_prefix, retry_count + 1, max_retry, str(e)))

            # All retries exhausted
            raise RetryExhaustedException(
                "{0} Maximum retry attempts ({1}) exhausted".format(log_prefix, max_retry),
                status_code=last_status_code
            )

        return wrapper

    return decorator

class ECS(object):
    """
    Background: The Itau customer is migrating to the cloud and requires metadata IMDS v2 interface parity with AWS.
    Retrieve temporary security credentials from the ECS service. If the cached credentials are valid,
    return the cached credentials; otherwise, fetch new ones. Supports v2/v1 features and includes a retry mechanism.
    """
    ak = None
    sk = None
    token = None
    expires = None
    # Thread lock to ensure thread-safe credential updates
    lock = threading.Lock()

    @staticmethod
    def search():
        # Fixed access IP.(IMDS standard address)
        hostIP = '169.254.169.254'
        # v2 request API token URL.
        tokenURL = '/meta-data/latest/api/token'
        # v1 and v2 URLs for obtaining the security key.
        securitykeyURL = '/openstack/latest/securitykey'

        # Check the cache first: if the credentials are not expired, return the cached credentials directly
        cached_cred = ECS._search_handle_expires(datetime, timedelta)
        if cached_cred is not None:
            return cached_cred

        # Lock to prevent concurrent credential updates (double-checked locking).
        if ECS.lock.acquire():
            try:
                # Check the cache again (to prevent updates by other threads during the lock release period)
                cached_cred = ECS._search_handle_lock_acquire(datetime, timedelta)
                if cached_cred is not None:
                    return cached_cred

                accessKey = None
                secretKey = None
                securityToken = None
                expiresAt = None
                conn = None
                try:
                    try:
                        # Obtain IP connection conn, status code, and API token with retry mechanism.
                        conn, status, token = ECS._get_api_token(hostIP, tokenURL)

                    except RetryExhaustedException as e:
                        # Retry failed, extract the last status code, preserving the original status code semantics
                        log_client.log(ERROR, str(e))
                        # Continue the logic with the last failure status code, use 500 if no status code is available, but only as a fallback
                        status = e.status_code if e.status_code is not None else 500
                        conn, token = None, None

                    # If the status code is < 300 but the result does not contain the token, log a warning. Then call the v1 API.
                    token_is_null = (status < 300 and (token is None or token.strip() == b''))
                    if token_is_null:
                        log_client.log(WARNING,'Failed to obtain a temporary ECS api token through the v2 interface, attempting to use v1.')
                    msg_maximum = 'Maximum number of retries reached, v{0} failed to obtain a temporary ECS credential.'
                    # Current environment does not support v2.
                    if status in [404, 405] or token_is_null:
                        # Obtain a credential that includes ak, sk, securitykey, and the expiration time.
                        response_credential = ECS._get_securitykey(conn, securitykeyURL, headers={}, flag_v2=False)
                        # Retry failed, returning empty response_credential.
                        if not response_credential:
                            log_client.log(ERROR, msg_maximum.format(1))
                            raise NoneTokenException(msg_maximum.format(1))
                    # v2 request succeeded.
                    elif status < 300:
                        securitykey_headers = {'X-securitykey-Token': token}
                        response_credential = ECS._get_securitykey(conn, securitykeyURL, securitykey_headers)
                        # Retry failed, returning empty response_credential.
                        if not response_credential:
                            log_client.log(ERROR, msg_maximum.format(2))
                            raise NoneTokenException(msg_maximum.format(2))
                    # Only enter the else branch if all retries fail; otherwise, determine whether to execute v1 or v2 based on the returned result.
                    else:
                        msg_fail_code = 'Maximum number of retries reached, failed to obtain a temporary ECS token, status code: {0}.'.format(status)
                        log_client.log(ERROR, msg_fail_code)
                        raise NoneTokenException(msg_fail_code)

                except Exception as e:
                    # use the unexpired securityKey
                    if ECS._search_judge(datetime):
                        return {
                            'accessKey': ECS.ak,
                            'secretKey': ECS.sk,
                            'securityToken': ECS.token
                        }
                    # Do not throw sensitive information in exceptions.
                    log_client.log(ERROR, "Failed to get the credential.")
                    raise NoneTokenException("Failed to get the credential.")
                finally:
                    if conn:
                        conn.close()

                try:
                    # Parse the credential using JSON, which is more efficient than the previous regular expression matching.
                    credential = json.loads(response_credential)['credential']
                except (JSONDecodeError, KeyError) as e:
                    if ECS._search_judge(datetime):
                        return {
                            'accessKey': ECS.ak,
                            'secretKey': ECS.sk,
                            'securityToken': ECS.token
                        }
                    msg_json_loads = 'Failed to parse token response: {0}.'.format(str(e))
                    log_client.log(ERROR, msg_json_loads)
                    raise NoneTokenException(msg_json_loads)
                accessKey = credential.get('access')
                secretKey = credential.get('secret')
                securityToken = credential.get('securitytoken')
                expiresAt = credential.get('expires_at')

                # Validate credential field completeness.
                if not all([accessKey, secretKey, securityToken, expiresAt]):
                    if ECS._search_judge(datetime):
                        return {
                            'accessKey': ECS.ak,
                            'secretKey': ECS.sk,
                            'securityToken': ECS.token
                        }
                    msg_incomplete = 'The ECS credential fields required for OBS obtainment are incomplete.'
                    log_client.log(ERROR, msg_incomplete)
                    raise NoneTokenException(msg_incomplete)

                ECS.ak = accessKey
                ECS.sk = secretKey
                ECS.token = securityToken
                ECS.expires = datetime.strptime(expiresAt, '%Y-%m-%dT%H:%M:%S.%fZ')

                return {
                    'accessKey': accessKey,
                    'secretKey': secretKey,
                    'securityToken': securityToken
                }
            finally:
                ECS.lock.release()



    @staticmethod
    def _search_handle_expires(current_datetime, ttl_timedelta):
        if ECS.expires is not None:
            token_date_now = current_datetime.utcnow()
            if token_date_now < (ECS.expires - ttl_timedelta(minutes=10)):
                return {
                    'accessKey': ECS.ak,
                    'secretKey': ECS.sk,
                    'securityToken': ECS.token
                }

    @staticmethod
    def _search_handle_lock_acquire(current_datetime, ttl_timedelta):
        if ECS.expires is not None and current_datetime.utcnow() < (ECS.expires - ttl_timedelta(minutes=10)):
            return {
                'accessKey': ECS.ak,
                'secretKey': ECS.sk,
                'securityToken': ECS.token
            }

    @staticmethod
    @retry_mechanism(max_retry=3, base_wait=0.1, log_prefix="Obtaining security credential failed.")
    def _get_securitykey(conn, contactTokenURL, headers, flag_v2=True, retry_count=0):
        """Retrieve security credentials (with retry mechanism)"""
        result = ECS._conn_request(conn, 'GET', contactTokenURL, headers=headers, flag_v2=flag_v2)
        credential_bytes = result.read()
        if credential_bytes:
            return False, credential_bytes.decode('utf-8')
        else:
            log_client.log(WARNING, "Obtained an empty security credential (retry {0}/3).".format(retry_count + 1))
            return True, None



    @staticmethod
    @retry_mechanism(max_retry=3, base_wait=0.1, log_prefix="Obtaining temporary ECS token failed.")
    def _get_api_token(hostIP, contactTokenURL, retry_count=0):
        """Retrieve token from v2 API (with retry mechanism)."""
        try:
            # Add retry mechanism, the retry_count is passed in by the decorator and is read-only within the function.
            conn = httplib.HTTPConnection(hostIP, timeout=5)  # Handle timeout.
            # use v2 to obtain token
            headers = {'X-securitykey-Token-Ttl-Seconds': "21600"}
            getTokenResult = ECS._conn_request(conn, 'PUT', contactTokenURL, headers=headers)
            token = getTokenResult.read()
            # Current environment does not support v2; if the status code is 404 or 405, fall back to v1.
            status = getTokenResult.status
            if status in [404, 405]:
                # No need to retry
                return False, (conn, status, None)
            # Request succeeded; temporarily ignore whether the token is empty, it will be handled upon return.
            elif status < 300:
                if token:
                    token = token.decode('utf-8')
                return False, (conn, status, token)  # No need to retry.
            else:
                e = Exception("Failed to obtain token, status code: {0}.".format(status))
                e.status_code = status
                raise e
        except Exception as e:
            # Ensure that all exception states carry a status code.
            if not hasattr(e, "status_code"):
                e.status_code = None
            raise e    # Throw an exception to let the decorator handle the retry.

    @staticmethod
    def _conn_request(conn, method, url, headers, flag_v2=True):
        if flag_v2:
            conn.request(method, url, headers=headers)
        else:
            conn.request(method, url)
        result = ECS._search_get_result(conn)
        return result

    @staticmethod
    def _search_handle_response_body(responseBody):
        if not const.IS_PYTHON2:
            return responseBody.decode('utf-8')
        return responseBody

    @staticmethod
    def _search_judge(current_datetime):
        return ECS.expires is not None and current_datetime.utcnow() < ECS.expires

    @staticmethod
    def _search_get_result(conn):
        return conn.getresponse(True) if const.IS_PYTHON2 else conn.getresponse()


class IdTokenAuthException(Exception):
    """联邦认证异常基类"""
    def __init__(self, code, message, status=None, request_id=None):
        super(IdTokenAuthException, self).__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.request_id = request_id

    def __str__(self):
        if self.status is not None:
            return 'IdTokenAuthException: [status={}, code={}, message={}]'.format(
                self.status, self.code, self.message)
        return 'IdTokenAuthException: [code={}, message={}]'.format(
            self.code, self.message)


class IdTokenExpiredException(IdTokenAuthException):
    """ID Token已过期"""
    pass


class IdTokenInvalidException(IdTokenAuthException):
    """ID Token格式无效"""
    pass


class FederationTokenException(IdTokenAuthException):
    """获取联邦认证Token失败"""
    pass


class TemporaryAKSKException(IdTokenAuthException):
    """获取临时AKSK失败"""
    pass


class IdTokenParamsException(ValueError):
    """IdToken参数配置错误"""
    pass


class OIDC(object):
    """
    OIDC自动发现凭证提供者（纯类模式，与ENV/ECS一致）

    自动发现规则:
      - HUAWEI_CLOUD_IDP_ID 环境变量 → idp_id（必需）
      - OIDC_TOKEN_FILE 环境变量 → OIDC token文件路径（优先级1）
      - /var/run/secrets/tokens/oidc-token → CCE默认路径（优先级2）
      - 未指定project/domain → 获取unscoped token
    """

    _provider_instance = None
    _lock = threading.Lock()
    _proxy_host = None
    _proxy_port = None
    _proxy_username = None
    _proxy_password = None

    @staticmethod
    def search():
        # Step 1: 从环境变量获取 idp_id
        idp_id = os.environ.get('HUAWEI_CLOUD_IDP_ID')
        if not idp_id:
            raise NoneTokenException(
                'HUAWEI_CLOUD_IDP_ID environment variable is not set, '
                'OIDC skipped')

        # Step 2: 发现 OIDC token 文件
        oidc_token_file = os.environ.get('OIDC_TOKEN_FILE')
        if oidc_token_file:
            if not os.path.isfile(oidc_token_file):
                raise NoneTokenException(
                    "OIDC_TOKEN_FILE '{}' does not exist, "
                    "OIDC skipped".format(oidc_token_file))
        else:
            default_path = IdTokenCredentialsProvider._DEFAULT_OIDC_TOKEN_FILE
            if os.path.isfile(default_path):
                oidc_token_file = default_path
            else:
                raise NoneTokenException(
                    'Neither OIDC_TOKEN_FILE environment variable nor default '
                    "oidc-token file '{}' found, OIDC skipped".format(
                        default_path))

        # Step 3: 获取凭证（双重检查锁定）
        # 快速路径：已有缓存实例
        if OIDC._provider_instance is not None:
            id_token = OIDC._read_token_file(oidc_token_file)
            OIDC._provider_instance.id_token = id_token
            return OIDC._provider_instance.get_credentials()

        # 慢速路径：加锁创建实例
        OIDC._lock.acquire()
        try:
            if OIDC._provider_instance is not None:
                id_token = OIDC._read_token_file(oidc_token_file)
                OIDC._provider_instance.id_token = id_token
                return OIDC._provider_instance.get_credentials()

            id_token = OIDC._read_token_file(oidc_token_file)
            provider = IdTokenCredentialsProvider(
                id_token=id_token,
                idp_id=idp_id,
            )

            if OIDC._proxy_host is not None:
                provider.set_proxy(
                    OIDC._proxy_host,
                    OIDC._proxy_port,
                    OIDC._proxy_username,
                    OIDC._proxy_password,
                )

            result = provider.get_credentials()
            OIDC._provider_instance = provider
            return result

        except IdTokenAuthException:
            raise
        except NoneTokenException:
            raise
        except Exception as e:
            log_client.log(ERROR, 'OIDC: {}'.format(str(e)))
            raise NoneTokenException('OIDC failed: {}'.format(str(e))) from e
        finally:
            OIDC._lock.release()

    @staticmethod
    def _read_token_file(filepath):
        with open(filepath, 'r') as f:
            return f.read().strip()

    @staticmethod
    def set_proxy(proxy_host, proxy_port, proxy_username=None, proxy_password=None):
        if OIDC._proxy_host is None and proxy_host is not None:
            OIDC._proxy_host = proxy_host
            OIDC._proxy_port = proxy_port
            if OIDC._proxy_username is None and proxy_username is not None:
                OIDC._proxy_username = proxy_username
                OIDC._proxy_password = proxy_password
            if OIDC._provider_instance is not None:
                OIDC._provider_instance.set_proxy(
                    proxy_host, proxy_port, proxy_username, proxy_password)


class IdTokenCredentialsProvider(object):
    """
    联邦认证(IdToken)凭证提供者

    支持使用第三方身份提供商(IdP)签发的ID Token换取华为云OBS临时访问凭证。
    """

    # 默认OIDC Token文件路径（CCE Pod中的路径）
    _DEFAULT_OIDC_TOKEN_FILE = '/var/run/secrets/tokens/oidc-token'
    # 默认IAM端点
    _DEFAULT_IAM_ENDPOINT = 'https://iam.myhuaweicloud.com'

    # 用于security_providers匹配的名称
    __name__ = 'IdTokenCredentialsProvider'

    def __init__(self, id_token=None, oidc_token_file=None, config_file=None,
                 idp_id=None, project_id=None, project_name=None,
                 domain_id=None, domain_name=None, iam_endpoint=None,
                 refresh_before_seconds=300, max_retry_times=3,
                 credential_expires_seconds=86400,
                 proxy_host=None, proxy_port=None,
                 proxy_username=None, proxy_password=None):
        """
        初始化IdToken凭证提供者

        :param id_token: ID Token字符串(JWT格式，由IdP签发)，与oidc_token_file互斥
        :param oidc_token_file: OIDC Token文件路径(纯文本JWT)，未指定时使用默认路径
        :param config_file: 配置文件路径(JSON格式)，提供idp_id等其他参数
        :param idp_id: 身份提供商ID，需与华为云IAM中创建的配置一致
        :param project_id: 项目ID(与domain互斥，可与project_name同时指定)
        :param project_name: 项目名称(与domain互斥，可与project_id同时指定)
        :param domain_id: 华为云账号ID(与project互斥，可与domain_name同时指定)
        :param domain_name: 华为云账号名(与project互斥，可与domain_id同时指定)
        :param iam_endpoint: IAM服务地址，如不指定则使用默认值
        :param refresh_before_seconds: 提前刷新秒数，默认300，建议值300-600
        :param max_retry_times: 网络请求失败时的最大重试次数，默认3
        :param credential_expires_seconds: 临时AKSK有效期秒数，默认86400(24小时)，最小900，最大86400，超出范围自动修正
        :param proxy_host: 代理服务器地址，如不指定则使用ObsClient的代理配置
        :param proxy_port: 代理服务器端口
        :param proxy_username: 代理服务器用户名
        :param proxy_password: 代理服务器密码
        :raises IdTokenParamsException: 必填参数缺失或参数组合无效
        """
        # Step 1: 从配置文件加载参数（最低优先级）
        if config_file:
            self._load_config_file(config_file)

        # Step 2: 构造函数显式传入的参数覆盖配置文件（最高优先级）
        if idp_id is not None:
            self.idp_id = idp_id
        if project_id is not None:
            self.project_id = project_id
        if project_name is not None:
            self.project_name = project_name
        if domain_id is not None:
            self.domain_id = domain_id
        if domain_name is not None:
            self.domain_name = domain_name
        if iam_endpoint is not None:
            self.iam_endpoint = iam_endpoint
        if refresh_before_seconds != 300:
            self.refresh_before_seconds = refresh_before_seconds
        if max_retry_times != 3:
            self.max_retry_times = max_retry_times
        if credential_expires_seconds != 86400:
            self.credential_expires_seconds = credential_expires_seconds
        if proxy_host is not None:
            self.proxy_host = proxy_host
        if proxy_port is not None:
            self.proxy_port = proxy_port
        if proxy_username is not None:
            self.proxy_username = proxy_username
        if proxy_password is not None:
            self.proxy_password = proxy_password
        # oidc_token_file: 构造函数参数覆盖config_file中的值
        if oidc_token_file is not None:
            self.oidc_token_file = oidc_token_file
        elif not hasattr(self, 'oidc_token_file'):
            self.oidc_token_file = None

        # Step 3: 解析id_token
        # 优先级：直接传入id_token > 默认路径 > oidc_token_file > config_file中的id_token
        self.id_token = self._resolve_id_token(id_token)

        # Step 4: 设置默认值（如果config_file和构造函数都没有指定）
        if not hasattr(self, 'idp_id'):
            self.idp_id = idp_id
        if not hasattr(self, 'project_id'):
            self.project_id = project_id
        if not hasattr(self, 'project_name'):
            self.project_name = project_name
        if not hasattr(self, 'domain_id'):
            self.domain_id = domain_id
        if not hasattr(self, 'domain_name'):
            self.domain_name = domain_name
        if not hasattr(self, 'iam_endpoint'):
            self.iam_endpoint = iam_endpoint if iam_endpoint else self._DEFAULT_IAM_ENDPOINT
        if not hasattr(self, 'refresh_before_seconds'):
            self.refresh_before_seconds = refresh_before_seconds
        if not hasattr(self, 'max_retry_times'):
            self.max_retry_times = max_retry_times
        if not hasattr(self, 'credential_expires_seconds'):
            self.credential_expires_seconds = credential_expires_seconds
        if not hasattr(self, 'proxy_host'):
            self.proxy_host = proxy_host
        if not hasattr(self, 'proxy_port'):
            self.proxy_port = proxy_port
        if not hasattr(self, 'proxy_username'):
            self.proxy_username = proxy_username
        if not hasattr(self, 'proxy_password'):
            self.proxy_password = proxy_password

        # Step 5: 实例级别缓存
        self._ak = None
        self._sk = None
        self._token = None
        self._expires = None
        self._lock = threading.Lock()

        # Step 6: 参数校验
        self._validate_params()

    def _resolve_id_token(self, id_token):
        """
        解析id_token

        优先级：直接传入id_token > oidc_token_file > 默认路径

        :param id_token: 构造函数直接传入的token字符串
        :return: id_token字符串
        :raises IdTokenParamsException: 参数冲突或所有来源均无法获取token
        """
        # 优先级1：构造函数直接传入的id_token
        if id_token:
            if self.oidc_token_file:
                raise IdTokenParamsException("id_token and oidc_token_file are mutually exclusive")
            return id_token

        # 优先级2：oidc_token_file（构造函数或config_file指定）
        if self.oidc_token_file:
            try:
                with open(self.oidc_token_file, 'r') as f:
                    return f.read().strip()
            except IOError as e:
                raise IdTokenParamsException(
                    "Failed to read oidc_token_file '{}': {}".format(self.oidc_token_file, str(e))
                )

        # 优先级3：默认路径 /var/run/secrets/tokens/oidc-token
        try:
            with open(self._DEFAULT_OIDC_TOKEN_FILE, 'r') as f:
                return f.read().strip()
        except IOError:
            pass

        # 优先级4：config_file中的id_token
        config_id_token = getattr(self, '_config_id_token', None)
        if config_id_token:
            return config_id_token

        # 所有来源均无法获取token
        raise IdTokenParamsException(
            "No id_token available: default oidc-token file '{}' not found, "
            "no oidc_token_file specified, and no id_token in config. "
            "Please specify id_token or oidc_token_file".format(self._DEFAULT_OIDC_TOKEN_FILE)
        )

    def _load_config_file(self, config_file):
        """
        从JSON配置文件加载参数，仅填充未显式传入的参数

        :param config_file: 配置文件路径
        """
        with open(config_file, 'r') as f:
            config = json.load(f)

        config_keys = ['idp_id', 'project_id', 'project_name',
                       'domain_id', 'domain_name', 'iam_endpoint',
                       'refresh_before_seconds', 'max_retry_times',
                       'credential_expires_seconds', 'oidc_token_file',
                       'proxy_host', 'proxy_port', 'proxy_username', 'proxy_password']

        for key in config_keys:
            if key in config:
                setattr(self, key, config[key])

        # id_token from config file is stored separately for _resolve_id_token to handle
        if 'id_token' in config:
            self._config_id_token = config['id_token']

    def set_proxy(self, proxy_host, proxy_port, proxy_username=None, proxy_password=None):
        """
        设置代理配置

        由ObsClient在初始化后调用，将ObsClient的代理配置同步到provider。
        仅当provider自身未配置代理时生效。

        :param proxy_host: 代理服务器地址
        :param proxy_port: 代理服务器端口
        :param proxy_username: 代理服务器用户名
        :param proxy_password: 代理服务器密码
        """
        if self.proxy_host is None and proxy_host is not None:
            self.proxy_host = proxy_host
            self.proxy_port = proxy_port
            if self.proxy_username is None and proxy_username is not None:
                self.proxy_username = proxy_username
                self.proxy_password = proxy_password

    def _create_connection(self, parsed_url):
        """
        创建HTTP连接，支持代理

        :param parsed_url: urlparse解析后的IAM端点
        :return: HTTP/HTTPS连接对象
        """
        is_secure = parsed_url.scheme == 'https'
        target_host = parsed_url.netloc
        # 解析host:port
        if ':' in target_host:
            host, port = target_host.rsplit(':', 1)
            port = int(port)
        else:
            host = target_host
            port = 443 if is_secure else 80

        if self.proxy_host is not None and self.proxy_port is not None:
            # 代理认证头
            proxy_headers = {}
            if self.proxy_username and self.proxy_password:
                import base64
                auth = base64.b64encode(
                    ('{}:{}'.format(self.proxy_username, self.proxy_password)).encode('utf-8')
                ).decode('utf-8')
                proxy_headers['Proxy-Authorization'] = 'Basic {}'.format(auth)

            # 通过代理连接：先连代理，再用CONNECT隧道连目标
            if is_secure:
                conn = httplib.HTTPSConnection(
                    self.proxy_host, port=self.proxy_port, timeout=10
                )
                conn.set_tunnel(host, port, headers=proxy_headers if proxy_headers else None)
            else:
                conn = httplib.HTTPConnection(
                    self.proxy_host, port=self.proxy_port, timeout=10
                )
                conn.set_tunnel(host, port, headers=proxy_headers if proxy_headers else None)
        else:
            # 直连IAM
            if is_secure:
                conn = httplib.HTTPSConnection(host, port=port, timeout=10)
            else:
                conn = httplib.HTTPConnection(host, port=port, timeout=10)

        return conn

    def _validate_params(self):
        """
        校验参数组合有效性

        :raises IdTokenParamsException: 参数无效
        """
        errors = []

        if not self.id_token:
            errors.append("id_token is required")

        if not self.idp_id:
            errors.append("idp_id is required")

        # project和domain互斥校验
        has_project = self.project_id or self.project_name
        has_domain = self.domain_id or self.domain_name

        if has_project and has_domain:
            errors.append("project and domain are mutually exclusive")

        # project和domain均不指定时获取unscoped token（合法场景）

        # 数值范围检查与自动修正
        if self.credential_expires_seconds < 900:
            self.credential_expires_seconds = 86400
        elif self.credential_expires_seconds > 86400:
            self.credential_expires_seconds = 86400

        if self.refresh_before_seconds <= 0:
            errors.append("refresh_before_seconds must be positive")

        if self.max_retry_times <= 0:
            errors.append("max_retry_times must be greater than 0")

        if errors:
            raise IdTokenParamsException("; ".join(errors))

    @staticmethod
    def search():
        """
        获取临时AKSK凭证

        实现CredentialsProvider接口，供ObsClient调用。
        注意：此方法需要作为实例方法调用，请使用get_credentials()

        :return: 包含accessKey、secretKey、securityToken的字典
        :raises IdTokenAuthException: 认证失败
        """
        raise IdTokenAuthException(
            code='ProviderNotSet',
            message='IdTokenCredentialsProvider must be used as instance, call get_credentials() instead'
        )

    def get_credentials(self):
        """
        获取临时AKSK凭证

        实现凭证提供者接口，供ObsClient调用。

        :return: 包含accessKey、secretKey、securityToken的字典
        :raises IdTokenAuthException: 认证失败
        """
        with self._lock:
            now = datetime.utcnow()
            if self._ak and self._sk and self._token and self._expires:
                # 计算刷新时间点
                refresh_time = self._expires - timedelta(seconds=self.refresh_before_seconds)
                if now < refresh_time:
                    return {
                        'accessKey': self._ak,
                        'secretKey': self._sk,
                        'securityToken': self._token
                    }

            # 缓存过期或不存在，获取新凭证
            try:
                federation_token = self._get_federation_token()
                cred = self._get_temporary_aksk(federation_token)

                self._ak = cred['access']
                self._sk = cred['secret']
                self._token = cred['securitytoken']
                self._expires = datetime.strptime(
                    cred['expires_at'], '%Y-%m-%dT%H:%M:%S.%fZ'
                )

                return {
                    'accessKey': self._ak,
                    'secretKey': self._sk,
                    'securityToken': self._token
                }
            except IdTokenAuthException:
                raise
            except Exception as e:
                raise IdTokenAuthException(
                    code='UnknownError',
                    message='Failed to get credentials: {}'.format(str(e))
                )

    def refresh(self):
        """
        手动刷新凭证

        清除缓存，强制在下一次调用get_credentials()时获取新凭证
        """
        with self._lock:
            self._ak = None
            self._sk = None
            self._token = None
            self._expires = None

    def _get_federation_token(self):
        """
        调用IAM接口获取联邦认证Token

        API: POST /v3.0/OS-AUTH/id-token/tokens

        :return: federation_token字符串
        :raises FederationTokenException: 获取失败
        """
        url = "{}/v3.0/OS-AUTH/id-token/tokens".format(self.iam_endpoint)

        headers = {
            'Content-Type': 'application/json;charset=utf8',
            'X-Idp-Id': self.idp_id
        }

        body = {
            'auth': {
                'id_token': {
                    'id': self.id_token
                }
            }
        }

        # 添加project或domain信息（互斥，project优先）
        if self.project_id and self.project_name:
            body['auth']['scope'] = {'project': {'id': self.project_id, 'name': self.project_name}}
        elif self.project_id:
            body['auth']['scope'] = {'project': {'id': self.project_id}}
        elif self.project_name:
            body['auth']['scope'] = {'project': {'name': self.project_name}}
        elif self.domain_id and self.domain_name:
            body['auth']['scope'] = {'domain': {'id': self.domain_id, 'name': self.domain_name}}
        elif self.domain_id:
            body['auth']['scope'] = {'domain': {'id': self.domain_id}}
        elif self.domain_name:
            body['auth']['scope'] = {'domain': {'name': self.domain_name}}
        # 均不指定时获取unscoped token（不设置scope字段）

        last_exception = None
        for attempt in range(self.max_retry_times):
            try:
                return self._do_federation_token_request(url, headers, body)
            except FederationTokenException:
                # 不重试认证相关异常
                raise
            except Exception as e:
                last_exception = e
                if attempt < self.max_retry_times - 1:
                    # 指数退避
                    time.sleep(2 ** attempt)

        raise FederationTokenException(
            code='NetworkError',
            message='Failed to get federation token after {} retries: {}'.format(
                self.max_retry_times, str(last_exception))
        )

    def _do_federation_token_request(self, url, headers, body):
        """
        执行联邦认证Token请求

        :return: federation_token字符串
        :raises FederationTokenException: 请求失败
        """
        try:
            parsed_url = urlparse(self.iam_endpoint)
            conn = self._create_connection(parsed_url)

            try:
                conn.request('POST', '/v3.0/OS-AUTH/id-token/tokens', json.dumps(body), headers)
                response = conn.getresponse()

                if response.status >= 400:
                    error_body = response.read().decode('utf-8')
                    try:
                        error_json = json.loads(error_body)
                        # IAM标准错误格式: {"error_code": "...", "error_msg": "..."}
                        error_code = error_json.get('error_code') or \
                            error_json.get('error', {}).get('code', 'UnknownError')
                        error_msg = error_json.get('error_msg') or \
                            error_json.get('error', {}).get('message', 'Unknown error')
                    except Exception:
                        error_code = str(response.status)
                        error_msg = 'IAM returned non-JSON response (HTTP {})'.format(response.status)

                    # 判断错误类型
                    if response.status == 401:
                        if 'expired' in error_msg.lower():
                            raise IdTokenExpiredException(
                                code=error_code,
                                message=error_msg,
                                status=response.status
                            )
                        else:
                            raise IdTokenInvalidException(
                                code=error_code,
                                message=error_msg,
                                status=response.status
                            )
                    else:
                        raise FederationTokenException(
                            code=error_code,
                            message=error_msg,
                            status=response.status
                        )

                federation_token = response.getheader('X-Subject-Token')
                if not federation_token:
                    raise FederationTokenException(
                        code='MissingToken',
                        message='X-Subject-Token header not found in response'
                    )

                return federation_token

            finally:
                conn.close()

        except IdTokenAuthException:
            raise
        except Exception as e:
            raise FederationTokenException(
                code='NetworkError',
                message='Failed to request federation token: {}'.format(str(e))
            )

    def _get_temporary_aksk(self, federation_token):
        """
        调用IAM接口获取临时AKSK

        API: POST /v3.0/OS-CREDENTIAL/securitytokens

        :param federation_token: 联邦认证Token
        :return: 包含access、secret、securitytoken、expires_at的字典
        :raises TemporaryAKSKException: 获取失败
        """
        url = "{}/v3.0/OS-CREDENTIAL/securitytokens".format(self.iam_endpoint)

        headers = {
            'Content-Type': 'application/json;charset=utf8',
            'X-Auth-Token': federation_token
        }

        body = {
            'auth': {
                'identity': {
                    'methods': ['token'],
                    'token': {
                        'duration_seconds': self.credential_expires_seconds
                    }
                }
            }
        }

        last_exception = None
        for attempt in range(self.max_retry_times):
            try:
                return self._do_temporary_aksk_request(url, headers, body)
            except TemporaryAKSKException:
                # 不重试认证相关异常
                raise
            except Exception as e:
                last_exception = e
                if attempt < self.max_retry_times - 1:
                    # 指数退避
                    time.sleep(2 ** attempt)

        raise TemporaryAKSKException(
            code='NetworkError',
            message='Failed to get temporary AKSK after {} retries: {}'.format(
                self.max_retry_times, str(last_exception))
        )

    def _do_temporary_aksk_request(self, url, headers, body):
        """
        执行临时AKSK请求

        :param federation_token: 联邦认证Token
        :return: 包含access、secret、securitytoken、expires_at的字典
        :raises TemporaryAKSKException: 请求失败
        """
        try:
            parsed_url = urlparse(self.iam_endpoint)
            conn = self._create_connection(parsed_url)

            try:
                conn.request('POST', '/v3.0/OS-CREDENTIAL/securitytokens', json.dumps(body), headers)
                response = conn.getresponse()

                if response.status >= 400:
                    error_body = response.read().decode('utf-8')
                    try:
                        error_json = json.loads(error_body)
                        # IAM标准错误格式: {"error_code": "...", "error_msg": "..."}
                        error_code = error_json.get('error_code') or \
                            error_json.get('error', {}).get('code', 'UnknownError')
                        error_msg = error_json.get('error_msg') or \
                            error_json.get('error', {}).get('message', 'Unknown error')
                    except Exception:
                        error_code = str(response.status)
                        error_msg = 'IAM returned non-JSON response (HTTP {})'.format(response.status)

                    raise TemporaryAKSKException(
                        code=error_code,
                        message=error_msg,
                        status=response.status
                    )

                result_body = response.read().decode('utf-8')
                result = json.loads(result_body)

                credential = result.get('credential', {})
                return {
                    'access': credential.get('access'),
                    'secret': credential.get('secret'),
                    'securitytoken': credential.get('securitytoken'),
                    'expires_at': credential.get('expires_at')
                }

            finally:
                conn.close()

        except TemporaryAKSKException:
            raise
        except Exception as e:
            raise TemporaryAKSKException(
                code='NetworkError',
                message='Failed to request temporary AKSK: {}'.format(str(e))
            )
