"""
GeoTeach AI Agent - 视觉模型模块

使用SiliconFlow视觉模型进行图片描述和表格识别。
"""

import os
import base64
import json
from pathlib import Path
from typing import List, Dict, Optional
import requests

from config import get_siliconflow_config


class VisionProcessor:
    """视觉模型处理器"""
    
    def __init__(self):
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
    
    def extract_text(self, image_path: str) -> str:
        """
        从图片提取文字（OCR功能）
        
        Args:
            image_path: 图片路径
            
        Returns:
            提取的文字内容
        """
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
    
    def analyze_table(self, image_path: str) -> dict:
        """
        分析图片中的表格
        
        Args:
            image_path: 图片路径
            
        Returns:
            表格分析结果
        """
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
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            return {
                "has_table": False,
                "table_description": response,
                "headers": [],
                "rows": [],
                "summary": response
            }
    
    def extract_geographic_info(self, image_path: str) -> dict:
        """
        提取地理相关信息
        
        Args:
            image_path: 图片路径
            
        Returns:
            地理信息
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
        
        try:
            json_match = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_match)
        except:
            return {
                "type": "其他",
                "topics": [],
                "key_concepts": [],
                "data_points": [],
                "educational_value": response
            }
    
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


# 便捷函数
def describe_image(image_path: str) -> str:
    """便捷函数：生成图片描述"""
    processor = VisionProcessor()
    return processor.describe_image(image_path)
