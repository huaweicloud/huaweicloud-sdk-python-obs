# 对象标签管理功能实现设计文档

> **版本**: 1.0
> **创建日期**: 2026-02-24
> **功能优先级**: P0 - 核心业务功能
> **预估工作量**: 3-5天

---

## 目录

1. [功能概述](#1-功能概述)
2. [API设计](#2-api设计)
3. [数据模型](#3-数据模型)
4. [实现方案](#4-实现方案)
5. [测试策略](#5-测试策略)
6. [错误处理](#6-错误处理)
7. [兼容性设计](#7-兼容性设计)
8. [实现清单](#8-实现清单)

---

## 1. 功能概述

### 1.1 功能描述

对象标签(Object Tagging)功能允许用户为存储桶中的对象设置键值对标签,用于对象的精细化管理和分类。标签可以用于:

- **权限控制**: 基于标签的访问策略
- **生命周期管理**: 根据标签设置不同的生命周期规则
- **成本分摊**: 按标签进行成本分析和分摊
- **对象分类**: 便于管理和检索大量对象

### 1.2 API规格

根据华为云OBS API规范,对象标签管理包含以下三个接口:

| 接口 | HTTP方法 | 说明 |
|------|----------|------|
| setObjectTagging | PUT | 设置或覆盖对象标签 |
| getObjectTagging | GET | 获取对象标签 |
| deleteObjectTagging | DELETE | 删除对象标签 |

### 1.3 约束条件

- 标签数量限制: 单个对象最多10个标签
- 键名约束:
  - 长度: 1-128个字符
  - 字符集: 支持字母、数字、空格和特殊字符 `.+-=_:/`
  - 区分大小写
  - 不能以`obs:`开头(系统保留前缀)
- 键值约束:
  - 长度: 0-256个字符
  - 字符集: 支持字母、数字、空格和特殊字符 `.+-=_:/`
  - 区分大小写

---

## 2. API设计

### 2.1 方法签名

```python
def setObjectTagging(
    self,
    bucketName: str,
    objectKey: str,
    tags: Union[List[Dict[str, str]], Dict[str, str]],
    versionId: Optional[str] = None,
    extensionHeaders: Optional[Dict[str, str]] = None
) -> SetObjectTaggingResponse:
    """
    设置对象标签

    :param bucketName: 桶名称
    :param objectKey: 对象名称
    :param tags: 标签列表或字典
        - List格式: [{'key': 'env', 'value': 'prod'}, {'key': 'project', 'value': 'demo'}]
        - Dict格式: {'env': 'prod', 'project': 'demo'}
    :param versionId: 对象版本ID(可选)
    :param extensionHeaders: 扩展请求头(可选)
    :return: SetObjectTaggingResponse
    """

def getObjectTagging(
    self,
    bucketName: str,
    objectKey: str,
    versionId: Optional[str] = None,
    extensionHeaders: Optional[Dict[str, str]] = None
) -> GetObjectTaggingResponse:
    """
    获取对象标签

    :param bucketName: 桶名称
    :param objectKey: 对象名称
    :param versionId: 对象版本ID(可选)
    :param extensionHeaders: 扩展请求头(可选)
    :return: GetObjectTaggingResponse
    """

def deleteObjectTagging(
    self,
    bucketName: str,
    objectKey: str,
    versionId: Optional[str] = None,
    extensionHeaders: Optional[Dict[str, str]] = None
) -> DeleteObjectTaggingResponse:
    """
    删除对象标签

    :param bucketName: 桶名称
    :param objectKey: 对象名称
    :param versionId: 对象版本ID(可选)
    :param extensionHeaders: 扩展请求头(可选)
    :return: DeleteObjectTaggingResponse
    """
```

### 2.2 参数设计要点

1. **灵活的标签输入**: 支持List和Dict两种格式
   - List格式: 适合需要保持顺序的场景
   - Dict格式: 更简洁,适合大多数场景

2. **版本控制支持**: 通过`versionId`参数支持版本控制

3. **扩展头支持**: `extensionHeaders`保持与其他API的一致性

---

## 3. 数据模型

### 3.1 标签对象

```python
class Tag(object):
    """
    对象标签

    :param key: 标签键
    :param value: 标签值
    """
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return False
        return self.key == other.key and self.value == other.value

    def to_dict(self):
        """转换为字典"""
        return {'key': self.key, 'value': self.value}

    @classmethod
    def from_dict(cls, dict_data):
        """从字典创建"""
        return cls(key=dict_data.get('key'), value=dict_data.get('value'))
```

### 3.2 响应对象

```python
class SetObjectTaggingResponse(GetResult):
    """设置对象标签响应"""
    def __init__(self, body, headers):
        super(SetObjectTaggingResponse, self).__init__(body, headers)
        # 继承GetResult的所有属性: status, requestId, versionId等

class GetObjectTaggingResponse(GetResult):
    """获取对象标签响应"""
    def __init__(self, body, headers):
        super(GetObjectTaggingResponse, self).__init__(body, headers)
        self.tags = []  # List[Tag]
        # 从body中解析标签列表

class DeleteObjectTaggingResponse(GetResult):
    """删除对象标签响应"""
    def __init__(self, body, headers):
        super(DeleteObjectTaggingResponse, self).__init__(body, headers)
        # 继承GetResult的所有属性
```

### 3.3 XML结构

**请求XML (setObjectTagging):**
```xml
<Tagging>
    <TagSet>
        <Tag>
            <Key>project</Key>
            <Value>demo</Value>
        </Tag>
        <Tag>
            <Key>env</Key>
            <Value>production</Value>
        </Tag>
    </TagSet>
</Tagging>
```

**响应XML (getObjectTagging):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Tagging>
    <TagSet>
        <Tag>
            <Key>project</Key>
            <Value>demo</Value>
        </Tag>
        <Tag>
            <Key>env</Key>
            <Value>production</Value>
        </Tag>
    </TagSet>
</Tagging>
```

---

## 4. 实现方案

### 4.1 文件组织

```
src/obs/
├── client.py                 # 添加三个标签管理方法
├── model.py                  # 添加Tag类和响应类
├── convertor.py              # 添加标签相关的XML转换
└── const.py                  # 添加标签相关常量

src/tests/
├── test_object_tagging.py    # 标签功能测试用例
└── conftest.py               # 可能需要更新fixtures

examples/
└── object_tagging_sample.py  # 标签使用示例
```

### 4.2 实现步骤

#### 步骤1: 添加常量定义 (const.py)

```python
# 对象标签相关常量
OBJECT_TAGGING = 'tagging'  # 子资源标识
TAGGING_HEADER = 'x-obs-tagging'  # 请求头
```

#### 步骤2: 实现Tag模型类 (model.py)

```python
class Tag(object):
    # 完整实现见上文
```

#### 步骤3: 实现XML转换器 (convertor.py)

```python
def _convert_tags_to_xml(tags):
    """
    将标签列表/字典转换为XML

    :param tags: List[Tag] 或 Dict[str, str]
    :return: XML字符串
    """
    # 实现转换逻辑

def _convert_xml_to_tags(xml_text):
    """
    将XML响应转换为标签列表

    :param xml_text: XML字符串
    :return: List[Tag]
    """
    # 实现转换逻辑
```

#### 步骤4: 实现客户端方法 (client.py)

```python
@funcCache
def setObjectTagging(self, bucketName, objectKey, tags, versionId=None, extensionHeaders=None):
    """
    设置对象标签的完整实现
    """
    # 1. 参数验证
    # 2. 转换标签格式
    # 3. 构建请求
    # 4. 发送HTTP请求
    # 5. 返回响应
```

### 4.3 HTTP请求设计

**setObjectTagging:**
```
PUT /object-key?tagging HTTP/1.1
Host: bucket-name.obs.cn-north-4.myhuaweicloud.com
Content-Type: application/xml

<Tagging>
    <TagSet>...</TagSet>
</Tagging>
```

**getObjectTagging:**
```
GET /object-key?tagging HTTP/1.1
Host: bucket-name.obs.cn-north-4.myhuaweicloud.com
```

**deleteObjectTagging:**
```
DELETE /object-key?tagging HTTP/1.1
Host: bucket-name.obs.cn-north-4.myhuaweicloud.com
```

### 4.4 与现有代码的集成

1. **使用现有的`_make_request`方法**: 遵循现有的请求模式
2. **使用现有的缓存装饰器**: `@funcCache`
3. **使用现有的响应处理**: 继承`GetResult`基类
4. **使用现有的异常处理**: 统一的`ObsException`

---

## 5. 测试策略

### 5.1 测试范围

#### 5.1.1 功能测试

| 测试场景 | 测试点 | 预期结果 |
|---------|--------|---------|
| 设置标签 - List格式 | 使用List格式设置标签 | 成功设置,status=200 |
| 设置标签 - Dict格式 | 使用Dict格式设置标签 | 成功设置,status=200 |
| 获取标签 | 获取已设置的标签 | 返回正确的标签列表 |
| 删除标签 | 删除对象标签 | 成功删除,status=204 |
| 覆盖标签 | 重新设置标签覆盖旧标签 | 新标签生效 |
| 版本控制 | 对指定版本ID操作 | 操作指定版本 |

#### 5.1.2 边界测试

| 测试场景 | 测试点 | 预期结果 |
|---------|--------|---------|
| 空标签列表 | 设置空标签 | 成功清除所有标签 |
| 单个标签 | 设置1个标签 | 成功设置 |
| 最大标签数 | 设置10个标签 | 成功设置 |
| 超过最大数 | 设置11个标签 | 返回错误或只保留前10个 |
| 最小键长度 | 键长度=1 | 成功设置 |
| 最大键长度 | 键长度=128 | 成功设置 |
| 超长键 | 键长度>128 | 返回错误 |
| 最小值长度 | 值长度=0(空字符串) | 成功设置 |
| 最大值长度 | 值长度=256 | 成功设置 |
| 超长值 | 值长度>256 | 返回错误 |
| 特殊字符键 | 键包含`.+-=_:/` | 成功设置 |
| 系统前缀键 | 键以`obs:`开头 | 返回错误 |

#### 5.1.3 参数检查测试

| 测试场景 | 测试点 | 预期结果 |
|---------|--------|---------|
| 缺少bucketName | bucketName=None | 抛出ValueError |
| 缺少objectKey | objectKey=None | 抛出ValueError |
| 缺少tags | tags=None(设置时) | 抛出ValueError |
| 空bucketName | bucketName='' | 抛出ValueError |
| 空objectKey | objectKey='' | 抛出ValueError |
| 无效tags类型 | tags="string" | 抛出TypeError |
| 无效versionId | versionId=123 | 自动转换为字符串 |

#### 5.1.4 功能组合测试

| 测试场景 | 测试点 | 预期结果 |
|---------|--------|---------|
| 标签+元数据 | 同时设置标签和元数据 | 两者都生效 |
| 标签+ACL | 同时设置标签和ACL | 两者都生效 |
| 标签+生命周期 | 基于标签设置生命周期规则 | 生效 |
| 批量操作+标签 | 批量删除带标签的对象 | 正常删除 |

#### 5.1.5 异常场景测试

| 测试场景 | 测试点 | 预期结果 |
|---------|--------|---------|
| 对象不存在 | 对不存在的对象操作 | 返回404错误 |
| 桶不存在 | 对不存在的桶操作 | 返回404错误 |
| 无权限 | 没有操作权限 | 返回403错误 |
| 网络错误 | 模拟网络故障 | 抛出网络异常 |
| 服务端错误 | 模拟5xx错误 | 抛出ObsException |

#### 5.1.6 性能测试

| 测试场景 | 测试点 | 性能指标 |
|---------|--------|---------|
| 大量标签 | 设置10个标签 | 响应时间<500ms |
| 并发设置 | 多线程并发设置标签 | 无竞争条件 |
| 批量获取 | 循环获取多个对象标签 | 性能稳定 |

### 5.2 测试用例结构

```python
class TestObjectTagging(unittest.TestCase):
    """对象标签功能测试"""

    def test_set_object_tagging_with_list(self):
        """测试使用List格式设置标签"""
        pass

    def test_set_object_tagging_with_dict(self):
        """测试使用Dict格式设置标签"""
        pass

    def test_get_object_tagging(self):
        """测试获取对象标签"""
        pass

    def test_delete_object_tagging(self):
        """测试删除对象标签"""
        pass

    def test_overwrite_tags(self):
        """测试覆盖标签"""
        pass

    def test_tag_with_version_id(self):
        """测试带版本ID的标签操作"""
        pass

    # ... 更多测试用例
```

### 5.3 测试数据准备

```python
# conftest.py

@pytest.fixture
def tagging_test_object(obs_client, bucket_name):
    """创建用于标签测试的对象"""
    object_key = 'test-tagging-object.txt'
    # 上传测试对象
    obs_client.putObject(bucket_name, object_key, content='test content')
    yield object_key
    # 清理
    try:
        obs_client.deleteObject(bucket_name, object_key)
    except:
        pass
```

---

## 6. 错误处理

### 6.1 错误码映射

| HTTP状态码 | OBS错误码 | 说明 | 客户端行为 |
|-----------|-----------|------|-----------|
| 400 | InvalidTag | 标签格式错误 | 抛出ObsException |
| 400 | InvalidTagKey | 标签键无效 | 抛出ObsException |
| 400 | TooManyTags | 标签数量超限 | 抛出ObsException |
| 403 | AccessDenied | 权限不足 | 抛出ObsException |
| 404 | NoSuchKey | 对象不存在 | 抛出ObsException |
| 404 | NoSuchBucket | 桶不存在 | 抛出ObsException |
| 500 | InternalError | 服务端错误 | 抛出ObsException |

### 6.2 参数验证

在发送请求前进行客户端验证:

```python
def _validate_tags(tags):
    """
    验证标签参数

    :param tags: 待验证的标签
    :raises ValueError: 参数无效
    """
    if tags is None:
        raise ValueError("tags cannot be None")

    # 转换为统一格式
    tag_list = _normalize_tags(tags)

    if len(tag_list) > 10:
        raise ValueError("Maximum 10 tags allowed per object")

    for tag in tag_list:
        # 验证键
        if not tag.key or len(tag.key) > 128:
            raise ValueError(f"Tag key length must be 1-128, got: {len(tag.key)}")

        if tag.key.startswith('obs:'):
            raise ValueError("Tag key cannot start with 'obs:'")

        # 验证值
        if tag.value is not None and len(tag.value) > 256:
            raise ValueError(f"Tag value length must be 0-256, got: {len(tag.value)}")
```

### 6.3 异常处理示例

```python
try:
    resp = obsClient.setObjectTagging('bucket', 'object', tags)
except ValueError as e:
    print(f"参数验证失败: {e}")
except ObsException as e:
    print(f"OBS服务错误: {e.status} - {e.code}")
    print(f"RequestId: {e.requestId}")
except Exception as e:
    print(f"未知错误: {e}")
```

---

## 7. 兼容性设计

### 7.1 向后兼容性

1. **新增方法**: 不修改现有方法签名
2. **默认参数**: 新增参数使用默认值
3. **不改变现有行为**: 确保现有代码不受影响

### 7.2 Python版本兼容性

```python
# Python 2.7兼容
import sys
if sys.version_info[0] >= 3:
    from urllib.parse import quote
else:
    from urllib import quote

# 类型注解兼容(Python 3.5+)
try:
    from typing import List, Dict, Optional, Union
except ImportError:
    # Python 2.7忽略类型注解
    pass
```

### 7.3 字符串处理

```python
# 统一字符串处理
def _to_string(value):
    """将值转换为字符串(Python 2/3兼容)"""
    if sys.version_info[0] >= 3:
        return str(value) if value is not None else None
    else:
        return unicode(value) if value is not None else None
```

---

## 8. 实现清单

### 8.1 开发任务清单

#### Phase 1: 准备工作 (Day 1)
- [ ] 阅读华为云OBS API文档
- [ ] 研究现有类似功能实现
- [ ] 准备开发环境和测试账号

#### Phase 2: 核心实现 (Day 2-3)
- [ ] 实现Tag数据模型 (model.py)
- [ ] 实现XML转换器 (convertor.py)
- [ ] 实现setObjectTagging方法 (client.py)
- [ ] 实现getObjectTagging方法 (client.py)
- [ ] 实现deleteObjectTagging方法 (client.py)
- [ ] 添加常量定义 (const.py)

#### Phase 3: 测试实现 (Day 3-4)
- [ ] 编写功能测试用例
- [ ] 编写边界测试用例
- [ ] 编写参数检查测试
- [ ] 编写异常场景测试
- [ ] 编写性能测试
- [ ] 编写并发测试

#### Phase 4: 文档和示例 (Day 4-5)
- [ ] 编写API文档注释
- [ ] 编写使用示例代码
- [ ] 更新README.md
- [ ] 准备CHANGELOG条目

#### Phase 5: 验证和优化 (Day 5)
- [ ] 运行完整测试套件
- [ ] 代码审查和优化
- [ ] 性能优化(如需要)
- [ ] 最终验证

### 8.2 验收标准

#### 功能完整性
- [ ] 三个API方法全部实现
- [ ] 支持List和Dict两种标签格式
- [ ] 支持版本控制
- [ ] 正确处理所有HTTP状态码

#### 测试覆盖率
- [ ] 单元测试覆盖率 > 85%
- [ ] 功能测试全部通过
- [ ] 边界测试全部通过
- [ ] 异常测试全部通过

#### 代码质量
- [ ] 遵循PEP8代码规范
- [ ] 完整的类型注解(可选)
- [ ] 完整的文档字符串
- [ ] 通过代码审查

#### 文档完整性
- [ ] API文档完整
- [ ] 使用示例代码
- [ ] 错误处理说明
- [ ] 最佳实践指南

### 8.3 发布检查清单

- [ ] 所有测试通过
- [ ] 代码合并到主分支
- [ ] 版本号更新
- [ ] CHANGELOG更新
- [ ] README更新
- [ ] 示例代码添加到examples/
- [ ] API文档更新
- [ ] 发布说明准备

---

## 附录

### A. 参考文档

1. 华为云OBS API文档
   - [对象标签相关接口](https://support.huaweicloud.com/api-obs/obs_04_0085.html)
2. 华为云OBS Java SDK源码
   - ObsClient.java - 标签相关方法参考
3. 阿里云OSS Python SDK
   - oss2/models.py - Tag实现参考

### B. 相关Issue

- 功能需求: #OBJECT_TAGGING_FEATURE
- 实现跟踪: #IMPLEMENT_OBJECT_TAGGING

### C. 联系人

- 开发负责人: [待定]
- 审查人: [待定]
- 测试负责人: [待定]

---

**文档结束**

*本文档由 Claude Code 生成,用于指导对象标签管理功能的实现。*
