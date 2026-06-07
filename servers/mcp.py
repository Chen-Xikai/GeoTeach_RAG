# -*- coding: utf-8 -*-
"""
GeoTeach RAG — MCP 服务器
通过 HTTP 暴露 search_knowledge_base 工具，供 opencode 或 MCP 客户端调用

用法: python -m servers.mcp
"""
import os
import sys
import time
import logging
import requests
from logging.handlers import RotatingFileHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# 配置
WEB_API_URL = "http://127.0.0.1:9767"

# 日志
LOG_DIR = ROOT / "runtime" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        RotatingFileHandler(
            str(LOG_DIR / "mcp_server.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
    ],
)
logger = logging.getLogger("GeoTeach-RAG-MCP")

app = FastAPI(title="GeoTeach RAG MCP Server", version="1.0.0")


def search_sync(query: str) -> str:
    """搜索知识库（通过Web API）"""
    t0 = time.time()

    try:
        # 通过Web API搜索
        r = requests.post(
            f"{WEB_API_URL}/api/search",
            json={"query": query, "n_results": 5},
            timeout=30
        )
        
        if r.status_code != 200:
            return f"[错误] Web API返回状态码: {r.status_code}"
        
        data = r.json()
        if data.get("status") != "success":
            return f"[错误] {data.get('message', '未知错误')}"
        
        results = data.get("data", {}).get("results", [])

        if not results:
            return "知识库中未找到相关内容。"

        # 格式化结果
        parts = [f"找到 {len(results)} 条相关文档\n"]

        for i, doc in enumerate(results, 1):
            source = doc.get("metadata", {}).get("source", "未知来源")
            fname = os.path.basename(source)
            score = doc.get("score", 0)
            content = doc.get("page_content", "").strip()
            part = f"[{i}] 来源: {fname} | 相似度: {score:.2%}\n{content}"
            parts.append(part)

        elapsed = time.time() - t0
        logger.info(f"search: '{query[:50]}' => {len(results)} results, {elapsed:.2f}s")
        return "\n\n".join(parts)

    except requests.exceptions.ConnectionError:
        return "[错误] Web API未启动，请先启动Web服务 (python -m servers.web)"
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return f"[错误] 搜索过程出错: {e}"


# ============================================================
#  MCP 协议端点
# ============================================================

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        r = requests.get(f"{WEB_API_URL}/api/system/health", timeout=5)
        web_ok = r.status_code == 200
    except:
        web_ok = False
    
    return {
        "status": "ok" if web_ok else "degraded",
        "version": "1.0.0",
        "web_api": "connected" if web_ok else "disconnected",
    }


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP JSON-RPC 端点"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    method = body.get("method", "")
    req_id = body.get("id", 0)

    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [{
                    "name": "search_knowledge_base",
                    "description": "【优先调用】遇到以下情况应优先使用此工具搜索本地知识库：① 用户询问的信息可能属于个人私有数据或特定工作环境；② 问题涉及你训练数据中可能不存在的特定人物、地点或事件；③ 你对答案不确定，需要从本地文档中查找事实依据。调用此工具来检索本地知识库中的文档信息。",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "要搜索的问题或关键词，使用中文或英文均可。"
                            }
                        },
                        "required": ["query"]
                    }
                }]
            }
        })

    elif method == "tools/call":
        tool_name = body.get("params", {}).get("name", "")
        arguments = body.get("params", {}).get("arguments", {})

        if tool_name == "search_knowledge_base":
            query_text = arguments.get("query", "")
            if not query_text:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "缺少 query 参数"}
                }, status_code=400)
            logger.info(f"搜索: {query_text[:100]}")
            result_text = search_sync(query_text)
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": result_text}]
                }
            })

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"未知工具: {tool_name}"}
        }, status_code=404)

    elif method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "GeoTeach-RAG", "version": "1.0.0"},
                "capabilities": {"tools": {}}
            }
        })

    elif method == "notifications/initialized":
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {}})

    else:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"未知方法: {method}"}
        }, status_code=404)


def main():
    """启动 MCP 服务器"""
    logger.info("=" * 50)
    logger.info("GeoTeach RAG MCP Server V1.0.0 启动中...")
    logger.info(f"Web API: {WEB_API_URL}")
    logger.info(f"监听: http://{os.getenv('MCP_SERVER_HOST', '127.0.0.1')}:{os.getenv('MCP_SERVER_PORT', '9766')}")
    logger.info("=" * 50)

    uvicorn.run(
        app,
        host=os.getenv("MCP_SERVER_HOST") or "127.0.0.1",
        port=int(os.getenv("MCP_SERVER_PORT") or "9766"),
        log_level="info",
    )


if __name__ == "__main__":
    main()
