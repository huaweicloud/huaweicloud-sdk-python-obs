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

import pytest

from conftest import test_config
from obs import CTRCipherGenerator, CryptoObsClient, const
from test_crypto_obs_client import TestCryptoOBSClient, TestCryptoOBSClientWithSha256

if const.IS_PYTHON2:
    chr = unichr


class TestCTRCryptoClient(TestCryptoOBSClient):
    def get_client(self):
        client_type = "CTRCryptoClient"
        path_style = True if test_config["auth_type"] == "v2" else False
        ctr_cipher_generator = CTRCipherGenerator("0123456789abcdef0123456789abcdef", need_sha256=False)
        uploadClient = CryptoObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                                       server=test_config["endpoint"], cipher_generator=ctr_cipher_generator,
                                       is_signature_negotiation=False, path_style=path_style)
        downloadClient = CryptoObsClient(access_key_id=test_config["ak"],
                                         secret_access_key=test_config["sk"],
                                         server=test_config["endpoint"],
                                         cipher_generator=ctr_cipher_generator,
                                         is_signature_negotiation=False, path_style=path_style)
        return client_type, uploadClient, downloadClient

    def test_downloadFile_with_wrong_iv(self):
        has_exception = False
        object_key = "downloadFile_with_wrong_iv"
        upload_cipher_generator = CTRCipherGenerator("0123456789abcdef0123456789abcdef", crypto_iv="12345678",
                                                     need_sha256=False)
        uploadClient = CryptoObsClient(access_key_id=test_config["ak"],
                                       secret_access_key=test_config["sk"],
                                       server=test_config["endpoint"],
                                       cipher_generator=upload_cipher_generator)
        download_cipher_generator = CTRCipherGenerator("0123456789abcdef0123456789abcdef", crypto_iv="12345678",
                                                       need_sha256=False)
        downloadClient = CryptoObsClient(access_key_id=test_config["ak"],
                                         secret_access_key=test_config["sk"],
                                         server=test_config["endpoint"],
                                         cipher_generator=download_cipher_generator)
        upload_result = uploadClient.putContent(test_config["bucketName"], object_key, "test OBS")
        assert upload_result.status == 200
        try:
            downloadClient.getObject(test_config["bucketName"], object_key)
        except Exception as e:
            has_exception = True
            assert str(e) == "Crypto_iv is different between local and server"
        assert has_exception
        uploadClient.deleteObject(test_config["bucketName"], object_key)


class TestCTRCryptoClientWithSha256(TestCryptoOBSClientWithSha256):
    def get_client(self):
        client_type = "CTRCryptoClient"
        path_style = True if test_config["auth_type"] == "v2" else False
        ctr_cipher_generator = CTRCipherGenerator("0123456789abcdef0123456789abcdef", need_sha256=True)
        uploadClient = CryptoObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                                       server=test_config["endpoint"], cipher_generator=ctr_cipher_generator,
                                       is_signature_negotiation=False, path_style=path_style)
        downloadClient = CryptoObsClient(access_key_id=test_config["ak"],
                                         secret_access_key=test_config["sk"],
                                         server=test_config["endpoint"],
                                         cipher_generator=ctr_cipher_generator,
                                         is_signature_negotiation=False, path_style=path_style)
        return client_type, uploadClient, downloadClient


if __name__ == "__main__":
    pytest.main(["-v", 'test_ctr_crypto_client.py::TestCTRCryptoClient',
                 'test_ctr_crypto_client.py::TestCTRCryptoClientWithSha256'])
