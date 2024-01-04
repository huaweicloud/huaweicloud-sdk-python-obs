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

from obs import CryptoObsClient, CtrRSACipherGenerator
from conftest import test_config
from test_crypto_obs_client import TestCryptoOBSClient, TestCryptoOBSClientWithSha256


class TestRSACTRCryptoClient(TestCryptoOBSClient):
    def get_client(self):
        client_type = "RSACTRCryptoClient"
        public_cipher_generator = CtrRSACipherGenerator(test_config["public_key"], need_sha256=False)
        path_style = True if test_config["auth_type"] == "v2" else False
        uploadClient = CryptoObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                                       server=test_config["endpoint"], cipher_generator=public_cipher_generator,
                                       is_signature_negotiation=False, path_style=path_style)
        private_cipher_generator = CtrRSACipherGenerator(test_config["private_key"], need_sha256=False)
        downloadClient = CryptoObsClient(access_key_id=test_config["ak"],
                                         secret_access_key=test_config["sk"],
                                         server=test_config["endpoint"],
                                         cipher_generator=private_cipher_generator,
                                         is_signature_negotiation=False, path_style=path_style)
        return client_type, uploadClient, downloadClient


class TestRSACTRCryptoClientWithSha256(TestCryptoOBSClientWithSha256):
    def get_client(self):
        client_type = "RSACTRCryptoClient"
        public_cipher_generator = CtrRSACipherGenerator(test_config["public_key"], need_sha256=True)
        path_style = True if test_config["auth_type"] == "v2" else False
        uploadClient = CryptoObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                                       server=test_config["endpoint"], cipher_generator=public_cipher_generator,
                                       is_signature_negotiation=False, path_style=path_style)
        private_cipher_generator = CtrRSACipherGenerator(test_config["private_key"], need_sha256=True)
        downloadClient = CryptoObsClient(access_key_id=test_config["ak"],
                                         secret_access_key=test_config["sk"],
                                         server=test_config["endpoint"],
                                         cipher_generator=private_cipher_generator,
                                         is_signature_negotiation=False, path_style=path_style)
        return client_type, uploadClient, downloadClient


if __name__ == "__main__":
    pytest.main(["-v", 'test_rsa_crypto_client.py::TestRSACTRCryptoClient',
                 'test_rsa_crypto_client.py::TestRSACTRCryptoClientWithSha256'])
