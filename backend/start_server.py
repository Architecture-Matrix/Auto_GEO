# -*- coding: utf-8 -*-
"""
AutoGeo 后端启动脚本（Windows兼容版）

艹！这个SB脚本必须在导入任何异步模块之前设置事件循环策略
否则Playwright在Windows下会报NotImplementedError
"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# ==================== 关键：必须在最开始设置事件循环策略 ====================
# 艹！Windows下必须用ProactorEventLoop支持subprocess，而Playwright需要fork子进程
# SelectorEventLoop在Windows下不支持subprocess，会报NotImplementedError
# 这个策略必须在创建事件循环之前设置，必须在导入uvicorn之前执行！
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("[OK] Windows ProactorEventLoopPolicy set (subprocess supported)")
# ==================== 设置完毕 ====================

import uvicorn

if __name__ == "__main__":
    from backend.config import HOST, PORT, RELOAD, APP_NAME, APP_VERSION

    print(f"[START] Starting {APP_NAME} v{APP_VERSION}...")
    print(f"[ADDR] http://{HOST}:{PORT}")
    print(f"[RELOAD] {RELOAD}")

    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=RELOAD, log_level="info")
