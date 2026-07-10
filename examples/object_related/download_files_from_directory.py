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
  This sample demonstrates how to download files from a specific directory within a bucket on OBS using the OBS SDK for Python.
  The script uses pagination to efficiently handle large numbers of files and ensures all files are processed while preserving the original directory structure.
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
# Specify the name of the bucket to download files from.
bucketName = 'your-obs-bucket'
# Specify the directory to download files from.
remote_prefix = 'your-directory/'
# Specify the local directory to save downloaded files.
local_folder = 'your/local/path'

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        failed_list = []
        prefix_length = len(remote_prefix)
        page = 1

        # List objects in the specified directory
        object_list = obsClient.listObjects(bucketName, prefix=remote_prefix, encoding_type="url")

        if object_list.status >= 300:
            print('Failed to list objects in the specified directory')
            print('requestId:', object_list.requestId)
            print('errorCode:', object_list.errorCode)
            print('errorMessage:', object_list.errorMessage)
            exit(1)

        while True:
            print("Start to download page %s" % page)
            page += 1
            for obs_object in object_list.body["contents"]:
                object_key = obs_object["key"]
                # Extract the relative path from the object key
                relative_path = object_key[prefix_length:]
                # Construct the local file path
                local_file_path = os.path.join(local_folder, relative_path)
                # Ensure the local directory exists
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                print("Start to download object [%s] to [%s]" % (object_key, local_file_path))
                try:
                    obsClient.downloadFile(bucketName, object_key, taskNum=10,
                                           downloadFile=local_file_path)
                except Exception as e:
                    print("Failed to download %s" % object_key)
                    failed_list.append(object_key)

            # If is_truncated is False, it means all objects have been listed
            if not object_list.body["is_truncated"]:
                break
            # Use the next_marker from the previous response to list the next page
            object_list = obsClient.listObjects(bucketName, prefix=remote_prefix,
                                                encoding_type="url", marker=object_list.body["next_marker"])

        for i in failed_list:
            print("Failed to download %s, please try again" % i)
    except Exception as e:
        print('Download Files Failed')
        print(traceback.format_exc())
