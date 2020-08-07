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
 This sample demonstrates how to create an empty folder under
 specified bucket to OBS using the OBS SDK for Python.
"""

from __future__ import print_function
from obs import ObsClient

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'

# Constructs a obs client instance with your account for accessing OBS
obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

# Create bucket
print('Create a new bucket for demo\n')
obsClient.createBucket(bucketName)

keySuffixWithSlash1 = 'MyObjectKey1/'
keySuffixWithSlash2 = 'MyObjectKey2/'
# Create two empty folder without request body, note that the key must be suffixed with a slash
obsClient.putContent(bucketName, keySuffixWithSlash1, '')
print('Creating an empty folder ' + keySuffixWithSlash1)

obsClient.putContent(bucketName, keySuffixWithSlash2)
print('Creating an empty folder ' + keySuffixWithSlash2)

# Verify whether the size of the empty folder is zero
resp = obsClient.getObjectMetadata(bucketName, keySuffixWithSlash1)
print('Size of the empty folder ' + keySuffixWithSlash1 + ' is ' + str(dict(resp.header).get('content-length')))
resp = obsClient.getObjectMetadata(bucketName, keySuffixWithSlash2)
print('Size of the empty folder ' + keySuffixWithSlash2 + ' is ' + str(dict(resp.header).get('content-length')))
