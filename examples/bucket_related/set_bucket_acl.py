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
  This sample demonstrates how to set bucket ACL operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback

from obs import ObsClient, HeadPermission
from obs import ACL
from obs import Owner
from obs import Grantee
from obs import Grant
from obs import Group
from obs import Permission

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
        # ownerid: ID of the owner account.
        owner_id = 'ownerid'
        owner = Owner(owner_id=owner_id)
        # Specify a single user (where userid is the ID of an IAM user).
        grantee1 = Grantee(grantee_id='userid')
        # Specify all users.
        grantee2 = Grantee(group=Group.ALL_USERS)
        # Setting the read and write permissions for a specified user (userid)
        grant1 = Grant(grantee=grantee1, permission=Permission.READ)
        grant2 = Grant(grantee=grantee1, permission=Permission.WRITE)
        # Setting the public read permission for all users is risky. You can set the permission based on the actual service requirements. In this example, the public read permission is set.
        grant3 = Grant(grantee=grantee2, permission=Permission.READ)
        # Permission information object. The ACL of the bucket named examplebucket is set as follows: All users have the read permission, and the specified user (userid) has the read and write permissions.
        acl = ACL(owner=owner, grants=[grant1, grant2, grant3])
        # Set bucket ACL
        resp = obsClient.setBucketAcl(bucketName, acl)

        # If the return code is 2xx, the API is successfully called. Otherwise, the API fails to be called
        if resp.status < 300:
            print('Set Bucket Acl Succeeded')
            print('requestId:', resp.requestId)
        else:
            print('Set Bucket Acl Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
    except Exception as e:
        print('Set Bucket Acl Failed')
        print(traceback.format_exc())