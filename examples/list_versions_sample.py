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
 This sample demonstrates how to list versions under specified bucket
 from OBS using the OBS SDK for Python.
"""

from __future__ import print_function
from obs import ObsClient, Object, Versions, DeleteObjectsRequest

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

# Enable bucket versioning
obsClient.setBucketVersioning(bucketName, 'Enabled')

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

# List versions using default parameters, will return up to 1000 objects
print('List versions using default parameters:\n')
resp = obsClient.listVersions(bucketName)

for version in resp.body.versions:
    print('\t' + version.key + ' etag[' + version.etag + '] versionId[' + version.versionId + ']')

print('\n')

print('List all the versions in way of pagination')
nextKeyMarker = None
nextVersionIdMarker = None
index = 1
pageSize = 10

while True:
    resp = obsClient.listVersions(bucketName, Versions(key_marker=nextKeyMarker, version_id_marker=nextVersionIdMarker,
                                                       max_keys=pageSize))
    print('Page:' + str(index) + '\n')
    for version in resp.body.versions:
        print('\t' + version.key + ' etag[' + version.etag + '] versionId[' + version.versionId + ']')

    if not resp.body.head.isTruncated:
        break

    nextKeyMarker = resp.body.head.nextKeyMarker
    nextVersionIdMarker = resp.body.head.nextVersionIdMarker
    index += 1
print('\n')


# List all versions group by folder

def listVersionsByPrefix(resp):
    global obsClient
    for prefix in resp.body.commonPrefixs:
        print('Folder ' + prefix.prefix + ':')
        subresp = obsClient.listVersions(bucketName, Versions(delimiter='/', prefix=prefix.prefix))
        for version in subresp.body.versions:
            print('\t' + version.key + ' etag[' + version.etag + '] versionId[' + version.versionId + ']')
        listVersionsByPrefix(subresp)


print('List all versions group by folder \n')
resp = obsClient.listVersions(bucketName, Versions(delimiter='/'))
print('Root path:')
for version in resp.body.versions:
    print('\t' + version.key + ' etag[' + version.etag + '] versionId[' + version.versionId + ']')

print(resp.body.commonPrefixs)

listVersionsByPrefix(resp)

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
