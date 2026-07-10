#! /usr/bin/python
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
  This example shows how to use the Python SDK to download an object from an OBS bucket and obtain the download progress.
"""

from __future__ import print_function

import traceback

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# 【Optional】If you use temporary AK/SK and SecurityToken to access OBS, it is also recommended to obtain them through environment variables.
security_token = "SecurityToken"
# server is filled with the endpoint corresponding to the bucket. This example uses China-Hong Kong, please fill in other regions according to the actual situation.
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'

if __name__ == '__main__':
    # Create an obsClient instance
    # If you use temporary AK/SK and SecurityToken to access OBS, you need to specify the securityToken value through the security_token parameter when creating an instance.
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    # Get the progress of downloading an object
    def callback(transferredAmount, totalAmount, totalSeconds):
        # Get the average download rate (KB/S)
        print(transferredAmount * 1.0 / totalSeconds / 1024)
        # Get the download progress percentage
        print(transferredAmount * 100.0 / totalAmount)

    try:
        objectKey = "objectname"
        # Download an object
        resp = obsClient.getObject(bucketName=bucketName, objectKey=objectKey, progressCallback=callback)
        # When the return code is 2xx, the API call is successful, otherwise the API call fails
        if resp.status < 300:
            print('Get Object Succeeded')
            print('requestId:', resp.requestId)
            # Read object content
            try:
                while True:
                    chunk = resp.body.response.read(65536)
                    if not chunk:
                        break
                    print(chunk)
            finally:
                resp.body.response.close()
        else:
            print('Get Object Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Get Object Failed')
        print(traceback.format_exc())