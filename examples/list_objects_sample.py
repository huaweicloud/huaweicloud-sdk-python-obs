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
This sample demonstrates how to list objects under specified bucket
from OBS using the OBS SDK for Python.
"""

from __future__ import print_function
from obs import ObsClient, Object, DeleteObjectsRequest

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

content = 'Hello OBS'
keyPrefix = 'MyObjectKey'

keys = []

# First insert 100 objects for demo
for i in range(100):
    key = keyPrefix + str(i)
    obsClient.putContent(bucketName, key, content)
    keys.append(Object(key))

print('Put ' + str(len(keys)) + ' objects completed.' + '\n')

# List objects using default parameters, will return up to 1000 objects
print('List objects using default parameters:\n')
resp = obsClient.listObjects(bucketName)
for content in resp.body.contents:
    print('\t' + content.key + ' etag[' + content.etag + ']')

print('\n')

# List the first 10 objects
print('List the first 10 objects :\n')
resp = obsClient.listObjects(bucketName, max_keys=10)
for content in resp.body.contents:
    print('\t' + content.key + ' etag[' + content.etag + ']')

print('\n')

theSecond10ObjectsMarker = resp.body.next_marker

# List the second 10 objects using marker
print('List the second 10 objects using marker:\n')
resp = obsClient.listObjects(bucketName, max_keys=10, marker=theSecond10ObjectsMarker)
for content in resp.body.contents:
    print('\t' + content.key + ' etag[' + content.etag + ']')

print('\n')

# List objects with prefix and max keys
print('List objects with prefix and max keys:\n')
resp = obsClient.listObjects(bucketName, max_keys=5, prefix=keyPrefix + '2')
for content in resp.body.contents:
    print('\t' + content.key + ' etag[' + content.etag + ']')

print('\n')

# List all the objects in way of pagination
print('List all the objects in way of pagination: \n')
pageSize = 10
index = 1
nextMarker = None
while True:
    resp = obsClient.listObjects(bucketName, max_keys=pageSize, marker=nextMarker)
    print('Page:' + str(index) + '\n')
    for content in resp.body.contents:
        print('\t' + content.key + ' etag[' + content.etag + ']')

    if not resp.body.is_truncated:
        break
    nextMarker = resp.body.next_marker
    index += 1

print('\n')

# Delete all the objects created
resp = obsClient.deleteObjects(bucketName, DeleteObjectsRequest(False, keys))
print('Delete results:')
if resp.body.deleted:
    for delete in resp.body.deleted:
        print('\t' + str(delete))
if resp.body.error:
    for err in resp.body.error:
        print('\t' + str(err))
