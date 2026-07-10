#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# This sample demonstrates how to manage object tags in OBS Python SDK.

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obs import ObsClient, Tag

# Configure your access credentials
AK = '*** Provide your Access Key ***'
SK = '*** Provide your Secret Key ***'
SERVER = 'https://obs.cn-north-4.myhuaweicloud.com'
BUCKET_NAME = 'your-bucket-name'


def create_client():
    """Create OBS client"""
    return ObsClient(access_key_id=AK, secret_access_key=SK, server=SERVER)


def print_result(operation, result):
    """Print operation result"""
    print(f'\n{operation}:')
    print(f'  Status: {result.status}')
    if result.header:
        print(f'  Request ID: {dict(result.header).get("x-obs-request-id", "N/A")}')
    if hasattr(result, 'body') and hasattr(result.body, 'tags'):
        print(f'  Tags: {len(result.body.tags)}')
        for tag in result.body.tags:
            print(f'    - {tag.key}: {tag.value}')


def sample_set_tags_with_list():
    """
    Sample 1: Set object tags using list format
    """
    print('\n=== Sample 1: Set tags using list format ===')
    client = create_client()
    object_key = 'test-object-list.txt'

    try:
        # First, upload an object
        put_resp = client.putContent(BUCKET_NAME, object_key, 'Hello OBS')
        if put_resp.status == 200:
            print(f'Object uploaded: {object_key}')

        # Set tags using list format
        tags = [
            {'key': 'project', 'value': 'demo'},
            {'key': 'env', 'value': 'production'},
            {'key': 'team', 'value': 'backend'}
        ]
        set_resp = client.setObjectTagging(BUCKET_NAME, object_key, tags)
        print_result('Set tags (list format)', set_resp)

        # Get tags to verify
        get_resp = client.getObjectTagging(BUCKET_NAME, object_key)
        print_result('Get tags', get_resp)

    finally:
        # Cleanup
        client.deleteObject(BUCKET_NAME, object_key)
        print(f'Object deleted: {object_key}')


def sample_set_tags_with_dict():
    """
    Sample 2: Set object tags using dict format
    """
    print('\n=== Sample 2: Set tags using dict format ===')
    client = create_client()
    object_key = 'test-object-dict.txt'

    try:
        # Upload an object
        put_resp = client.putContent(BUCKET_NAME, object_key, 'Hello OBS')
        if put_resp.status == 200:
            print(f'Object uploaded: {object_key}')

        # Set tags using dict format (more concise)
        tags = {
            'project': 'demo',
            'env': 'production',
            'team': 'backend',
            'owner': 'john'
        }
        set_resp = client.setObjectTagging(BUCKET_NAME, object_key, tags)
        print_result('Set tags (dict format)', set_resp)

        # Get tags to verify
        get_resp = client.getObjectTagging(BUCKET_NAME, object_key)
        print_result('Get tags', get_resp)

    finally:
        # Cleanup
        client.deleteObject(BUCKET_NAME, object_key)
        print(f'Object deleted: {object_key}')


def sample_set_tags_with_tag_objects():
    """
    Sample 3: Set object tags using Tag objects
    """
    print('\n=== Sample 3: Set tags using Tag objects ===')
    client = create_client()
    object_key = 'test-object-tag.txt'

    try:
        # Upload an object
        put_resp = client.putContent(BUCKET_NAME, object_key, 'Hello OBS')
        if put_resp.status == 200:
            print(f'Object uploaded: {object_key}')

        # Set tags using Tag objects
        tags = [
            Tag('category', 'document'),
            Tag('priority', 'high'),
            Tag('status', 'active')
        ]
        set_resp = client.setObjectTagging(BUCKET_NAME, object_key, tags)
        print_result('Set tags (Tag objects)', set_resp)

        # Get tags to verify
        get_resp = client.getObjectTagging(BUCKET_NAME, object_key)
        print_result('Get tags', get_resp)

    finally:
        # Cleanup
        client.deleteObject(BUCKET_NAME, object_key)
        print(f'Object deleted: {object_key}')


def sample_get_tags():
    """
    Sample 4: Get object tags
    """
    print('\n=== Sample 4: Get object tags ===')
    client = create_client()
    object_key = 'test-object-get.txt'

    try:
        # Upload and set tags
        client.putContent(BUCKET_NAME, object_key, 'Hello OBS')
        client.setObjectTagging(BUCKET_NAME, object_key, {'key1': 'value1', 'key2': 'value2'})

        # Get tags
        get_resp = client.getObjectTagging(BUCKET_NAME, object_key)
        print_result('Get tags', get_resp)

        # Access individual tags
        if hasattr(get_resp.body, 'tags') and get_resp.body.tags:
            print('\nTag details:')
            for tag in get_resp.body.tags:
                print(f'  Key: {tag.key}, Value: {tag.value}')

    finally:
        # Cleanup
        client.deleteObject(BUCKET_NAME, object_key)
        print(f'Object deleted: {object_key}')


def sample_delete_tags():
    """
    Sample 5: Delete object tags
    """
    print('\n=== Sample 5: Delete object tags ===')
    client = create_client()
    object_key = 'test-object-delete.txt'

    try:
        # Upload and set tags
        client.putContent(BUCKET_NAME, object_key, 'Hello OBS')
        client.setObjectTagging(BUCKET_NAME, object_key, {'temp': 'tag'})

        # Get tags before deletion
        get_resp_before = client.getObjectTagging(BUCKET_NAME, object_key)
        print_result('Get tags (before deletion)', get_resp_before)

        # Delete tags
        del_resp = client.deleteObjectTagging(BUCKET_NAME, object_key)
        print_result('\nDelete tags', del_resp)

        # Get tags after deletion
        get_resp_after = client.getObjectTagging(BUCKET_NAME, object_key)
        print_result('\nGet tags (after deletion)', get_resp_after)

    finally:
        # Cleanup
        client.deleteObject(BUCKET_NAME, object_key)
        print(f'\nObject deleted: {object_key}')


def sample_overwrite_tags():
    """
    Sample 6: Overwrite existing tags
    """
    print('\n=== Sample 6: Overwrite existing tags ===')
    client = create_client()
    object_key = 'test-object-overwrite.txt'

    try:
        # Upload object
        client.putContent(BUCKET_NAME, object_key, 'Hello OBS')

        # Set initial tags
        initial_tags = {'version': '1.0', 'status': 'draft'}
        set_resp1 = client.setObjectTagging(BUCKET_NAME, object_key, initial_tags)
        print_result('Set initial tags', set_resp1)

        # Get initial tags
        get_resp1 = client.getObjectTagging(BUCKET_NAME, object_key)
        print_result('Get initial tags', get_resp1)

        # Overwrite with new tags
        new_tags = {'version': '2.0', 'status': 'published', 'reviewed': 'true'}
        set_resp2 = client.setObjectTagging(BUCKET_NAME, object_key, new_tags)
        print_result('\nOverwrite tags', set_resp2)

        # Get new tags
        get_resp2 = client.getObjectTagging(BUCKET_NAME, object_key)
        print_result('\nGet new tags', get_resp2)

    finally:
        # Cleanup
        client.deleteObject(BUCKET_NAME, object_key)
        print(f'\nObject deleted: {object_key}')


def sample_error_handling():
    """
    Sample 7: Error handling
    """
    print('\n=== Sample 7: Error handling ===')
    client = create_client()

    # Try to set tags on non-existent object
    print('\nTrying to set tags on non-existent object...')
    try:
        resp = client.setObjectTagging(BUCKET_NAME, 'non-existent-object', {'key': 'value'})
        if resp.status >= 400:
            print(f'  Error: HTTP {resp.status}')
            if hasattr(resp, 'errorCode'):
                print(f'  Error Code: {resp.errorCode}')
            if hasattr(resp, 'errorMessage'):
                print(f'  Error Message: {resp.errorMessage}')
        else:
            print(f'  Unexpected success: {resp.status}')
    except Exception as e:
        print(f'  Exception: {e}')

    # Try to get tags with missing parameters
    print('\nTrying to get tags with missing bucket name...')
    try:
        resp = client.getObjectTagging(None, 'object-key')
        print(f'  Unexpected success')
    except Exception as e:
        print(f'  Expected exception: {type(e).__name__}: {e}')


def sample_tag_boundaries():
    """
    Sample 8: Tag boundaries and constraints
    """
    print('\n=== Sample 8: Tag boundaries ===')
    client = create_client()
    object_key = 'test-object-boundaries.txt'

    try:
        # Upload object
        client.putContent(BUCKET_NAME, object_key, 'Hello OBS')

        # Test: Empty tag value (allowed)
        print('\nTest 1: Empty tag value')
        resp = client.setObjectTagging(BUCKET_NAME, object_key, {'empty-key': ''})
        print(f'  Status: {resp.status} (200 = success)')

        # Test: Special characters in key
        print('\nTest 2: Special characters in key')
        resp = client.setObjectTagging(BUCKET_NAME, object_key, {'test.key': 'value1', 'test-key': 'value2'})
        print(f'  Status: {resp.status} (200 = success)')

        # Test: Maximum number of tags (10)
        print('\nTest 3: Maximum tags (10)')
        max_tags = {f'key{i}': f'value{i}' for i in range(10)}
        resp = client.setObjectTagging(BUCKET_NAME, object_key, max_tags)
        print(f'  Status: {resp.status} (200 = success)')

        # Get tags to verify
        get_resp = client.getObjectTagging(BUCKET_NAME, object_key)
        print(f'  Tag count: {len(get_resp.body.tags)}')

    finally:
        # Cleanup
        client.deleteObject(BUCKET_NAME, object_key)
        print(f'\nObject deleted: {object_key}')


if __name__ == '__main__':
    print('OBS Python SDK - Object Tagging Samples')
    print('=======================================')

    # Note: Replace AK, SK, and BUCKET_NAME with your actual credentials
    # before running these samples

    samples = [
        ('Set tags (list format)', sample_set_tags_with_list),
        ('Set tags (dict format)', sample_set_tags_with_dict),
        ('Set tags (Tag objects)', sample_set_tags_with_tag_objects),
        ('Get tags', sample_get_tags),
        ('Delete tags', sample_delete_tags),
        ('Overwrite tags', sample_overwrite_tags),
        ('Error handling', sample_error_handling),
        ('Tag boundaries', sample_tag_boundaries),
    ]

    for name, sample_func in samples:
        try:
            sample_func()
        except Exception as e:
            print(f'\nSample "{name}" failed with error: {e}')
            import traceback
            traceback.print_exc()

    print('\n\nAll samples completed!')
    print('\nNote: Some samples may fail if you do not configure valid credentials.')
