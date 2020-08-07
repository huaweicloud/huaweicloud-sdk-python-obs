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
 This sample demonstrates how to download an object concurrently
 from OBS using the OBS SDK for Python.
"""

from __future__ import print_function
import multiprocessing
import os
import platform
import threading
from obs import ObsClient, GetObjectHeader

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'
objectKey = 'my-obs-object-key-demo'
localFilePath = '/temp/' + objectKey
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


def doGetObject(lock, completedBlocks, bucketName, objectKey, startPos, endPos, i):
    if IS_WINDOWS:
        global obsClient
    else:
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
    resp = obsClient.getObject(bucketName, objectKey, headers=GetObjectHeader(range='%d-%d' % (startPos, endPos)))
    if resp.status < 300:
        response = resp.body.response
        chunk_size = 65536
        if response is not None:
            with open(localFilePath, 'rb+') as f:
                f.seek(startPos, 0)
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                response.close()
        print('Part#' + str(i + 1) + 'done\n')
        with lock:
            completedBlocks.value += 1
    else:
        print('\tPart#' + str(i + 1) + ' failed\n')


if __name__ == '__main__':
    # Constructs a obs client instance with your account for accessing OBS
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
    # Create bucket
    print('Create a new bucket to upload file\n')
    resp = obsClient.createBucket(bucketName)
    if resp.status >= 300:
        raise Exception('Create Bucket failed')

    # Upload an object to your bucket
    print('Uploading a new object to OBS from a file\n')
    resp = obsClient.putFile(bucketName, objectKey, sampleFilePath)
    if resp.status >= 300:
        raise Exception('putFile failed')

    # Get size of the object
    resp = obsClient.getObjectMetadata(bucketName, objectKey)
    if resp.status >= 300:
        raise Exception('getObjectMetadata failed')

    header = dict(resp.header)
    objectSize = int(header.get('content-length'))

    print('Object size ' + str(objectSize) + '\n')

    # Calculate how many blocks to be divided
    # 5MB
    blockSize = 5 * 1024 * 1024
    blockCount = int(objectSize / blockSize)
    if objectSize % blockSize != 0:
        blockCount += 1

    print('Total blocks count ' + str(blockCount) + '\n')

    # Download the object concurrently
    print('Start to download ' + objectKey + '\n')

    if os.path.exists(localFilePath):
        os.remove(localFilePath)

    lock = threading.Lock() if IS_WINDOWS else multiprocessing.Lock()
    proc = threading.Thread if IS_WINDOWS else multiprocessing.Process

    class Temp(object):
        pass

    completedBlocks = Temp() if IS_WINDOWS else multiprocessing.Value('i', 0)

    if IS_WINDOWS:
        completedBlocks.value = 0

    processes = []

    with open(localFilePath, 'wb') as f:
        pass

    for i in range(blockCount):
        startPos = i * blockSize
        endPos = objectSize - 1 if (i + 1) == blockCount else ((i + 1) * blockSize - 1)
        p = proc(target=doGetObject, args=(lock, completedBlocks, bucketName, objectKey, startPos, endPos, i))
        p.daemon = True
        processes.append(p)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    if completedBlocks.value != blockCount:
        raise Exception('Download fails due to some blocks are not finished yet')

    print('Succeed to download object ' + objectKey + '\n')

    print('Deleting object ' + objectKey + '\n')
    resp = obsClient.deleteObject(bucketName, objectKey)
    if resp.status < 300:
        print('Deleting object ' + objectKey + ' Succeed\n')
    else:
        raise Exception('Deleting object failed')
