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
  This sample demonstrates how to initiate multipart upload operation on OBS using the OBS SDK for Python.
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
# Specify a pre-defined ACL (PRIVATE as an example).
acl = 'PRIVATE'
# Specify a storage class (STANDARD as an example) for the object.
storageClass = 'STANDARD'
# Specify a custom metadata of the object.
metadata = {'key': 'value'}
# Specify the MIME type for the object.
contentType = 'text/plain'
# Specify the lifecycle (7 as an example) for the object, in days.
expires = 7

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Initiate a multipart upload
        resp = obsClient.initiateMultipartUpload(bucketName, objectKey, acl, storageClass, metadata,
                                                 contentType=contentType, expires=expires, encoding_type='url')

        # If the return code is 2xx, the API is successfully called. Otherwise, the API fails to be called
        if resp.status < 300:
            print('Initiate Multipart Upload Succeeded')
            print('requestId:', resp.requestId)
            print('bucketName:', resp.body.bucketName)
            print('objectKey:', resp.body.objectKey)
            print('uploadId:', resp.body.uploadId)
        else:
            print('Initiate Multipart Upload Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Initiate Multipart Upload Failed')
        print(traceback.format_exc())