"""
GeoTeach AI Agent - Web API服务器

提供REST API接口和前端静态文件托管。
"""

import os
import json
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import (
    get_web_config,
    get_docs_dir,
    get_generated_dir,
    get_catalog_dir,
)
from core.database import DocumentDatabase
from core.document import load_single_document, read_file
from core.generator import ContentGenerator


# ==================== 初始化 ====================

app = FastAPI(
    title="GeoTeach AI Agent",
    description="地理教学AI助手API（支持多模态）",
    version="1.1.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局实例
db = None
generator = None


def get_db() -> DocumentDatabase:
    """获取数据库实例"""
    global db
    if db is None:
        db = DocumentDatabase()
    return db


def get_generator() -> ContentGenerator:
    """获取生成器实例"""
    global generator
    if generator is None:
        generator = ContentGenerator(get_db())
    return generator


# ==================== 数据模型 ====================

class GenerateRequest(BaseModel):
    """生成请求"""
    topic: str
    textbook_version: str = "人教版"
    grade_level: str = "高中"
    chapter: str = ""
    class_hours: str = "1课时"
    students: str = ""


class QARequest(BaseModel):
    """问答请求"""
    question: str


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    n_results: int = 5
    category: Optional[str] = None


class ImportRequest(BaseModel):
    """导入请求"""
    use_multimodal: bool = True


# ==================== 系统API ====================

@app.get("/api/system/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "1.1.0"}


@app.get("/api/system/status")
async def system_status():
    """系统状态"""
    db = get_db()
    stats = db.get_stats()
    
    # 检查OCR和Vision可用性
    ocr_available = False
    vision_available = False
    
    try:
        import paddleocr
        ocr_available = True
    except ImportError:
        pass
    
    try:
        from core.vision import VisionProcessor
        vision_available = True
    except Exception:
        pass
    
    return {
        "database": stats,
        "version": "1.1.0",
        "features": {
            "ocr": ocr_available,
            "vision": vision_available,
            "multimodal": ocr_available or vision_available
        }
    }


# ==================== 文档管理API ====================

@app.get("/api/documents")
async def list_documents(category: Optional[str] = None):
    """获取文档列表"""
    db = get_db()
    documents = db.list_documents(category=category)
    return {"documents": documents}


@app.post("/api/documents/import")
async def import_document(
    file: UploadFile = File(...), 
    category: str = "textbook",
    use_multimodal: bool = True,
    chunk_size: int = 200,
    chunk_overlap: int = 30
):
    """上传文档到待审核目录（安全模式）"""
    try:
        # 检查文件类型
        allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.pptx']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式: {file_ext}，支持: {', '.join(allowed_extensions)}"
            )
        
        # 保存到待审核目录
        docs_dir = get_docs_dir()
        pending_dir = docs_dir / "_pending"
        pending_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名（避免冲突）
        import time
        timestamp = int(time.time())
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = pending_dir / safe_filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 保存元数据
        meta_path = file_path.with_suffix(".meta.json")
        import json
        meta = {
            "original_filename": file.filename,
            "category": category,
            "use_multimodal": use_multimodal,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "upload_time": timestamp,
            "file_size": len(content),
            "status": "pending"
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "pending", 
            "message": "文件已上传，等待管理员审核",
            "filename": file.filename,
            "pending_id": safe_filename
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/pending")
async def list_pending_documents():
    """列出待审核的文档"""
    try:
        docs_dir = get_docs_dir()
        pending_dir = docs_dir / "_pending"
        
        if not pending_dir.exists():
            return {"status": "success", "files": [], "count": 0}
        
        import json
        files = []
        for meta_file in pending_dir.glob("*.meta.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["pending_id"] = meta_file.stem.replace(".meta", "")
                files.append(meta)
            except Exception:
                continue
        
        # 按上传时间倒序
        files.sort(key=lambda x: x.get("upload_time", 0), reverse=True)
        
        return {"status": "success", "files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ApproveRequest(BaseModel):
    """审核请求"""
    pending_id: str
    approved: bool


@app.post("/api/documents/approve")
async def approve_document(request: ApproveRequest):
    """审核文档（批准或拒绝）"""
    try:
        docs_dir = get_docs_dir()
        pending_dir = docs_dir / "_pending"
        
        # 查找文件
        file_path = pending_dir / request.pending_id
        meta_path = file_path.with_suffix(".meta.json")
        
        if not file_path.exists() or not meta_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取元数据
        import json
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        if request.approved:
            # 批准：移动到正式目录
            category = meta.get("category", "textbook")
            category_dir = docs_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            original_filename = meta.get("original_filename", file_path.name)
            target_path = category_dir / original_filename
            
            # 如果目标已存在，添加时间戳
            if target_path.exists():
                import time
                name = Path(original_filename).stem
                ext = Path(original_filename).suffix
                target_path = category_dir / f"{name}_{int(time.time())}{ext}"
            
            # 移动文件
            import shutil
            shutil.move(str(file_path), str(target_path))
            
            # 处理文档（添加到向量库）
            from core.document import load_single_document
            docs = load_single_document(str(target_path), use_multimodal=meta.get("use_multimodal", True))
            
            chunk_cfg = {
                "chunk_size": meta.get("chunk_size", 200),
                "overlap": meta.get("chunk_overlap", 30),
                "separators": ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
            }
            
            db = get_db()
            source_path = str(target_path).replace("\\", "/")
            for doc in docs:
                doc["metadata"]["source"] = source_path
                doc["metadata"]["category"] = category
                db.add(doc, chunk_cfg=chunk_cfg)
            
            # 删除元数据文件
            meta_path.unlink()
            
            return {
                "status": "approved",
                "message": f"文件已批准并添加到 {category} 分类",
                "filename": original_filename,
                "documents_count": len(docs)
            }
        else:
            # 拒绝：删除文件
            file_path.unlink()
            meta_path.unlink()
            
            return {
                "status": "rejected",
                "message": "文件已拒绝并删除",
                "filename": meta.get("original_filename", "")
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/import-all")
async def import_all_documents(use_multimodal: bool = True):
    """导入所有文档"""
    try:
        docs_dir = get_docs_dir()
        db = get_db()
        
        allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.pptx']
        imported = 0
        total_docs = 0
        
        for file_path in docs_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in allowed_extensions:
                try:
                    docs = load_single_document(str(file_path), use_multimodal=use_multimodal)
                    for doc in docs:
                        doc["metadata"]["source"] = str(file_path)
                        db.add(doc)
                    imported += 1
                    total_docs += len(docs)
                    print(f"导入成功: {file_path} ({len(docs)}个文档)")
                except Exception as e:
                    print(f"导入失败 {file_path}: {e}")
        
        return {
            "status": "success", 
            "imported": imported,
            "total_documents": total_docs,
            "multimodal": use_multimodal
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/stats")
async def document_stats():
    """获取文档统计"""
    db = get_db()
    return db.get_stats()


class DeleteRequest(BaseModel):
    """删除请求"""
    source: str


@app.post("/api/documents/delete")
async def delete_document(request: DeleteRequest):
    """删除文档"""
    try:
        db = get_db()
        # 标准化路径
        source = request.source.replace("\\", "/")
        db.delete(source)
        return {"status": "success", "source": source}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/content")
async def get_document_content(source: str):
    """获取文档内容"""
    try:
        # 读取文件内容
        file_path = Path(source)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        content = read_file(str(file_path))
        return {"status": "success", "source": source, "content": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/download/{category}/{filename}")
async def download_document(category: str, filename: str):
    """下载文档文件"""
    try:
        docs_dir = get_docs_dir()
        file_path = docs_dir / category / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/list-files")
async def list_files(category: str = None):
    """列出所有文件（用于同步）"""
    try:
        docs_dir = get_docs_dir()
        files = []
        
        allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.pptx']
        
        if category:
            scan_dir = docs_dir / category
            if scan_dir.exists():
                for f in scan_dir.iterdir():
                    if f.is_file() and f.suffix in allowed_extensions:
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
                        if f.is_file() and f.suffix in allowed_extensions:
                            files.append({
                                "filename": f.name,
                                "category": cat_dir.name,
                                "size": f.stat().st_size,
                                "modified": f.stat().st_mtime
                            })
        
        return {"status": "success", "files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 教材目录API ====================

# 学段名称映射（中文 -> 英文目录名）
LEVEL_MAPPING = {
    "初中": "junior",
    "高中": "senior",
    "junior": "junior",
    "senior": "senior"
}


def get_level_dir(level: str) -> Path:
    """获取学段目录"""
    catalog_dir = get_catalog_dir()
    # 将中文转换为英文目录名
    level_key = LEVEL_MAPPING.get(level, level.lower())
    return catalog_dir / level_key


@app.get("/api/catalog/levels")
async def get_levels():
    """获取学段列表"""
    return {"levels": ["初中", "高中"]}


@app.get("/api/catalog/grades")
async def get_grades(level: str):
    """获取年级列表"""
    level_dir = get_level_dir(level)
    
    if not level_dir.exists():
        return {"grades": []}
    
    grades = []
    for json_file in level_dir.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for grade in data.get("年级", []):
                grades.append(grade["name"])
    
    return {"grades": grades}


@app.get("/api/catalog/chapters")
async def get_chapters(level: str, grade: str, semester: str):
    """获取章节列表"""
    level_dir = get_level_dir(level)
    
    if not level_dir.exists():
        return {"chapters": []}
    
    for json_file in level_dir.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for g in data.get("年级", []):
                if g["name"] == grade:
                    for s in g.get("学期", []):
                        if s["name"] == semester:
                            return {"chapters": s.get("章节", [])}
    
    return {"chapters": []}


# ==================== 内容生成API ====================

@app.post("/api/generate/speech-draft")
async def generate_speech_draft(request: GenerateRequest):
    """生成说课稿"""
    try:
        generator = get_generator()
        result = generator.generate_speech_draft(
            topic=request.topic,
            textbook_version=request.textbook_version,
            grade_level=request.grade_level,
            chapter=request.chapter,
            class_hours=request.class_hours
        )
        return {"status": "success", "content": result["content"], "sources": result["sources"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/lecture-draft")
async def generate_lecture_draft(request: GenerateRequest):
    """生成讲课稿"""
    try:
        generator = get_generator()
        result = generator.generate_lecture_draft(
            topic=request.topic,
            textbook_version=request.textbook_version,
            grade_level=request.grade_level,
            chapter=request.chapter,
            class_hours=request.class_hours
        )
        return {"status": "success", "content": result["content"], "sources": result["sources"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/lesson-plan")
async def generate_lesson_plan(request: GenerateRequest):
    """生成教案"""
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
        return {"status": "success", "content": result["content"], "sources": result["sources"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/study-plan")
async def generate_study_plan(request: GenerateRequest):
    """生成学案"""
    try:
        generator = get_generator()
        result = generator.generate_study_plan(
            topic=request.topic,
            textbook_version=request.textbook_version,
            grade_level=request.grade_level,
            chapter=request.chapter,
            class_hours=request.class_hours
        )
        return {"status": "success", "content": result["content"], "sources": result["sources"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 搜索API ====================

@app.post("/api/search")
async def search_documents(request: SearchRequest):
    """搜索文档"""
    try:
        db = get_db()
        results = db.search(
            query=request.query,
            n_results=request.n_results,
            category=request.category
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 问答API ====================

@app.post("/api/qa")
async def question_answer(request: QARequest):
    """智能问答"""
    try:
        generator = get_generator()
        result = generator.answer_question(request.question)
        return {"status": "success", "answer": result["answer"], "sources": result["sources"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 静态文件服务 ====================

# 挂载前端静态文件
frontend_dir = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """服务前端页面"""
    frontend_dir = Path(__file__).parent.parent / "frontend" / "dist"
    
    # 尝试返回静态文件
    file_path = frontend_dir / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    
    # 返回index.html（SPA路由）
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    
    return {"message": "GeoTeach AI Agent API"}


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    
    config = get_web_config()
    uvicorn.run(
        "servers.web:app",
        host=config["host"],
        port=config["port"],
        reload=True
    )
