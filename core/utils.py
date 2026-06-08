# -*- coding: utf-8 -*-
"""
GeoTeach RAG - 工具函数模块
"""

import hashlib


def content_hash(text: str) -> str:
    """计算内容哈希（MD5）"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()
