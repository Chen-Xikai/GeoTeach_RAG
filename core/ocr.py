"""
GeoTeach AI Agent - OCR识别模块

支持在线OCR API和本地PaddleOCR。
"""

import os
import base64
from pathlib import Path
from typing import List, Dict, Optional
import requests

from config import get_siliconflow_config


class OCRProcessor:
    """OCR文字识别处理器"""
    
    def __init__(self, mode: str = "online"):
        """
        初始化OCR处理器
        
        Args:
            mode: 'online' 使用在线API，'local' 使用本地PaddleOCR
        """
        self.mode = mode
        self._ocr = None
        
        if mode == "online":
            config = get_siliconflow_config()
            self._api_key = config["api_key"]
            self._base_url = config["base_url"]
    
    def _encode_image(self, image_path: str) -> str:
        """将图片编码为base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def _ocr_online(self, image_path: str) -> str:
        """使用在线API进行OCR"""
        import base64
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # 使用SiliconFlow的视觉模型进行OCR
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请提取这张图片中的所有文字内容，保持原有格式。如果有表格，请用Markdown表格格式输出。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096
        }
        
        response = requests.post(
            f"{self._base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]
    
    def _ocr_local(self, image_path: str) -> str:
        """使用本地PaddleOCR进行OCR"""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch',
                    show_log=False
                )
            except ImportError:
                raise ImportError(
                    "PaddleOCR未安装，请运行: pip install paddleocr paddlepaddle"
                )
        
        result = self._ocr.ocr(image_path, cls=True)
        
        if not result or not result[0]:
            return ""
        
        texts = []
        for line in result[0]:
            text = line[1][0]
            confidence = line[1][1]
            if confidence > 0.5:
                texts.append(text)
        
        return "\n".join(texts)
    
    def extract_text(self, image_path: str) -> str:
        """
        从图片提取文字
        
        Args:
            image_path: 图片路径
            
        Returns:
            提取的文字内容
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        if self.mode == "online":
            return self._ocr_online(image_path)
        else:
            return self._ocr_local(image_path)
    
    def extract_tables(self, image_path: str) -> List[List[str]]:
        """
        从图片中提取表格数据
        
        Args:
            image_path: 图片路径
            
        Returns:
            表格数据（二维数组）
        """
        if self.mode == "online":
            return self._extract_tables_online(image_path)
        else:
            return self._extract_tables_local(image_path)
    
    def _extract_tables_online(self, image_path: str) -> List[List[str]]:
        """使用在线API提取表格"""
        import base64
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """请提取这张图片中的表格数据，以JSON格式返回：
{
  "has_table": true/false,
  "table_data": [["列1", "列2", ...], ["值1", "值2", ...], ...]
}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2048
        }
        
        response = requests.post(
            f"{self._base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        
        result_text = response.json()["choices"][0]["message"]["content"]
        
        # 解析JSON
        try:
            import json
            json_match = result_text[result_text.find('{'):result_text.rfind('}')+1]
            result = json.loads(json_match)
            if result.get("has_table"):
                return result.get("table_data", [])
            return []
        except:
            return []
    
    def _extract_tables_local(self, image_path: str) -> List[List[str]]:
        """使用本地OCR提取表格"""
        # 获取带坐标的文本
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
            except ImportError:
                return []
        
        result = self._ocr.ocr(image_path, cls=True)
        
        if not result or not result[0]:
            return []
        
        # 按y坐标排序（行）
        text_blocks = []
        for line in result[0]:
            bbox = line[0]
            text = line[1][0]
            text_blocks.append({
                "text": text,
                "y": bbox[0][1],
                "x": bbox[0][0]
            })
        
        text_blocks.sort(key=lambda x: (x['y'], x['x']))
        
        # 简单的表格检测
        rows = []
        current_row = []
        current_y = None
        threshold = 20
        
        for block in text_blocks:
            y = block['y']
            
            if current_y is None or abs(y - current_y) > threshold:
                if current_row:
                    rows.append(current_row)
                current_row = [block['text']]
                current_y = y
            else:
                current_row.append(block['text'])
        
        if current_row:
            rows.append(current_row)
        
        return rows


# 便捷函数
def extract_text_from_image(image_path: str, mode: str = "online") -> str:
    """便捷函数：从图片提取文字"""
    processor = OCRProcessor(mode=mode)
    return processor.extract_text(image_path)
