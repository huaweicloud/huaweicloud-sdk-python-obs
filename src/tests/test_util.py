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

import os
import random
import unittest

import obs.util as util


class MockConn(object):
    def __init__(self):
        self.send_length = 0
        self.end = False
        self.not_data_times = 0
        self.read_memory_list = []
        self.read_memory = b""

    def send(self, chunk, final=False):
        self.end = final
        self.read_memory_list.append(chunk)
        if len(chunk) == 0:
            self.not_data_times += 1
        if final:
            self.read_memory = b"".join(self.read_memory_list)
        self.send_length += len(chunk)


class TestUtilGetEntity(unittest.TestCase):
    def setUp(self):
        self.file_path_list = ["3k", "300k", "3M", "300M", "3G"]
        self.path_prefix = "D:/workspace/mpb_tools/"

    def test_send_file_entity_by_total_count(self):
        for i in self.file_path_list:
            new_conn = MockConn()
            file_path = self.path_prefix + i
            file_total_count = os.path.getsize(file_path)
            entity = util.get_file_entity_by_total_count(file_path, file_total_count)
            while True:
                entity(new_conn)
                if new_conn.end or new_conn.not_data_times > 10:
                    break
            self.assertEqual(new_conn.send_length, file_total_count)
            with open(file_path, "rb") as f:
                self.assertEqual(new_conn.read_memory, f.read())

    def test_send_file_entity_by_offset_and_partsize(self):
        for i in self.file_path_list:
            new_conn = MockConn()
            file_path = self.path_prefix + i
            file_total_count = os.path.getsize(file_path)
            partSize = int(file_total_count / 3)
            offset = partSize
            entity = util.get_file_entity_by_offset_partsize(file_path, offset, partSize)
            while True:
                entity(new_conn)
                if new_conn.end or new_conn.not_data_times > 10:
                    break
            self.assertEqual(new_conn.send_length, partSize)
            with open(file_path, "rb") as f:
                f.seek(offset)
                self.assertEqual(new_conn.read_memory, f.read(partSize))

    def test_send_entity_by_file(self):
        # 验证重构后读文件结果和原本一致
        for i in self.file_path_list:
            new_conn = MockConn()
            file_path = self.path_prefix + i
            file_total_count = os.path.getsize(file_path)
            readable_object = open(file_path, "rb")
            entity = util.get_entity_for_send_with_total_count(read_able=readable_object, totalCount=file_total_count)
            while True:
                entity(new_conn)
                if new_conn.end or new_conn.not_data_times > 10:
                    break
            self.assertEqual(new_conn.send_length, file_total_count)
            with open(file_path, "rb") as f:
                self.assertEqual(new_conn.read_memory, f.read())

    def test_send_entity_by_file_with_offset_and_partsize(self):
        for i in self.file_path_list:
            new_conn = MockConn()
            file_path = self.path_prefix + i
            file_total_count = os.path.getsize(file_path)
            partSize = int(file_total_count / 3)
            offset = partSize
            readable_object = open(file_path, "rb")
            readable_object.seek(offset)
            entity = util.get_entity_for_send_with_total_count(read_able=readable_object, totalCount=partSize)
            while True:
                entity(new_conn)
                if new_conn.end or new_conn.not_data_times > 10:
                    break
            self.assertEqual(new_conn.send_length, partSize)
            with open(file_path, "rb") as f:
                f.seek(offset)
                self.assertEqual(new_conn.read_memory, f.read(partSize))

    def test_send_readable_entity_by_total_count(self):
        for n in range(5):
            offset_percent = random.random()
            for i in self.file_path_list:
                new_conn = MockConn()
                new_conn2 = MockConn()
                file_path = self.path_prefix + i
                file_total_count = os.path.getsize(file_path)
                readable_object = open(file_path, "rb")
                readable_object2 = open(file_path, "rb")
                readable_object.seek(int(file_total_count * offset_percent))
                readable_object2.seek(int(file_total_count * offset_percent))
                entity = util.get_entity_for_send_with_total_count(read_able=readable_object, totalCount=file_total_count
                                                                   - int(file_total_count * offset_percent))
                entity2 = util.get_readable_entity_by_total_count(readable_object2, file_total_count
                                                                  - int(file_total_count * offset_percent))
                while True:
                    entity(new_conn)
                    entity2(new_conn2)
                    if new_conn.end or new_conn.not_data_times > 10:
                        break
                self.assertEqual(new_conn.send_length, new_conn2.send_length)
                self.assertEqual(new_conn.read_memory, new_conn2.read_memory)
