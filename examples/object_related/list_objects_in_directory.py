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
  This sample demonstrates how to list objects in a specific directory within a bucket on OBS using the OBS SDK for Python.
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
# Specify the name of the bucket to list objects from.
bucketName = 'your-obs-bucket'
# Specify the prefix to list objects from.
prefix = 'your-prefix'
# Specify the maximum number of objects to list in a single request.
max_keys = 1000

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        mark = None
        total_size = 0
        o_num = 1
        f_num = 1

        while True:
            resp = obsClient.listObjects(bucketName, marker=mark, prefix=prefix, encoding_type='url')

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
        print('o_num:', o_num)
        print('f_num:', f_num)
    except Exception as e:
        print('List Objects Failed')
        print(traceback.format_exc())