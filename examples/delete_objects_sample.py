#!/usr/bin/python
# -*- coding:utf-8 -*-

'''
 This sample demonstrates how to delete objects under specified bucket
 from OBS using the OBS SDK for Python.

'''

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'

from obs import *
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
