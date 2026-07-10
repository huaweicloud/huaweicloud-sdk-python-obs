#!/usr/bin/python
# -*- coding:utf-8 -*-
# Copyright 2019 Huawei Technologies Co.,Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations under the License.
#
"""
  This sample demonstrates how to restore delete markers for objects in a bucket operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

from obs import ObsClient
from obs import Versions, Object
from obs import DeleteObjectsRequest
import traceback
import time

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
prefix = 'prefix'
# Restore all delete markers within this time range
startTime = '2026/06/03 00:00:00'  # eg :2026/06/03 00:00:00
endTime = '2026/06/04 00:00:00'  # eg:2026/06/04 00:00:00

if __name__ == '__main__':
    # Create an obsClient instance
    obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

    is_truncated = True
    key_marker = None
    version_id_marker = None
    deleted_list = []

    while is_truncated is True:
        try:
            # List delete markers
            resp = obsClient.listVersions(bucketName, version=Versions(prefix=prefix, key_marker=key_marker,
                    version_id_marker=version_id_marker, max_keys=1000, encoding_type='url'))
            if (resp.status > 300):
                print('Something is wrong when listing versions. Error Code: {0}. Error Message: {1}'.format(
                    resp.errorCode, resp.errorMessage))
                continue
            is_truncated = resp.body.head.isTruncated  # Whether there is a next page
            key_marker = resp.body.head.nextKeyMarker  # The starting position for listing multi-version objects. The returned object list will be all objects after this parameter in lexicographical order.
            version_id_marker = resp.body.head.nextVersionIdMarker  # Used with key_marker to return all objects after this parameter in lexicographical order by object name and version number. If version_id_marker is not a version number of key_marker, this parameter is invalid.

            # Filter delete markers by time
            for item in resp.body.markers:
                if (time.strptime(endTime, "%Y/%m/%d %H:%M:%S") >= time.strptime(item.lastModified, "%Y/%m/%d %H:%M:%S") >= time.strptime(startTime, "%Y/%m/%d %H:%M:%S")):
                    deleted_list.append(Object(key=item.key, versionId=item.versionId))

            # Batch delete
            if deleted_list:
                resp = obsClient.deleteObjects(bucketName, DeleteObjectsRequest(objects=deleted_list, encoding_type='url'))
                if (resp.status > 300):
                    print('Something is wrong when deleting objects. Error Code: {0}. Error Message: {1}'.format(
                        resp.errorCode, resp.errorMessage))
                else:
                    print('Successfully deleted objects.')
        except Exception as e:
            print(traceback.format_exc())

    print("finish")