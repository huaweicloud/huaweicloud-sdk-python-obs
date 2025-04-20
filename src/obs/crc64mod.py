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
