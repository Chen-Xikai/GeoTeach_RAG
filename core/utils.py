# -*- coding: utf-8 -*-
"""
GeoTeach RAG - 工具函数模块

提供通用的工具函数。
"""

import hashlib
from pathlib import Path
from datetime import datetime


def content_hash(text: str) -> str:
    """计算内容哈希（MD5）"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def md5_short(text: str, length: int = 8) -> str:
    """计算短MD5哈希"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:length]


def get_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_path(path: str) -> str:
    """标准化路径（使用正斜杠）"""
    return str(Path(path)).replace("\\", "/")


def ensure_dir(path: str) -> Path:
    """确保目录存在"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_file_info(file_path: Path) -> dict:
    """获取文件信息"""
    stat = file_path.stat()
    return {
        "path": str(file_path),
        "name": file_path.name,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "extension": file_path.suffix.lower(),
    }
