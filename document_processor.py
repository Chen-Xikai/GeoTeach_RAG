import os
from pathlib import Path
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP

# 文件扩展名与加载器映射
LOADER_MAPPING = {
    '.pdf': PyPDFLoader,
    '.docx': Docx2txtLoader,
    '.txt': TextLoader,
    '.md': UnstructuredMarkdownLoader
}

def load_single_document(file_path: str):
    """加载单个文档"""
    ext = Path(file_path).suffix.lower()
    if ext not in LOADER_MAPPING:
        raise ValueError(f"不支持的文件格式: {ext}")
    
    loader_class = LOADER_MAPPING[ext]
    loader = loader_class(file_path)
    return loader.load()

def load_documents(data_dir: str = "data"):
    """加载data目录下所有文档"""
    documents = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"数据目录 {data_dir} 不存在")
        return documents
    
    for ext in LOADER_MAPPING:
        files = list(data_path.rglob(f"*{ext}"))
        for file_path in files:
            try:
                docs = load_single_document(str(file_path))
                # 添加来源元数据
                for doc in docs:
                    doc.metadata['source'] = str(file_path)
                documents.extend(docs)
                print(f"已加载: {file_path}")
            except Exception as e:
                print(f"加载失败 {file_path}: {e}")
    
    return documents

def split_documents(documents):
    """分割文档"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""]
    )
    return text_splitter.split_documents(documents)

def process_documents(data_dir: str = "data"):
    """处理文档：加载 + 分割"""
    print(f"开始加载文档 from {data_dir}...")
    documents = load_documents(data_dir)
    print(f"共加载 {len(documents)} 个文档")
    
    print("开始分割文档...")
    splits = split_documents(documents)
    print(f"分割为 {len(splits)} 个片段")
    
    return splits
