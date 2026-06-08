"""
GeoTeach AI Agent - 配置加载模块

提供统一的配置加载和访问接口。
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 获取配置目录路径
CONFIG_DIR = Path(__file__).parent
ROOT_DIR = CONFIG_DIR.parent

# 加载环境变量
load_dotenv(CONFIG_DIR / ".env")


def load_config() -> dict:
    """加载config.json配置"""
    config_path = CONFIG_DIR / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict):
    """保存config.json配置"""
    config_path = CONFIG_DIR / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ==================== API配置 ====================

def get_siliconflow_config() -> dict:
    """获取SiliconFlow API配置"""
    return {
        "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
        "base_url": os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
    }


def get_embedding_config() -> dict:
    """获取Embedding配置"""
    return {
        "model": os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5"),
    }


def get_rerank_config() -> dict:
    """获取Rerank配置"""
    return {
        "enabled": os.getenv("RERANK_ENABLED", "true").lower() == "true",
        "model": os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3"),
    }


def get_llm_config() -> dict:
    """获取LLM配置"""
    return {
        "model": os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
    }


# ==================== 服务配置 ====================

def get_web_config() -> dict:
    """获取Web服务配置"""
    return {
        "host": os.getenv("WEB_HOST", "127.0.0.1"),
        "port": int(os.getenv("WEB_PORT", "9767")),
    }


# ==================== RAG配置 ====================

def get_retrieval_config() -> dict:
    """获取检索配置"""
    config = load_config()
    return config.get("retrieval", {"k": 5, "fetch_k": 15})


def get_chunk_config(template: str = None) -> dict:
    """获取切分配置"""
    config = load_config()
    templates = config.get("chunk", {}).get("templates", {})
    
    if template and template in templates:
        return templates[template]
    
    default_template = config.get("chunk", {}).get("default_template", "chinese")
    return templates.get(default_template, {
        "chunk_size": 500,
        "overlap": 50,
        "strategy": "recursive",
        "separators": ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    })


# ==================== 路径配置 ====================

def get_docs_dir() -> Path:
    """获取文档目录"""
    return ROOT_DIR / os.getenv("DOCS_DIR", "data/docs")


def get_generated_dir() -> Path:
    """获取生成内容目录"""
    return ROOT_DIR / os.getenv("GENERATED_DIR", "data/generated")


def get_templates_dir() -> Path:
    """获取模板目录"""
    return CONFIG_DIR / "templates"


def get_catalog_dir() -> Path:
    """获取教材目录"""
    return CONFIG_DIR / "catalog"


# ==================== 模板配置 ====================

def get_template_config(template_type: str) -> dict:
    """获取模板配置"""
    config = load_config()
    return config.get("templates", {}).get(template_type, {})


def get_collection_name() -> str:
    """获取集合名称"""
    config = load_config()
    return config.get("collection", {}).get("name", "geoteach_docs")


def get_vision_config() -> dict:
    """获取视觉模型配置"""
    config = load_config()
    return config.get("vision", {
        "enabled": True,
        "ocr_engine": "paddleocr",
        "ocr_language": "ch",
        "vision_model": "Qwen/Qwen2.5-VL-7B-Instruct",
        "table_recognition": True,
        "image_description": True,
        "extract_geographic_info": True
    })


# ==================== 工具函数 ====================

def ensure_directories():
    """确保所有必要目录存在"""
    dirs = [
        get_docs_dir(),
        get_generated_dir(),
        get_templates_dir(),
        get_catalog_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
