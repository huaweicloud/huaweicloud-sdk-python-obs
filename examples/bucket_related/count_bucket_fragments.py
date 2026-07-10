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
  This sample demonstrates how to  count bucket fragments (small files) on OBS using the OBS SDK for Python.
"""

from obs import ObsClient
import os
import traceback
from obs import ListMultipartUploadsRequest

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
        totalFragmentSize = 0
        upload_id_marker = None
        is_flag = True
        while is_flag:
            # The maximum number of multipart upload tasks to list, with a value range of 1 to 1000. When the value exceeds the range, it will be handled with the default value of 1000. The value here is 10.
            max_uploads = 1
            # The request parameters for listing multipart upload tasks in a bucket.
            multipart = ListMultipartUploadsRequest(max_uploads=max_uploads, upload_id_marker=upload_id_marker)
            # List multipart upload tasks in a bucket.
            resp = obsClient.listMultipartUploads(bucketName, multipart)

            if resp.body.nextUploadIdMarker is not None:
                upload_id_marker = resp.body.nextUploadIdMarker
            else:
                is_flag = False

            # Iterate through the multipart upload task list, query the part list based on the uploadId, and calculate the total size of the fragments.
            for upload in resp.body.upload:
                uploadId = upload.uploadId
                objectKey = upload.key
                partsResp = obsClient.listParts(bucketName, objectKey, uploadId)
                for part in partsResp.body.parts:
                    totalFragmentSize += part.size

        # Output the statistics results
        print('Total Fragment Size in Bucket:', totalFragmentSize, 'bytes')
    except Exception as e:
        print('Count Bucket Fragments Failed')
        print(traceback.format_exc())