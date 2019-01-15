#!/usr/bin/python
# -*- coding:utf-8 -*-

'''
 This sample demonstrates how to multipart upload an object concurrently
 from OBS using the OBS SDK for Python.
'''

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'
objectKey = 'my-obs-object-key-demo'
sampleFilePath = '*** Provide your local file path ***'

import platform, os, threading, multiprocessing
IS_WINDOWS = platform.system() == 'Windows' or os.name == 'nt'

def createSampleFile(sampleFilePath):
    if not os.path.exists(sampleFilePath):
        _dir = os.path.dirname(sampleFilePath)
        if not os.path.exists(_dir):
            os.makedirs(_dir, mode=0o755)
        import uuid
        index = 1000000
        with open(sampleFilePath, 'w') as f:
            while index >= 0:
                f.write(str(uuid.uuid1()) + '\n')
                f.write(str(uuid.uuid4()) + '\n')
                index -= 1
    return sampleFilePath

from obs import *

def doUploadPart(partETags, bucketName, objectKey, partNumber, uploadId, filePath, partSize, offset):
    if IS_WINDOWS:
        global obsClient
    else:
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
    resp = obsClient.uploadPart(bucketName, objectKey, partNumber, uploadId, content=filePath, isFile=True, partSize=partSize, offset=offset)
    if resp.status < 300:
        partETags[partNumber] = resp.body.etag
        print('Part#', partNumber, 'done\n')

if __name__ == '__main__':
    # Constructs a obs client instance with your account for accessing OBS
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
    # Create bucket
    print('Create a new bucket for demo\n')
    obsClient.createBucket(bucketName)

    # Claim a upload id firstly
    resp = obsClient.initiateMultipartUpload(bucketName, objectKey)
    uploadId = resp.body.uploadId
    print('Claiming a new upload id ' + uploadId + '\n')

    # 5MB
    partSize = 5 * 1024 * 1024

    #createSampleFile(sampleFilePath)

    fileLength = os.path.getsize(sampleFilePath)

    partCount = int(fileLength / partSize) if (fileLength % partSize == 0) else int(fileLength / partSize) + 1

    if partCount > 10000:
        raise Exception('Total parts count should not exceed 10000')

    print('Total parts count ' + str(partCount) + '\n')


    # Upload multiparts to your bucket
    print('Begin to upload multiparts to OBS from a file\n')

    proc = threading.Thread if IS_WINDOWS else multiprocessing.Process
    partETags = dict() if IS_WINDOWS else multiprocessing.Manager().dict()

    processes = []

    for i in range(partCount):
        offset = i * partSize
        currPartSize = (fileLength - offset) if i + 1 == partCount else partSize
        p = proc(target=doUploadPart, args=(partETags, bucketName, objectKey, i + 1, uploadId, sampleFilePath, currPartSize, offset))
        p.daemon = True
        processes.append(p)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    if len(partETags) != partCount:
        raise Exception('Upload multiparts fail due to some parts are not finished yet')

    # View all parts uploaded recently
    print('Listing all parts......')
    resp = obsClient.listParts(bucketName, objectKey, uploadId)
    for part in resp.body.parts:
        print('\tPart#' + str(part.partNumber) + ', ETag=' + part.etag)
    print('\n')

    # Complete to upload multiparts
    
    partETags = sorted(partETags.items(), key=lambda d: d[0])

    parts = []
    for key, value in partETags:
        parts.append(CompletePart(partNum=key, etag=value))

    print('Completing to upload multiparts\n')
    resp = obsClient.completeMultipartUpload(bucketName, objectKey, uploadId, CompleteMultipartUploadRequest(parts))
    
    if resp.status < 300:
        print('Succeed to complete multiparts into an object named ' + objectKey + '\n')
    
