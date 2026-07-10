#!/usr/bin/python
# -*- coding:utf-8 -*-
# Copyright 2019 Huawei Technologies Co.,Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations under the License.
#
"""
  This sample demonstrates how to set bucket quota on OBS using the OBS SDK for Python.
"""
#
from __future__ import print_function
import os
from obs import ObsClient
import traceback
#
# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
#
if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
    try:
        # Specify the bucket quota value, for example, 1G, in bytes
        quota = 1024 * 1024 * 1024
        # Set bucket quota
        resp = obsClient.setBucketQuota(bucketName, quota)
        # Return code is 2xx when the API call is successful, otherwise the API call fails
        if resp.status < 300:
            print('Set Bucket Quota Succeeded')
            print('requestId:', resp.requestId)
        else:
            print('Set Bucket Quota Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Set Bucket Quota Failed')
        print(traceback.format_exc())