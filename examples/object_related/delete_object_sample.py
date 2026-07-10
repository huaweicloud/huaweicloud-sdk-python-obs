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
  This sample demonstrates how to delete object operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback

from obs import ObsClient

# Obtain an AK and SK pair using environment variables (recommended) or import it in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
objectKey = 'your-object-key'

if __name__ == '__main__':
    try:
        # Create an obsClient instance
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
        # Delete the object.
        resp = obsClient.deleteObject(bucketName, objectKey)

        # If the return code is 2xx, the API is successfully called. Otherwise, the API fails to be called. If a nonexistent version ID is used to delete a versioned object (that is, the requested object does not exist), a success message is still returned.
        if resp.status <  300:
            print('Delete Object Succeeded')
            print('requestId:', resp.requestId)
            print('deleteMarker:', resp.body.deleteMarker)
            print('versionId:', resp.body.versionId)
        else:
            print('Delete Object Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Delete Object Failed')
        print(traceback.format_exc())