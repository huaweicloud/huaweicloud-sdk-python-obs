#! /usr/bin/python
# -*- coding:utf-8 -*-
# Copyright 2019 Huawei Technologies Co.,Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations under the License.
#
"""
  This sample demonstrates how to copy an object from one bucket to another on OBS using the OBS SDK for Python.
"""

from __future__ import print_function


import traceback

from obs import ObsClient
from obs import CopyObjectHeader

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'

# 【Optional】If you use temporary AK/SK and SecurityToken to access OBS, it is also recommended to obtain them through environment variables.
security_token = "SecurityToken"
# server is filled with the endpoint corresponding to the bucket. This example uses China-Hong Kong, please fill in other regions according to the actual situation.
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'

if __name__ == '__main__':
    # Create an obsClient instance
    # If you use temporary AK/SK and SecurityToken to access OBS, you need to specify the securityToken value through the security_token parameter when creating an instance.
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Additional header fields for copying an object
        headers = CopyObjectHeader()
        # If metadata is set, you need to specify the directive in the headers as 'REPLACE'
        headers.directive = 'REPLACE'
        # if_match, if the ETag value of the source object is the same as this parameter value, the copy is performed, otherwise an error code is returned
        headers.if_match = '8f4e******************ba8c'
        # Custom metadata for the target object
        metadata = {"meta1": "value1"}
        # Specify the source bucket
        sourceBucketName = "sourcebucket"
        # Specify the source object
        sourceObjectKey = "sourceobjectkey"
        # Specify the destination bucket
        destBucketName = "destbucket"
        # Specify the destination object name
        destObjectKey = "destobjectkey"
        # Copy an object
        resp = obsClient.copyObject(sourceBucketName, sourceObjectKey, destBucketName, destObjectKey, metadata, headers)

        # When the return code is 2xx, the API call is successful, otherwise the API call fails
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