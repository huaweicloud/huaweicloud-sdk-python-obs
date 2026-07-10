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
  This sample demonstrates how to count the size and number of files of a certain type (suffix) on OBS using the OBS SDK for Python.
"""

from obs import ObsClient
import os
import traceback
import sys

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
# Fill in the bucketName with the name of the already created bucket.
bucketName = 'your-obs-bucket'
# Fill in the fileExtension with the file suffix you want to count, for example '.txt' or '.jpg'
fileExtension = '.txt'

if __name__ == '__main__':
    # Create an obsClient instance
    # If using temporary AK/SK and SecurityToken to access OBS, you need to specify the securityToken value through the security_token parameter when creating the instance.
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Get all objects in the bucket.
        resp = obsClient.listObjects(bucketName)

        # Check if the API call was successful
        if resp.status < 300:
            totalFileSize = 0
            fileCount = 0

            # Iterate through the object list and count the size and number of files with the specified suffix.
            for content in resp.body.contents:
                if content.key.endswith(fileExtension):
                    totalFileSize += content.size
                    fileCount += 1
        else:
            print('List Objects Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
            sys.exit(1)  # 使用 sys.exit() 退出程序

        # Output the statistics results
        print(f'Total {fileExtension} Files Count:', fileCount)
        print(f'Total {fileExtension} Files Size:', totalFileSize, 'bytes')
    except Exception as e:
        print('Count Files by Extension Failed')
        print(traceback.format_exc())
