# -*- coding: utf-8 -*-
"""
GeoTeach AI Agent - 异步工具模块

提供异步处理优化，支持并发执行。
"""

import asyncio
from typing import List, Callable, Any, Coroutine
from functools import partial


async def run_in_executor(func, *args, **kwargs):
    """在线程池中运行同步函数"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


async def batch_process(items: List[Any], process_func: Callable, batch_size: int = 10) -> List[Any]:
    """批量处理任务"""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_func(item) for item in batch],
            return_exceptions=True
        )
        results.extend(batch_results)
    
    return results


async def parallel_search(queries: List[str], search_func: Callable) -> List[List[dict]]:
    """并行搜索多个查询"""
    tasks = [run_in_executor(search_func, query) for query in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理异常
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"查询 '{queries[i]}' 失败: {result}")
            processed_results.append([])
        else:
            processed_results.append(result)
    
    return processed_results


class AsyncTaskQueue:
    """异步任务队列"""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = asyncio.Queue()
        self.results = {}
    
    async def add_task(self, task_id: str, coro: Coroutine):
        """添加任务"""
        await self.queue.put((task_id, coro))
    
    async def process_task(self, task_id: str, coro: Coroutine):
        """处理单个任务"""
        async with self.semaphore:
            try:
                result = await coro
                self.results[task_id] = {"success": True, "result": result}
            except Exception as e:
                self.results[task_id] = {"success": False, "error": str(e)}
    
    async def run_all(self) -> dict:
        """运行所有任务"""
        tasks = []
        
        while not self.queue.empty():
            task_id, coro = await self.queue.get()
            task = asyncio.create_task(self.process_task(task_id, coro))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        return self.results


def async_retry(max_retries: int = 3, delay: float = 1.0):
    """异步重试装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator
