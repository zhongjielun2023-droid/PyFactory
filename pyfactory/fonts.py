"""
PyFactory - 字体管理模块
解决Pygame中文显示问题
"""

import pygame
import os
import sys
from typing import Dict, Optional


class FontManager:
    """字体管理器 - 处理中文字体加载"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if FontManager._initialized:
            return
        FontManager._initialized = True
        
        self._fonts: Dict[int, pygame.font.Font] = {}
        self._font_path: Optional[str] = None
        self._find_chinese_font()
    
    def _find_chinese_font(self):
        """查找系统中支持中文的字体"""
        # macOS 中文字体路径
        mac_fonts = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
        ]
        
        # Windows 中文字体路径
        win_fonts = [
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simsun.ttc",    # 宋体
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
        ]
        
        # Linux 中文字体路径
        linux_fonts = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        
        # 根据系统选择字体列表
        if sys.platform == 'darwin':
            font_list = mac_fonts
        elif sys.platform == 'win32':
            font_list = win_fonts
        else:
            font_list = linux_fonts
        
        # 查找可用字体
        for font_path in font_list:
            if os.path.exists(font_path):
                self._font_path = font_path
                return
        
        # 尝试使用pygame的系统字体查找
        try:
            available_fonts = pygame.font.get_fonts()
            chinese_font_names = [
                'pingfangsc', 'pingfang', 'microsoftyahei', 'msyh',
                'simsun', 'simhei', 'heiti', 'stheiti', 'hiraginosansgb',
                'notosanscjk', 'wenquanyimicrohei', 'arialunicodems'
            ]
            for name in chinese_font_names:
                if name in available_fonts:
                    self._font_path = pygame.font.match_font(name)
                    if self._font_path:
                        return
        except:
            pass
        
        # 如果找不到，使用None（默认字体，可能不支持中文）
        self._font_path = None
    
    def get_font(self, size: int) -> pygame.font.Font:
        """获取指定大小的字体"""
        if size not in self._fonts:
            try:
                if self._font_path:
                    self._fonts[size] = pygame.font.Font(self._font_path, size)
                else:
                    # 尝试使用SysFont
                    self._fonts[size] = pygame.font.SysFont(
                        'pingfangsc,microsoftyahei,simsun,arial', size
                    )
            except:
                # 最后的fallback
                self._fonts[size] = pygame.font.Font(None, size)
        
        return self._fonts[size]
    
    def render(self, text: str, size: int, color: tuple, 
               antialias: bool = True) -> pygame.Surface:
        """渲染文本"""
        font = self.get_font(size)
        return font.render(text, antialias, color)


# 全局字体管理器实例
_font_manager: Optional[FontManager] = None


def get_font_manager() -> FontManager:
    """获取字体管理器实例"""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager


def get_font(size: int) -> pygame.font.Font:
    """获取指定大小的字体"""
    return get_font_manager().get_font(size)


def render_text(text: str, size: int, color: tuple) -> pygame.Surface:
    """渲染文本"""
    return get_font_manager().render(text, size, color)
