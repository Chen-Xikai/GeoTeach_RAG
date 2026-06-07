#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""循环测试脚本 - 测试文件上传功能"""

import os
import sys
import requests
import time
from datetime import datetime

# 配置
API_BASE = "http://127.0.0.1:9767/api"
LOG_FILE = "TEST_LOG.md"

def log_message(message, level="INFO"):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def test_health():
    """测试健康检查"""
    try:
        r = requests.get(f"{API_BASE}/system/health", timeout=10)
        return r.status_code == 200
    except Exception as e:
        log_message(f"健康检查失败: {e}", "ERROR")
        return False

def test_upload(category="textbook"):
    """测试文件上传"""
    try:
        # 创建测试文件
        test_content = f"测试文档内容 - {datetime.now()}"
        test_file = f"data/test_upload_{category}.txt"
        os.makedirs("data", exist_ok=True)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # 上传文件
        with open(test_file, "rb") as f:
            r = requests.post(
                f"{API_BASE}/documents/import",
                files={"file": (f"test_{category}.txt", f, "text/plain")},
                params={"category": category, "use_multimodal": False, "chunk_size": 200, "chunk_overlap": 30},
                timeout=60
            )
        
        result = r.json()
        success = result.get("status") == "success"
        
        # 清理测试文件
        os.remove(test_file)
        
        return success, result
    except Exception as e:
        log_message(f"上传测试失败: {e}", "ERROR")
        return False, {"error": str(e)}

def test_document_list():
    """测试文档列表"""
    try:
        r = requests.get(f"{API_BASE}/documents", timeout=10)
        result = r.json()
        return len(result.get("documents", []))
    except Exception as e:
        log_message(f"文档列表查询失败: {e}", "ERROR")
        return -1

def test_catalog():
    """测试教材目录"""
    try:
        # 测试初中
        r = requests.get(f"{API_BASE}/catalog/grades?level=初中", timeout=10)
        junior_grades = r.json().get("grades", [])
        
        # 测试高中
        r = requests.get(f"{API_BASE}/catalog/grades?level=高中", timeout=10)
        senior_grades = r.json().get("grades", [])
        
        return len(junior_grades) > 0 and len(senior_grades) > 0
    except Exception as e:
        log_message(f"教材目录查询失败: {e}", "ERROR")
        return False

def run_test_cycle(cycle_num):
    """运行一次测试循环"""
    log_message(f"=== 第{cycle_num}次测试 ===")
    
    results = {
        "cycle": cycle_num,
        "health": False,
        "upload_textbook": False,
        "upload_curriculum": False,
        "upload_lesson_plan": False,
        "doc_count": 0,
        "catalog": False
    }
    
    # 测试1: 健康检查
    results["health"] = test_health()
    status = "通过" if results["health"] else "失败"
    log_message(f"健康检查: {status}")
    
    if not results["health"]:
        return results
    
    # 测试2: 文件上传（不同分类）
    categories = ["textbook", "curriculum", "lesson_plan"]
    for cat in categories:
        success, result = test_upload(cat)
        results[f"upload_{cat}"] = success
        status = "成功" if success else "失败"
        log_message(f"上传到 {cat}: {status}")
        if not success:
            log_message(f"  错误详情: {result}", "ERROR")
    
    # 测试3: 文档列表
    doc_count = test_document_list()
    results["doc_count"] = doc_count
    log_message(f"文档数量: {doc_count}")
    
    # 测试4: 教材目录
    results["catalog"] = test_catalog()
    status = "正常" if results["catalog"] else "异常"
    log_message(f"教材目录: {status}")
    
    return results

def main():
    """主函数"""
    log_message("=" * 50)
    log_message("开始20次循环测试")
    log_message("=" * 50)
    
    all_results = []
    
    for i in range(1, 21):
        results = run_test_cycle(i)
        all_results.append(results)
        
        # 记录到日志文件
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n### 第{i}次检查\n")
            f.write(f"- 健康检查: {'PASS' if results['health'] else 'FAIL'}\n")
            f.write(f"- 上传到textbook: {'PASS' if results['upload_textbook'] else 'FAIL'}\n")
            f.write(f"- 上传到curriculum: {'PASS' if results['upload_curriculum'] else 'FAIL'}\n")
            f.write(f"- 上传到lesson_plan: {'PASS' if results['upload_lesson_plan'] else 'FAIL'}\n")
            f.write(f"- 文档数量: {results['doc_count']}\n")
            f.write(f"- 教材目录: {'PASS' if results['catalog'] else 'FAIL'}\n")
        
        # 等待一段时间再进行下一次测试
        if i < 20:
            time.sleep(2)
    
    # 汇总结果
    log_message("=" * 50)
    log_message("测试汇总")
    log_message("=" * 50)
    
    success_count = sum(1 for r in all_results if all([r["health"], r["upload_textbook"], r["upload_curriculum"], r["upload_lesson_plan"], r["catalog"]]))
    log_message(f"成功次数: {success_count}/20")
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n## 测试汇总\n")
        f.write(f"- 成功次数: {success_count}/20\n")
        f.write(f"- 最终文档数量: {all_results[-1]['doc_count']}\n")

if __name__ == "__main__":
    main()
