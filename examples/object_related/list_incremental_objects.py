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
  This sample demonstrates how to list incremental objects within a specified time range in a bucket on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback
import datetime
from obs import ObsClient

# Configure OBS client
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'

# Define the time range for incremental objects
start_time = datetime.datetime(2023, 1, 1)  # Start time (inclusive)
end_time = datetime.datetime(2023, 1, 31)   # End time (inclusive)

if __name__ == '__main__':
    # Create an OBS client instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    try:
        # Initialize variables for pagination
        marker = None
        incremental_objects = []

        while True:
            # List objects with pagination
            resp = obsClient.listObjects(bucketName, marker=marker, max_keys=1000)
            if resp.status < 300:
                print('List Objects Succeeded')
                objects = resp.body.contents

                # Convert lastModified to datetime.datetime and filter objects by the specified time range
                incremental_objects.extend([
                    obj for obj in objects
                    if start_time <= datetime.datetime.strptime(obj.lastModified, '%Y/%m/%d %H:%M:%S') <= end_time
                ])

                # Update marker for the next page
                marker = resp.body.next_marker
                if not resp.body.is_truncated:
                    break
            else:
                print('List Objects Failed')
                print('requestId:', resp.requestId)
                print('errorCode:', resp.errorCode)
                print('errorMessage:', resp.errorMessage)
                break

        # Output the incremental objects
        print(f'Incremental objects in bucket {bucketName} from {start_time} to {end_time}:')
        for obj in incremental_objects:
            print(f'Key: {obj.key}, Last Modified: {obj.lastModified}, Size: {obj.size} bytes')

        # Output the total number of incremental objects
        print(f'Total number of incremental objects: {len(incremental_objects)}')

    except Exception as e:
        print('List Objects Failed')
        print(traceback.format_exc())
