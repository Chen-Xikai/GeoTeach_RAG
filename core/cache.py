# -*- coding: utf-8 -*-
"""
GeoTeach AI Agent - Embedding缓存模块

提供基于文件的Embedding缓存，避免重复调用API。
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from functools import lru_cache


class EmbeddingCache:
    """Embedding向量缓存"""
    
    def __init__(self, cache_dir: str = "data/cache", max_memory_items: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "embedding_cache.json"
        
        # 内存缓存（LRU）
        self._memory_cache: Dict[str, List[float]] = {}
        self._max_memory_items = max_memory_items
        
        # 加载磁盘缓存
        self._disk_cache: Dict[str, List[float]] = {}
        self._load_cache()
        
        # 统计
        self._hits = 0
        self._misses = 0
    
    def _load_cache(self):
        """从磁盘加载缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._disk_cache = json.load(f)
                print(f"加载Embedding缓存: {len(self._disk_cache)}条记录")
            except Exception as e:
                print(f"加载缓存失败: {e}")
                self._disk_cache = {}
    
    def _save_cache(self):
        """保存缓存到磁盘"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._disk_cache, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def _get_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode("utf-8")).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """获取缓存的Embedding"""
        key = self._get_key(text)
        
        # 先查内存缓存
        if key in self._memory_cache:
            self._hits += 1
            return self._memory_cache[key]
        
        # 再查磁盘缓存
        if key in self._disk_cache:
            self._hits += 1
            # 提升到内存缓存
            self._memory_cache[key] = self._disk_cache[key]
            return self._disk_cache[key]
        
        self._misses += 1
        return None
    
    def set(self, text: str, embedding: List[float]):
        """设置缓存"""
        key = self._get_key(text)
        
        # 更新内存缓存
        self._memory_cache[key] = embedding
        
        # 内存缓存满了，清理一半
        if len(self._memory_cache) > self._max_memory_items:
            keys_to_remove = list(self._memory_cache.keys())[:self._max_memory_items // 2]
            for k in keys_to_remove:
                del self._memory_cache[k]
        
        # 更新磁盘缓存
        self._disk_cache[key] = embedding
    
    def get_batch(self, texts: List[str]) -> Tuple[List[Optional[List[float]]], List[int]]:
        """批量获取缓存，返回(结果列表, 未命中索引列表)"""
        results = []
        missed_indices = []
        
        for i, text in enumerate(texts):
            embedding = self.get(text)
            results.append(embedding)
            if embedding is None:
                missed_indices.append(i)
        
        return results, missed_indices
    
    def set_batch(self, texts: List[str], embeddings: List[List[float]]):
        """批量设置缓存"""
        for text, embedding in zip(texts, embeddings):
            self.set(text, embedding)
    
    def save(self):
        """手动保存缓存"""
        self._save_cache()
    
    def get_stats(self) -> dict:
        """获取缓存统计"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            "memory_items": len(self._memory_cache),
            "disk_items": len(self._disk_cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%"
        }


# 全局缓存实例
_cache_instance: Optional[EmbeddingCache] = None


def get_embedding_cache() -> EmbeddingCache:
    """获取全局Embedding缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = EmbeddingCache()
    return _cache_instance
