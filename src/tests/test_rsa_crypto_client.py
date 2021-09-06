# coding:utf-8
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
