import os
import shutil
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from config import (
    VECTOR_DB_URI, VECTOR_DB_COLLECTION, TOP_K
)

# SiliconFlow免费Embedding配置
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "sk-free")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5"

def get_embeddings():
    """获取SiliconFlow免费Embedding模型"""
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=SILICONFLOW_API_KEY,
        openai_api_base=SILICONFLOW_BASE_URL,
        check_embedding_ctx_length=False
    )

def get_vector_store():
    """获取Chroma向量库实例"""
    embeddings = get_embeddings()
    
    return Chroma(
        embedding_function=embeddings,
        persist_directory=VECTOR_DB_URI,
        collection_name=VECTOR_DB_COLLECTION
    )

def add_documents(docs):
    """添加文档到向量库"""
    vector_store = get_vector_store()
    vector_store.add_documents(docs)
    print(f"已添加 {len(docs)} 个文档片段到向量库")

def get_retriever():
    """获取检索器"""
    vector_store = get_vector_store()
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K}
    )

def clear_collection():
    """清空向量库（删除本地数据库目录）"""
    try:
        if os.path.exists(VECTOR_DB_URI):
            shutil.rmtree(VECTOR_DB_URI)
            print("已清空向量库")
        else:
            print("向量库目录不存在")
    except Exception as e:
        print(f"清空失败: {e}")

def get_collection_stats():
    """获取集合统计信息"""
    try:
        if os.path.exists(VECTOR_DB_URI):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(VECTOR_DB_URI):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            return {
                "name": VECTOR_DB_COLLECTION,
                "status": "已初始化",
                "file_size": f"{total_size / 1024:.2f} KB"
            }
        else:
            return {
                "name": VECTOR_DB_COLLECTION,
                "status": "未初始化",
                "file_size": "0 KB"
            }
    except Exception as e:
        return {"name": VECTOR_DB_COLLECTION, "status": "错误", "error": str(e)}
