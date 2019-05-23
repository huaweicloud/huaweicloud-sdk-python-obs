#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2019 Huawei Technologies Co.,Ltd.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License.  You may obtain a copy of the
# License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations under the License.

from obs import const

LOCK_COUNT = 16

lock_list = None
 
if const.IS_WINDOWS:
    lock_list = []
    import threading
    for i in range(LOCK_COUNT):
        lock_list.append(threading.RLock())
else:
    import multiprocessing
    lock0 = multiprocessing.RLock()
    lock1 = multiprocessing.RLock()
    lock2 = multiprocessing.RLock()
    lock3 = multiprocessing.RLock()
    lock4 = multiprocessing.RLock()
    lock5 = multiprocessing.RLock()
    lock6 = multiprocessing.RLock()
    lock7 = multiprocessing.RLock()
    lock8 = multiprocessing.RLock()
    lock9 = multiprocessing.RLock()
    lock10 = multiprocessing.RLock()
    lock11 = multiprocessing.RLock()
    lock12 = multiprocessing.RLock()
    lock13 = multiprocessing.RLock()
    lock14 = multiprocessing.RLock()
    lock15 = multiprocessing.RLock()
 
def get_lock(index):
    if index < 0 or index >= LOCK_COUNT:
        raise Exception('cannot find a valid lock')
    
    return globals()['lock' + str(index)] if lock_list is None else lock_list[index]

