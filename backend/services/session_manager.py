# -*- coding: utf-8 -*-
"""
安全会话管理器
管理AI平台授权会话的加密存储和加载
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from playwright.async_api import async_playwright

from backend.config import DATA_DIR, ENCRYPTION_KEY, DEFAULT_USER_AGENT, AI_PLATFORMS, BROWSER_ARGS
from backend.services.crypto import CryptoService


class SecureSessionManager:
    """
    安全的会话管理器
    负责会话的加密存储、加载和验证
    """

    def __init__(self):
        """
        初始化会话管理器
        """
        self._crypto = CryptoService(ENCRYPTION_KEY)
        self._session_dir = DATA_DIR / "sessions"
        self._session_dir.mkdir(exist_ok=True)

    def _get_session_file_path(self, user_id: int, project_id: int, platform: str) -> Path:
        """
        获取会话文件路径

        Args:
            user_id: 用户ID
            project_id: 项目ID
            platform: AI平台标识

        Returns:
            会话文件路径
        """
        # 生成安全的文件名，包含用户ID和项目ID
        safe_user_id = str(user_id).zfill(8)
        safe_project_id = str(project_id).zfill(8)
        file_name = f"session_{safe_user_id}_{safe_project_id}_{platform}.enc"
        return self._session_dir / file_name

    async def save_session(
        self, user_id: int, project_id: int, platform: str, storage_state: Dict[str, Any], is_new_login: bool = False
    ) -> bool:
        """
        保存会话状态（加密）

        Args:
            user_id: 用户ID
            project_id: 项目ID
            platform: AI平台标识
            storage_state: Playwright存储状态
            is_new_login: 是否为新登录（如果是，将强制更新created_at）

        Returns:
            是否保存成功
        """
        try:
            # 验证参数
            if not all([user_id, project_id, platform, storage_state]):
                logger.error("保存会话参数不完整")
                return False

            # 添加/更新会话时间戳
            current_time = datetime.now().isoformat()
            storage_state["last_modified"] = current_time

            # 如果是新登录，或者没有created_at，则更新/设置created_at
            if is_new_login or "created_at" not in storage_state:
                storage_state["created_at"] = current_time
                logger.info(f"更新会话创建时间: platform={platform}, time={current_time}")
            else:
                # 确保已有created_at保留下来
                # 注意：如果storage_state是全新的对象且不包含created_at，上面的if会处理它
                pass

            # 序列化存储状态
            storage_json = json.dumps(storage_state, ensure_ascii=False)

            # 加密数据
            encrypted_data = self._crypto.encrypt(storage_json)

            # 保存到文件
            file_path = self._get_session_file_path(user_id, project_id, platform)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(encrypted_data)

            logger.info(f"会话保存成功: user_id={user_id}, project_id={project_id}, platform={platform}")
            return True

        except Exception as e:
            logger.error(f"保存会话失败: {e}")
            return False

    async def load_session(
        self, user_id: int, project_id: int, platform: str, validate: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        加载会话状态（解密）

        Args:
            user_id: 用户ID
            project_id: 项目ID
            platform: AI平台标识
            validate: 是否验证会话有效性

        Returns:
            解密后的存储状态，失败返回None
        """
        try:
            # 验证参数
            if not all([user_id, project_id, platform]):
                logger.error("加载会话参数不完整")
                return None

            # 读取文件
            file_path = self._get_session_file_path(user_id, project_id, platform)
            if not file_path.exists():
                logger.warning(f"会话文件不存在: {file_path}")
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                encrypted_data = f.read()

            # 解密数据
            decrypted_json = self._crypto.decrypt(encrypted_data)
            if not decrypted_json:
                logger.error("会话解密失败")
                return None

            # 反序列化
            storage_state = json.loads(decrypted_json)

            # 验证会话有效性
            if validate:
                session_status = await self.validate_session(
                    user_id=user_id, project_id=project_id, platform=platform, storage_state=storage_state
                )

                if session_status != "valid":
                    logger.warning(
                        f"会话无效: {session_status}, user_id={user_id}, project_id={project_id}, platform={platform}"
                    )
                    return None

            logger.info(f"会话加载成功: user_id={user_id}, project_id={project_id}, platform={platform}")
            return storage_state

        except Exception as e:
            logger.error(f"加载会话失败: {e}")
            return None

    async def validate_session(
        self, user_id: int, project_id: int, platform: str, storage_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        验证会话有效性（心跳检测）

        Args:
            user_id: 用户ID
            project_id: 项目ID
            platform: AI平台标识
            storage_state: 存储状态（可选，如不提供则加载）

        Returns:
            会话状态: "valid", "expiring", "invalid"
        """
        try:
            # 如果没有提供存储状态，先加载
            if storage_state is None:
                storage_state = await self.load_session(
                    user_id=user_id, project_id=project_id, platform=platform, validate=False
                )

            if not storage_state:
                return "invalid"

            # 检查会话时间
            last_modified = storage_state.get("last_modified")
            if last_modified:
                try:
                    last_modified_time = datetime.fromisoformat(last_modified)
                    now = datetime.now()
                    age = now - last_modified_time

                    # 会话超过7天视为无效
                    if age > timedelta(days=7):
                        logger.warning(f"会话已过期: {age}, platform={platform}")
                        return "invalid"

                    # 会话超过5天视为临近过期
                    if age > timedelta(days=5):
                        logger.warning(f"会话临近过期: {age}, platform={platform}")
                        return "expiring"
                except Exception as e:
                    logger.error(f"解析会话时间失败: {e}")

            # 执行心跳检测（浏览器验证）
            heartbeat_valid = await self._perform_heartbeat_check(platform=platform, storage_state=storage_state)

            if not heartbeat_valid:
                logger.warning(f"心跳检测失败: platform={platform}")
                return "invalid"

            # 更新会话时间
            storage_state["last_modified"] = datetime.now().isoformat()
            await self.save_session(
                user_id=user_id, project_id=project_id, platform=platform, storage_state=storage_state
            )

            return "valid"

        except Exception as e:
            logger.error(f"验证会话失败: {e}")
            return "invalid"

    async def _perform_heartbeat_check(self, platform: str, storage_state: Dict[str, Any]) -> bool:
        """
        执行心跳检测（打开平台页面验证会话）
        优化：增加超时时间、添加重试机制、优化加载策略、支持自动安装浏览器

        Args:
            platform: AI平台标识
            storage_state: 存储状态

        Returns:
            心跳检测是否成功
        """
        max_retries = 2
        retry_count = 0

        while retry_count <= max_retries:
            try:
                # 获取平台配置
                platform_config = AI_PLATFORMS.get(platform)
                if not platform_config:
                    logger.error(f"未知平台: {platform}")
                    return False

                platform_url = platform_config.get("url", "")
                if not platform_url:
                    logger.error(f"平台URL未配置: {platform}")
                    return False

                # 启动浏览器
                async with async_playwright() as p:
                    # 1. 尝试查找本地 Chrome 路径
                    chrome_paths = [
                        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                    ]

                    # Mac OS 支持
                    if sys.platform == "darwin":
                        chrome_paths = [
                            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                        ]

                    executable_path = None
                    for path in chrome_paths:
                        if os.path.exists(path):
                            executable_path = path
                            logger.info(f"✅ [SessionManager] 找到本地 Chrome 浏览器: {path}")
                            break

                    # 准备启动参数
                    # 策略：前几次尝试使用headless=True，最后一次尝试headless=False（如果允许）
                    # 为了不打扰用户，默认尽量headless。但如果之前的尝试失败了，尝试无头模式可能会继续失败
                    # 这里保持 headless=True，除非特定平台需要

                    use_headless = True
                    # 如果是重试且不是第一次，尝试使用非无头模式（如果这是最后一次机会）
                    if retry_count == max_retries:
                        # 最后的挣扎：尝试显示浏览器窗口，看看是否能绕过检测
                        # 但为了避免突然弹出窗口吓到用户，我们只在特定错误下这样做
                        # 暂时还是保持True，或者可以改为False
                        # use_headless = False
                        pass

                    launch_options = {"headless": use_headless, "args": BROWSER_ARGS, "timeout": 30000}

                    if executable_path:
                        launch_options["executable_path"] = executable_path

                    # 启动浏览器
                    browser = None
                    try:
                        browser = await p.chromium.launch(**launch_options)
                    except Exception as browser_error:
                        error_msg = str(browser_error)
                        logger.warning(f"浏览器启动失败: {error_msg}")

                        # 如果指定了executable_path但失败，尝试回退到内置浏览器
                        if executable_path:
                            launch_options.pop("executable_path", None)
                            try:
                                browser = await p.chromium.launch(**launch_options)
                            except Exception as inner_error:
                                logger.error(f"内置浏览器启动失败: {inner_error}")

                        # 自动安装逻辑
                        if not browser and "Executable doesn't exist" in str(error_msg):
                            logger.warning("检测到浏览器缺失，尝试自动安装...")
                            try:
                                logger.info("正在执行: playwright install chromium")
                                process = await asyncio.create_subprocess_exec(
                                    sys.executable,
                                    "-m",
                                    "playwright",
                                    "install",
                                    "chromium",
                                    stdout=asyncio.subprocess.PIPE,
                                    stderr=asyncio.subprocess.PIPE,
                                )
                                stdout, stderr = await process.communicate()

                                if process.returncode == 0:
                                    logger.info("浏览器安装成功，重试启动...")
                                    browser = await p.chromium.launch(**launch_options)
                                else:
                                    logger.error(f"自动安装失败: {stderr.decode()}")
                            except Exception as install_error:
                                logger.error(f"自动安装过程异常: {install_error}")

                        if not browser:
                            raise Exception(f"无法启动浏览器: {error_msg}")

                    try:
                        # 创建上下文并加载存储状态
                        context = await browser.new_context(storage_state=storage_state, user_agent=DEFAULT_USER_AGENT)
                        page = await context.new_page()

                        # 导航到平台页面
                        # 使用 domcontentloaded 代替 load，加快响应速度
                        try:
                            await page.goto(platform_url, wait_until="domcontentloaded", timeout=60000)
                        except Exception as nav_error:
                            logger.warning(f"页面导航超时或失败: {nav_error}, platform={platform}")
                            # 即使导航超时，也可能已经加载了部分内容，继续检查

                        # 等待关键元素出现（输入框或登录按钮）
                        # 修复：增加超时到30秒，给页面更多加载时间
                        try:
                            await page.wait_for_selector(
                                "textarea, input[type='text'], [contenteditable='true'], [class*='login'], button",
                                timeout=30000,  # 修复：从15秒增加到30秒
                                state="visible",
                            )
                        except Exception:
                            pass

                        await asyncio.sleep(2)

                        # 检查是否需要登录
                        # 增强：使用与 AuthService 一致的精确检测逻辑
                        login_indicators = [
                            "[class*='login']",
                            "[id*='login']",
                            "[class*='auth']",
                            "[id*='auth']",
                            "button:has-text('登录')",
                            "button:has-text('Sign in')",
                            "button:has-text('立即登录')",
                            "div:has-text('登录'):visible",
                        ]

                        # 针对特定平台的额外检测
                        if platform == "doubao":
                            login_indicators.extend(
                                [
                                    "[data-testid*='login']",
                                    "header button:has-text('登录')",
                                    "div[class*='right'] :text('登录')",
                                ]
                            )

                        if platform == "qianwen":
                            login_indicators.extend(
                                ["div[class*='login']", "div[class*='sign-in']", "[class*='auth-btn']"]
                            )

                        has_login = False
                        for indicator in login_indicators:
                            try:
                                # 同样增加文本长度检查，防止误判
                                if "text=" in indicator or "has-text" in indicator:
                                    elements = await page.query_selector_all(indicator)
                                    for el in elements:
                                        if await el.is_visible():
                                            text = await el.inner_text()
                                            if text and len(text.strip()) < 10 and ("登录" in text or "Sign" in text):
                                                has_login = True
                                                logger.debug(f"检测到登录元素: {indicator} ('{text}')")
                                                break
                                else:
                                    element = await page.query_selector(indicator)
                                    if element and await element.is_visible():
                                        has_login = True
                                        logger.debug(f"检测到登录元素: {indicator}")
                                        break
                            except Exception:
                                continue
                            if has_login:
                                break

                        if has_login:
                            # 再次确认：有些时候可能是未登录态的横幅，但如果能找到输入框，其实是已登录的
                            # 比如千问，未登录时也有输入框。所以单纯有输入框不能证明已登录。
                            # 必须是：没有登录按钮 且 有输入框

                            # 这里的逻辑是：只要有登录按钮，就一定是未登录/失效
                            logger.warning(f"心跳检测失败: 需要登录, platform={platform}")
                            return False

                        # 检查是否能找到输入框（说明已登录）
                        input_selectors = [
                            "textarea[placeholder*='输入']",
                            "textarea[placeholder*='提问']",
                            "[contenteditable='true']",
                            "textarea",
                        ]

                        has_input = False
                        for selector in input_selectors:
                            try:
                                element = await page.query_selector(selector)
                                if element and await element.is_visible():
                                    has_input = True
                                    break
                            except Exception:
                                continue

                        if not has_input:
                            logger.warning(f"心跳检测警告: 未找到输入框, platform={platform}")
                            # 不直接返回False，因为有些页面结构可能不同，只要没有出现登录按钮，且页面加载了，就倾向于认为是valid
                            # 或者是页面结构变了。保守起见，如果也没发现登录按钮，我们返回True?
                            # 但如果页面白屏（加载失败），既没登录按钮也没输入框。
                            # 这种情况下，如果 retry_count < max_retries，会重试。
                            if retry_count < max_retries:
                                raise Exception("页面加载可能不完整，未找到明确状态指示")
                            else:
                                # 最后一次尝试，如果没有明确的登录按钮，且没有输入框，
                                # 我们假设它是有效的（可能是UI变了），避免误报Unauthorized
                                logger.info(f"未找到输入框但也没找到登录按钮，假定会话有效: platform={platform}")
                                return True

                        logger.info(f"心跳检测成功: platform={platform}")
                        return True

                    finally:
                        if browser:
                            await browser.close()

            except Exception as e:
                retry_count += 1
                logger.warning(f"心跳检测尝试 {retry_count} 失败: {e}, platform={platform}")
                if retry_count > max_retries:
                    logger.error(f"心跳检测最终失败: {e}")
                    return False
                await asyncio.sleep(2)

        return False

    async def get_session_status_fast(self, user_id: int, project_id: int, platform: str) -> Dict[str, Any]:
        """
        快速获取会话状态（仅检查文件，不执行浏览器验证）

        Args:
            user_id: 用户ID
            project_id: 项目ID
            platform: AI平台标识

        Returns:
            会话状态详情
        """
        try:
            # 检查会话文件是否存在
            file_path = self._get_session_file_path(user_id, project_id, platform)
            exists = file_path.exists()

            status = "invalid"
            age_info = {}

            if exists:
                # 文件存在，暂定为valid，具体需要通过validate_session进一步验证
                # 但为了快速响应，这里返回valid或expiring
                status = "valid"

                # 尝试读取文件获取时间信息
                try:
                    # 获取文件修改时间作为最后修改时间
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    now = datetime.now()
                    age = now - mtime

                    # 简单的时间检查
                    if age > timedelta(days=7):
                        status = "invalid"
                    elif age > timedelta(days=5):
                        status = "expiring"

                    age_info = {"last_modified": mtime.isoformat(), "age_hours": round(age.total_seconds() / 3600, 1)}
                except Exception:
                    pass

            return {
                "status": status,
                "exists": exists,
                "age_info": age_info,
                "platform": platform,
                "is_fast_check": True,
            }
        except Exception as e:
            logger.error(f"快速获取会话状态失败: {e}")
            return {"status": "invalid", "exists": False, "error": str(e)}

    async def get_session_status(self, user_id: int, project_id: int, platform: str) -> Dict[str, Any]:
        """
        获取会话状态详情（执行完整验证）

        Args:
            user_id: 用户ID
            project_id: 项目ID
            platform: AI平台标识

        Returns:
            会话状态详情
        """
        try:
            # 检查会话文件是否存在
            file_path = self._get_session_file_path(user_id, project_id, platform)
            logger.info(f"检查会话状态: platform={platform}, file_path={file_path}, exists={file_path.exists()}")

            if not file_path.exists():
                logger.warning(f"会话文件不存在: platform={platform}, file_path={file_path}")
                return {"status": "invalid", "reason": "会话不存在", "exists": False}

            # 加载存储状态
            storage_state = await self.load_session(
                user_id=user_id, project_id=project_id, platform=platform, validate=False
            )

            if not storage_state:
                # 会话损坏但文件存在，返回expiring状态
                logger.warning(f"会话损坏: platform={platform}")
                return {"status": "expiring", "reason": "会话损坏", "exists": True}

            # 验证会话（增加重试机制）
            session_status = "invalid"
            retry_count = 2
            for attempt in range(retry_count):
                try:
                    session_status = await self.validate_session(
                        user_id=user_id, project_id=project_id, platform=platform, storage_state=storage_state
                    )
                    if session_status == "valid":
                        break
                except Exception as e:
                    logger.warning(f"第{attempt + 1}次验证会话失败: {e}")
                    if attempt < retry_count - 1:
                        import asyncio

                        await asyncio.sleep(1)  # 等待1秒后重试

            # 获取会话时间信息
            last_modified = storage_state.get("last_modified")
            created_at = storage_state.get("created_at")
            age_info = {}
            if last_modified:
                try:
                    last_modified_time = datetime.fromisoformat(last_modified)
                    now = datetime.now()
                    age = now - last_modified_time
                    age_info = {
                        "created_at": created_at,
                        "last_modified": last_modified,
                        "age_seconds": int(age.total_seconds()),
                        "age_hours": round(age.total_seconds() / 3600, 1),
                        "age_days": round(age.total_seconds() / 86400, 1),
                    }
                except Exception as e:
                    logger.error(f"解析会话时间失败: {e}")

            # 如果心跳检测失败但会话文件存在，返回"expiring"状态而不是"invalid"
            if session_status == "invalid" and file_path.exists():
                session_status = "expiring"

            logger.info(f"会话状态检测完成: platform={platform}, status={session_status}")
            return {"status": session_status, "exists": True, "age_info": age_info, "platform": platform}

        except Exception as e:
            logger.error(f"获取会话状态失败: {e}")
            # 即使发生异常，也要检查会话文件是否存在
            try:
                file_path = self._get_session_file_path(user_id, project_id, platform)
                exists = file_path.exists()
                logger.info(f"异常处理 - 文件存在性检查: platform={platform}, exists={exists}")
                return {
                    "status": "expiring" if exists else "invalid",
                    "reason": f"获取状态失败: {str(e)}",
                    "exists": exists,
                }
            except Exception as inner_e:
                logger.error(f"异常处理失败: {inner_e}")
                return {"status": "invalid", "reason": f"获取状态失败: {str(e)}", "exists": False}

    async def delete_session(self, user_id: int, project_id: int, platform: str) -> bool:
        """
        删除会话

        Args:
            user_id: 用户ID
            project_id: 项目ID
            platform: AI平台标识

        Returns:
            是否删除成功
        """
        try:
            file_path = self._get_session_file_path(user_id, project_id, platform)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"会话删除成功: user_id={user_id}, project_id={project_id}, platform={platform}")
            return True
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False

    async def list_sessions(self, user_id: Optional[int] = None, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        列出用户/项目的所有会话

        Args:
            user_id: 用户ID（可选）
            project_id: 项目ID（可选）

        Returns:
            会话列表
        """
        try:
            sessions = []

            for file_path in self._session_dir.glob("session_*.enc"):
                file_name = file_path.name

                # 解析文件名
                parts = file_name.split("_")
                if len(parts) >= 4:
                    try:
                        session_user_id = int(parts[1])
                        session_project_id = int(parts[2])
                        session_platform = parts[3].rsplit(".", 1)[0]

                        # 过滤条件
                        if user_id is not None and session_user_id != user_id:
                            continue
                        if project_id is not None and session_project_id != project_id:
                            continue

                        sessions.append(
                            {
                                "user_id": session_user_id,
                                "project_id": session_project_id,
                                "platform": session_platform,
                                "file_path": str(file_path),
                                "last_modified": file_path.stat().st_mtime,
                            }
                        )
                        logger.info(f"发现会话文件: platform={session_platform}, file_path={file_path}")
                    except Exception as e:
                        logger.warning(f"解析会话文件失败: {file_path}, error={e}")
                        continue

            # 按平台排序
            sessions.sort(key=lambda x: x["platform"])

            return {"sessions": sessions, "total": len(sessions)}

        except Exception as e:
            logger.error(f"列出会话失败: {e}")
            return {"sessions": [], "total": 0}

    async def check_session_exists(self, user_id: int, project_id: int, platform: str) -> bool:
        """
        检查会话是否存在

        Args:
            user_id: 用户ID
            project_id: 项目ID
            platform: AI平台标识

        Returns:
            会话是否存在
        """
        file_path = self._get_session_file_path(user_id, project_id, platform)
        return file_path.exists()


# 全局单例
secure_session_manager = SecureSessionManager()
