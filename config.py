import os
from dotenv import load_dotenv

load_dotenv()

# 小米mimo配置（同时用于Chat和Embedding）
MIMO_API_KEY = os.getenv("MIMO_API_KEY")
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://platform.xiaomimimo.com/api/v1")
MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-v2.5pro")

# Milvus Lite配置（本地文件存储）
VECTOR_DB_URI = os.getenv("VECTOR_DB_URI", "./milvus_local.db")
VECTOR_DB_COLLECTION = os.getenv("VECTOR_DB_COLLECTION", "geo_teach_docs")

# RAG配置
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K = int(os.getenv("TOP_K", "4"))
