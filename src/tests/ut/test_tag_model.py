#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# Tag模型类单元测试
# 对应集成测试: TestObjectTagging

import pytest
from obs import Tag, TagInfoModel


class TestTag(object):
    """Tag模型类单元测试"""

    def test_tag_creation(self):
        """测试Tag对象创建"""
        tag = Tag('key', 'value')
        assert tag.key == 'key'
        assert tag.value == 'value'

    def test_tag_equality(self):
        """测试Tag对象相等性"""
        tag1 = Tag('key', 'value')
        tag2 = Tag('key', 'value')
        tag3 = Tag('key', 'different')

        assert tag1 == tag2
        assert tag1 != tag3
        assert tag1 != "not a tag"

    def test_tag_to_dict(self):
        """测试Tag转字典"""
        tag = Tag('key', 'value')
        tag_dict = tag.to_dict()
        assert tag_dict == {'key': 'key', 'value': 'value'}

    def test_tag_from_dict(self):
        """测试从字典创建Tag"""
        tag_dict = {'key': 'test_key', 'value': 'test_value'}
        tag = Tag.from_dict(tag_dict)
        assert tag.key == 'test_key'
        assert tag.value == 'test_value'

    def test_tag_from_dict_none(self):
        """测试从None创建Tag"""
        tag = Tag.from_dict(None)
        assert tag is None


class TestTagInfoModel(object):
    """TagInfoModel类单元测试"""

    def test_tag_info_model_creation(self):
        """测试TagInfoModel创建"""
        model = TagInfoModel()
        assert model.tags == []

    def test_tag_info_model_with_tags(self):
        """测试TagInfoModel带标签"""
        tags = [Tag('k1', 'v1'), Tag('k2', 'v2')]
        model = TagInfoModel(tags=tags)
        assert len(model.tags) == 2
        assert model.tags[0].key == 'k1'
