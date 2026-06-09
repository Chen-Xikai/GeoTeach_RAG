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
                except Exception:
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
            safe_source = source.replace("\\", "\\\\")
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'source == "{safe_source}"',
                limit=1
            )
            return len(results) > 0
        except Exception:
            return False
    
    def get_hash(self, source: str) -> Optional[str]:
        """获取文档hash"""
        try:
            safe_source = source.replace("\\", "\\\\")
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'source == "{safe_source}"',
                output_fields=["content_hash"],
                limit=1
            )
            if results:
                return results[0].get("content_hash")
            return None
        except Exception:
            return None
    
    def list_documents(self, category: str = None) -> List[dict]:
        """获取唯一文档列表（按source去重，返回切片数和文件类型）"""
        try:
            filter_expr = None
            if category:
                filter_expr = f'category == "{category}"'
            
            # 查询所有chunk
            results = self.client.query(
                collection_name=self.collection_name,
                filter=filter_expr,
                output_fields=["source", "category", "file_type"],
                limit=10000
            )
            
            # 按source分组计数
            doc_chunks = {}
            for result in results:
                source = result.get("source", "")
                if source:
                    if source not in doc_chunks:
                        doc_chunks[source] = {
                            "category": result.get("category", ""),
                            "file_type": result.get("file_type", "other"),
                            "chunks": 0
                        }
                    doc_chunks[source]["chunks"] += 1
            
            # 返回去重结果 + chunks数量 + 文件类型
            documents = []
            for source, info in doc_chunks.items():
                documents.append({
                    "id": source,
                    "metadata": {"source": source, "category": info["category"]},
                    "file_type": info["file_type"],
                    "chunks": info["chunks"]
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
    
    def get_document_info(self, source: str) -> Optional[dict]:
        """获取文档信息"""
        try:
            # Milvus过滤器需要转义反斜杠
            safe_source = source.replace("\\", "\\\\")
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'source == "{safe_source}"',
                output_fields=["source", "category", "content_hash", "content"],
                limit=1
            )
            if results:
                result = results[0]
                # 统计chunks数量
                count_results = self.client.query(
                    collection_name=self.collection_name,
                    filter=f'source == "{safe_source}"',
                    output_fields=["id"],
                    limit=1000
                )
                chunks = len(count_results) if count_results else 0
                
                return {
                    "source": result.get("source", ""),
                    "source_name": Path(result.get("source", "")).name,
                    "category": result.get("category", ""),
                    "content_hash": result.get("content_hash", ""),
                    "chunks": chunks,
                }
            return None
        except Exception as e:
            print(f"获取文档信息失败 {source}: {e}")
            return None
    
    def get_document_chunks(self, source: str) -> List[dict]:
        """获取指定文档的所有切片"""
        try:
            # Milvus过滤器需要转义反斜杠
            safe_source = source.replace("\\", "\\\\")
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'source == "{safe_source}"',
                output_fields=["id", "content", "category", "source"],
                limit=10000
            )
            chunks = []
            for i, result in enumerate(results, 1):
                chunks.append({
                    "index": i,
                    "content": result.get("content", ""),
                    "source": result.get("source", ""),
                    "category": result.get("category", ""),
                })
            return chunks
        except Exception as e:
            print(f"获取切片失败 {source}: {e}")
            return []
    
    def update_file_type(self, source: str, file_type: str) -> bool:
        """更新文档的文件类型"""
        try:
            safe_source = source.replace("\\", "\\\\")
            # 查询该文档的所有chunk
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'source == "{safe_source}"',
                output_fields=["id", "source", "category", "content_hash", "content"],
                limit=10000
            )
            
            if not results:
                print(f"未找到文档: {source}")
                return False
            
            # 获取第一个chunk的embedding用于更新
            ids_to_update = [r["id"] for r in results]
            
            # Milvus Lite 不支持直接更新字段，需要删除后重新插入
            # 但为了简单起见，我们只更新第一个chunk的file_type
            # 实际上Milvus Lite的动态字段更新有限制
            # 这里我们采用删除+重新插入的方式
            
            # 获取embedding
            search_results = self.client.search(
                collection_name=self.collection_name,
                data=[self.embeddings.embed_query("test")],
                limit=1,
                filter=f'source == "{safe_source}"',
                output_fields=["vector", "source", "category", "file_type", "content_hash", "content"]
            )
            
            if search_results and search_results[0]:
                # 删除旧记录
                self.client.delete(
                    collection_name=self.collection_name,
                    ids=ids_to_update
                )
                
                # 重新插入，更新file_type
                new_data = []
                for i, r in enumerate(results):
                    new_data.append({
                        "id": r["id"],
                        "vector": search_results[0][0].get("entity", {}).get("vector", []),
                        "source": r.get("source", ""),
                        "category": r.get("category", ""),
                        "file_type": file_type,
                        "content_hash": r.get("content_hash", ""),
                        "content": r.get("content", ""),
                    })
                
                self.client.insert(
                    collection_name=self.collection_name,
                    data=new_data
                )
                
                print(f"已更新文件类型: {source} -> {file_type}")
                return True
            
            return False
        except Exception as e:
            print(f"更新文件类型失败: {e}")
            return False
    
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
            file_type = metadata.pop("file_type", "other")
            
            doc_ids.append(doc_id)
            texts.append(chunk["page_content"])
            metadatas.append({
                "doc_id": doc_id,
                "source": source,
                "category": category,
                "file_type": file_type,
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
            safe_source = source.replace("\\", "\\\\")
            
            # 先尝试精确匹配
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'source == "{safe_source}"',
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
    
    def check_orphan_records(self, local_dirs: List[str]) -> List[dict]:
        """检查孤立记录（本地文件已删除，但向量记录还在）
        
        Args:
            local_dirs: 本地目录路径列表
            
        Returns:
            孤立记录列表
        """
        # 收集所有本地文件路径
        all_local_files = set()
        for dir_path in local_dirs:
            p = Path(dir_path)
            if p.exists():
                for f in p.rglob("*"):
                    if f.is_file():
                        all_local_files.add(str(f.resolve()))
        
        # 检查向量记录
        stored_sources = self.list_sources()
        orphans = []
        for source in stored_sources:
            source_path = Path(source)
            # 检查文件是否存在
            if not source_path.exists() and str(source_path.resolve()) not in all_local_files:
                orphans.append({"source": source})
        
        return orphans
    
    def clean_orphan_records(self, local_dirs: List[str]) -> int:
        """清理孤立记录
        
        Args:
            local_dirs: 本地目录路径列表
            
        Returns:
            清理的记录数
        """
        orphans = self.check_orphan_records(local_dirs)
        count = 0
        for doc in orphans:
            self.delete(doc["source"])
            count += 1
        return count
    
    def sync(self, documents: List[dict], chunk_cfg: dict = None, source_type: str = "local_file", on_progress=None) -> dict:
        """同步文档 — 延迟加载（直接操作）
        
        对比 hash，自动增删改
        
        Args:
            documents: 文档列表，每个文档包含 path, page_content, metadata
            chunk_cfg: 切块配置
            source_type: 来源类型
            on_progress: 进度回调函数 (op, idx, total, name, count)
            
        Returns:
            同步统计信息
        """
        from core.chunking import chunk_single_document
        from core.utils import content_hash
        
        stats = {"added": 0, "updated": 0, "unchanged": 0, "deleted": 0}
        
        # 获取当前本地文件路径
        current_sources = set()
        for doc in documents:
            source = doc.get("metadata", {}).get("source", "") or doc.get("path", "")
            if source:
                current_sources.add(source)
        
        # 获取已存储的文件路径
        stored_sources = self.list_sources()
        
        # 计算差异
        new_sources = current_sources - stored_sources      # 需要添加
        delete_sources = stored_sources - current_sources   # 需要删除
        common_sources = current_sources & stored_sources   # 需要检查更新
        
        n = len(documents)
        
        # 1. 处理新增文档
        for idx, doc in enumerate(documents, 1):
            source = doc.get("metadata", {}).get("source", "") or doc.get("path", "")
            if source in new_sources:
                fname = Path(source).name
                self.add(doc, chunk_cfg, source_type)
                stats["added"] += 1
                if on_progress:
                    on_progress("add", idx, n, fname, 0)
        
        # 2. 处理更新文档（对比 hash，延迟加载）
        for idx, doc in enumerate(documents, 1):
            source = doc.get("metadata", {}).get("source", "") or doc.get("path", "")
            if source in common_sources:
                fname = Path(source).name
                stored_h = self.get_hash(source)
                current_h = content_hash(doc.get("page_content", ""))
                if stored_h != current_h:
                    # 直接更新
                    self.update(doc, chunk_cfg, source_type)
                    stats["updated"] += 1
                    if on_progress:
                        on_progress("update", idx, n, fname, 0)
                else:
                    stats["unchanged"] += 1
        
        # 3. 处理删除文档
        for source in delete_sources:
            self.delete(source)
            stats["deleted"] += 1
            if on_progress:
                on_progress("delete", 0, 0, Path(source).name, 0)
        
        print(f"同步完成: 新增 {stats['added']}, 更新 {stats['updated']}, 删除 {stats['deleted']}, 未变 {stats['unchanged']}")
        return stats
    
    def rebuild(self, documents: List[dict], chunk_cfg: dict = None, source_type: str = "local_file", on_progress=None) -> int:
        """全量重建 — 影子集合策略
        
        创建新集合 → 重新处理所有文档 → 验证 → 切换 → 清理旧集合
        
        Args:
            documents: 文档列表
            chunk_cfg: 切块配置
            source_type: 来源类型
            on_progress: 进度回调函数
            
        Returns:
            重建的chunk数量
        """
        from core.chunking import chunk_single_document
        from datetime import datetime
        
        shadow_name = None
        try:
            # 创建影子集合
            shadow_name = f"{self.collection_name}_v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 创建新集合
            self.client.create_collection(
                collection_name=shadow_name,
                dimension=1024,
            )
            print(f"创建影子集合: {shadow_name}")
            
            # 处理所有文档
            total = 0
            n = len(documents)
            for i, doc in enumerate(documents, 1):
                chunks = chunk_single_document(doc, chunk_cfg, source_type)
                if chunks:
                    self._add_to_collection(shadow_name, chunks)
                    total += len(chunks)
                    fname = Path(doc.get("metadata", {}).get("source", "")).name
                    if on_progress:
                        on_progress("rebuild", i, n, fname, len(chunks))
            
            # 验证影子集合
            shadow_stats = self.client.get_collection_stats(shadow_name)
            shadow_count = shadow_stats.get("row_count", 0)
            if shadow_count == 0 and total > 0:
                raise ValueError("影子集合验证失败: 数据为空")
            
            # 切换到影子集合
            old_collection = self.collection_name
            self.collection_name = shadow_name
            self._next_id = shadow_count + 1
            
            # 清理旧集合
            try:
                self.client.drop_collection(old_collection)
                print(f"清理旧集合: {old_collection}")
            except Exception as e:
                print(f"清理旧集合失败（可忽略）: {e}")
            
            # 保存缓存
            self._cache.save()
            
            print(f"重建完成: {shadow_name}, {total} chunks")
            return total
            
        except Exception as e:
            print(f"重建失败: {e}")
            # 清理失败的影子集合
            if shadow_name:
                try:
                    self.client.drop_collection(shadow_name)
                except Exception:
                    pass
            raise
    
    def _add_to_collection(self, collection_name: str, chunks: List[dict]):
        """向指定集合添加chunks"""
        texts = [c["page_content"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        # 批量获取嵌入向量
        cached_results, missed_indices = self._cache.get_batch(texts)
        
        if missed_indices:
            missed_texts = [texts[i] for i in missed_indices]
            missed_embeddings = self.embeddings.embed_documents(missed_texts)
            self._cache.set_batch(missed_texts, missed_embeddings)
            for i, idx in enumerate(missed_indices):
                cached_results[idx] = missed_embeddings[i]
        
        embeddings = cached_results
        
        # 构建数据
        data = []
        for i, (emb, meta) in enumerate(zip(embeddings, metadatas)):
            content_hash = hashlib.md5(texts[i].encode()).hexdigest()
            data.append({
                "id": self._next_id + i,
                "vector": emb,
                "source": meta.get("source", ""),
                "category": meta.get("category", ""),
                "file_type": meta.get("file_type", "other"),
                "content_hash": content_hash,
                "content": texts[i],
            })
        
        # 插入数据
        self.client.insert(
            collection_name=collection_name,
            data=data
        )
        
        self._next_id += len(data)
