"""
PyFactory - 专业UI模块 (使用 pygame-gui)
提供现代化的UI组件和动画效果
"""

import pygame
import pygame_gui
from pygame_gui.elements import (
    UIButton, UILabel, UIPanel, UITextEntryLine,
    UITextBox, UIWindow, UIDropDownMenu
)
from pygame_gui.core import ObjectID
import pytweening
from typing import Optional, Callable, List, Dict, Tuple, Any
from dataclasses import dataclass, field
import math
import time

from config import WINDOW_WIDTH, WINDOW_HEIGHT, COLORS


@dataclass
class Animation:
    """动画数据类"""
    start_value: float
    end_value: float
    duration: float
    elapsed: float = 0.0
    easing: str = 'easeOutQuad'
    on_complete: Optional[Callable] = None
    
    @property
    def progress(self) -> float:
        return min(1.0, self.elapsed / self.duration)
    
    @property
    def value(self) -> float:
        easing_func = getattr(pytweening, self.easing, pytweening.linear)
        t = easing_func(self.progress)
        return self.start_value + (self.end_value - self.start_value) * t
    
    @property
    def is_complete(self) -> bool:
        return self.elapsed >= self.duration
    
    def update(self, dt: float):
        self.elapsed += dt
        if self.is_complete and self.on_complete:
            self.on_complete()


class AnimationManager:
    """动画管理器"""
    
    def __init__(self):
        self.animations: Dict[str, Animation] = {}
    
    def add(self, name: str, start: float, end: float, duration: float,
            easing: str = 'easeOutQuad', on_complete: Callable = None):
        self.animations[name] = Animation(
            start_value=start,
            end_value=end,
            duration=duration,
            easing=easing,
            on_complete=on_complete
        )
    
    def get(self, name: str, default: float = 0) -> float:
        if name in self.animations:
            return self.animations[name].value
        return default
    
    def update(self, dt: float):
        completed = []
        for name, anim in self.animations.items():
            anim.update(dt)
            if anim.is_complete:
                completed.append(name)
        for name in completed:
            del self.animations[name]


class ParticleEffect:
    """粒子效果"""
    
    @dataclass
    class Particle:
        x: float
        y: float
        vx: float
        vy: float
        life: float
        max_life: float
        color: Tuple[int, int, int]
        size: float
    
    def __init__(self):
        self.particles: List[ParticleEffect.Particle] = []
    
    def emit(self, x: float, y: float, color: Tuple[int, int, int], 
             count: int = 10, speed: float = 100, life: float = 1.0):
        import random
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(speed * 0.5, speed)
            self.particles.append(self.Particle(
                x=x, y=y,
                vx=math.cos(angle) * spd,
                vy=math.sin(angle) * spd,
                life=life,
                max_life=life,
                color=color,
                size=random.uniform(3, 8)
            ))
    
    def update(self, dt: float):
        for p in self.particles[:]:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 200 * dt  # 重力
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)
    
    def draw(self, surface: pygame.Surface):
        for p in self.particles:
            alpha = int(255 * (p.life / p.max_life))
            size = int(p.size * (p.life / p.max_life))
            if size > 0:
                color = (*p.color, alpha)
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, color, (size, size), size)
                surface.blit(s, (int(p.x - size), int(p.y - size)))


class ProUIManager:
    """专业UI管理器"""
    
    def __init__(self):
        self.manager = pygame_gui.UIManager(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            'theme.json'
        )
        self.animations = AnimationManager()
        self.particles = ParticleEffect()
        self.toasts: List[Dict] = []
    
    def process_events(self, event: pygame.event.Event):
        self.manager.process_events(event)
    
    def update(self, dt: float):
        self.manager.update(dt)
        self.animations.update(dt)
        self.particles.update(dt)
        
        # 更新toast
        for toast in self.toasts[:]:
            toast['time'] -= dt
            if toast['time'] <= 0:
                self.toasts.remove(toast)
    
    def draw(self, surface: pygame.Surface):
        self.manager.draw_ui(surface)
        self.particles.draw(surface)
        self._draw_toasts(surface)
    
    def show_toast(self, message: str, toast_type: str = 'info', duration: float = 2.0):
        colors = {
            'info': COLORS['accent'],
            'success': COLORS['success'],
            'error': COLORS['error'],
            'warning': COLORS['warning']
        }
        self.toasts.append({
            'message': message,
            'color': colors.get(toast_type, COLORS['accent']),
            'time': duration,
            'max_time': duration
        })
    
    def _draw_toasts(self, surface: pygame.Surface):
        from fonts import get_font
        font = get_font(20)
        y = 80
        for toast in self.toasts:
            alpha = min(255, int(255 * (toast['time'] / toast['max_time']) * 2))
            text = font.render(toast['message'], True, toast['color'])
            
            # 背景
            padding = 15
            rect = pygame.Rect(
                WINDOW_WIDTH // 2 - text.get_width() // 2 - padding,
                y,
                text.get_width() + padding * 2,
                text.get_height() + 10
            )
            
            bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(bg, (*COLORS['panel_bg'][:3], alpha), 
                           (0, 0, rect.width, rect.height), border_radius=8)
            pygame.draw.rect(bg, (*toast['color'][:3], alpha),
                           (0, 0, rect.width, rect.height), 2, border_radius=8)
            surface.blit(bg, rect.topleft)
            
            text.set_alpha(alpha)
            surface.blit(text, (rect.x + padding, rect.y + 5))
            y += rect.height + 10
    
    def emit_success_particles(self, x: float, y: float):
        self.particles.emit(x, y, COLORS['success'], count=20, speed=150)
    
    def emit_error_particles(self, x: float, y: float):
        self.particles.emit(x, y, COLORS['error'], count=15, speed=100)


class GlowEffect:
    """发光效果"""
    
    @staticmethod
    def draw_glow_rect(surface: pygame.Surface, rect: pygame.Rect, 
                       color: Tuple[int, int, int], intensity: float = 1.0):
        glow_size = int(10 * intensity)
        for i in range(glow_size, 0, -2):
            alpha = int(30 * (1 - i / glow_size) * intensity)
            glow_rect = rect.inflate(i * 2, i * 2)
            s = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=8 + i)
            surface.blit(s, glow_rect.topleft)
    
    @staticmethod
    def draw_glow_circle(surface: pygame.Surface, center: Tuple[int, int],
                         radius: int, color: Tuple[int, int, int], intensity: float = 1.0):
        glow_size = int(15 * intensity)
        for i in range(glow_size, 0, -2):
            alpha = int(40 * (1 - i / glow_size) * intensity)
            s = pygame.Surface((radius * 2 + i * 2, radius * 2 + i * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (radius + i, radius + i), radius + i)
            surface.blit(s, (center[0] - radius - i, center[1] - radius - i))


class SmoothValue:
    """平滑变化的值"""
    
    def __init__(self, initial: float = 0, speed: float = 5.0):
        self.target = initial
        self.current = initial
        self.speed = speed
    
    def set(self, value: float):
        self.target = value
    
    def update(self, dt: float):
        diff = self.target - self.current
        self.current += diff * min(1.0, self.speed * dt)
    
    @property
    def value(self) -> float:
        return self.current


# 全局UI管理器
pro_ui: Optional[ProUIManager] = None


def init_pro_ui():
    """初始化专业UI"""
    global pro_ui
    pro_ui = ProUIManager()
    return pro_ui


def get_pro_ui() -> ProUIManager:
    """获取UI管理器"""
    global pro_ui
    if pro_ui is None:
        pro_ui = init_pro_ui()
    return pro_ui
