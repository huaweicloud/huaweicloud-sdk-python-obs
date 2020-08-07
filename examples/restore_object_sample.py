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
 This sample demonstrates how to download an cold object
 from OBS using the OBS SDK for Python.
"""

from __future__ import print_function
from obs import ObsClient, CreateBucketHeader, StorageClass, RestoreTier
import time

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-cold-bucket-demo'
objectKey = 'my-obs-cold-object-key-demo'

# Constructs a obs client instance with your account for accessing OBS
obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

# Create a cold bucket
print('Create a new cold bucket for demo\n')
obsClient.createBucket(bucketName, CreateBucketHeader(storageClass=StorageClass.COLD))

# Create a cold object
print('Create a new cold object for demo\n')
obsClient.putContent(bucketName, objectKey, 'Hello OBS')

# Restore the cold object
print('Restore the cold object')
obsClient.restoreObject(bucketName, objectKey, 1, tier=RestoreTier.EXPEDITED)

# Wait 6 minute to get the object
time.sleep(6 * 60)

# Get the cold object status
print('Get the cold object status')
resp = obsClient.restoreObject(bucketName, objectKey, 1, tier=RestoreTier.EXPEDITED)
print('\tstatus code ' + str(resp.status))

# Get the cold object
print('Get the cold object')
resp = obsClient.getObject(bucketName, objectKey, loadStreamInMemory=True)
print('\tobject content:%s' % resp.body.buffer)

# Delete the cold object
obsClient.deleteObject(bucketName, objectKey)
