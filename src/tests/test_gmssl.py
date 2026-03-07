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

import ssl
import time

import pytest
from obs import (
    ObsClient,
    CustomDomainConfiguration,
    # ClientVerify
)
from conftest import test_config


bucket_name = "ztw-test11"
right_domain_name = 'ztw.test.com'
right_name = 'aaa'
right_certificate_id = '1234512345123450'
server_cert = '/root/tmp/server.pem'
server_key = '/root/tmp/server.key.pem'
ca_cert = '/root/tmp/sm2.ca.pem'
client_sign_cert = '/root/tmp/sm2.sig.pem'
client_sign_key = '/root/tmp/sm2.sig.key.pem'
client_key_password = '456'
client_enc_cert = '/root/tmp/sm2.enc.pem'
client_enc_key = '/root/tmp/sm2.enc.key.pem'
client_enc_key2 = '/root/tmp/sm2.enc2.key.pem'
client_enc_key_password = '123'
client_wrong_sign_cert = '/root/tmp/wrong.sig.pem'
client_wrong_sign_key = '/root/tmp/wrong.sig.key.pem'




class TestGMSSL(object):

    def get_client(self):

        path_style = True if test_config["auth_type"] == "v2" else False
        obsClient = ObsClient(
            access_key_id=test_config["ak"],
            secret_access_key=test_config["sk"],
            server=test_config["endpoint"],
            is_signature_negotiation=False,
            path_style=path_style,
        )

        return obsClient

    def test_gmssl_algorithm_suite(self):
        """
            1.使用国密套件ECC-SM4-SM3初始化sdk客户端
            2.获取桶列表
            3.使用国密套件ECDHE-SM4-SM3初始化sdk客户端
            4.获取桶列表
            5.上传对象B到桶A中
            6.下载对象B
        """
        return
        obs_client = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                               server='ztw.test.com', is_cname=True, is_use_gmssl=True,
                               custom_ciphers='ECDHE-SM4-SM3',
                               )
        resp = obs_client.listBuckets()
        assert resp.status == 200
        obs_client = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                               server='ztw.test.com', is_cname=True, is_use_gmssl=True,
                               custom_ciphers='ECDHE-SM4-SM3',
                               )
        resp = obs_client.listBuckets()
        assert resp.status == 200
        resp = obs_client.putContent('ztw-test11', 'objectKey', content='Hellow OBS')
        assert resp.status == 200
        resp = obs_client.getObject('ztw-test11', 'objectKey')
        assert resp.status == 200

    def test_gmssl_verify_001(self):
        return

        """
            1.初始化客户端时指定ssl_verify，并配置正确的证书路径
            2.获取桶列表
        """
        obs_client = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                               server='ztw.test.com', is_cname=True, is_use_gmssl=True, ssl_verify=ca_cert
                               )
        resp = obs_client.listBuckets()
        assert resp.status == 200

    def test_gmssl_verify_002(self):
        return

        """
            1.初始化客户端时指定ssl_verify，并配置错误的国密证书的证书路径
            2.获取桶列表
        """
        obs_client = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                               server='ztw.test.com', is_cname=True, is_use_gmssl=True, ssl_verify='./wrong_cert'
                               )
        try:
            obs_client.listBuckets()
        except ssl.SSLCertVerificationError as e:
            assert e == '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1082)'

    def test_gmssl_verify_003(self):
        return

        """
            1.初始化客户端时指定ssl_verify，并配置正确的服务端证书路径，并通过client_verify参数指定客户端国密证书和密钥的路径
            2.获取桶列表
            3.初始化客户端时指定ssl_verify，并配置正确的服务端证书路径，并通过client_verify参数指定客户端国密证书、加密密钥和密钥密码的路径
            4.获取桶列表
        """
        client_verify = ClientVerify(clientCert=client_sign_cert, clientKey=client_sign_key)

        obs_client = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                               server='ztw.test.com', is_cname=True, is_use_gmssl=True, ssl_verify=ca_cert,
                               client_verify=client_verify
                               )
        resp = obs_client.listBuckets()
        assert resp.status == 200
        client_verify = ClientVerify(clientCert=client_sign_cert, clientKey=client_sign_key,
                                     clientKeyPassword=client_key_password)

        obs_client = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                               server='ztw.test.com', is_cname=True, is_use_gmssl=True, ssl_verify=ca_cert,
                               client_verify=client_verify
                               )
        resp = obs_client.listBuckets()
        assert resp.status == 200

    def test_gmssl_verify_004(self):
        return

        """
            1.初始化客户端时指定ssl_verify，并配置正确服务端证书路径，并通过client_verify参数指定错误的客户端国密证书路径和正确密钥的路径
            2.获取桶列表
            3.初始化客户端时指定ssl_verify，并配置正确服务端证书路径，并通过client_verify参数指定正确客户端国密证书和错误密钥的路径
            4.获取桶列表
        """
        client_verify = ClientVerify(clientCert=client_wrong_sign_cert, clientKey=client_sign_key)

        obs_client = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                               server='ztw.test.com', is_cname=True, is_use_gmssl=True, ssl_verify=ca_cert,
                               client_verify=client_verify
                               )
        try:
            obs_client.listBuckets()
        except FileNotFoundError as e:
            assert e == '[Errno 2] No such file or directory'

        client_verify = ClientVerify(clientCert=client_sign_cert, clientKey=client_wrong_sign_key)
        obs_client = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                               server='ztw.test.com', is_cname=True, is_use_gmssl=True, ssl_verify=ca_cert,
                               client_verify=client_verify
                               )
        try:
            obs_client.listBuckets()
        except FileNotFoundError as e:
            assert e == '[Errno 2] No such file or directory'

    def test_put_custom_domain_with_gm_001(self):
        return

        """
            1、设置桶自定义域名www.aaa.com并配置国密证书，Certificate传入国密证书、PrivateKey传入国密证书密钥，CertificateType设置为server_sm（服务端国密证书），ENCCertificate传入国密证书的加密证书，ENCPrivateKey传入国密证书的加密私钥
            2、查询桶A的自定义域名
            3、设置桶自定义域名www.aaa.com并配置客户端证书，Certificate传入客户端证书，CertificateType设置为client
            4、查询桶A的自定义域名
            5、设置桶自定义域名www.aaa.com并配置非国密服务端证书，Certificate传入服务端证书、PrivateKey传入服务端证书密钥，CertificateType设置为server
            6、查询桶A的自定义域名
            7、设置桶自定义域名www.aaa.com并删除客户端证书，CertificateType设置为client,DeleteCertificate设置为true
            8、查询桶A的自定义域名
        """
        domain_name = 'www.aaa.com'
        obs_client = self.get_client()
        params = {
            "name": "server_sm_cert",
            "certificateId": "cert-1",
            "certificate": client_sign_cert,
            "privateKey": client_sign_key,
            "certificateType": "server_sm",
            "encCertificate": client_enc_cert,
            "encPrivateKey": client_enc_key,
            "deleteCertificate": False,
        }
        certificate_info = CustomDomainConfiguration(**params)
        resp = obs_client.setBucketCustomDomain(bucket_name, domain_name, certificate_info)
        assert resp.status == 200
        get_result = obs_client.getBucketCustomDomain(bucket_name)
        assert get_result.status == 200
        for domain in get_result.body.domains:
            if domain.domain_name == domain_name:
                assert domain.certificateType == 'server_sm'

        params = {
            "name": "client_cert",
            "certificateId": "cert-2",
            "certificate": ca_cert,
            "certificateType": "client",
            "deleteCertificate": False,
        }
        certificate_info = CustomDomainConfiguration(**params)
        resp = obs_client.setBucketCustomDomain(bucket_name, domain_name, certificate_info)
        assert resp.status == 200
        get_result = obs_client.getBucketCustomDomain(bucket_name)
        assert get_result.status == 200
        for domain in get_result.body.domains:
            if domain.domain_name == domain_name:
                assert domain.certificateType == 'client'

        params = {
            "name": "server_cert",
            "certificateId": "cert-123",
            "certificate": server_cert,
            "privateKey": server_key,
            "certificateType": "server",
            "deleteCertificate": False,
        }
        certificate_info = CustomDomainConfiguration(**params)
        resp = obs_client.setBucketCustomDomain(bucket_name, domain_name, certificate_info)
        assert resp.status == 200
        get_result = obs_client.getBucketCustomDomain(bucket_name)
        assert get_result.status == 200
        for domain in get_result.body.domains:
            if domain.domain_name == domain_name:
                assert domain.certificateType == 'server'

        params = {
            "certificateType": "client",
            "deleteCertificate": True,
        }
        certificate_info = CustomDomainConfiguration(**params)
        resp = obs_client.setBucketCustomDomain(bucket_name, domain_name, certificate_info)
        assert resp.status == 200
        get_result = obs_client.getBucketCustomDomain(bucket_name)
        assert get_result.status == 200
        for domain in get_result.body.domains:
            if domain.domain_name == domain_name:
                assert domain.certificateType == 'client'

    def test_put_custom_domain_with_gm_002(self):
        return

        """
            1、设置桶自定义域名www.aaa.com并配置国密证书，Certificate传入国密证书、PrivateKey传入国密证书密钥，CertificateType设置为server_sm（服务端国密证书），ENCCertificate传入国密证书的加密证书，ENCPrivateKey传入国密证书的加密私钥（加密后的密钥）
            2、设置桶自定义域名www.aaa.com并配置客户端证书，Certificate传入客户端证书，CertificateType设置为client
            3、设置桶自定义域名www.aaa.com并配置国密证书，Certificate传入国密证书、PrivateKey传入国密证书密钥，CertificateType设置为server_sm（服务端国密证书），ENCCertificate传入国密证书的加密证书，ENCPrivateKey传入国密证书的加密私钥
            4、设置桶自定义域名www.aaa.com并配置客户端证书，Certificate传入客户端证书，CertificateType设置为client
            5、设置桶自定义域名www.aaa.com并删除服务端端证书，CertificateType设置为server_sm,DeleteCertificate设置为true
        """
        domain_name = 'www.aaa.com'
        obs_client = self.get_client()
        params = {
            "name": "server_sm_cert",
            "certificateId": "cert-1",
            "certificate": client_sign_cert,
            "privateKey": client_sign_key,
            "certificateType": "server_sm",
            "encCertificate": client_enc_cert,
            "encPrivateKey": client_enc_key2,
            "deleteCertificate": False,
        }
        certificate_info = CustomDomainConfiguration(**params)
        resp = obs_client.setBucketCustomDomain(bucket_name, domain_name, certificate_info)
        assert resp.status == 400

        params = {
            "name": "client_cert",
            "certificateId": "cert-2",
            "certificate": ca_cert,
            "certificateType": "client",
            "deleteCertificate": False,
        }
        certificate_info = CustomDomainConfiguration(**params)
        resp = obs_client.setBucketCustomDomain(bucket_name, domain_name, certificate_info)
        assert resp.status == 400

        params = {
            "name": "server_sm_cert",
            "certificateId": "cert-1",
            "certificate": client_sign_cert,
            "privateKey": client_sign_key,
            "certificateType": "server_sm",
            "encCertificate": client_enc_cert,
            "encPrivateKey": client_enc_key,
            "deleteCertificate": False,
        }
        certificate_info = CustomDomainConfiguration(**params)
        resp = obs_client.setBucketCustomDomain(bucket_name, domain_name, certificate_info)
        assert resp.status == 200
        get_result = obs_client.getBucketCustomDomain(bucket_name)
        assert get_result.status == 200
        for domain in get_result.body.domains:
            if domain.domain_name == domain_name:
                assert domain.certificateType == 'server_sm'

        params = {
            "name": "client_cert",
            "certificateId": "cert-2",
            "certificate": ca_cert,
            "certificateType": "client",
            "deleteCertificate": False,
        }
        certificate_info = CustomDomainConfiguration(**params)
        resp = obs_client.setBucketCustomDomain(bucket_name, domain_name, certificate_info)
        assert resp.status == 200
        get_result = obs_client.getBucketCustomDomain(bucket_name)
        assert get_result.status == 200
        for domain in get_result.body.domains:
            if domain.domain_name == domain_name:
                assert domain.certificateType == 'client'

        params = {
            "certificateType": "server_sm",
            "deleteCertificate": True,
        }
        certificate_info = CustomDomainConfiguration(**params)
        resp = obs_client.setBucketCustomDomain(bucket_name, domain_name, certificate_info)
        assert resp.status == 400

    def test_gmssl_performance_001(self):
        return

        """
            1、使用国密算法上传100MB对象
        """

        obs_client = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                               server='ztw.test.com', is_cname=True, is_use_gmssl=True)
        objectKey = 'File_100MB'
        file_path = './File_100MB'
        start = time.time()
        obs_client.putFile(bucket_name, objectKey, file_path)
        end = time.time()
        cost = end - start
        assert cost <= 5

    def test_gmssl_performance_002(self):
        return

        """
            1、使用国密算法上传100MB对象
        """

        obs_client = ObsClient(access_key_id=test_config["ak"], secret_access_key=test_config["sk"],
                               server='ztw.test.com', is_cname=True, is_use_gmssl=True)
        objectKey = 'File_100MB'
        file_path = './File_100MB_d'
        start = time.time()
        obs_client.getObject(bucket_name, objectKey, downloadPath=file_path)
        end = time.time()
        cost = end - start
        assert cost <= 5


