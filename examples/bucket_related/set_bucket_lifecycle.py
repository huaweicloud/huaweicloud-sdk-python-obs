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
  This sample demonstrates how to set bucket lifecycle operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback

from obs import ObsClient
from obs import Expiration, NoncurrentVersionExpiration
from obs import DateTime
from obs import Rule
from obs import Lifecycle

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Set lifecycle rules for the bucket
        # Set lifecycle rule for objects with prefix 'prefix1' to expire and delete after 60 days
        rule1 = Rule(id='rule1', prefix='prefix1', status='Enabled', expiration=Expiration(days=60))
        # Set lifecycle rule for objects with prefix 'prefix2' to expire and delete on December 31, 2026
        rule2 = Rule(id='rule2', prefix='prefix2', status='Enabled', expiration=Expiration(date=DateTime(2026, 12, 31)))
        lifecycle = Lifecycle(rule=[rule1, rule2])
        # Set bucket lifecycle
        resp = obsClient.setBucketLifecycle(bucketName, lifecycle)

        # If the return code is 2xx, the API is successfully called. Otherwise, the API fails to be called
        if resp.status < 300:
            print('Set Bucket Lifecycle Succeeded')
            print('requestId:', resp.requestId)
        else:
            print('Set Bucket Lifecycle Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Set Bucket Lifecycle Failed')
        print(traceback.format_exc())