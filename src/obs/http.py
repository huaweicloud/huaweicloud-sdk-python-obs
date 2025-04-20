# -*- coding: utf-8 -*-

"""
obs.http
"""
from obs.ilog import DEBUG, ERROR
from obs.const import CONNECTION_POOL_SIZE, READ_ONCE_LENGTH, IS_PYTHON2
from requests.adapters import HTTPAdapter
import requests

# url编码
try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus


class CustomHttpAdapter(HTTPAdapter):
    """
      重构HTTPAdapter用于传入tls context，自定义 custom_ciphers
    """

    def __init__(self, context=None, *args, **kwargs):
        self.context = context
        super(CustomHttpAdapter, self).__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.context
        return super(CustomHttpAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self.context
        return super(CustomHttpAdapter, self).proxy_manager_for(*args, **kwargs)


class Session(object):
    """属于同一个Session的请求共享一组连接池，如有可能也会重用HTTP连接。"""

    def __init__(self, context=None, pool_size=None, trust_env=True):
        """
        初始化设置http和https的HTTP ADAPTER
        :param context: ssl context，用于重载HttpAdapter
        :param pool_size: 设置连接池大小，默认10
        :param trust_env: 设置获取环境变量中的代理，默认需要获取，但是OBS CLIENT默认不获取
        """
        self.session = requests.Session()
        self.session.trust_env = trust_env
        psize = pool_size or CONNECTION_POOL_SIZE
        self.session.mount('http://', CustomHttpAdapter(context=context, pool_connections=psize, pool_maxsize=psize))
        self.session.mount('https://', CustomHttpAdapter(context=context, pool_connections=psize, pool_maxsize=psize))

    def do_request(self, req, timeout, log_client):
        """
        使用session发送请求，指定超时时间和日志输出client
        :param req: 发送请求的对象
        :type req: Request
        :param timeout: 请求超时时间
        :param log_client: 日志输出Client
        :return: 请求的Response
        """
        try:
            log_client.log(DEBUG,
                           "Send request, method: {0}, url: {1}, headers: {2}, timeout: {3}, proxies: {4}".format(
                               req.method, req.url, req.headers, timeout, req.proxies))
            return Response(self.session.request(req.method, req.url,
                                                 data=req.data,
                                                 headers=req.headers,
                                                 stream=True,
                                                 allow_redirects=False,
                                                 verify=False if not req.cert else True,
                                                 timeout=timeout,
                                                 proxies=req.get_proxy()), log_client)
        except requests.RequestException as e:
            log_client.log(ERROR, "request obs failed. {}".format(e))
            raise Exception(e)


class IterableToStreamDataAdapter(object):
    """
      重构不可知内容大小的读，用于回调和通知
      r = requests.post("http://httpbin.org/post", data=IterableToStreamDataAdapter(__file__, chunksize=10))
    """

    def __init__(self, readable, chunk_size=READ_ONCE_LENGTH, notifier=None, auto_close=True):
        self.readable = readable
        self.chunk_size = chunk_size
        self.read_sofar = 0
        self.notifier = notifier
        self.auto_close = auto_close

    def __iter__(self):
        """
        针对文件或可read的句柄，进行遍历读，实现一边读一边写
        :return: yield数据
        """
        try:
            while True:
                data = self.readable.read(self.chunk_size)
                if not data:
                    break
                new_read_count = len(data)
                if new_read_count > 0:
                    self.notifier.send(new_read_count)
                yield data
        finally:
            if hasattr(self.readable, 'close') and callable(self.readable.close) and self.auto_close:
                self.readable.close()


class IterableToContentStreamDataAdapter(object):
    """
      重构已知内容大小的读，用于回调和通知
      Python 3 对迭代器协议进行了改进，移除了 __getitem__ 的隐式迭代支持，使得迭代行为更加明确和一致。
      r = requests.post("http://httpbin.org/post", data=IterableToContentStreamDataAdapter(__file__, chunksize=10))
    """

    def __init__(self, readable=None, total_count=None, chunk_size=READ_ONCE_LENGTH, notifier=None, auto_close=True,
                 file_path=None, offset=None):
        if not readable and not file_path:
            raise Exception("not get readable or file_path")
        if file_path:
            self.readable = open(file_path, "rb")
            if offset:
                self.readable.seek(offset)
        else:
            self.readable = readable
        self.chunk_size = chunk_size
        self.total_count = total_count
        self.read_sofar = 0
        self.notifier = notifier
        self.auto_close = auto_close

    if IS_PYTHON2:
        def read(self, chunk_size=None):
            """
            python2 通过read来读对象
            :param chunk_size: 需要读的block大小
            :return: 数据
            """
            chunk_size = chunk_size or self.chunk_size
            if self.total_count is None or self.total_count - self.read_sofar >= chunk_size:
                read_count_once = chunk_size
            else:
                read_count_once = self.total_count - self.read_sofar
            if read_count_once <= 0:
                return None
            data = self.readable.read(read_count_once)
            new_read_count = len(data)
            if new_read_count > 0:
                self.notifier.send(new_read_count)
            self.read_sofar += new_read_count
            if (self.total_count is not None and self.read_sofar >= self.total_count) or (
                    self.total_count is not None and not data):
                if hasattr(self.readable, 'close') and callable(self.readable.close) and self.auto_close:
                    self.readable.close()
            return data

    def __iter__(self):
        """
        重构__iter__方法，针对文件或可read的句柄，进行遍历读，实现一边读一边写
        :return:
        """
        try:
            read_count = 0
            while True:
                if self.total_count is None or self.total_count - read_count >= self.chunk_size:
                    read_count_once = self.chunk_size
                else:
                    read_count_once = self.total_count - read_count
                data = self.readable.read(read_count_once)
                new_read_count = len(data)
                if new_read_count > 0:
                    self.notifier.send(new_read_count)
                read_count += new_read_count
                if (self.total_count is not None and read_count >= self.total_count) or (
                        self.total_count is not None and not data):
                    yield data
                    break
                yield data
        finally:
            if hasattr(self.readable, 'close') and callable(self.readable.close) and self.auto_close:
                self.readable.close()

    def __len__(self):
        """
        指定待读取文件大小
        :param self:
        :return: 待读取文件大小
        """
        return self.total_count


class Connection(object):
    """定义新HTTP连接对象，用于封装Request、Response、Session"""

    def __init__(self, request, session, log_client):
        """
        初始化新HTTP连接对象
        :param request: 封装请求的参数
        :type request: Request
        :param session: HTTP连接池Session
        :type session: Session
        :param log_client:
        """
        self.req = request
        self.session = session
        self.response = None  # 对外返回的Response对象
        self.log_client = log_client

    def set_tunnel(self, server, port, header):
        self.req.server = server
        self.req.port = port
        self.req.tunnel_headers = header

    def close(self):
        self.log_client.log(DEBUG, "close http connection")

    def putheader(self, key, value):
        """
        重载增加请求头信息，支持多次添加同一头字段，用逗号分隔合并。
        :param key: 头域key
        :param value: 头域value
        :return: 无返回
        """
        str_value = self._header_value_to_str(value)
        if key in self.req.headers:
            self.req.headers[key] = "{}, {}".format(self.req.headers[key], str_value)
        else:
            self.req.headers[key] = str_value

    def _header_value_to_str(self, value):
        # 处理 Python 2 和 Python 3 的字符串类型
        try:
            if isinstance(value, unicode):
                return value.encode('latin-1')
        except NameError:
            pass
        if isinstance(value, bytes):
            return value.decode('latin-1')
        if isinstance(value, int):
            return str(value)
        return str(value)

    def endheaders(self):
        """
        重载结束写头信息，并发起HTTP请求
        :return: 无返回
        """
        self.req.headers.update(self.req.tunnel_headers) if self.req.tunnel_headers else self.req.headers
        self.response = self.session.do_request(self.req, self.req.timeout, self.log_client)

    def request(self, method, path, body=None, headers=None):
        """
        重载发起http请求
        :param method: 请求方法
        :param path: 请求path
        :param body: 请求body，可为字符串、字符、可读对象IterableToContentStreamDataAdapter或IterableToStreamDataAdapter
        :param headers: 请求头域列表
        :return: 无返回
        """
        if not headers:
            headers = {}
        self.req.method = method
        self.req.url = "{scheme}://{server}:{port}{path}".format(scheme=self.req.scheme,
                                                                 server=self.req.server, port=self.req.port,
                                                                 path=path)
        self.req.data = body
        if self.req.headers:
            headers.update(self.req.headers)
        self.req.headers = headers

        chunked = not (self.req.data is None or 'Content-Length' in self.req.headers)
        if chunked:
            del self.req.headers["Host"]
        self.response = self.session.do_request(self.req, self.req.timeout, self.log_client)

    def getresponse(self, myseq=None):
        """
        重载获取response
        :param myseq: 序号，无用字段,兼容老的conn
        :return:
        """
        return self.response



class Request(object):
    """
    HTTP请求的标准对象封装
    """

    def __init__(self, server, port=None, scheme=None, method=None, proxies=None, redirect=True, timeout=None,
                 proxy_host=None, proxy_port=None, proxy_user=None, proxy_password=None, verify=False, cert=None):
        """
        请求需要包含的字段
        :param server: 请求服务
        :param port: 请求端口
        :param scheme: 请求scheme
        :param method: 请求方法
        :param proxies: 请求封装好的代理，{"https": "https://proxy.x.x:8080"}
        :param redirect: 是否需要重定向，默认是需要重定向。requests库封装了重定向方法，不需要SDK重新发起HTTP请求
        :param timeout: 请求的超时
        :param proxy_host: 请求的代理地址
        :param proxy_port: 请求的代理端口
        :param proxy_user: 请求的代理用户名
        :param proxy_password: 请求的代理用户密码
        :param verify: 是否校验https ssl证书
        :param cert: 证书路径
        """
        self.server = server
        self.port = port
        self.proxies = proxies
        self.redirect = redirect
        self.tunnel_headers = None
        self.method = method
        self.url = None
        self.data = None
        self.scheme = scheme
        self.headers = {}
        self.timeout = timeout
        self.response = None
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_user = proxy_user
        self.proxy_password = proxy_password
        self.verify = verify
        self.cert = cert

    def get_proxy(self):
        """
        封装https的代理信息
        :return:
        """
        if self.proxy_host is None:
            return None
        return {
            self.scheme: "%s://%s%s%s" % (
                self.scheme,
                "%s:%s@" % (
                quote_plus(self.proxy_user), quote_plus(self.proxy_password)) if self.proxy_user is not None else "",
                self.proxy_host,
                ":%s" % self.proxy_port if self.proxy_port is not None else ""
            )
        }


# 默认response读的chunk大小
_CHUNK_SIZE = 8 * 1024


class Response(object):
    """
    HTTP请求的Response对象
    """

    def __init__(self, response, log_client):
        """
        地址HTTPSCONNECTION封装的response
        :param response: response对象
        :param log_client:
        """
        self.response = response
        self.status = response.status_code
        self.headers = response.headers
        self.request_id = response.headers.get('x-obs-request-id', '')
        if not self.request_id:
            self.request_id = response.headers.get('x-amz-request-id', '')
        self.reason = response.reason
        self.__read_all = False
        log_client.log(DEBUG, "Get response headers, req-id:{0}, status: {1}, headers: {2}".format(self.request_id,
                                                                                                   self.status,
                                                                                                   self.headers))

    def close(self):
        self.response.close()

    def getheaders(self):
        """
        获取response的头域列表
        :return:
        """
        return self.headers.items()

    def getheader(self, key, default_value=None):
        """
        知道key获取头域
        :param key: 头域key
        :param default_value: 默认值
        :return:
        """
        ret = self.headers.get(key)
        return ret if ret is not None else default_value

    def read(self, amt=None):
        """
        读Response
        :param amt: 可指定只读返回结果的大小
        :return: 结果
        """
        if self.__read_all:
            return b''
        if amt is None:
            content_chunks = []
            for chunk in self.response.iter_content(_CHUNK_SIZE):
                content_chunks.append(chunk)
            contents = b''.join(content_chunks)

            self.__read_all = True
            return contents
        else:
            total_count = amt
            read_sofar = 0
            content_chunks = []
            while True:
                if read_sofar >= total_count:
                    break
                read_count_once = total_count - read_sofar
                chunk = self.response.raw.read(read_count_once, decode_content=True)
                read_sofar += len(chunk)
                if not chunk:
                    self.__read_all = True
                    break
                content_chunks.append(chunk)
            contents = b''.join(content_chunks)
            return contents

    def __iter__(self):
        """
        response body的迭代器
        :return: 数据迭代读
        """
        return self.response.iter_content(_CHUNK_SIZE)
