# -*- coding: utf-8 -*-
"""
GeoTeach RAG - 文件审核脚本

从远程服务器下载待审核的文件到本地，进行安全检查后批准或拒绝。

用法:
  python review_files.py --server URL --list              # 列出待审核文件
  python review_files.py --server URL --download ID       # 下载文件到本地审核
  python review_files.py --server URL --approve ID        # 批准文件
  python review_files.py --server URL --reject ID         # 拒绝文件
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime


# 默认配置
DEFAULT_SERVER = "https://your-app.up.railway.app"  # 替换为你的Railway域名
REVIEW_DIR = "data/review"  # 本地审核目录


def list_pending(server: str):
    """列出待审核文件"""
    try:
        url = f"{server}/api/documents/pending"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        files = data.get("files", [])
        count = data.get("count", 0)
        
        if count == 0:
            print("没有待审核的文件")
            return
        
        print(f"\n待审核文件 ({count} 个):")
        print("-" * 80)
        print(f"{'ID':<30} {'文件名':<30} {'分类':<10} {'大小':<10} {'上传时间'}")
        print("-" * 80)
        
        for f in files:
            pending_id = f.get("pending_id", "")
            filename = f.get("original_filename", "")
            category = f.get("category", "")
            size = f.get("file_size", 0)
            upload_time = f.get("upload_time", 0)
            
            # 格式化大小
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/1024/1024:.1f}MB"
            
            # 格式化时间
            time_str = datetime.fromtimestamp(upload_time).strftime("%Y-%m-%d %H:%M") if upload_time else "-"
            
            print(f"{pending_id:<30} {filename:<30} {category:<10} {size_str:<10} {time_str}")
        
        print()
    except Exception as e:
        print(f"获取待审核文件失败: {e}")


def download_for_review(server: str, pending_id: str, local_dir: str):
    """下载文件到本地审核目录"""
    try:
        # 获取待审核文件列表
        url = f"{server}/api/documents/pending"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # 查找目标文件
        target_file = None
        for f in data.get("files", []):
            if f.get("pending_id") == pending_id:
                target_file = f
                break
        
        if not target_file:
            print(f"未找到待审核文件: {pending_id}")
            return False
        
        # 下载文件
        filename = target_file.get("original_filename", "unknown")
        download_url = f"{server}/api/documents/download/_pending/{pending_id}"
        
        print(f"正在下载: {filename}...")
        response = requests.get(download_url, timeout=60, stream=True)
        response.raise_for_status()
        
        # 保存到审核目录
        review_path = Path(local_dir)
        review_path.mkdir(parents=True, exist_ok=True)
        
        file_path = review_path / filename
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 保存元数据
        meta_path = file_path.with_suffix(".review.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "pending_id": pending_id,
                "server": server,
                "filename": filename,
                "category": target_file.get("category"),
                "download_time": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"下载成功: {file_path}")
        print(f"元数据: {meta_path}")
        print("\n请检查文件内容，确认安全后运行:")
        print(f"  python review_files.py --server {server} --approve {pending_id}")
        print(f"  python review_files.py --server {server} --reject {pending_id}")
        
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False


def approve_file(server: str, pending_id: str):
    """批准文件"""
    try:
        url = f"{server}/api/documents/approve"
        data = {"pending_id": pending_id, "approved": True}
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        print(f"批准成功: {result.get('message', '')}")
        return True
    except Exception as e:
        print(f"批准失败: {e}")
        return False


def reject_file(server: str, pending_id: str):
    """拒绝文件"""
    try:
        url = f"{server}/api/documents/approve"
        data = {"pending_id": pending_id, "approved": False}
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        print(f"拒绝成功: {result.get('message', '')}")
        return True
    except Exception as e:
        print(f"拒绝失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="GeoTeach RAG 文件审核脚本")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="服务器地址")
    parser.add_argument("--list", action="store_true", help="列出待审核文件")
    parser.add_argument("--download", metavar="ID", help="下载文件到本地审核")
    parser.add_argument("--approve", metavar="ID", help="批准文件")
    parser.add_argument("--reject", metavar="ID", help="拒绝文件")
    parser.add_argument("--review-dir", default=REVIEW_DIR, help="本地审核目录")
    
    args = parser.parse_args()
    
    if args.list:
        list_pending(args.server)
    elif args.download:
        download_for_review(args.server, args.download, args.review_dir)
    elif args.approve:
        approve_file(args.server, args.approve)
    elif args.reject:
        reject_file(args.server, args.reject)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
