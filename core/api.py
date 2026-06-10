"""
GeoTeach AI Agent - API适配器

提供Rerank API接口。
"""

import requests
from typing import List, Tuple
from config import get_siliconflow_config, get_rerank_config


class RerankAPI:
    """Rerank API适配器"""
    
    def __init__(self):
        config = get_siliconflow_config()
        rerank_config = get_rerank_config()
        
        self._enabled = rerank_config["enabled"]
        self._api_key = config["api_key"]
        self._base_url = config["base_url"]
        self._model = rerank_config["model"]
    
    @property
    def enabled(self) -> bool:
        """是否启用Rerank"""
        return self._enabled
    
    def rerank(self, query: str, documents: List[str]) -> Tuple[List[float], List[int]]:
        """同步重排"""
        if not self._enabled:
            return [1.0] * len(documents), list(range(len(documents)))
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self._model,
            "query": query,
            "documents": documents,
            "top_n": len(documents)
        }
        
        response = requests.post(
            f"{self._base_url}/rerank",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        scores = [item["relevance_score"] for item in result["results"]]
        indices = [item["index"] for item in result["results"]]
        
        return scores, indices
