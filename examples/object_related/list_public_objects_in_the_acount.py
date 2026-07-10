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
  This sample demonstrates how to list public read objects in a bucket using the OBS SDK for Python.
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
bucketName = 'your-obs-bucket'

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK,
                          secret_access_key=SK,
                          server=server)

    try:
        # List all buckets
        resp = obsClient.listBuckets(True)
        bucket_names = []  # A list for storing bucket names.

        if resp.status < 300:
            print('List Buckets Succeeded')
            # Iterate through all buckets and store the bucket names in a list.
            for bucket in resp.body.buckets:
                bucket_names.append(bucket.name)
                print(bucket.name)  # Output only the bucket names.
        else:
            print('List Buckets Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)

        # Store all objects with public read permissions.
        public_objects = []

        # Get ACL information (if the bucket exists).
        if bucket_names:
            for bucket_name in bucket_names:
                try:
                    print(f"\nRetrieving the object list for the bucket {bucket_name}...")
                    max_num = 1000
                    mark = None
                    index = 1
                    while True:
                        resp = obsClient.listObjects(bucket_name, marker=mark, max_keys=max_num, encoding_type='url')
                        if resp.status < 300:
                            print('name:', resp.body.name)
                            for content in resp.body.contents:
                                print('object [' + str(index) + ']')
                                print('key:', content.key)
                                print('size:', content.size)
                                print('storageClass:', content.storageClass)

                                # Get object ACL.
                                try:
                                    print(f"\nRetrieving ACL information for the object {content.key}...")
                                    acl_resp = obsClient.getObjectAcl(bucket_name, content.key)
                                    if acl_resp.status < 300:
                                        print('Get Object Acl Succeeded')

                                        for grant in acl_resp.body.grants:
                                            print('grant [' + str(index) + ']')
                                            print('grantee_id:', grant.grantee.grantee_id)
                                            print('grantee_name:', grant.grantee.grantee_name)
                                            print('group:', grant.grantee.group)
                                            print('permission:', grant.permission)

                                            # Check if it has public read permission.
                                            if grant.grantee.group == "Everyone" and grant.permission == "READ":
                                                public_objects.append(f"{bucket_name}/{content.key}")
                                                print(f"Found an object with public read permission: {bucket_name}/{content.key}")
                                    else:
                                        print('Get Object Acl Failed')
                                        print('requestId:', acl_resp.requestId)
                                        print('errorCode:', acl_resp.errorCode)
                                        print('errorMessage:', acl_resp.errorMessage)
                                except Exception as e:
                                    print(f'Failed to get ACL for the object {content.key}')
                                    print('Error:', str(e))
                                    print('Traceback:', traceback.format_exc())

                                index += 1
                            if resp.body.is_truncated is True:
                                mark = resp.body.next_marker
                            else:
                                break
                        else:
                            print('errorCode:', resp.errorCode)
                            print('errorMessage:', resp.errorMessage)
                            break
                except Exception as e:
                    print(f'Failed to get the object list for the bucket {bucket_name}')
                    print('Error:', str(e))
                    print('Traceback:', traceback.format_exc())

        # Output all objects with public read permission.
        if public_objects:
            print("\nAll objects with public read permission:")
            for obj in public_objects:
                print(obj)
        else:
            print("\nNo objects with public read permission were found")

    except Exception as e:
        print('Operation Failed')
        print(traceback.format_exc())