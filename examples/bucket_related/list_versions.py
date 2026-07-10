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
  This sample demonstrates how to list some or all of the object versions in a bucket operation on OBS using the OBS SDK for Python.
"""

import traceback

from obs import ObsClient
from obs import Versions

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'

if __name__ == '__main__':
    # Create an obsClient instance.
    # If you use a temporary AK and SK pair and a security token to access OBS, you must specify security_token when creating an instance.
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Specify an object prefix.
        prefix = 'test/'
        max_keys = 100
        # List object versions in a bucket.
        resp = obsClient.listVersions(bucketName, version=Versions(prefix, max_keys, encoding_type='url'))

        # If status code 2xx is returned, the API is called successfully. Otherwise, the API call fails.
        if resp.status < 300:
            print('List Versions Succeeded')
            print('requestId:', resp.requestId)
            print('name:', resp.body.head.name)
            print('prefix:', resp.body.head.prefix)
            print('maxKeys:', resp.body.head.maxKeys)
            print('isTruncated:', resp.body.head.isTruncated)
            index = 1
            for version in resp.body.versions:
                print('version [' + str(index) + ']')
                print('key:', version.key)
                print('versionId:', version.versionId)
                print('lastModified:', version.lastModified)
                print('etag:', version.etag)
                print('size:', version.size)
                print('storageClass:', version.storageClass)
                print('owner_id:', version.owner.owner_id)
                print('owner_name:', version.owner.owner_name)
                index += 1

            index = 1
            for marker in resp.body.markers:
                print('marker [' + str(index) + ']')
                print('key:', marker.key)
                print('versionId:', marker.versionId)
                print('lastModified:', marker.lastModified)
                print('owner_id:', marker.owner.owner_id)
                print('owner_name:', marker.owner.owner_name)
                index += 1
        else:
            print('List Versions Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('List Versions Failed')
        print(traceback.format_exc())
