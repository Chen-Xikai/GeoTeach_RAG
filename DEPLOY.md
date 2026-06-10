# GeoTeach RAG 部署指南

## 目录

1. [本地部署](#1-本地部署)
2. [Docker 部署](#2-docker-部署)
3. [环境变量配置](#3-环境变量配置)
4. [安全说明](#4-安全说明)

---

## 1. 本地部署

### 1.1 环境要求

- Python 3.11+
- Node.js 18+（用于构建前端）
- SiliconFlow API 密钥

### 1.2 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/Chen-Xikai/GeoTeach_RAG.git
cd GeoTeach_RAG

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp config/.env.example config/.env
# 编辑 config/.env 填入你的 API 密钥

# 4. 安装前端依赖并构建
cd frontend
npm install
npm run build
cd ..

# 5. 启动服务
python start.py
```

### 1.3 访问应用

- 地址：http://127.0.0.1:9767
- 默认密码：123

---

## 2. Docker 部署

### 2.1 构建镜像

```bash
docker build -t geoteach-rag .
```

### 2.2 运行容器

```bash
docker run -d \
  -p 9767:9767 \
  -e SILICONFLOW_API_KEY=your-api-key \
  -e ACCESS_PASSWORD=123 \
  -e ADMIN_PASSWORD=123 \
  -v $(pwd)/data:/app/data \
  --name geoteach-rag \
  geoteach-rag
```

### 2.3 访问应用

- 地址：http://localhost:9767

---

## 3. 环境变量配置

### 3.1 必需的环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `SILICONFLOW_API_KEY` | SiliconFlow API密钥 | `sk-xxx` |
| `WEB_HOST` | 监听地址 | `0.0.0.0` |
| `WEB_PORT` | 监听端口 | `9767` |

### 3.2 可选的环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SILICONFLOW_BASE_URL` | API基础URL | `https://api.siliconflow.cn/v1` |
| `EMBEDDING_MODEL` | Embedding模型 | `BAAI/bge-large-zh-v1.5` |
| `LLM_MODEL` | LLM模型 | `Qwen/Qwen2.5-7B-Instruct` |
| `VISION_MODEL` | Vision模型 | `Qwen/Qwen2.5-VL-7B-Instruct` |
| `ACCESS_PASSWORD` | 访问密码 | `123` |
| `ADMIN_PASSWORD` | 管理员密码 | `123` |
| `ALLOWED_ORIGINS` | 允许的跨域来源 | `*` |
| `MILVUS_DB_PATH` | Milvus数据库路径 | `data/milvus.db` |

---

## 4. 安全说明

### 4.1 API安全

- 支持密码认证（ACCESS_PASSWORD / ADMIN_PASSWORD）
- 管理员密码可访问系统设置
- 建议在生产环境中使用强密码

### 4.2 数据安全

- Milvus 数据库存储在本地 `data/milvus.db`
- 建议定期备份 `data/` 目录

---

## 5. 常见问题

### Q: 启动后端口被占用怎么办？

A: 修改 `config/.env` 中的 `WEB_PORT` 使用其他端口，或终止占用端口的进程：
```bash
netstat -ano | findstr :9767
taskkill /F /PID <找到的PID>
```

### Q: Embedding API 不可用？

A: 确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

### Q: 前端页面空白？

A: 确保已构建前端：
```bash
cd frontend && npm install && npm run build
```
