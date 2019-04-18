#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

