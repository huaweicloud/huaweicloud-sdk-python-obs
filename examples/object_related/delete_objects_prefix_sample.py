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
  This sample demonstrates how to delete objects in a folder operation on OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback
import os

from obs import ObsClient, DeleteObjectsRequest, Object

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
# Specify the folder to be deleted.
prefix = 'test/'
# Specify the maximum number of objects to be listed at a time. 1000 is used in this example.
max_num = 1000

if __name__ == '__main__':
    try:
        # Create an obsClient instance
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
        mark = None
        index = 1
        failed_list = []
        while True:
            resp = obsClient.listObjects(bucketName=bucketName, prefix=prefix, marker=mark, max_keys=max_num,
                                         encoding_type='url')
            if resp.status < 300:
                need_to_delete_objects = [Object(key=i["key"], versionId=None) for i in resp.body["contents"]]
                del_resp = obsClient.deleteObjects(bucketName,
                                                   DeleteObjectsRequest(False, need_to_delete_objects, encoding_type="url"))
                for delete in del_resp.body.deleted:
                    print("Successfully deleted %s " % delete.key)
                    index += 1
                if del_resp.body.error:
                    for err in del_resp.body.error:
                        print("Failed to delete %s" % err.key)
                        failed_list.append(err.key)
                if resp.body.is_truncated is True:
                    mark = resp.body.next_marker
                else:
                    break
            else:
                print('errorCode:', resp.errorCode)
                print('errorMessage:', resp.errorMessage)
                break
        print("Total deleted %s objects" % index)
        for i in failed_list:
            print("Failed to delete %s, please try again" % i)
    except Exception as e:
        print('Delete Objects Failed')
        print(traceback.format_exc())