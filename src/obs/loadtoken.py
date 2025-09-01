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
else:
    import http.client as httplib

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
            conn = httplib.HTTPConnection(hostIP, timeout=10)  # Handle timeout.
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
