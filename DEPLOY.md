# GeoTeach RAG 部署指南

## 目录

1. [Railway部署](#1-railway部署)
2. [文件审核流程](#2-文件审核流程)
3. [环境变量配置](#3-环境变量配置)
4. [安全说明](#4-安全说明)

---

## 1. Railway部署

### 1.1 准备工作

1. 注册 [Railway](https://railway.app) 账号
2. Fork 项目到你的 GitHub 账号

### 1.2 部署步骤

1. 登录 Railway
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择你 fork 的仓库
4. Railway 会自动检测 Dockerfile 并部署

### 1.3 配置环境变量

在 Railway 项目设置中添加环境变量：

```
SILICONFLOW_API_KEY=your-api-key
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
VISION_MODEL=Qwen/Qwen2.5-VL-7B-Instruct
WEB_HOST=0.0.0.0
WEB_PORT=${{PORT}}
```

### 1.4 配置域名

Railway 会自动提供一个 `*.up.railway.app` 域名，也可以配置自定义域名。

---

## 2. 文件审核流程

### 2.1 安全机制

为了防止恶意文件（病毒、木马等）被直接入库，系统采用**人工审核机制**：

1. 用户上传文件 → 进入 `_pending` 待审核目录
2. 管理员审核文件 → 批准或拒绝
3. 批准后文件才会入库并被处理

### 2.2 审核方式

#### 方式一：Web界面审核

1. 访问 Web 界面
2. 点击"资料库"
3. 切换到"待审核"标签页
4. 查看文件信息，点击"批准"或"拒绝"

#### 方式二：命令行审核脚本

```bash
# 列出待审核文件
python review_files.py --server https://your-app.up.railway.app --list

# 下载文件到本地审核
python review_files.py --server https://your-app.up.railway.app --download <pending_id>

# 批准文件
python review_files.py --server https://your-app.up.railway.app --approve <pending_id>

# 拒绝文件
python review_files.py --server https://your-app.up.railway.app --reject <pending_id>
```

### 2.3 审核建议

1. **检查文件类型**：确认是 PDF、DOCX、TXT、MD、PPTX
2. **检查文件名**：避免可疑命名（如 `.exe.pdf`）
3. **检查文件大小**：异常大的文件需要警惕
4. **本地扫描**：下载后用杀毒软件扫描
5. **内容预览**：确认内容是地理教学资料

---

## 3. 环境变量配置

### 3.1 必需的环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `SILICONFLOW_API_KEY` | SiliconFlow API密钥 | `sk-xxx` |
| `WEB_HOST` | 监听地址 | `0.0.0.0` |
| `WEB_PORT` | 监听端口 | `${{PORT}}` |

### 3.2 可选的环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SILICONFLOW_BASE_URL` | API基础URL | `https://api.siliconflow.cn/v1` |
| `EMBEDDING_MODEL` | Embedding模型 | `BAAI/bge-large-zh-v1.5` |
| `LLM_MODEL` | LLM模型 | `Qwen/Qwen2.5-7B-Instruct` |
| `VISION_MODEL` | Vision模型 | `Qwen/Qwen2.5-VL-7B-Instruct` |
| `MILVUS_DB_PATH` | Milvus数据库路径 | `data/milvus.db` |

---

## 4. 安全说明

### 4.1 文件安全

- 所有上传文件先进入待审核目录
- 不会被自动处理或入库
- 管理员审核后才会被使用

### 4.2 API安全

- 文件下载API只对管理员开放
- 建议配置 API 认证（可选）

### 4.3 数据安全

- Milvus 数据库存储在本地
- 定期备份 `data/milvus.db` 目录

---

## 5. API接口

### 5.1 文件上传（待审核）

```
POST /api/documents/import
```

文件进入 `_pending` 目录，等待审核。

### 5.2 待审核文件列表

```
GET /api/documents/pending
```

### 5.3 审核文件

```
POST /api/documents/approve
Body: { "pending_id": "xxx", "approved": true/false }
```

### 5.4 下载文件

```
GET /api/documents/download/{category}/{filename}
```

---

## 6. 常见问题

### Q: 为什么文件没有被处理？

A: 文件需要管理员审核后才会被处理。请在"待审核"标签页中批准文件。

### Q: 如何批量审核？

A: 可以使用命令行脚本 `review_files.py` 进行批量操作。

### Q: 误批准了恶意文件怎么办？

A: 在"已入库"标签页中删除该文件。

### Q: 如何自动化审核？

A: 目前不支持自动审核，建议人工检查后批准。未来可以考虑集成杀毒扫描。

---

## 7. 更新日志

### v1.3.1
- 新增文件审核机制
- 新增待审核文件列表
- 新增审核脚本 `review_files.py`
- 优化安全防护

### v1.3.0
- 新增 Railway 部署支持
- 新增 Embedding 缓存
- 新增 MCP 服务支持
