#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GeoTeach AI Agent - 启动脚本"""

import os
import sys

# 抑制TensorFlow警告
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# 使用绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['MILVUS_DB_PATH'] = os.path.join(script_dir, 'data', 'milvus.db')

# 确保在项目根目录运行
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入并运行
from servers.web import app
import uvicorn

if __name__ == "__main__":
    print("=" * 50)
    print("  GeoTeach AI Agent - 地理教学助手")
    print("=" * 50)
    print()
    print("  启动中...")
    print("  访问地址: http://127.0.0.1:9767")
    print("  按 Ctrl+C 停止服务")
    print()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=9767,
        log_level="info"
    )
