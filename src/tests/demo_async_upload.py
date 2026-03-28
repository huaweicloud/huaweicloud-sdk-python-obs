#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
异步上传功能演示
展示 pause/resume/cancel 功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from obs import ObsClient, UploadTaskStatus
import time

# 配置 OBS 客户端
ak = 'your-access-key'
sk = 'your-secret-key'
endpoint = 'https://obs.cn-north-4.myhuaweicloud.com'
bucket = 'your-bucket-name'

def demo_basic_upload():
    """演示基本异步上传"""
    print("\n=== 演示 1: 基本异步上传 ===")

    client = ObsClient(
        access_key_id=ak,
        secret_access_key=sk,
        server=endpoint
    )

    # 创建测试文件
    test_file = '/tmp/demo_upload.dat'
    with open(test_file, 'wb') as f:
        f.write(b'Demo content ' * 100000)  # ~1.3MB

    try:
        # 启动异步上传
        task = client.uploadFileAsync(
            bucket,
            'demo-async-object',
            test_file,
            partSize=500 * 1024,  # 500KB 分片
            taskNum=2
        )

        print(f"上传开始... 状态: {task.status}")

        # 等待完成
        response = task.wait_for_completion(timeout=30)

        print(f"上传完成! 状态: {task.status}")
        print(f"传输字节: {task.transferred_bytes} / {task.total_bytes}")
        print(f"进度: {task.get_progress_percentage():.1f}%")
        print(f"HTTP 状态码: {response.status}")

    finally:
        # 清理
        try:
            client.deleteObject(bucket, 'demo-async-object')
            os.remove(test_file)
        except:
            pass


def demo_pause_resume():
    """演示暂停和恢复上传"""
    print("\n=== 演示 2: 暂停和恢复上传 ===")

    client = ObsClient(
        access_key_id=ak,
        secret_access_key=sk,
        server=endpoint
    )

    # 创建测试文件 (5MB)
    test_file = '/tmp/demo_pause_resume.dat'
    with open(test_file, 'wb') as f:
        f.write(b'0' * (5 * 1024 * 1024))

    try:
        # 启动上传（必须启用 checkpoint 才能暂停）
        task = client.uploadFileAsync(
            bucket,
            'demo-pause-resume-object',
            test_file,
            partSize=1 * 1024 * 1024,  # 1MB 分片
            taskNum=2,
            enableCheckpoint=True  # 必须启用
        )

        print(f"上传开始... 状态: {task.status}")

        # 等待一下
        time.sleep(1)
        print(f"当前进度: {task.get_progress_percentage():.1f}%")

        # 暂停上传
        print("正在暂停上传...")
        task.pause()
        print(f"已暂停! 状态: {task.status}")

        time.sleep(1)

        # 恢复上传
        print("正在恢复上传...")
        task.resume()
        print(f"已恢复! 状态: {task.status}")

        # 等待完成
        response = task.wait_for_completion(timeout=60)

        print(f"上传完成! 状态: {task.status}")
        print(f"最终进度: {task.get_progress_percentage():.1f}%")

    finally:
        # 清理
        try:
            client.deleteObject(bucket, 'demo-pause-resume-object')
            os.remove(test_file)
            checkpoint_file = test_file + '.upload_record'
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
        except:
            pass


def demo_cancel():
    """演示取消上传"""
    print("\n=== 演示 3: 取消上传 ===")

    client = ObsClient(
        access_key_id=ak,
        secret_access_key=sk,
        server=endpoint
    )

    # 创建测试文件
    test_file = '/tmp/demo_cancel.dat'
    with open(test_file, 'wb') as f:
        f.write(b'0' * (5 * 1024 * 1024))

    try:
        # 启动上传
        task = client.uploadFileAsync(
            bucket,
            'demo-cancel-object',
            test_file,
            partSize=1 * 1024 * 1024,
            taskNum=2,
            enableCheckpoint=True
        )

        print(f"上传开始... 状态: {task.status}")

        # 等待一下
        time.sleep(0.5)
        print(f"当前进度: {task.get_progress_percentage():.1f}%")

        # 取消上传
        print("正在取消上传...")
        task.cancel()
        print(f"已取消! 状态: {task.status}")
        print(f"is_cancelled: {task.is_cancelled}")

        # 取消后无法恢复
        print("注意: 取消后的上传无法恢复")

    finally:
        # 清理
        try:
            client.deleteObject(bucket, 'demo-cancel-object')
            os.remove(test_file)
            checkpoint_file = test_file + '.upload_record'
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
        except:
            pass


def demo_progress_callback():
    """演示进度回调"""
    print("\n=== 演示 4: 进度回调 ===")

    client = ObsClient(
        access_key_id=ak,
        secret_access_key=sk,
        server=endpoint
    )

    # 创建测试文件
    test_file = '/tmp/demo_progress.dat'
    with open(test_file, 'wb') as f:
        f.write(b'X' * (2 * 1024 * 1024))

    # 进度回调函数
    def progress_callback(transferred, total, current_part_transferred, current_part_size):
        percent = (transferred / total * 100) if total > 0 else 0
        print(f"  进度: {percent:.1f}% ({transferred}/{total} bytes)")

    try:
        # 使用进度回调上传
        task = client.uploadFileAsync(
            bucket,
            'demo-progress-object',
            test_file,
            progressCallback=progress_callback
        )

        print("上传开始 (查看进度回调输出)...")
        response = task.wait_for_completion(timeout=30)

        print(f"上传完成! 状态: {task.status}")

    finally:
        # 清理
        try:
            client.deleteObject(bucket, 'demo-progress-object')
            os.remove(test_file)
        except:
            pass


def demo_completion_callback():
    """演示完成回调"""
    print("\n=== 演示 5: 完成回调 ===")

    client = ObsClient(
        access_key_id=ak,
        secret_access_key=sk,
        server=endpoint
    )

    # 创建测试文件
    test_file = '/tmp/demo_completion.dat'
    with open(test_file, 'wb') as f:
        f.write(b'0' * (1024 * 1024))

    # 完成回调函数
    def on_complete(task):
        print(f"  回调: 上传完成! 状态={task.status}, 进度={task.get_progress_percentage():.1f}%")

    try:
        task = client.uploadFileAsync(
            bucket,
            'demo-completion-object',
            test_file
        )

        # 设置完成回调
        task.set_completion_callback(on_complete)

        print("上传开始...")
        response = task.wait_for_completion(timeout=30)

        print(f"主线程: 上传完成! 状态: {task.status}")

    finally:
        # 清理
        try:
            client.deleteObject(bucket, 'demo-completion-object')
            os.remove(test_file)
        except:
            pass


if __name__ == '__main__':
    print("========================================")
    print("  OBS Python SDK 异步上传功能演示")
    print("========================================")

    print("\n注意: 请先配置正确的 AK、SK 和 Endpoint")
    print("当前配置:")
    print(f"  AK: {ak[:20]}...")
    print(f"  SK: {sk[:20]}...")
    print(f"  Endpoint: {endpoint}")
    print(f"  Bucket: {bucket}")

    # 取消下面的注释来运行演示
    # demo_basic_upload()
    # demo_pause_resume()
    # demo_cancel()
    # demo_progress_callback()
    # demo_completion_callback()

    print("\n演示脚本已准备就绪!")
    print("请在脚本中配置正确的 OBS 凭证后，取消相应的演示函数调用")
