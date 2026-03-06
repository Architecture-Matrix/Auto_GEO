# -*- mode: python ; coding: utf-8 -*-
"""
AutoGeo 单一 EXE 打包配置
版本: v3.1.4
说明: 打包后端 + 前端静态文件成单一可执行文件
修复: 修复 collect_data_files 格式问题
"""

import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 配置文件
        ('config.py', '.'),
        # 数据模型和API
        ('database', 'database'),
        ('api', 'api'),
        ('services', 'services'),
        ('schemas', 'schemas'),
        # 静态资源（前端构建产物）
        ('static', 'static'),
    ],
    hiddenimports=[
        # 核心框架
        'playwright.async_api',
        'playwright.sync_api',
        'playwright',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'fastapi.responses',
        'fastapi.websockets',
        'fastapi.staticfiles',
        'sqlalchemy',
        'sqlalchemy.dialects',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.ext',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.orm',
        # 日志和工具
        'loguru',
        'cryptography',
        'httpx',
        'curl_cffi',
        'curl_cffi.requests',
        'websockets',
        'apscheduler',
        'pydantic',
        'pydantic.dataclasses',
        'aiofiles',
        'jinja2',
        'python_dotenv',
        # Windows API
        'win32api',
        'win32con',
        'win32gui',
        'win32crypt',
        'pywintypes',
        # 其他
        'dataclasses',
        'pathlib',
        'typing_extensions',
        'email_validator',
        'markdown_it',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest_asyncio',
        'IPython',
        'ipdb',
        'black',
        'flake8',
        'mypy',
        'ruff',
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
    ],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AutoGeoBackend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
