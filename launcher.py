# -*- coding: utf-8 -*-
"""
GeoTeach RAG - 启动管理器

提供GUI界面管理服务的启动、停止、状态检查。
用法: python launcher.py
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import requests
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config.version import VERSION, PROJECT_NAME


class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.web_process = None
        self.mcp_process = None
    
    def is_web_running(self) -> bool:
        try:
            r = requests.get("http://127.0.0.1:9767/api/system/health", timeout=2)
            return r.status_code == 200
        except Exception:
            return False
    
    def is_mcp_running(self) -> bool:
        try:
            r = requests.get("http://127.0.0.1:9766/health", timeout=2)
            return r.status_code == 200
        except Exception:
            return False
    
    def start_web(self):
        if self.is_web_running():
            return True
        try:
            self.web_process = subprocess.Popen(
                [sys.executable, "-m", "servers.web"],
                cwd=str(ROOT),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(3)
            return self.is_web_running()
        except Exception as e:
            print(f"启动Web服务失败: {e}")
            return False
    
    def start_mcp(self):
        if self.is_mcp_running():
            return True
        try:
            self.mcp_process = subprocess.Popen(
                [sys.executable, "-m", "servers.mcp"],
                cwd=str(ROOT),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(3)
            return self.is_mcp_running()
        except Exception as e:
            print(f"启动MCP服务失败: {e}")
            return False
    
    def stop_web(self):
        if self.web_process:
            try:
                self.web_process.terminate()
                self.web_process = None
            except Exception:
                pass
        # 尝试通过端口杀进程
        try:
            subprocess.run(["taskkill", "/F", "/FI", "WINDOWTITLE eq *servers.web*"], 
                         capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass
    
    def stop_mcp(self):
        if self.mcp_process:
            try:
                self.mcp_process.terminate()
                self.mcp_process = None
            except Exception:
                pass
        try:
            subprocess.run(["taskkill", "/F", "/FI", "WINDOWTITLE eq *servers.mcp*"], 
                         capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass
    
    def stop_all(self):
        self.stop_web()
        self.stop_mcp()


class LauncherGUI:
    """启动器GUI"""
    
    def __init__(self):
        self.manager = ServiceManager()
        self.root = tk.Tk()
        self.root.title(f"{PROJECT_NAME} 启动管理器")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # 设置图标和样式
        self.setup_ui()
        
        # 初始状态检查
        self.update_status()
    
    def setup_ui(self):
        """设置UI"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text=PROJECT_NAME, font=("Helvetica", 18, "bold"))
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="地理教学AI助手", font=("Helvetica", 10))
        subtitle_label.pack(pady=(0, 20))
        
        # 状态框架
        status_frame = ttk.LabelFrame(main_frame, text="服务状态", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Web服务状态
        web_frame = ttk.Frame(status_frame)
        web_frame.pack(fill=tk.X, pady=5)
        ttk.Label(web_frame, text="Web服务 (端口 9767):").pack(side=tk.LEFT)
        self.web_status_label = ttk.Label(web_frame, text="检查中...", foreground="gray")
        self.web_status_label.pack(side=tk.RIGHT)
        
        # MCP服务状态
        mcp_frame = ttk.Frame(status_frame)
        mcp_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mcp_frame, text="MCP服务 (端口 9766):").pack(side=tk.LEFT)
        self.mcp_status_label = ttk.Label(mcp_frame, text="检查中...", foreground="gray")
        self.mcp_status_label.pack(side=tk.RIGHT)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 启动所有按钮
        self.start_all_btn = ttk.Button(button_frame, text="启动所有服务", command=self.start_all)
        self.start_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 停止所有按钮
        self.stop_all_btn = ttk.Button(button_frame, text="停止所有服务", command=self.stop_all)
        self.stop_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 刷新按钮
        self.refresh_btn = ttk.Button(button_frame, text="刷新状态", command=self.update_status)
        self.refresh_btn.pack(side=tk.LEFT)
        
        # 单独控制框架
        control_frame = ttk.LabelFrame(main_frame, text="单独控制", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Web服务控制
        web_ctrl_frame = ttk.Frame(control_frame)
        web_ctrl_frame.pack(fill=tk.X, pady=5)
        ttk.Label(web_ctrl_frame, text="Web服务:").pack(side=tk.LEFT)
        ttk.Button(web_ctrl_frame, text="启动", command=self.start_web).pack(side=tk.LEFT, padx=5)
        ttk.Button(web_ctrl_frame, text="停止", command=self.stop_web).pack(side=tk.LEFT, padx=5)
        ttk.Button(web_ctrl_frame, text="打开", command=self.open_web).pack(side=tk.LEFT, padx=5)
        
        # MCP服务控制
        mcp_ctrl_frame = ttk.Frame(control_frame)
        mcp_ctrl_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mcp_ctrl_frame, text="MCP服务:").pack(side=tk.LEFT)
        ttk.Button(mcp_ctrl_frame, text="启动", command=self.start_mcp).pack(side=tk.LEFT, padx=5)
        ttk.Button(mcp_ctrl_frame, text="停止", command=self.stop_mcp).pack(side=tk.LEFT, padx=5)
        
        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 版本信息
        version_label = ttk.Label(main_frame, text=f"v{VERSION} | 基于 Milvus Lite", font=("Helvetica", 8))
        version_label.pack(pady=(10, 0))
    
    def log(self, message: str):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def update_status(self):
        """更新状态显示"""
        # 检查Web服务
        if self.manager.is_web_running():
            self.web_status_label.config(text="运行中", foreground="green")
        else:
            self.web_status_label.config(text="未运行", foreground="red")
        
        # 检查MCP服务
        if self.manager.is_mcp_running():
            self.mcp_status_label.config(text="运行中", foreground="green")
        else:
            self.mcp_status_label.config(text="未运行", foreground="red")
    
    def start_web(self):
        """启动Web服务"""
        self.log("正在启动Web服务...")
        threading.Thread(target=self._start_web_thread, daemon=True).start()
    
    def _start_web_thread(self):
        if self.manager.start_web():
            self.log("Web服务启动成功!")
        else:
            self.log("Web服务启动失败!")
        self.root.after(0, self.update_status)
    
    def start_mcp(self):
        """启动MCP服务"""
        self.log("正在启动MCP服务...")
        threading.Thread(target=self._start_mcp_thread, daemon=True).start()
    
    def _start_mcp_thread(self):
        if self.manager.start_mcp():
            self.log("MCP服务启动成功!")
        else:
            self.log("MCP服务启动失败!")
        self.root.after(0, self.update_status)
    
    def start_all(self):
        """启动所有服务"""
        self.log("正在启动所有服务...")
        threading.Thread(target=self._start_all_thread, daemon=True).start()
    
    def _start_all_thread(self):
        web_ok = self.manager.start_web()
        mcp_ok = self.manager.start_mcp()
        
        if web_ok:
            self.log("Web服务启动成功!")
        else:
            self.log("Web服务启动失败!")
        
        if mcp_ok:
            self.log("MCP服务启动成功!")
        else:
            self.log("MCP服务启动失败!")
        
        self.root.after(0, self.update_status)
    
    def stop_web(self):
        """停止Web服务"""
        self.manager.stop_web()
        self.log("Web服务已停止")
        self.root.after(1000, self.update_status)
    
    def stop_mcp(self):
        """停止MCP服务"""
        self.manager.stop_mcp()
        self.log("MCP服务已停止")
        self.root.after(1000, self.update_status)
    
    def stop_all(self):
        """停止所有服务"""
        self.manager.stop_all()
        self.log("所有服务已停止")
        self.root.after(1000, self.update_status)
    
    def open_web(self):
        """打开Web界面"""
        import webbrowser
        webbrowser.open("http://localhost:9767")
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    launcher = LauncherGUI()
    launcher.run()
