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

import io
import json
import os
import random
import time
from datetime import datetime

import obs.scheduler as Scheduler
import pytest

# import conftest
from obs import (
    ObsClient,
)


def read_env_info():
    with open(os.path.join(os.getcwd(), "test_config.json"), "r") as f:
        return json.loads(f.read())


test_config = read_env_info()


class TestShadowToken(object):
    def get_client(self):

        path_style = True if test_config["auth_type"] == "v2" else False
        obsClient = ObsClient(
            access_key_id=test_config["ak"],
            secret_access_key=test_config["sk"],
            server=test_config["server"],
            is_signature_negotiation=False,
            path_style=path_style,
        )

        return obsClient

    def test_get_x_auth_token(self):
        obsclient = self.get_client()
        resp = Scheduler.get_X_Auth_token(
            name=test_config["auth_name"],
            password=test_config["auth_password"],
            domain=test_config["auth_domain"],
            scope=test_config["scope"],
            url=test_config["login_url"],
        )
        assert len(resp.get("id")) > 0

    def test_set_shadow_token(self):
        obsclient = self.get_client()
        resp = Scheduler.refresh_shadow_tokens(
            url=test_config["security_token_url"],
            endpoint=test_config["scope"],
        )
        assert len(resp.get("securitytoken")) > 0

    def test_get_shadow_token(self):
        obsclient = self.get_client()
        resp = Scheduler.get_from_cache("shadow_tokens")
        assert len(resp["security_token"]) != 0

    def test_shadow_obs_client(self):
        obsclient = self.get_client()

        shadow_client = obsclient.get_shadow_client()
        assert shadow_client != None

    def test_list_bucket_with_shadow_obs(self):
        obsclient = self.get_client()
        shadow_obsClient = obsclient.get_shadow_client()
        resp = shadow_obsClient.listBuckets()

        assert resp.status < 300

    def test_list_bucket(self):
        obsclient = self.get_client()
        resp = obsclient.listBuckets()

        assert resp.status < 300
