# -*- coding: utf-8 -*-
"""
Playwright发布适配器模块
用这个来管理所有平台的发布器！
"""

from .base import BasePublisher, PublisherRegistry, registry, get_publisher, list_publishers
from .zhihu import ZhihuPublisher
from .baijiahao import BaijiahaoPublisher
from .sohu import SohuPublisher
from .toutiao import ToutiaoPublisher
from .xiaohongshu import XiaohongshuPublisher
from .douyin import DouyinPublisher


def register_publishers(platforms_config):
    """
    注册所有平台发布器

    注意：这个函数需要在服务启动时调用！
    """
    for platform_id, config in platforms_config.items():
        publisher = None

        if platform_id == "zhihu":
            publisher = ZhihuPublisher(platform_id, config)
        elif platform_id == "baijiahao":
            publisher = BaijiahaoPublisher(platform_id, config)
        elif platform_id == "sohu":
            publisher = SohuPublisher(platform_id, config)
        elif platform_id == "toutiao":
            publisher = ToutiaoPublisher(platform_id, config)
        elif platform_id == "xiaohongshu":
            publisher = XiaohongshuPublisher(platform_id, config)
        elif platform_id == "douyin":
            publisher = DouyinPublisher(platform_id, config)

        if publisher:
            registry.register(platform_id, publisher)


__all__ = [
    "BasePublisher",
    "PublisherRegistry",
    "registry",
    "get_publisher",
    "list_publishers",
    "register_publishers",
    "ZhihuPublisher",
    "BaijiahaoPublisher",
    "SohuPublisher",
    "ToutiaoPublisher",
    "XiaohongshuPublisher",
    "DouyinPublisher",
]
