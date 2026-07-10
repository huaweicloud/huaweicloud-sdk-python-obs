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
  This sample demonstrates how to download objects from a bucket operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import os
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

    # Parameters for downloading objects
    remote_prefix = 'test'
    local_folder = 'D:/'
    failed_list = []
    prefix_length = len(remote_prefix)

    # List objects in the bucket with the specified prefix
    object_list = obsClient.listObjects(bucketName, prefix=remote_prefix, encoding_type="url")
    page = 1

    while True:
        print('Start to download page %s' % page)
        page += 1
        for obs_object in object_list.body["contents"]:
            object_key = obs_object["key"]
            # Convert the OBS object name to a local path
            download_file_path = os.path.join(local_folder, object_key[prefix_length + 1:].replace("/", os.sep))
            print('Start to download object [%s] to [%s]' % (object_key, download_file_path))
            try:
                obsClient.downloadFile(bucketName, object_key, taskNum=10, downloadFile=download_file_path)
            except Exception as e:
                print('Failed to download %s' % object_key)
                failed_list.append(object_key)

        # If is_truncated is False, all objects have been listed
        if not object_list.body["is_truncated"]:
            break
        # Use the next_marker from the previous response to list the next page
        object_list = obsClient.listObjects(bucketName, prefix=remote_prefix, encoding_type="url", marker=object_list.body["next_marker"])

    # Print failed download objects
    for i in failed_list:
        print('Failed to download %s, please try again' % i)
