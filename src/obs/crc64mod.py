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

__all__ = '''mkCrcFun Crc
'''.split()

from obs.const import IS_PYTHON2
import struct


class Crc:
    def __init__(self, poly, initCrc=~0, rev=True, xorOut=0, initialize=True):
        if not initialize:
            return

        (sizeBits, initCrc, xorOut) = _verifyParams(poly, initCrc, xorOut)
        self.digest_size = sizeBits // 8
        self.poly = poly
        self.initCrc = initCrc
        self.reverse = rev
        self.xorOut = xorOut

        (crcfun, table) = _mkCrcFun(poly, sizeBits, initCrc, rev, xorOut)
        self.table = table
        self._crc = crcfun

        self.crcValue = self.initCrc

    def __str__(self):
        lst = []
        lst.append('reverse = %s' % self.reverse)
        lst.append('poly = 0x%X' % self.poly)
        fmt = '0x%%0%dX' % (self.digest_size * 2)
        lst.append('crcValue = %s' % (fmt % self.crcValue))
        lst.append('xorOut   = %s' % (fmt % self.xorOut))
        lst.append('initCrc  = %s' % (fmt % self.initCrc))
        return '\n'.join(lst)

    def new(self, arg=None):
        n = Crc(poly=None, initialize=False)
        n._crc = self._crc
        n.table = self.table
        n.digest_size = self.digest_size
        n.reverse = self.reverse
        n.initCrc = self.initCrc
        n.crcValue = self.initCrc
        n.xorOut = self.xorOut
        n.poly = self.poly
        if arg is not None:
            n.update(arg)
        return n

    def copy(self):
        c = self.new()
        c.crcValue = self.crcValue
        return c

    def update(self, data):
        self.crcValue = self._crc(data, self.crcValue)

    def digest(self):
        n = self.digest_size
        crc = self.crcValue
        lst = []
        while n > 0:
            lst.append(crc & 0xFF)
            crc = crc >> 8
            n -= 1
        lst.reverse()
        return bytes(lst)

    def hexdigest(self):
        crc = self.crcValue
        n = self.digest_size
        lst = []
        while n > 0:
            lst.append('%02X' % (crc & 0xFF))
            crc = crc >> 8
            n -= 1
        lst.reverse()
        return ''.join(lst)


def mkCrcFun(poly, initCrc=~0, rev=True, xorOut=0):
    (sizeBits, initCrc, xorOut) = _verifyParams(poly, initCrc, xorOut)
    return _mkCrcFun(poly, sizeBits, initCrc, rev, xorOut)[0]


def _verifyPoly(poly):
    msg = 'The degree of the polynomial must be 64'
    n = 64
    low = 1 << n
    high = low * 2
    if low <= poly < high:
        return n
    raise ValueError(msg)


def _bitrev(x, n):
    y = 0
    for i in range(n):
        y = (y << 1) | (x & 1)
        x = x >> 1
    return y


def _bytecrc(crc, poly, n):
    mask = 1 << (n - 1)
    for i in range(8):
        if crc & mask:
            crc = (crc << 1) ^ poly
        else:
            crc = crc << 1
    mask = (1 << n) - 1
    crc = crc & mask
    return crc


def _bytecrc_r(crc, poly, n):
    for i in range(8):
        if crc & 1:
            crc = (crc >> 1) ^ poly
        else:
            crc = crc >> 1
    mask = (1 << n) - 1
    crc = crc & mask
    return crc


def _mkTable(poly, n):
    mask = (1 << n) - 1
    poly = poly & mask
    table = [_bytecrc(i << (n - 8), poly, n) for i in range(256)]
    return table


def _mkTable_r(poly, n):
    mask = (1 << n) - 1
    poly = _bitrev(poly & mask, n)
    table = [_bytecrc_r(i, poly, n) for i in range(256)]
    return table


_sizeToTypeCode = {}

for typeCode in 'B H I L Q'.split():
    size = {1: 8, 2: 16, 4: 32, 8: 64}.get(struct.calcsize(typeCode), None)
    if size is not None and size not in _sizeToTypeCode:
        _sizeToTypeCode[size] = '256%s' % typeCode

_sizeToTypeCode[24] = _sizeToTypeCode[32]

del typeCode, size


def _verifyParams(poly, initCrc, xorOut):
    sizeBits = _verifyPoly(poly)
    mask = (1 << sizeBits) - 1
    initCrc = initCrc & mask
    xorOut = xorOut & mask
    return (sizeBits, initCrc, xorOut)


def _mkCrcFun(poly, sizeBits, initCrc, rev, xorOut):
    if rev:
        tableList = _mkTable_r(poly, sizeBits)
        _fun = _crc64r
    else:
        tableList = _mkTable(poly, sizeBits)
        _fun = _crc64

    _table = tableList

    if xorOut == 0:
        def crcfun(data, crc=initCrc, table=_table, fun=_fun):
            return fun(data, crc, table)
    else:
        def crcfun(data, crc=initCrc, table=_table, fun=_fun):
            return xorOut ^ fun(data, xorOut ^ crc, table)

    return crcfun, tableList


def _get_buffer_view(in_obj):
    if isinstance(in_obj, str):
        raise TypeError('Unicode-objects must be encoded before calculating a CRC')
    mv = memoryview(in_obj)
    if mv.ndim > 1:
        raise BufferError('Buffer must be single dimension')
    return mv


def _crc64(data, crc, table):
    crc = crc & 0xFFFFFFFFFFFFFFFF
    if IS_PYTHON2:
        for x in data:
            crc = table[ord(x) ^ (int(crc >> 56) & 0xFF)] ^ ((crc << 8) & 0xFFFFFFFFFFFFFF00)
    else:
        mv = _get_buffer_view(data)
        for x in mv.tobytes():
            crc = table[x ^ ((crc >> 56) & 0xFF)] ^ ((crc << 8) & 0xFFFFFFFFFFFFFF00)
    return crc


def _crc64r(data, crc, table):
    crc = crc & 0xFFFFFFFFFFFFFFFF
    if IS_PYTHON2:
        for x in data:
            crc = table[ord(x) ^ int(crc & 0xFF)] ^ (crc >> 8)
    else:
        mv = _get_buffer_view(data)
        for x in mv.tobytes():
            crc = table[x ^ (crc & 0xFF)] ^ (crc >> 8)
    return crc


import sys

is_py3 = (sys.version_info[0] == 3)
if is_py3:
    xrange = range
    long = int
    sys.maxint = sys.maxsize


def mkCombineFun(poly, initCrc=~long(0), rev=True, xorOut=0):
    (sizeBits, initCrc, xorOut) = _verifyParams(poly, initCrc, xorOut)

    mask = (long(1) << sizeBits) - 1
    if rev:
        poly = _bitrev(long(poly) & mask, sizeBits)
    else:
        poly = long(poly) & mask

    if sizeBits == 64:
        fun = _combine64
    else:
        return NotImplemented

    def combine_fun(crc1, crc2, len2):
        return fun(poly, initCrc ^ xorOut, rev, xorOut, crc1, crc2, len2)

    return combine_fun


GF2_DIM = 64


def gf2_matrix_square(square, mat):
    for n in xrange(GF2_DIM):
        square[n] = gf2_matrix_times(mat, mat[n])


def gf2_matrix_times(mat, vec):
    summary = 0
    mat_index = 0

    while vec:
        if vec & 1:
            summary ^= mat[mat_index]

        vec >>= 1
        mat_index += 1

    return summary


def _combine64(poly, initCrc, rev, xorOut, crc1, crc2, len2):
    if len2 == 0:
        return crc1

    even = [0] * GF2_DIM
    odd = [0] * GF2_DIM

    crc1 ^= initCrc ^ xorOut

    if (rev):
        odd[0] = poly
        row = 1
        for n in xrange(1, GF2_DIM):
            odd[n] = row
            row <<= 1
    else:
        row = 2
        for n in xrange(0, GF2_DIM - 1):
            odd[n] = row
            row <<= 1
        odd[GF2_DIM - 1] = poly

    gf2_matrix_square(even, odd)

    gf2_matrix_square(odd, even)

    while True:
        gf2_matrix_square(even, odd)
        if len2 & long(1):
            crc1 = gf2_matrix_times(even, crc1)
        len2 >>= 1
        if len2 == 0:
            break

        gf2_matrix_square(odd, even)
        if len2 & long(1):
            crc1 = gf2_matrix_times(odd, crc1)
        len2 >>= 1

        if len2 == 0:
            break

    crc1 ^= crc2

    return crc1


def _verifyPoly(poly):
    msg = 'The degree of the polynomial must be 8, 16, 24, 32 or 64'
    poly = long(poly)
    for n in (8, 16, 24, 32, 64):
        low = long(1) << n
        high = low * 2
        if low <= poly < high:
            return n
    raise ValueError(msg)


def _bitrev(x, n):
    x = long(x)
    y = long(0)
    for i in xrange(n):
        y = (y << 1) | (x & long(1))
        x = x >> 1
    if ((long(1) << n) - 1) <= sys.maxint:
        return int(y)
    return y


def _verifyParams(poly, initCrc, xorOut):
    sizeBits = _verifyPoly(poly)

    mask = (long(1) << sizeBits) - 1

    initCrc = long(initCrc) & mask
    if mask <= sys.maxint:
        initCrc = int(initCrc)

    xorOut = long(xorOut) & mask
    if mask <= sys.maxint:
        xorOut = int(xorOut)

    return (sizeBits, initCrc, xorOut)
