#!/usr/bin/python
# -*- coding:utf-8 -*-
# Copyright 2019 Huawei Technologies Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations under the License.

"""
  This sample demonstrates how to upload a folder to a bucket using the OBS SDK for Python.
"""

from __future__ import print_function

from obs import ObsClient
import traceback

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
objectKey = 'your-object-key'

if __name__ == '__main__':
    try:
        # Create an obsClient instance
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
        # Specify a name for the uploaded folder. All files in the local folder are uploaded to this folder. Its name cannot end with a slash (/).
        objectKey = "folder"
        # Specify the full path of the folder to be uploaded, for example, aa/.
        folder_path = 'localfolder/'

        # Upload the folder
        resp = obsClient.putFile(bucketName, objectKey, folder_path)

        # Process the upload results
        if isinstance(resp, list):
            for res in resp:
                if res[1].status < 300:
                    print(f'Put File Succeeded, objectkey: {res[0]}')
                else:
                    print(f'Put File Failed, objectkey: {res[0]}')
                    print('requestId:', res[1].requestId)
                    print('errorCode:', res[1].errorCode)
                    print('errorMessage:', res[1].errorMessage)
        else:
            if resp.status < 300:
                print(f'Put File Succeeded, objectkey: {objectKey}')
            else:
                print(f'Put File Failed, objectkey: {objectKey}')
                print('requestId:', resp.requestId)
                print('errorCode:', resp.errorCode)
                print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Put File Failed')
        print(traceback.format_exc())