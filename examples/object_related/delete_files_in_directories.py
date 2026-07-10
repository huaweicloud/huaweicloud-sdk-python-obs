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
  This sample demonstrates how to delete files in specific directories within a bucket on OBS using the OBS SDK for Python.
  The script uses pagination to efficiently handle large numbers of files and ensures all files are processed.
"""

from __future__ import print_function

import traceback

from obs import ObsClient, DeleteObjectsRequest
import os

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket. CN-Hong Kong is used here as an example. Replace it with the one in use.
server = 'https://your-endpoint'
# Specify the name of the bucket to delete files from.
bucketName = 'your-obs-bucket'
# Specify the directories to delete files from.
directories = ['directory01/']

if __name__ == '__main__':
    # Create an obsClient instance.
    obsClient = ObsClient(
        access_key_id=AK,
        secret_access_key=SK,
        server=server,
    )

    try:
        total_deleted = 0
        for directory in directories:
            # Initialize variables for pagination
            marker = None
            objects_to_delete = []

            while True:
                # List objects with pagination
                resp = obsClient.listObjects(bucketName, prefix=directory, marker=marker)
                if resp.status < 300:
                    if resp.body and resp.body.contents:
                        for content in resp.body.contents:
                            objects_to_delete.append({'key': content.key})

                    # Update marker for the next page
                    marker = resp.body.next_marker
                    if not resp.body.is_truncated:
                        break
                else:
                    print(f"Failed to list files: {resp.errorCode}, {resp.errorMessage}, directory: {directory}")
                    print('requestId:', resp.requestId)
                    break

            if objects_to_delete:
                # Create DeleteObjectsRequest object
                delete_request = DeleteObjectsRequest()
                delete_request.quiet = False  # Optional, set to True to reduce detailed information in the response
                delete_request.objects = objects_to_delete

                # Delete files
                delete_resp = obsClient.deleteObjects(bucketName, delete_request)
                if delete_resp.status < 300:
                    print(f"Successfully deleted {len(objects_to_delete)} files, directory: {directory}")
                    total_deleted += len(objects_to_delete)
                else:
                    print(f"Failed to delete files: {delete_resp.errorCode}, {delete_resp.errorMessage}, directory: {directory}, requestId: {delete_resp.requestId}")
            else:
                print(f"No files to delete in directory: {directory}")

        print(f"Total of {total_deleted} files deleted successfully")
    except Exception as e:
        print('Delete Files Failed')
        print(traceback.format_exc())
