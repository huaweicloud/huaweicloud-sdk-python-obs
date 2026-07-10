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
  This sample demonstrates how to get bucket storage info operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback

from obs import ObsClient
import os

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket. CN-Hong Kong is used here as an example. Replace it with the one in use.
server = 'https://obs.ap-southeast-1.myhuaweicloud.com'
# Specify the name of the bucket to get storage info for.
bucketName = 'examplebucket'

if __name__ == '__main__':
    # Create an obsClient instance.
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Get bucket storage info.
        resp = obsClient.getBucketStorageInfo(bucketName)
        # If status code 2xx is returned, the API is called successfully. Otherwise, the API call fails.
        if resp.status < 300:
            print('Get Bucket StorageInfo Succeeded')
            print('requestId:', resp.requestId)
            print('size:', resp.body.size)
            print('objectNumber:', resp.body.objectNumber)
        else:
            print('Get Bucket StorageInfo Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Get Bucket StorageInfo Failed')
        print(traceback.format_exc())