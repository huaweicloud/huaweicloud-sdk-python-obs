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
 This sample demonstrates how to list objects under a specified folder of a bucket
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
folderPrefix = 'src'
subFolderPrefix = 'test'

keys = []

# First prepare folders and sub folders
for i in range(5):
    key = folderPrefix + str(i) + '/'
    obsClient.putContent(bucketName, key)
    keys.append(Object(key))

    for j in range(3):
        subKey = key + subFolderPrefix + str(j) + '/'
        obsClient.putContent(bucketName, subKey)
        keys.append(Object(subKey))

# Insert 2 objects in each folder
resp = obsClient.listObjects(bucketName)
for content in resp.body.contents:
    for i in range(2):
        objectKey = content.key + keyPrefix + str(i)
        obsClient.putContent(bucketName, objectKey, content)
        keys.append(Object(objectKey))

# Insert 2 objects in root path
obsClient.putContent(bucketName, keyPrefix + str(0), content)
obsClient.putContent(bucketName, keyPrefix + str(1), content)
keys.append(Object(keyPrefix + str(0)))
keys.append(Object(keyPrefix + str(1)))
print('Put %d objects completed' % len(keys))
print('\n')

# List all objects in folder src0/
print('List all objects in folder src0/ \n')
resp = obsClient.listObjects(bucketName, 'src0/')
for content in resp.body.contents:
    print('\t' + content.key + ' etag[' + content.etag + ']')

print('\n')

# List all objects in sub folder src0/test0/
print('List all objects in folder src0/test0/ \n')
resp = obsClient.listObjects(bucketName, 'src0/test0/')
for content in resp.body.contents:
    print('\t' + content.key + ' etag[' + content.etag + ']')

print('\n')


# List all objects group by folder

def listObjectsByPrefix(resp):
    for prefix in resp.body.commonPrefixs:
        print('Folder ' + prefix.prefix + ':')
        subresp = obsClient.listObjects(bucketName, delimiter='/', prefix=prefix.prefix)
        for content in subresp.body.contents:
            print('\t' + content.key)
        listObjectsByPrefix(subresp)


print('List all objects group by folder \n')
resp = obsClient.listObjects(bucketName, delimiter='/')
print('Root path:')
for content in resp.body.contents:
    print('\t' + content.key + ' etag[' + content.etag + ']')

listObjectsByPrefix(resp)

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
