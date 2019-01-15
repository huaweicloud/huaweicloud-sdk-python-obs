#!/usr/bin/python
# -*- coding:utf-8 -*-

'''
 This sample demonstrates how to create an empty folder under
 specified bucket to OBS using the OBS SDK for Python.
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
