"""
GeoTeach AI Agent - 文本切分模块

提供多种文本切分策略，支持递归切分和扁平切分。
"""

from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_chunk_config


def split_text(text: str, cfg: dict = None) -> List[str]:
    """按模板配置切片"""
    if cfg is None:
        cfg = get_chunk_config()
    
    chunk_size = cfg.get("chunk_size", 500)
    
    # 如果文本长度小于等于chunk_size，直接返回整个文本作为一个chunk
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=cfg.get("overlap", 50),
        separators=cfg.get("separators", ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""])
    )
    
    return text_splitter.split_text(text)


def chunk_single_document(doc: dict, chunk_cfg: dict = None, source_type: str = "local_file") -> List[dict]:
    """对单个文档切片，生成带元数据的chunk列表"""
    if chunk_cfg is None:
        chunk_cfg = get_chunk_config()
    
    text = doc.get("page_content", "")
    metadata = doc.get("metadata", {})
    
    chunks_text = split_text(text, chunk_cfg)
    
    chunks = []
    for i, chunk_text in enumerate(chunks_text):
        chunk = {
            "page_content": chunk_text,
            "metadata": {
                **metadata,
                "chunk_index": i,
                "chunk_total": len(chunks_text),
                "source_type": source_type
            }
        }
        chunks.append(chunk)
    
    return chunks


def evaluate_chunks(chunks: List[dict]) -> dict:
    """评估切分质量，返回可视化数据"""
    if not chunks:
        return {
            "count": 0,
            "avg_length": 0,
            "min_length": 0,
            "max_length": 0,
            "std_dev": 0,
            "distribution": {},
            "samples": []
        }
    
    lengths = [len(chunk["page_content"]) for chunk in chunks]
    
    avg_length = sum(lengths) / len(lengths)
    min_length = min(lengths)
    max_length = max(lengths)
    
    # 计算标准差
    variance = sum((x - avg_length) ** 2 for x in lengths) / len(lengths)
    std_dev = variance ** 0.5
    
    # 长度分布
    distribution = {}
    for length in lengths:
        bucket = f"{(length // 100) * 100}-{(length // 100) * 100 + 99}"
        distribution[bucket] = distribution.get(bucket, 0) + 1
    
    # 示例chunks
    samples = []
    for i, chunk in enumerate(chunks[:3]):
        samples.append({
            "index": i,
            "content": chunk["page_content"][:200] + "..." if len(chunk["page_content"]) > 200 else chunk["page_content"],
            "length": len(chunk["page_content"])
        })
    
    return {
        "count": len(chunks),
        "avg_length": round(avg_length, 2),
        "min_length": min_length,
        "max_length": max_length,
        "std_dev": round(std_dev, 2),
        "distribution": distribution,
        "samples": samples
    }
