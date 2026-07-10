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
  This example shows how to use the Python SDK to upload a file to an OBS bucket and verify data consistency using the CRC64 function.
"""

from __future__ import print_function

from obs import ObsClient, PutObjectHeader
import os
import traceback

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = "https://your-endpoint"
bucketName = "your-obs-bucket"
objectKey = "example/objectname"
# Full path of the file/folder to be uploaded, e.g., aa/bb.txt, or aa/
file_path = "D:\\example.txt"

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    headers = PutObjectHeader()
    # Set CRC64 check
    headers.isAttachCrc64 = True

    try:
        # Put file
        resp = obsClient.putFile(bucketName, objectKey, file_path, headers=headers)
        # Return code 2xx indicates success, otherwise failure
        if resp.status < 300:
            print('Put File Succeeded')
            print('requestId:', resp.requestId)
            print('crc64:', resp.body.crc64)
            print('versionId:', resp.body.versionId)
        else:
            print('Put File Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Put File Failed')
        print(traceback.format_exc())