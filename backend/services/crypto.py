# -*- coding: utf-8 -*-
"""
加密解密工具 - 工业加固版
采用 AES-256 (Fernet) 对敏感的 Cookie 和 StorageState 进行加密存储
"""

import base64
import json
from loguru import logger
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Any, Dict, List

from backend.config import ENCRYPTION_KEY


class CryptoService:
    """
    加密服务单例类
    """

    def __init__(self, key: Any = ENCRYPTION_KEY):
        """
        初始化并派生密钥
        """
        # 确保 key 是 bytes 类型
        if isinstance(key, str):
            key_bytes = key.encode()
        else:
            key_bytes = bytes(key)

        # 1. 派生强密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"auto_geo_secure_salt_v1",  # 盐值固定以确保重启后仍能解密旧数据
            iterations=100000,
        )

        # Fernet 密钥必须是 32 字节的 base64 编码
        derived_key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
        self._fernet = Fernet(derived_key)

    def encrypt(self, data: str) -> str:
        """
        加密字符串：返回 URL 安全的 Base64 字符串
        """
        if not data:
            return ""
        try:
            # Fernet.encrypt 直接返回的就是 URL-Safe Base64 格式的 bytes
            encrypted_bytes = self._fernet.encrypt(data.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"❌ 加密失败: {e}")
            return ""

    def decrypt(self, encrypted_str: str) -> str:
        """
        解密字符串
        """
        if not encrypted_str:
            return ""
        try:
            decrypted_bytes = self._fernet.decrypt(encrypted_str.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception:
            # 这种情况通常发生在密钥被修改后尝试解密旧数据
            logger.warning("⚠️ 解密失败：可能是密钥不匹配或数据损坏")
            return ""

    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        加密字典
        """
        if not data:
            return ""
        return self.encrypt(json.dumps(data, ensure_ascii=False))

    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """
        解密为字典
        """
        if not encrypted_data:
            return {}
        decrypted_str = self.decrypt(encrypted_data)
        if not decrypted_str:
            return {}
        try:
            return json.loads(decrypted_str)
        except json.JSONDecodeError:
            return {}


# ==================== 全局单例与便捷导出 ====================

crypto_service = CryptoService()


def encrypt_cookies(cookies: List[Dict]) -> str:
    """
    加密 Playwright 获取的 Cookies 列表
    """
    if not cookies:
        return ""
    # 直接加密列表转换的 JSON
    return crypto_service.encrypt(json.dumps(cookies))


def decrypt_cookies(encrypted: str) -> List[Dict]:
    """
    解密 Cookies 列表
    """
    if not encrypted:
        return []
    decrypted_str = crypto_service.decrypt(encrypted)
    try:
        return json.loads(decrypted_str) if decrypted_str else []
    except:
        return []


def encrypt_storage_state(storage_state: Dict) -> str:
    """
    加密 storage_state (包含 localStorage)
    """
    if not storage_state:
        return ""
    return crypto_service.encrypt_dict(storage_state)


def decrypt_storage_state(encrypted: str) -> Dict:
    """
    解密 storage_state
    """
    if not encrypted:
        return {}
    return crypto_service.decrypt_dict(encrypted)