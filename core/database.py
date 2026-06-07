"""
GeoTeach AI Agent - 数据库操作模块

提供Milvus的CRUD操作支持，包含Embedding缓存优化。
"""

import os
import hashlib
from typing import List, Dict, Optional, Set
from pathlib import Path

from config import (
    get_collection_name,
    get_siliconflow_config,
    get_embedding_config,
    get_retrieval_config,
)
from core.cache import get_embedding_cache


class DocumentDatabase:
    """统一的数据库操作类 - 使用Milvus Lite"""
    
    def __init__(self):
        self.collection_name = get_collection_name()
        # 使用绝对路径
        db_path = os.getenv("MILVUS_DB_PATH", "data/milvus.db")
        self.db_path = os.path.abspath(db_path)
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 初始化Embedding
        config = get_siliconflow_config()
        embedding_config = get_embedding_config()
        
        self._api_key = config["api_key"]
        self._base_url = config["base_url"]
        self._embedding_model = embedding_config["model"]
        
        # 延迟初始化
        self._client = None
        self._embeddings = None
        self._next_id = 1
        
        # Embedding缓存
        self._cache = get_embedding_cache()
    
    @property
    def client(self):
        """延迟加载Milvus客户端"""
        if self._client is None:
            try:
                from pymilvus import MilvusClient
                # 使用Milvus Lite（本地文件存储）
                self._client = MilvusClient(uri=self.db_path)
                
                # 确保集合存在
                self._ensure_collection()
            except ImportError:
                raise ImportError("pymilvus未安装，请运行: pip install pymilvus milvus-lite")
        return self._client
    
    @property
    def embeddings(self):
        """延迟加载Embedding模型"""
        if self._embeddings is None:
            from langchain_openai import OpenAIEmbeddings
            self._embeddings = OpenAIEmbeddings(
                model=self._embedding_model,
                openai_api_key=self._api_key,
                openai_api_base=self._base_url,
                check_embedding_ctx_length=False
            )
        return self._embeddings
    
    def _ensure_collection(self):
        """确保集合存在并优化索引"""
        try:
            # 检查集合是否存在
            collections = self.client.list_collections()
            
            if self.collection_name not in collections:
                # 创建集合
                self.client.create_collection(
                    collection_name=self.collection_name,
                    dimension=1024,  # BAAI/bge-large-zh-v1.5的维度
                )
                print(f"创建集合: {self.collection_name}")
                
                # 创建索引（优化查询性能）
                self._create_index()
                
                self._next_id = 1
            else:
                # 加载集合到内存（查询前必须加载）
                self.client.load_collection(self.collection_name)
                # 使用count()方法获取文档数量来设置next_id
                try:
                    count = self.count()
                    self._next_id = count + 1
                except:
                    self._next_id = 1
        except Exception as e:
            print(f"确保集合存在失败: {e}")
    
    def _create_index(self):
        """创建向量索引（优化查询性能）"""
        try:
            # 使用IVF_FLAT索引，适合中小规模数据
            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="IVF_FLAT",
                metric_type="COSINE",
                params={"nlist": 1024}
            )
            
            self.client.create_index(
                collection_name=self.collection_name,
                index_params=index_params
            )
            print(f"创建索引成功: IVF_FLAT, nlist=1024")
        except Exception as e:
            print(f"创建索引失败（可忽略）: {e}")
    
    def count(self) -> int:
        """获取文档总数（chunk数量）"""
        try:
            stats = self.client.get_collection_stats(self.collection_name)
            return stats.get("row_count", 0)
        except Exception:
            return 0
    
    def count_documents(self) -> int:
        """获取唯一文档数量（按source去重）"""
        try:
            sources = self.list_sources()
            return len(sources)
        except Exception:
            return 0
    
    def exists(self, source: str) -> bool:
        """检查文档是否存在"""
        try:
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'source == "{source}"',
                limit=1
            )
            return len(results) > 0
        except Exception:
            return False
    
    def get_hash(self, source: str) -> Optional[str]:
        """获取文档hash"""
        try:
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'source == "{source}"',
                output_fields=["content_hash"],
                limit=1
            )
            if results:
                return results[0].get("content_hash")
            return None
        except Exception:
            return None
    
    def list_documents(self, category: str = None) -> List[dict]:
        """获取唯一文档列表（按source去重）"""
        try:
            filter_expr = None
            if category:
                filter_expr = f'category == "{category}"'
            
            results = self.client.query(
                collection_name=self.collection_name,
                filter=filter_expr,
                output_fields=["source", "category", "content"],
                limit=1000
            )
            
            # 按source去重，只保留每个文档的第一个chunk
            seen_sources = set()
            documents = []
            for result in results:
                source = result.get("source", "")
                if source and source not in seen_sources:
                    seen_sources.add(source)
                    content = result.get("content", "")
                    documents.append({
                        "id": source,
                        "metadata": {
                            "source": source,
                            "category": result.get("category", ""),
                        },
                        "content": content[:200] if content else ""
                    })
            
            return documents
        except Exception as e:
            print(f"列出文档失败: {e}")
            return []
    
    def list_sources(self) -> Set[str]:
        """获取所有唯一来源"""
        try:
            results = self.client.query(
                collection_name=self.collection_name,
                output_fields=["source"],
                limit=1000
            )
            sources = set()
            for result in results:
                source = result.get("source")
                if source:
                    sources.add(source)
            return sources
        except Exception:
            return set()
    
    def search(self, query: str, n_results: int = 5, category: str = None) -> List[dict]:
        """搜索文档（带缓存和索引优化）"""
        retrieval_config = get_retrieval_config()
        k = n_results or retrieval_config.get("k", 5)
        
        try:
            # 尝试从缓存获取查询向量
            cached_embedding = self._cache.get(query)
            if cached_embedding:
                query_embedding = cached_embedding
            else:
                # 获取查询向量
                query_embedding = self.embeddings.embed_query(query)
                # 缓存查询向量
                self._cache.set(query, query_embedding)
            
            # 构建过滤条件
            filter_expr = None
            if category:
                filter_expr = f'category == "{category}"'
            
            # 搜索参数优化
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 16}  # IVF索引的搜索参数
            }
            
            # 搜索
            results = self.client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                limit=k,
                filter=filter_expr,
                output_fields=["source", "category", "content"],
                search_params=search_params
            )
            
            documents = []
            if results and len(results) > 0:
                for hit in results[0]:
                    entity = hit.get("entity", {})
                    content = entity.get("content", "")
                    
                    documents.append({
                        "page_content": content,
                        "metadata": {
                            "source": entity.get("source", ""),
                            "category": entity.get("category", ""),
                        },
                        "score": hit.get("distance", 0)
                    })
            
            return documents
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def add(self, doc: dict, chunk_cfg: dict = None, source_type: str = "local_file") -> List[str]:
        """添加文档（带缓存优化）"""
        from core.chunking import chunk_single_document
        
        # 验证文档内容
        content = doc.get("page_content", "")
        if not content or not content.strip():
            print("警告：文档内容为空，跳过添加")
            return []
        
        # 验证Embedding API
        try:
            test_embedding = self.embeddings.embed_query("test")
            if not test_embedding or len(test_embedding) == 0:
                raise Exception("Embedding API返回空结果")
        except Exception as e:
            raise Exception(f"Embedding API不可用: {e}")
        
        chunks = chunk_single_document(doc, chunk_cfg, source_type)
        
        doc_ids = []
        texts = []
        metadatas = []
        
        for chunk in chunks:
            content_hash = hashlib.md5(chunk["page_content"].encode()).hexdigest()
            doc_id = f"{chunk['metadata'].get('source', 'unknown')}_{content_hash}"
            
            # 准备元数据
            metadata = chunk["metadata"].copy()
            source = metadata.pop("source", "unknown")
            category = metadata.pop("category", "")
            
            doc_ids.append(doc_id)
            texts.append(chunk["page_content"])
            metadatas.append({
                "doc_id": doc_id,
                "source": source,
                "category": category,
                "content_hash": content_hash,
                "content": chunk["page_content"],
            })
        
        # 批量获取嵌入向量（带缓存）
        cached_results, missed_indices = self._cache.get_batch(texts)
        
        if missed_indices:
            # 只对未缓存的文本调用API
            missed_texts = [texts[i] for i in missed_indices]
            missed_embeddings = self.embeddings.embed_documents(missed_texts)
            
            # 更新缓存
            self._cache.set_batch(missed_texts, missed_embeddings)
            
            # 合并结果
            for i, idx in enumerate(missed_indices):
                cached_results[idx] = missed_embeddings[i]
        
        embeddings = cached_results
        
        # 构建数据（包含id字段）
        data = []
        for i, (emb, meta) in enumerate(zip(embeddings, metadatas)):
            data.append({
                "id": self._next_id + i,
                "vector": emb,
                **meta
            })
        
        # 插入数据
        self.client.insert(
            collection_name=self.collection_name,
            data=data
        )
        
        # 更新ID计数器
        self._next_id += len(data)
        
        # 保存缓存
        self._cache.save()
        
        return doc_ids
    
    def delete(self, source: str):
        """删除文档"""
        if not source:
            print("删除失败: source为空")
            return
            
        try:
            # 标准化路径（使用正斜杠）
            source_normalized = source.replace("\\", "/")
            
            # 先尝试精确匹配
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'source == "{source}"',
                output_fields=["id"]
            )
            
            # 如果精确匹配失败，使用文件名匹配
            if not results:
                filename = Path(source).name
                results = self.client.query(
                    collection_name=self.collection_name,
                    filter=f'source like "%{filename}%"',
                    output_fields=["id"]
                )
            
            if results:
                ids_to_delete = [r["id"] for r in results]
                self.client.delete(
                    collection_name=self.collection_name,
                    ids=ids_to_delete
                )
                print(f"已删除: {source} ({len(ids_to_delete)}个文档)")
            else:
                print(f"未找到文档: {source}")
        except Exception as e:
            print(f"删除失败: {e}")
    
    def update(self, doc: dict, chunk_cfg: dict = None, source_type: str = "local_file") -> List[str]:
        """更新文档"""
        source = doc.get("metadata", {}).get("source", "")
        if source:
            self.delete(source)
        return self.add(doc, chunk_cfg, source_type)
    
    def clear(self):
        """清空向量库"""
        try:
            self.client.drop_collection(self.collection_name)
            self._next_id = 1
            self._ensure_collection()
            print("已清空向量库")
        except Exception as e:
            print(f"清空失败: {e}")
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        try:
            doc_count = self.count_documents()
            chunk_count = self.count()
            cache_stats = self._cache.get_stats()
            return {
                "count": doc_count,
                "chunk_count": chunk_count,
                "status": "已初始化" if chunk_count > 0 else "未初始化",
                "database": "Milvus Lite",
                "cache": cache_stats
            }
        except Exception as e:
            return {"count": 0, "chunk_count": 0, "status": "错误", "error": str(e), "database": "Milvus Lite"}
