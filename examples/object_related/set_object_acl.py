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
  This sample demonstrates how to set object ACL operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback

from obs import ObsClient, ACL, Owner, Grant, Permission, Grantee

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
objectKey = 'your-object-key'

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Get the bucket's ACL to verify the owner_id and grantee_id.
        bucket_acl_resp = obsClient.getBucketAcl(bucketName)
        if bucket_acl_resp.status < 300:
            owner_id = bucket_acl_resp.body.owner.owner_id
            grantee_id = owner_id  # You can use other valid user IDs.
        else:
            print('Get Bucket Acl Failed')
            print('requestId:', bucket_acl_resp.requestId)
            print('errorCode:', bucket_acl_resp.errorCode)
            print('errorMessage:', bucket_acl_resp.errorMessage)
            exit(1)

        # Set the permission for a single user (ID is grantee_id) to read and write the object
        grantee = Grantee(grantee_id=grantee_id)
        print('grantee:', grantee)
        print('grantee_id:', grantee_id)
        grant0 = Grant(grantee=grantee, permission=Permission.READ)
        grant1 = Grant(grantee=grantee, permission=Permission.WRITE)
        # Set ACL
        acl = ACL(owner=Owner(owner_id=owner_id), grants=[grant0, grant1])

        # Set object ACL
        resp = obsClient.setObjectAcl(bucketName, objectKey, acl)

        # If the return code is 2xx, the API is successfully called. Otherwise, the API fails to be called
        if resp.status < 300:
            print('Set Object Acl Succeeded')
            print('requestId:', resp.requestId)
        else:
            print('Set Object Acl Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Set Object Acl Failed')
        print(traceback.format_exc())
