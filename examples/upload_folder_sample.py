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
  This sample demonstrates how to upload folder to OBS using the OBS SDK for Python.
"""

from __future__ import print_function

import traceback
import os

from obs import ObsClient

# Obtain an AK and SK pair using environment variables or import the AK and SK pair in other ways. Using hard coding may result in leakage.
# Obtain an AK and SK pair on the management console. For details, see https://support.huaweicloud.com/intl/en-us/usermanual-ca/ca_01_0003.html.
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
# Set server to the endpoint corresponding to the bucket
server = 'https://your-endpoint'
bucketName = 'your-obs-bucket'
# Specify the remote prefix for uploaded files
remotePrefix = 'remote_prefix/'
# Specify the local folder path to be uploaded
localFolder = 'your/local/path'

def upload_files(obsClient, bucket, local_folder, remote_prefix, failed_list):
    """
    Upload files from local folder to OBS bucket
    
    Args:
        obsClient: OBS client instance
        bucket: OBS bucket name
        local_folder: Local folder path
        remote_prefix: Remote prefix for uploaded files
        failed_list: List to record failed files
    """
    # Get the absolute path of the local folder
    local_folder = os.path.abspath(local_folder)
    
    # Stack-based approach to process directories
    folder_stack = [local_folder]
    
    # Process all folders in the stack
    while folder_stack:
        current_folder = folder_stack.pop()
        
        try:
            # Get all items in the current folder
            items = os.listdir(current_folder)
            
            for item in items:
                item_path = os.path.join(current_folder, item)
                
                if os.path.isfile(item_path):
                    # If it's a file, upload to OBS
                    # Construct the remote object key
                    relative_path = os.path.relpath(item_path, local_folder)
                    object_key = remote_prefix + relative_path.replace(os.sep, "/")
                    
                    print('Start to upload ' + item_path + ' to OBS, using objectKey: ' + object_key)
                    
                    try:
                        # Upload file
                        with open(item_path, 'rb') as f:
                            resp = obsClient.putContent(bucket, object_key, f)
                            
                        if resp.status < 300:
                            print('Upload succeeded: ' + item_path)
                        else:
                            print('Upload failed: ' + item_path + ', status code: ' + str(resp.status))
                            failed_list.append(item_path)
                    except Exception as e:
                        print('Upload exception: ' + item_path + ', error: ' + str(e))
                        failed_list.append(item_path)
                elif os.path.isdir(item_path):
                    # If it's a directory, add it to the stack for later processing
                    folder_stack.append(item_path)
                    
        except Exception as e:
            print('Error processing folder ' + current_folder + ': ' + str(e))

if __name__ == '__main__':
    # Used to record failed files
    failedList = []
    obsClient = None

    try:
        # Create an obsClient instance
        obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
        
        # Create bucket if not exists
        resp = obsClient.createBucket(bucketName)
        if resp.status < 300:
            print('Create Bucket Succeeded')

            # Start uploading
            print('Start to upload folder ' + localFolder + ' to OBS bucket ' + bucketName)

            # Upload files
            upload_files(obsClient, bucketName, localFolder, remotePrefix, failedList)

            # Print failed list
            if failedList:
                print('Failed to upload the following files:')
                for item in failedList:
                    print('  - ' + item)
            else:
                print('All files uploaded successfully!')

        else:
            print('Create Bucket Failed')
            print('requestId:', resp.requestId)
            print('errorCode:', resp.errorCode)
            print('errorMessage:', resp.errorMessage)
            print('Bucket creation failed. Exiting...')

    except Exception as e:
        print('Upload folder failed!')
        print(traceback.format_exc())
    finally:
        # Close the obsClient to release resources
        if obsClient is not None:
            obsClient.close()