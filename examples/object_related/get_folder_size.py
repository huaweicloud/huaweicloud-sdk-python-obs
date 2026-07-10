#!/usr/bin/python
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
  This example shows how to use the Python SDK to obtain the size of a file.
"""

from __future__ import print_function
import os
import traceback

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Specify the prefix that the object names in the list must contain
        prefix = 'test/'
        # Specify the maximum number (1000 as an example) of returned objects. The value ranges from 1 to 1,000. If the value is not in this range, 1,000 is returned by default.
        max_keys = 1000
        mark = None
        total_size = 0
        # Initialize object count
        o_num = 1
        # Initialize directory count
        f_num = 1

        while True:
            resp = obsClient.listObjects(bucketName, marker=mark, prefix=prefix, encoding_type='url')

            # If the return code is 2xx, the API is successfully called. Otherwise, the API fails to be called
            if resp.status < 300:
                print('requestId:', resp.requestId)
                print('is_truncated:', resp.body.is_truncated)
                for content in resp.body.contents:
                    print('key:', content.key)
                    print('size:', content.size)
                    total_size += content.size
                    if content.key.endswith("/"):
                        print('folder [' + str(f_num) + ']')
                        f_num += 1
                    else:
                        print('object [' + str(o_num) + ']')
                        o_num += 1
                if resp.body.is_truncated is True:
                    mark = resp.body.next_marker
                else:
                    break
            else:
                print('errorCode:', resp.errorCode)
                print('errorMessage:', resp.errorMessage)

        print('total_size:', total_size)
        print("o_num:", o_num)
        print("f_num:", f_num)
    except Exception as e:
        print('List Objects Failed')
        print(traceback.format_exc())