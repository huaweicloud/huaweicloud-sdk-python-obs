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
  This sample demonstrates how to upload files to OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import os
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
# Before running the sample code, ensure that the environment variables AccessKeyID and SecretAccessKey have been configured.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# (Optional) If you use a temporary AK and SK pair and a security token to access OBS, obtain them from environment variables.
# security_token = os.getenv("SecurityToken")
# Set server to the endpoint corresponding to the bucket. CN-Hong Kong is used here as an example. Replace it with the one in use.
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
# Specify a name for the uploaded folder. All files in the local folder are uploaded to this folder. Its name must end with a slash (/). If you want to upload files to the root directory, enter an empty string for the prefix, that is, prefix = ''.
prefix = 'testobs/'
folderPath = 'localfolder/'
threadNum = 20

if __name__ == '__main__':
    try:
        # Create an obsClient instance.
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
        # Create a thread pool for upload.
        pool = ThreadPoolExecutor(threadNum)
        allTask = []

        g = os.walk(folderPath)
        for path, dir_list, file_list in g:
            for file_name in file_list:
                srcKey = os.path.join(path, file_name)
                obsObjectKey = prefix + srcKey.split(folderPath)[1].replace('\\', '/')
                exists = False
                try:
                    # Check whether the file already exists on OBS based on the object name.
                    resp = obsClient.headObject(bucketName, obsObjectKey)
                    if resp.status < 300:
                        exists = True
                    elif resp.status == 404:
                        exists = False
                    else:
                        print('Error happened, reupload it.')
                    if not exists:
                        print("File %s not exists in obs, upload it", srcKey)
                        allTask.append(pool.submit(obsClient.putFile, bucketName, obsObjectKey, srcKey))
                except:
                    print(traceback.format_exc())

        for future in as_completed(allTask):
            put_resp = future.result()
            if put_resp.status < 300:
                print(f'Put File Succeeded, objectUrl: {put_resp.body.objectUrl}')
            else:
                print('Put File Failed')
                print('requestId:', put_resp.requestId)
                print('errorCode:', put_resp.errorCode)
                print('errorMessage:', put_resp.errorMessage)
        
        # Shutdown the thread pool to release resources
        pool.shutdown(wait=True)
    except Exception as e:
        print('Upload Files Failed')
        print(traceback.format_exc())
    finally:
        if 'pool' in locals() and pool:
            pool.shutdown(wait=True)