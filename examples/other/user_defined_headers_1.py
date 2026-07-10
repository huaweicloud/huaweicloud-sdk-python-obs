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
  This sample demonstrates how to download an object with rate limiting operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback
import os

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'

# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
objectKey = 'your-object-name'

# Specify the full path (localfile as an example) to which objects are downloaded. The full path contains the local file name.
downloadPath = 'localfile'

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Configure the download rate limit by specifying x-obs-traffic-limit, in bits. The value range is from 819200 (100 KB) to 838860800 (100 MB). 819200 is used as an example.
        extensionHeaders = {'x-obs-traffic-limit': 819200}

        # Download the object at a limited rate.
        resp = obsClient.getObject(bucketName, objectKey, downloadPath, extensionHeaders=extensionHeaders)

        # If status code 2xx is returned, the API was called successfully. Otherwise, the call failed.
        if resp.status < 300:
            print('Get Object Succeeded')
            print('requestId:', resp.requestId)
            print('url:', resp.body.url)
        else:
            print('Get Object Failed')
            print('status:', resp.status)
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Get Object Failed')
        print(traceback.format_exc())