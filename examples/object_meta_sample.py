#!/usr/bin/python
# -*- coding:utf-8 -*-

'''
 This sample demonstrates how to set/get self-defined metadata for object
 on OBS using the OBS SDK for Python.
'''

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'
objectKey = 'my-obs-object-key-demo'

from obs import *
# Constructs a obs client instance with your account for accessing OBS
obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

# Create bucket
print('Create a new bucket for demo\n')
obsClient.createBucket(bucketName)

# Setting object mime type
headers = PutObjectHeader(contentType='text/plain')

# Setting self-defined metadata
metadata = {'meta1' : 'value1', 'meta2' : 'value2'}

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
