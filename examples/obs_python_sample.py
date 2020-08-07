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

from __future__ import print_function
from obs import ObsClient, LogConf, CreateBucketHeader, Grantee, Grant, StorageClass, Owner, Group, Permission, ACL
from obs import Versions, Expiration, DateTime, NoncurrentVersionExpiration, Rule, Lifecycle, RedirectAllRequestTo
from obs import IndexDocument, ErrorDocument, Condition, Redirect, RoutingRule, WebsiteConfiguration, Logging, TagInfo
from obs import CorsRule, FilterRule, TopicConfiguration, EventType, Notification, ListMultipartUploadsRequest, Object
from obs import DeleteObjectsRequest, CompletePart, CompleteMultipartUploadRequest, PutObjectHeader, AppendObjectHeader
from obs import AppendObjectContent, GetObjectRequest, GetObjectHeader, RestoreTier, CopyObjectHeader

AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
server = 'https://your-endpoint'
bucketName = 'my-obs-bucket-demo'

# create ObsClient instance
obsClient = ObsClient(access_key_id=AK, secret_access_key=SK, server=server)
bucketClient = obsClient.bucketClient(bucketName)


# init log
def initLog():
    obsClient.initLog(LogConf('../log.conf'), 'obsclient')


# create bucket
def CreateBucket():
    headers = CreateBucketHeader(aclControl='public-read', storageClass=StorageClass.WARM)
    resp = bucketClient.createBucket(header=headers)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage,
          ',resHeader:', resp.header)


# delete bucket
def DeleteBucket():
    resp = bucketClient.deleteBucket()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage,
          ',resHeader:', resp.header)


# list buckets
def ListBuckets():
    resp = obsClient.listBuckets()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)

    listBucket = resp.body
    if listBucket:
        print('owner_id:', listBucket.owner.owner_id)
        i = 0
        for item in listBucket.buckets:
            print('buckets[', i, ']:')
            print('bucket_name:', item.name, ',create_date:', item.create_date)
            i += 1


# head bucket
def HeadBucket():
    resp = bucketClient.headBucket()
    if resp.status < 300:
        print('bucket exists')
    elif resp.status == 404:
        print('bucket does not exist')
    else:
        print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage,
              ',resHeader:', resp.header)


# get bucket metadata
def GetBucketMetadata():
    resp = bucketClient.getBucketMetadata(origin='www.example.com', requestHeaders='header1')
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('storageClass:', resp.body.storageClass)
        print('accessContorlAllowOrigin:', resp.body.accessContorlAllowOrigin)
        print('accessContorlMaxAge:', resp.body.accessContorlMaxAge)
        print('accessContorlExposeHeaders:', resp.body.accessContorlExposeHeaders)
        print('accessContorlAllowMethods:', resp.body.accessContorlAllowMethods)
        print('accessContorlAllowHeaders:', resp.body.accessContorlAllowHeaders)


# set bucket quota
def SetBucketQuota():
    resp = bucketClient.setBucketQuota(quota=1048576 * 600)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get bucket quota
def GetBucketQuota():
    resp = bucketClient.getBucketQuota()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('quota:', resp.body.quota)


# set bucket storagePolicy
def SetBucketStoragePolicy():
    resp = bucketClient.setBucketStoragePolicy(storageClass='STANDARD')
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get bucket storagePolicy
def GetBucketStoragePolicy():
    resp = bucketClient.getBucketStoragePolicy()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('storageClass:', resp.body.storageClass)


# get bucket storageinfo
def GetBucketStorageInfo():
    resp = bucketClient.getBucketStorageInfo()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('size:', resp.body.size, ',objectNumber:', resp.body.objectNumber)


# set bucket acl
def SetBucketAcl():
    Lowner = Owner(owner_id='ownerid')

    Lgrantee1 = Grantee(grantee_id='userid', group=None)
    Lgrantee2 = Grantee(group=Group.LOG_DELIVERY)

    Lgrant1 = Grant(grantee=Lgrantee1, permission=Permission.READ)
    Lgrant2 = Grant(grantee=Lgrantee2, permission=Permission.READ_ACP)
    Lgrant3 = Grant(grantee=Lgrantee2, permission=Permission.WRITE)
    Lgrants = [Lgrant1, Lgrant2, Lgrant3]

    Lacl = ACL(owner=Lowner, grants=Lgrants)

    resp = bucketClient.setBucketAcl(acl=Lacl)
    # resp = obsClient.setBucketAcl(bucketName=bucketName, aclControl='public-read-write')
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get bucket acl
def GetBucketAcl():
    resp = bucketClient.getBucketAcl()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('owner_id:', resp.body.owner.owner_id)
        i = 0
        for grant in resp.body.grants:
            print('grants[', i, ']:')
            print('permission:', grant.permission)
            print('grantee_id:', grant.grantee.grantee_id, ',group:', grant.grantee.group)
            i += 1


# set bucket policy
def SetBucketPolicy():
    LpolicyJSON = 'your policy'
    resp = bucketClient.setBucketPolicy(policyJSON=LpolicyJSON)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get bucket policy
def GetBucketPolicy():
    resp = bucketClient.getBucketPolicy()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('policyJSON:', resp.body)


# delete bucket policy
def DeleteBucketPolicy():
    resp = bucketClient.deleteBucketPolicy()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# set bucket versioning configuration
def SetBucketVersioning():
    resp = bucketClient.setBucketVersioning(status='Enabled')
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get bucket versioning configuration
def GetBucketVersioning():
    resp = bucketClient.getBucketVersioning()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    print('status:', resp.body)


# list versions
def ListVersions():
    lversion = Versions(prefix=None, key_marker=None, max_keys=10, delimiter=None, version_id_marker=None)
    resp = bucketClient.listVersions(version=lversion)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('name:', resp.body.head.name, ',prefix:', resp.body.head.prefix, ',keyMarker:', resp.body.head.keyMarker,
              ',maxKeys:', resp.body.head.maxKeys)
        print('nextKeyMarker:', resp.body.head.nextKeyMarker, ',nextVersionIdMarker:',
              resp.body.head.nextVersionIdMarker, ',versionIdMarker:', resp.body.head.versionIdMarker, ',isTruncated:',
              resp.body.head.isTruncated)
        i = 0
        for version in resp.body.versions:
            print('versions[', i, ']:')
            print('owner_id:', version.owner.owner_id)
            print('key:', version.key)
            print('lastModified:', version.lastModified, ',versionId:', version.versionId, ',etag:', version.etag,
                  ',storageClass:', version.storageClass, ',isLatest:', version.isLatest, ',size:', version.size)
            i += 1
        i = 0
        for marker in resp.body.markers:
            print('markers[', i, ']:')
            print('owner_id:', marker.owner.owner_id)
            print('key:', marker.key)
            print('key:', marker.key, ',versionId:', marker.versionId, ',isLatest:', marker.isLatest, ',lastModified:',
                  marker.lastModified)
            i += 1
        i = 0
        for prefix in resp.body.commonPrefixs:
            print('commonPrefixs[', i, ']')
            print('prefix:', prefix.prefix)
            i += 1


# list objects
def ListObjects():
    resp = bucketClient.listObjects(prefix=None, marker=None, max_keys=10, delimiter=None)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('name:', resp.body.name, ',prefix:', resp.body.prefix, ',marker:', resp.body.marker, ',max_keys:',
              resp.body.max_keys)
        print('delimiter:', resp.body.delimiter, ',is_truncated:', resp.body.is_truncated, ',next_marker:',
              resp.body.next_marker)
        i = 0
        for content in resp.body.contents:
            print('contents[', i, ']:')
            print('owner_id:', content.owner.owner_id)
            print('key:', content.key, ',lastModified:', content.lastModified, ',etag:', content.etag, ',size:',
                  content.size, ',storageClass:', content.storageClass)
            i += 1
        i = 0
        for prefix in resp.body.commonPrefixs:
            print('commonprefixs[', i, ']:')
            print('prefix:', prefix.prefix)
            i += 1


# set bucket lifecycle configuration
def SetBucketLifecycle():
    Lexpiration = Expiration(date=DateTime(2030, 6, 10), days=None)

    noncurrentVersionExpiration = NoncurrentVersionExpiration(noncurrentDays=60)

    Lrule = Rule(id='101', prefix='test', status='Enabled', expiration=Lexpiration,
                 noncurrentVersionExpiration=noncurrentVersionExpiration)

    Lrules = [Lrule]
    Llifecycle = Lifecycle(rule=Lrules)

    resp = bucketClient.setBucketLifecycle(lifecycle=Llifecycle)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get bucket lifecycle configuration
def GetBucketLifecycle():
    resp = bucketClient.getBucketLifecycle()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        i = 0
        for rule in resp.body.lifecycleConfig.rule:
            print('rule[', i, ']:')
            print('id:', rule.id, ',prefix:', rule.prefix, ',status:', rule.status)
            print('expiration:', rule.expiration)
            print('noncurrentVersionExpiration:', rule.noncurrentVersionExpiration)
            i += 1


# delete bucket lifecycle configuration
def DeleteBucketLifecycle():
    resp = bucketClient.deleteBucketLifecycle()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# set bucket website configuration
def SetBucketWebsite():
    Lweb = RedirectAllRequestTo(hostName='www.xxx.com', protocol='http')

    Lindex = IndexDocument(suffix='index.html')

    Lerr = ErrorDocument(key='error.html')

    Lcondition = Condition(keyPrefixEquals=None, httpErrorCodeReturnedEquals=404)

    Lredirect = Redirect(protocol='http', hostName=None, replaceKeyPrefixWith=None, replaceKeyWith='NotFound.html',
                         httpRedirectCode=None)

    Lrout = RoutingRule(condition=Lcondition, redirect=Lredirect)

    Lrouts = [Lrout, Lrout]
    Lwebsite = WebsiteConfiguration(redirectAllRequestTo=Lweb, indexDocument=Lindex, errorDocument=Lerr,
                                    routingRules=Lrouts)

    resp = bucketClient.setBucketWebsite(website=Lwebsite)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get bucket website configuration
def GetBucketWebsite():
    resp = bucketClient.getBucketWebsite()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        if resp.body.redirectAllRequestTo:
            print('redirectAllRequestTo.hostName:', resp.body.redirectAllRequestTo.hostName,
                  ',redirectAllRequestTo.Protocol:', resp.body.redirectAllRequestTo.protocol)
        if resp.body.indexDocument:
            print('indexDocument.suffix:', resp.body.indexDocument.suffix)
        if resp.body.errorDocument:
            print('errorDocument.key:', resp.body.errorDocument.key)
        if resp.body.routingRules:
            i = 0
            for rout in resp.body.routingRules:
                print('routingRule[', i, ']:')
                i += 1
                print('condition.keyPrefixEquals:', rout.condition.keyPrefixEquals,
                      ',condition.httpErrorCodeReturnedEquals:', rout.condition.httpErrorCodeReturnedEquals)
                print('redirect.protocol:', rout.redirect.protocol, ',redirect.hostName:', rout.redirect.hostName,
                      ',redirect.replaceKeyPrefixWith:', rout.redirect.replaceKeyPrefixWith,
                      ',redirect.replaceKeyWith:', rout.redirect.replaceKeyWith, ',redirect.httpRedirectCode:',
                      rout.redirect.httpRedirectCode)


# delete bucket website configuration
def DeleteBucketWebsite():
    resp = bucketClient.deleteBucketWebsite()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# set bucket logging configuration
def SetBucketLogging():
    Lgrantee = Grantee(grantee_id='userid', group=None)
    Lgrantee1 = Grantee(grantee_id=None, group=Group.ALL_USERS)

    Lgrant1 = Grant(grantee=Lgrantee, permission=Permission.WRITE)
    Lgrant2 = Grant(grantee=Lgrantee1, permission=Permission.READ)

    LgrantList = [Lgrant1, Lgrant2]
    Llog = Logging(targetBucket='bucket003', targetPrefix='log_1', targetGrants=LgrantList, agency='your agency')

    resp = bucketClient.setBucketLogging(logstatus=Llog)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get bucket logging configuration
def GetBucketLogging():
    resp = bucketClient.getBucketLogging()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('targetBucket:', resp.body.targetBucket, 'targetPrefix:', resp.body.targetPrefix)
        i = 0
        for grant in resp.body.targetGrants:
            print('targetGrant[', i, ']:')
            i += 1
            print('permission:', grant.permission, ',grantee.grantee_id:', grant.grantee.grantee_id, ',grantee.group:',
                  grant.grantee.group)


# get bucket location
def GetBucketLocation():
    resp = bucketClient.getBucketLocation()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('location:', resp.body.location)


# set bucket tagging
def SetBucketTagging():
    tagInfo = TagInfo()
    tagInfo.addTag('testKey1', 'testValue1').addTag('testKey2', 'testValue2')
    resp = bucketClient.setBucketTagging(tagInfo=tagInfo)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# delete bucket tagging
def DeleteBucketTagging():
    resp = bucketClient.deleteBucketTagging()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get bucket tagging
def GetBucketTagging():
    resp = bucketClient.getBucketTagging()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    for tag in resp.body.tagSet:
        print('{0}:{1}'.format(tag.key, tag.value))


# set bucket cors
def SetBucketCors():
    cors1 = CorsRule(id='101', allowedMethod=['PUT', 'POST', 'GET', 'DELETE'],
                     allowedOrigin=['www.xxx.com', 'www.x.com'], allowedHeader=['header-1', 'header-2'],
                     maxAgeSecond=100, exposeHeader=['head1'])
    cors2 = CorsRule(id='102', allowedMethod=['PUT', 'POST', 'GET', 'DELETE'],
                     allowedOrigin=['www.xxx.com', 'www.x.com'], allowedHeader=['header-1', 'header-2'],
                     maxAgeSecond=100, exposeHeader=['head1'])

    corsList = [cors1, cors2]

    resp = bucketClient.setBucketCors(corsList)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get bucket cors
def GetBucketCors():
    resp = bucketClient.getBucketCors()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body is not None:
        index = 1
        for rule in resp.body:
            print('corsRule [' + str(index) + ']')
            print('id:', rule.id)
            print('allowedMethod', rule.allowedMethod)
            print('allowedOrigin', rule.allowedOrigin)
            print('allowedHeader', rule.allowedHeader)
            print('maxAgeSecond', rule.maxAgeSecond)
            print('exposeHeader', rule.exposeHeader)
            index += 1


# delete bucket cors
def DeleteBucketCors():
    resp = bucketClient.deleteBucketCors()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# set bucket notification
def SetBucketNotification():
    fr1 = FilterRule(name='prefix', value='smn')
    fr2 = FilterRule(name='suffix', value='.jpg')
    topicConfiguration = TopicConfiguration(id='001', topic='urn:smn:region3:35667523534:topic1',
                                            events=[EventType.OBJECT_CREATED_ALL], filterRules=[fr1, fr2])
    resp = bucketClient.setBucketNotification(Notification(topicConfigurations=[topicConfiguration]))
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get bucket notification
def GetBucketNotification():
    resp = bucketClient.getBucketNotification()
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body is not None:
        for topicConfiguration in resp.body.topicConfigurations:
            print('id:', topicConfiguration.id)
            print('topic:', topicConfiguration.topic)
            print('events:', topicConfiguration.events)
            index = 1
            for rule in topicConfiguration.filterRules:
                print('rule [' + str(index) + ']')
                print('name:', rule.name)
                print('value:', rule.value)


# list multipart uploads
def ListMultipartUploads():
    Lmultipart = ListMultipartUploadsRequest(delimiter=None, prefix=None, max_uploads=10, key_marker=None,
                                             upload_id_marker=None)
    resp = bucketClient.listMultipartUploads(multipart=Lmultipart)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('bucket:', resp.body.bucket, ',keyMarker:', resp.body.keyMarker, 'uploadIdMarker:',
              resp.body.uploadIdMarker, ',nextKeyMarker:', resp.body.nextKeyMarker, 'delimiter:', resp.body.delimiter)
        print('nextUploadIdMarker:', resp.body.nextUploadIdMarker, ',maxUploads:', resp.body.maxUploads, 'isTruncated:',
              resp.body.isTruncated, ',prefix:', resp.body.prefix)
        if resp.body.upload:
            i = 0
            for upload in resp.body.upload:
                print('upload[', i, ']:')
                i += 1
                print('key:', upload.key, ',uploadId:', upload.uploadId, ',storageClass:', upload.storageClass,
                      ',initiated:', upload.initiated)
                if upload.owner:
                    print('owner.owner_id:', upload.owner.owner_id)
                if upload.initiator:
                    print('initiator.id:', upload.initiator.id, 'initiator.name:', upload.initiator.name)
        if resp.body.commonPrefixs:
            i = 0
            for commonPrefix in resp.body.commonPrefixs:
                print('commonPrefix[', i, ']:')
                i += 1
                print('prefix:', commonPrefix.prefix)


# set object acl
def SetObjectAcl():
    Lowner = Owner(owner_id='ownerid')

    Lgrantee = Grantee(grantee_id='userid', group=None)

    Lgrant = Grant(grantee=Lgrantee, permission=Permission.READ)

    Lgrants = [Lgrant]

    Lacl = ACL(owner=Lowner, grants=Lgrants)

    resp = bucketClient.setObjectAcl(objectKey='test.txt', acl=Lacl, versionId=None,
                                     aclControl='public-read-write')
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get object acl
def GetObjectAcl():
    resp = bucketClient.getObjectAcl(objectKey='test.txt', versionId=None)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('owner_id:', resp.body.owner.owner_id)
        i = 0
        for grant in resp.body.grants:
            print('Grant[', i, ']:')
            i += 1
            print('permission:', grant.permission)
            print('grantee_id:', grant.grantee.grantee_id, ',grantee.group:', grant.grantee.group)


# delete object
def DeleteObject():
    resp = bucketClient.deleteObject(objectKey='test.txt', versionId=None)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# delete objects
def DeleteObjects():
    Lobject1 = Object(key='test.xml', versionId=None)
    Lobject2 = Object(key='test.txt', versionId=None)
    Lobject3 = Object(key='test', versionId=None)
    Lobjects = [Lobject1, Lobject2, Lobject3]

    Lreq = DeleteObjectsRequest(quiet=False, objects=Lobjects)

    resp = bucketClient.deleteObjects(deleteObjectsRequest=Lreq)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        if resp.body.deleted:
            i = 0
            for delete in resp.body.deleted:
                print('deleted[', i, ']:')
                i += 1
                print('key:', delete.key, ',deleteMarker:', delete.deleteMarker, ',deleteMarkerVersionId:',
                      delete.deleteMarkerVersionId)
        if resp.body.error:
            i = 0
            for err in resp.body.error:
                print('error[', i, ']:')
                print('key:', err.key, ',code:', err.code, ',message:', err.message)


# abort multipart uplod
def AbortMultipartUpload():
    resp = bucketClient.abortMultipartUpload(objectKey='test.zip', uploadId='uploadid')
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# initiate multipart upload
def InitiateMultipartUpload():
    resp = bucketClient.initiateMultipartUpload(objectKey='test.zip', websiteRedirectLocation=None)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('bucketName:', resp.body.bucketName, ',objectKey:', resp.body.objectKey, ',uploadId:', resp.body.uploadId)


# complete multipart upload
def CompleteMultipartUpload():
    Lpart1 = CompletePart(partNum=1, etag='etagvalue1')
    Lpart2 = CompletePart(partNum=2, etag='etagvalue2')
    Lparts = [Lpart1, Lpart2]

    LcompleteMultipartUploadRequest = CompleteMultipartUploadRequest(parts=Lparts)

    resp = bucketClient.completeMultipartUpload(objectKey='test.zip', uploadId='uploadid',
                                                completeMultipartUploadRequest=LcompleteMultipartUploadRequest)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('location:', resp.body.location, ',bucket:', resp.body.bucket, ',key:', resp.body.key, ',etag:',
              resp.body.etag)


# upload part
def UploadPart():
    resp = bucketClient.uploadPart(objectKey='test.zip', partNumber=1, uploadId='uploadid',
                                   content='/temp/bigfile.zip', isFile=True, partSize=100 * 1024 * 1024, offset=0)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage,
          ',header:', resp.header)

    etag1 = dict(resp.header).get('etag')
    print(etag1)

    resp = bucketClient.uploadPart(objectKey='test.zip', partNumber=2, uploadId='uploadid',
                                   content='/temp/bigfile.zip', isFile=True, partSize=200 * 1024 * 1024,
                                   offset=100 * 1024 * 1024)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage,
          ',header:', resp.header)

    etag2 = dict(resp.header).get('etag')
    print(etag2)


# copy part
def CopyPart():
    resp = bucketClient.copyPart(objectKey='test.txt', partNumber=1, uploadId='uploadid',
                                 copySource='bucket002/test.txt')
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('lastModified:', resp.body.lastModified, ',etag:', resp.body.etag)


# list parts
def ListParts():
    resp = bucketClient.listParts(objectKey='test.zip', uploadId='uploadid', maxParts=None,
                                  partNumberMarker=None)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('bucketName:', resp.body.bucketName, ',objectKey:', resp.body.objectKey, ',uploadId:', resp.body.uploadId,
              ',storageClass:', resp.body.storageClass, )
        print('partNumbermarker:', resp.body.partNumbermarker, ',nextPartNumberMarker:', resp.body.nextPartNumberMarker,
              ',maxParts:', resp.body.maxParts, ',isTruncated:', resp.body.isTruncated, )
        if resp.body.initiator:
            print('initiator.name:', resp.body.initiator.name, ',initiator.id:', resp.body.initiator.id)
        if resp.body.parts:
            i = 0
            for part in resp.body.parts:
                print('part[', i, ']:')
                i += 1
                print('partNumber:', part.partNumber, ',lastModified:', part.lastModified, ',etag:', part.etag,
                      ',size:', part.size)


# restore object
def RestoreObject():
    resp = bucketClient.restoreObject(objectKey='test.txt', days=1, versionId=None, tier=RestoreTier.EXPEDITED)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# get object metadata
def GetObjectMetadata():
    resp = bucketClient.getObjectMetadata(objectKey='test.txt', versionId=None)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    print('etag:', resp.body.etag)
    print('lastModified:', resp.body.lastModified)
    print('contentType:', resp.body.contentType)
    print('contentLength:', resp.body.contentLength)


# put content
def PutContent():
    Lheaders = PutObjectHeader(md5=None, acl='private', location=None, contentType='text/plain')

    Lmetadata = {'key': 'value'}

    resp = bucketClient.putContent(objectKey='test.txt', content='msg content to put',
                                   metadata=Lmetadata, headers=Lheaders)

    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    print(resp.header)


def AppendObject():
    Lheaders = AppendObjectHeader(md5=None, acl='private', location=None, contentType=None)

    Lmetadata = {'key': 'value'}

    content = AppendObjectContent()
    content.content = 'msg content to put'

    resp = bucketClient.appendObject(objectKey='test.txt', content=content,
                                     metadata=Lmetadata, headers=Lheaders)

    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    print(resp.body)

    content.position = resp.body.nextPosition
    resp = bucketClient.appendObject(objectKey='test.txt', content=content,
                                     metadata=Lmetadata, headers=Lheaders)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# put file
def PutFile():
    Lheaders = PutObjectHeader(md5=None, acl='private', location=None, contentType='text/plain')

    Lmetadata = {'key': 'value'}
    file_path = '/temp/test.txt'

    resp = bucketClient.putFile(objectKey='test.txt', file_path=file_path,
                                metadata=Lmetadata, headers=Lheaders)
    if isinstance(resp, list):
        for k, v in resp:
            print('objectKey', k, 'common msg:status:', v.status, ',errorCode:', v.errorCode, ',errorMessage:',
                  v.errorMessage)
    else:
        print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)


# copy object
def CopyObject():
    Lheader = CopyObjectHeader(acl=None, directive=None, if_match=None, if_none_match=None,
                               if_modified_since=DateTime(2017, 6, 6), if_unmodified_since=None,
                               location=None)
    Lmetadata = {'key': 'value'}
    resp = bucketClient.copyObject(sourceBucketName=bucketName, sourceObjectKey='test.txt',
                                   destObjectKey='test-back.txt', metadata=Lmetadata, headers=Lheader)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    if resp.body:
        print('lastModified:', resp.body.lastModified, ',etag:', resp.body.etag)


# get object
def GetObject():
    LobjectRequest = GetObjectRequest(content_type='text/plain', content_language=None, expires=None,
                                      cache_control=None, content_disposition=None, content_encoding=None,
                                      versionId=None)

    Lheaders = GetObjectHeader(range='0-10', if_modified_since=None, if_unmodified_since=None, if_match=None,
                               if_none_match=None)
    loadStreamInMemory = False
    resp = bucketClient.getObject(objectKey='test.txt', downloadPath='/temp/test',
                                  getObjectRequest=LobjectRequest, headers=Lheaders,
                                  loadStreamInMemory=loadStreamInMemory)
    print('common msg:status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage,
          ',header:', resp.header)
    if loadStreamInMemory:
        print(resp.body.buffer)
        print(resp.body.size)
    elif resp.body.response:
        response = resp.body.response
        chunk_size = 65536
        if response is not None:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                print(chunk)
            response.close()
    else:
        print(resp.body.url)


if __name__ == '__main__':
    #     initLog()
    # =========================================================
    #     bucket operations
    # =========================================================
    #     CreateBucket()
    #     DeleteBucket()
    #     ListBuckets()
    #     HeadBucket()
    #     GetBucketMetadata()
    #     SetBucketQuota()
    #     GetBucketQuota()
    #     SetBucketStoragePolicy()
    #     GetBucketStoragePolicy()
    #     GetBucketStorageInfo()
    #     SetBucketAcl()
    #     GetBucketAcl()
    #     SetBucketPolicy()
    #     GetBucketPolicy()
    #     DeleteBucketPolicy()
    #     SetBucketVersioning()
    #     GetBucketVersioning()
    #     ListVersions()
    #     ListObjects()
    #     ListMultipartUploads()
    #     SetBucketLifecycle()
    #     GetBucketLifecycle()
    #     DeleteBucketLifecycle()
    #     SetBucketWebsite()
    #     GetBucketWebsite()
    #     DeleteBucketWebsite()
    #     SetBucketLogging()
    #     GetBucketLogging()
    #     GetBucketLocation()
    #     SetBucketTagging()
    #     GetBucketTagging()
    #     DeleteBucketTagging()
    #     SetBucketCors()
    #     GetBucketCors()
    #     DeleteBucketCors()
    #     SetBucketNotification()
    #     GetBucketNotification()
    # =========================================================
    #     object operations
    # =========================================================
    #     PutContent()
    #     AppendObject()
    #     CopyObject()
    #     PutFile()
    #     GetObject()
    #     GetObjectMetadata()
    #     SetObjectAcl()
    #     GetObjectAcl()
    #     DeleteObject()
    #     DeleteObjects()
    #     RestoreObject()
    #     AbortMultipartUpload()
    #     InitiateMultipartUpload()
    #     UploadPart()
    #     CompleteMultipartUpload()
    #     CopyPart()
    #     ListParts()
    pass
