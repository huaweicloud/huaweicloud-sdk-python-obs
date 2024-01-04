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

from obs.ilog import DEBUG, ERROR, INFO
from obs.model import DeleteObjectsRequest, Object

def _resume_delete(bucketName, prefix, obsClient):

    folderList, objectList = _resume_list_object(bucketName, prefix, obsClient)
    errorList = []
    deleteList = []
    if(objectList != []):
        index = 0
        while index < len(objectList):
            del_list = objectList[index:index+1000]
            need_to_delete_objects = [Object(key=i) for i in del_list]
            try:
                resp = obsClient.deleteObjects(bucketName, DeleteObjectsRequest(False, need_to_delete_objects,
                                                                                encoding_type="url"))
                deleteList += resp.body.deleted
                if resp.body.error:
                    errorList += resp.body.error
            except Exception as e:
                obsClient.log_client.log(ERROR,
                                         'something is wrong when detele objects.ErrorCode:{0}. ErrorMessage:{1}'.format(
                                             resp.errorCode, resp.errorMessage))
                raise e
            index += 1000
    folder_list = sorted(folderList, key=lambda t: t[0], reverse=True)
    if(folderList != []):
        for obj in folder_list:
            try:
                resp = obsClient.deleteObject(bucketName, obj[1])
                if (resp.status < 300):
                    deleteList.append(obj)
                elif (resp.status > 300):
                    errorList.append((obj, resp.errorCode, resp.errorMessage))
            except Exception as e:
                obsClient.log_client.log(ERROR,
                                         'something is wrong when detele folder{2}.ErrorCode:{0}. ErrorMessage:{1}'.format(
                                             resp.errorCode, resp.errorMessage, obj[1]))
                raise e
    return deleteList, errorList

def _resume_list_object(bucketName, prefix, obsClient, marker=None, folderList=None, objectList=None):
    if(folderList is None):
        folderList = []
    if(objectList is None):
        objectList = []
    try:
        resp = obsClient.listObjects(bucketName, prefix, marker, 1000)
        if (resp.status > 300):
            raise Exception('something is wrong when list objects.ErrorCode:{0}. ErrorMessage:{1}'.format(
                                     resp.errorCode, resp.errorMessage))
    except Exception as e:
        obsClient.log_client.log(ERROR,
                                 'something is wrong when list objects.ErrorCode:{0}. ErrorMessage:{1}'.format(
                                     resp.errorCode, resp.errorMessage))
        raise e

    for obj in resp.body.contents:
        if(obj["key"].endswith("/")):
            dep = obj["key"].count("/")
            folder = (dep, obj["key"])
            folderList.append(folder)
        else:
            objectList.append(obj["key"])
    if (not resp.body.is_truncated):
        return folderList, objectList
    _resume_list_object(bucketName, prefix, obsClient, resp.body.next_marker, folderList, objectList)
    return folderList, objectList

