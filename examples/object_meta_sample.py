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
 This sample demonstrates how to set/get self-defined metadata for object
 on OBS using the OBS SDK for Python.
"""

from __future__ import print_function
from obs import ObsClient, PutObjectHeader

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

# Setting object mime type
headers = PutObjectHeader(contentType='text/plain')

# Setting self-defined metadata
metadata = {'meta1': 'value1', 'meta2': 'value2'}

resp = obsClient.putContent(bucketName, objectKey, 'Hello OBS', metadata=metadata, headers=headers)
if resp.status < 300:
    print('Create object ' + objectKey + ' successfully!\n')
else:
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)

# Get object metadata
resp = obsClient.getObjectMetadata(bucketName, objectKey)
header = dict(resp.header)
print('\tContentType:' + header.get('content-type'))
print('\tmeta1:' + header.get('meta1'))
print('\tmeta2:' + header.get('meta2'))

obsClient.deleteObject(bucketName, objectKey)
