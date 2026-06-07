# -*- coding: utf-8 -*-
"""
GeoTeach RAG - 文件同步脚本

从远程服务器下载新上传的文件到本地。
用法: python sync_files.py [--server URL] [--interval 秒数]
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime


# 默认配置
DEFAULT_SERVER = "https://your-app.up.railway.app"  # 替换为你的Railway域名
DEFAULT_INTERVAL = 300  # 5分钟
LOCAL_DOCS_DIR = "data/docs"
SYNC_STATE_FILE = "data/sync_state.json"


def load_sync_state() -> dict:
    """加载同步状态"""
    state_file = Path(SYNC_STATE_FILE)
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_sync": 0, "downloaded_files": []}


def save_sync_state(state: dict):
    """保存同步状态"""
    state_file = Path(SYNC_STATE_FILE)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def list_remote_files(server: str) -> list:
    """获取远程文件列表"""
    try:
        url = f"{server}/api/documents/list-files"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("files", [])
    except Exception as e:
        print(f"获取远程文件列表失败: {e}")
        return []


def download_file(server: str, category: str, filename: str, local_dir: str) -> bool:
    """下载单个文件"""
    try:
        url = f"{server}/api/documents/download/{category}/{filename}"
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        
        # 创建本地目录
        local_path = Path(local_dir) / category / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"下载成功: {category}/{filename}")
        return True
    except Exception as e:
        print(f"下载失败 {category}/{filename}: {e}")
        return False


def sync_files(server: str, local_dir: str):
    """同步文件"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始同步...")
    
    # 加载同步状态
    state = load_sync_state()
    downloaded = set(state.get("downloaded_files", []))
    
    # 获取远程文件列表
    remote_files = list_remote_files(server)
    if not remote_files:
        print("没有远程文件或获取失败")
        return
    
    print(f"远程文件数量: {len(remote_files)}")
    
    # 统计
    new_count = 0
    skip_count = 0
    fail_count = 0
    
    for file_info in remote_files:
        category = file_info.get("category", "textbook")
        filename = file_info.get("filename", "")
        
        if not filename:
            continue
        
        file_key = f"{category}/{filename}"
        
        # 检查是否已下载
        if file_key in downloaded:
            skip_count += 1
            continue
        
        # 检查本地是否已存在
        local_path = Path(local_dir) / category / filename
        if local_path.exists():
            downloaded.add(file_key)
            skip_count += 1
            continue
        
        # 下载文件
        if download_file(server, category, filename, local_dir):
            downloaded.add(file_key)
            new_count += 1
        else:
            fail_count += 1
    
    # 更新同步状态
    state["last_sync"] = time.time()
    state["downloaded_files"] = list(downloaded)
    save_sync_state(state)
    
    print(f"同步完成: 新增 {new_count}, 跳过 {skip_count}, 失败 {fail_count}")


def main():
    parser = argparse.ArgumentParser(description="GeoTeach RAG 文件同步脚本")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="服务器地址")
    parser.add_argument("--interval", type=int, default=0, help="同步间隔（秒），0表示只同步一次")
    parser.add_argument("--local-dir", default=LOCAL_DOCS_DIR, help="本地目录")
    
    args = parser.parse_args()
    
    print(f"服务器: {args.server}")
    print(f"本地目录: {args.local_dir}")
    
    if args.interval > 0:
        print(f"同步间隔: {args.interval}秒")
        print("按 Ctrl+C 停止")
        
        while True:
            try:
                sync_files(args.server, args.local_dir)
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n停止同步")
                break
    else:
        sync_files(args.server, args.local_dir)


if __name__ == "__main__":
    main()
