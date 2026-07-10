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
  This sample demonstrates how to create post signature for browser-based upload on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
# Specify an object name (the name displayed after the file is uploaded to the bucket).
objectKey = 'your-object-key'

if __name__ == '__main__':
    try:
        # Create an obsClient instance
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
        # Configure the validity period (in seconds) for a browser-based upload request. 3600 is used as an example.
        expires = 3600
        # Specify parameters for a browser-based upload except key, policy, and signature. In this example, x-obs-acl is set to private and content-type is set to text/plain.
        formParams = {'x-obs-acl': 'private', 'content-type': 'text/plain'}
        # Create parameters for a browser-based upload.
        resp = obsClient.createPostSignature(bucketName, objectKey, expires, formParams)

        print('originPolicy:', resp.originPolicy)
        print('policy:', resp.policy)
        print('signature:', resp.signature)
    except Exception as e:
        print(traceback.format_exc())