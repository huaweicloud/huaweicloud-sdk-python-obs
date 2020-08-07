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
 This sample demonstrates how to multipart upload an object concurrently by copy mode
 to OBS using the OBS SDK for Python.
"""

from __future__ import print_function
import multiprocessing
import os
import platform
import threading
from obs import ObsClient, CompletePart, CompleteMultipartUploadRequest

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'
sourceBucketName = bucketName
sourceObjectKey = 'my-obs-object-key-demo'
objectKey = sourceObjectKey + '-back'
sampleFilePath = '*** Provide your local file path ***'
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


def doCopyPart(partETags, bucketName, objectKey, partNumber, uploadId, copySource, copySourceRange):
    if IS_WINDOWS:
        global obsClient
    else:
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
    resp = obsClient.copyPart(bucketName=bucketName, objectKey=objectKey, partNumber=partNumber, uploadId=uploadId,
                              copySource=copySource, copySourceRange=copySourceRange)
    if resp.status < 300:
        partETags[partNumber] = resp.body.etag
        print('Part#' + str(partNumber) + 'done\n')
    else:
        print('\tPart#' + str(partNumber) + ' failed\n')


if __name__ == '__main__':
    # Constructs a obs client instance with your account for accessing OBS
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
    # Create bucket
    print('Create a new bucket for demo\n')
    resp = obsClient.createBucket(bucketName)
    if resp.status >= 300:
        raise Exception('Create Bucket failed')

    # # Upload an object to your source bucket
    print('Uploading a new object to OBS from a file\n')
    resp = obsClient.putFile(sourceBucketName, sourceObjectKey, sampleFilePath)
    if resp.status >= 300:
        raise Exception('putFile failed')

    # Claim a upload id firstly
    resp = obsClient.initiateMultipartUpload(bucketName, objectKey)
    if resp.status >= 300:
        raise Exception('initiateMultipartUpload failed')

    uploadId = resp.body.uploadId
    print('Claiming a new upload id ' + uploadId + '\n')

    # 5MB
    partSize = 5 * 1024 * 1024
    resp = obsClient.getObjectMetadata(sourceBucketName, sourceObjectKey)
    if resp.status >= 300:
        raise Exception('getObjectMetadata failed')

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

        p = proc(target=doCopyPart, args=(
            partETags, bucketName, objectKey, i + 1, uploadId, sourceBucketName + '/' + sourceObjectKey,
            str(rangeStart) + '-' + str(rangeEnd)))
        p.daemon = True
        processes.append(p)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    if len(partETags) != partCount:
        raise Exception('copyParts fail due to some parts are not finished yet')

    # View all parts uploaded recently
    print('Listing all parts......')
    resp = obsClient.listParts(bucketName, objectKey, uploadId)
    if resp.status < 300:
        for part in resp.body.parts:
            print('\tPart#' + str(part.partNumber) + ', ETag=' + part.etag)
        print('\n')
    else:
        raise Exception('listParts failed')

    # Complete to upload multiparts

    partETags = sorted(partETags.items(), key=lambda d: d[0])

    parts = []
    for key, value in partETags:
        parts.append(CompletePart(partNum=key, etag=value))

    print('Completing to upload multiparts\n')
    resp = obsClient.completeMultipartUpload(bucketName, objectKey, uploadId, CompleteMultipartUploadRequest(parts))
    if resp.status < 300:
        print('Succeed to complete multiparts into an object named ' + objectKey + '\n')
    else:
        print('errorCode:', resp.errorCode)
        print('errorMessage:', resp.errorMessage)
        raise Exception('completeMultipartUpload failed')
