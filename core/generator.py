"""
GeoTeach AI Agent - 内容生成器

提供教学内容生成功能，包括说课稿、讲课稿、教案、学案等。
"""

import json
from typing import List, Dict, Optional
from pathlib import Path

from config import (
    get_siliconflow_config,
    get_llm_config,
    get_templates_dir,
)
from core.api import RerankAPI
from core.database import DocumentDatabase


class ContentGenerator:
    """内容生成器"""
    
    def __init__(self, db: DocumentDatabase):
        self.db = db
        self.rerank_api = RerankAPI()
        
        config = get_siliconflow_config()
        llm_config = get_llm_config()
        
        self._api_key = config["api_key"]
        self._base_url = config["base_url"]
        self._model = llm_config["model"]
        
        # 加载模板
        self._templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, dict]:
        """加载所有模板"""
        templates = {}
        templates_dir = get_templates_dir()
        
        for template_file in templates_dir.glob("*.json"):
            with open(template_file, "r", encoding="utf-8") as f:
                template = json.load(f)
                templates[template["id"]] = template
        
        return templates
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM生成内容"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "你是一位经验丰富的地理教学专家。请根据要求生成专业的教学内容。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4096
        }
        
        response = requests.post(
            f"{self._base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        
        return result["choices"][0]["message"]["content"]
    
    def _retrieve_context(self, query: str, category: str = None, k: int = 5) -> tuple:
        """检索相关上下文
        
        Returns:
            tuple: (context_text, sources_list)
        """
        docs = self.db.search(query, n_results=k, category=category)
        
        if not docs:
            return "暂无相关参考资料。", []
        
        # 使用Rerank重排
        if self.rerank_api.enabled:
            documents = [doc["page_content"] for doc in docs]
            scores, indices = self.rerank_api.rerank(query, documents)
            reranked_docs = [docs[i] for i in indices]
        else:
            reranked_docs = docs
        
        # 格式化上下文
        context_parts = []
        sources = []
        for i, doc in enumerate(reranked_docs, 1):
            source = doc["metadata"].get("source", "未知来源")
            filename = source.split('/')[-1].split('\\')[-1]
            content = doc["page_content"]
            context_parts.append(f"[{i}] {content}")
            sources.append({
                "id": i,
                "source": source,
                "filename": filename,
                "content": content[:200] + "..." if len(content) > 200 else content
            })
        
        return "\n\n".join(context_parts), sources
    
    def generate_speech_draft(
        self,
        topic: str,
        textbook_version: str = "人教版",
        grade_level: str = "高中",
        chapter: str = "",
        class_hours: str = "1课时"
    ) -> dict:
        """生成说课稿"""
        # 检索上下文
        query = f"{topic} {chapter} 说课稿"
        context, sources = self._retrieve_context(query, category="excellent_lesson")
        
        # 生成Prompt
        prompt = f"""请根据以下信息生成专业的地理说课稿。

## 课题信息
- 课题名称：{topic}
- 教材版本：{textbook_version}
- 学段：{grade_level}
- 章节位置：{chapter}
- 课时：{class_hours}

## 参考资料
{context}

## 生成要求
请按照以下结构生成说课稿：

1. 开场白
2. 设计理念
3. 课标分析
4. 学情分析
5. 教学目标
6. 教学重难点
7. 教学方法
8. 教学过程
9. 结束语

请确保内容专业、逻辑清晰、符合课标要求。"""
        
        content = self._call_llm(prompt)
        return {"content": content, "sources": sources}
    
    def generate_lecture_draft(
        self,
        topic: str,
        textbook_version: str = "人教版",
        grade_level: str = "高中",
        chapter: str = "",
        class_hours: str = "1课时"
    ) -> dict:
        """生成讲课稿"""
        # 检索上下文
        query = f"{topic} {chapter} 讲课稿"
        context, sources = self._retrieve_context(query, category="excellent_lesson")
        
        # 生成Prompt
        prompt = f"""请根据以下信息生成详细的地理讲课稿。

## 课题信息
- 课题名称：{topic}
- 教材版本：{textbook_version}
- 学段：{grade_level}
- 章节位置：{chapter}
- 课时：{class_hours}

## 参考资料
{context}

## 生成要求
请按照以下结构生成讲课稿：

1. 开场白
2. 情境导入
3. 探究环节1
4. 认知冲突
5. 探究环节2
6. 课堂总结
7. 课后作业
8. 结束语

请确保：
- 语言口语化、自然
- 互动性强，有师生互动
- 包含板书设计
- 时间控制合理"""
        
        content = self._call_llm(prompt)
        return {"content": content, "sources": sources}
    
    def generate_lesson_plan(
        self,
        topic: str,
        textbook_version: str = "人教版",
        grade_level: str = "高中",
        chapter: str = "",
        class_hours: str = "1课时",
        students: str = ""
    ) -> dict:
        """生成教案"""
        # 检索上下文
        query = f"{topic} {chapter} 教案"
        context, sources = self._retrieve_context(query, category="excellent_lesson")
        
        # 生成Prompt
        prompt = f"""请根据以下信息生成规范的地理教案。

## 课题信息
- 课题名称：{topic}
- 教材版本：{textbook_version}
- 学段：{grade_level}
- 章节位置：{chapter}
- 课时：{class_hours}
- 授课对象：{students}

## 参考资料
{context}

## 生成要求
请按照以下结构生成教案：

1. 基本信息
2. 课标分析
3. 设计理念
4. 课程内容分析
5. 学情分析
6. 教学目标
7. 教学重难点
8. 教法与学法
9. 教学过程
10. 教学评价

请确保内容完整、步骤清晰、可操作性强。"""
        
        content = self._call_llm(prompt)
        return {"content": content, "sources": sources}
    
    def generate_study_plan(
        self,
        topic: str,
        textbook_version: str = "人教版",
        grade_level: str = "高中",
        chapter: str = "",
        class_hours: str = "1课时"
    ) -> dict:
        """生成学案"""
        # 检索上下文
        query = f"{topic} {chapter} 学案"
        context, sources = self._retrieve_context(query, category="excellent_study")
        
        # 生成Prompt
        prompt = f"""请根据以下信息生成情境化的地理学案。

## 课题信息
- 课题名称：{topic}
- 教材版本：{textbook_version}
- 学段：{grade_level}
- 章节位置：{chapter}
- 课时：{class_hours}

## 参考资料
{context}

## 生成要求
请按照以下结构生成学案：

1. 基本信息（班级、姓名）
2. 情境启思（真实情境引入）
3. 实践活动（教具操作、小组合作）
4. 初步探索（基础探究）
5. 情境再现（认知冲突）
6. 深入学习（核心知识）
7. 课后作业
8. 情境再现（预习引导）

请确保：
- 情境设计真实、有趣
- 问题设计层次分明
- 活动设计可操作性强
- 图文结合，留有绘图空间"""
        
        content = self._call_llm(prompt)
        return {"content": content, "sources": sources}
    
    def answer_question(self, question: str) -> dict:
        """智能问答
        
        Returns:
            dict: {"answer": str, "sources": list}
        """
        # 检索上下文
        context, sources = self._retrieve_context(question)
        
        # 生成Prompt
        prompt = f"""你是一位资深的地理教育专家，擅长解答地理教学相关问题。

## 相关资料
{context}

## 问题
{question}

## 回答要求
1. 回答要专业、准确
2. 结合实际教学经验
3. 如果涉及课标要求，请引用具体条目
4. 提供可操作的建议
5. 在回答中引用相关资料时，请使用 [1]、[2] 等序号标注引用来源

请给出详细的回答："""
        
        answer = self._call_llm(prompt)
        
        return {
            "answer": answer,
            "sources": sources
        }
