FROM node:20-slim AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码（排除前端源码和node_modules）
COPY config/ config/
COPY core/ core/
COPY servers/ servers/
COPY runtime/ runtime/
COPY data/ data/
COPY start.py launcher.py ./
COPY *.md ./

# 复制前端构建产物
COPY --from=frontend-builder /frontend/dist frontend/dist/

# 创建必要目录
RUN mkdir -p data/docs data/generated data/cache data/images runtime/logs runtime/state

# 暴露端口
EXPOSE 9767

# 启动命令
CMD ["python", "start.py"]
