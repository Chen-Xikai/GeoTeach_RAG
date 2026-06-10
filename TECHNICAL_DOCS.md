# GeoTeach RAG 完整技术文档

> 版本：v1.4.0 | 更新日期：2025-06-10

---

## 一、项目概述

| 属性 | 值 |
|------|-----|
| 名称 | GeoTeach RAG |
| 版本 | v1.4.0 |
| 用途 | 基于 RAG 技术的地理教学 AI 助手 |
| 技术栈 | FastAPI + Vue 3 + Milvus Lite + SiliconFlow API |
| 向量模型 | BAAI/bge-large-zh-v1.5 (1024维) |
| LLM | Qwen2.5-7B-Instruct |
| Vision | Qwen2.5-VL-7B-Instruct |
| Rerank | BAAI/bge-reranker-v2-m3 |

---

## 二、系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Element Plus)            │
│  Home │ Library │ Generator │ QA │ Settings │ Login          │
│  ├─ api/index.js (axios + interceptors)                      │
│  ├─ router/index.js (hash history, auth guard)               │
│  └─ views/*.vue (10 pages)                                   │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP / WebSocket
┌────────────────────────┴─────────────────────────────────────┐
│                    Backend (FastAPI + Uvicorn)                 │
│  servers/web.py (30+ endpoints)                              │
│  servers/mcp.py (MCP JSON-RPC)                               │
│  servers/embedding.py (OpenAI-compatible)                    │
│  servers/rerank.py (Rerank service)                          │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────────┐
│                    Core Modules                                │
│  agent.py ─→ generator.py ─→ database.py ─→ Milvus Lite     │
│      │            │                │                          │
│      ↓            ↓                ↓                          │
│  evaluator.py  api.py(Rerank)  cache.py(EmbeddingCache)     │
│  chunking.py   ocr.py(Vision)  multimodal.py                │
│  image_extractor.py            web_crawler.py                │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────────┐
│                    External Services                           │
│  SiliconFlow API (Embedding + LLM + Rerank + Vision)         │
│  Milvus Lite (data/milvus.db)                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 三、核心模块详解 (core/)

### 3.1 agent.py — 智能 Agent

**文件路径：** `core/agent.py` (211行)

实现自主评估、多轮检索决策、Query 改写等智能行为。

| 方法 | 签名 | 功能 |
|------|------|------|
| `__init__` | `(generator)` | 初始化 Agent，绑定 ContentGenerator |
| `rewrite_query` | `(original_query, history) → List[str]` | 根据对话历史改写 query，生成 1-3 个检索查询 |
| `evaluate_retrieval` | `(query, results) → dict` | 评估检索质量（最高分、平均分、多样性） |
| `evaluate_answer` | `(query, context, answer) → dict` | LLM-as-judge 评估回答质量（忠实度、相关性、完整性） |
| `compress_history` | `(history, max_messages) → list` | 压缩对话历史，保留最近 N 条 |
| `should_retrieve_more` | `(retrieval_result, round_num) → bool` | 决策是否需要更多检索 |
| `should_regenerate` | `(answer_result, round_num) → bool` | 决策是否需要重新生成回答 |

**配置参数：**
- `max_retrieval_rounds = 2` — 最大检索轮数
- `retrieval_threshold = 0.5` — 检索质量阈值
- `answer_threshold = 0.6` — 回答质量阈值

---

### 3.2 database.py — 向量数据库

**文件路径：** `core/database.py` (923行)

Milvus Lite 向量数据库操作，支持 CRUD、混合搜索、同步重建。

| 方法 | 签名 | 功能 |
|------|------|------|
| `__init__` | `(collection_name, db_path)` | 初始化 Milvus 客户端、缓存、配置 |
| `add` | `(doc, chunk_cfg, source_type) → List[str]` | 添加文档（切片→embedding→插入） |
| `delete` | `(source)` | 删除文档（按 source 路径） |
| `update` | `(doc, chunk_cfg, source_type) → List[str]` | 更新文档 |
| `search` | `(query, n_results, category) → List[dict]` | 向量相似度搜索 |
| `hybrid_search` | `(query, n_results, category, fetch_k) → List[dict]` | 混合搜索（向量 + BM25 + RRF 融合） |
| `_bm25_search` | `(query, n_results, category) → List[dict]` | BM25 关键词搜索 |
| `_rrf_fusion` | `(vector_results, bm25_results, k) → List[dict]` | Reciprocal Rank Fusion 融合 |
| `list_documents` | `(category) → List[dict]` | 列出文档（按 source 去重，含切片数） |
| `get_document_info` | `(source) → dict` | 获取文档元数据 |
| `get_document_chunks` | `(source) → List[dict]` | 获取文档所有切片内容 |
| `update_file_type` | `(source, file_type) → bool` | 更新文档文件类型 |
| `sync` | `(documents, chunk_cfg, on_progress) → dict` | 增量同步 |
| `rebuild` | `(documents, chunk_cfg, on_progress) → int` | 全量重建（影子集合策略） |
| `count` | `() → int` | 获取切片总数 |
| `get_stats` | `() → dict` | 获取数据库统计信息 |
| `check_orphan_records` | `(dirs) → List[str]` | 检查孤立记录 |
| `clean_orphan_records` | `(dirs) → int` | 清理孤立记录 |

**Milvus Schema：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INT64 | 主键 |
| `vector` | FLOAT_VECTOR(1024) | Embedding 向量 |
| `source` | VARCHAR | 文件路径 |
| `category` | VARCHAR | 分类 |
| `file_type` | VARCHAR | 文件类型 |
| `content_hash` | VARCHAR | 内容哈希 |
| `content` | VARCHAR | 切片文本 |

**索引配置：**
- 类型：IVF_FLAT
- 度量：COSINE
- nlist：1024
- nprobe：16

---

### 3.3 generator.py — 内容生成器

**文件路径：** `core/generator.py` (487行)

提供教学内容生成和智能问答功能。

| 方法 | 签名 | 功能 |
|------|------|------|
| `__init__` | `(db)` | 初始化生成器，加载模板、API 密钥 |
| `_call_llm` | `(prompt) → str` | 单轮 LLM 调用 |
| `_call_llm_with_messages` | `(messages) → str` | 多轮 LLM 调用 |
| `_retrieve_context` | `(query, category, k) → tuple` | 检索 + Rerank + 格式化上下文 |
| `generate_speech_draft` | `(topic, ...) → dict` | 生成说课稿 |
| `generate_lecture_draft` | `(topic, ...) → dict` | 生成讲课稿 |
| `generate_lesson_plan` | `(topic, ...) → dict` | 生成教案 |
| `generate_study_plan` | `(topic, ...) → dict` | 生成学案 |
| `answer_question_with_agent` | `(question, mode, history) → dict` | Agent 模式智能问答 |

**内容生成模板（4种）：**

| 模板 | 结构 |
|------|------|
| 说课稿 | 开场白→设计理念→课标分析→学情分析→教学目标→重难点→方法→过程→结束语 |
| 讲课稿 | 开场白→情境导入→探究环节→认知冲突→课堂总结→作业→板书设计 |
| 教案 | 基本信息→课标分析→设计理念→内容分析→学情→目标→重难点→教法学法→过程→评价 |
| 学案 | 情境启思→实践活动→初步探索→情境再现→深入学习→作业→预习引导 |

---

### 3.4 multimodal.py — 文档处理

**文件路径：** `core/multimodal.py` (384行)

整合文档读取、文本提取功能。

| 函数/类 | 签名 | 功能 |
|---------|------|------|
| `read_file` | `(filepath) → str` | 按扩展名读取文件内容 |
| `_read_pptx` | `(filepath) → str` | 读取 PPT 文本 + 表格 |
| `_read_pdf` | `(filepath) → str` | 读取 PDF 文本 |
| `_read_docx` | `(filepath) → str` | 读取 DOCX 文本 + 表格 |
| `_read_text` | `(filepath) → str` | 读取 TXT/MD（编码回退） |
| `_clean_text` | `(text) → str` | 清理无效 Unicode 字符 |
| `load_single_document` | `(filepath, use_multimodal) → List[dict]` | 加载单个文档 |
| `load_all_documents` | `(*dirs, use_multimodal) → List[dict]` | 加载所有目录下的文档 |
| `MultimodalProcessor.process_document` | `(file_path) → List[dict]` | 多模态处理（文本 + 图片 + OCR） |

**支持格式：** `.pdf`, `.docx`, `.pptx`, `.txt`, `.md`

---

### 3.5 ocr.py — 视觉处理

**文件路径：** `core/ocr.py` (444行)

使用视觉模型进行图片理解、OCR、表格识别、地理信息提取。

| 方法 | 签名 | 功能 |
|------|------|------|
| `extract_text` | `(image_path) → str` | OCR 文字识别 |
| `describe_image` | `(image_path) → str` | 图片描述生成 |
| `analyze_table` | `(image_path) → dict` | 表格识别 |
| `extract_tables` | `(image_path) → List[List[str]]` | 提取表格数据 |
| `extract_geographic_info` | `(image_path) → dict` | 地理信息提取 |

---

### 3.6 evaluator.py — 评测模块

**文件路径：** `core/evaluator.py` (270行)

RAGAS 检索评测和切片质量评估。

| 方法 | 签名 | 功能 |
|------|------|------|
| `evaluate_retrieval_quality` | `(query, results, ground_truth) → dict` | 检索质量评估（precision, recall, MRR） |
| `evaluate_answer_quality` | `(query, answer, contexts) → dict` | 回答质量评估（faithfulness, relevance, completeness） |
| `evaluate_chunk_quality` | `(chunks) → dict` | 切片质量评估（长度统计、分布） |
| `ChunkOptimizer.compare_strategies` | `(text, strategies) → dict` | 切片策略对比 |

---

### 3.7 其他模块

| 模块 | 文件 | 功能 |
|------|------|------|
| `api.py` | 85行 | RerankAPI 适配器 |
| `cache.py` | 138行 | EmbeddingCache（内存 LRU + JSON 磁盘） |
| `chunking.py` | 105行 | RecursiveCharacterTextSplitter 切片 |
| `image_extractor.py` | 165行 | 从 PPT/PDF/DOCX 提取图片 |
| `web_crawler.py` | 108行 | 网页爬取 + 内容清理 |
| `utils.py` | 11行 | MD5 哈希工具 |

---

## 七、服务器模块 (servers/)

### 7.1 web.py — Web API（30+ 端点）

**文件路径：** `servers/web.py` (1343行)

#### 认证 API
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/check` | 检查是否需要密码 |

#### 系统 API
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/system/health` | 健康检查 |
| GET | `/api/system/status` | 系统状态 |

#### 配置 API
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/config` | 获取配置 |
| PUT | `/api/config` | 更新配置 |
| GET | `/api/config/templates` | 获取模板 |
| GET | `/api/config/chunk` | 获取切分配置 |
| PUT | `/api/config/chunk` | 更新切分配置 |

#### 文档管理 API
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/documents` | 文档列表 |
| POST | `/api/documents/upload` | 上传文件 |
| POST | `/api/documents/import` | 导入到向量库 |
| POST | `/api/documents/import-file` | 单文件导入 |
| POST | `/api/documents/batch-import` | 批量导入 |
| POST | `/api/documents/import-all` | 导入所有本地文档 |
| DELETE | `/api/documents/{path}` | 删除文档 |
| POST | `/api/documents/batch-delete` | 批量删除 |
| POST | `/api/documents/delete-all` | 删除所有 |
| POST | `/api/documents/update` | 更新文档 |
| PUT | `/api/documents/update-file-type` | 更新文件类型 |
| POST | `/api/documents/sync` | 增量同步 |
| POST | `/api/documents/rebuild` | 全量重建 |
| POST | `/api/documents/clean-orphans` | 清理孤立记录 |
| GET | `/api/documents/orphans` | 检查孤立记录 |
| GET | `/api/documents/stats` | 文档统计 |
| GET | `/api/documents/detail` | 文档详情 |
| GET | `/api/documents/chunks` | 文档切片 |
| GET | `/api/documents/list-files` | 列出文件 |
| GET | `/api/documents/pending` | 待审核文件 |
| POST | `/api/documents/approve/{id}` | 批准文件 |
| POST | `/api/documents/reject/{id}` | 拒绝文件 |
| POST | `/api/documents/crawl-web` | 网页爬取入库 |

#### 教材目录 API
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/catalog/levels` | 学段列表 |
| GET | `/api/catalog/grades` | 年级列表 |
| GET | `/api/catalog/chapters` | 章节列表 |

#### 内容生成 API
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/generate/speech-draft` | 生成说课稿 |
| POST | `/api/generate/lecture-draft` | 生成讲课稿 |
| POST | `/api/generate/lesson-plan` | 生成教案 |
| POST | `/api/generate/study-plan` | 生成学案 |

#### 搜索和问答 API
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/search` | 向量搜索 |
| POST | `/api/qa` | 智能问答（Agent 模式） |

#### 评测 API
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/evaluate/retrieval` | 检索质量评估 |
| POST | `/api/evaluate/answer` | 回答质量评估 |
| POST | `/api/evaluate/chunks` | 切片质量评估 |

#### WebSocket
| 路径 | 功能 |
|------|------|
| `/ws` | 实时进度推送 |

---

### 7.2 mcp.py — MCP 服务器

**文件路径：** `servers/mcp.py` (214行)

| 端点 | 功能 |
|------|------|
| GET `/health` | 健康检查 |
| POST `/mcp` | MCP JSON-RPC 端点 |

---

### 7.3 embedding.py — Embedding 服务

**文件路径：** `servers/embedding.py` (221行)

| 端点 | 功能 |
|------|------|
| GET `/v1/models` | 模型列表 |
| GET `/health` | 健康检查 |
| POST `/v1/embeddings` | 创建 embedding |

---

### 7.4 rerank.py — Rerank 服务

**文件路径：** `servers/rerank.py` (168行)

| 端点 | 功能 |
|------|------|
| GET `/health` | 健康检查 |
| POST `/rerank` | 文档重排 |
| POST `/v1/rerank` | 文档重排（OpenAI 兼容） |

---

## 八、前端模块 (frontend/)

### 8.1 页面组件

| 组件 | 路由 | 功能 |
|------|------|------|
| `Home.vue` | `/` | 首页：统计卡片、快捷操作、系统信息 |
| `Library.vue` | `/library` | 资料库：文件上传、网页爬取、文档列表、详情查看、切片预览 |
| `Generator.vue` | `/generator` | 内容生成：教材目录选择、4种模板、Markdown渲染 |
| `QA.vue` | `/qa` | 智能问答：教师/学生模式、会话管理、多轮对话、导出 |
| `Settings.vue` | `/settings` | 系统设置：API配置、检索配置、切分配置、维护工具 |
| `Login.vue` | `/login` | 登录页面 |
| `Documents.vue` | `/documents` | 文档管理 |
| `Search.vue` | `/search` | 搜索页面 |
| `Config.vue` | `/config` | 配置页面 |
| `Services.vue` | `/services` | 服务管理 |

### 8.2 API 客户端 (api/index.js)

| API 对象 | 方法 | 功能 |
|----------|------|------|
| `systemApi` | `health()`, `status()` | 系统状态 |
| `authApi` | `login(password)`, `check()` | 认证 |
| `configApi` | `get()`, `update()`, `templates()`, `getChunk()`, `updateChunk()` | 配置 |
| `catalogApi` | `getLevels()`, `getGrades()`, `getChapters()` | 教材目录 |
| `documentsApi` | `list()`, `upload()`, `importFiles()`, `batchImport()`, `delete()`, `update()`, `sync()`, `rebuild()`, `cleanOrphans()`, `orphans()`, `stats()`, `detail()`, `chunks()`, `pending()`, `approve()`, `reject()`, `importFile()`, `updateFileType()`, `crawlWeb()` | 文档管理 |
| `searchApi` | `search(query, nResults, category)` | 搜索 |
| `generateApi` | `speechDraft()`, `lectureDraft()`, `lessonPlan()`, `studyPlan()` | 内容生成 |
| `qaApi` | `ask(question, mode, history)` | 智能问答 |
| `servicesApi` | `start()`, `stop()` | 服务管理 |
| `createWebSocket` | `(onMessage) → WebSocket` | WebSocket 连接 |

---

## 九、数据流

### 9.1 文档入库流

```
用户上传 → POST /api/documents/import-file
  ↓
保存到 data/docs/
  ↓
read_file() → 按格式读取文本
  ↓
chunk_single_document() → RecursiveCharacterTextSplitter 切分
  ↓
EmbeddingCache.get_batch() → 命中/未命中
  ↓
embed_documents() → SiliconFlow API 生成向量
  ↓
EmbeddingCache.set_batch() → 缓存
  ↓
Milvus client.insert() → 存入向量库
```

### 9.2 智能问答流（Agent 模式）

```
用户输入问题
  ↓
Agent.rewrite_query() → 改写 query（1-3个）
  ↓
database.hybrid_search() → 向量搜索 + BM25 + RRF 融合
  ↓
Agent.evaluate_retrieval() → 评估检索质量
  ├─ 不够 → 重新改写 query，再次检索
  └─ 足够 → 继续
  ↓
构建 messages（system + history + context）
  ↓
LLM 生成回答
  ↓
Agent.evaluate_answer() → 评估回答质量
  ├─ 不够 → 重新检索 + 重新生成
  └─ 足够 → 返回给用户
```

### 9.3 混合搜索流

```
Query
  ├─→ 向量搜索（fetch_k=15）→ COSINE 相似度
  └─→ BM25 搜索（关键词匹配）
       ↓
  RRF 融合：score = Σ 1/(k + rank_i)
       ↓
  返回 top-k 结果
```

---

## 十、配置参数

### 10.1 环境变量 (config/.env)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SILICONFLOW_API_KEY` | API 密钥 | 必填 |
| `SILICONFLOW_BASE_URL` | API 基础 URL | `https://api.siliconflow.cn/v1` |
| `EMBEDDING_MODEL` | Embedding 模型 | `BAAI/bge-large-zh-v1.5` |
| `LLM_MODEL` | LLM 模型 | `Qwen/Qwen2.5-7B-Instruct` |
| `VISION_MODEL` | Vision 模型 | `Qwen/Qwen2.5-VL-7B-Instruct` |
| `RERANK_ENABLED` | 启用 Rerank | `true` |
| `RERANK_MODEL` | Rerank 模型 | `BAAI/bge-reranker-v2-m3` |
| `WEB_HOST` | 监听地址 | `127.0.0.1` |
| `WEB_PORT` | 监听端口 | `9767` |
| `ACCESS_PASSWORD` | 访问密码 | `123` |
| `ADMIN_PASSWORD` | 管理员密码 | `123` |
| `ALLOWED_ORIGINS` | CORS 来源 | `*` |
| `MILVUS_DB_PATH` | Milvus 路径 | `data/milvus.db` |
| `RETRIEVAL_K` | 检索数量 | `5` |
| `RETRIEVAL_FETCH_K` | 过度检索数量 | `15` |
| `CHUNK_SIZE` | 切片大小 | `500` |
| `CHUNK_OVERLAP` | 重叠长度 | `50` |
| `DOCS_DIR` | 文档目录 | `data/docs` |
| `GENERATED_DIR` | 生成目录 | `data/generated` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

### 10.2 文件类型选项

| 值 | 标签 |
|------|------|
| `teaching_design` | 教学设计 |
| `study_guide` | 导学案 |
| `textbook` | 课本 |
| `curriculum` | 课程标准 |
| `reference_paper` | 参考论文 |
| `web_page` | 网页资料 |
| `other` | 其他资料 |

---

## 十一、目录结构

```
GeoTeach_RAG/
├── config/
│   ├── .env                    # 环境变量
│   ├── .env.example            # 环境变量模板
│   ├── config.json             # 应用配置
│   ├── settings.py             # 配置加载模块
│   ├── version.py              # 版本信息
│   ├── catalog/                # 教材目录 JSON
│   └── templates/              # 内容生成模板 JSON
├── core/
│   ├── agent.py                # 智能 Agent
│   ├── api.py                  # Rerank API
│   ├── cache.py                # Embedding 缓存
│   ├── chunking.py             # 文本切分
│   ├── database.py             # Milvus 数据库
│   ├── evaluator.py            # RAGAS 评测
│   ├── generator.py            # 内容生成器
│   ├── image_extractor.py      # 图片提取
│   ├── multimodal.py           # 文档处理
│   ├── ocr.py                  # 视觉处理
│   ├── utils.py                # 工具函数
│   └── web_crawler.py          # 网页爬取
├── servers/
│   ├── web.py                  # Web API 服务器
│   ├── mcp.py                  # MCP 服务器
│   ├── embedding.py            # Embedding 服务
│   └── rerank.py               # Rerank 服务
├── frontend/
│   ├── src/
│   │   ├── api/index.js        # API 客户端
│   │   ├── router/index.js     # 路由配置
│   │   ├── views/*.vue         # 页面组件
│   │   ├── components/*.vue    # 通用组件
│   │   ├── App.vue             # 根组件
│   │   ├── main.js             # 入口文件
│   │   └── styles/main.css     # 全局样式
│   ├── dist/                   # 构建产物
│   └── package.json            # 依赖配置
├── data/
│   ├── docs/                   # 文档存储
│   ├── cache/                  # Embedding 缓存
│   ├── generated/              # 生成内容
│   ├── images/                 # 提取的图片
│   └── milvus.db               # Milvus 数据库
├── runtime/
│   ├── logs/                   # 日志文件
│   └── state/                  # 运行时状态
├── start.py                    # 启动脚本
├── launcher.py                 # GUI 启动器
├── requirements.txt            # Python 依赖
├── Dockerfile                  # Docker 构建文件
├── README.md                   # 项目说明
├── DEPLOY.md                   # 部署指南
└── TECHNICAL_DOCS.md           # 技术文档（本文件）
```

---

## 十二、启动方式

```bash
# 本地启动
cd C:\Users\ASUS\Desktop\AI_Tey\RAG\GeoTeach_RAG
python start.py

# 访问 http://127.0.0.1:9767
# 密码: 123
```

---

## 十三、更新日志

### v1.4.0 (当前版本)
- 新增智能 Agent（自主评估、Query改写、多轮检索决策）
- 新增混合搜索（向量 + BM25 + RRF 融合）
- 新增 RAGAS 评测模块
- 新增切片优化验证
- 新增网页爬取功能
- 新增文件类型标签（7类）
- 新增教师端/学生端模式切换
- 新增会话管理和聊天记录持久化
- 新增多轮对话上下文
- 修复文件上传 Content-Type boundary 问题
- 修复 Milvus 路径转义问题
- 修复切片数显示不一致
- 修复登录跳转和路由问题
- 移除 Railway 部署，改为本地/Docker 部署
- 全面代码审计，删除死代码

### v1.3.0
- 新增 Embedding 缓存机制
- 新增 MCP 服务支持
- 新增异步处理优化
- 优化 Milvus 索引参数

### v1.2.0
- 迁移到 Milvus Lite 向量数据库
- 优化文档处理流程

### v1.1.0
- 新增 PPT 支持
- 新增多模态处理
- 新增 Vision API 集成

### v1.0.0
- 初始版本
