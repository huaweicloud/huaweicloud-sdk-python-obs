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
  This sample demonstrates how to list buckets and check public read permissions on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import os
import traceback
from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = os.getenv("HUAWEICLOUD_SDK_AK")
SK = os.getenv("HUAWEICLOUD_SDK_SK")
# Set server to the endpoint corresponding to the bucket
server = "https://obs.cn-east-3.myhuaweicloud.com"

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(
        access_key_id=AK,
        secret_access_key=SK,
        server=server
    )

    try:
        # List all buckets
        resp = obsClient.listBuckets(True)
        bucket_names = []  # A list for storing bucket names.


        if resp.status < 300:
            print('List Buckets Succeeded')
            # Iterate through all buckets and store the bucket names in the list.
            for bucket in resp.body.buckets:
                bucket_names.append(bucket.name)
                print(bucket.name)  # Output only the bucket names.
        else:
            print('List Buckets Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)

        # Get ACL information (if the bucket exists).
        if bucket_names:
            acls = {}
            for bucket_name in bucket_names:
                try:
                    print(f"\n正在获取桶 {bucket_name} 的ACL信息...")
                    resp = obsClient.getBucketAcl(bucket_name)

                    if resp.status < 300:
                        print('Get Bucket Acl Succeeded')

                        # Store the ACL information of the current bucket.
                        bucket_acls = {
                            "request_id": resp.requestId,
                            "owner": {
                                "id": resp.body.owner.owner_id,
                                "name": resp.body.owner.owner_name
                            },
                            "grants": []
                        }

                        # Process each grant.
                        for grant in resp.body.grants:
                            grant_info = {
                                "grantee_id": grant.grantee.grantee_id,
                                "grantee_name": grant.grantee.grantee_name,
                                "group": grant.grantee.group,
                                "permission": grant.permission
                            }
                            bucket_acls["grants"].append(grant_info)
                            print(grant_info)  # Print the grant information.

                        acls[bucket_name] = bucket_acls

                    else:
                        print('Get Bucket Acl Failed')
                        print('requestId:', resp.requestId)
                        print('errorCode:', resp.errorCode)
                        print('errorMessage:', resp.errorMessage)

                except Exception as e:
                    print(f'获取桶 {bucket_name} ACL失败')
                    print('Error:', str(e))
                    print('Traceback:', traceback.format_exc())

            # Check the ACL information to find buckets with public read permissions.
            public_buckets = []
            for bucket_name, acl_info in acls.items():
                for grant in acl_info["grants"]:
                    if grant["group"] == "Everyone" and grant["permission"] == "READ":
                        public_buckets.append(bucket_name)
                        print(f"发现public读权限的桶: {bucket_name}")

            print("所有public读权限的桶:", public_buckets)

    except Exception as e:
        print('Operation Failed')
        print(traceback.format_exc())