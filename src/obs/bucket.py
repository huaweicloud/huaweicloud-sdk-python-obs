#!/usr/bin/python
# -*- coding:utf-8 -*-


class BucketClient(object):
    
    allowedMethod = [
        'createBucket',
        'deleteBucket',
        'headBucket',
        'getBucketMetadata',
        'setBucketQuota',
        'getBucketQuota',
        'getBucketStorageInfo',
        'setBucketAcl',
        'getBucketAcl',
        'setBucketPolicy',
        'getBucketPolicy',
        'deleteBucketPolicy',
        'setBucketVersioning',
        'getBucketVersioning',
        'listVersions',
        'listObjects',
        'listMultipartUploads',
        'deleteBucketLifecycle',
        'setBucketLifecycle',
        'getBucketLifecycle',
        'deleteBucketWebsite',
        'setBucketWebsite',
        'getBucketWebsite',
        'setBucketLogging',
        'getBucketLogging',
        'getBucketLocation',
        'getBucketTagging',
        'setBucketTagging',
        'deleteBucketTagging',
        'setBucketCors',
        'deleteBucketCors',
        'getBucketCors',
        'setBucketNotification',
        'getBucketNotification',
        'getObjectMetadata',
        'setObjectMetadata',
        'getObject',
        'putContent',
        'putObject',
        'appendObject',
        'putFile',
        'uploadPart',
        'copyObject',
        'setObjectAcl',
        'getObjectAcl',
        'deleteObject',
        'deleteObjects',
        'restoreObject',
        'initiateMultipartUpload',
        'copyPart',
        'completeMultipartUpload',
        'abortMultipartUpload',
        'listParts',
        'getBucketStoragePolicy',
        'setBucketStoragePolicy',
        'optionsBucket',
        'optionsObject'
    ]
    
    def __init__(self, obsClient, bucketName):
        self.__obsClient = obsClient
        self.__bucketName = bucketName
        
    
    def __getattr__(self, key):
        if key in self.allowedMethod and hasattr(self.__obsClient, key):
            orignalMethod = getattr(self.__obsClient, key)
            if callable(orignalMethod):
                def delegate(*args, **kwargs):
                    _args = list(args)
                    if key == 'copyObject':
                        if 'destBucketName' not in kwargs:
                            if len(_args) >= 2:
                                _args.insert(2, self.__bucketName)
                            else:
                                kwargs['destBucketName'] = self.__bucketName
                    else:
                        if 'bucketName' not in kwargs:
                            _args.insert(0, self.__bucketName)
                    return orignalMethod(*_args, **kwargs)
                return delegate
        return super(BucketClient, self).__getattribute__(key)

