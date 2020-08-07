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
 This sample demonstrates how to do common operations in temporary signature way
 on OBS using the OBS SDK for Python.
"""

from __future__ import print_function
import sys
from obs import ObsClient, CorsRule, const
from obs.convertor import Convertor
from obs.util import base64_encode, md5_encode

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'
objectKey = 'my-obs-object-key-demo'

IS_PYTHON2 = sys.version_info.major == 2 or sys.version < '3'

if IS_PYTHON2:
    from urlparse import urlparse
    import httplib
else:
    import http.client as httplib
    from urllib.parse import urlparse

# Constructs a obs client instance with your account for accessing OBS
obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server, is_secure=False, signature='obs')


def doAction(msg, method, url, headers=None, content=None):
    print(msg + ' using temporary signature url:')
    print('\t' + url)

    url = urlparse(url)

    if headers is None:
        headers = {}

    conn = httplib.HTTPConnection(url.hostname, url.port)
    path = url.path + '?' + url.query
    conn.request(method, path, headers=headers)

    if content is not None:
        if not IS_PYTHON2 and not isinstance(content, bytes):
            content = content.encode('UTF-8')
        conn.send(content)

    result = conn.getresponse(True) if const.IS_PYTHON2 else conn.getresponse()
    status = result.status
    responseContent = result.read()
    if status < 300:
        print(msg + ' using temporary signature url successfully.')
    else:
        print(msg + ' using temporary signature url failed!!')

    if responseContent:
        print('\tresponseContent:')
        print('\t%s' % responseContent)
    conn.close()
    print('\n')


# Create bucket
method = 'PUT'
location = 'your-location'
locationEle = 'Location'
content = '<CreateBucketConfiguration><%s>%s</%s></CreateBucketConfiguration>' % (locationEle, location, locationEle)
headers = {'Content-Length': str(len(content))}
res = obsClient.createSignedUrl(method, bucketName, expires=3600, headers=headers)
doAction('Creating bucket', method, res['signedUrl'], res['actualSignedRequestHeaders'], content)

# Set/Get/Delete bucket cors
method = 'PUT'
cors1 = CorsRule(id='rule1', allowedMethod=['PUT', 'HEAD', 'GET'],
                 allowedOrigin=['http://www.a.com', 'http://www.b.com'], allowedHeader=['Authorization1'],
                 maxAgeSecond=100, exposeHeader=['x-obs-test1'])
cors2 = CorsRule(id='rule2', allowedMethod=['PUT', 'HEAD', 'GET'],
                 allowedOrigin=['http://www.c.com', 'http://www.d.com'], allowedHeader=['Authorization2'],
                 maxAgeSecond=200, exposeHeader=['x-obs-test2'])
corsList = [cors1, cors2]

content = Convertor('').trans_cors_rules(corsList)
headers = {'Content-Type': 'application/xml', 'Content-Length': str(len(content)),
           'Content-MD5': base64_encode(md5_encode(content))}
res = obsClient.createSignedUrl(method, bucketName, specialParam='cors', headers=headers)
doAction('Setting bucket cors', method, res['signedUrl'], res['actualSignedRequestHeaders'], content)

method = 'GET'
res = obsClient.createSignedUrl(method, bucketName, specialParam='cors')
doAction('Getting bucket cors', method, res['signedUrl'], res['actualSignedRequestHeaders'])

method = 'DELETE'
res = obsClient.createSignedUrl(method, bucketName, specialParam='cors')
doAction('Deleting bucket cors', method, res['signedUrl'], res['actualSignedRequestHeaders'])

# Put object
method = 'PUT'
content = 'Hello OBS'
headers = {'Content-Length': str(len(content))}
res = obsClient.createSignedUrl(method, bucketName, objectKey, headers=headers)
doAction('Creating object', method, res['signedUrl'], res['actualSignedRequestHeaders'], content)

# Get object
method = 'GET'
res = obsClient.createSignedUrl(method, bucketName, objectKey)
doAction('Getting object', method, res['signedUrl'], res['actualSignedRequestHeaders'])

# Set/Get object acl
method = 'PUT'
headers = {'x-obs-acl': 'public-read'}
res = obsClient.createSignedUrl(method, bucketName, objectKey, specialParam='acl', headers=headers)
doAction('Setting object acl', method, res['signedUrl'], res['actualSignedRequestHeaders'])

method = 'GET'
res = obsClient.createSignedUrl(method, bucketName, objectKey, specialParam='acl')
doAction('Getting object acl', method, res['signedUrl'], res['actualSignedRequestHeaders'])

# Delete object
method = 'DELETE'
res = obsClient.createSignedUrl(method, bucketName, objectKey)
doAction('Deleting object', method, res['signedUrl'], res['actualSignedRequestHeaders'])

# Delete bucket
method = 'DELETE'
res = obsClient.createSignedUrl(method, bucketName, expires=3600)
doAction('Deleting bucket', method, res['signedUrl'], res['actualSignedRequestHeaders'])
