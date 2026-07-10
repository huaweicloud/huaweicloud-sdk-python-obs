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
  This sample demonstrates how to list multipart uploads operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function
import os
import traceback

from obs import ObsClient, ListMultipartUploadsRequest

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'

# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'

# Specify the prefix that the object names in the multipart uploads to be listed must contain.
prefix = 'prefix'
# Specify the maximum number (10 as an example) of returned multipart uploads. The value ranges from 1 to 1,000. If the value is not in this range, 1,000 is returned by default.
max_uploads = 10

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Specify request parameters for listing multipart uploads
        multipart = ListMultipartUploadsRequest(prefix=prefix, max_uploads=max_uploads)

        # List multipart uploads in a bucket
        resp = obsClient.listMultipartUploads(bucketName, multipart, encoding_type='url')

        # If the return code is 2xx, the API is successfully called. Otherwise, the API fails to be called
        if resp.status < 300:
            print('List Multipart Uploads Succeeded')
            print('requestId:', resp.requestId)
            print('bucket:', resp.body.bucket)
            print('prefix:', resp.body.prefix)
            print('maxUploads:', resp.body.maxUploads)
            print('isTruncated:', resp.body.isTruncated)
            index = 1
            for upload in resp.body.upload:
                print('upload [' + str(index) + ']')
                print('key:', upload.key)
                print('uploadId:', upload.uploadId)
                print('storageClass:', upload.storageClass)
                print('initiated:', upload.initiated)
                print('owner_id:', upload.owner.owner_id)
                print('owner_name:', upload.owner.owner_name)
                index += 1
        else:
            print('List Multipart Uploads Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('List Multipart Uploads Failed')
        print(traceback.format_exc())