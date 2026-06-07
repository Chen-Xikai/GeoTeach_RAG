"""
GeoTeach AI Agent - 配置层
"""

from .settings import (
    load_config,
    save_config,
    get_siliconflow_config,
    get_embedding_config,
    get_rerank_config,
    get_llm_config,
    get_web_config,
    get_retrieval_config,
    get_chunk_config,
    get_docs_dir,
    get_generated_dir,
    get_templates_dir,
    get_catalog_dir,
    get_template_config,
    get_collection_name,
    ensure_directories,
)

__all__ = [
    "load_config",
    "save_config",
    "get_siliconflow_config",
    "get_embedding_config",
    "get_rerank_config",
    "get_llm_config",
    "get_web_config",
    "get_retrieval_config",
    "get_chunk_config",
    "get_docs_dir",
    "get_generated_dir",
    "get_templates_dir",
    "get_catalog_dir",
    "get_template_config",
    "get_collection_name",
    "ensure_directories",
]
