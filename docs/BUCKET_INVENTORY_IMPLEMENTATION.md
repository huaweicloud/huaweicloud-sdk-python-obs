# 桶清单(Bucket Inventory)功能实现文档

## 功能概述

桶清单(Bucket Inventory)是华为云OBS提供的一项功能，用于定期生成桶中对象的清单报告。清单报告包含对象的元数据信息，可以导出到指定的目标桶。

## API接口

### 1. putBucketInventory - 设置/更新桶清单配置

```python
from obs import ObsClient, InventoryConfiguration, InventoryDestination
from obs import InventoryFormat, InventoryFrequency, InventoryIncludedObjectVersions

client = ObsClient(
    access_key_id='your-access-key',
    secret_access_key='your-secret-key',
    server='https://obs.cn-north-4.myhuaweicloud.com'
)

# 创建清单配置
destination = InventoryDestination(
    bucket='destination-bucket',
    accountId='123456789',
    prefix='inventory/',
    format=InventoryFormat.CSV
)

config = InventoryConfiguration(
    inventoryId='my-inventory',
    isEnabled=True,
    objectVersion=InventoryIncludedObjectVersions.All,
    frequency=InventoryFrequency.Daily,
    destination=destination
)

resp = client.putBucketInventory('source-bucket', 'my-inventory', config)
print(resp.status)  # 200
```

### 2. getBucketInventory - 获取桶清单配置

```python
resp = client.getBucketInventory('source-bucket', 'my-inventory')
if resp.status == 200:
    config = resp.configuration
    print(f"Inventory ID: {config.inventoryId}")
    print(f"Enabled: {config.isEnabled}")
    print(f"Frequency: {config.frequency}")
```

### 3. deleteBucketInventory - 删除桶清单配置

```python
resp = client.deleteBucketInventory('source-bucket', 'my-inventory')
print(resp.status)  # 204
```

### 4. listBucketInventory - 列举桶的所有清单配置

```python
resp = client.listBucketInventory('source-bucket')
if resp.status == 200:
    for config in resp.configurations:
        print(f"Inventory ID: {config.inventoryId}")
        print(f"Enabled: {config.isEnabled}")
```

## 配置参数说明

### InventoryConfiguration

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| inventoryId | str | 是 | 清单配置ID |
| isEnabled | bool | 是 | 是否启用清单 |
| objectVersion | str | 是 | 对象版本: All(所有版本) 或 Current(当前版本) |
| frequency | str | 是 | 频率: Daily(每天) 或 Weekly(每周) |
| filter | InventoryFilter | 否 | 对象前缀过滤器 |
| destination | InventoryDestination | 是 | 清单报告目标位置 |
| optionalFields | list | 否 | 可选字段列表 |

### InventoryDestination

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| bucket | str | 是 | 目标桶名称 |
| accountId | str | 否 | 目标桶所有者账户ID |
| prefix | str | 否 | 清单报告前缀 |
| format | str | 是 | 格式: CSV |

### InventoryFilter

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prefix | str | 是 | 对象前缀过滤条件 |

### 可选字段 (InventoryOptionalFields)

- Size - 对象大小
- LastModifiedDate - 最后修改时间
- ETag - 对象ETag
- StorageClass - 存储类型
- IsMultipartUploaded - 是否为分片上传
- ReplicationStatus - 跨区域复制状态
- EncryptionStatus - 加密状态
- ObjectAcl - 对象ACL
- ObjectOwner - 对象所有者
- VersionId - 版本ID

## 使用示例

### 示例1: 基本清单配置

```python
from obs import ObsClient, InventoryConfiguration, InventoryDestination
from obs import InventoryFormat, InventoryFrequency, InventoryIncludedObjectVersions

client = ObsClient(ak='xxx', sk='xxx', server='https://obs.region.myhuaweicloud.com')

destination = InventoryDestination(
    bucket='my-dest-bucket',
    format=InventoryFormat.CSV
)

config = InventoryConfiguration(
    inventoryId='daily-inventory',
    isEnabled=True,
    objectVersion=InventoryIncludedObjectVersions.All,
    frequency=InventoryFrequency.Daily,
    destination=destination
)

resp = client.putBucketInventory('my-source-bucket', 'daily-inventory', config)
```

### 示例2: 带过滤器的清单配置

```python
from obs import InventoryFilter

filter_rule = InventoryFilter(prefix='images/')

config = InventoryConfiguration(
    inventoryId='images-inventory',
    isEnabled=True,
    objectVersion=InventoryIncludedObjectVersions.Current,
    frequency=InventoryFrequency.Weekly,
    filter=filter_rule,
    destination=destination
)
```

### 示例3: 带可选字段的清单配置

```python
from obs import InventoryOptionalFields

optional_fields = [
    InventoryOptionalFields.Size,
    InventoryOptionalFields.LastModifiedDate,
    InventoryOptionalFields.StorageClass
]

config = InventoryConfiguration(
    inventoryId='detailed-inventory',
    isEnabled=True,
    objectVersion=InventoryIncludedObjectVersions.All,
    frequency=InventoryFrequency.Daily,
    optionalFields=optional_fields,
    destination=destination
)
```

## 实现文件

- **模型类**: `src/obs/model.py` - InventoryConfiguration, InventoryDestination等
- **转换器**: `src/obs/convertor.py` - XML转换方法
- **客户端**: `src/obs/client.py` - ObsClient方法
- **单元测试**: `src/tests/ut/test_inventory_model.py`, `src/tests/ut/test_xml_convertor.py`
- **集成测试**: `src/tests/test_bucket_inventory.py`

## 测试

### 运行单元测试
```bash
cd src/tests
python3 -m pytest ut/test_inventory_model.py -v
python3 -m pytest ut/test_xml_convertor.py::TestBucketInventoryConvertor -v
```

### 运行集成测试
```bash
cd src/tests
python3 -m pytest test_bucket_inventory.py -v
```

注意: 集成测试需要有效的OBS凭证配置在 `src/tests/test_config.json` 中。
