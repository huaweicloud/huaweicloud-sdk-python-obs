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
  This sample demonstrates how to get my bucket metadata operation on OBS using the OBS SDK for Python.
"""

import traceback

from obs import ObsClient

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
        # Specify the origin (usually a domain name) of the cross-origin request.
        origin = 'http://www.a.com'
        # Specify the HTTP headers of the cross-origin request.
        requestHeaders = 'x-obs-header'
        # Obtain the bucket metadata.
        resp = obsClient.getBucketMetadata(bucketName, origin, requestHeaders)

        # If status code 2xx is returned, the API is called successfully. Otherwise, the API call fails.
        if resp.status < 300:
            print('Get Bucket Metadata Succeeded')
            print('requestId:', resp.requestId)
            print('storageClass:', resp.body.storageClass)
            print('accessContorlAllowOrigin:', resp.body.accessContorlAllowOrigin)
            print('accessContorlMaxAge:', resp.body.accessContorlMaxAge)
            print('accessContorlExposeHeaders:', resp.body.accessContorlExposeHeaders)
            print('accessContorlAllowMethods:', resp.body.accessContorlAllowMethods)
            print('accessContorlAllowHeaders:', resp.body.accessContorlAllowHeaders)
        else:
            print('Get Bucket Metadata Failed')
            print('requestId:', resp.requestId)
            print('status:', resp.status)
    except Exception as e:
        print('Get Bucket Metadata Failed')
        print(traceback.format_exc())
