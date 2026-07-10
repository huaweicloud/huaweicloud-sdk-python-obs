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
  This sample demonstrates how to download folder from OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import os
import traceback

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
# Authentication AK and SK are directly written in the code, which has a great security risk. It is recommended to store them in a configuration file or environment variables in encrypted form and decrypt them when used to ensure security.
# This example uses AK and SK saved in environment variables to implement identity authentication. Please set the environment variables HUAWEICLOUD_SDK_AK and HUAWEICLOUD_SDK_SK in the local environment before running this example.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
# Specify the remote prefix for downloaded files
remotePrefix = 'remote_prefix/'
# Specify the local folder path to download to
localFolder = 'your/local/path'

if __name__ == '__main__':
    # Used to record failed objects
    failedList = []
    obsClient = None
    
    try:
        # Create an obsClient instance
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
        
        # List objects with the specified prefix
        objectList = obsClient.listObjects(bucketName, prefix=remotePrefix, encoding_type="url")
        
        page = 1
        
        while True:
            print("Start to download page %s" % page)
            page += 1
            
            if objectList.body is None:
                print("No objects found")
                break
                
            if "contents" not in objectList.body:
                print("No objects found in response")
                break
                
            for obsObject in objectList.body["contents"]:
                objectKey = obsObject["key"]
                # Calculate the relative path by removing the prefix
                # Handle the case where remotePrefix might not end with '/' 
                if remotePrefix.endswith('/'):
                    if objectKey.startswith(remotePrefix):
                        relativePath = objectKey[len(remotePrefix):]
                        # Handle the case where objectKey equals remotePrefix (both end with '/')
                        if relativePath == '':
                            print("Failed to download %s" % objectKey)
                            print("local file name not supported end with /")
                            failedList.append(objectKey)
                            continue
                    else:
                        relativePath = objectKey
                else:
                    # If prefix doesn't end with '/', we need to be more careful
                    if objectKey.startswith(remotePrefix + '/'):
                        relativePath = objectKey[len(remotePrefix) + 1:]
                    else:
                        relativePath = objectKey
                
                # Convert OBS object name to local path
                downloadFilePath = os.path.join(localFolder, relativePath.replace("/", os.sep))
                print("Start to download object [%s] to [%s]" % (objectKey, downloadFilePath))
                
                try:
                    # Create local directory if not exists
                    downloadDir = os.path.dirname(downloadFilePath)
                    if not os.path.exists(downloadDir):
                        os.makedirs(downloadDir)
                    
                    # Download file and check return value
                    resp = obsClient.downloadFile(bucketName, objectKey, taskNum=10,
                                           downloadFile=downloadFilePath)
                    if resp.status < 300:
                        print("Download succeeded: " + objectKey)
                    else:
                        print("Download failed: " + objectKey + ", status code: " + str(resp.status))
                        failedList.append(objectKey)
                except Exception as e:
                    print("Failed to download %s" % objectKey)
                    failedList.append(objectKey)

            # If is_truncated is False, it means all objects have been listed
            if not objectList.body.get("is_truncated", False):
                break
            # Use the next_marker from the previous response as the marker for the next listing
            objectList = obsClient.listObjects(bucketName, prefix=remotePrefix,
                                               encoding_type="url", marker=objectList.body.get("next_marker"))

        # Print failed list
        if failedList:
            print("Failed to download the following objects:")
            for item in failedList:
                print("  - " + item)
            print("Total failed downloads: %d" % len(failedList))
        else:
            print("All files downloaded successfully!")
            
    except Exception as e:
        print('Download folder failed!')
        print(traceback.format_exc())
    finally:
        # Close the obsClient to release resources
        if obsClient is not None:
            obsClient.close()

