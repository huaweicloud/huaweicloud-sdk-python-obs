#!/usr/bin/python
# -*- coding:utf-8 -*-

'''
 This sample demonstrates how to multipart upload an object concurrently by copy mode
 to OBS using the OBS SDK for Python.
'''

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'
sourceBucketName = bucketName
sourceObjectKey = 'my-obs-object-key-demo'
objectKey = sourceObjectKey + '-back'
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

def doCopyPart(partETags, bucketName, objectKey, partNumber, uploadId, copySource, copySourceRange):
    if IS_WINDOWS:
        global obsClient
    else:
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
    resp = obsClient.copyPart(bucketName=bucketName, objectKey=objectKey, partNumber=partNumber, uploadId=uploadId, copySource=copySource, copySourceRange=copySourceRange)
    if resp.status < 300:
        partETags[partNumber] = resp.body.etag
        print('Part#', partNumber, 'done\n')

if __name__ == '__main__':
    # Constructs a obs client instance with your account for accessing OBS
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
    # Create bucket
    print('Create a new bucket for demo\n')
    obsClient.createBucket(bucketName)

    # # Upload an object to your source bucket
    print('Uploading a new object to OBS from a file\n')
    obsClient.putFile(sourceBucketName, sourceObjectKey, sampleFilePath)

    # Claim a upload id firstly
    resp = obsClient.initiateMultipartUpload(bucketName, objectKey)
    uploadId = resp.body.uploadId
    print('Claiming a new upload id ' + uploadId + '\n')

    # 5MB
    partSize = 5 * 1024 * 1024
    resp = obsClient.getObjectMetadata(sourceBucketName, sourceObjectKey)
    header = dict(resp.header)
    objectSize = int(header.get('content-length'))

    partCount = int(objectSize / partSize) if (objectSize % partSize == 0) else int(objectSize / partSize) + 1

    if partCount > 10000:
        raise Exception('Total parts count should not exceed 10000')

    print('Total parts count ' + str(partCount) + '\n')

    # Upload multiparts by copy mode
    print('Begin to upload multiparts to OBS by copy mode \n')
    
    proc = threading.Thread if IS_WINDOWS else multiprocessing.Process

    partETags = dict() if IS_WINDOWS else multiprocessing.Manager().dict()

    processes = []

    for i in range(partCount):
        rangeStart = i * partSize
        rangeEnd = objectSize - 1 if (i + 1 == partCount) else rangeStart + partSize - 1

        p = proc(target=doCopyPart, args=(partETags, bucketName, objectKey, i+1, uploadId, sourceBucketName + '/' + sourceObjectKey, str(rangeStart) + '-' + str(rangeEnd)))
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
