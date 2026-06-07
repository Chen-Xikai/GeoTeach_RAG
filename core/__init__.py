"""
GeoTeach AI Agent - 核心层
"""

from .api import EmbeddingAPI, RerankAPI
from .chunking import split_text, chunk_single_document, evaluate_chunks
from .database import DocumentDatabase
from .document import read_file, load_single_document, load_all_documents, get_document_paths
from .generator import ContentGenerator
from .image_extractor import ImageExtractor
from .ocr import OCRProcessor
from .vision import VisionProcessor
from .multimodal import MultimodalProcessor, process_document_multimodal

__all__ = [
    "EmbeddingAPI",
    "RerankAPI",
    "split_text",
    "chunk_single_document",
    "evaluate_chunks",
    "DocumentDatabase",
    "read_file",
    "load_single_document",
    "load_all_documents",
    "get_document_paths",
    "ContentGenerator",
    "ImageExtractor",
    "OCRProcessor",
    "VisionProcessor",
    "MultimodalProcessor",
    "process_document_multimodal",
]
