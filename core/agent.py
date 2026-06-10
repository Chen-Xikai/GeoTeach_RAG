"""
GeoTeach RAG - 智能 Agent 模块

实现自主评估、多轮检索决策、Query 改写等智能行为。
"""

import json
from typing import List, Dict, Optional


class RAGAgent:
    """RAG 智能 Agent"""
    
    def __init__(self, generator):
        """
        Args:
            generator: ContentGenerator 实例
        """
        self.generator = generator
        self.max_retrieval_rounds = 2  # 最大检索轮数
        self.retrieval_threshold = 0.5  # 检索质量阈值
        self.answer_threshold = 0.6  # 回答质量阈值
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        return self.generator._call_llm(prompt)
    
    def _call_llm_with_messages(self, messages: list) -> str:
        """使用消息列表调用 LLM"""
        return self.generator._call_llm_with_messages(messages)
    
    # ==================== Query 改写 ====================
    
    def rewrite_query(self, original_query: str, history: list = None) -> List[str]:
        """
        根据对话历史改写 query，生成多个检索查询
        
        Args:
            original_query: 原始查询
            history: 对话历史
            
        Returns:
            改写后的查询列表
        """
        history_text = ""
        if history:
            history_text = "\n对话历史：\n" + "\n".join(
                f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content'][:100]}"
                for m in history[-6:]
            )
        
        prompt = f"""你是一个地理教学检索助手。请根据用户的原始查询和对话历史，生成1-3个改写后的检索查询，以提高检索质量。

原始查询：{original_query}
{history_text}

要求：
1. 保持地理学科专业性
2. 如果查询指代不明（如"第3点"），结合历史补充完整
3. 生成的查询应该更具体、更精确
4. 每个查询一行

请直接输出改写后的查询（每行一个）："""
        
        result = self._call_llm(prompt)
        queries = [q.strip() for q in result.split('\n') if q.strip() and len(q.strip()) > 2]
        
        # 确保原始查询在列表中
        if original_query not in queries:
            queries.insert(0, original_query)
        
        return queries[:3]  # 最多3个查询
    
    # ==================== 检索质量评估 ====================
    
    def evaluate_retrieval(self, query: str, results: list) -> dict:
        """
        评估检索结果质量
        
        Returns:
            {"sufficient": bool, "reason": str, "score": float}
        """
        if not results:
            return {"sufficient": False, "reason": "no_results", "score": 0}
        
        # 检查最高相似度
        scores = [r.get("score", 0) for r in results]
        max_score = max(scores) if scores else 0
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 检查结果多样性
        sources = set(r.get("metadata", {}).get("source", "") for r in results)
        source_count = len(sources)
        
        # 综合评分
        score = (max_score * 0.4 + avg_score * 0.3 + min(source_count / 3, 1) * 0.3)
        
        if max_score < self.retrieval_threshold:
            return {"sufficient": False, "reason": "low_relevance", "score": score}
        
        if source_count < 2 and len(results) > 2:
            return {"sufficient": False, "reason": "low_diversity", "score": score}
        
        return {"sufficient": True, "reason": "ok", "score": score}
    
    # ==================== 回答质量评估 ====================
    
    def evaluate_answer(self, query: str, context: str, answer: str) -> dict:
        """
        评估回答质量
        
        Returns:
            {"faithfulness": float, "relevance": float, "sufficient": bool}
        """
        eval_prompt = f"""请评估以下回答的质量，返回JSON格式。

问题：{query}

参考资料摘要：{context[:500]}...

回答：{answer[:500]}...

评估标准：
1. faithfulness（忠实度）：回答是否基于参考资料，而非编造？(0.0-1.0)
2. relevance（相关性）：回答是否回答了用户的问题？(0.0-1.0)
3. completeness（完整性）：回答是否全面？(0.0-1.0)

只返回JSON，不要其他内容：
{{"faithfulness": 0.8, "relevance": 0.9, "completeness": 0.7}}"""
        
        try:
            result = self._call_llm(eval_prompt)
            # 提取JSON
            json_match = result[result.find('{'):result.rfind('}')+1]
            scores = json.loads(json_match)
            
            avg_score = (
                scores.get("faithfulness", 0.5) * 0.4 +
                scores.get("relevance", 0.5) * 0.35 +
                scores.get("completeness", 0.5) * 0.25
            )
            
            return {
                "faithfulness": scores.get("faithfulness", 0.5),
                "relevance": scores.get("relevance", 0.5),
                "completeness": scores.get("completeness", 0.5),
                "avg_score": avg_score,
                "sufficient": avg_score >= self.answer_threshold
            }
        except Exception as e:
            return {"faithfulness": 0.5, "relevance": 0.5, "completeness": 0.5, "avg_score": 0.5, "sufficient": True}
    
    # ==================== 上下文压缩 ====================
    
    def compress_history(self, history: list, max_messages: int = 10) -> list:
        """
        压缩对话历史以适应 token 限制
        
        Args:
            history: 完整对话历史
            max_messages: 最大保留消息数
            
        Returns:
            压缩后的对话历史
        """
        if len(history) <= max_messages:
            return history
        
        # 保留最近 max_messages 条
        recent = history[-max_messages:]
        return recent
    
    # ==================== 多轮检索决策 ====================
    
    def should_retrieve_more(self, retrieval_result: dict, round_num: int) -> bool:
        """
        决策是否需要更多检索
        
        Args:
            retrieval_result: 检索评估结果
            round_num: 当前检索轮数
            
        Returns:
            是否需要更多检索
        """
        if round_num >= self.max_retrieval_rounds:
            return False
        
        if retrieval_result.get("sufficient", True):
            return False
        
        return True
    
    def should_regenerate(self, answer_result: dict, round_num: int) -> bool:
        """
        决策是否需要重新生成回答
        
        Args:
            answer_result: 回答评估结果
            round_num: 当前生成轮数
            
        Returns:
            是否需要重新生成
        """
        if round_num >= 2:  # 最多生成2次
            return False
        
        if answer_result.get("sufficient", True):
            return False
        
        return True
