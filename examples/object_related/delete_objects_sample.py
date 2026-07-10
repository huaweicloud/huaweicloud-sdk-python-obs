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
  This sample demonstrates how to delete objects operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback

from obs import ObsClient, DeleteObjectsRequest, Object

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'

if __name__ == '__main__':
    try:
        # Create an obsClient instance
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
        # Specify the objects to be deleted in a batch.
        object1 = Object(key='objectkey1', versionId=None)
        object2 = Object(key='objectkey2', versionId=None)

        # Specify encoding_type when the object name contains special characters.
        encoding_type = 'url'

        # Batch delete the objects.
        resp = obsClient.deleteObjects(bucketName, DeleteObjectsRequest(quiet=False, objects=[object1, object2],
                                                                        encoding_type=encoding_type))

        # If status code 2xx is returned, the API is called successfully. Otherwise, the API call fails.
        if resp.status < 300:
            print('Delete Objects Succeeded')
            print('requestId:', resp.requestId)
            if resp.body.deleted:
                index = 1
                for delete in resp.body.deleted:
                    print('delete[' + str(index) + ']')
                    print('key:', delete.key, ',deleteMarker:', delete.deleteMarker, ',deleteMarkerVersionId:',
                          delete.deleteMarkerVersionId)
                    print('versionId:', delete.versionId)
                    index += 1
            if resp.body.error:
                index = 1
                for err in resp.body.error:
                    print('err[' + str(index) + ']')
                    print('key:', err.key, ',code:', err.code, ',message:', err.message)
                    print('versionId:', err.versionId)
                    index += 1
        else:
            print('Delete Objects Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Delete Objects Failed')
        print(traceback.format_exc())