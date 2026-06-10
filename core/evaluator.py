"""
GeoTeach RAG - 评测模块

提供 RAGAS 检索评测和切片质量评估。
"""

import json
from typing import List, Dict, Optional


class RAGEvaluator:
    """RAG 评测器"""
    
    def __init__(self, generator=None):
        """
        Args:
            generator: ContentGenerator 实例
        """
        self.generator = generator
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        if self.generator:
            return self.generator._call_llm(prompt)
        raise Exception("No generator available")
    
    # ==================== 检索质量评估 ====================
    
    def evaluate_retrieval_quality(self, query: str, results: list, ground_truth: list = None) -> dict:
        """
        评估检索结果质量
        
        Args:
            query: 查询文本
            results: 检索结果列表
            ground_truth: 标注的相关文档列表（可选）
            
        Returns:
            评估结果
        """
        evaluation = {
            "query": query,
            "num_results": len(results),
            "metrics": {}
        }
        
        if not results:
            evaluation["metrics"] = {
                "has_results": False,
                "score": 0
            }
            return evaluation
        
        # 基础指标
        scores = [r.get("score", 0) for r in results]
        evaluation["metrics"]["has_results"] = True
        evaluation["metrics"]["max_score"] = max(scores) if scores else 0
        evaluation["metrics"]["avg_score"] = sum(scores) / len(scores) if scores else 0
        evaluation["metrics"]["min_score"] = min(scores) if scores else 0
        
        # 多样性指标
        sources = set()
        for r in results:
            source = r.get("metadata", {}).get("source", "")
            if source:
                sources.add(source)
        evaluation["metrics"]["unique_sources"] = len(sources)
        evaluation["metrics"]["diversity"] = len(sources) / max(len(results), 1)
        
        # 如果有标注数据，计算 recall 和 precision
        if ground_truth:
            retrieved_sources = set(r.get("metadata", {}).get("source", "") for r in results)
            ground_truth_set = set(ground_truth)
            
            # Precision@k
            relevant_retrieved = retrieved_sources & ground_truth_set
            evaluation["metrics"]["precision"] = len(relevant_retrieved) / max(len(retrieved_sources), 1)
            
            # Recall@k
            evaluation["metrics"]["recall"] = len(relevant_retrieved) / max(len(ground_truth_set), 1)
            
            # MRR (Mean Reciprocal Rank)
            mrr = 0
            for i, r in enumerate(results, 1):
                if r.get("metadata", {}).get("source", "") in ground_truth_set:
                    mrr = 1.0 / i
                    break
            evaluation["metrics"]["mrr"] = mrr
        
        # 综合评分
        score = (
            evaluation["metrics"]["max_score"] * 0.3 +
            evaluation["metrics"]["diversity"] * 0.3 +
            (evaluation["metrics"].get("recall", 0.5) if ground_truth else 0.5) * 0.4
        )
        evaluation["metrics"]["overall_score"] = round(score, 3)
        
        return evaluation
    
    # ==================== 回答质量评估 ====================
    
    def evaluate_answer_quality(self, query: str, answer: str, contexts: list) -> dict:
        """
        评估回答质量（使用 LLM-as-judge）
        
        Args:
            query: 用户问题
            answer: AI 回答
            contexts: 检索到的上下文列表
            
        Returns:
            评估结果
        """
        context_text = "\n".join([f"[{i+1}] {c[:200]}" for i, c in enumerate(contexts[:5])])
        
        eval_prompt = f"""你是一个严格的评估专家。请评估以下 RAG 系统的回答质量。

用户问题：{query}

检索到的参考资料：
{context_text}

AI 回答：
{answer[:800]}

请从以下维度评估（每项 0.0-1.0 分）：

1. **faithfulness**（忠实度）：回答是否忠实于参考资料，没有编造信息？
2. **relevance**（相关性）：回答是否直接回答了用户的问题？
3. **completeness**（完整性）：回答是否涵盖了问题的各个方面？
4. **clarity**（清晰度）：回答是否清晰易懂？

只返回JSON格式：
{{"faithfulness": 0.8, "relevance": 0.9, "completeness": 0.7, "clarity": 0.85}}"""
        
        try:
            result = self._call_llm(eval_prompt)
            scores = self._parse_json_response(result)
            
            if scores:
                avg = (
                    scores.get("faithfulness", 0.5) * 0.35 +
                    scores.get("relevance", 0.5) * 0.3 +
                    scores.get("completeness", 0.5) * 0.2 +
                    scores.get("clarity", 0.5) * 0.15
                )
                scores["overall_score"] = round(avg, 3)
                scores["grade"] = self._score_to_grade(avg)
                return scores
        except Exception as e:
            print(f"回答评估失败: {e}")
        
        return {"faithfulness": 0.5, "relevance": 0.5, "completeness": 0.5, "clarity": 0.5, "overall_score": 0.5, "grade": "C"}
    
    # ==================== 切片质量评估 ====================
    
    def evaluate_chunk_quality(self, chunks: list) -> dict:
        """
        评估切片质量
        
        Args:
            chunks: 切片列表
            
        Returns:
            切片质量评估结果
        """
        if not chunks:
            return {"count": 0, "quality": "no_chunks"}
        
        lengths = [len(c.get("page_content", "")) for c in chunks]
        
        # 长度统计
        avg_length = sum(lengths) / len(lengths)
        min_length = min(lengths)
        max_length = max(lengths)
        
        # 长度分布
        distribution = {
            "0-99": sum(1 for l in lengths if l < 100),
            "100-299": sum(1 for l in lengths if 100 <= l < 300),
            "300-499": sum(1 for l in lengths if 300 <= l < 500),
            "500-999": sum(1 for l in lengths if 500 <= l < 1000),
            "1000+": sum(1 for l in lengths if l >= 1000)
        }
        
        # 质量评分
        # 理想长度：300-700 字符
        ideal_count = sum(1 for l in lengths if 300 <= l <= 700)
        quality_score = ideal_count / max(len(lengths), 1)
        
        return {
            "count": len(chunks),
            "avg_length": round(avg_length, 1),
            "min_length": min_length,
            "max_length": max_length,
            "distribution": distribution,
            "quality_score": round(quality_score, 3),
            "quality_grade": self._score_to_grade(quality_score)
        }
    
    # ==================== 工具函数 ====================
    
    def _parse_json_response(self, text: str) -> dict:
        """从 LLM 响应中提取 JSON"""
        try:
            json_match = text[text.find('{'):text.rfind('}')+1]
            return json.loads(json_match)
        except Exception:
            return None
    
    def _score_to_grade(self, score: float) -> str:
        """分数转等级"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B"
        elif score >= 0.6:
            return "C"
        elif score >= 0.5:
            return "D"
        else:
            return "F"


class ChunkOptimizer:
    """切片优化器"""
    
    def __init__(self, evaluator: RAGEvaluator = None):
        self.evaluator = evaluator or RAGEvaluator()
    
    def compare_strategies(self, text: str, strategies: list = None) -> dict:
        """
        对比不同切片策略的效果
        
        Args:
            text: 测试文本
            strategies: 切片策略列表
            
        Returns:
            各策略的对比结果
        """
        from core.chunking import split_text
        
        if not strategies:
            strategies = [
                {"chunk_size": 200, "overlap": 20, "name": "小切片"},
                {"chunk_size": 500, "overlap": 50, "name": "中切片"},
                {"chunk_size": 1000, "overlap": 100, "name": "大切片"},
            ]
        
        results = []
        for strategy in strategies:
            chunks = split_text(text, strategy)
            chunk_dicts = [{"page_content": c} for c in chunks]
            quality = self.evaluator.evaluate_chunk_quality(chunk_dicts)
            quality["strategy_name"] = strategy.get("name", "unknown")
            quality["chunk_size"] = strategy.get("chunk_size", 500)
            quality["overlap"] = strategy.get("overlap", 50)
            results.append(quality)
        
        # 找出最佳策略
        best = max(results, key=lambda x: x.get("quality_score", 0))
        
        return {
            "strategies": results,
            "best_strategy": best.get("strategy_name"),
            "best_score": best.get("quality_score", 0)
        }
