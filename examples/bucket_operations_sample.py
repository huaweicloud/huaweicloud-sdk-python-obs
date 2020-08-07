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
  This sample demonstrates how to do bucket-related operations
  (such as do bucket ACL/CORS/Lifecycle/Logging/Website/Location/Tagging/OPTIONS)
  on OBS using the OBS SDK for Python.
"""

from __future__ import print_function
from obs import ObsClient, Rule, Expiration, DateTime, NoncurrentVersionExpiration, WebsiteConfiguration, \
    IndexDocument, ErrorDocument, CorsRule, Options, Lifecycle, Logging, TagInfo

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'

bucketName = 'my-obs-bucket-demo'

# Constructs a obs client instance with your account for accessing OBS
obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)

bucketClient = obsClient.bucketClient(bucketName)


def createBucket():
    #     resp = obsClient.createBucket(bucketName)
    resp = bucketClient.createBucket()
    if resp.status < 300:
        print('Create bucket:' + bucketName + ' successfully!\n')
    else:
        print(resp.errorCode)


def getBucketLocation():
    #     resp = obsClient.getBucketLocation(bucketName)
    resp = bucketClient.getBucketLocation()
    if resp.status < 300:
        print('Getting bucket location ' + str(resp.body) + ' \n')
    else:
        print(resp.errorCode)


def getBucketStorageInfo():
    #     resp = obsClient.getBucketStorageInfo(bucketName)
    resp = bucketClient.getBucketStorageInfo()
    if resp.status < 300:
        print('Getting bucket storageInfo ' + str(resp.body) + ' \n')
    else:
        print(resp.errorCode)


def doBucketQuotaOperation():
    # Set bucket quota to 1GB
    #     obsClient.setBucketQuota(bucketName, 1024 * 1024 * 1024)
    bucketClient.setBucketQuota(1024 * 1024 * 1024)
    #     resp = obsClient.getBucketQuota(bucketName)
    resp = bucketClient.getBucketQuota()

    print('Getting bucket quota ' + str(resp.body) + ' \n')


def doBucketVersioningOperation():
    #     print('Getting bucket versioning config ' + str(obsClient.getBucketVersioning(bucketName).body) + ' \n')
    print('Getting bucket versioning config ' + str(bucketClient.getBucketVersioning().body) + ' \n')
    # Enable bucket versioning
    #     obsClient.setBucketVersioning(bucketName, 'Enabled')
    bucketClient.setBucketVersioning('Enabled')
    print('Current bucket versioning config ' + str(obsClient.getBucketVersioning(bucketName).body) + ' \n')

    # Suspend bucket versioning
    #     obsClient.setBucketVersioning(bucketName, 'Suspended')
    bucketClient.setBucketVersioning('Suspended')
    print('Current bucket versioning config ' + str(obsClient.getBucketVersioning(bucketName).body) + ' \n')


def doBucketAclOperation():
    print('Setting bucket ACL to public-read \n')
    #     obsClient.setBucketAcl(bucketName, aclControl='public-read')
    bucketClient.setBucketAcl(aclControl='public-read')

    #     print('Getting bucket ACL ' + str(obsClient.getBucketAcl(bucketName).body) + ' \n')
    print('Getting bucket ACL ' + str(bucketClient.getBucketAcl().body) + ' \n')
    print('Setting bucket ACL to private \n')
    obsClient.setBucketAcl(bucketName, None, 'private')

    print('Getting bucket ACL ' + str(obsClient.getBucketAcl(bucketName).body) + ' \n')


def doBucketCorsOperation():
    print('Setting bucket CORS\n')
    cors1 = CorsRule(id='rule1', allowedMethod=['PUT', 'HEAD', 'GET'],
                     allowedOrigin=['http://www.a.com', 'http://www.b.com'], allowedHeader=['Authorization1'],
                     maxAgeSecond=100, exposeHeader=['x-obs-test1'])
    cors2 = CorsRule(id='rule2', allowedMethod=['PUT', 'HEAD', 'GET'],
                     allowedOrigin=['http://www.c.com', 'http://www.d.com'], allowedHeader=['Authorization2'],
                     maxAgeSecond=200, exposeHeader=['x-obs-test2'])

    corsList = [cors1, cors2]

    #     obsClient.setBucketCors(bucketName, corsList)
    bucketClient.setBucketCors(corsList)

    #     print('Getting bucket CORS ' + str(obsClient.getBucketCors(bucketName).body) + '\n')
    print('Getting bucket CORS ' + str(bucketClient.getBucketCors().body) + '\n')


def optionsBucket():
    print('Options bucket \n')
    option = Options(origin='http://www.a.com', accessControlRequestMethods=['GET', 'PUT'],
                     accessControlRequestHeaders=['Authorization1'])
    #     print('\t' + str(obsClient.optionsBucket(bucketName, option).body))
    print('\t' + str(bucketClient.optionsBucket(option).body))


def getBucketMetadata():
    print('Getting bucket metadata\n')

    #     resp = obsClient.getBucketMetadata(bucketName, origin='http://www.b.com', requestHeaders='Authorization1')
    resp = bucketClient.getBucketMetadata(origin='http://www.b.com', requestHeaders='Authorization1')
    print('storageClass:', resp.body.storageClass)
    print('accessContorlAllowOrigin:', resp.body.accessContorlAllowOrigin)
    print('accessContorlMaxAge:', resp.body.accessContorlMaxAge)
    print('accessContorlExposeHeaders:', resp.body.accessContorlExposeHeaders)
    print('accessContorlAllowMethods:', resp.body.accessContorlAllowMethods)
    print('accessContorlAllowHeaders:', resp.body.accessContorlAllowHeaders)

    print('Deleting bucket CORS\n')
    #     obsClient.deleteBucketCors(bucketName)
    resp = bucketClient.deleteBucketCors()
    print('status' + str(resp.status))


def doBucketLifycleOperation():
    print('Setting bucket lifecycle\n')

    rule1 = Rule(id='delete obsoleted files', prefix='obsoleted/', status='Enabled', expiration=Expiration(days=10))
    rule2 = Rule(id='delete temporary files', prefix='temporary/', status='Enabled',
                 expiration=Expiration(date=DateTime(2017, 12, 31)))
    rule3 = Rule(id='delete temp files', prefix='temp/', status='Enabled',
                 noncurrentVersionExpiration=NoncurrentVersionExpiration(noncurrentDays=10))

    Llifecycle = Lifecycle(rule=[rule1, rule2, rule3])
    #     obsClient.setBucketLifecycle(bucketName, Llifecycle)
    bucketClient.setBucketLifecycle(Llifecycle)

    print('Getting bucket lifecycle:')
    #     resp = obsClient.getBucketLifecycle(bucketName)
    resp = bucketClient.getBucketLifecycle()
    print('\t' + str(resp.body) + '\n')

    print('Deleting bucket lifecyle\n')
    #     obsClient.deleteBucketLifecycle(bucketName)
    bucketClient.deleteBucketLifecycle()


def doBucketLoggingOperation():
    print('Setting bucket logging\n')

    # obsClient.setBucketLogging(bucketName, Logging(targetBucket=bucketName,
    # targetPrefix='log-', agency='your agency'))
    bucketClient.setBucketLogging(Logging(targetBucket=bucketName, targetPrefix='log-', agency='your agency'))

    print('Getting bucket logging:')
    #     print('\t' + str(obsClient.getBucketLogging(bucketName).body) + '\n')
    print('\t' + str(bucketClient.getBucketLogging().body) + '\n')

    print('Deleting bucket logging\n')
    obsClient.setBucketLogging(bucketName, Logging())

    print('Getting bucket logging:')
    print('\t' + str(obsClient.getBucketLogging(bucketName).body) + '\n')


def doBucketWebsiteOperation():
    print('Setting bucket website\n')
    Lwebsite = WebsiteConfiguration(indexDocument=IndexDocument(suffix='index.html'),
                                    errorDocument=ErrorDocument(key='error.html'))
    #     obsClient.setBucketWebsite(bucketName, Lwebsite)
    bucketClient.setBucketWebsite(Lwebsite)

    print('Getting bucket website:')
    #     print('\t' + str(obsClient.getBucketWebsite(bucketName).body) + '\n')
    print('\t' + str(bucketClient.getBucketWebsite().body) + '\n')
    print('Deleting bucket website\n')
    #     obsClient.deleteBucketWebsite(bucketName)
    bucketClient.deleteBucketWebsite()


def doBucketTaggingOperation():
    print('Setting bucket tagging\n')
    tagInfo = TagInfo()
    tagInfo.addTag('key1', 'value1').addTag('key2', 'value2')
    #     resp = obsClient.setBucketTagging(bucketName, tagInfo)
    resp = bucketClient.setBucketTagging(tagInfo)

    if resp.status < 300:
        print('Getting bucket tagging\n')
        #         resp = obsClient.getBucketTagging(bucketName)
        resp = bucketClient.getBucketTagging()
        for item in resp.body.tagSet:
            print('\t' + item.key + ':' + item.value + '\n')

        print('Deleting bucket tagging\n')
        #         obsClient.deleteBucketTagging(bucketName)
        bucketClient.deleteBucketTagging()
    else:
        print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


def deleteBucket():
    print('Deleting bucket ' + bucketName + '\n')
    #     resp = obsClient.deleteBucket(bucketName)
    resp = bucketClient.deleteBucket()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# Put bucket operation
createBucket()

# Get bucket location operation
getBucketLocation()

# Get bucket storageInfo operation
getBucketStorageInfo()

# Put/Get bucket quota operations
doBucketQuotaOperation()

# Put/Get bucket versioning operations
doBucketVersioningOperation()

# Put/Get bucket acl operations
doBucketAclOperation()

# Put/Get/Delete bucket cors operations
doBucketCorsOperation()

# Options bucket operation
optionsBucket()

# Get bucket metadata operation
getBucketMetadata()

# Put/Get/Delete bucket lifecycle operations
doBucketLifycleOperation()

# Put/Get/Delete bucket logging operations
doBucketLoggingOperation()

# Put/Get/Delete bucket website operations
doBucketWebsiteOperation()

# Put/Get/Delete bucket tagging operations
doBucketTaggingOperation()

# Delete bucket operation
deleteBucket()
