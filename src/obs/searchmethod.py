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

from obs.loadtoken import NoneTokenException
from obs.ilog import WARNING

def get_token(security_providers, name='OBS_DEFAULT'):
    if name == 'OBS_DEFAULT':
        for method in security_providers:
            try:
                value = _call_provider_method(method)
            except Exception as e:
                log_msg = "Provider '{}' search error: {}".format(
                    getattr(method, '__name__', 'Unknown'), str(e))
                try:
                    from obs.loadtoken import log_client
                    log_client.log(WARNING, log_msg)
                except Exception:
                    print(log_msg)
            else:
                return {'accessKey': value.get('accessKey'),
                        'secretKey': value.get('secretKey'),
                        'securityToken': value.get('securityToken')}
        raise NoneTokenException('get token failed')

    for method in security_providers:
        if getattr(method, '__name__') == name:
            try:
                value = _call_provider_method(method)
            except Exception:
                raise
            else:
                return {'accessKey': value.get('accessKey'),
                        'secretKey': value.get('secretKey'),
                        'securityToken': value.get('securityToken')}
    raise ValueError('No such method: ' + name)


def _call_provider_method(method):
    """
    调用凭证提供者的方法获取凭证

    优先调用实例方法get_credentials()，如果没有则调用静态方法search()

    :param method: 凭证提供者实例或类
    :return: 包含accessKey、secretKey、securityToken的字典
    """
    # 如果是实例且有get_credentials方法，优先调用
    if hasattr(method, 'get_credentials') and callable(getattr(method, 'get_credentials')):
        return method.get_credentials()
    # 否则调用静态方法search()
    return method.search()
