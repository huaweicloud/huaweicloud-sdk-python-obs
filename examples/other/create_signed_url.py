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
  This sample demonstrates how to create signed URLs for various operations on OBS using the OBS SDK for Python.
"""

from __future__ import print_function
import os
import traceback
import base64

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'

# Set server to the endpoint corresponding to the bucket.
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
objectKey = 'your-object-name'

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Create a signed URL for creating a bucket
        res1 = obsClient.createSignedUrl(method='PUT', bucketName=bucketName, expires=3600)
        print('signedUrl:', res1.signedUrl)
        print('actualSignedRequestHeaders:', res1.actualSignedRequestHeaders)

        # Create a signed URL for uploading an object
        res2 = obsClient.createSignedUrl(method='PUT', bucketName=bucketName, objectKey=objectKey, expires=3600,
                                        headers={'Content-Type': 'text/plain'})
        print('signedUrl:', res2.signedUrl)
        print('actualSignedRequestHeaders:', res2.actualSignedRequestHeaders)

        # Create a signed URL for setting an object ACL
        res3 = obsClient.createSignedUrl(method='PUT', bucketName=bucketName, objectKey=objectKey, specialParam='acl',
                                        expires=3600, headers={'x-obs-acl': 'private'})
        print('signedUrl:', res3.signedUrl)
        print('actualSignedRequestHeaders:', res3.actualSignedRequestHeaders)

        # Create a signed URL for downloading an object
        res4 = obsClient.createSignedUrl(method='GET', bucketName=bucketName, objectKey=objectKey, expires=3600)
        print('signedUrl:', res4.signedUrl)
        print('actualSignedRequestHeaders:', res4.actualSignedRequestHeaders)

        # Create a signed URL for deleting an object
        res5 = obsClient.createSignedUrl(method='DELETE', bucketName=bucketName, objectKey=objectKey, expires=3600)
        print('signedUrl:', res5.signedUrl)
        print('actualSignedRequestHeaders:', res5.actualSignedRequestHeaders)

        # Create a signed URL for deleting a bucket
        res6 = obsClient.createSignedUrl(method='DELETE', bucketName=bucketName, expires=3600)
        print('signedUrl:', res6.signedUrl)
        print('actualSignedRequestHeaders:', res6.actualSignedRequestHeaders)

        # Create a signed URL for initiating a multipart task
        res7 = obsClient.createSignedUrl(method='POST', bucketName=bucketName, objectKey=objectKey,
                                        specialParam='uploads', expires=3600)
        print('signedUrl:', res7.signedUrl)
        print('actualSignedRequestHeaders:', res7.actualSignedRequestHeaders)

        # Create a signed URL for uploading a part
        res8 = obsClient.createSignedUrl(method='PUT', bucketName=bucketName, objectKey=objectKey, expires=3600,
                                        queryParams={'partNumber': '1', 'uploadId': '00000*****'})
        print('signedUrl:', res8.signedUrl)
        print('actualSignedRequestHeaders:', res8.actualSignedRequestHeaders)

        # Create a signed URL for assembling parts
        res9 = obsClient.createSignedUrl(method='POST', bucketName=bucketName, objectKey=objectKey, expires=3600,
                                        queryParams={'uploadId': '00000*****'})
        print('signedUrl:', res9.signedUrl)
        print('actualSignedRequestHeaders:', res9.actualSignedRequestHeaders)

        # Create a signed URL for image persistency
        # Name of the bucket that stores the source object
        sourceBucketName = bucketName
        # Source object name before the processing
        sourceObjectKey = objectKey

        # Name of the object after processing
        targetObjectName = "save.png"
        # (Optional) Name of the bucket that stores the new object
        targetBucketName = "saveBucketName"
        queryParams = {}
        queryParams["x-image-process"] = "image/resize,w_100"
        queryParams["x-image-save-object"] = base64.b64encode(targetObjectName.encode("utf-8")).decode()
        # Optional parameter
        queryParams["x-image-save-bucket"] = base64.b64encode(targetBucketName.encode("utf-8")).decode()

        res10 = obsClient.createSignedUrl(method='GET', bucketName=sourceBucketName, objectKey=sourceObjectKey,
                                        queryParams=queryParams, expires=3600)
        print('signedUrl:', res10.signedUrl)
        print('actualSignedRequestHeaders:', res10.actualSignedRequestHeaders)
    except Exception as e:
        print(traceback.format_exc())