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
  This sample demonstrates how to perform multipart upload operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import os
import traceback
from obs import ObsClient, CompleteMultipartUploadRequest, CompletePart

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
# Bucket name
bucketName = 'your-obs-bucket'
# Object name
objectKey = 'your-object-name'
# Local file path to upload
filePath = 'D:/tmp/file.txt'
# MIME type for the object
contentType = 'text/plain'
# Size of each part to upload (512MB)
partSize = 512 * 1024 * 1024

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Initiate a multipart upload
        resp = obsClient.initiateMultipartUpload(bucketName, objectKey, contentType=contentType)
        if resp.status >= 300:
            print('Initiate Multipart Upload Failed')
            print("status_code:", resp.status)
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
        else:
            uploadId = resp.body["uploadId"]

            contentLength = os.path.getsize(filePath)
            offset = 0
            partNum = 1
            etags = {}

            # Upload parts
            while offset < contentLength:
                currentPartSize = min(partSize, (contentLength - offset))
                resp1 = obsClient.uploadPart(bucketName, objectKey, partNum, uploadId, filePath, True, currentPartSize,
                                             offset)
                etags[partNum] = resp1.body.etag
                offset += currentPartSize
                partNum += 1

            # Assemble parts
            completes = [CompletePart(i, etags[i]) for i in range(1, partNum)]
            completeMultipartUploadRequest = CompleteMultipartUploadRequest(parts=completes)

            # Complete multipart upload
            resp = obsClient.completeMultipartUpload(bucketName, objectKey, uploadId, completeMultipartUploadRequest)

            # Check response status
            if resp.status < 300:
                print('Upload Part Succeeded')
                print('requestId:', resp.requestId)
                print('etag:', resp.body.etag)
            else:
                print('Upload Part Failed')
                print('requestId:', resp.requestId)
                print('errorCode:', resp.errorCode)
                print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('multPartsUpload Failed')
        print(traceback.format_exc())