"""
PyFactory - UI系统
使用Pygame实现游戏界面
"""

import pygame
from typing import Optional, List, Dict, Any, Tuple, Callable
from config import (
    COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, GRID_SIZE,
    MACHINE_TYPES, LEVEL_CATEGORIES, SHAPE_COLORS
)
from fonts import get_font


class UIElement:
    """UI元素基类"""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.enabled = True
        self.hovered = False
        
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def contains_point(self, x: int, y: int) -> bool:
        return self.get_rect().collidepoint(x, y)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        return False
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        pass


class Button(UIElement):
    """按钮组件"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str, callback: Callable = None,
                 color: Tuple = None, text_color: Tuple = None):
        super().__init__(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color = color or COLORS['button_normal']
        self.hover_color = COLORS['button_hover']
        self.active_color = COLORS['button_active']
        self.text_color = text_color or COLORS['text']
        self.font_size = 24
        self.border_radius = 8
        self.pressed = False
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.contains_point(*event.pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.contains_point(*event.pos):
                self.pressed = True
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.pressed:
                self.pressed = False
                if self.contains_point(*event.pos) and self.callback:
                    self.callback()
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
            
        # 选择颜色
        if self.pressed:
            color = self.active_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.color
        
        # 绘制按钮背景
        rect = self.get_rect()
        pygame.draw.rect(surface, color, rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, COLORS['panel_border'], rect, 2, 
                        border_radius=self.border_radius)
        
        # 绘制文本
        font = get_font(self.font_size)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)


class IconButton(Button):
    """图标按钮"""
    
    def __init__(self, x: int, y: int, size: int, icon: str,
                 callback: Callable = None, tooltip: str = ""):
        super().__init__(x, y, size, size, "", callback)
        self.icon = icon
        self.tooltip = tooltip
        self.font_size = size - 8
        
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
            
        # 选择颜色
        if self.pressed:
            color = self.active_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.color
        
        # 绘制圆形按钮
        center = (self.x + self.width // 2, self.y + self.height // 2)
        pygame.draw.circle(surface, color, center, self.width // 2)
        pygame.draw.circle(surface, COLORS['panel_border'], center, 
                          self.width // 2, 2)
        
        # 绘制图标文字
        font = get_font(self.font_size)
        text_surface = font.render(self.icon, True, self.text_color)
        text_rect = text_surface.get_rect(center=center)
        surface.blit(text_surface, text_rect)
        
        # 绘制提示
        if self.hovered and self.tooltip:
            self._draw_tooltip(surface)
    
    def _draw_tooltip(self, surface: pygame.Surface):
        font = get_font(20)
        text = font.render(self.tooltip, True, COLORS['text'])
        padding = 6
        rect = pygame.Rect(
            self.x + self.width + 5,
            self.y,
            text.get_width() + padding * 2,
            text.get_height() + padding * 2
        )
        pygame.draw.rect(surface, COLORS['panel_bg'], rect)
        pygame.draw.rect(surface, COLORS['panel_border'], rect, 1)
        surface.blit(text, (rect.x + padding, rect.y + padding))


class Panel(UIElement):
    """面板组件"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 title: str = ""):
        super().__init__(x, y, width, height)
        self.title = title
        self.children: List[UIElement] = []
        self.bg_color = COLORS['panel_bg']
        self.border_color = COLORS['panel_border']
        self.draggable = False
        self.drag_offset = (0, 0)
        self.is_dragging = False
        
    def add_child(self, child: UIElement):
        self.children.append(child)
        
    def remove_child(self, child: UIElement):
        if child in self.children:
            self.children.remove(child)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        
        # 先处理子元素事件
        for child in reversed(self.children):
            if child.handle_event(event):
                return True
        
        # 处理拖动
        if self.draggable:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.contains_point(*event.pos):
                    # 检查是否在标题栏
                    if event.pos[1] < self.y + 30:
                        self.is_dragging = True
                        self.drag_offset = (event.pos[0] - self.x, 
                                           event.pos[1] - self.y)
                        return True
            
            elif event.type == pygame.MOUSEBUTTONUP:
                self.is_dragging = False
            
            elif event.type == pygame.MOUSEMOTION and self.is_dragging:
                self.x = event.pos[0] - self.drag_offset[0]
                self.y = event.pos[1] - self.drag_offset[1]
                return True
        
        return False
    
    def update(self, dt: float):
        for child in self.children:
            child.update(dt)
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        rect = self.get_rect()
        
        # 绘制背景
        pygame.draw.rect(surface, self.bg_color, rect, border_radius=8)
        pygame.draw.rect(surface, self.border_color, rect, 2, border_radius=8)
        
        # 绘制标题
        if self.title:
            font = get_font(28)
            title_surface = font.render(self.title, True, COLORS['text'])
            surface.blit(title_surface, (self.x + 10, self.y + 8))
            
            # 标题分隔线
            pygame.draw.line(surface, self.border_color,
                           (self.x, self.y + 32), (self.x + self.width, self.y + 32))
        
        # 绘制子元素
        for child in self.children:
            child.draw(surface)


class TextInput(UIElement):
    """文本输入框"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 placeholder: str = "", is_password: bool = False):
        super().__init__(x, y, width, height)
        self.text = ""
        self.placeholder = placeholder
        self.is_password = is_password
        self.focused = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.max_length = 50
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.focused = self.contains_point(*event.pos)
            return self.focused
        
        if event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.focused = False
            elif len(self.text) < self.max_length:
                if event.unicode and event.unicode.isprintable():
                    self.text += event.unicode
            return True
        
        return False
    
    def update(self, dt: float):
        if self.focused:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        rect = self.get_rect()
        
        # 背景
        bg_color = COLORS['button_hover'] if self.focused else COLORS['button_normal']
        pygame.draw.rect(surface, bg_color, rect, border_radius=4)
        pygame.draw.rect(surface, COLORS['accent'] if self.focused else COLORS['panel_border'],
                        rect, 2, border_radius=4)
        
        # 文本
        font = get_font(24)
        if self.text:
            display_text = '*' * len(self.text) if self.is_password else self.text
            text_surface = font.render(display_text, True, COLORS['text'])
        else:
            text_surface = font.render(self.placeholder, True, COLORS['text_secondary'])
        
        text_rect = text_surface.get_rect(midleft=(rect.x + 10, rect.centery))
        
        # 裁剪文本
        clip_rect = pygame.Rect(rect.x + 5, rect.y, rect.width - 10, rect.height)
        surface.set_clip(clip_rect)
        surface.blit(text_surface, text_rect)
        surface.set_clip(None)
        
        # 光标
        if self.focused and self.cursor_visible:
            cursor_x = text_rect.right + 2
            pygame.draw.line(surface, COLORS['text'],
                           (cursor_x, rect.y + 5), (cursor_x, rect.bottom - 5), 2)


class Label(UIElement):
    """标签组件"""
    
    def __init__(self, x: int, y: int, text: str, font_size: int = 24,
                 color: Tuple = None, centered: bool = False):
        super().__init__(x, y, 0, 0)
        self.text = text
        self.font_size = font_size
        self.color = color or COLORS['text']
        self.centered = centered
        
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        font = get_font(self.font_size)
        text_surface = font.render(self.text, True, self.color)
        
        if self.centered:
            text_rect = text_surface.get_rect(center=(self.x, self.y))
        else:
            text_rect = text_surface.get_rect(topleft=(self.x, self.y))
        
        surface.blit(text_surface, text_rect)


class ScrollPanel(Panel):
    """可滚动面板"""
    
    def __init__(self, x: int, y: int, width: int, height: int, title: str = ""):
        super().__init__(x, y, width, height, title)
        self.scroll_offset = 0
        self.content_height = 0
        self.scroll_speed = 30
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        
        if event.type == pygame.MOUSEWHEEL:
            if self.contains_point(*pygame.mouse.get_pos()):
                self.scroll_offset -= event.y * self.scroll_speed
                max_scroll = max(0, self.content_height - self.height + 40)
                self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
                return True
        
        return super().handle_event(event)
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        rect = self.get_rect()
        
        # 绘制背景
        pygame.draw.rect(surface, self.bg_color, rect, border_radius=8)
        pygame.draw.rect(surface, self.border_color, rect, 2, border_radius=8)
        
        # 绘制标题
        title_height = 0
        if self.title:
            font = get_font(28)
            title_surface = font.render(self.title, True, COLORS['text'])
            surface.blit(title_surface, (self.x + 10, self.y + 8))
            pygame.draw.line(surface, self.border_color,
                           (self.x, self.y + 32), (self.x + self.width, self.y + 32))
            title_height = 35
        
        # 裁剪区域
        clip_rect = pygame.Rect(self.x + 2, self.y + title_height + 2,
                               self.width - 4, self.height - title_height - 4)
        surface.set_clip(clip_rect)
        
        # 绘制子元素（应用滚动偏移）
        for child in self.children:
            original_y = child.y
            child.y -= self.scroll_offset
            child.draw(surface)
            child.y = original_y
        
        surface.set_clip(None)
        
        # 绘制滚动条
        if self.content_height > self.height - title_height:
            scrollbar_height = max(20, (self.height - title_height) ** 2 / self.content_height)
            scrollbar_y = self.y + title_height + (self.scroll_offset / self.content_height) * (self.height - title_height)
            scrollbar_rect = pygame.Rect(
                self.x + self.width - 8,
                scrollbar_y,
                6,
                scrollbar_height
            )
            pygame.draw.rect(surface, COLORS['button_hover'], scrollbar_rect, border_radius=3)


class MachineSelector(Panel):
    """机器选择器面板"""
    
    def __init__(self, x: int, y: int, on_select: Callable = None):
        super().__init__(x, y, 200, 400, "机器选择")
        self.on_select = on_select
        self.selected_type: Optional[str] = None
        self._create_buttons()
        
    def _create_buttons(self):
        categories = {
            'basic': '基础',
            'transform': '变换',
            'logic': '逻辑',
            'data': '数据'
        }
        
        y_offset = 40
        for category, cat_name in categories.items():
            # 类别标题
            label = Label(self.x + 10, self.y + y_offset, f"【{cat_name}】", 
                         font_size=20, color=COLORS['accent'])
            self.add_child(label)
            y_offset += 25
            
            # 该类别的机器
            for mtype, minfo in MACHINE_TYPES.items():
                if minfo.get('category') == category:
                    btn = Button(
                        self.x + 10, self.y + y_offset,
                        180, 30, minfo['name'],
                        lambda t=mtype: self._on_machine_click(t)
                    )
                    btn.font_size = 20
                    self.add_child(btn)
                    y_offset += 35
            
            y_offset += 10
    
    def _on_machine_click(self, machine_type: str):
        self.selected_type = machine_type
        if self.on_select:
            self.on_select(machine_type)


class CodeEditor(Panel):
    """代码编辑器面板"""
    
    def __init__(self, x: int, y: int, width: int, height: int, on_change: Callable = None):
        super().__init__(x, y, width, height, "Python代码")
        self.code = ""
        self.lines: List[str] = [""]
        self.cursor_line = 0
        self.cursor_col = 0
        self.focused = False
        self.scroll_offset = 0
        self.line_height = 22
        self.font = None
        self.on_change = on_change  # 代码变化回调
        self.error_line = -1  # 错误行号
        self.error_msg = ""  # 错误信息
        
    def set_code(self, code: str):
        self.code = code
        self.lines = code.split('\n') if code else [""]
        self.cursor_line = 0
        self.cursor_col = 0
    
    def get_code(self) -> str:
        return '\n'.join(self.lines)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.focused = self.contains_point(*event.pos)
            if self.focused:
                # 计算点击位置对应的行列
                click_y = event.pos[1] - self.y - 40 + self.scroll_offset
                self.cursor_line = min(max(0, click_y // self.line_height), 
                                       len(self.lines) - 1)
                return True
        
        if event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_RETURN:
                # 换行
                current = self.lines[self.cursor_line]
                self.lines[self.cursor_line] = current[:self.cursor_col]
                self.lines.insert(self.cursor_line + 1, current[self.cursor_col:])
                self.cursor_line += 1
                self.cursor_col = 0
            elif event.key == pygame.K_BACKSPACE:
                if self.cursor_col > 0:
                    current = self.lines[self.cursor_line]
                    self.lines[self.cursor_line] = current[:self.cursor_col-1] + current[self.cursor_col:]
                    self.cursor_col -= 1
                elif self.cursor_line > 0:
                    # 合并到上一行
                    prev_len = len(self.lines[self.cursor_line - 1])
                    self.lines[self.cursor_line - 1] += self.lines[self.cursor_line]
                    self.lines.pop(self.cursor_line)
                    self.cursor_line -= 1
                    self.cursor_col = prev_len
            elif event.key == pygame.K_LEFT:
                if self.cursor_col > 0:
                    self.cursor_col -= 1
            elif event.key == pygame.K_RIGHT:
                if self.cursor_col < len(self.lines[self.cursor_line]):
                    self.cursor_col += 1
            elif event.key == pygame.K_UP:
                if self.cursor_line > 0:
                    self.cursor_line -= 1
                    self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_line]))
            elif event.key == pygame.K_DOWN:
                if self.cursor_line < len(self.lines) - 1:
                    self.cursor_line += 1
                    self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_line]))
            elif event.key == pygame.K_TAB:
                # 插入4个空格
                current = self.lines[self.cursor_line]
                self.lines[self.cursor_line] = current[:self.cursor_col] + "    " + current[self.cursor_col:]
                self.cursor_col += 4
            elif event.unicode and event.unicode.isprintable():
                current = self.lines[self.cursor_line]
                self.lines[self.cursor_line] = current[:self.cursor_col] + event.unicode + current[self.cursor_col:]
                self.cursor_col += 1
            
            # 触发代码变化回调
            if self.on_change:
                self.on_change(self.get_code())
            
            return True
        
        if event.type == pygame.MOUSEWHEEL and self.focused:
            self.scroll_offset -= event.y * self.line_height * 2
            max_scroll = max(0, len(self.lines) * self.line_height - (self.height - 50))
            self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
            return True
        
        return super().handle_event(event)
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        if self.font is None:
            self.font = get_font(16)
        
        super().draw(surface)
        
        # 代码区域
        code_rect = pygame.Rect(self.x + 5, self.y + 40, 
                               self.width - 10, self.height - 50)
        
        # 绘制行号背景
        line_num_width = 35
        pygame.draw.rect(surface, COLORS['button_normal'],
                        (self.x + 5, self.y + 40, line_num_width, self.height - 50))
        
        # 裁剪区域
        surface.set_clip(code_rect)
        
        # 绘制代码行
        for i, line in enumerate(self.lines):
            y = self.y + 45 + i * self.line_height - self.scroll_offset
            
            if y < self.y + 35 or y > self.y + self.height - 10:
                continue
            
            # 行号
            line_num = self.font.render(str(i + 1), True, COLORS['text_secondary'])
            surface.blit(line_num, (self.x + 8, y))
            
            # 高亮错误行
            if i == self.error_line:
                error_rect = pygame.Rect(
                    self.x + line_num_width + 5, y - 2,
                    self.width - line_num_width - 15, self.line_height
                )
                pygame.draw.rect(surface, (80, 30, 30), error_rect)
            # 高亮当前行
            elif i == self.cursor_line and self.focused:
                highlight_rect = pygame.Rect(
                    self.x + line_num_width + 5, y - 2,
                    self.width - line_num_width - 15, self.line_height
                )
                pygame.draw.rect(surface, COLORS['button_hover'], highlight_rect)
            
            # 代码文本（简单的语法高亮）
            self._draw_code_line(surface, line, self.x + line_num_width + 10, y)
            
            # 光标
            if i == self.cursor_line and self.focused:
                cursor_x = self.x + line_num_width + 10
                if self.cursor_col > 0:
                    prefix = self.font.render(line[:self.cursor_col], True, COLORS['text'])
                    cursor_x += prefix.get_width()
                pygame.draw.line(surface, COLORS['accent'],
                               (cursor_x, y), (cursor_x, y + self.line_height - 4), 2)
        
        surface.set_clip(None)
    
    def _draw_code_line(self, surface: pygame.Surface, line: str, x: int, y: int):
        """绘制代码行（简单语法高亮）"""
        keywords = {'def', 'if', 'else', 'elif', 'for', 'while', 'return', 
                   'class', 'import', 'from', 'in', 'not', 'and', 'or', 'True', 'False', 'None'}
        
        words = []
        current_word = ""
        for char in line:
            if char.isalnum() or char == '_':
                current_word += char
            else:
                if current_word:
                    words.append(current_word)
                    current_word = ""
                words.append(char)
        if current_word:
            words.append(current_word)
        
        current_x = x
        for word in words:
            if word in keywords:
                color = COLORS['accent']
            elif word.isdigit():
                color = COLORS['warning']
            elif word.startswith('"') or word.startswith("'"):
                color = COLORS['success']
            elif word == '#':
                color = COLORS['text_secondary']
            else:
                color = COLORS['text']
            
            text = self.font.render(word, True, color)
            surface.blit(text, (current_x, y))
            current_x += text.get_width()


class Toast:
    """提示消息"""
    
    def __init__(self):
        self.messages: List[Tuple[str, float, str]] = []  # (message, timer, type)
        self.duration = 3.0
        
    def show(self, message: str, msg_type: str = 'info'):
        self.messages.append((message, self.duration, msg_type))
        
    def update(self, dt: float):
        self.messages = [(msg, timer - dt, t) for msg, timer, t in self.messages if timer > 0]
        
    def draw(self, surface: pygame.Surface):
        font = get_font(24)
        y = 50
        
        for message, timer, msg_type in self.messages:
            if msg_type == 'success':
                color = COLORS['success']
            elif msg_type == 'error':
                color = COLORS['error']
            else:
                color = COLORS['accent']
            
            text = font.render(message, True, color)
            
            rect = pygame.Rect(
                WINDOW_WIDTH // 2 - text.get_width() // 2 - 15,
                y,
                text.get_width() + 30,
                text.get_height() + 16
            )
            
            # 背景
            pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=4)
            pygame.draw.rect(surface, color, rect, 1, border_radius=4)
            
            surface.blit(text, (rect.x + 15, rect.y + 8))
            y += rect.height + 5


class ConfirmDialog(Panel):
    """确认对话框"""
    
    def __init__(self, title: str, message: str, 
                 on_confirm: Callable = None, on_cancel: Callable = None):
        width, height = 400, 200
        x = (WINDOW_WIDTH - width) // 2
        y = (WINDOW_HEIGHT - height) // 2
        super().__init__(x, y, width, height, title)
        
        self.message = message
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        
        # 消息标签
        msg_label = Label(x + width // 2, y + 80, message, 
                         font_size=24, centered=True)
        self.add_child(msg_label)
        
        # 确认按钮
        confirm_btn = Button(x + 50, y + 140, 120, 40, "确认",
                            self._confirm, COLORS['success'])
        self.add_child(confirm_btn)
        
        # 取消按钮
        cancel_btn = Button(x + width - 170, y + 140, 120, 40, "取消",
                           self._cancel)
        self.add_child(cancel_btn)
    
    def _confirm(self):
        if self.on_confirm:
            self.on_confirm()
        self.visible = False
    
    def _cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self.visible = False


class HintPanel(Panel):
    """提示面板"""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height, "提示")
        self.hints: List[str] = []
        self.current_hint = 0
        
    def set_hints(self, hints: List[str]):
        self.hints = hints
        self.current_hint = 0
        self._update_display()
    
    def next_hint(self):
        if self.current_hint < len(self.hints) - 1:
            self.current_hint += 1
            self._update_display()
    
    def _update_display(self):
        # 清除旧内容
        self.children.clear()
        
        if not self.hints:
            return
        
        # 提示内容
        hint_text = self.hints[self.current_hint]
        lines = self._wrap_text(hint_text, self.width - 30)
        
        y_offset = 45
        for line in lines:
            label = Label(self.x + 15, self.y + y_offset, line, 
                         font_size=20, color=COLORS['text'])
            self.add_child(label)
            y_offset += 25
        
        # 提示进度
        progress_text = f"提示 {self.current_hint + 1}/{len(self.hints)}"
        progress_label = Label(self.x + self.width - 80, self.y + self.height - 30,
                              progress_text, font_size=18, color=COLORS['text_secondary'])
        self.add_child(progress_label)
        
        # 下一个按钮
        if self.current_hint < len(self.hints) - 1:
            next_btn = Button(self.x + 15, self.y + self.height - 45, 80, 30,
                             "下一个", self.next_hint)
            next_btn.font_size = 18
            self.add_child(next_btn)
    
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """文本换行"""
        font = get_font(20)
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines


class ColorPicker(Panel):
    """颜色选择器"""
    
    def __init__(self, x: int, y: int, on_select: Callable = None):
        super().__init__(x, y, 180, 120, "选择颜色")
        self.on_select = on_select
        self.selected_color = 'white'
        self._create_buttons()
        
    def _create_buttons(self):
        colors = SHAPE_COLORS
        cols = 4
        btn_size = 35
        padding = 5
        
        for i, color in enumerate(colors):
            col = i % cols
            row = i // cols
            x = self.x + 15 + col * (btn_size + padding)
            y = self.y + 45 + row * (btn_size + padding)
            
            btn = Button(x, y, btn_size, btn_size, "",
                        lambda c=color: self._on_color_click(c),
                        COLORS.get(f'shape_{color}', COLORS['shape_white']))
            btn.border_radius = btn_size // 2
            self.add_child(btn)
    
    def _on_color_click(self, color: str):
        self.selected_color = color
        if self.on_select:
            self.on_select(color)


class TutorialOverlay:
    """新手教程引导覆盖层"""
    
    def __init__(self):
        self.active = False
        self.current_step = 0
        self.steps: List[Dict[str, Any]] = []
        self.on_complete: Optional[Callable] = None
        self.highlight_rect: Optional[pygame.Rect] = None
        
    def start_tutorial(self, tutorial_id: str, on_complete: Callable = None):
        """启动教程"""
        self.on_complete = on_complete
        self.current_step = 0
        
        if tutorial_id == 'first_level':
            self.steps = [
                {
                    'title': '🎮 欢迎来到 PyFactory!',
                    'content': '这是一个通过建造工厂来学习Python编程的游戏。\n\n你的目标是：将基础图形加工成目标图形！',
                    'highlight': None,
                    'position': 'center'
                },
                {
                    'title': '🎯 查看目标',
                    'content': '右上角显示的是本关需要生产的目标图形。\n\n你需要建造工厂来生产这个图形！',
                    'highlight': 'target',
                    'position': 'left'
                },
                {
                    'title': '🔧 选择机器',
                    'content': '左侧是机器选择面板。\n\n【基础】源头 - 产生图形\n【基础】输出口 - 收集产品\n【基础】传送带 - 连接机器',
                    'highlight': 'machine_selector',
                    'position': 'right'
                },
                {
                    'title': '📍 放置机器',
                    'content': '1. 点击左侧选择"源头"机器\n2. 在网格中点击放置\n3. 再放置一个"输出口"',
                    'highlight': 'grid',
                    'position': 'right'
                },
                {
                    'title': '🔗 连接机器',
                    'content': '放置机器后，右键点击机器可以：\n\n• 开始连接 - 连接到另一台机器\n• 删除机器 - 移除这台机器\n• 设置参数 - 配置机器属性',
                    'highlight': 'grid',
                    'position': 'right'
                },
                {
                    'title': '▶️ 运行工厂',
                    'content': '点击上方的 ▶ 按钮启动工厂！\n\n图形会从源头产生，经过加工后到达输出口。\n当输出正确的图形后，关卡完成！',
                    'highlight': 'controls',
                    'position': 'bottom'
                },
                {
                    'title': '💡 获取提示',
                    'content': '遇到困难？点击"提示"按钮查看帮助！\n\n每个关卡都有对应的Python代码示例，\n点击"代码"按钮可以查看。',
                    'highlight': 'hint_btn',
                    'position': 'left'
                },
                {
                    'title': '🚀 开始游戏！',
                    'content': '现在你已经了解了基本操作。\n\n试着完成第一个关卡吧！\n\n提示：放置 源头 → 输出口，然后连接它们。',
                    'highlight': None,
                    'position': 'center'
                }
            ]
        elif tutorial_id == 'quick_guide':
            self.steps = [
                {
                    'title': '⚡ 快速指南',
                    'content': '【左键】选择/放置机器\n【右键】连接/删除机器\n【▶】运行工厂\n【⏸】暂停工厂\n【↺】重置工厂',
                    'highlight': None,
                    'position': 'center'
                }
            ]
        else:
            self.steps = []
            
        self.active = len(self.steps) > 0
    
    def next_step(self):
        """下一步"""
        self.current_step += 1
        if self.current_step >= len(self.steps):
            self.active = False
            if self.on_complete:
                self.on_complete()
    
    def prev_step(self):
        """上一步"""
        if self.current_step > 0:
            self.current_step -= 1
    
    def skip(self):
        """跳过教程"""
        self.active = False
        if self.on_complete:
            self.on_complete()
    
    def set_highlight_rect(self, name: str, rect: pygame.Rect):
        """设置高亮区域"""
        if self.active and self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            if step.get('highlight') == name:
                self.highlight_rect = rect
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.active:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.next_step()
                return True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.skip()
                return True
            elif event.key == pygame.K_LEFT:
                self.prev_step()
                return True
            elif event.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
                self.next_step()
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface):
        if not self.active or self.current_step >= len(self.steps):
            return
        
        step = self.steps[self.current_step]
        
        # 半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        
        # 如果有高亮区域，在遮罩上挖洞
        if self.highlight_rect:
            # 扩大高亮区域
            hr = self.highlight_rect.inflate(20, 20)
            pygame.draw.rect(overlay, (0, 0, 0, 0), hr)
        
        surface.blit(overlay, (0, 0))
        
        # 高亮边框
        if self.highlight_rect:
            hr = self.highlight_rect.inflate(20, 20)
            pygame.draw.rect(surface, COLORS['accent'], hr, 3, border_radius=8)
        
        # 对话框位置
        dialog_width = 450
        dialog_height = 220
        position = step.get('position', 'center')
        
        if position == 'center':
            dialog_x = (WINDOW_WIDTH - dialog_width) // 2
            dialog_y = (WINDOW_HEIGHT - dialog_height) // 2
        elif position == 'left':
            dialog_x = 50
            dialog_y = (WINDOW_HEIGHT - dialog_height) // 2
        elif position == 'right':
            dialog_x = WINDOW_WIDTH - dialog_width - 50
            dialog_y = (WINDOW_HEIGHT - dialog_height) // 2
        elif position == 'bottom':
            dialog_x = (WINDOW_WIDTH - dialog_width) // 2
            dialog_y = WINDOW_HEIGHT - dialog_height - 80
        else:
            dialog_x = (WINDOW_WIDTH - dialog_width) // 2
            dialog_y = (WINDOW_HEIGHT - dialog_height) // 2
        
        # 绘制对话框
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(surface, COLORS['panel_bg'], dialog_rect, border_radius=12)
        pygame.draw.rect(surface, COLORS['accent'], dialog_rect, 3, border_radius=12)
        
        # 标题
        title_font = get_font(32)
        title_surface = title_font.render(step['title'], True, COLORS['accent'])
        surface.blit(title_surface, (dialog_x + 20, dialog_y + 15))
        
        # 内容
        content_font = get_font(22)
        content_lines = step['content'].split('\n')
        y_offset = 60
        for line in content_lines:
            if line:
                text_surface = content_font.render(line, True, COLORS['text'])
                surface.blit(text_surface, (dialog_x + 20, dialog_y + y_offset))
            y_offset += 28
        
        # 底部提示
        hint_font = get_font(18)
        progress_text = f"第 {self.current_step + 1} / {len(self.steps)} 步"
        progress_surface = hint_font.render(progress_text, True, COLORS['text_secondary'])
        surface.blit(progress_surface, (dialog_x + 20, dialog_y + dialog_height - 35))
        
        nav_text = "点击继续 | ESC跳过 | ←→切换"
        nav_surface = hint_font.render(nav_text, True, COLORS['text_secondary'])
        surface.blit(nav_surface, (dialog_x + dialog_width - nav_surface.get_width() - 20, 
                                   dialog_y + dialog_height - 35))


# 全局Toast实例
toast = Toast()

# 全局教程实例
tutorial = TutorialOverlay()
