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

import hashlib
import io
import os

import pytest

from conftest import gen_random_file, test_config
from obs import CompleteMultipartUploadRequest, CompletePart, CryptoObsClient
from test_obs_client import TestOBSClient


class TestCryptoOBSClient(TestOBSClient):
    def get_client(self):
        client_type = "CTRCryptoClient"
        path_style = True if test_config["auth_type"] == "v2" else False

        uploadClient = CryptoObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                                       server=test_config["endpoint"], cipher_generator="",
                                       is_signature_negotiation=False, path_style=path_style)
        downloadClient = CryptoObsClient(access_key_id=test_config["ak"],
                                         secret_access_key=test_config["sk"],
                                         server=test_config["endpoint"],
                                         cipher_generator="",
                                         is_signature_negotiation=False, path_style=path_style)
        return client_type, uploadClient, downloadClient

    def get_encrypted_content(self):
        pass

    def test_initiateEncryptedMultipartUpload_and_uploadEncryptedPart(self):
        client_type, uploadClient, downloadClient = self.get_client()
        object_name = client_type + "test_initiateEncryptedMultipartUpload"
        test_bytes = io.BytesIO(b"test_initiateEncryptedMultipartUpload")
        cipher = uploadClient.cipher_generator.new(test_bytes)
        init_result = uploadClient.initiateEncryptedMultipartUpload(test_config["bucketName"], object_name, cipher)
        assert init_result.status == 200
        assert "uploadId" in init_result.body
        gen_random_file(object_name, 10240)
        uploaded_parts = []
        upload_result = uploadClient.uploadEncryptedPart(test_config["bucketName"], object_name, 1,
                                                         init_result.body["uploadId"], crypto_cipher=cipher,
                                                         object=test_config["path_prefix"] + object_name, isFile=True)
        assert upload_result.status == 200
        uploaded_parts.append(CompletePart(partNum=1, etag=dict(upload_result.header).get('etag')))
        upload_result = uploadClient.uploadEncryptedPart(test_config["bucketName"], object_name, 2,
                                                         init_result.body["uploadId"], crypto_cipher=cipher,
                                                         object=open(test_config["path_prefix"] + object_name, "rb"))
        assert upload_result.status == 200

        uploaded_parts.append(CompletePart(partNum=2, etag=dict(upload_result.header).get('etag')))
        upload_result = uploadClient.uploadEncryptedPart(test_config["bucketName"], object_name, 3,
                                                         init_result.body["uploadId"], crypto_cipher=cipher,
                                                         object="test obs")
        assert upload_result.status == 200

        uploaded_parts.append(CompletePart(partNum=3, etag=dict(upload_result.header).get('etag')))
        complete_result = uploadClient.completeMultipartUpload(test_config["bucketName"], object_name,
                                                               init_result.body["uploadId"],
                                                               CompleteMultipartUploadRequest(uploaded_parts))
        assert complete_result.status == 200

        download_result = downloadClient.getObject(test_config["bucketName"], object_name, loadStreamInMemory=True)
        assert download_result.status == 200
        download_sha256 = hashlib.sha256()
        download_sha256.update(download_result.body.buffer)
        local_sha256 = hashlib.sha256()
        with open(test_config["path_prefix"] + object_name, "rb") as f:
            local_sha256.update(f.read())
            f.seek(0)
            local_sha256.update(f.read())
        local_sha256.update("test obs".encode("UTF-8"))
        assert local_sha256.hexdigest() == download_sha256.hexdigest()

        uploadClient.deleteObject(test_config["bucketName"], object_name)
        os.remove(test_config["path_prefix"] + object_name)

    def test_appendObject(self):
        client_type, uploadClient, downloadClient = self.get_client()
        has_exception = False
        try:
            uploadClient.appendObject(test_config["bucketName"], "test_append_object")
        except Exception as e:
            has_exception = True
            assert str(e) == 'AppendObject is not supported in CryptoObsClient'
        assert has_exception

    def test_copyPart(self):
        client_type, uploadClient, downloadClient = self.get_client()
        has_exception = False
        try:
            uploadClient.copyPart(test_config["bucketName"], "test_copyPart", 1,
                                  "test_copyPart_ID", "test_copyPart_source")
        except Exception as e:
            has_exception = True
            assert str(e) == 'CopyPart is not supported in CryptoObsClient'
        assert has_exception

    def test_initiateMultipartUpload(self):
        client_type, uploadClient, downloadClient = self.get_client()
        has_exception = False
        try:
            uploadClient.initiateMultipartUpload(test_config["bucketName"], "test_initiateMultipartUpload")
        except Exception as e:
            has_exception = True
            assert str(e) == 'InitiateMultipartUpload is not supported in CryptoObsClient'
        assert has_exception

    def test_uploadPart(self):
        client_type, uploadClient, downloadClient = self.get_client()
        has_exception = False
        try:
            uploadClient.uploadPart(test_config["bucketName"], "test_uploadPart", 1, "test_uploadPart")
        except Exception as e:
            has_exception = True
            assert str(e) == 'UploadPart is not supported in CryptoObsClient'
        assert has_exception

    def test_getObject_with_no_metadata(self):
        has_exception = False
        object_key = "test_downloadFile_with_no_metadata"
        client_type, uploadClient, downloadClient = self.get_client()
        upload_result = uploadClient.putContent(test_config["bucketName"], object_key,
                                                "test obs")
        assert upload_result.status == 200

        set_result = uploadClient.setObjectMetadata(test_config["bucketName"], object_key,
                                                    metadata={"aaa": "bbb"})
        assert set_result.status == 200
        try:
            downloadClient.getObject(test_config["bucketName"], object_key)
        except Exception as e:
            has_exception = True
            assert str(e) == "Crypto mod is not in object's metadata"
        assert has_exception
        uploadClient.deleteObject(test_config["bucketName"], object_key)

    def test_getObject_with_wrong_crypto_mod(self):
        has_exception = False
        object_key = "test_downloadFile_with_no_metadata"
        client_type, uploadClient, downloadClient = self.get_client()
        upload_result = uploadClient.putContent(test_config["bucketName"], object_key,
                                                "test obs")
        assert upload_result.status == 200

        set_result = uploadClient.setObjectMetadata(test_config["bucketName"], object_key,
                                                    metadata={"encrypted-algorithm": "wrong encrypted-algorithm"})
        assert set_result.status == 200
        try:
            downloadClient.getObject(test_config["bucketName"], object_key)
        except Exception as e:
            has_exception = True
            assert str(e) == "Object's crypto mod is not equals cipher-generator's, " \
                                "please change a different cipher-generator"
        assert has_exception
        uploadClient.deleteObject(test_config["bucketName"], object_key)

    def test_initiateMultipartUpload_and_uploadPart_and_copyPart(self):
        has_exception = False
        try:
            super(TestCryptoOBSClient, self).test_initiateMultipartUpload_and_uploadPart_and_copyPart()
        except Exception as e:
            has_exception = True
            assert str(e) == 'InitiateMultipartUpload is not supported in CryptoObsClient'
        assert has_exception


class TestCryptoOBSClientWithSha256(TestCryptoOBSClient):
    def test_putContent_with_file_stream(self, gen_test_file):
        has_exception = False
        try:
            super(TestCryptoOBSClientWithSha256, self).test_putContent_with_file_stream(gen_test_file)
        except Exception as e:
            has_exception = True
            assert str(e) == "Could not calculate sha256 for a stream object"
        assert has_exception

    def test_putContent_with_network_stream(self, gen_test_file):
        has_exception = False
        try:
            super(TestCryptoOBSClientWithSha256, self).test_putContent_with_network_stream(gen_test_file)
        except Exception as e:
            has_exception = True
            assert str(e) == "Could not calculate sha256 for a stream object"
        assert has_exception

    def test_putContent_has_sha256(self):
        client_type, uploadClient, downloadClient = self.get_client()
        object_key = "test_putContent_has_sha256"
        upload_result = uploadClient.putContent(test_config["bucketName"], object_key, "test obs")
        assert upload_result.status == 200

        metadata = uploadClient.getObjectMetadata(test_config["bucketName"], object_key)
        assert metadata.status == 200
        metadata_dict = dict(metadata.header)
        assert metadata_dict["plaintext-sha256"] == "4c3600ae5c56b61a2b0d15681a5f3945ad92f671891d7ec3db366743d09ade08"
        assert "encrypted-start" in metadata_dict
        uploadClient.deleteObject(test_config["bucketName"], object_key)

    def test_uploadFile_has_sha256(self):
        client_type, uploadClient, downloadClient = self.get_client()
        object_key = "test_uploadFile_has_sha256"
        gen_random_file(object_key, 10240)
        upload_result = uploadClient.uploadFile(test_config["bucketName"], object_key,
                                                test_config["path_prefix"] + object_key)
        assert upload_result.status == 200
        sha256 = hashlib.sha256()
        with open(test_config["path_prefix"] + object_key) as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                sha256.update(chunk)

        metadata = uploadClient.getObjectMetadata(test_config["bucketName"], object_key)
        assert metadata.status == 200
        metadata_dict = dict(metadata.header)
        assert metadata_dict["plaintext-sha256"] == sha256.hexdigest()
        assert "encrypted-start" in metadata_dict
        uploadClient.deleteObject(test_config["bucketName"], object_key)
        os.remove(test_config["path_prefix"] + object_key)

    def test_putFile_has_sha256(self):
        client_type, uploadClient, downloadClient = self.get_client()
        object_key = "test_putFile_has_sha256"
        gen_random_file(object_key, 10240)
        upload_result = uploadClient.putFile(test_config["bucketName"], object_key,
                                             test_config["path_prefix"] + object_key)
        assert upload_result.status == 200
        sha256 = hashlib.sha256()
        with open(test_config["path_prefix"] + object_key) as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                sha256.update(chunk)

        metadata = uploadClient.getObjectMetadata(test_config["bucketName"], object_key)
        assert metadata.status == 200
        metadata_dict = dict(metadata.header)
        assert metadata_dict["plaintext-sha256"] == sha256.hexdigest()
        assert "encrypted-start" in metadata_dict
        uploadClient.deleteObject(test_config["bucketName"], object_key)
        os.remove(test_config["path_prefix"] + object_key)

    def test_initiateEncryptedMultipartUpload_and_uploadEncryptedPart(self):
        has_exception = False
        try:
            super(TestCryptoOBSClientWithSha256, self).test_initiateEncryptedMultipartUpload_and_uploadEncryptedPart()
        except Exception as e:
            has_exception = True
            assert str(e) == 'Could not calculate sha256 for initiateMultipartUpload'
        assert has_exception


if __name__ == "__main__":
    pytest.main(["-v", 'test_ctr_crypto_client.py::TestCryptoOBSClient'])
