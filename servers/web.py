# -*- coding: utf-8 -*-
"""
GeoTeach RAG — Web API 服务器
提供 REST API 接口 + WebSocket 实时进度 + 托管前端静态文件
用法: python -m servers.web
"""
import os
import sys
import json
import asyncio
import logging
import socket
from pathlib import Path
from typing import List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / "config" / ".env")

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import (
    get_web_config, get_docs_dir, get_generated_dir, get_catalog_dir,
    get_chunk_config, get_retrieval_config, get_collection_name
)
from config.version import VERSION, PROJECT_NAME

LOG_DIR = ROOT / "runtime" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "web_api.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GeoTeach-Web")

app = FastAPI(title=f"{PROJECT_NAME} Web API", version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:9767", "http://127.0.0.1:9767", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
#  WebSocket 管理器
# ============================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# 线程池，用于执行同步/重建等耗时操作
executor = ThreadPoolExecutor(max_workers=2)

# ============================================================
#  数据模型
# ============================================================

class ApiResponse(BaseModel):
    status: str
    data: Any = None
    message: str = ""

class SearchRequest(BaseModel):
    query: str
    n_results: int = 5
    category: Optional[str] = None

class QARequest(BaseModel):
    question: str

class GenerateRequest(BaseModel):
    topic: str
    textbook_version: str = "人教版"
    grade_level: str = "高中"
    chapter: str = ""
    class_hours: str = "1课时"
    students: str = ""

class ImportRequest(BaseModel):
    files: List[str]

class SyncRequest(BaseModel):
    source: str = "all"

# ============================================================
#  全局实例
# ============================================================

db = None
generator = None

def get_db():
    global db
    if db is None:
        from core.database import DocumentDatabase
        db = DocumentDatabase()
    return db

def get_generator():
    global generator
    if generator is None:
        from core.generator import ContentGenerator
        generator = ContentGenerator(get_db())
    return generator

# ============================================================
#  工具函数
# ============================================================

def check_port(host: str, port: int) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def get_local_documents(source: str = "all") -> List[str]:
    """获取本地文档路径列表（返回绝对路径）"""
    from core.multimodal import SUPPORTED_EXTENSIONS
    
    docs_dir = get_docs_dir()
    paths = []
    
    if source in ("all", "docs"):
        if docs_dir.exists():
            for ext in SUPPORTED_EXTENSIONS:
                for f in docs_dir.rglob(f"*{ext}"):
                    if f.is_file():
                        # 返回绝对路径，与向量库中存储的路径一致
                        paths.append(str(f.resolve()))
    
    return paths

# ============================================================
#  WebSocket 端点
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ============================================================
#  系统 API
# ============================================================

@app.get("/api/system/health")
async def health_check():
    return {"status": "healthy", "version": VERSION}

@app.get("/api/system/status")
async def system_status():
    db = get_db()
    stats = db.get_stats()
    
    return ApiResponse(
        status="success",
        data={
            "version": VERSION,
            "database": stats,
            "services": {
                "web": {"online": True, "port": int(os.getenv("WEB_PORT", "9767"))},
                "mcp": {"online": check_port("127.0.0.1", int(os.getenv("MCP_SERVER_PORT", "9766"))), "port": int(os.getenv("MCP_SERVER_PORT", "9766"))},
            }
        }
    )

# ============================================================
#  配置 API
# ============================================================

@app.get("/api/config")
async def get_config():
    try:
        config_path = ROOT / "config" / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return ApiResponse(status="success", data={"config": config})
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

@app.get("/api/config/templates")
async def get_templates():
    try:
        config_path = ROOT / "config" / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        templates = config.get("chunk", {}).get("templates", {})
        return ApiResponse(status="success", data=templates)
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

@app.get("/api/config/chunk")
async def get_chunk_config_api():
    try:
        config = get_chunk_config()
        return ApiResponse(status="success", data=config)
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

# ============================================================
#  文档管理 API
# ============================================================

@app.get("/api/documents")
async def list_documents(source: str = "all"):
    """获取文档列表（带状态）"""
    try:
        db = get_db()
        
        # 获取本地文件
        local_docs = get_local_documents(source)
        local_set = set(local_docs)
        
        # 获取向量库文档（通过查询所有文档）
        vector_docs = []
        try:
            # 使用db的list_documents方法
            vector_docs = db.list_documents()
        except Exception as e:
            logger.error(f"获取向量库文档失败: {e}")
        
        # 构建向量库文档映射
        vector_map = {}
        for doc in vector_docs:
            src = doc.get("id", "") or doc.get("metadata", {}).get("source", "")
            if src:
                vector_map[src] = doc
        
        result = []
        for doc_path in local_docs:
            doc_name = Path(doc_path).name
            if doc_path in vector_map:
                v = vector_map[doc_path]
                result.append({
                    "path": doc_path,
                    "name": doc_name,
                    "source_type": "local",
                    "status": "imported",
                    "chunks": v.get("chunks", 0),
                    "content_hash": v.get("content_hash", ""),
                })
            else:
                result.append({
                    "path": doc_path,
                    "name": doc_name,
                    "source_type": "local",
                    "status": "local",
                    "chunks": 0,
                    "content_hash": "",
                })
        
        # 添加孤立记录
        for doc in vector_docs:
            doc_source = doc.get("id", "") or doc.get("metadata", {}).get("source", "")
            if doc_source and doc_source not in local_set:
                result.append({
                    "path": doc_source,
                    "name": Path(doc_source).name,
                    "source_type": "local",
                    "status": "orphan",
                    "chunks": 0,
                    "content_hash": "",
                })
        
        return ApiResponse(status="success", data=result)
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        return ApiResponse(status="error", message=str(e))

@app.post("/api/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """上传文件到 data/docs 目录"""
    try:
        docs_dir = get_docs_dir()
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded = []
        for file in files:
            safe_name = os.path.basename(file.filename)
            file_path = docs_dir / safe_name
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            uploaded.append(file.filename)
            logger.info(f"上传文件: {file.filename}")
        
        return ApiResponse(status="success", data={"uploaded": uploaded, "count": len(uploaded)})
    except Exception as e:
        logger.error(f"上传失败: {e}")
        return ApiResponse(status="error", message=str(e))

@app.post("/api/documents/import")
async def import_documents(request: ImportRequest):
    """导入文档到向量库"""
    try:
        from core.multimodal import read_file, SUPPORTED_EXTENSIONS
        
        db = get_db()
        chunk_cfg = get_chunk_config()
        
        results = []
        total_chunks = 0
        
        for file_path in request.files:
            full_path = Path(file_path)
            if not full_path.exists():
                results.append({"file": file_path, "status": "error", "message": "文件不存在"})
                continue
            
            ext = full_path.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                results.append({"file": file_path, "status": "error", "message": f"不支持的格式: {ext}"})
                continue
            
            try:
                text = read_file(str(full_path))
                if not text or not text.strip():
                    results.append({"file": file_path, "status": "error", "message": "文件内容为空"})
                    continue
                
                doc_name = full_path.stem
                text = f"[文件名: {doc_name}]\n{text}"
                doc = {
                    "page_content": text,
                    "metadata": {
                        "source": str(full_path),
                        "filename": full_path.name,
                    }
                }
                
                doc_ids = db.add(doc, chunk_cfg, source_type="local_file")
                count = len(doc_ids) if doc_ids else 0
                total_chunks += count
                results.append({"file": file_path, "status": "success", "chunks": count})
                
                await manager.broadcast({
                    "type": "import_progress",
                    "data": {"file": full_path.name, "chunks": count, "status": "success"}
                })
            except Exception as e:
                results.append({"file": file_path, "status": "error", "message": str(e)})
        
        return ApiResponse(
            status="success",
            data={"results": results, "total_chunks": total_chunks}
        )
    except Exception as e:
        logger.error(f"导入失败: {e}")
        return ApiResponse(status="error", message=str(e))

@app.post("/api/documents/batch-import")
async def batch_import_documents(request: ImportRequest):
    """批量导入文档（带WebSocket进度）"""
    try:
        from core.multimodal import read_file, SUPPORTED_EXTENSIONS
        
        db = get_db()
        chunk_cfg = get_chunk_config()
        
        total = len(request.files)
        imported = 0
        total_chunks = 0
        
        for idx, file_path in enumerate(request.files, 1):
            full_path = Path(file_path)
            if not full_path.exists():
                continue
            
            ext = full_path.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            
            try:
                text = read_file(str(full_path))
                if not text or not text.strip():
                    continue
                
                doc_name = full_path.stem
                text = f"[文件名: {doc_name}]\n{text}"
                doc = {
                    "page_content": text,
                    "metadata": {
                        "source": str(full_path),
                        "filename": full_path.name,
                    }
                }
                
                doc_ids = db.add(doc, chunk_cfg, source_type="local_file")
                count = len(doc_ids) if doc_ids else 0
                total_chunks += count
                imported += 1
                
                await manager.broadcast({
                    "type": "batch_progress",
                    "data": {"op": "import", "idx": idx, "total": total, "name": full_path.name, "status": "success", "chunks": count}
                })
            except Exception as e:
                logger.warning(f"导入失败 {file_path}: {e}")
        
        await manager.broadcast({
            "type": "batch_complete",
            "data": {"op": "import", "imported": imported, "total_chunks": total_chunks}
        })
        
        return ApiResponse(status="success", data={"imported": imported, "total_chunks": total_chunks})
    except Exception as e:
        logger.error(f"批量导入失败: {e}")
        return ApiResponse(status="error", message=str(e))

@app.delete("/api/documents/{file_path:path}")
async def delete_document(file_path: str):
    """删除文档向量记录"""
    try:
        db = get_db()
        logger.info(f"删除文档: {file_path}")
        db.delete(file_path)
        logger.info(f"删除成功: {file_path}")
        return ApiResponse(status="success", message=f"已删除: {file_path}")
    except Exception as e:
        logger.error(f"删除失败: {file_path}, 错误: {e}")
        return ApiResponse(status="error", message=str(e))

@app.post("/api/documents/batch-delete")
async def batch_delete_documents(request: ImportRequest):
    """批量删除文档"""
    try:
        db = get_db()
        deleted = 0
        
        for file_path in request.files:
            try:
                db.delete(file_path)
                deleted += 1
            except Exception as e:
                logger.warning(f"删除失败 {file_path}: {e}")
        
        return ApiResponse(status="success", data={"deleted": deleted})
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

@app.post("/api/documents/delete-all")
async def delete_all_documents(request: ImportRequest = ImportRequest(files=[])):
    """删除所有文档向量记录"""
    try:
        db = get_db()
        sources = db.list_sources()
        deleted = 0
        
        for source in sources:
            try:
                db.delete(source)
                deleted += 1
            except Exception as e:
                logger.warning(f"删除失败 {source}: {e}")
        
        logger.info(f"完全删除完成: {deleted} 个文档")
        return ApiResponse(status="success", data={"deleted": deleted})
    except Exception as e:
        logger.error(f"完全删除失败: {e}")
        return ApiResponse(status="error", message=str(e))

class UpdateRequest(BaseModel):
    file_path: str

@app.post("/api/documents/update")
async def update_document(request: UpdateRequest):
    """更新单个文档"""
    try:
        from core.multimodal import read_file, SUPPORTED_EXTENSIONS
        
        file_path = request.file_path
        if not file_path:
            return ApiResponse(status="error", message="未指定文件路径")
        
        full_path = Path(file_path)
        if not full_path.exists():
            return ApiResponse(status="error", message="文件不存在")
        
        ext = full_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return ApiResponse(status="error", message=f"不支持的格式: {ext}")
        
        text = read_file(str(full_path))
        if not text or not text.strip():
            return ApiResponse(status="error", message="文件内容为空")
        
        db = get_db()
        chunk_cfg = get_chunk_config()
        
        doc_name = full_path.stem
        text = f"[文件名: {doc_name}]\n{text}"
        doc = {
            "page_content": text,
            "metadata": {
                "source": str(full_path),
                "filename": full_path.name,
            }
        }
        
        doc_ids = db.update(doc, chunk_cfg, source_type="local_file")
        count = len(doc_ids) if doc_ids else 0
        
        logger.info(f"更新成功: {file_path}, {count} chunks")
        return ApiResponse(status="success", data={"chunks": count})
    except Exception as e:
        logger.error(f"更新失败: {e}")
        return ApiResponse(status="error", message=str(e))

@app.post("/api/documents/sync")
async def sync_documents(request: SyncRequest = SyncRequest()):
    """增量同步文档"""
    try:
        from core.multimodal import load_all_documents
        
        db = get_db()
        chunk_cfg = get_chunk_config()
        
        # 加载本地文档
        docs_dir = get_docs_dir()
        if not docs_dir.exists():
            return ApiResponse(status="error", message="没有找到数据目录")
        
        logger.info(f"开始同步文档...")
        documents = load_all_documents(docs_dir)
        if not documents:
            return ApiResponse(status="error", message="没有本地文档")
        
        logger.info(f"共加载 {len(documents)} 份文档")
        
        # 创建进度队列
        progress_queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        
        # 进度回调
        def on_progress(op, idx, total, name, count):
            try:
                loop.call_soon_threadsafe(
                    progress_queue.put_nowait,
                    {"op": op, "idx": idx, "total": total, "name": name, "count": count}
                )
            except Exception:
                pass
        
        # 异步进度推送协程
        async def push_progress():
            while True:
                try:
                    msg = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
                    if msg.get("done"):
                        break
                    await manager.broadcast({"type": "sync_progress", "data": msg})
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break
        
        push_task = asyncio.create_task(push_progress())
        
        # 在线程池中执行同步
        stats = await loop.run_in_executor(
            executor,
            lambda: db.sync(documents, chunk_cfg, on_progress=on_progress)
        )
        
        # 通知进度推送结束
        progress_queue.put_nowait({"done": True})
        await push_task
        
        logger.info(f"同步完成: {stats}")
        
        await manager.broadcast({"type": "sync_complete", "data": stats})
        
        return ApiResponse(status="success", data=stats)
    except Exception as e:
        logger.error(f"同步失败: {e}")
        return ApiResponse(status="error", message=str(e))

@app.post("/api/documents/rebuild")
async def rebuild_documents(request: SyncRequest = SyncRequest()):
    """全量重建向量库"""
    try:
        from core.multimodal import load_all_documents
        
        db = get_db()
        chunk_cfg = get_chunk_config()
        
        # 加载本地文档
        docs_dir = get_docs_dir()
        if not docs_dir.exists():
            return ApiResponse(status="error", message="没有找到数据目录")
        
        logger.info("开始重建向量库...")
        documents = load_all_documents(docs_dir)
        if not documents:
            return ApiResponse(status="error", message="没有本地文档")
        
        logger.info(f"共加载 {len(documents)} 份文档")
        
        # 创建进度队列
        progress_queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        
        def on_progress(op, idx, total, name, count):
            try:
                loop.call_soon_threadsafe(
                    progress_queue.put_nowait,
                    {"op": op, "idx": idx, "total": total, "name": name, "count": count}
                )
            except Exception:
                pass
        
        async def push_progress():
            while True:
                try:
                    msg = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
                    if msg.get("done"):
                        break
                    await manager.broadcast({"type": "rebuild_progress", "data": msg})
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break
        
        push_task = asyncio.create_task(push_progress())
        
        # 在线程池中执行重建
        count = await loop.run_in_executor(
            executor,
            lambda: db.rebuild(documents, chunk_cfg, on_progress=on_progress)
        )
        
        progress_queue.put_nowait({"done": True})
        await push_task
        
        logger.info(f"重建完成: {count} chunks")
        
        await manager.broadcast({
            "type": "rebuild_complete",
            "data": {"chunks": count, "documents": len(documents)}
        })
        
        return ApiResponse(status="success", data={"chunks": count, "documents": len(documents)})
    except Exception as e:
        logger.error(f"重建失败: {e}")
        return ApiResponse(status="error", message=str(e))

@app.post("/api/documents/clean-orphans")
async def clean_orphan_records():
    """清理孤立记录"""
    try:
        db = get_db()
        docs_dir = get_docs_dir()
        
        count = db.clean_orphan_records([str(docs_dir)])
        
        return ApiResponse(status="success", data={"cleaned": count})
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

@app.get("/api/documents/orphans")
async def check_orphan_records():
    """检查孤立记录"""
    try:
        db = get_db()
        docs_dir = get_docs_dir()
        
        orphans = db.check_orphan_records([str(docs_dir)])
        
        return ApiResponse(status="success", data={"orphans": orphans, "count": len(orphans)})
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

@app.get("/api/documents/stats")
async def get_document_stats():
    """获取文档统计"""
    try:
        db = get_db()
        stats = db.get_stats()
        return ApiResponse(status="success", data=stats)
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

@app.get("/api/documents/list-files")
async def list_files(category: str = None):
    """列出所有文件（用于同步）"""
    try:
        docs_dir = get_docs_dir()
        files = []
        
        from core.multimodal import SUPPORTED_EXTENSIONS
        
        if category:
            scan_dir = docs_dir / category
            if scan_dir.exists():
                for f in scan_dir.iterdir():
                    if f.is_file() and f.suffix in SUPPORTED_EXTENSIONS:
                        files.append({
                            "filename": f.name,
                            "category": category,
                            "size": f.stat().st_size,
                            "modified": f.stat().st_mtime
                        })
        else:
            for cat_dir in docs_dir.iterdir():
                if cat_dir.is_dir():
                    for f in cat_dir.iterdir():
                        if f.is_file() and f.suffix in SUPPORTED_EXTENSIONS:
                            files.append({
                                "filename": f.name,
                                "category": cat_dir.name,
                                "size": f.stat().st_size,
                                "modified": f.stat().st_mtime
                            })
        
        return ApiResponse(status="success", data={"files": files, "count": len(files)})
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

# ============================================================
#  教材目录 API
# ============================================================

@app.get("/api/catalog/levels")
async def get_levels():
    return ApiResponse(status="success", data=["初中", "高中"])

@app.get("/api/catalog/grades")
async def get_grades(level: str):
    try:
        catalog_dir = get_catalog_dir()
        level_dir = catalog_dir / ("junior" if level == "初中" else "senior")
        
        if not level_dir.exists():
            return ApiResponse(status="success", data=[])
        
        grades = []
        for f in level_dir.iterdir():
            if f.suffix == '.json':
                grades.append(f.stem)
        
        return ApiResponse(status="success", data=grades)
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

@app.get("/api/catalog/chapters")
async def get_chapters(level: str, grade: str = None, semester: str = None):
    try:
        catalog_dir = get_catalog_dir()
        level_dir = catalog_dir / ("junior" if level == "初中" else "senior")
        
        if not level_dir.exists():
            return ApiResponse(status="success", data=[])
        
        # 读取目录文件
        catalog_file = level_dir / "pep.json"
        if not catalog_file.exists():
            return ApiResponse(status="success", data=[])
        
        with open(catalog_file, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
        
        # 根据参数过滤
        chapters = catalog.get("chapters", [])
        
        return ApiResponse(status="success", data=chapters)
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

# ============================================================
#  内容生成 API
# ============================================================

@app.post("/api/generate/speech-draft")
async def generate_speech_draft(request: GenerateRequest):
    try:
        generator = get_generator()
        result = generator.generate_speech_draft(
            topic=request.topic,
            textbook_version=request.textbook_version,
            grade_level=request.grade_level,
            chapter=request.chapter,
            class_hours=request.class_hours
        )
        return ApiResponse(status="success", data={"content": result})
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

@app.post("/api/generate/lecture-draft")
async def generate_lecture_draft(request: GenerateRequest):
    try:
        generator = get_generator()
        result = generator.generate_lecture_draft(
            topic=request.topic,
            textbook_version=request.textbook_version,
            grade_level=request.grade_level,
            chapter=request.chapter,
            class_hours=request.class_hours
        )
        return ApiResponse(status="success", data={"content": result})
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

@app.post("/api/generate/lesson-plan")
async def generate_lesson_plan(request: GenerateRequest):
    try:
        generator = get_generator()
        result = generator.generate_lesson_plan(
            topic=request.topic,
            textbook_version=request.textbook_version,
            grade_level=request.grade_level,
            chapter=request.chapter,
            class_hours=request.class_hours,
            students=request.students
        )
        return ApiResponse(status="success", data={"content": result})
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

@app.post("/api/generate/study-plan")
async def generate_study_plan(request: GenerateRequest):
    try:
        generator = get_generator()
        result = generator.generate_study_plan(
            topic=request.topic,
            textbook_version=request.textbook_version,
            grade_level=request.grade_level,
            chapter=request.chapter,
            class_hours=request.class_hours
        )
        return ApiResponse(status="success", data={"content": result})
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

# ============================================================
#  搜索和问答 API
# ============================================================

@app.post("/api/search")
async def search_documents(request: SearchRequest):
    try:
        db = get_db()
        results = db.search(request.query, n_results=request.n_results, category=request.category)
        return ApiResponse(status="success", data={"results": results})
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

@app.post("/api/qa")
async def question_answer(request: QARequest):
    try:
        generator = get_generator()
        result = generator.answer_question(request.question)
        return ApiResponse(status="success", data={"answer": result["answer"], "sources": result["sources"]})
    except Exception as e:
        return ApiResponse(status="error", message=str(e))

# ============================================================
#  静态文件服务
# ============================================================

import mimetypes

mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('application/json', '.json')

frontend_dir = ROOT / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """服务前端页面"""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404)
    
    file_path = frontend_dir / full_path
    if file_path.exists() and file_path.is_file():
        media_type, _ = mimetypes.guess_type(str(file_path))
        response = FileResponse(str(file_path), media_type=media_type)
        # 添加缓存控制头
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        response = FileResponse(str(index_path), media_type="text/html")
        # 添加缓存控制头
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    return {"message": "GeoTeach RAG API"}

# ============================================================
#  启动入口
# ============================================================

if __name__ == "__main__":
    config = get_web_config()
    uvicorn.run(
        "servers.web:app",
        host=config["host"],
        port=config["port"],
        reload=True
    )
