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
 This sample demonstrates how to do object-related operations
 (such as create/delete/get/copy object, do object ACL/OPTIONS)
 on OBS using the OBS SDK for Python.
"""

from __future__ import print_function
from obs import ObsClient, CorsRule, Options

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'
objectKey = 'my-obs-object-key-demo'

# Constructs a obs client instance with your account for accessing OBS
obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

bucketClient = obsClient.bucketClient(bucketName)

# Create bucket
print('Create a new bucket for demo\n')
# obsClient.createBucket(bucketName)
bucketClient.createBucket()

# Create object
# resp = obsClient.putContent(bucketName, objectKey, 'Hello OBS')
resp = bucketClient.putContent(objectKey, 'Hello OBS')
if resp.status < 300:
    print('Create object ' + objectKey + ' successfully!\n')

# Get object metadata
print('Getting object metadata')
# resp = obsClient.getObjectMetadata(bucketName, objectKey, 'Hello OBS')
resp = bucketClient.getObjectMetadata(objectKey, 'Hello OBS')
print('\t' + str(resp.header))

# Get object
print('Getting object content')
# resp = obsClient.getObject(bucketName, objectKey, loadStreamInMemory=True)
resp = bucketClient.getObject(objectKey, loadStreamInMemory=True)
print('\tobject content:%s' % resp.body.buffer)

# Copy object
print('Copying object\n')
destObjectKey = objectKey + '-back'
# resp = obsClient.copyObject(sourceBucketName=bucketName, sourceObjectKey=objectKey,
# destBucketName=bucketName, destObjectKey=destObjectKey)
resp = bucketClient.copyObject(sourceBucketName=bucketName, sourceObjectKey=objectKey, destObjectKey=destObjectKey)
if resp.status < 300:
    print('Copy object ' + destObjectKey + ' successfully!\n')

# Options object
cors1 = CorsRule(id='rule1', allowedMethod=['PUT', 'HEAD', 'GET'],
                 allowedOrigin=['http://www.a.com', 'http://www.b.com'], allowedHeader=['Authorization1'],
                 maxAgeSecond=100, exposeHeader=['x-obs-test1'])
corsList = [cors1]
# obsClient.setBucketCors(bucketName, corsList)
bucketClient.setBucketCors(corsList)

print('Options object:')
options = Options(origin='http://www.a.com', accessControlRequestMethods=['PUT'])
# resp = obsClient.optionsObject(bucketName, objectKey, options)
resp = bucketClient.optionsObject(objectKey, options)
print(resp.body)

# Put/Get object acl operations
print('Setting object ACL to public-read \n')
# obsClient.setObjectAcl(bucketName, objectKey, aclControl='public-read')
bucketClient.setObjectAcl(objectKey, aclControl='public-read')

# print('Getting object ACL ' + str(obsClient.getObjectAcl(bucketName, objectKey).body) + '\n')
print('Getting object ACL ' + str(bucketClient.getObjectAcl(objectKey).body) + '\n')
print('Setting object ACL to private \n')

print('Getting object ACL ' + str(obsClient.getObjectAcl(bucketName, objectKey).body) + '\n')

# Delete object
print('Deleting objects\n')
# obsClient.deleteObject(bucketName, objectKey)
# obsClient.deleteObject(bucketName, destObjectKey)
bucketClient.deleteObject(objectKey)
bucketClient.deleteObject(destObjectKey)
