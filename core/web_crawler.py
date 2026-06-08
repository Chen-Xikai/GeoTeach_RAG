"""
GeoTeach AI Agent - 网页爬取模块

从URL抓取网页内容并转换为文档格式。
"""

import re
import hashlib
from pathlib import Path
from typing import Optional

import requests


def crawl_webpage(url: str, timeout: int = 30) -> Optional[dict]:
    """
    爬取网页内容
    
    Args:
        url: 网页URL
        timeout: 请求超时时间（秒）
        
    Returns:
        {"title": str, "content": str, "url": str} 或 None
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
        response.raise_for_status()
        
        # 尝试使用BeautifulSoup解析
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除script和style标签
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            title = soup.title.string if soup.title else url
            content = soup.get_text(separator='\n', strip=True)
            
        except ImportError:
            # 如果没有BeautifulSoup，使用正则表达式简单提取
            title_match = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else url
            
            # 移除HTML标签
            content = re.sub(r'<script[^>]*>.*?</script>', '', response.text, flags=re.DOTALL)
            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
            content = re.sub(r'<[^>]+>', ' ', content)
            content = re.sub(r'\s+', ' ', content).strip()
        
        # 清理内容
        content = _clean_content(content)
        
        if not content or len(content) < 10:
            print(f"网页内容过少: {url}")
            return None
        
        return {
            "title": title[:200] if title else url,
            "content": content,
            "url": url
        }
        
    except requests.exceptions.RequestException as e:
        print(f"爬取网页失败 {url}: {e}")
        return None
    except Exception as e:
        print(f"处理网页失败 {url}: {e}")
        return None


def _clean_content(content: str) -> str:
    """清理网页内容"""
    # 移除多余空白
    content = re.sub(r'\n\s*\n', '\n\n', content)
    content = re.sub(r' +', ' ', content)
    
    # 移除常见噪声
    noise_patterns = [
        r'版权所有.*?保留所有权利',
        r'Copyright.*?All rights reserved',
        r'本网站.*?ICP备.*?号',
        r'登录.*?注册',
        r'首页.*?关于我们.*?联系方式',
    ]
    for pattern in noise_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    return content.strip()


def url_to_filename(url: str) -> str:
    """将URL转换为文件名"""
    # 移除协议
    name = re.sub(r'https?://', '', url)
    # 移除特殊字符
    name = re.sub(r'[^\w\-]', '_', name)
    # 限制长度
    name = name[:100]
    # 添加hash保证唯一性
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"web_{name}_{url_hash}.txt"
