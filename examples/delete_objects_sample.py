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
 This sample demonstrates how to delete objects under specified bucket
 from OBS using the OBS SDK for Python.
"""

from __future__ import print_function
from obs import ObsClient, Object, DeleteObjectsRequest

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'

# Constructs a obs client instance with your account for accessing OBS
obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

# Create bucket
print('Create a new bucket for demo\n')
obsClient.createBucket(bucketName)

# Batch put objects into the bucket
content = 'Thank you for using Object Storage Service'
keyPrefix = 'MyObjectKey'
keys = []
for i in range(100):
    key = keyPrefix + str(i)
    obsClient.putContent(bucketName, key, content)
    print('Succeed to put object ' + str(key))
    keys.append(Object(key=key))

print('\n')

# Delete all objects uploaded recently under the bucket
print('\nDeleting all objects\n')

resp = obsClient.deleteObjects(bucketName, DeleteObjectsRequest(False, keys))

print('Delete results:')
if resp.body.deleted:
    for delete in resp.body.deleted:
        print('\t' + str(delete))
if resp.body.error:
    for err in resp.body.error:
        print('\t' + str(err))
