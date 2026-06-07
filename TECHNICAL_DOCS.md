# GeoTeach RAG 技术文档

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈总结](#2-技术栈总结)
3. [系统架构](#3-系统架构)
4. [目录结构](#4-目录结构)
5. [配置说明](#5-配置说明)
6. [核心模块](#6-核心模块)
7. [性能优化](#7-性能优化)
8. [API接口](#8-api接口)
9. [MCP服务](#9-mcp服务)
10. [部署指南](#10-部署指南)

---

## 1. 项目概述

### 1.1 项目简介

GeoTeach RAG 是一个基于 RAG（检索增强生成）技术的地理教学 AI 助手系统，专为地理教师设计，提供：

- **智能资料管理** - 支持 PPT、PDF、DOCX、TXT、Markdown 格式
- **AI 内容生成** - 说课稿、讲课稿、教案、学案自动生成
- **智能问答** - 基于知识库的专业地理教学问答
- **多模态处理** - 支持图片识别、OCR、表格提取
- **MCP 集成** - 支持 Model Context Protocol，可与 AI 助手集成

### 1.2 核心特性

- ✅ 支持多种文档格式（PPT、PDF、DOCX、TXT、MD）
- ✅ 多模态处理（图片识别、OCR、表格提取）
- ✅ 教材目录管理（人教版初中+高中）
- ✅ 多种教学模板（说课稿、讲课稿、教案、学案）
- ✅ 智能问答系统
- ✅ Rerank 检索优化
- ✅ Embedding 缓存加速
- ✅ MCP 协议支持
- ✅ 中文优化

---

## 2. 技术栈总结

### 2.1 技术栈全景

| 层级 | 组件 | 技术选型 | 版本 | 用途 |
|------|------|----------|------|------|
| **前端** | UI框架 | Vue 3 + Element Plus | - | 用户界面 |
| | 构建工具 | Vite | - | 前端构建 |
| | HTTP客户端 | Axios | - | API调用 |
| **后端** | Web框架 | FastAPI | >=0.100.0 | REST API |
| | ASGI服务器 | Uvicorn | >=0.23.0 | 应用服务器 |
| **AI模型** | Embedding | SiliconFlow BAAI/bge-large-zh-v1.5 | - | 文本向量化(1024维) |
| | Rerank | SiliconFlow BAAI/bge-reranker-v2-m3 | - | 检索重排序 |
| | LLM | SiliconFlow Qwen/Qwen2.5-7B-Instruct | - | 内容生成 |
| | Vision | SiliconFlow Qwen/Qwen2.5-VL-7B-Instruct | - | 图片识别/OCR |
| **数据库** | 向量数据库 | Milvus Lite (pymilvus) | >=2.4.0 | 向量存储和检索 |
| **工具库** | 文本切分 | LangChain Text Splitters | >=0.2.0 | 文档分块 |
| | 文档加载 | LangChain Community | >=0.2.0 | PDF加载 |
| | 文档处理 | python-docx, python-pptx, PyMuPDF | - | Office/PDF解析 |
| **协议** | MCP | 自定义实现 | - | AI助手集成 |
| **语言** | Python | Python | >=3.11 | 后端开发 |

### 2.2 技术选型理由

#### 向量数据库：Milvus Lite
- **本地部署**：无需额外服务，基于本地文件
- **高性能**：支持IVF_FLAT索引，查询速度快
- **Python友好**：pymilvus提供良好的Python支持

#### Embedding模型：BGE-large-zh-v1.5
- **中文优化**：专门针对中文文本训练
- **1024维向量**：平衡精度和性能
- **API调用**：通过SiliconFlow云端调用，无需本地GPU

#### LLM：Qwen2.5-7B-Instruct
- **中文能力强**：阿里通义千问系列
- **性价比高**：7B参数，成本可控
- **指令遵循**：Instruct版本，适合生成任务

---

## 3. 系统架构

### 3.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户界面层                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Web 前端 (Vue 3 + Element Plus)             │   │
│  │   首页 │ 资料库 │ 内容生成 │ 智能问答 │ 设置            │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                        服务层 (FastAPI)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ 文档管理 │ │ 内容生成 │ │ 智能问答 │ │ 教材目录 │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│  ┌──────────────────────────────────────────────────────┐     │
│  │                    MCP 服务                           │     │
│  └──────────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────────┤
│                        核心层                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ 文档处理 │ │ 向量检索 │ │ 内容生成 │ │ 多模态   │         │
│  │ document │ │ database │ │ generator│ │multimodal│         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│  │ 缓存模块 │ │ 异步工具 │ │ 文本切分 │                      │
│  │  cache   │ │async_utils│ │ chunking │                      │
│  └──────────┘ └──────────┘ └──────────┘                      │
├─────────────────────────────────────────────────────────────────┤
│                        配置层                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ 环境变量 │ │ 应用配置 │ │ 教材目录 │ │ 模板配置 │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 数据流

```
文档上传 → 文本提取 → 图片提取 → OCR识别 → 文本切分 → 向量化 → Milvus存储
                                                                  ↓
                                                      Embedding缓存
                                                                  ↓
用户查询 → 缓存查询 → 向量化 → Milvus检索 → Rerank → LLM生成 ← 上下文
```

### 3.3 RAG流程详解

1. **文档处理流程**
   - 文档上传 → 格式识别 → 内容提取（文本+图片）
   - 图片 → Vision API → OCR文字 + 图片描述
   - 文本切分（RecursiveCharacterTextSplitter）
   - 向量化（BGE Embedding）
   - 存储到Milvus

2. **查询流程**
   - 用户输入问题
   - 查询向量化（带缓存）
   - Milvus向量检索（IVF_FLAT索引）
   - Rerank重排序
   - 构建上下文
   - LLM生成回答

---

## 4. 目录结构

```
GeoTeach_RAG/
│
├── config/                          # 配置层
│   ├── __init__.py                  # 包初始化
│   ├── .env                         # 环境变量（API密钥等）
│   ├── .env.example                 # 环境变量模板
│   ├── config.json                  # 应用配置
│   ├── settings.py                  # 配置加载模块
│   ├── catalog/                     # 教材目录
│   │   ├── junior/                  # 初中
│   │   │   └── pep.json             # 人教版
│   │   └── senior/                  # 高中
│   │       └── pep.json             # 人教版
│   └── templates/                   # 教学模板
│       ├── speech_draft.json        # 说课稿模板
│       ├── lecture_draft.json       # 讲课稿模板
│       ├── lesson_plan.json         # 教案模板
│       └── study_plan.json          # 学案模板
│
├── core/                            # 核心层
│   ├── __init__.py                  # 包初始化
│   ├── api.py                       # API适配器（Embedding/Rerank）
│   ├── async_utils.py               # 异步工具模块 [新增]
│   ├── cache.py                     # Embedding缓存模块 [新增]
│   ├── chunking.py                  # 文本切分模块
│   ├── database.py                  # 数据库操作（Milvus Lite）
│   ├── document.py                  # 文档处理模块
│   ├── generator.py                 # 内容生成器
│   ├── image_extractor.py           # 图片提取模块
│   ├── multimodal.py                # 多模态处理器
│   ├── ocr.py                       # OCR识别模块
│   ├── vision.py                    # 视觉模型模块
│   ├── maintenance.py               # 维护工具
│   ├── scheduler.py                 # 任务调度器
│   └── utils.py                     # 工具函数
│
├── servers/                         # 服务层
│   ├── __init__.py
│   ├── web.py                       # FastAPI Web服务器
│   └── mcp.py                       # MCP服务（Model Context Protocol）
│
├── frontend/                        # Web前端
│   ├── index.html                   # 主页面
│   ├── package.json                 # Node.js配置
│   ├── vite.config.js               # Vite配置
│   └── src/                         # 源代码
│       ├── api/index.js             # API接口定义
│       ├── views/                   # 页面组件
│       │   ├── Home.vue             # 首页
│       │   ├── Library.vue          # 资料库
│       │   ├── Generator.vue        # 内容生成
│       │   ├── QA.vue               # 智能问答
│       │   └── Settings.vue         # 设置
│       └── components/              # 公共组件
│
├── data/                            # 数据目录
│   ├── docs/                        # 通用文档
│   ├── textbook/                    # 课本资料
│   ├── curriculum/                  # 课程标准
│   ├── lesson_plan/                 # 教案库
│   ├── study_plan/                  # 学案库
│   ├── excellent_lesson/            # 优秀教案
│   ├── excellent_study/             # 优秀学案
│   ├── speech_draft/                # 说课稿
│   ├── lecture_draft/               # 讲课稿
│   ├── generated/                   # 生成内容
│   ├── images/                      # 提取的图片
│   ├── cache/                       # 缓存目录 [新增]
│   │   └── embedding_cache.json     # Embedding缓存
│   └── milvus.db                    # Milvus数据库
│
├── runtime/                         # 运行时
│   ├── logs/                        # 日志
│   └── state/                       # 状态
│
├── opencode.json                    # OpenCode配置 [新增]
├── .env                             # 环境变量
├── .gitignore                       # Git忽略
├── .python-version                  # Python版本
├── pyproject.toml                   # 项目配置
├── requirements.txt                 # 依赖列表
└── README.md                        # 项目说明
```

---

## 5. 配置说明

### 5.1 环境变量 (.env)

```bash
# ==================== API配置 ====================
# SiliconFlow API (用于Embedding、Rerank、LLM、Vision)
SILICONFLOW_API_KEY=your-api-key-here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1

# 小米mimo API配置（可选）
MIMO_API_KEY=your-mimo-key
MIMO_BASE_URL=https://platform.xiaomimimo.com/api/v1
MIMO_MODEL=mimo-v2.5pro

# Embedding模型
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# Rerank模型
RERANK_ENABLED=true
RERANK_MODEL=BAAI/bge-reranker-v2-m3

# LLM模型
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct

# Vision模型
VISION_MODEL=Qwen/Qwen2.5-VL-7B-Instruct

# ==================== 服务配置 ====================
WEB_HOST=127.0.0.1
WEB_PORT=9767

# MCP服务器配置
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=9766

# ==================== 数据目录 ====================
DOCS_DIR=data/docs
GENERATED_DIR=data/generated
MILVUS_DB_PATH=data/milvus.db

# ==================== 向量库配置 ====================
VECTOR_DB_COLLECTION=geoteach_docs
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K=4
```

### 5.2 应用配置 (config.json)

```json
{
  "collection": {"name": "geoteach_docs"},
  "chunk": {
    "templates": {
      "chinese": {
        "chunk_size": 500,
        "overlap": 50,
        "separators": ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
      },
      "academic": {
        "chunk_size": 1000,
        "overlap": 100
      }
    },
    "default_template": "chinese"
  },
  "vision": {
    "enabled": true,
    "ocr_engine": "vision_api",
    "table_recognition": true,
    "image_description": true
  },
  "retrieval": {
    "k": 5,
    "fetch_k": 15
  }
}
```

---

## 6. 核心模块

### 6.1 数据库操作 (core/database.py)

基于 Milvus Lite 的向量数据库操作，支持缓存优化。

```python
from core.database import DocumentDatabase

db = DocumentDatabase()

# 添加文档（自动缓存Embedding）
db.add(doc)

# 搜索文档（使用缓存的查询向量）
results = db.search("查询", n_results=5)

# 列出文档
documents = db.list_documents()

# 删除文档
db.delete("source_path")

# 获取统计信息（包含缓存统计）
stats = db.get_stats()
```

**优化特性：**
- IVF_FLAT索引，加速向量检索
- Embedding缓存，减少API调用
- 批量处理，提高吞吐量

### 6.2 Embedding缓存 (core/cache.py) [新增]

基于文件的Embedding缓存机制。

```python
from core.cache import get_embedding_cache

cache = get_embedding_cache()

# 获取缓存
embedding = cache.get("文本")

# 设置缓存
cache.set("文本", embedding)

# 批量操作
results, missed_indices = cache.get_batch(texts)
cache.set_batch(texts, embeddings)

# 获取统计
stats = cache.get_stats()
```

**特性：**
- 内存LRU缓存 + 磁盘持久化
- 批量操作接口
- 缓存命中率统计

### 6.3 异步工具 (core/async_utils.py) [新增]

异步处理优化工具。

```python
from core.async_utils import run_in_executor, batch_process, parallel_search

# 线程池执行
result = await run_in_executor(sync_function, arg1, arg2)

# 批量处理
results = await batch_process(items, process_func, batch_size=10)

# 并行搜索
results = await parallel_search(queries, search_func)
```

### 6.4 文档处理 (core/document.py)

支持多格式文档加载。

```python
from core.document import load_single_document

# 加载单个文档
docs = load_single_document("path/to/file.pptx")

# 使用多模态处理
docs = load_single_document("path/to/file.pptx", use_multimodal=True)
```

### 6.5 多模态处理器 (core/multimodal.py)

整合图片提取、OCR、视觉模型的多模态处理。

```python
from core.multimodal import MultimodalProcessor

processor = MultimodalProcessor(use_vision_api=True)
docs = processor.process_document("path/to/file.pptx")
```

### 6.6 内容生成器 (core/generator.py)

基于 LLM 的内容生成。

```python
from core.generator import ContentGenerator

generator = ContentGenerator(db)

# 生成说课稿
speech = generator.generate_speech_draft(
    topic="地球的运动",
    textbook_version="人教版",
    grade_level="高中",
    chapter="第一章"
)

# 智能问答
answer = generator.answer_question("什么是板块构造？")
```

---

## 7. 性能优化

### 7.1 Embedding缓存

**问题**：每次查询都需要调用Embedding API，增加延迟和成本。

**解决方案**：
- 查询向量缓存：相同查询直接返回缓存结果
- 文档向量缓存：批量添加时跳过已缓存文本
- 双层缓存：内存LRU + 磁盘持久化

**效果**：
- 首次查询：~500ms（API调用）
- 缓存命中：~5ms（内存查询）
- 重复文档导入：跳过已处理的文本块

### 7.2 向量索引优化

**索引类型**：IVF_FLAT
- 适合中小规模数据（<100万向量）
- 平衡查询速度和精度

**参数配置**：
```python
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "COSINE",
    "params": {"nlist": 1024}
}

search_params = {
    "metric_type": "COSINE",
    "params": {"nprobe": 16}
}
```

### 7.3 批量处理

**文档导入**：
- 批量获取Embedding
- 只对未缓存文本调用API
- 批量插入Milvus

**查询优化**：
- 并行搜索支持
- 异步任务队列

---

## 8. API接口

### 8.1 系统API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/system/health` | GET | 健康检查 |
| `/api/system/status` | GET | 系统状态 |

### 8.2 文档管理API

| 端点 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/api/documents` | GET | category? | 获取文档列表 |
| `/api/documents/import` | POST | file, category, use_multimodal, chunk_size, chunk_overlap | 导入文档 |
| `/api/documents/import-all` | POST | use_multimodal | 批量导入 |
| `/api/documents/delete` | POST | source | 删除文档 |
| `/api/documents/stats` | GET | - | 文档统计 |

### 8.3 教材目录API

| 端点 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/api/catalog/levels` | GET | - | 获取学段列表 |
| `/api/catalog/grades` | GET | level | 获取年级列表 |
| `/api/catalog/chapters` | GET | level, grade, semester | 获取章节列表 |

### 8.4 内容生成API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/generate/speech-draft` | POST | 生成说课稿 |
| `/api/generate/lecture-draft` | POST | 生成讲课稿 |
| `/api/generate/lesson-plan` | POST | 生成教案 |
| `/api/generate/study-plan` | POST | 生成学案 |

**请求体：**
```json
{
  "topic": "地球的运动",
  "textbook_version": "人教版",
  "grade_level": "高中高二",
  "chapter": "第一章 地球的运动",
  "class_hours": "1课时"
}
```

### 8.5 搜索和问答API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/search` | POST | 搜索文档 |
| `/api/qa` | POST | 智能问答 |

---

## 9. MCP服务

### 9.1 概述

MCP（Model Context Protocol）服务允许AI助手（如OpenCode）通过标准协议访问知识库。

### 9.2 启动MCP服务

```bash
python -m servers.mcp
```

服务运行在 `http://127.0.0.1:9766`

### 9.3 MCP配置

**OpenCode配置 (opencode.json)**：
```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "geoteach": {
      "type": "remote",
      "url": "http://127.0.0.1:9766/mcp",
      "enabled": true
    }
  }
}
```

### 9.4 MCP工具

| 工具名 | 说明 |
|--------|------|
| `search_knowledge_base` | 搜索本地知识库 |

**使用场景**：
- 用户询问的信息可能属于个人私有数据
- 问题涉及特定人物、地点或事件
- 需要从本地文档中查找事实依据

### 9.5 API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/mcp` | POST | MCP JSON-RPC端点 |

---

## 10. 部署指南

### 10.1 环境要求

- Python 3.11+
- pip 或 uv
- 4GB+ 内存
- 网络连接（用于API调用）

### 10.2 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd GeoTeach_RAG

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp config/.env.example config/.env
# 编辑 config/.env，填入API密钥

# 5. 启动Web服务
python -m servers.web

# 6. 启动MCP服务（可选）
python -m servers.mcp
```

### 10.3 访问应用

- Web界面：http://localhost:9767
- MCP服务：http://localhost:9766

---

## 附录

### A. 依赖列表

```
# 核心依赖
langchain>=0.2.0
langchain-openai>=0.1.0
langchain-community>=0.2.0
langchain-text-splitters>=0.2.0
pymilvus>=2.4.0
milvus-lite>=2.4.0

# 文档处理
pypdf>=4.0.0
docx2txt>=0.8
python-docx>=1.2.0
python-pptx>=0.6.21
PyMuPDF>=1.23.0

# 图像处理
Pillow>=10.0.0

# Web框架
fastapi>=0.100.0
uvicorn>=0.23.0
python-multipart>=0.0.6

# 配置和工具
python-dotenv>=1.0.0
pydantic>=2.0.0
requests>=2.31.0
httpx>=0.24.0
rich>=13.0.0
```

### B. 更新日志

**v1.2.0 (当前版本)**
- 新增 Embedding 缓存机制
- 新增 异步处理优化
- 新增 MCP 服务支持
- 优化 Milvus 索引参数（IVF_FLAT）
- 优化 批量处理性能
- 修复 文档上传分类问题
- 修复 删除功能实现

**v1.1.0**
- 新增 PPT 支持
- 新增多模态处理（图片识别、OCR、表格识别）
- 新增 Vision API 集成
- 优化文档处理流程
- 精简依赖（移除PaddleOCR本地依赖）

**v1.0.0**
- 初始版本
- 支持 PDF、DOCX、TXT、MD 格式
- 基础 RAG 功能
- 教材目录管理
- 内容生成功能

### C. 许可证

MIT License
