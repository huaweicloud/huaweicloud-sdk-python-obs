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
 This sample demonstrates how to use IdToken (OIDC Token) federated authentication
 to access OBS using the OBS SDK for Python.

 Three initialization modes are shown:
   1. CCE default path mode  — zero-config in CCE Pod
   2. Direct parameter mode  — pass id_token, idp_id, etc. directly
   3. Config file mode       — load parameters from a JSON config file

 Prerequisites:
   - An IdP (Identity Provider) has been configured in Huawei Cloud IAM
   - A valid ID Token (JWT) is available
"""

from __future__ import print_function
from obs import ObsClient, IdTokenCredentialsProvider

# ============================================================================
# Mode 1: CCE default path mode
# ============================================================================
# In a CCE Pod, the OIDC Token is automatically mounted at
# /var/run/secrets/tokens/oidc-token. No need to specify oidc_token_file.
# Only idp_id and project_name (or project_id) are required.

def demo_cce_default_path():
    """
    CCE zero-config mode: oidc-token is read from the default path
    /var/run/secrets/tokens/oidc-token automatically.
    """
    print('=' * 60)
    print('Mode 1: CCE default path mode')
    print('=' * 60)

    obsClient = ObsClient(
        id_token_credentials_provider=IdTokenCredentialsProvider(),
        server='obs.cn-north-4.myhuaweicloud.com'
    )

    try:
        resp = obsClient.listBuckets()
        if resp.status < 300:
            print('List buckets succeeded:')
            for bucket in resp.body:
                print('\t' + bucket.name)
        else:
            print('List buckets failed, status:', resp.status)
    finally:
        obsClient.close()


# ============================================================================
# Mode 2: Direct parameter mode
# ============================================================================
# Pass id_token string and all parameters directly to the constructor.
# Suitable for scenarios where the token is obtained from environment
# variables or other sources.

def demo_direct_parameters():
    """
    Direct parameter mode: pass id_token, idp_id, project_name, etc. directly.
    """
    print('=' * 60)
    print('Mode 2: Direct parameter mode')
    print('=' * 60)

    obsClient = ObsClient(
        id_token_credentials_provider=IdTokenCredentialsProvider(
            id_token='eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...',  # Required: JWT format ID Token
            idp_id='your-idp-id',                                  # Required: Identity Provider ID
            project_name='cn-north-4',                             # Required: project name or project_id
            credential_expires_seconds=3600,                       # Optional: token validity (900-86400s), default 86400
            refresh_before_seconds=300,                            # Optional: refresh before expiry (s), default 300
        ),
        server='obs.cn-north-4.myhuaweicloud.com'
    )

    try:
        resp = obsClient.listBuckets()
        if resp.status < 300:
            print('List buckets succeeded:')
            for bucket in resp.body:
                print('\t' + bucket.name)
        else:
            print('List buckets failed, status:', resp.status)
    finally:
        obsClient.close()


# ============================================================================
# Mode 3: Config file mode
# ============================================================================
# Load parameters from a JSON config file. The config file can contain
# id_token, oidc_token_file, idp_id, project_name, domain_id, etc.
# Constructor parameters take priority over config file values.

def demo_config_file():
    """
    Config file mode: load parameters from a JSON config file.

    Example config file (id_token_config.json):
    {
        "oidc_token_file": "/var/run/secrets/tokens/oidc-token",
        "idp_id": "your-idp-id",
        "project_name": "cn-north-4",
        "domain_id": "your-domain-id",
        "iam_endpoint": "https://iam.cn-north-4.myhuaweicloud.com",
        "credential_expires_seconds": 3600,
        "refresh_before_seconds": 300
    }

    Alternatively, use "id_token" instead of "oidc_token_file" in the config:
    {
        "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
        "idp_id": "your-idp-id",
        "project_name": "cn-north-4"
    }
    """
    print('=' * 60)
    print('Mode 3: Config file mode')
    print('=' * 60)

    # Option A: pass config file path as string to ObsClient directly
    obsClient = ObsClient(
        id_token_credentials_provider='id_token_config.json',
        server='obs.cn-north-4.myhuaweicloud.com'
    )

    try:
        resp = obsClient.listBuckets()
        if resp.status < 300:
            print('List buckets succeeded:')
            for bucket in resp.body:
                print('\t' + bucket.name)
        else:
            print('List buckets failed, status:', resp.status)
    finally:
        obsClient.close()


# ============================================================================
# Advanced: Credential refresh
# ============================================================================

def demo_credential_refresh():
    """
    Demonstrates manual and automatic credential refresh.
    """
    print('=' * 60)
    print('Advanced: Credential refresh')
    print('=' * 60)

    provider = IdTokenCredentialsProvider(
        config_file='id_token_config.json',
        credential_expires_seconds=900,     # Minimum: 15 minutes
        refresh_before_seconds=60,          # Refresh 60s before expiry
    )

    obsClient = ObsClient(
        id_token_credentials_provider=provider,
        server='obs.cn-north-4.myhuaweicloud.com'
    )

    try:
        # Get initial credentials
        cred = provider.get_credentials()
        print('Initial accessKey:', cred.get('accessKey')[:8] + '...')

        # Manual refresh — clears cache and fetches new credentials on next call
        provider.refresh()
        cred = provider.get_credentials()
        print('After refresh, accessKey:', cred.get('accessKey')[:8] + '...')

        # Automatic refresh — when credentials approach expiry,
        # get_credentials() automatically fetches new ones
        resp = obsClient.listBuckets()
        if resp.status < 300:
            print('List buckets succeeded after refresh')
    finally:
        obsClient.close()


if __name__ == '__main__':
    # Uncomment the demo you want to run:

    demo_cce_default_path()
    demo_direct_parameters()
    demo_config_file()
    demo_credential_refresh()

    print('Please uncomment one of the demo functions above to run.')
