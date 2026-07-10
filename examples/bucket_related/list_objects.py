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
  This sample demonstrates how to list all objects in bucket operation on OBS using the OBS SDK for Python.
"""

from obs import ObsClient

import traceback

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
        # Specify the maximum number of objects to be listed at a time. 100 is used as an example.
        max_keys = 100
        # List objects in the bucket.
        resp = obsClient.listObjects(bucketName, prefix, max_keys=max_keys, encoding_type='url')

        # If status code 2xx is returned, the API is called successfully. Otherwise, the API call fails.
        if resp.status < 300:
            print('List Objects Succeeded')
            print('requestId:', resp.requestId)
            print('name:', resp.body.name)
            print('prefix:', resp.body.prefix)
            print('max_keys:', resp.body.max_keys)
            print('is_truncated:', resp.body.is_truncated)
            index = 1
            for content in resp.body.contents:
                print('object [' + str(index) + ']')
                print('key:', content.key)
                print('lastModified:', content.lastModified)
                print('etag:', content.etag)
                print('size:', content.size)
                print('storageClass:', content.storageClass)
                print('owner_id:', content.owner.owner_id)
                print('owner_name:', content.owner.owner_name)
                index += 1
        else:
            print('List Objects Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('List Objects Failed')
        print(traceback.format_exc())