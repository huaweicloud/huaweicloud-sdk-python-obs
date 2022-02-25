# coding:utf-8
import hashlib
import json
import os
import random
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from obs.const import IS_PYTHON2

if IS_PYTHON2:
    chr = unichr


def read_env_info():
    with open(os.path.join(os.getcwd(), "test_config.json"), "r") as f:
        return json.loads(f.read())


def compare_sha256(original_file, target_file, is_file=True):
    original_sha256 = hashlib.sha256()
    target_sha256 = hashlib.sha256()
    with open(original_file, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            original_sha256.update(chunk)
    if is_file:
        with open(target_file, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                target_sha256.update(chunk)
    else:
        while True:
            chunk = target_file.read(65536)
            if not chunk:
                break
            target_sha256.update(chunk)
    return target_sha256.hexdigest() == original_sha256.hexdigest()


def download_and_check(obsClient, bucket_name, object_name, download_path, source_file):
    try:
        obsClient.downloadFile(bucket_name, object_name, downloadFile=download_path, taskNum=10)
        compare_result = compare_sha256(source_file, download_path)
        return compare_result
    except Exception:
        return False
    finally:
        os.remove(download_path)
        obsClient.deleteObject(bucket_name, object_name)


test_config = read_env_info()


@pytest.fixture(params=test_config["test_files"].items())
def gen_test_file(request):
    file_name = request.keywords.node.name + "_" + request.param[0]
    gen_random_file(file_name, request.param[1])
    yield file_name
    os.remove(test_config["path_prefix"] + file_name)


@pytest.fixture()
def delete_bucket_after_test():
    results = {"need_delete_buckets": []}
    yield results
    if "client" in results:
        for bucket_name in results["need_delete_buckets"]:
            delete_result = results["client"].deleteBucket(bucket_name)
            assert delete_result.status == 204


def gen_random_file(file_name, file_size):
    tmp_1024 = "".join(chr(random.randint(10000, 40000)) for _ in range(341)).encode("UTF-8")
    tmp_1024 += b"m"
    with open(test_config["path_prefix"] + file_name, "wb") as f:
        for _ in range(file_size):
            f.write(tmp_1024)
