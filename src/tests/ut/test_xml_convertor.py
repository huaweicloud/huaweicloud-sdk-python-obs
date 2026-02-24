#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# XML转换器单元测试
# 对应集成测试: TestObjectTagging

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from obs.convertor import Convertor

try:
    import xml.etree.cElementTree as ET
except Exception:
    import xml.etree.ElementTree as ET


class TestXMLConvertor(object):
    """XML转换器单元测试 - 对象标签XML处理"""

    def setup_method(self):
        """设置测试环境"""
        class HA:
            pass
        ha = HA()
        self.adapter = Convertor('obs', ha)

    def test_normalize_tags_from_dict(self):
        """测试将字典格式标签标准化"""
        tags_dict = {'key1': 'value1', 'key2': 'value2'}
        normalized = self.adapter._normalize_tags(tags_dict)

        assert len(normalized) == 2
        assert normalized[0] == {'key': 'key1', 'value': 'value1'}

    def test_normalize_tags_from_list(self):
        """测试将列表格式标签标准化"""
        tags_list = [
            {'key': 'k1', 'value': 'v1'},
            {'key': 'k2', 'value': 'v2'}
        ]
        normalized = self.adapter._normalize_tags(tags_list)

        assert len(normalized) == 2
        assert normalized[0] == {'key': 'k1', 'value': 'v1'}

    def test_normalize_tags_from_tag_objects(self):
        """测试将Tag对象列表标准化"""
        from obs import Tag
        tags = [Tag('k1', 'v1'), Tag('k2', 'v2')]
        normalized = self.adapter._normalize_tags(tags)

        assert len(normalized) == 2
        assert normalized[0]['key'] == 'k1'

    def test_normalize_tags_none(self):
        """测试None标签标准化"""
        normalized = self.adapter._normalize_tags(None)
        assert normalized == []

    def test_trans_object_tags_to_xml(self):
        """测试将标签转换为XML"""
        tags = {'key1': 'value1', 'key2': 'value2'}
        xml = self.adapter._trans_object_tags_to_xml(tags)

        root = ET.fromstring(xml)
        assert root.tag == 'Tagging'
        tagset = root.find('TagSet')
        tag_elements = tagset.findall('Tag')
        assert len(tag_elements) == 2

    def test_trans_object_tags_empty_value(self):
        """测试空值标签转换为XML"""
        tags = {'key1': '', 'key2': 'value2'}
        xml = self.adapter._trans_object_tags_to_xml(tags)

        root = ET.fromstring(xml)
        tagset = root.find('TagSet')
        tag_elements = tagset.findall('Tag')
        assert len(tag_elements) == 2
        value1 = tag_elements[0].find('Value')
        assert value1 is not None

    def test_parse_object_tagging_xml(self):
        """测试解析对象标签XML"""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <Tagging>
            <TagSet>
                <Tag>
                    <Key>key1</Key>
                    <Value>value1</Value>
                </Tag>
            </TagSet>
        </Tagging>'''

        result = self.adapter.parseGetObjectTagging(xml)

        assert hasattr(result, 'tags')
        assert len(result.tags) == 1
        assert result.tags[0].key == 'key1'

    def test_parse_object_tagging_empty_xml(self):
        """测试解析空标签XML"""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <Tagging>
            <TagSet>
            </TagSet>
        </Tagging>'''

        result = self.adapter.parseGetObjectTagging(xml)

        assert hasattr(result, 'tags')
        assert len(result.tags) == 0

    def test_trans_set_object_tagging(self):
        """测试设置对象标签的转换"""
        from obs import const
        tags = {'key1': 'value1', 'key2': 'value2'}
        result = self.adapter.trans_set_object_tagging(tags=tags, versionId=None)

        assert 'pathArgs' in result
        assert 'headers' in result
        assert 'entity' in result
        assert const.TAGGING_PARAM in result['pathArgs']

        entity = result['entity']
        root = ET.fromstring(entity)
        assert root.tag == 'Tagging'

    def test_trans_set_object_tagging_with_version_id(self):
        """测试带versionId的对象标签转换"""
        from obs import const
        tags = {'key1': 'value1'}
        version_id = 'test-version-id'
        result = self.adapter.trans_set_object_tagging(tags=tags, versionId=version_id)

        assert const.VERSION_ID_PARAM in result['pathArgs']
        assert result['pathArgs'][const.VERSION_ID_PARAM] == version_id
