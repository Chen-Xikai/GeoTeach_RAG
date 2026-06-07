# -*- coding: utf-8 -*-
"""
GeoTeach RAG - 服务健康检查脚本

检查所有服务的运行状态。
用法: python health_check.py
"""

import sys
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def check_web_service():
    """检查Web服务"""
    try:
        r = requests.get("http://127.0.0.1:9767/api/system/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return True, data.get("status", "ok")
        return False, f"状态码: {r.status_code}"
    except Exception as e:
        return False, str(e)


def check_mcp_service():
    """检查MCP服务"""
    try:
        r = requests.get("http://127.0.0.1:9766/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return True, data
        return False, f"状态码: {r.status_code}"
    except Exception as e:
        return False, str(e)


def check_mcp_tools():
    """检查MCP工具"""
    try:
        r = requests.post(
            "http://127.0.0.1:9766/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            tools = data.get("result", {}).get("tools", [])
            return True, [t["name"] for t in tools]
        return False, f"状态码: {r.status_code}"
    except Exception as e:
        return False, str(e)


def check_mcp_search():
    """检查MCP搜索功能"""
    try:
        r = requests.post(
            "http://127.0.0.1:9766/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search_knowledge_base",
                    "arguments": {"query": "测试"}
                }
            },
            timeout=30
        )
        if r.status_code == 200:
            data = r.json()
            if "result" in data:
                return True, "搜索功能正常"
            return False, data.get("error", "未知错误")
        return False, f"状态码: {r.status_code}"
    except Exception as e:
        return False, str(e)


def check_database():
    """检查数据库"""
    try:
        db_path = ROOT / "data" / "milvus.db"
        if db_path.exists():
            size_mb = db_path.stat().st_size / 1024 / 1024
            return True, f"数据库存在 ({size_mb:.2f} MB)"
        return False, "数据库不存在"
    except Exception as e:
        return False, str(e)


def check_cache():
    """检查缓存"""
    try:
        cache_path = ROOT / "data" / "cache" / "embedding_cache.json"
        if cache_path.exists():
            size_kb = cache_path.stat().st_size / 1024
            return True, f"缓存存在 ({size_kb:.2f} KB)"
        return False, "缓存不存在"
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 50)
    print("GeoTeach RAG 健康检查")
    print("=" * 50)
    print()

    checks = [
        ("Web服务 (9767)", check_web_service),
        ("MCP服务 (9766)", check_mcp_service),
        ("MCP工具", check_mcp_tools),
        ("MCP搜索", check_mcp_search),
        ("数据库", check_database),
        ("缓存", check_cache),
    ]

    all_ok = True
    for name, check_func in checks:
        ok, detail = check_func()
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}: {detail}")
        if not ok:
            all_ok = False

    print()
    print("=" * 50)
    if all_ok:
        print("所有服务正常!")
    else:
        print("部分服务异常，请检查!")
    print("=" * 50)

    # 显示访问地址
    print()
    print("访问地址:")
    print("  Web界面: http://localhost:9767")
    print("  MCP服务: http://localhost:9766")
    print()
    print("OpenCode配置:")
    print('  opencode.json 中已配置MCP服务')
    print('  重启opencode后可使用search_knowledge_base工具')

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
