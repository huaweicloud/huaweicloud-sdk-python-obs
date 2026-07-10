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
  This sample demonstrates how to copy object operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback

from obs import ObsClient, CopyObjectHeader

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
sourceBucketName = 'your-source-bucket'
sourceObjectKey = 'your-source-object-key'
destBucketName = 'your-dest-bucket'
destObjectKey = 'your-dest-object-key'

if __name__ == '__main__':
    try:
        # Create an obsClient instance
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
        # Specify additional headers of the request for copying an object.
        headers = CopyObjectHeader()
        # Set directive of headers to REPLACE when custom metadata is configured.
        headers.directive = 'REPLACE'
        # Specify the value of if_match. If the ETag of the source object is the same as the one specified by this parameter, the source object is copied. Otherwise, an error code is returned.
        headers.if_match = '8f4e******************ba8c'
        # Specify custom metadata of the target object.
        metadata = {'meta': 'value'}

        # Copy the object.
        resp = obsClient.copyObject(sourceBucketName, sourceObjectKey, destBucketName, destObjectKey,
                                    metadata, headers)

        # If status code 2xx is returned, the API is called successfully. Otherwise, the API call fails.
        if resp.status < 300:
            print('Copy Object Succeeded')
            print('requestId:', resp.requestId)
            print('etag:', resp.body.etag)
            print('lastModified:', resp.body.lastModified)
            print('versionId:', resp.body.versionId)
            print('copySourceVersionId:', resp.body.copySourceVersionId)
        else:
            print('Copy Object Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Copy Object Failed')
        print(traceback.format_exc())