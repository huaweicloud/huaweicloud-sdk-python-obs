#!/usr/bin/python
# -*- coding:utf-8 -*-

'''
 This sample demonstrates how to download an object
 from OBS in different ways using the OBS SDK for Python.
'''

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'
objectKey = 'my-obs-object-key-demo'
localFile = '/temp/test.txt'

import os
from obs import *

def createSampleFile(sampleFilePath):
    if not os.path.exists(sampleFilePath):
        _dir = os.path.dirname(sampleFilePath)
        if not os.path.exists(_dir):
            os.makedirs(_dir, mode=0o755)
        import uuid
        with open(sampleFilePath, 'w') as f:
            f.write(str(uuid.uuid1()) + '\n')
            f.write(str(uuid.uuid4()) + '\n')
    return sampleFilePath

# Constructs a obs client instance with your account for accessing OBS
obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

# Create bucket
print('Create a new bucket for demo\n')
obsClient.createBucket(bucketName)

sampleFilePath = '/temp/test.txt'
# Upload an object to your bucket
print('Uploading a new object to OBS from a file\n')
obsClient.putFile(bucketName, objectKey, createSampleFile(sampleFilePath))

print('Downloading an object as a socket stream\n')

# Download the object as a socket stream and display it directly
resp = obsClient.getObject(bucketName, objectKey, downloadPath=None)
if resp.status < 300:
    response = resp.body.response
    chunk_size = 65536
    if response is not None:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            print(chunk)
        response.close()

# Download the object to a file
print('Downloading an object to :' + localFile + '\n')
obsClient.getObject(bucketName, objectKey, downloadPath=localFile)

# Download the object as a stream object
print('Downloading an object as a stream object')
resp = obsClient.getObject(bucketName, objectKey, loadStreamInMemory=True)
print('stream object content:')
print(resp.body.buffer)


print('Deleting object ' + objectKey + '\n')
obsClient.deleteObject(bucketName, objectKey)

if os.path.exists(sampleFilePath):
    os.remove(sampleFilePath)
