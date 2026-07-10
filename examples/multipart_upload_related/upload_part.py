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
  This sample demonstrates how to upload part operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function
import os
import traceback

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'

# Set server to the endpoint corresponding to the bucket. CN-Hong Kong is used here as an example. Replace it with the one in use.
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
# Specify the name of the object to be uploaded to the bucket.
objectKey = 'your-object-name'
# Specify the part number, which ranges from 1 to 10,000
partNumber = "your-partNumber"
# Specify the ID of the multipart upload.
uploadId = "your-uploadid"
# Specify the content of the part to be uploaded as a string or readable object.
object = 'Hello OBS'
# Specify whether object indicates the file path. The default value is False.
isFile = False
# Specify the start offset (in bytes) of a part in the source file. The default value is 0.
offset = 0
# Specify the size (in bytes) of a part in the source file. The default value is the file size minus offset.
partSize = 9 * 1024 * 1024
# Specify whether to automatically calculate the MD5 value of the data to be uploaded. The default value is False.
isAttachMd5 = True

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Upload the part to a specified bucket using the multipart upload ID.
        resp = obsClient.uploadPart(bucketName, objectKey, partNumber, uploadId, object, isFile, partSize,
                                    offset, isAttachMd5=isAttachMd5)

        # If the return code is 2xx, the API is successfully called. Otherwise, the API fails to be called
        if resp.status < 300:
            print('Upload Part Succeeded')
            print('requestId:', resp.requestId)
            print('etag:', resp.body.etag)
        else:
            print('Upload Part Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Upload Part Failed')
        print(traceback.format_exc())