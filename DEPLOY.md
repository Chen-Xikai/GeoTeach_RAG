# GeoTeach RAG 部署指南

## 目录

1. [Railway部署](#1-railway部署)
2. [文件同步](#2-文件同步)
3. [环境变量配置](#3-环境变量配置)

---

## 1. Railway部署

### 1.1 准备工作

1. 注册 [Railway](https://railway.app) 账号
2. 安装 Railway CLI（可选）

### 1.2 部署步骤

#### 方法一：通过GitHub部署（推荐）

1. Fork 项目到你的 GitHub 账号
2. 登录 Railway
3. 点击 "New Project" → "Deploy from GitHub repo"
4. 选择你 fork 的仓库
5. Railway 会自动检测 Dockerfile 并部署

#### 方法二：通过CLI部署

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 初始化项目
railway init

# 部署
railway up
```

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

1. 在 Railway 项目设置中点击 "Settings"
2. 在 "Networking" 部分可以配置自定义域名
3. Railway 会自动提供一个 `*.up.railway.app` 域名

---

## 2. 文件同步

### 2.1 使用同步脚本

在本地运行同步脚本，从 Railway 下载新上传的文件：

```bash
# 单次同步
python sync_files.py --server https://your-app.up.railway.app

# 定时同步（每5分钟）
python sync_files.py --server https://your-app.up.railway.app --interval 300

# 指定本地目录
python sync_files.py --server https://your-app.up.railway.app --local-dir data/docs
```

### 2.2 设置定时任务

#### Windows（任务计划程序）

1. 打开 "任务计划程序"
2. 创建基本任务
3. 设置触发器（如每小时）
4. 操作：启动程序 `python`
5. 参数：`sync_files.py --server https://your-app.up.railway.app`

#### Linux/Mac（crontab）

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每小时同步一次）
0 * * * * cd /path/to/GeoTeach_RAG && python sync_files.py --server https://your-app.up.railway.app
```

### 2.3 同步状态

同步状态保存在 `data/sync_state.json`，包含：
- `last_sync`: 上次同步时间
- `downloaded_files`: 已下载文件列表

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

## 4. API接口

### 4.1 文件下载API

```
GET /api/documents/download/{category}/{filename}
```

下载指定分类下的文件。

### 4.2 文件列表API

```
GET /api/documents/list-files?category=textbook
```

列出所有文件，用于同步脚本。

---

## 5. 常见问题

### Q: Railway部署失败怎么办？

A: 检查以下几点：
1. Dockerfile 是否正确
2. 依赖是否完整
3. 环境变量是否配置

### Q: 同步脚本连接失败怎么办？

A: 检查以下几点：
1. Railway 服务是否正常运行
2. 域名是否正确
3. 网络是否通畅

### Q: 文件同步不完整怎么办？

A: 删除 `data/sync_state.json` 重新同步。

---

## 6. 更新日志

### v1.3.0
- 新增 Railway 部署支持
- 新增 文件同步脚本
- 新增 文件下载API
