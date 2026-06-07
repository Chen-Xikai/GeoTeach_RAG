# -*- coding: utf-8 -*-
"""
GeoTeach RAG - 任务调度器模块

支持 Embedding 的优先级队列调度，确保建库和查询请求互不阻塞。

功能:
  - 优先级队列：priority=0 (VIP查询) / priority=100 (建库)
  - 委托 EmbeddingAPI 执行实际向量化

用法:
  from core.scheduler import get_scheduler

  scheduler = get_scheduler()
  embeddings = scheduler.embed_sync(["文本1", "文本2"], priority=100)
  vec = await scheduler.embed_async(["查询文本"], priority=0)
"""

import os
import sys
import threading
import queue
import uuid
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logger = logging.getLogger("GeoTeach-Scheduler")

_global_scheduler = None
_global_lock = threading.Lock()


class TaskScheduler:
    """优先级队列调度器，委托 EmbeddingAPI 执行向量化"""

    def __init__(self, emb_api=None):
        if emb_api is None:
            from core.api import EmbeddingAPI
            emb_api = EmbeddingAPI()
        
        self._api = emb_api
        self._queue = queue.PriorityQueue()
        self._results = {}
        self._results_lock = threading.Lock()
        self._running = False
        self._thread = None
        self.start()
        logger.info(f"调度器已启动 (model={emb_api.get_info()['model']})")

    def start(self):
        """启动调度器"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True, name="SchedulerWorker")
        self._thread.start()

    def stop(self):
        """停止调度器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _worker(self):
        """工作线程"""
        while self._running:
            try:
                priority, task_id, texts, event = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                vectors = self._api.embed(texts)
                with self._results_lock:
                    self._results[task_id] = vectors
            except Exception as e:
                with self._results_lock:
                    self._results[task_id] = e
            finally:
                event.set()

    def embed_sync(self, texts: List[str], priority: int = 100, timeout: int = 300) -> List[List[float]]:
        """同步 embedding
        
        Args:
            texts: 文本列表
            priority: 优先级（0=VIP查询, 100=建库）
            timeout: 超时时间（秒）
            
        Returns:
            向量列表
        """
        task_id = uuid.uuid4().hex
        event = threading.Event()
        self._queue.put((priority, task_id, texts, event))
        if not event.wait(timeout=timeout):
            raise TimeoutError(f"Embedding 服务超时 ({timeout}s)")
        with self._results_lock:
            result = self._results.pop(task_id, None)
        if isinstance(result, Exception):
            raise result
        return result

    async def embed_async(self, texts: List[str], priority: int = 0, timeout: int = 60) -> List[List[float]]:
        """异步 embedding
        
        Args:
            texts: 文本列表
            priority: 优先级（0=VIP查询, 100=建库）
            timeout: 超时时间（秒）
            
        Returns:
            向量列表
        """
        return await asyncio.to_thread(self.embed_sync, texts, priority=priority, timeout=timeout)

    def get_info(self) -> dict:
        """获取调度器信息"""
        return {
            "running": self._running,
            "queue_size": self._queue.qsize(),
            "model": self._api.get_info()['model'],
        }


def get_scheduler() -> TaskScheduler:
    """获取全局单例调度器"""
    global _global_scheduler
    if _global_scheduler is not None:
        return _global_scheduler

    with _global_lock:
        if _global_scheduler is not None:
            return _global_scheduler

        _global_scheduler = TaskScheduler()
        return _global_scheduler
