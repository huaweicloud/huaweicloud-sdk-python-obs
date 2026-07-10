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
  This sample demonstrates how to upload and download objects with SSE-KMS encryption on OBS using the OBS SDK for Python.
"""

from __future__ import print_function
import os
import traceback

from obs import ObsClient, PutObjectHeader, GetObjectHeader, SseKmsHeader

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'

# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
objectKey = 'your-object-name'
file_path = 'localfile'
downloadPath = 'localfile'

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Specify the SSE-KMS encryption header for the object upload request
        put_headers = PutObjectHeader()
        put_headers.sseHeader = SseKmsHeader.getInstance()

        # Upload the object
        resp = obsClient.putFile(bucketName, objectKey, file_path, headers=put_headers)

        # If status code 2xx is returned, the API is called successfully. Otherwise, the API call fails.
        if resp.status < 300:
            print('Put File Succeeded')
            print('requestId:', resp.requestId)
        else:
            print('Put File Failed')
            print('status:', resp.status)
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)

        # Specify the SSE-KMS decryption header for the object download request
        get_headers = GetObjectHeader()
        get_headers.sseHeader = SseKmsHeader.getInstance()

        # Download the object
        resp2 = obsClient.getObject(bucketName, objectKey, downloadPath, headers=get_headers)

        # If status code 2xx is returned, the API is called successfully. Otherwise, the API call fails.
        if resp2.status < 300:
            print('Get Object Succeeded')
            print('requestId:', resp2.requestId)
        else:
            print('Get Object Failed')
            print('status:', resp.status)
            print('requestId:', resp2.requestId)
            print('errorCode:', resp2.errorCode)
            print('errorMessage:', resp2.errorMessage)
    except Exception as e:
        print('Operation Failed')
        print(traceback.format_exc())