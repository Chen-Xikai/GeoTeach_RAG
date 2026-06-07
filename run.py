#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动脚本"""

import sys
import os
import uvicorn

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from servers.web import app

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
