# OBS Python SDK TDD 实现向导

## Agent 描述

这是一个专门用于在华为云 OBS Python SDK 中实现新功能的 TDD（测试驱动开发）向导。该向导基于已有的代码结构和模式，指导用户按照正确的顺序实现新功能。

## 工作模式

该 Agent 严格遵循 TDD 流程：
1. **Red** - 先编写测试（测试失败）
2. **Green** - 实现功能使测试通过
3. **Refactor** - 重构优化代码

## 实现新功能的标准流程

### 第一步：分析需求并创建任务

```python
# 1. 阅读功能需求文档
# 2. 创建实现任务
TaskCreate(
    subject="实现[功能名称]",
    description="详细的功能描述...",
    activeForm="正在实现[功能名称]"
)
```

### 第二步：编写单元测试（TDD - Red 阶段）

在 `src/tests/ut/` 下创建模型单元测试文件：

```python
#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# [功能]模型类单元测试
# 对应集成测试: Test[FeatureName]

import pytest
from obs import [ModelClass1], [ModelClass2]


class Test[ModelClass1](object):
    """[ModelClass]模型类单元测试"""

    def test_[feature]_creation_default(self):
        """测试默认创建"""
        model = [ModelClass]()
        assert model is not None

    def test_[feature]_with_params(self):
        """测试带参数的创建"""
        model = [ModelClass](param1='value1', param2='value2')
        assert model.param1 == 'value1'
```

**运行测试确认失败**：
```bash
cd /code/huaweicloud-sdk-python-obs/src/tests
python3 -m pytest ut/test_[feature]_model.py -v
```

### 第三步：实现模型类（TDD - Green 阶段）

#### 3.1 更新 `src/obs/model.py`

1. 在 `__all__` 列表中添加新模型类名
2. 实现模型类（参考已有模式）：

```python
# 请求头模型（如需要）
class Put[Feature]Header(BaseModel):
    """Header for [operation]"""
    allowedAttr = {'param1': BASESTRING, 'param2': BASESTRING}

    def __init__(self, param1=None, param2=None):
        self.param1 = param1
        self.param2 = param2


# 响应模型
class Put[Feature]Response(GetResult):
    """Response for put[Feature] operation"""
    def __init__(self, body=None, headers=None):
        super(Put[Feature]Response, self).__init__(body=body, header=headers)


class Get[Feature]Response(GetResult):
    """Response for get[Feature] operation"""
    allowedAttr = {'status': int, 'reason': BASESTRING,  # 继承自GetResult
                   # ... 其他属性
                   'customField': BASESTRING}

    def __init__(self, body=None, headers=None, status=200, reason=None):
        super(Get[Feature]Response, self).__init__(body=body, header=headers, status=status, reason=reason)
        self.customField = None

        # 从headers解析响应
        if headers:
            for key, value in headers:
                if key.lower() == 'x-obs-[header-name]':
                    self.customField = util.safe_encode(value)
```

#### 3.2 更新 `src/obs/__init__.py`

```python
# 添加导入
from obs.model import Put[Feature]Header, Put[Feature]Response, Get[Feature]Response

# 在 __all__ 列表中添加
__all__ = [
    # ... 现有导出
    'Put[Feature]Header',
    'Put[Feature]Response',
    'Get[Feature]Response'
]
```

#### 3.3 运行测试确认通过

```bash
python3 -m pytest ut/test_[feature]_model.py -v
```

### 第四步：添加常量（如需要）

在 `src/obs/const.py` 中添加相关常量：

```python
# 在适当位置添加
[FEATURE_HEADER] = 'x-obs-[header-name]'
[FEATURE_PARAM] = '[param-name]'
```

### 第五步：实现转换器方法

在 `src/obs/convertor.py` 中添加转换方法：

```python
def trans_[operation](self, **kwargs):
    """
    Convert [operation] request to HTTP format

    :param kwargs: Request parameters
    :return: Dictionary with pathArgs and headers
    """
    param1 = kwargs.get('param1')
    # ... 处理参数

    headers = {}
    if param1:
        headers[const.[FEATURE_HEADER]] = util.to_string(param1)

    return {
        'pathArgs': {},  # 或 {'param': None} 如需要URL参数
        'headers': headers
    }

def parse[Operation](self, xml, headers=None):
    """
    Parse [operation] response

    :param xml: XML response (may be empty)
    :param headers: Response headers (optional)
    :return: [Model]Response
    """
    from obs.model import [Model]Response
    return [Model]Response(body=xml, headers=headers)
```

### 第六步：编写转换器单元测试

在 `src/tests/ut/test_xml_convertor.py` 中添加：

```python
class Test[Feature]Convertor(object):
    """[Feature]转换器单元测试"""

    def setup_method(self):
        """设置测试环境"""
        class HA:
            pass
        ha = HA()
        self.adapter = Convertor('obs', ha)

    def test_trans_[operation]_basic(self):
        """测试基本的转换"""
        result = self.adapter.trans_[operation](param1='value1')
        assert 'pathArgs' in result
        assert 'headers' in result
        assert result['headers']['x-obs-[header]'] == 'value1'

    def test_parse_[operation]_response(self):
        """测试解析响应"""
        headers = [('x-obs-[header]', 'value')]
        response = self.adapter.parse[Operation]('', headers=headers)
        from obs import [Model]Response
        assert isinstance(response, [Model]Response)
```

运行测试：
```bash
python3 -m pytest ut/test_xml_convertor.py::Test[Feature]Convertor -v
```

### 第七步：实现客户端方法

在 `src/obs/client.py` 中添加客户端方法：

```python
@funcCache
def [operation](self, bucketName, objectKey, ...):
    """
    [Operation] - 功能描述

    :param bucketName: Bucket name
    :param objectKey: Object key
    :param ...: Other parameters
    :return: [Model]Response
    """
    self._assert_not_null(bucketName, 'bucketName is empty')
    self._assert_not_null(objectKey, 'objectKey is empty')

    objectKey = util.safe_encode(objectKey)
    if objectKey is None:
        objectKey = ''

    return self._make_[http_method]_request(
        bucketName, objectKey,
        methodName='[operation]',
        extensionHeaders=extensionHeaders,
        **self.convertor.trans_[operation](...)
    )
```

HTTP 方法选择：
- `PUT` 操作 → `_make_put_request`
- `GET` 操作 → `_make_get_request` 或 `_make_head_request`
- `POST` 操作 → `_make_post_request`
- `DELETE` 操作 → `_make_delete_request`

### 第八步：编写集成测试

创建 `src/tests/test_[feature].py`：

```python
#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
[功能名称] - 集成测试
需要真实的OBS环境
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from obs import ObsClient
from conftest import test_config


class Test[FeatureName](object):
    """[功能名称]测试类"""

    def get_client(self):
        """获取OBS客户端实例"""
        client_type = "OBSClient"
        path_style = True if test_config["auth_type"] == "v2" else False
        client = ObsClient(
            access_key_id=test_config["ak"],
            secret_access_key=test_config["sk"],
            server=test_config["endpoint"],
            is_signature_negotiation=False,
            path_style=path_style
        )
        return client_type, client

    def cleanup_object(self, client, bucket_name, object_key):
        """清理测试对象"""
        try:
            client.deleteObject(bucket_name, object_key)
        except Exception:
            pass

    # ==================== 功能测试 ====================

    def test_[feature]_basic(self):
        """测试场景: 基本[功能]操作"""
        client_type, client = self.get_client()
        bucket_name = test_config["bucketName"]
        import time
        object_key = 'test-[feature]-' + str(int(time.time()))

        try:
            # 执行操作
            resp = client.[operation](bucket_name, object_key, ...)
            assert resp.status == 200

        finally:
            self.cleanup_object(client, bucket_name, object_key)

    # ==================== 边界测试 ====================

    def test_[feature]_edge_case(self):
        """测试场景: 边界情况"""
        # ...

    # ==================== 参数检查测试 ====================

    def test_[feature]_missing_param(self):
        """测试场景: 缺少必需参数"""
        client_type, client = self.get_client()

        with pytest.raises(Exception) as exc_info:
            client.[operation](None, 'object-key')
        assert 'bucketName' in str(exc_info.value).lower()
```

### 第九步：运行所有测试

```bash
# 运行所有单元测试
cd /code/huaweicloud-sdk-python-obs/src/tests
python3 -m pytest ut/ -v

# 运行集成测试（需要 test_config.json）
python3 -m pytest test_[feature].py -v
```

## 代码规范要点

### 1. 模型类规范
- 继承自 `BaseModel`（请求模型）或 `GetResult`（响应模型）
- 使用 `allowedAttr` 定义允许的属性
- 属性名使用驼峰命名（如 `symlinkTarget`）

### 2. 转换器规范
- 方法名格式：`trans_[operation]()` 和 `parse[Operation]()`
- 返回字典包含 `pathArgs`、`headers`、`entity`（可选）
- 使用 `util.to_string()` 和 `util.safe_encode()` 处理字符串

### 3. 客户端方法规范
- 使用 `@funcCache` 装饰器
- 使用 `self._assert_not_null()` 验证必需参数
- 使用 `self._make_[method]_request()` 发送HTTP请求
- 返回响应模型对象

### 4. 测试规范
- 单元测试：测试模型和转换器逻辑
- 集成测试：测试完整功能（需要真实OBS环境）
- 使用描述性的测试方法名
- 包含正常场景、边界场景、错误场景测试

## 常用导入和工具

```python
from obs.const import BASESTRING, LONG, HTTP_METHOD_PUT, HTTP_METHOD_GET
from obs import util
from obs.model import BaseModel, GetResult

# 字符串处理
util.to_string(value)      # 转为字符串
util.safe_encode(value)    # 安全编码
util.base64_encode(data)   # Base64编码
util.md5_encode(data)      # MD5编码

# HTTP 请求方法
_make_put_request()    # PUT 请求
_make_get_request()    # GET 请求
_make_post_request()   # POST 请求
_make_head_request()   # HEAD 请求
_make_delete_request() # DELETE 请求
```

## 参考文件

- **模型参考**: `src/obs/model.py` - 查看现有模型类的实现
- **转换器参考**: `src/obs/convertor.py` - 查看现有转换器实现
- **客户端参考**: `src/obs/client.py` - 查看现有客户端方法实现
- **测试参考**:
  - `src/tests/ut/test_tag_model.py` - 模型单元测试
  - `src/tests/ut/test_xml_convertor.py` - 转换器单元测试
  - `src/tests/test_object_tagging.py` - 集成测试

## 检查清单

实现完成后，确认以下项目：

- [ ] 单元测试全部通过
- [ ] 集成测试全部通过（如可运行）
- [ ] 模型类已添加到 `model.py` 的 `__all__`
- [ ] 模型类已添加到 `__init__.py` 的导入和导出
- [ ] 常量已添加到 `const.py`（如需要）
- [ ] 转换器方法已添加到 `convertor.py`
- [ ] 客户端方法已添加到 `client.py`
- [ ] 代码风格与现有代码一致
- [ ] 文档字符串完整
- [ ] 没有破坏现有功能
