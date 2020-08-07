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
 This sample demonstrates how to upload multiparts to OBS
 using the OBS SDK for Python.
"""

from __future__ import print_function
from obs import ObsClient, CompleteMultipartUploadRequest, CompletePart

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'
objectKey = 'my-obs-object-key-demo'

# Constructs a obs client instance with your account for accessing OBS
obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

# Create bucket
print('Create a new bucket for demo\n')
obsClient.createBucket(bucketName)

# Step 1: initiate multipart upload
print('Step 1: initiate multipart upload \n')
resp = obsClient.initiateMultipartUpload(bucketName, objectKey)
uploadId = resp.body.uploadId

# Step 2: upload a part
print('Step 2: upload a part\n')

partNum = 1
resp = obsClient.uploadPart(bucketName, objectKey, partNumber=partNum, uploadId=uploadId, content='Hello OBS')
etag = dict(resp.header).get('etag')

# Step 3: complete multipart upload
print('Step 3: complete multipart upload\n')
resp = obsClient.completeMultipartUpload(bucketName, objectKey, uploadId,
                                         CompleteMultipartUploadRequest([CompletePart(partNum=partNum, etag=etag)]))
if resp.status < 300:
    print('Complete finished\n')
