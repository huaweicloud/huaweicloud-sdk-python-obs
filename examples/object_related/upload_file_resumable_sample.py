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
  This sample demonstrates how to upload file using resumable upload on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
# Specify an object name (the name displayed after the file is uploaded to the bucket).
objectKey = 'your-object-key'
# Specify the path of the file to be uploaded.
uploadFile = 'localfile'

if __name__ == '__main__':
    try:
        # Create an obsClient instance
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

        # Specify the number of parts that can be concurrently uploaded.
        taskNum = 5
        # Specify the part size, in bytes. 10 MB is used as an example.
        partSize = 10 * 1024 * 1024
        # Enable the resumable upload by setting enableCheckpoint to True.
        enableCheckpoint = True
        # Upload the object using resumable upload.
        resp = obsClient.uploadFile(bucketName, objectKey, uploadFile, partSize, taskNum, enableCheckpoint, encoding_type='url')

        # If status code 2xx is returned, the API is called successfully. Otherwise, the API call fails.
        if resp.status < 300:
            print('Upload File Succeeded')
            print('requestId:', resp.requestId)
        else:
            print('Upload File Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Upload File Failed')
        print(traceback.format_exc())