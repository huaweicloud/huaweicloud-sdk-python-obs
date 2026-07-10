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
  This sample demonstrates how to create bucket with object lock on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback

from obs import ObsClient, CreateBucketHeader
import os

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# (Optional) If you use a temporary AK and SK pair and a security token to access OBS, obtain them from environment variables.
# Set server to the endpoint corresponding to the bucket. CN-Hong Kong is used here as an example. Replace it with the one in use.
server = 'https://your-endpoint'
# Specify the name of the bucket to create.
bucketName = 'your-obs-bucket'
# Specify the region where the bucket is to be created. The region must be the same as that in the endpoint passed.
location = 'your-obs-bucket-region'
# Additional header fields for creating a bucket, such as the bucket ACL being private, the storage class being Standard Access Storage, and the multi-AZ storage method.
header = CreateBucketHeader(aclControl='PRIVATE', storageClass='STANDARD')
# Extension headers for enabling object lock.
extensionHeaders = {'x-obs-bucket-object-lock-enabled': 'true'}

if __name__ == '__main__':
    # Create an obsClient instance.
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Create bucket with object lock enabled.
        resp = obsClient.createBucket(bucketName, header, location, extensionHeaders)
        if resp.status < 300:
            print('Create Bucket Succeeded')
            print('requestId:', resp.requestId)
        else:
            print('Create Bucket Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)

        # Enable versioning on the bucket.
        resp = obsClient.setBucketVersioning(bucketName, 'Enabled')
        if resp.status < 300:
            print('Enable Versioning Succeeded')
            print('requestId:', resp.requestId)
        else:
            print('Enable Versioning Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)

    except Exception as e:
        print('Create Bucket Failed')
        print(traceback.format_exc())
