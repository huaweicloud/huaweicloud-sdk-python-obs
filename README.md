Version 3.1.4
新特性：

资料&demo:

修复问题：
1. 修复使用chunk模式上传对象时，不符合HTTP规范的问题；
2. 修复ObsClient.putContent/ObsClient.putObject/ObsClient.putFile/ObsClient.appendObject/ObsClient.uploadPart开启进度条后，在报错场景下未及时清理进度的问题；
3. 修复ObsClient.initLog可能导致日志冲突的问题，修改为不继承父配置；
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
2. 接口参考设置/获取桶的时间通知配置章节，新增函数工作流服务配置的参数描述；
3. 开发指南访问日志章节，修改开启桶日志小节的代码示例；

修复问题：
1. 修复创建桶接口（ObsClient.createBucket）由于协议协商导致报错信息不准确的问题；
2. 修复示例代码 examples/obs_python_sample.py中 SetBucketLogging函数的错误；
3. 修复SDK上传对象接口（ObsClient.setObjectMetadata）接口对contentDisposition参数处理有误的问题；
4. 修改对象临时鉴权访问接口（ObsClient.createSignedUrl)对特殊字符的编码策略，将'~'符号作为URL编码保留字符，解决Python2.x/3.x环境结果不一致的问题；
5. 优化底层代码，提升SDK在Python2.x环境下小文件上传/下载的性能；
6. 修复在linux操作系统下，引入obs包会fork进程的问题；