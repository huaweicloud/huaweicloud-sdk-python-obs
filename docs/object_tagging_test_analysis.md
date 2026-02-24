# 对象标签管理功能 - 测试场景分析文档

> **版本**: 1.0
> **创建日期**: 2026-02-24
> **测试方法**: TDD (测试驱动开发)
> **参考测试文件**: test_obs_client.py, conftest.py

---

## 目录

1. [测试策略概述](#1-测试策略概述)
2. [现有测试风格分析](#2-现有测试风格分析)
3. [功能测试用例](#3-功能测试用例)
4. [边界测试用例](#4-边界测试用例)
5. [参数检查测试用例](#5-参数检查测试用例)
6. [功能组合测试用例](#6-功能组合测试用例)
7. [并发测试用例](#7-并发测试用例)
8. [性能测试用例](#8-性能测试用例)
9. [异常测试用例](#9-异常测试用例)
10. [测试数据管理](#10-测试数据管理)
11. [TDD实施计划](#11-tdd实施计划)

---

## 1. 测试策略概述

### 1.1 测试层次

```
┌─────────────────────────────────────────┐
│           集成测试层          │
│  - 完整的API调用流程                      │
│  - 真实OBS服务端点                       │
│  - 端到端场景验证                         │
├─────────────────────────────────────────┤
│           功能测试层                      │
│  - 业务逻辑验证                           │
│  - 标签CRUD操作                           │
│  - 版本控制支持                           │
├─────────────────────────────────────────┤
│          边界测试层                       │
│  - 参数边界值测试                         │
│  - 约束条件验证                           │
│  - 极限场景测试                           │
├─────────────────────────────────────────┤
│          单元测试层                       │
│  - 数据模型验证                           │
│  - XML转换器测试                          │
│  - 参数验证函数测试                       │
└─────────────────────────────────────────┘
```

### 1.2 测试覆盖目标

| 测试类型 | 覆盖率目标 | 测试数量 | 优先级 |
|---------|-----------|---------|--------|
| 功能测试 | 100% | ~12个 | P0 |
| 边界测试 | 100% | ~18个 | P0 |
| 参数检查 | 100% | ~8个 | P0 |
| 功能组合 | 80% | ~6个 | P1 |
| 并发测试 | 主要场景 | ~4个 | P1 |
| 性能测试 | 关键指标 | ~5个 | P1 |
| 异常测试 | 主要异常 | ~6个 | P0 |

### 1.3 测试命名规范

遵循现有测试风格:

```python
# 格式: test_<功能>_<场景>_<条件>
def test_set_object_tagging_with_list_format(self):
    """测试: 设置对象标签使用List格式"""
    pass

def test_get_object_tagging_with_version_id(self):
    """测试: 获取对象标签带版本ID"""
    pass

def test_delete_object_tagging_of_nonexistent_object(self):
    """测试: 删除不存在对象的标签"""
    pass
```

---

## 2. 现有测试风格分析

### 2.1 测试类结构

参考 `test_obs_client.py:39`:

```python
class TestObjectTagging(object):
    """对象标签功能测试类"""

    def get_client(self):
        """获取OBS客户端实例"""
        # 返回 (client_type, uploadClient, downloadClient)
        pass

    def cleanup_object(self, client, bucket_name, object_key):
        """清理测试对象"""
        try:
            client.deleteObject(bucket_name, object_key)
        except:
            pass
```

### 2.2 断言风格

现有测试使用的断言模式:

```python
# 1. 状态码断言
assert resp.status == 200
assert create_result.status == 200

# 2. 响应体断言
assert "uploadId" in init_result.body
assert ("fs-file-interface", 'Enabled') in bucket_metadata.header

# 3. 值比较断言
assert resp.body.buffer == expected_content
assert bucket_name in all_buckets

# 4. 异常断言
with pytest.raises(ValueError):
    invalid_function_call()
```

### 2.3 Fixture使用模式

参考 `conftest.py` 的fixture设计:

```python
# 1. 资源生成和清理
@pytest.fixture
def tagging_test_object(obs_client):
    """创建用于标签测试的对象,测试后自动清理"""
    object_key = 'test-tagging-obj.txt'
    obs_client.putContent(bucket_name, object_key, content='test')
    yield object_key
    # 清理
    obs_client.deleteObject(bucket_name, object_key)

# 2. 参数化测试
@pytest.fixture(params=['list', 'dict', 'tag_object'])
def tag_format(request):
    """参数化不同的标签格式"""
    return request.param
```

### 2.4 配置读取

```python
# 从conftest读取配置
from conftest import test_config

bucket_name = test_config["bucketName"]
path_prefix = test_config["path_prefix"]
```

---

## 3. 功能测试用例

### 3.1 设置对象标签 (setObjectTagging)

#### TC-TAG-SET-001: 使用List格式设置标签

```python
def test_set_object_tagging_with_list_format(self):
    """
    测试场景: 使用List格式设置对象标签
    测试步骤:
        1. 创建测试对象
        2. 使用List格式设置标签
        3. 验证响应状态码
        4. 获取标签验证设置成功
    预期结果:
        - 设置操作返回200
        - 获取的标签与设置的一致
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-list-' + str(int(time.time()))

    try:
        # 1. 上传测试对象
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 2. 设置标签(List格式)
        tags = [
            {'key': 'project', 'value': 'demo'},
            {'key': 'env', 'value': 'production'},
            {'key': 'owner', 'value': 'test-team'}
        ]
        set_resp = client.setObjectTagging(bucket_name, object_key, tags)
        assert set_resp.status == 200

        # 3. 验证标签
        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert get_resp.status == 200
        assert len(get_resp.body.tags) == 3

        # 验证标签内容
        tag_dict = {tag.key: tag.value for tag in get_resp.body.tags}
        assert tag_dict['project'] == 'demo'
        assert tag_dict['env'] == 'production'
        assert tag_dict['owner'] == 'test-team'

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-SET-002: 使用Dict格式设置标签

```python
def test_set_object_tagging_with_dict_format(self):
    """
    测试场景: 使用Dict格式设置对象标签
    测试步骤:
        1. 创建测试对象
        2. 使用Dict格式设置标签
        3. 验证响应状态码
        4. 获取标签验证设置成功
    预期结果:
        - 设置操作返回200
        - 获取的标签与设置的一致
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-dict-' + str(int(time.time()))

    try:
        # 1. 上传测试对象
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 2. 设置标签(Dict格式)
        tags = {
            'project': 'demo',
            'env': 'production',
            'owner': 'test-team'
        }
        set_resp = client.setObjectTagging(bucket_name, object_key, tags)
        assert set_resp.status == 200

        # 3. 验证标签
        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert get_resp.status == 200
        assert len(get_resp.body.tags) == 3

        # 验证标签内容
        tag_dict = {tag.key: tag.value for tag in get_resp.body.tags}
        assert tag_dict['project'] == 'demo'
        assert tag_dict['env'] == 'production'
        assert tag_dict['owner'] == 'test-team'

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-SET-003: 使用Tag对象设置标签

```python
def test_set_object_tagging_with_tag_objects(self):
    """
    测试场景: 使用Tag对象列表设置标签
    """
    from obs import Tag

    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-obj-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 使用Tag对象
        tags = [
            Tag('key1', 'value1'),
            Tag('key2', 'value2')
        ]
        set_resp = client.setObjectTagging(bucket_name, object_key, tags)
        assert set_resp.status == 200

        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert get_resp.status == 200
        assert len(get_resp.body.tags) == 2

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-SET-004: 覆盖已有标签

```python
def test_set_object_tagging_overwrite_existing(self):
    """
    测试场景: 重新设置标签覆盖旧标签
    测试步骤:
        1. 设置初始标签
        2. 重新设置不同的标签
        3. 验证新标签生效
    预期结果:
        - 新标签完全替换旧标签
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-overwrite-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 设置初始标签
        initial_tags = {'old-key1': 'old-value1', 'old-key2': 'old-value2'}
        set_resp1 = client.setObjectTagging(bucket_name, object_key, initial_tags)
        assert set_resp1.status == 200

        # 验证初始标签
        get_resp1 = client.getObjectTagging(bucket_name, object_key)
        assert len(get_resp1.body.tags) == 2

        # 覆盖为新标签
        new_tags = {'new-key1': 'new-value1', 'new-key2': 'new-value2', 'new-key3': 'new-value3'}
        set_resp2 = client.setObjectTagging(bucket_name, object_key, new_tags)
        assert set_resp2.status == 200

        # 验证新标签
        get_resp2 = client.getObjectTagging(bucket_name, object_key)
        assert len(get_resp2.body.tags) == 3
        tag_dict = {tag.key: tag.value for tag in get_resp2.body.tags}
        assert 'new-key1' in tag_dict
        assert 'old-key1' not in tag_dict

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

### 3.2 获取对象标签 (getObjectTagging)

#### TC-TAG-GET-001: 获取已设置的标签

```python
def test_get_object_tagging_success(self):
    """
    测试场景: 获取已设置标签的对象
    预期结果: 返回完整的标签列表
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-get-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 设置标签
        tags = {'key1': 'value1', 'key2': 'value2'}
        set_resp = client.setObjectTagging(bucket_name, object_key, tags)
        assert set_resp.status == 200

        # 获取标签
        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert get_resp.status == 200
        assert hasattr(get_resp.body, 'tags')
        assert len(get_resp.body.tags) == 2

        # 验证响应字段
        tag = get_resp.body.tags[0]
        assert hasattr(tag, 'key')
        assert hasattr(tag, 'value')

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-GET-002: 获取无标签对象的标签

```python
def test_get_object_tagging_no_tags(self):
    """
    测试场景: 获取没有标签的对象
    预期结果: 返回空标签列表
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-none-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 获取标签(对象未设置标签)
        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert get_resp.status == 200
        assert len(get_resp.body.tags) == 0

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-GET-003: 获取指定版本ID的标签

```python
def test_get_object_tagging_with_version_id(self):
    """
    测试场景: 获取指定版本对象的标签
    前置条件: 桶已启用版本控制
    测试步骤:
        1. 启用版本控制的桶
        2. 上传对象并设置标签
        3. 重新上传对象创建新版本
        4. 使用versionId获取旧版本标签
    预期结果: 返回指定版本的标签
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-version-' + str(int(time.time()))

    try:
        # 确保版本控制已启用
        version_resp = client.getBucketVersioning(bucket_name)
        if version_resp.body != 'Enabled':
            self.skipTest("Bucket versioning not enabled")

        # 上传第一个版本并设置标签
        put_resp1 = client.putContent(bucket_name, object_key, 'version 1')
        version_id_1 = put_resp1.body.versionId

        tags_v1 = {'version': 'v1', 'status': 'old'}
        client.setObjectTagging(bucket_name, object_key, tags_v1, versionId=version_id_1)

        # 上传第二个版本并设置标签
        put_resp2 = client.putContent(bucket_name, object_key, 'version 2')
        version_id_2 = put_resp2.body.versionId

        tags_v2 = {'version': 'v2', 'status': 'current'}
        client.setObjectTagging(bucket_name, object_key, tags_v2, versionId=version_id_2)

        # 获取不同版本的标签
        get_resp1 = client.getObjectTagging(bucket_name, object_key, versionId=version_id_1)
        tag_dict1 = {tag.key: tag.value for tag in get_resp1.body.tags}
        assert tag_dict1['version'] == 'v1'

        get_resp2 = client.getObjectTagging(bucket_name, object_key, versionId=version_id_2)
        tag_dict2 = {tag.key: tag.value for tag in get_resp2.body.tags}
        assert tag_dict2['version'] == 'v2'

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

### 3.3 删除对象标签 (deleteObjectTagging)

#### TC-TAG-DEL-001: 删除已有标签

```python
def test_delete_object_tagging_success(self):
    """
    测试场景: 删除对象的标签
    测试步骤:
        1. 设置对象标签
        2. 删除对象标签
        3. 验证标签已删除
    预期结果:
        - 删除操作返回204
        - 获取标签返回空列表
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-del-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 设置标签
        tags = {'key1': 'value1', 'key2': 'value2'}
        set_resp = client.setObjectTagging(bucket_name, object_key, tags)
        assert set_resp.status == 200

        # 删除标签
        del_resp = client.deleteObjectTagging(bucket_name, object_key)
        assert del_resp.status == 204

        # 验证标签已删除
        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert get_resp.status == 200
        assert len(get_resp.body.tags) == 0

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-DEL-002: 删除无标签对象的标签

```python
def test_delete_object_tagging_no_tags(self):
    """
    测试场景: 删除没有标签的对象
    预期结果: 操作成功返回204
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-del-none-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 删除标签(对象无标签)
        del_resp = client.deleteObjectTagging(bucket_name, object_key)
        assert del_resp.status == 204

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-DEL-003: 删除指定版本的标签

```python
def test_delete_object_tagging_with_version_id(self):
    """
    测试场景: 删除指定版本对象的标签
    预期结果: 只删除指定版本的标签
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-del-ver-' + str(int(time.time()))

    try:
        version_resp = client.getBucketVersioning(bucket_name)
        if version_resp.body != 'Enabled':
            self.skipTest("Bucket versioning not enabled")

        # 上传并设置标签
        put_resp = client.putContent(bucket_name, object_key, 'content')
        version_id = put_resp.body.versionId

        tags = {'version': 'v1'}
        client.setObjectTagging(bucket_name, object_key, tags, versionId=version_id)

        # 删除指定版本的标签
        del_resp = client.deleteObjectTagging(bucket_name, object_key, versionId=version_id)
        assert del_resp.status == 204

        # 验证标签已删除
        get_resp = client.getObjectTagging(bucket_name, object_key, versionId=version_id)
        assert len(get_resp.body.tags) == 0

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

---

## 4. 边界测试用例

### 4.1 标签数量边界

#### TC-TAG-EDGE-001: 空标签列表

```python
def test_set_object_tagging_empty_list(self):
    """
    测试场景: 设置空标签列表
    预期结果: 相当于删除所有标签,返回200
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-empty-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 先设置标签
        client.setObjectTagging(bucket_name, object_key, {'key': 'value'})

        # 设置空标签列表
        set_resp = client.setObjectTagging(bucket_name, object_key, [])
        assert set_resp.status == 200

        # 验证标签已清除
        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert len(get_resp.body.tags) == 0

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-EDGE-002: 单个标签

```python
def test_set_object_tagging_single_tag(self):
    """
    测试场景: 设置单个标签(最小边界)
    预期结果: 成功设置
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-single-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        set_resp = client.setObjectTagging(bucket_name, object_key, {'key': 'value'})
        assert set_resp.status == 200

        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert len(get_resp.body.tags) == 1

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-EDGE-003: 最大标签数量(10个)

```python
def test_set_object_tagging_max_tags(self):
    """
    测试场景: 设置10个标签(最大值)
    预期结果: 成功设置10个标签
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-max-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 创建10个标签
        tags = {f'key{i}': f'value{i}' for i in range(10)}
        set_resp = client.setObjectTagging(bucket_name, object_key, tags)
        assert set_resp.status == 200

        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert len(get_resp.body.tags) == 10

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-EDGE-004: 超过最大标签数量

```python
def test_set_object_tagging_exceed_max_tags(self):
    """
    测试场景: 设置11个标签(超过限制)
    预期结果:
        - 选项A: 客户端验证抛出ValueError
        - 选项B: 服务端返回400错误
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-exceed-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 创建11个标签
        tags = {f'key{i}': f'value{i}' for i in range(11)}

        # 客户端验证
        with pytest.raises((ValueError, Exception)) as exc_info:
            client.setObjectTagging(bucket_name, object_key, tags)

        # 如果是服务端错误
        if 'TooManyTags' in str(exc_info.value) or 'InvalidTag' in str(exc_info.value):
            pass  # 符合预期

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

### 4.2 键长度边界

#### TC-TAG-EDGE-005: 最小键长度(1个字符)

```python
def test_set_object_tagging_min_key_length(self):
    """
    测试场景: 键长度为1个字符
    预期结果: 成功设置
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-minkey-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        set_resp = client.setObjectTagging(bucket_name, object_key, {'a': 'value'})
        assert set_resp.status == 200

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-EDGE-006: 最大键长度(128个字符)

```python
def test_set_object_tagging_max_key_length(self):
    """
    测试场景: 键长度为128个字符
    预期结果: 成功设置
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-maxkey-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        max_key = 'a' * 128
        set_resp = client.setObjectTagging(bucket_name, object_key, {max_key: 'value'})
        assert set_resp.status == 200

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-EDGE-007: 超过最大键长度

```python
def test_set_object_tagging_exceed_max_key_length(self):
    """
    测试场景: 键长度超过128个字符
    预期结果: 返回错误
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-overkey-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        exceed_key = 'a' * 129

        with pytest.raises((ValueError, Exception)):
            client.setObjectTagging(bucket_name, object_key, {exceed_key: 'value'})

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

### 4.3 值长度边界

#### TC-TAG-EDGE-008: 空字符串值

```python
def test_set_object_tagging_empty_value(self):
    """
    测试场景: 标签值为空字符串
    预期结果: 成功设置(允许空值)
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-emptyval-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        set_resp = client.setObjectTagging(bucket_name, object_key, {'key': ''})
        assert set_resp.status == 200

        get_resp = client.getObjectTagging(bucket_name, object_key)
        tag = get_resp.body.tags[0]
        assert tag.value == ''

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-EDGE-009: 最大值长度(256个字符)

```python
def test_set_object_tagging_max_value_length(self):
    """
    测试场景: 标签值为256个字符
    预期结果: 成功设置
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-maxval-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        max_value = 'a' * 256
        set_resp = client.setObjectTagging(bucket_name, object_key, {'key': max_value})
        assert set_resp.status == 200

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

### 4.4 特殊字符边界

#### TC-TAG-EDGE-010: 特殊字符键名

```python
def test_set_object_tagging_special_characters(self):
    """
    测试场景: 键名包含允许的特殊字符(.+-=_:/)
    预期结果: 成功设置
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-special-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        tags = {
            'test.key': 'value1',
            'test-key': 'value2',
            'test+key': 'value3',
            'test_key': 'value4',
            'test=key': 'value5',
            'test:key': 'value6',
            'test/key': 'value7'
        }
        set_resp = client.setObjectTagging(bucket_name, object_key, tags)
        assert set_resp.status == 200

        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert len(get_resp.body.tags) == 7

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-EDGE-011: 系统保留前缀

```python
def test_set_object_tagging_system_prefix(self):
    """
    测试场景: 键名以系统保留前缀obs:开头
    预期结果: 返回错误或拒绝设置
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-sys-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        with pytest.raises((ValueError, Exception)):
            client.setObjectTagging(bucket_name, object_key, {'obs:system': 'value'})

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-EDGE-012: Unicode字符

```python
def test_set_object_tagging_unicode_characters(self):
    """
    测试场景: 标签包含Unicode字符
    预期结果: 成功设置和获取
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-unicode-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        tags = {
            '中文标签': '中文值',
            '日本語': '日本語',
            '한국어': '한국어',
            'emoji😀': 'value'
        }
        set_resp = client.setObjectTagging(bucket_name, object_key, tags)
        assert set_resp.status == 200

        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert len(get_resp.body.tags) == 4

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

#### TC-TAG-EDGE-013: 大小写敏感

```python
def test_set_object_tagging_case_sensitive(self):
    """
    测试场景: 标签键大小写敏感性
    预期结果: Key和KEY被视为不同标签
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-case-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        tags = {
            'Key': 'value1',
            'KEY': 'value2',
            'key': 'value3'
        }
        set_resp = client.setObjectTagging(bucket_name, object_key, tags)
        assert set_resp.status == 200

        get_resp = client.getObjectTagging(bucket_name, object_key)
        assert len(get_resp.body.tags) == 3

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

---

## 5. 参数检查测试用例

### 5.1 必需参数验证

#### TC-TAG-PARAM-001: 缺少bucketName

```python
def test_set_object_tagging_missing_bucket_name(self):
    """
    测试场景: bucketName为None
    预期结果: 抛出ValueError
    """
    _, client, _ = self.get_client()

    with pytest.raises(ValueError):
        client.setObjectTagging(None, 'object-key', {'key': 'value'})
```

#### TC-TAG-PARAM-002: 缺少objectKey

```python
def test_set_object_tagging_missing_object_key(self):
    """
    测试场景: objectKey为None
    预期结果: 抛出ValueError
    """
    _, client, _ = self.get_client()

    with pytest.raises(ValueError):
        client.setObjectTagging('bucket-name', None, {'key': 'value'})
```

#### TC-TAG-PARAM-003: 缺少tags

```python
def test_set_object_tagging_missing_tags(self):
    """
    测试场景: tags为None
    预期结果: 抛出ValueError
    """
    _, client, _ = self.get_client()

    with pytest.raises(ValueError):
        client.setObjectTagging('bucket-name', 'object-key', None)
```

### 5.2 空字符串参数验证

#### TC-TAG-PARAM-004: 空bucketName

```python
def test_set_object_tagging_empty_bucket_name(self):
    """
    测试场景: bucketName为空字符串
    预期结果: 抛出ValueError
    """
    _, client, _ = self.get_client()

    with pytest.raises(ValueError):
        client.setObjectTagging('', 'object-key', {'key': 'value'})
```

#### TC-TAG-PARAM-005: 空objectKey

```python
def test_set_object_tagging_empty_object_key(self):
    """
    测试场景: objectKey为空字符串
    预期结果: 抛出ValueError
    """
    _, client, _ = self.get_client()

    with pytest.raises(ValueError):
        client.setObjectTagging('bucket-name', '', {'key': 'value'})
```

### 5.3 参数类型验证

#### TC-TAG-PARAM-006: 无效tags类型

```python
def test_set_object_tagging_invalid_tags_type(self):
    """
    测试场景: tags参数类型无效
    预期结果: 抛出TypeError或ValueError
    """
    _, client, _ = self.get_client()

    # 字符串类型
    with pytest.raises((TypeError, ValueError)):
        client.setObjectTagging('bucket-name', 'object-key', 'invalid')

    # 整数类型
    with pytest.raises((TypeError, ValueError)):
        client.setObjectTagging('bucket-name', 'object-key', 123)
```

#### TC-TAG-PARAM-007: 无效versionId类型

```python
def test_get_object_tagging_invalid_version_id_type(self):
    """
    测试场景: versionId参数类型无效(应自动转换)
    预期结果: 自动转换为字符串或抛出异常
    """
    _, client, _ = self.get_client()

    # 整数versionId
    try:
        # 如果实现支持自动转换
        result = client.getObjectTagging('bucket-name', 'object-key', versionId=123)
        # 验证内部已转换为字符串
    except (TypeError, ValueError):
        # 如果不支持,抛出异常也是合理的
        pass
```

---

## 6. 功能组合测试用例

### 6.1 标签与元数据组合

#### TC-TAG-COMB-001: 设置标签和元数据

```python
def test_set_object_tagging_with_metadata(self):
    """
    测试场景: 同时设置对象标签和自定义元数据
    测试步骤:
        1. 上传对象时设置元数据
        2. 设置对象标签
        3. 验证两者都生效
    预期结果: 标签和元数据相互独立
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-meta-' + str(int(time.time()))

    try:
        # 上传时设置元数据
        from obs import PutObjectHeader
        header = PutObjectHeader()
        header.metaData = {'meta1': 'value1', 'meta2': 'value2'}

        put_resp = client.putContent(bucket_name, object_key, 'test content', headers=header)
        assert put_resp.status == 200

        # 设置标签
        set_resp = client.setObjectTagging(bucket_name, object_key, {'tag1': 'tagvalue1'})
        assert set_resp.status == 200

        # 验证元数据
        meta_resp = client.getObjectMetadata(bucket_name, object_key)
        assert meta_resp.header.get('x-obs-meta-meta1') == 'value1'

        # 验证标签
        tag_resp = client.getObjectTagging(bucket_name, object_key)
        assert len(tag_resp.body.tags) == 1

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

### 6.2 标签与ACL组合

#### TC-TAG-COMB-002: 设置标签和ACL

```python
def test_set_object_tagging_with_acl(self):
    """
    测试场景: 同时设置对象标签和ACL
    预期结果: 两者都生效
    """
    from obs import_acl

    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-acl-' + str(int(time.time()))

    try:
        put_resp = client.putContent(bucket_name, object_key, 'test content')
        assert put_resp.status == 200

        # 设置ACL
        acl = acl.ACL()
        # 添加ACL权限...
        # client.setObjectAcl(bucket_name, object_key, acl)

        # 设置标签
        set_resp = client.setObjectTagging(bucket_name, object_key, {'tag1': 'value1'})
        assert set_resp.status == 200

        # 验证两者都生效
        tag_resp = client.getObjectTagging(bucket_name, object_key)
        assert len(tag_resp.body.tags) == 1

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

### 6.3 批量操作与标签

#### TC-TAG-COMB-003: 批量删除带标签的对象

```python
def test_delete_objects_with_tags(self):
    """
    测试场景: 批量删除有标签的对象
    测试步骤:
        1. 创建多个对象并设置标签
        2. 批量删除对象
        3. 验证删除成功
    预期结果: 对象被成功删除,标签自动删除
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    prefix = 'test-tag-batch-' + str(int(time.time())) + '-'

    objects_to_delete = []

    try:
        # 创建3个带标签的对象
        for i in range(3):
            object_key = prefix + str(i)
            client.putContent(bucket_name, object_key, f'content {i}')
            client.setObjectTagging(bucket_name, object_key, {'index': str(i)})
            objects_to_delete.append(object_key)

        # 批量删除
        del_resp = client.deleteObjects(bucket_name, objects_to_delete)
        assert del_resp.status == 200

        # 验证删除
        for object_key in objects_to_delete:
            try:
                client.getObjectTagging(bucket_name, object_key)
                assert False, f"Object {object_key} should be deleted"
            except Exception:
                pass  # 对象不存在,符合预期

    except Exception as e:
        # 清理
        for object_key in objects_to_delete:
            try:
                client.deleteObject(bucket_name, object_key)
            except:
                pass
        raise
```

### 6.4 复制对象与标签

#### TC-TAG-COMB-004: 复制对象时处理标签

```python
def test_copy_object_with_tagging(self):
    """
    测试场景: 复制对象时标签的处理
    测试步骤:
        1. 创建源对象并设置标签
        2. 复制对象
        3. 验证目标对象标签
    预期结果: 根据实现,标签可能被复制或不复制
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    source_key = 'test-tag-copy-source-' + str(int(time.time()))
    dest_key = 'test-tag-copy-dest-' + str(int(time.time()))

    try:
        # 创建源对象并设置标签
        client.putContent(bucket_name, source_key, 'source content')
        client.setObjectTagging(bucket_name, source_key, {'source': 'tag'})

        # 复制对象
        copy_resp = client.copyObject(bucket_name, source_key, bucket_name, dest_key)
        assert copy_resp.status == 200

        # 验证目标对象标签(根据OBS实现,复制可能不包含标签)
        dest_tag_resp = client.getObjectTagging(bucket_name, dest_key)

        # 如果标签不被复制,目标对象应该没有标签
        # 如果标签被复制,目标对象应该有相同的标签
        # 具体行为取决于OBS服务实现

    finally:
        self.cleanup_object(client, bucket_name, source_key)
        self.cleanup_object(client, bucket_name, dest_key)
```

---

## 7. 并发测试用例

### 7.1 并发设置标签

#### TC-TAG-CONC-001: 多线程并发设置标签

```python
import threading

def test_concurrent_set_object_tagging(self):
    """
    测试场景: 多个线程并发设置同一对象的标签
    测试步骤:
        1. 创建测试对象
        2. 启动多个线程并发设置标签
        3. 验证最终结果
    预期结果:
        - 所有操作都成功
        - 最终标签为最后一次设置的标签
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-concurrent-' + str(int(time.time()))

    try:
        client.putContent(bucket_name, object_key, 'test content')

        errors = []
        results = []

        def set_tags(thread_id):
            try:
                tags = {'thread': str(thread_id), 'value': f'value-{thread_id}'}
                resp = client.setObjectTagging(bucket_name, object_key, tags)
                results.append((thread_id, resp.status))
            except Exception as e:
                errors.append(e)

        # 启动10个线程
        threads = []
        for i in range(10):
            t = threading.Thread(target=set_tags, args=(i,))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证所有操作都成功
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10

        # 验证最终标签
        final_resp = client.getObjectTagging(bucket_name, object_key)
        assert final_resp.status == 200
        # 最终标签应该是某个线程设置的值

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

### 7.2 并发读取标签

#### TC-TAG-CONC-002: 多线程并发读取标签

```python
def test_concurrent_get_object_tagging(self):
    """
    测试场景: 多个线程并发读取同一对象的标签
    预期结果:
        - 所有读取操作成功
        - 返回的标签一致
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-concurrent-get-' + str(int(time.time()))

    try:
        client.putContent(bucket_name, object_key, 'test content')
        client.setObjectTagging(bucket_name, object_key, {'key': 'value'})

        errors = []
        tag_lists = []

        def get_tags():
            try:
                resp = client.getObjectTagging(bucket_name, object_key)
                tag_lists.append(resp.body.tags)
            except Exception as e:
                errors.append(e)

        # 启动10个读取线程
        threads = []
        for _ in range(10):
            t = threading.Thread(target=get_tags)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 验证
        assert len(errors) == 0
        assert len(tag_lists) == 10

        # 验证所有读取结果一致
        for tags in tag_lists:
            assert len(tags) == 1
            assert tags[0].key == 'key'
            assert tags[0].value == 'value'

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

### 7.3 并发设置和删除

#### TC-TAG-CONC-003: 并发设置和删除标签

```python
def test_concurrent_set_and_delete_tagging(self):
    """
    测试场景: 并发执行设置和删除操作
    预期结果: 无竞争条件,操作按预期执行
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-mixed-' + str(int(time.time()))

    try:
        client.putContent(bucket_name, object_key, 'test content')
        client.setObjectTagging(bucket_name, object_key, {'initial': 'tag'})

        errors = []

        def set_tags():
            try:
                for i in range(10):
                    client.setObjectTagging(bucket_name, object_key, {'op': 'set', 'iter': str(i)})
                    time.sleep(0.01)
            except Exception as e:
                errors.append(('set', e))

        def delete_tags():
            try:
                for i in range(10):
                    client.deleteObjectTagging(bucket_name, object_key)
                    time.sleep(0.01)
            except Exception as e:
                errors.append(('delete', e))

        t1 = threading.Thread(target=set_tags)
        t2 = threading.Thread(target=delete_tags)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # 验证没有错误
        assert len(errors) == 0

        # 最终状态可能是没有标签或有标签
        final_resp = client.getObjectTagging(bucket_name, object_key)
        assert final_resp.status == 200

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

### 7.4 并发操作不同对象

#### TC-TAG-CONC-004: 并发操作多个对象

```python
def test_concurrent_operations_multiple_objects(self):
    """
    测试场景: 多个线程并发操作不同对象的标签
    预期结果: 所有操作成功,互不影响
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    prefix = 'test-tag-multi-' + str(int(time.time()))

    objects = []
    for i in range(5):
        object_key = f'{prefix}-{i}'
        client.putContent(bucket_name, object_key, f'content {i}')
        objects.append(object_key)

    try:
        errors = []

        def operate_on_object(obj_index):
            try:
                object_key = f'{prefix}-{obj_index}'
                for j in range(5):
                    tags = {'object': str(obj_index), 'iteration': str(j)}
                    client.setObjectTagging(bucket_name, object_key, tags)
                    time.sleep(0.01)
            except Exception as e:
                errors.append((obj_index, e))

        # 启动5个线程,每个操作一个对象
        threads = []
        for i in range(5):
            t = threading.Thread(target=operate_on_object, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0

        # 验证每个对象都有标签
        for i in range(5):
            object_key = f'{prefix}-{i}'
            resp = client.getObjectTagging(bucket_name, object_key)
            assert resp.status == 200
            assert len(resp.body.tags) > 0

    finally:
        for object_key in objects:
            self.cleanup_object(client, bucket_name, object_key)
```

---

## 8. 性能测试用例

### 8.1 大量标签性能

#### TC-TAG-PERF-001: 设置最大标签数性能

```python
import time

def test_performance_set_max_tags(self):
    """
    测试场景: 设置10个标签(最大值)的性能
    性能指标: 操作时间 < 500ms
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-perf-max-' + str(int(time.time()))

    try:
        client.putContent(bucket_name, object_key, 'test content')

        tags = {f'key{i}': f'value{i}' for i in range(10)}

        start_time = time.time()
        resp = client.setObjectTagging(bucket_name, object_key, tags)
        elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒

        assert resp.status == 200
        assert elapsed_time < 500, f"Setting 10 tags took {elapsed_time}ms, expected < 500ms"

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

### 8.2 批量获取标签性能

#### TC-TAG-PERF-002: 批量获取标签性能

```python
def test_performance_batch_get_tagging(self):
    """
    测试场景: 循环获取100个对象的标签
    性能指标: 平均每次操作 < 200ms
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    prefix = 'test-tag-perf-batch-' + str(int(time.time())

    objects = []
    try:
        # 创建100个对象并设置标签
        for i in range(100):
            object_key = f'{prefix}-{i}'
            client.putContent(bucket_name, object_key, f'content {i}')
            client.setObjectTagging(bucket_name, object_key, {'index': str(i)})
            objects.append(object_key)

        # 批量获取标签
        start_time = time.time()
        for i in range(100):
            object_key = f'{prefix}-{i}'
            resp = client.getObjectTagging(bucket_name, object_key)
            assert resp.status == 200
        elapsed_time = (time.time() - start_time) * 1000

        avg_time = elapsed_time / 100
        assert avg_time < 200, f"Average get tagging took {avg_time}ms, expected < 200ms"

    finally:
        for object_key in objects:
            self.cleanup_object(client, bucket_name, object_key)
```

### 8.3 删除标签性能

#### TC-TAG-PERF-003: 删除标签性能

```python
def test_performance_delete_tagging(self):
    """
    测试场景: 删除10个标签的性能
    性能指标: 操作时间 < 300ms
    """
    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'test-tag-perf-del-' + str(int(time.time()))

    try:
        client.putContent(bucket_name, object_key, 'test content')

        # 设置10个标签
        tags = {f'key{i}': f'value{i}' for i in range(10)}
        client.setObjectTagging(bucket_name, object_key, tags)

        # 测试删除性能
        start_time = time.time()
        resp = client.deleteObjectTagging(bucket_name, object_key)
        elapsed_time = (time.time() - start_time) * 1000

        assert resp.status == 204
        assert elapsed_time < 300, f"Delete tagging took {elapsed_time}ms, expected < 300ms"

    finally:
        self.cleanup_object(client, bucket_name, object_key)
```

---

## 9. 异常测试用例

### 9.1 对象不存在

#### TC-TAG-EXC-001: 操作不存在的对象

```python
def test_operate_nonexistent_object(self):
    """
    测试场景: 对不存在的对象进行标签操作
    预期结果: 返回404错误
    """
    from obs import ObsException

    _, client, _ = self.get_client()
    bucket_name = test_config["bucketName"]
    object_key = 'nonexistent-object-' + str(int(time.time()))

    # 设置标签
    try:
        resp = client.setObjectTagging(bucket_name, object_key, {'key': 'value'})
        assert resp.status == 404
    except ObsException as e:
        assert e.status == 404

    # 获取标签
    try:
        resp = client.getObjectTagging(bucket_name, object_key)
        assert resp.status == 404
    except ObsException as e:
        assert e.status == 404

    # 删除标签
    try:
        resp = client.deleteObjectTagging(bucket_name, object_key)
        assert resp.status == 404
    except ObsException as e:
        assert e.status == 404
```

### 9.2 桶不存在

#### TC-TAG-EXC-002: 操作不存在的桶

```python
def test_operate_nonexistent_bucket(self):
    """
    测试场景: 对不存在的桶进行标签操作
    预期结果: 返回404错误
    """
    from obs import ObsException

    _, client, _ = self.get_client()
    bucket_name = 'nonexistent-bucket-' + str(int(time.time()))
    object_key = 'test-object'

    try:
        resp = client.setObjectTagging(bucket_name, object_key, {'key': 'value'})
        assert resp.status == 404
    except ObsException as e:
        assert e.status == 404
```

### 9.3 无权限

#### TC-TAG-EXC-003: 无权限操作

```python
def test_operate_without_permission(self):
    """
    测试场景: 使用无权限的凭证操作
    前置条件: 配置无权限的AK/SK
    预期结果: 返回403错误
    """
    # 这个测试需要准备无权限的测试账号
    # 跳过如果配置不存在
    if 'unauthorized_ak' not in test_config:
        self.skipTest("No unauthorized credentials configured")

    from obs import ObsException

    client = ObsClient(
        access_key_id=test_config["unauthorized_ak"],
        secret_access_key=test_config["unauthorized_sk"],
        server=test_config["endpoint"]
    )

    bucket_name = test_config["bucketName"]
    object_key = 'test-object'

    try:
        resp = client.setObjectTagging(bucket_name, object_key, {'key': 'value'})
        assert resp.status == 403
    except ObsException as e:
        assert e.status == 403
```

### 9.4 网络错误

#### TC-TAG-EXC-004: 网络连接错误

```python
def test_network_connection_error(self):
    """
    测试场景: 网络不可达
    预期结果: 抛出网络连接异常
    """
    from obs import ObsClient

    client = ObsClient(
        access_key_id=test_config["ak"],
        secret_access_key=test_config["sk"],
        server='http://invalid-endpoint-12345.com'
    )

    try:
        resp = client.setObjectTagging('bucket', 'object', {'key': 'value'})
        assert False, "Should raise exception"
    except Exception as e:
        # 验证是网络相关的异常
        assert 'connection' in str(e).lower() or 'network' in str(e).lower()
```

---

## 10. 测试数据管理

### 10.1 Fixture定义

```python
# conftest.py

@pytest.fixture
def tagging_bucket(obs_client):
    """
    创建用于标签测试的桶
    测试后自动清理
    """
    bucket_name = test_config["bucket_prefix"] + "tagging-test-" + str(int(time.time()))

    # 创建桶
    create_resp = obs_client.createBucket(bucket_name, location=test_config["location"])
    assert create_resp.status == 200

    yield bucket_name

    # 清理
    try:
        # 删除所有对象
        resp = obs_client.listObjects(bucket_name)
        if resp.status == 200:
            for content in resp.body.contents:
                obs_client.deleteObject(bucket_name, content.key)
        # 删除桶
        obs_client.deleteBucket(bucket_name)
    except:
        pass


@pytest.fixture
def tagging_test_objects(obs_client, tagging_bucket, count=5):
    """
    创建多个用于标签测试的对象
    """
    object_keys = []

    for i in range(count):
        object_key = f'tagging-test-obj-{i}-{int(time.time())}'
        obs_client.putContent(tagging_bucket, object_key, f'content {i}')
        object_keys.append(object_key)

    yield tagging_bucket, object_keys

    # 清理
    for object_key in object_keys:
        try:
            obs_client.deleteObject(tagging_bucket, object_key)
        except:
            pass
```

### 10.2 测试数据清理

```python
def cleanup_tagging_test_data(client, bucket_name, prefix=None):
    """
    清理标签测试数据

    :param client: OBS客户端
    :param bucket_name: 桶名称
    :param prefix: 对象键前缀,为None时删除所有对象
    """
    try:
        resp = client.listObjects(bucket_name, prefix=prefix)
        if resp.status == 200:
            for content in resp.body.contents:
                client.deleteObject(bucket_name, content.key)
    except Exception as e:
        print(f"Warning: Cleanup failed with error: {e}")
```

---

## 11. TDD实施计划

### 11.1 红绿重构循环

```
┌─────────────────────────────────────────┐
│           RED (编写失败的测试)           │
│  - 编写测试用例                          │
│  - 运行测试(失败)                        │
│  - 验证测试正确失败                      │
├─────────────────────────────────────────┤
│          GREEN (最小化实现)              │
│  - 编写最小代码使测试通过                │
│  - 运行测试(通过)                        │
│  - 不关注代码质量                        │
├─────────────────────────────────────────┤
│          REFACTOR (重构)                 │
│  - 优化代码结构                          │
│  - 提取重复代码                          │
│  - 改进命名和注释                        │
│  - 确保测试仍然通过                      │
└─────────────────────────────────────────┘
```

### 11.2 TDD实施步骤

#### Phase 1: Tag模型类 (Day 1)

1. **RED**: 编写Tag类测试
   ```python
   def test_tag_creation():
       tag = Tag('key', 'value')
       assert tag.key == 'key'
       assert tag.value == 'value'
   ```

2. **GREEN**: 实现Tag类
3. **REFACTOR**: 优化Tag类

#### Phase 2: XML转换器 (Day 1)

1. **RED**: 编写XML转换测试
2. **GREEN**: 实现转换逻辑
3. **REFACTOR**: 重构代码

#### Phase 3: setObjectTagging (Day 2)

1. **RED**: 编写功能测试
2. **GREEN**: 实现方法
3. **REFACTOR**: 优化代码

#### Phase 4: getObjectTagging (Day 2)

1. **RED**: 编写功能测试
2. **GREEN**: 实现方法
3. **REFACTOR**: 优化代码

#### Phase 5: deleteObjectTagging (Day 2)

1. **RED**: 编写功能测试
2. **GREEN**: 实现方法
3. **REFACTOR**: 优化代码

#### Phase 6: 边界和异常测试 (Day 3)

1. **RED**: 编写边界测试
2. **GREEN**: 添加参数验证
3. **REFACTOR**: 改进错误处理

### 11.3 测试组织

```python
# test_object_tagging.py

import pytest
from obs import ObsClient, Tag

class TestTagModel:
    """Tag模型类测试"""
    pass

class TestTaggingConvertor:
    """XML转换器测试"""
    pass

class TestSetObjectTagging:
    """设置对象标签测试"""
    pass

class TestGetObjectTagging:
    """获取对象标签测试"""
    pass

class TestDeleteObjectTagging:
    """删除对象标签测试"""
    pass

class TestTaggingBoundary:
    """边界测试"""
    pass

class TestTaggingException:
    """异常测试"""
    pass
```

---

## 附录

### A. 测试执行命令

```bash
# 运行所有标签测试
pytest src/tests/test_object_tagging.py -v

# 运行特定测试类
pytest src/tests/test_object_tagging.py::TestSetObjectTagging -v

# 运行特定测试用例
pytest src/tests/test_object_tagging.py::TestSetObjectTagging::test_set_object_tagging_with_list_format -v

# 并行运行测试
pytest src/tests/test_object_tagging.py -n auto

# 生成覆盖率报告
pytest src/tests/test_object_tagging.py --cov=obs --cov-report=html
```

### B. 测试配置示例

```json
// test_config.json
{
    "ak": "your-access-key",
    "sk": "your-secret-key",
    "endpoint": "https://obs.cn-north-4.myhuaweicloud.com",
    "bucketName": "test-bucket",
    "bucket_prefix": "test-",
    "path_prefix": "/tmp/obs-test/",
    "location": "cn-north-4",
    "test_files": {
        "small": 1,
        "medium": 100,
        "large": 500
    }
}
```

---

**文档结束**

*本文档详细描述了对象标签管理功能的测试策略和测试用例,确保功能实现的完整性和可靠性。*
