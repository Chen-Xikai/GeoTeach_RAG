# GeoTeach RAG 地理教学助手

基于RAG（检索增强生成）的地理教学问答系统，使用Milvus向量数据库、LangChain框架和Streamlit界面。

## 功能特点

- 支持多种文档格式：PDF、DOCX、TXT、Markdown
- 使用Jina Embeddings进行文本向量化（免费API）
- 使用Milvus作为向量数据库（本地Docker部署）
- 支持多轮对话，保留历史上下文
- 显示引用的文档片段，方便验证
- 中文界面，操作简单

## 快速开始

### 1. 启动Milvus

```bash
docker-compose up -d
```

等待Milvus启动完成（约1-2分钟），可以通过以下命令检查状态：

```bash
docker-compose ps
```

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

编辑 `.env` 文件，填入你的API密钥：

```env
# Jina Embeddings API（免费注册：https://jina.ai/）
JINA_API_KEY=your_jina_api_key_here

# mimo-v2.5pro LLM API
MIMO_API_KEY=your_mimo_api_key_here
MIMO_BASE_URL=your_mimo_base_url_here
```

### 4. 启动Web界面

```bash
streamlit run app.py
```

浏览器会自动打开 http://localhost:8501

## 使用说明

### 上传文档

1. 在左侧边栏点击"上传文档"
2. 选择要上传的文件（支持PDF、DOCX、TXT、Markdown）
3. 点击"处理上传的文档"按钮
4. 等待处理完成

### 开始对话

1. 确保已点击"初始化RAG系统"按钮
2. 在底部输入框输入你的问题
3. 系统会自动检索相关文档并生成回答
4. 点击"📎 查看引用的文档片段"可以查看引用来源

### 知识库管理

- **刷新状态**：查看当前知识库中的文档片段数量
- **清空知识库**：删除所有已上传的文档（谨慎操作）

## 项目结构

```
GeoTeach_RAG/
├── docker-compose.yml      # Milvus部署配置
├── requirements.txt        # Python依赖
├── .env                    # 环境变量配置
├── config.py              # 配置管理
├── document_processor.py  # 文档处理模块
├── vector_store.py        # 向量库操作模块
├── rag_chain.py           # RAG检索链模块
├── app.py                 # Streamlit Web界面
└── data/                  # 文档存放目录
    ├── pdf/
    ├── docx/
    └── txt/
```

## 常见问题

### Q: Milvus启动失败怎么办？

A: 确保Docker已安装并运行，检查端口19530和9091是否被占用。

### Q: Jina Embeddings如何获取API Key？

A: 访问 https://jina.ai/ 注册账号，免费额度为每月100万Token。

### Q: 支持哪些文档格式？

A: 目前支持PDF、DOCX、TXT和Markdown格式。

### Q: 如何提高检索效果？

A: 
- 确保文档内容质量高、格式规范
- 调整 `.env` 中的 `CHUNK_SIZE` 和 `CHUNK_OVERLAP` 参数
- 增加 `TOP_K` 值以获取更多相关文档

## 技术栈

- **向量数据库**: Milvus 2.4
- **Embedding**: Jina Embeddings v3
- **LLM**: mimo-v2.5pro
- **框架**: LangChain
- **界面**: Streamlit

## 许可证

MIT License
