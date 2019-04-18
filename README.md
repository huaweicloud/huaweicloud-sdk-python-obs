Version 3.1.2.1

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
