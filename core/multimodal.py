"""
GeoTeach AI Agent - 多模态处理器

整合图片提取、OCR、视觉模型，处理包含图片的文档。
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.image_extractor import ImageExtractor
from core.vision import VisionProcessor


class MultimodalProcessor:
    """多模态文档处理器"""
    
    def __init__(self, use_vision_api: bool = True):
        """
        初始化多模态处理器
        
        Args:
            use_vision_api: 是否使用视觉模型API
        """
        self.image_extractor = ImageExtractor()
        self.use_vision_api = use_vision_api
        
        if use_vision_api:
            try:
                self.vision_processor = VisionProcessor()
            except Exception as e:
                print(f"视觉模型初始化失败: {e}")
                self.use_vision_api = False
                self.vision_processor = None
        else:
            self.vision_processor = None
    
    def process_document(self, file_path: str) -> List[dict]:
        """
        处理包含图片的文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            处理后的文档列表
        """
        documents = []
        file_path = str(file_path)
        ext = Path(file_path).suffix.lower()
        
        # 1. 提取文本内容
        text_docs = self._extract_text(file_path, ext)
        documents.extend(text_docs)
        
        # 2. 提取图片
        images = self.image_extractor.extract(file_path)
        
        if not images:
            return documents
        
        # 3. 处理每个图片
        for img in images:
            img_doc = self._process_image(img)
            if img_doc:
                documents.append(img_doc)
        
        return documents
    
    def _extract_text(self, file_path: str, ext: str) -> List[dict]:
        """提取文档文本内容"""
        try:
            if ext == '.pptx':
                return self._extract_from_pptx(file_path)
            elif ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif ext == '.docx':
                return self._extract_from_docx(file_path)
            elif ext in ['.txt', '.md']:
                return self._extract_from_text(file_path)
            else:
                return []
        except Exception as e:
            print(f"文本提取失败: {e}")
            return []
    
    def _extract_from_pptx(self, file_path: str) -> List[dict]:
        """从PPT提取文本"""
        try:
            from pptx import Presentation
        except ImportError:
            return []
        
        prs = Presentation(file_path)
        documents = []
        
        for slide_num, slide in enumerate(prs.slides, 1):
            text_content = []
            
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text_content.append(shape.text)
                
                # 提取表格
                if shape.has_table:
                    table = shape.table
                    rows = []
                    for row in table.rows:
                        cells = [cell.text.strip() for cell in row.cells]
                        rows.append(" | ".join(cells))
                    text_content.append("\n".join(rows))
            
            if text_content:
                content = "\n".join(text_content)
                documents.append({
                    "page_content": content,
                    "metadata": {
                        "source": file_path,
                        "type": "text",
                        "slide_number": slide_num,
                        "total_slides": len(prs.slides)
                    }
                })
        
        return documents
    
    def _extract_from_pdf(self, file_path: str) -> List[dict]:
        """从PDF提取文本"""
        try:
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            
            documents = []
            for i, doc in enumerate(docs):
                documents.append({
                    "page_content": doc.page_content,
                    "metadata": {
                        "source": file_path,
                        "type": "text",
                        "page": i + 1
                    }
                })
            return documents
        except Exception as e:
            print(f"PDF提取失败: {e}")
            return []
    
    def _extract_from_docx(self, file_path: str) -> List[dict]:
        """从DOCX提取文本"""
        try:
            from docx import Document
            doc = Document(file_path)
            
            text_content = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_content.append(para.text)
            
            # 提取表格
            for table in doc.tables:
                rows = []
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    rows.append(" | ".join(cells))
                text_content.append("\n".join(rows))
            
            if text_content:
                return [{
                    "page_content": "\n".join(text_content),
                    "metadata": {
                        "source": file_path,
                        "type": "text"
                    }
                }]
            return []
        except Exception as e:
            print(f"DOCX提取失败: {e}")
            return []
    
    def _extract_from_text(self, file_path: str) -> List[dict]:
        """从文本文件提取内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content.strip():
                return [{
                    "page_content": content,
                    "metadata": {
                        "source": file_path,
                        "type": "text"
                    }
                }]
            return []
        except Exception as e:
            print(f"文本提取失败: {e}")
            return []
    
    def _process_image(self, img_info: dict) -> Optional[dict]:
        """处理单个图片"""
        image_path = img_info["path"]
        
        try:
            # 视觉模型处理
            ocr_text = ""
            description = ""
            table_data = {}
            geo_info = {}
            
            if self.use_vision_api and self.vision_processor:
                try:
                    # OCR识别
                    ocr_text = self.vision_processor.extract_text(image_path)
                    
                    # 图片描述
                    description = self.vision_processor.describe_image(image_path)
                    
                    # 表格识别
                    table_data = self.vision_processor.analyze_table(image_path)
                    
                    # 地理信息提取
                    geo_info = self.vision_processor.extract_geographic_info(image_path)
                    
                except Exception as e:
                    print(f"视觉模型处理失败: {e}")
            
            # 合并内容
            content_parts = []
            
            if description:
                content_parts.append(f"【图片描述】\n{description}")
            
            if ocr_text:
                content_parts.append(f"【OCR文字】\n{ocr_text}")
            
            if table_data.get("has_table"):
                content_parts.append(f"【表格内容】\n{table_data.get('table_description', '')}")
            
            if geo_info.get("topics"):
                content_parts.append(f"【地理主题】\n{', '.join(geo_info['topics'])}")
            
            if not content_parts:
                return None
            
            content = "\n\n".join(content_parts)
            
            # 构建元数据
            metadata = {
                "source": img_info.get("source", ""),
                "type": "image",
                "image_path": image_path,
                "has_ocr": bool(ocr_text),
                "has_table": table_data.get("has_table", False)
            }
            
            if "slide" in img_info:
                metadata["slide_number"] = img_info["slide"]
            if "page" in img_info:
                metadata["page"] = img_info["page"]
            
            return {
                "page_content": content,
                "metadata": metadata
            }
        
        except Exception as e:
            print(f"图片处理失败 {image_path}: {e}")
            return None
    
    def process_batch(self, file_paths: List[str], max_workers: int = 2) -> List[dict]:
        """
        批量处理文档
        
        Args:
            file_paths: 文件路径列表
            max_workers: 最大并发数
            
        Returns:
            处理后的文档列表
        """
        all_documents = []
        
        for file_path in file_paths:
            try:
                docs = self.process_document(file_path)
                all_documents.extend(docs)
                print(f"处理完成: {file_path} ({len(docs)}个文档)")
            except Exception as e:
                print(f"处理失败 {file_path}: {e}")
        
        return all_documents


# 便捷函数
def process_document_multimodal(file_path: str, use_vision_api: bool = True) -> List[dict]:
    """便捷函数：处理单个文档"""
    processor = MultimodalProcessor(use_vision_api=use_vision_api)
    return processor.process_document(file_path)
