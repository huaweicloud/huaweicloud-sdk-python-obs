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

import base64
import hashlib
import json
import re
import warnings

from obs import const, progress, crc64mod
from obs.http import IterableToContentStreamDataAdapter, IterableToStreamDataAdapter, Connection
if const.IS_PYTHON2:
    import urllib
else:
    import urllib.parse as urllib
from obs.ilog import INFO, ERROR
import crcmod

warnings.filterwarnings("ignore", message="[InsecureRequestWarning]", module="urllib")

def validate_length(value, field_name, min_len, max_len):
    if not min_len <= len(value) <= max_len:
        raise Exception("{} length must be between {} and {} characters. (value len: {})".format(field_name, min_len,
                                                                                                 max_len, len(value)))

def check_field(value, field_name, min_len=None, max_len=None, check_exists=False):
    if not value:
        raise Exception("{} does not exist.".format(field_name))
    if not check_exists and min_len is not None and max_len is not None:
        validate_length(value, field_name, min_len, max_len)


def to_bool(item):
    try:
        return True if item is not None and str(item).lower() == 'true' else False
    except Exception:
        return None


def to_int(item):
    try:
        return int(item)
    except Exception:
        return None


def to_long(item):
    try:
        return const.LONG(item)
    except Exception:
        return None


def to_float(item):
    try:
        return float(item)
    except Exception:
        return None


def to_string(item):
    try:
        return str(item) if item is not None else ''
    except Exception:
        return ''


def is_valid(item):
    return item is not None and item.strip() != ''


class RequestFormat(object):

    @staticmethod
    def get_path_format():
        return PathFormat()

    @staticmethod
    def get_sub_domain_format():
        return SubdomainFormat()

    @classmethod
    def convert_path_string(cls, path_args, allowdNames=None):
        e = ''
        if isinstance(path_args, dict):
            e1 = '?'
            e2 = '&'
            for path_key, path_value in path_args.items():
                flag = True
                if allowdNames is not None and path_key not in allowdNames:
                    flag = False
                if flag:
                    path_key = encode_item(path_key, '/')
                    if path_value is None:
                        e1 += path_key + '&'
                        continue
                    e2 += path_key + '=' + encode_item(path_value, '/') + '&'
            e = (e1 + e2).replace('&&', '&').replace('?&', '?')[:-1]
        return e

    def get_endpoint(self, server, port, bucket):
        return

    def get_path_base(self, bucket, key):
        return

    def get_url(self, bucket, key, path_args):
        return


class PathFormat(RequestFormat):

    @staticmethod
    def get_server(server, bucket):
        return server

    def get_path_base(self, bucket, key):
        if bucket:
            return '/' + bucket + '/' + encode_object_key(key) if key else '/' + bucket
        return '/' + encode_object_key(key) if key else '/'

    def get_endpoint(self, server, port, bucket):
        if port == 80 or port == 443:
            return server
        return server + ':' + str(port)

    def get_url(self, bucket, key, path_args):
        path_base = self.get_path_base(bucket, key)
        path_arguments = self.convert_path_string(path_args)
        return path_base + path_arguments

    def get_full_url(self, is_secure, server, port, bucket, key, path_args):
        url = 'https://' if is_secure else 'http://'
        url += self.get_endpoint(server, port, bucket)
        url += self.get_url(bucket, key, path_args)
        return url


class SubdomainFormat(RequestFormat):

    @staticmethod
    def get_server(server, bucket):
        return bucket + '.' + server if bucket else server

    def get_path_base(self, bucket, key):
        if key is None:
            return '/'
        return '/' + encode_object_key(key)

    def get_endpoint(self, server, port, bucket):
        if port == 80 or port == 443:
            return self.get_server(server, bucket)
        return self.get_server(server, bucket) + ':' + str(port)

    def get_url(self, bucket, key, path_args):
        url = self.convert_path_string(path_args)
        return self.get_path_base(bucket, key) + url

    def get_full_url(self, is_secure, server, port, bucket, key, path_args):
        url = 'https://' if is_secure else 'http://'
        url += self.get_endpoint(server, port, bucket)
        url += self.get_url(bucket, key, path_args)
        return url


class delegate(object):
    def __init__(self, conn):
        self.conn = conn

    def send(self, data, final=False, stream_id=None):
        self.conn.send(data)


def conn_delegate(conn):
    return delegate(conn)


def get_readable_entity(readable, chunk_size=const.READ_ONCE_LENGTH, notifier=None, auto_close=True,
                        use_http_conns=False):
    if notifier is None:
        notifier = progress.NONE_NOTIFIER
    if use_http_conns:
        return IterableToStreamDataAdapter(readable=readable, chunk_size=chunk_size, notifier=notifier,
                                           auto_close=auto_close)
    def entity(conn):
        try:
            while True:
                chunk = readable.read(chunk_size)
                if not chunk:
                    conn.send('0\r\n\r\n' if const.IS_PYTHON2 else '0\r\n\r\n'.encode('UTF-8'), final=True)
                    break
                newReadCount = len(chunk)
                if newReadCount > 0:
                    notifier.send(newReadCount)
                hex_chunk = hex(len(chunk))[2:]
                conn.send(hex_chunk if const.IS_PYTHON2 else hex_chunk.encode('UTF-8'))
                conn.send('\r\n' if const.IS_PYTHON2 else '\r\n'.encode('UTF-8'))
                conn.send(chunk)
                conn.send('\r\n' if const.IS_PYTHON2 else '\r\n'.encode('UTF-8'))
        finally:
            if hasattr(readable, 'close') and callable(readable.close) and auto_close:
                readable.close()

    return entity


def get_readable_entity_by_total_count(readable, totalCount, chunk_size=const.READ_ONCE_LENGTH, notifier=None,
                                       auto_close=True, use_http_conns=False):
    return get_entity_for_send_with_total_count(totalCount=totalCount, chunk_size=chunk_size, notifier=notifier,
                                                auto_close=auto_close, read_able=readable, use_http_conns=use_http_conns)


def get_file_entity_by_total_count(file_path, totalCount, chunk_size=const.READ_ONCE_LENGTH, notifier=None,
                                   use_http_conns=False):
    return get_entity_for_send_with_total_count(file_path, totalCount, None, chunk_size, notifier,
                                                use_http_conns=use_http_conns)


def get_entity_for_send_with_total_count(file_path=None, totalCount=None, offset=None, chunk_size=const.READ_ONCE_LENGTH,
                                         notifier=None, auto_close=True, read_able=None, use_http_conns=False):
    if notifier is None:
        notifier = progress.NONE_NOTIFIER
    if use_http_conns:
        return IterableToContentStreamDataAdapter(readable=read_able, total_count=totalCount, chunk_size=chunk_size,
                                                  notifier=notifier, auto_close=auto_close, file_path=file_path, offset=offset)
    def entity(conn):
        readCount = 0
        if file_path:
            readable = open(file_path, "rb")
            if offset:
                readable.seek(offset)
        else:
            readable = read_able
        try:
            while True:
                if totalCount is None or totalCount - readCount >= chunk_size:
                    readCountOnce = chunk_size
                else:
                    readCountOnce = totalCount - readCount
                chunk = readable.read(readCountOnce)
                newReadCount = len(chunk)
                if newReadCount > 0:
                    notifier.send(newReadCount)
                readCount += newReadCount
                if (totalCount is not None and readCount >= totalCount) or (totalCount is not None and not chunk):
                    conn.send(chunk, final=True)
                    break
                conn.send(chunk)
        finally:
            if hasattr(readable, 'close') and callable(readable.close) and auto_close:
                readable.close()

    return entity


def get_file_entity_by_offset_partsize(file_path, offset, totalCount, chunk_size=const.READ_ONCE_LENGTH, notifier=None,
                                       use_http_conns=False):
    return get_entity_for_send_with_total_count(file_path, totalCount, offset, chunk_size, notifier, use_http_conns=use_http_conns)


def is_ipaddress(item):
    return re.match(const.IPv4_REGEX, item)


def md5_encode(unencoded):
    m = hashlib.md5()
    unencoded = unencoded if const.IS_PYTHON2 else (
        unencoded.encode('UTF-8') if not isinstance(unencoded, bytes) else unencoded)
    m.update(unencoded)
    return m.digest()


def covert_string_to_bytes(str_object):
    if not const.IS_PYTHON2:
        if isinstance(str_object, str):
            return str_object.encode("UTF-8")
    return str_object


def base64_encode(unencoded):
    unencoded = unencoded if const.IS_PYTHON2 else (
        unencoded.encode('UTF-8') if not isinstance(unencoded, bytes) else unencoded)
    encode_str = base64.b64encode(unencoded, altchars=None)
    return encode_str if const.IS_PYTHON2 else encode_str.decode('UTF-8')


def encode_object_key(key):
    return encode_item(key, '/~')


def encode_item(item, safe='/'):
    return urllib.quote(to_string(item), safe)


def decode_item(item):
    return urllib.unquote(item)


def safe_trans_to_utf8(item):
    if not const.IS_PYTHON2:
        return item
    if item is not None:
        item = safe_encode(item)
        try:
            return item.decode('GB2312').encode('UTF-8')
        except Exception:
            return item
    return None


def safe_trans_to_gb2312(item):
    if not const.IS_PYTHON2:
        return item
    if item is not None:
        item = safe_encode(item)
        try:
            return item.decode('UTF-8').encode('GB2312')
        except Exception:
            return item
    return None


def safe_decode(item):
    if not const.IS_PYTHON2:
        return item
    if isinstance(item, str):
        try:
            item = item.decode('UTF-8')
        except Exception:
            try:
                item = item.decode('GB2312')
            except Exception:
                item = None
    return item


def safe_encode(item):
    if not const.IS_PYTHON2:
        return item
    if isinstance(item, const.UNICODE):
        try:
            item = item.encode('UTF-8')
        except UnicodeDecodeError:
            try:
                item = item.encode('GB2312')
            except Exception:
                item = None
    return item


def md5_file_encode_by_size_offset(file_path=None, size=None, offset=None, chuckSize=None):
    if file_path is not None and size is not None and offset is not None:
        m = hashlib.md5()
        with open(file_path, 'rb') as fp:
            CHUNK_SIZE = const.READ_ONCE_LENGTH if chuckSize is None else chuckSize
            fp.seek(offset)
            read_count = 0
            while read_count < size:
                read_size = CHUNK_SIZE if size - read_count >= CHUNK_SIZE else size - read_count
                data = fp.read(read_size)
                read_count_once = len(data)
                if read_count_once <= 0:
                    break
                m.update(data)
                read_count += read_count_once
        return m.digest()

def sha256_file_encode_by_size_offset(file_path=None, size=None, offset=None, chuckSize=None):
    if file_path is not None and size is not None and offset is not None:
        m = hashlib.sha256()
        with open(file_path, 'rb') as fp:
            CHUNK_SIZE = const.READ_ONCE_LENGTH if chuckSize is None else chuckSize
            fp.seek(offset)
            read_count = 0
            while read_count < size:
                read_size = CHUNK_SIZE if size - read_count >= CHUNK_SIZE else size - read_count
                data = fp.read(read_size)
                read_count_once = len(data)
                if read_count_once <= 0:
                    break
                m.update(data)
                read_count += read_count_once
        return m.digest()


def do_close(result, conn, connHolder, log_client=None):
    if not result:
        close_conn(conn, log_client)
    elif result.getheader('connection', '').lower() == 'close':
        if log_client:
            log_client.log(INFO, 'server inform to close connection')
        close_conn(conn, log_client)
    elif to_int(result.status) >= 500 or connHolder is None:
        close_conn(conn, log_client)
    elif hasattr(conn, '_clear') and conn._clear:
        close_conn(conn, log_client)
    elif isinstance(conn, Connection):  # 清理result
        close_conn(result, log_client)
    else:
        if connHolder is not None:
            try:
                connHolder['connSet'].put_nowait(conn)
            except Exception:
                close_conn(conn, log_client)


def close_conn(conn, log_client=None):
    try:
        if conn:
            conn.close()
    except Exception as ex:
        if log_client:
            log_client.log(ERROR, ex)


SKIP_VERIFY_ATTR_TYPE = False


def verify_attr_type(value, allowedAttrType):
    if SKIP_VERIFY_ATTR_TYPE:
        return True
    if isinstance(allowedAttrType, list):
        for t in allowedAttrType:
            if isinstance(value, t):
                return True
        return False
    return isinstance(value, allowedAttrType)


def lazyCallback(*args, **kwargs):
    pass


def jsonLoadsForPy2(json_text):
    return _byteify(json.loads(json_text, object_hook=_byteify), ignore_dicts=True)


def _byteify(data, ignore_dicts=False):
    if isinstance(data, const.UNICODE):
        return data.encode('utf-8')
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=True) for item in data]
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    return data


class Crc64(object):
    _POLY = 0x142F0E1EBA9EA3693
    _XOROUT = 0XFFFFFFFFFFFFFFFF

    def __init__(self, init_crc=0):
        self.crc64 = crcmod.Crc(self._POLY, initCrc=init_crc, rev=True, xorOut=self._XOROUT)

        self.crc64_combineFun = crc64mod.mkCombineFun(self._POLY, initCrc=init_crc, rev=True, xorOut=self._XOROUT)

    def __call__(self, data):
        self.update(data)

    def update(self, data):
        self.crc64.update(data)

    def combine(self, crc1, crc2, len2):
        return self.crc64_combineFun(crc1, crc2, len2)
    @property
    def crc(self):
        return self.crc64.crcValue


def calculate_file_crc64(file_name, block_size=64 * 1024, init_crc=0, offset=None, totalCount=None):
    readCount = 0
    with open(file_name, 'rb') as f:
        if offset:
            f.seek(offset)
        crc64 = Crc64(init_crc)
        while True:
            if totalCount is None or totalCount - readCount >= block_size:
                readCountOnce = block_size
            else:
                readCountOnce = totalCount -readCount
            data = f.read(readCountOnce)
            readCount += readCountOnce
            if (totalCount is not None and readCount >= totalCount) or not data:
                crc64.update(data)
                break
            crc64.update(data)
    f.close()
    return crc64.crc


def calculate_content_crc64(content, block_size=64 * 1024, init_crc=0):
    crc64 = Crc64(init_crc)
    if hasattr(content, 'read'):
        while True:
            data = content.read(block_size)
            if not data:
                break
            crc64.update(data)
    else:
        crc64.update(content)

    return crc64.crc


def calc_obj_crc_from_parts(parts, init_crc=0):
    object_crc = 0
    crc_obj = Crc64(init_crc)
    for part in parts:
        if not part.crc64 or not part.size:
            raise Exception('part {0} has no size or crc64'.format(part.partNum))
        else:
            object_crc = crc_obj.combine(object_crc, to_int(part.crc64), part.size)
    return object_crc