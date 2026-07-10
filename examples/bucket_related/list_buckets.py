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
  This sample demonstrates how to list all my buckets operation on OBS using the OBS SDK for Python.
"""

import traceback

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'

if __name__ == "__main__":
    # Create an obsClient instance.
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
    try:
        # List buckets and set isQueryLocation to True to query the bucket region.
        resp = obsClient.listBuckets(True)
        # If status code 2xx is returned, the API is called successfully. Otherwise, the API call fails.
        if resp.status < 300:
            print('List Buckets Succeeded')
            print('requestId:', resp.requestId)
            print('name:', resp.body.owner.owner_id)
            print('create_date:', resp.body.owner.owner_name)
            index = 1
            for bucket in resp.body.buckets:
                print('bucket [' + str(index) + ']')
                print('name:', bucket.name)
                print('create_date:', bucket.create_date)
                print('location:', bucket.location)
                index += 1
        else:
            print('List Buckets Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('List Buckets Failed')
        print(traceback.format_exc())
