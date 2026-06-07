import hashlib


def content_hash(content: str) -> str:
    """计算内容hash"""
    return hashlib.md5(content.encode()).hexdigest()


def md5_short(text: str) -> str:
    """生成短MD5"""
    return hashlib.md5(text.encode()).hexdigest()[:8]
