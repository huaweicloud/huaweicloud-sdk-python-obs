# 安装

```
pip install esdk-obs-python
```

# 更新日志

Version 3.20.11

新特性：

资料&demo:

修复问题：
1. 修复uploadFile/downloadFile接口，不支持指定携带加密头域的问题；

-------------------------------------------------------------------------------------------------
Version 3.20.9.1

新特性：

资料&demo:

修复问题：
1. 修复调用uploadFile接口同时指定checkSum和enableCheckpoint参数为True时抛出异常的问题；

-------------------------------------------------------------------------------------------------
Version 3.20.5

新特性：
1. 新增异步抓取策略相关接口(ObsClient.setBucketFetchPolicy/ObsClient.getBucketFetchPolicy/ObsClient.deleteBucketFetchPolicy)；
2. 新增异步抓取任务相关接口(ObsClient.setBucketFetchJob/ObsClient.getBucketFetchJob)；
3. 新增服务编排接口（详见obs.workflow.py）；

资料&demo:
1. 开发指南文档新增异步抓取、服务编排章节；
2. 接口参考文档新增异步抓取接口、服务编排接口章节；
3. 接口参考文档预定义常量章节新增异步抓取策略状态，数据类型章节新增异步抓取接口、服务编排接口相关响应结果的描述；

修复问题：

-------------------------------------------------------------------------------------------------

Version 3.20.1

新特性：
1. 新增判断对象是否存在的接口(ObsClient.headObject)；
2. 新增设置桶请求者付费配置和获取桶请求者付费配置的接口(ObsClient.setBucketRequestPayment/ObsClient.getBucketRequestPayment)；
3. 新增对请求者付费头域的支持，可以通过设置接口的extensionHeaders参数来配置携带请求者付费头域；

资料&demo:
1. 开发指南文档管理对象章节新增判断对象是否存在，接口参考文档对象相关接口章节新增判断对象是否存在；
2. 开发指南文档管理桶章节新增管理桶请求者付费，接口参考文档桶相关接口章节新增设置桶的请求者付费配置和获取桶的请求者付费配置，数据类型章节新增获取桶请求者付费配置响应结果及拓展附加头域；
3. 接口参考文档预定义常量章节新增请求者付费配置；
4. 接口参考文档各接口方法定义中新增对拓展附加头域的描述；

修复问题：

-------------------------------------------------------------------------------------------------

Version 3.19.11

资料&demo:

修复问题：
1. 修复在GET请求返回302情况下进行重定向会添加鉴权信息头的问题；
2. 修复根据文件名后缀获取content-type类型时不支持大写文件名后缀的问题；
3. 修复Authentication make_canonicalstring计算鉴权接口中请求参数排序有误的问题；
4. 修改示例代码 examples/concurrent_copy_part_sample.py中不处理失败请求的问题；
5. 修改示例代码 examples/concurrent_download_object_sample.py中不处理失败请求的问题；
6. 修改示例代码 examples/concurrent_upload_part_sample.py中不处理失败请求的问题。
7. 修复匿名访问方式下，部分响应字段为空的问题。
-------------------------------------------------------------------------------------------------

Version 3.19.7.2

资料&demo:

修复问题：
1. 修复包相对导入方式在Python3.x版本不兼容的问题；
-------------------------------------------------------------------------------------------------

Version 3.19.7.1

新特性：
1. 创建OBS客户端接口（ObsClient）新增对以自定义方式获取访问秘钥创建OBS客户端的支持。当前提供从环境变量中获取访问秘钥及从ECS服务器上获取临时访问秘钥两种获取方式，允许自定义其他获取方式。同时支持多种获取方式的组合，对多种获取方式的组合，支持以链式方式或指定方式的形式获取访问秘钥创建OBS客户端；

资料&demo:
1. 接口参考OBS客户端初始化章节，新增security_providers参数及security_provider_policy参数；
2. 接口参考OBS客户端初始化章节，代码样例新增以预定义方式获取访问秘钥创建OBS客户端；
3. 开发指南创建OBS客户端章节，新增预定义方式获取访问秘钥及组合方式获取访问秘钥创建OBS客户端的代码示例；
4. 开发指南配置OBS客户端章节，新增security_providers参数及security_provider_policy参数；

修复问题：
-------------------------------------------------------------------------------------------------

Version 3.19.5.2

资料&demo:

修复问题：
1. 修复调用接口出现broken pipe异常后会导致报错no attribute的问题；
-------------------------------------------------------------------------------------------------

Version 3.19.5.1

资料&demo:
1. 接口参考OBS客户端初始化章节，新增max_redirect_count参数；
2. 开发指南配置OBS客户端章节，新增max_redirect_count参数；

修复问题：
1. 修复GET请求，服务端返回无限次重定向，导致无限循环。新增max_redirect_count参数可有限次重定向，并超过最大重定向次数数抛出异常；
-------------------------------------------------------------------------------------------------

Version 3.19.5
更新发布版本号，新的版本号命名方式：主版本号.年标识.月标识。

新特性：
1. 断点续传上传接口（uploadFile）新增header附加头域，可在头域中设置acl, storageClass等参数；
2. OBS非2xx的状态响应默认增加error级别的日志记录；

资料&demo:
1. 接口参考数据类型章节新增对断点续传上传附加头域的参数描述；
2. 接口参考预定义常量章节，预定义访问策略新增BUCKET_OWNER_FULL_CONTROL值；
3. 开发指南快速入门章节新增临时访问密钥的创建和使用；

修复问题：
1. 修复GET请求，服务端返回302重定向时，新的请求没有提取Location完整信息的问题；
2. 修复特殊场景下，日志切割引发进程异常退出的问题；
3. 优化断点续传上传接口（uploadFile），将默认分段大小更新为9MB；
4. 修复bucketClient不支持桶加密相关接口的问题；
-------------------------------------------------------------------------------------------------

Version 3.1.4
新特性：

资料&demo:

修复问题：
1. 修复使用chunk模式上传对象时，不符合HTTP规范的问题；
2. 修复ObsClient.putContent/ObsClient.putObject/ObsClient.putFile/ObsClient.appendObject/ObsClient.uploadPart开启进度条后，在报错场景下未及时清理进度的问题；
3. 修复ObsClient.initLog可能导致日志冲突的问题，修改OBS客户端的日志为不继承父配置；
4. 修复ObsClient.close方法未正常关闭日志文件句柄的问题；

-------------------------------------------------------------------------------------------------

Version 3.1.2.1
新特性：
1. 新增桶加密接口（ObsClient.setBucketEncryption/ObsClient.getBucketEncryption/ObsClient.deleteBucketEncryption），目前仅支持SSE-KMS的服务端加密方式；
2. 对象上传相关接口（ObsClient.putContent/ObsClient.putObject/ObsClient.appendObject/ObsClient.uploadPart）新增是否自动关闭输入流标识符，默认为 True；

资料&demo:

修复问题：
1. 修复linux操作系统下，多次初始化ObsClient导致的fork多个子进程的问题。


-------------------------------------------------------------------------------------------------
Version 3.1.2
新特性：
1. 桶事件通知接口（ObsClient.setBucketNotification/ObsClient.getBucketNotification）新增对函数工作流服务配置和查询的支持；
2. 断点续传下载接口（ObsClient.downloadFile）新增图片转码参数；
3. 新增批量下载接口（ObsClient.downloadFiles）, 支持按指定前缀下载对象，支持进度返回、大文件自动分段下载和断点续传下载；

资料&demo:
1. 开发指南事件通知章节，新增对函数工作流服务配置的介绍；
2. 接口参考设置/获取桶的事件通知配置章节，新增函数工作流服务配置的参数描述；
3. 开发指南访问日志章节，修改开启桶日志小节的代码示例；

修复问题：
1. 修复创建桶接口（ObsClient.createBucket）由于协议协商导致报错信息不准确的问题；
2. 修复示例代码 examples/obs_python_sample.py中 SetBucketLogging函数的错误；
3. 修复SDK上传对象接口（ObsClient.setObjectMetadata）接口对contentDisposition参数处理有误的问题；
4. 修改对象临时鉴权访问接口（ObsClient.createSignedUrl)对特殊字符的编码策略，将'~'符号作为URL编码保留字符，解决Python2.x/3.x环境结果不一致的问题；
5. 优化底层代码，提升SDK在Python2.x环境下小文件上传/下载的性能；
6. 修复在linux操作系统下，引入obs包会fork进程的问题；