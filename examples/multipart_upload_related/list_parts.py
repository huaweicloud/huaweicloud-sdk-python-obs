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
  This sample demonstrates how to list parts operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function
import os
import traceback

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'

# Set server to the endpoint corresponding to the bucket. CN-Hong Kong is used here as an example. Replace it with the one in use.
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
objectKey = 'your-object-name'
# Specify the ID of the multipart upload.
uploadId = "your-uploadid"
# Specify the maximum number (10 as an example) of parts that can be listed per page.
maxParts = 10

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # List the uploaded parts
        resp = obsClient.listParts(bucketName, objectKey, uploadId, maxParts, encoding_type='url')

        # If the return code is 2xx, the API is successfully called. Otherwise, the API fails to be called
        if resp.status < 300:
            print('List Parts Succeeded')
            print('requestId:', resp.requestId)
            print('bucketName:', resp.body.bucketName)
            print('objectKey:', resp.body.objectKey)
            print('uploadId:', resp.body.uploadId)
            print('storageClass:', resp.body.storageClass)
            print('isTruncated:', resp.body.isTruncated)
            print('initiator:', resp.body.initiator)
            print('owner:', resp.body.owner)

            index = 1
            for part in resp.body.parts:
                print('part [' + str(index) + ']')
                print('partNumber:', part.partNumber)
                print('lastModified:', part.lastModified)
                print('etag:', part.etag)
                print('size:', part.size)
                index += 1
        else:
            print('List Parts Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('List Parts Failed')
        print(traceback.format_exc())