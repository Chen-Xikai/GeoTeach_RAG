"""
GeoTeach AI Agent - 视觉与OCR识别模块

整合在线/本地OCR、图片描述、表格识别、地理信息提取。
"""

import os
import json
import base64
from pathlib import Path
from typing import List, Dict, Optional
import requests

from config import get_siliconflow_config


class VisionProcessor:
    """视觉模型处理器（整合OCR、图片描述、表格分析、地理信息提取）"""
    
    def __init__(self, mode: str = "online"):
        """
        初始化视觉处理器
        
        Args:
            mode: 'online' 使用在线API，'local' 使用本地PaddleOCR
        """
        self.mode = mode
        self._ocr = None
        
        config = get_siliconflow_config()
        self._api_key = config["api_key"]
        self._base_url = config["base_url"]
        self._model = "Qwen/Qwen2.5-VL-7B-Instruct"
    
    def _encode_image(self, image_path: str) -> str:
        """将图片编码为base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def _call_vision_api(self, messages: List[dict], max_tokens: int = 2048) -> str:
        """调用视觉模型API"""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            f"{self._base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]
    
    def _parse_json_response(self, response: str, default: dict = None) -> dict:
        """从LLM响应中提取JSON"""
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except Exception:
            return default or {}
    
    # ==================== OCR ====================
    
    def extract_text(self, image_path: str) -> str:
        """
        从图片提取文字（OCR功能）
        
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
    
    def _ocr_online(self, image_path: str) -> str:
        """使用在线API进行OCR"""
        image_data = self._encode_image(image_path)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请提取这张图片中的所有文字内容，保持原有格式。如果有表格，请用Markdown表格格式输出。只输出文字内容，不要添加额外说明。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
        
        return self._call_vision_api(messages)
    
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
    
    # ==================== 表格识别 ====================
    
    def analyze_table(self, image_path: str) -> dict:
        """
        分析图片中的表格（返回详细信息）
        
        Args:
            image_path: 图片路径
            
        Returns:
            表格分析结果 {has_table, table_description, headers, rows, summary}
        """
        if self.mode == "online":
            return self._analyze_table_online(image_path)
        else:
            return self._analyze_table_local(image_path)
    
    def _analyze_table_online(self, image_path: str) -> dict:
        """使用在线API分析表格"""
        image_data = self._encode_image(image_path)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """请分析这张图片中的表格内容，返回JSON格式：
{
  "has_table": true/false,
  "table_description": "表格描述",
  "headers": ["列1", "列2", ...],
  "rows": [["值1", "值2", ...], ...],
  "summary": "表格内容总结"
}

只返回JSON，不要添加其他内容。"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
        
        response = self._call_vision_api(messages)
        
        return self._parse_json_response(response, default={
            "has_table": False,
            "table_description": response,
            "headers": [],
            "rows": [],
            "summary": response
        })
    
    def _analyze_table_local(self, image_path: str) -> dict:
        """使用本地OCR分析表格"""
        rows = self._extract_tables_local(image_path)
        if rows:
            return {
                "has_table": True,
                "table_description": f"检测到 {len(rows)} 行表格数据",
                "headers": rows[0] if rows else [],
                "rows": rows[1:] if len(rows) > 1 else [],
                "summary": f"表格包含 {len(rows)} 行数据"
            }
        return {
            "has_table": False,
            "table_description": "未检测到表格",
            "headers": [],
            "rows": [],
            "summary": "未检测到表格"
        }
    
    def extract_tables(self, image_path: str) -> List[List[str]]:
        """
        从图片中提取表格数据（返回二维数组）
        
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
        image_data = self._encode_image(image_path)
        
        messages = [
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
        ]
        
        response = self._call_vision_api(messages, max_tokens=2048)
        
        result = self._parse_json_response(response)
        if result.get("has_table"):
            return result.get("table_data", [])
        return []
    
    def _extract_tables_local(self, image_path: str) -> List[List[str]]:
        """使用本地OCR提取表格"""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
            except ImportError:
                return []
        
        result = self._ocr.ocr(image_path, cls=True)
        
        if not result or not result[0]:
            return []
        
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
    
    # ==================== 图片描述 ====================
    
    def describe_image(self, image_path: str) -> str:
        """
        生成图片描述
        
        Args:
            image_path: 图片路径
            
        Returns:
            图片描述文字
        """
        image_data = self._encode_image(image_path)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请详细描述这张图片的内容。如果是地理相关的图片，请特别关注：\n1. 图表类型（地图、示意图、统计图等）\n2. 关键数据和信息\n3. 地理概念和知识点\n4. 图例和标注"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
        
        return self._call_vision_api(messages)
    
    # ==================== 地理信息提取 ====================
    
    def extract_geographic_info(self, image_path: str) -> dict:
        """
        提取地理相关信息
        
        Args:
            image_path: 图片路径
            
        Returns:
            地理信息 {type, topics, key_concepts, data_points, educational_value}
        """
        image_data = self._encode_image(image_path)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """请分析这张地理图片，提取以下信息并以JSON格式返回：
{
  "type": "地图/示意图/统计图/景观图/其他",
  "topics": ["相关地理主题"],
  "key_concepts": ["关键地理概念"],
  "data_points": ["重要数据点"],
  "educational_value": "教学价值描述"
}

只返回JSON，不要添加其他内容。"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
        
        response = self._call_vision_api(messages)
        
        return self._parse_json_response(response, default={
            "type": "其他",
            "topics": [],
            "key_concepts": [],
            "data_points": [],
            "educational_value": response
        })
    
    # ==================== 健康检查 ====================
    
    def health_check(self) -> tuple:
        """健康检查"""
        try:
            from PIL import Image
            import io
            
            img = Image.new('RGB', (100, 100), color='red')
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            image_data = base64.b64encode(buffer.getvalue()).decode()
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "这是什么颜色？"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                    ]
                }
            ]
            
            self._call_vision_api(messages)
            return True, "Vision API正常"
        except Exception as e:
            return False, f"Vision API异常: {str(e)}"


# 向后兼容别名
OCRProcessor = VisionProcessor


# 便捷函数
def extract_text_from_image(image_path: str, mode: str = "online") -> str:
    """便捷函数：从图片提取文字"""
    processor = VisionProcessor(mode=mode)
    return processor.extract_text(image_path)


def describe_image(image_path: str) -> str:
    """便捷函数：生成图片描述"""
    processor = VisionProcessor()
    return processor.describe_image(image_path)
