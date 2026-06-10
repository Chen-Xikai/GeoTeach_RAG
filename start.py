#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GeoTeach RAG - 启动脚本"""

import os
import sys

# 使用绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('MILVUS_DB_PATH', os.path.join(script_dir, 'data', 'milvus.db'))

# 确保在项目根目录运行
os.chdir(script_dir)
sys.path.insert(0, script_dir)

# 导入并运行
from servers.web import app
import uvicorn

if __name__ == "__main__":
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "9767"))
    
    print("=" * 50)
    print("  GeoTeach AI Agent - 地理教学助手")
    print("=" * 50)
    print()
    print("  启动中...")
    print(f"  访问地址: http://{host}:{port}")
    print("  按 Ctrl+C 停止服务")
    print()
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
