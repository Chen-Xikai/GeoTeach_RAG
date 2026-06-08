# GeoTeach AI Agent - 地理教学AI助手

基于 RAG（检索增强生成）技术的地理教学 AI 助手系统，支持多模态文档处理、AI内容生成、智能问答等功能。

## 功能特点

### 📚 资料管理
- 支持 PPT、PDF、DOCX、TXT、Markdown 格式
- 按教材目录分类管理（人教版初中+高中）
- 多模态处理（图片识别、OCR、表格提取）

### 🛠️ AI内容生成
- **说课稿** - 基于参考资料自动生成专业说课稿
- **讲课稿** - 生成详细的讲课稿
- **教案** - 生成规范的教案
- **学案** - 生成情境化学案

### ❓ 智能问答
- 解答地理教学相关问题
- 基于知识库提供专业建议

### 📖 教材目录
- 人教版初中地理（七年级、八年级）
- 人教版高中地理（必修、选择性必修）

### 🔌 MCP集成
- 支持 Model Context Protocol
- 可与 OpenCode 等AI助手集成
- 知识库智能检索

### ⚡ 性能优化
- Embedding缓存机制，减少API调用
- Milvus IVF_FLAT索引，加速向量检索
- 批量处理，提高吞吐量

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `config/.env.example` 为 `config/.env`，填入 API 密钥：

```bash
cp config/.env.example config/.env
```

### 3. 启动Web服务

```bash
python -m servers.web
```

### 4. 启动MCP服务（可选）

```bash
python -m servers.mcp
```

### 5. 访问应用

- Web界面：http://localhost:9767
- MCP服务：http://localhost:9766

## 技术栈

| 组件 | 技术 |
|------|------|
| **前端** | Vue 3 + Element Plus + Vite |
| **后端** | Python 3.11+, FastAPI, Uvicorn |
| **向量数据库** | Milvus Lite |
| **Embedding** | BGE-large-zh-v1.5 (1024维) |
| **LLM** | Qwen2.5-7B-Instruct |
| **Vision** | Qwen2.5-VL-7B-Instruct |
| **协议** | MCP (Model Context Protocol) |

## 项目结构

```
GeoTeach_RAG/
├── config/          # 配置层
├── core/            # 核心层
│   ├── database.py  # Milvus数据库操作
│   ├── cache.py     # Embedding缓存
│   └── async_utils.py # 异步工具
├── servers/         # 服务层
│   ├── web.py       # Web API
│   └── mcp.py       # MCP服务
├── frontend/        # 前端（Vue 3）
├── data/            # 数据目录
└── runtime/         # 运行时
```

## 文档

- [技术文档](TECHNICAL_DOCS.md) - 详细的系统架构和API文档
- [部署指南](DEPLOY.md) - Railway部署和文件同步
- [教材目录](config/catalog/) - 人教版地理教材目录

## 更新日志

### v1.4.0 (当前版本)
- 新增 Embedding 缓存机制
- 新增 MCP 服务支持
- 新增 异步处理优化
- 优化 Milvus 索引参数
- 修复 文档上传分类问题
- 修复 删除功能实现

### v1.2.0
- 迁移到 Milvus Lite 向量数据库
- 优化文档处理流程

### v1.1.0
- 新增 PPT 支持
- 新增多模态处理
- 新增 Vision API 集成

### v1.0.0
- 初始版本

## 许可证

MIT License
