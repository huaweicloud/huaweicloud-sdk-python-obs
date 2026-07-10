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
  This sample demonstrates how to complete multipart upload operation on OBS using the OBS SDK for Python.
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
bucketName = 'your-obs-bucket'
objectKey = 'your-object-name'
# Specify the ID of the multipart upload.
uploadId = "your-uploadid"

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Specify the list of parts to be assembled by configuring completeMultipartUploadRequest. Each part contains partNum and etag.
        part1 = CompletePart(partNum=1, etag='etag1')
        part2 = CompletePart(partNum=2, etag='etag2')
        completeMultipartUploadRequest = CompleteMultipartUploadRequest(parts=[part1,part2])

        # Assemble the parts uploaded to the bucket.
        resp = obsClient.completeMultipartUpload(bucketName, objectKey, uploadId, completeMultipartUploadRequest, encoding_type='url')

        # If the return code is 2xx, the API is successfully called. Otherwise, the API fails to be called
        if resp.status < 300:
            print('Complete Multipart Upload Succeeded')
            print('requestId:', resp.requestId)
            print('etag:', resp.body.etag)
            print('bucket:', resp.body.bucket)
            print('key:', resp.body.key)
            print('location:', resp.body.location)
            print('versionId:', resp.body.versionId)
        else:
            print('Complete Multipart Upload Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Complete Multipart Upload Failed')
        print(traceback.format_exc())