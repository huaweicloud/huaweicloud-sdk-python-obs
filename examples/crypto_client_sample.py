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
 This sample demonstrates how to using crypto client in OBS Python SDK.
"""
from obs import CompleteMultipartUploadRequest, CompletePart, CryptoObsClient
from obs.obs_cipher_suite import CTRCipherGenerator, CtrRSACipherGenerator

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'

bucketName = 'my-obs-bucket-demo'
test_file = "path/to/your/test/file"

# Construct a crypto obs client with CtrRSACipherGenerator
# CtrRSACipherGenerator using public key
public_g = CtrRSACipherGenerator("/path/to/public_key.pem", master_key_info="Test_Key22")
public_client = CryptoObsClient(access_key_id=AK, secret_access_key=SK, server=server, cipher_generator=public_g)

# CtrRSACipherGenerator using private key
private_g = CtrRSACipherGenerator("/path/to/private_key.pem", master_key_info="Test_Key22")
private_client = CryptoObsClient(access_key_id=AK, secret_access_key=SK, server=server, cipher_generator=private_g)

# Construct a crypto obs client with CTRCipherGenerator
# The byte length of master key mast equal 32
ctr_g = CTRCipherGenerator("your-master-key")
ctr_client = CryptoObsClient(access_key_id=AK, secret_access_key=SK, server=server, cipher_generator=ctr_g)

# Create bucket
bucketClient = ctr_client.bucketClient(bucketName)

# Upload file
# Uploading file in crypto obsClient is same as in normal obsClient
upload_object_key = "upload_test_file_with_ctr_client"
ctr_client_result = ctr_client.putFile(bucketName, upload_object_key, test_file)
if ctr_client_result.status < 300:
    print('Upload finished\n')

# Multipart upload File

object_key = "Multipart_upload_File"

# Step 1: Generate a cipher using empty string
print('Step 1: Generate a cipher using empty string \n')
cipher = ctr_client.cipher_generator.new("")

# Step 2: initiate multipart upload
print('Step 2: initiate multipart upload \n')
init_result = ctr_client.initiateEncryptedMultipartUpload(bucketName, object_key, cipher)
uploadId = init_result.body.uploadId

# Step 3: upload a part
print('Step 3: upload a part\n')
partNum = 1
resp = ctr_client.uploadEncryptedPart(bucketName, object_key, partNumber=partNum, uploadId=uploadId,
                                      crypto_cipher=cipher, content='Hello OBS')
etag = dict(resp.header).get('etag')

# Step 4: complete multipart upload
print('Step 4: complete multipart upload\n')
resp = ctr_client.completeMultipartUpload(bucketName, object_key, uploadId,
                                          CompleteMultipartUploadRequest([CompletePart(partNum=partNum, etag=etag)]))
if resp.status < 300:
    print('Complete finished\n')

# Download file
# Downloading file in crypto obsClient is same as in normal obsClient
download_result = ctr_client.getObject(bucketName, upload_object_key, downloadPath="/path/to/save")
if download_result.status < 300:
    print('Download finished\n')
