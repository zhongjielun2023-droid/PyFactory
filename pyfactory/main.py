"""
PyFactory - Python工厂教学游戏
主程序入口

一款面向青少年的Python教学游戏，通过工厂建造和图形加工来学习编程概念。
灵感来自异形工厂(Shapez.io)。

教学大纲参考：全国计算机等级考试二级Python
"""

import pygame
import sys
import json
import time
from typing import Optional, List, Dict, Any

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, FPS,
    COLORS, GRID_SIZE, GRID_COLS, GRID_ROWS,
    MACHINE_TYPES, LEVEL_CATEGORIES, STAR_FULL, STAR_EMPTY, DEBUG
)
from shapes import Shape, create_shape, create_random_shape
from machines import Machine, create_machine, SourceMachine, OutputMachine
from game_engine import game_engine, code_executor, Factory, Level
from database import db
from ui import (
    Button, Panel, Label, TextInput, ScrollPanel,
    MachineSelector, CodeEditor, Toast, toast,
    ConfirmDialog, HintPanel, ColorPicker, IconButton,
    TutorialOverlay, tutorial, AchievementDialog
)
from ui import clear_tooltip
from fonts import get_font
from code_parser import parser as code_parser, get_template

# DEBUG is provided by config.DEBUG


class GameScene:
    """游戏场景基类"""
    
    def __init__(self, game: 'PyFactoryGame'):
        self.game = game
        
    def handle_event(self, event: pygame.event.Event):
        pass
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        pass


class LoginScene(GameScene):
    """登录场景"""
    
    def __init__(self, game: 'PyFactoryGame'):
        super().__init__(game)
        self._create_ui()
    
    def _create_ui(self):
        w = self.game.window_width if hasattr(self.game, 'window_width') else WINDOW_WIDTH
        h = self.game.window_height if hasattr(self.game, 'window_height') else WINDOW_HEIGHT
        
        center_x = w // 2
        center_y = h // 2
        
        # 标题
        self.title_label = Label(center_x, 150, "PyFactory", 
                                font_size=72, color=COLORS['accent'], centered=True)
        self.subtitle_label = Label(center_x, 210, "Python工厂教学游戏",
                                   font_size=32, color=COLORS['text_secondary'], centered=True)
        
        # 登录表单
        self.username_input = TextInput(center_x - 150, center_y - 60, 300, 45, "用户名")
        self.password_input = TextInput(center_x - 150, center_y, 300, 45, "密码", is_password=True)
        
        self.login_btn = Button(center_x - 150, center_y + 70, 300, 50, "登录", self._on_login)
        
        self.error_label = Label(center_x, center_y + 140, "", 
                                font_size=20, color=COLORS['error'], centered=True)
        
        # 提示信息
        self.hint_label = Label(center_x, h - 50, 
                               "默认账号: x  密码: 1",
                               font_size=18, color=COLORS['text_secondary'], centered=True)
        
        # 预填默认账号
        self.username_input.text = "x"
        self.password_input.text = "1"
    
    def on_resize(self, width: int, height: int):
        """窗口大小变化时更新布局"""
        self._create_ui()
    
    def _on_login(self):
        username = self.username_input.text.strip()
        password = self.password_input.text
        
        if not username:
            self.error_label.text = "请输入用户名"
            return
        
        if game_engine.login(username, password):
            self.game.switch_scene('menu')
            toast.show(f"欢迎回来, {username}!", 'success')
        else:
            self.error_label.text = "用户名或密码错误"
    
    def handle_event(self, event: pygame.event.Event):
        self.username_input.handle_event(event)
        self.password_input.handle_event(event)
        self.login_btn.handle_event(event)
        
        # 回车登录
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self._on_login()
    
    def update(self, dt: float):
        self.username_input.update(dt)
        self.password_input.update(dt)
    
    def draw(self, surface: pygame.Surface):
        # 背景
        surface.fill(COLORS['background'])
        
        # 装饰图形
        self._draw_decoration(surface)
        
        # UI元素
        self.title_label.draw(surface)
        self.subtitle_label.draw(surface)
        self.username_input.draw(surface)
        self.password_input.draw(surface)
        self.login_btn.draw(surface)
        self.error_label.draw(surface)
        self.hint_label.draw(surface)
    
    def _draw_decoration(self, surface: pygame.Surface):
        """绘制装饰性图形"""
        shapes_data = [
            ('circle', 'red', 100, 300),
            ('square', 'blue', 150, 500),
            ('triangle', 'green', WINDOW_WIDTH - 120, 280),
            ('diamond', 'yellow', WINDOW_WIDTH - 180, 450),
            ('star', 'purple', 80, 600),
            ('hexagon', 'orange', WINDOW_WIDTH - 100, 620),
        ]
        
        for shape_type, color, x, y in shapes_data:
            shape = create_shape(shape_type, color)
            shape.draw(surface, x, y, 0.8)


class MenuScene(GameScene):
    """主菜单场景"""
    
    def __init__(self, game: 'PyFactoryGame'):
        super().__init__(game)
        self._create_ui()
    
    def _create_ui(self):
        w = self.game.window_width if hasattr(self.game, 'window_width') else WINDOW_WIDTH
        h = self.game.window_height if hasattr(self.game, 'window_height') else WINDOW_HEIGHT
        
        center_x = w // 2
        
        # 标题
        self.title = Label(center_x, 80, "PyFactory", 
                          font_size=64, color=COLORS['accent'], centered=True)
        
        # 用户信息
        username = game_engine.current_user.get('username', '') if game_engine.current_user else ''
        self.user_label = Label(w - 150, 20, f"用户: {username}",
                               font_size=20, color=COLORS['text_secondary'])
        
        # 菜单按钮 - 自适应布局
        btn_width = min(300, w - 100)
        btn_height = 55
        btn_x = center_x - btn_width // 2
        btn_spacing = 70
        start_y = 180
        
        self.demo_btn = Button(btn_x, start_y, btn_width, btn_height,
                               "[新手演示]", lambda: self.game.switch_scene('demo'),
                               color=COLORS['success'])
        self.level_btn = Button(btn_x, start_y + btn_spacing, btn_width, btn_height, 
                               "关卡模式", lambda: self.game.switch_scene('level_select'))
        self.sandbox_btn = Button(btn_x, start_y + btn_spacing * 2, btn_width, btn_height,
                                 "沙盒模式", self._start_sandbox)
        self.blueprint_btn = Button(btn_x, start_y + btn_spacing * 3, btn_width, btn_height,
                                   "我的蓝图", lambda: self.game.switch_scene('blueprints'))
        self.achievement_btn = Button(btn_x, start_y + btn_spacing * 4, btn_width, btn_height,
                                     "成就", lambda: self.game.switch_scene('achievements'))
        self.logout_btn = Button(btn_x, start_y + btn_spacing * 5, btn_width, btn_height,
                                "退出登录", self._logout)
        
        self.buttons = [
            self.demo_btn, self.level_btn, self.sandbox_btn, self.blueprint_btn,
            self.achievement_btn, self.logout_btn
        ]
        
        # 进度统计
        self._load_stats()
    
    def on_resize(self, width: int, height: int):
        """窗口大小变化时更新布局"""
        self._create_ui()
    
    def _load_stats(self):
        progress = game_engine.get_user_progress()
        completed = sum(1 for p in progress.values() if p.get('completed'))
        total = len(game_engine.get_levels())
        total_stars = sum(p.get('stars', 0) for p in progress.values())
        
        self.stats_label = Label(WINDOW_WIDTH // 2, 140,
                                f"进度: {completed}/{total} 关卡  星{total_stars}",
                                font_size=24, color=COLORS['text_secondary'], centered=True)
    
    def _start_sandbox(self):
        game_engine.start_sandbox()
        self.game.switch_scene('game')
    
    def _logout(self):
        game_engine.logout()
        self.game.switch_scene('login')
        toast.show("已退出登录")
    
    def handle_event(self, event: pygame.event.Event):
        for btn in self.buttons:
            btn.handle_event(event)
    
    def draw(self, surface: pygame.Surface):
        surface.fill(COLORS['background'])
        
        self.title.draw(surface)
        self.user_label.draw(surface)
        self.stats_label.draw(surface)
        
        for btn in self.buttons:
            btn.draw(surface)


class LevelSelectScene(GameScene):
    """关卡选择场景"""
    
    def __init__(self, game: 'PyFactoryGame'):
        super().__init__(game)
        self.current_category = 'basics'
        self._create_ui()
    
    def _create_ui(self):
        w = self.game.window_width if hasattr(self.game, 'window_width') else WINDOW_WIDTH
        h = self.game.window_height if hasattr(self.game, 'window_height') else WINDOW_HEIGHT
        
        # 返回按钮
        self.back_btn = Button(20, 20, 100, 40, "← 返回",
                              lambda: self.game.switch_scene('menu'))
        self.back_btn.font_size = 20
        
        # 标题
        self.title = Label(w // 2, 40, "选择关卡",
                          font_size=48, color=COLORS['accent'], centered=True)
        
        # 类别标签页
        self.category_buttons: List[Button] = []
        self._create_category_tabs()
        
        # 关卡网格
        self.level_panel = ScrollPanel(50, 150, w - 100, h - 180)
        self._load_levels()
    
    def on_resize(self, width: int, height: int):
        """窗口大小变化时更新布局"""
        self._create_ui()
    
    def _create_category_tabs(self):
        x = 50
        for cat_id, cat_name in LEVEL_CATEGORIES.items():
            btn = Button(x, 100, 120, 35, cat_name,
                        lambda c=cat_id: self._select_category(c))
            btn.font_size = 18
            self.category_buttons.append(btn)
            x += 130
    
    def _select_category(self, category: str):
        self.current_category = category
        self._load_levels()
    
    def _load_levels(self):
        self.level_panel.children.clear()
        
        levels = game_engine.get_levels_by_category(self.current_category)
        progress = game_engine.get_user_progress()
        
        y = self.level_panel.y + 20
        for i, level in enumerate(levels):
            level_progress = progress.get(level['id'], {})
            completed = level_progress.get('completed', False)
            stars = level_progress.get('stars', 0)
            
            # 关卡卡片
            card = self._create_level_card(level, completed, stars, 
                                          self.level_panel.x + 20, y)
            self.level_panel.add_child(card)
            y += 90
        
        self.level_panel.content_height = y - self.level_panel.y
    
    def _create_level_card(self, level: Dict, completed: bool, stars: int,
                          x: int, y: int) -> Panel:
        card = Panel(x, y, self.level_panel.width - 60, 80)
        card.bg_color = COLORS['button_hover'] if completed else COLORS['panel_bg']
        
        # 关卡标题
        title = Label(x + 15, y + 15, level['title'], font_size=24)
        card.add_child(title)
        
        # 描述
        desc = Label(x + 15, y + 42, level.get('description', '')[:50] + '...',
                    font_size=18, color=COLORS['text_secondary'])
        card.add_child(desc)
        
        # 星星（已改为实心星/空心星）
        if completed:
            star_text = STAR_FULL * stars + STAR_EMPTY * (3 - stars)
        else:
            star_text = STAR_EMPTY * 3
        star_label = Label(x + card.width - 100, y + 25, star_text, font_size=24)
        card.add_child(star_label)
        
        # 难度
        diff = "●" * level.get('difficulty', 1) + "○" * (5 - level.get('difficulty', 1))
        diff_label = Label(x + card.width - 100, y + 50, diff,
                          font_size=14, color=COLORS['warning'])
        card.add_child(diff_label)
        
        # 开始按钮
        start_btn = Button(x + card.width - 180, y + 20, 70, 40, "开始",
                          lambda lid=level['id']: self._start_level(lid))
        start_btn.font_size = 18
        card.add_child(start_btn)
        
        return card
    
    def _start_level(self, level_id: str):
        if game_engine.load_level(level_id):
            self.game.switch_scene('game')
        else:
            toast.show("加载关卡失败", 'error')
    
    def handle_event(self, event: pygame.event.Event):
        self.back_btn.handle_event(event)
        self.level_panel.handle_event(event)
        
        for btn in self.category_buttons:
            btn.handle_event(event)
    
    def draw(self, surface: pygame.Surface):
        surface.fill(COLORS['background'])
        
        self.back_btn.draw(surface)
        self.title.draw(surface)
        
        # 高亮当前类别
        for btn in self.category_buttons:
            if btn.text == LEVEL_CATEGORIES.get(self.current_category):
                btn.color = COLORS['accent']
            else:
                btn.color = COLORS['button_normal']
            btn.draw(surface)
        
        self.level_panel.draw(surface)


class GameScene_(GameScene):
    """游戏主场景"""
    
    def __init__(self, game: 'PyFactoryGame'):
        super().__init__(game)
        
        # 可调整的布局参数
        self.code_panel_width = 280  # 代码面板宽度
        self.hint_panel_width = 270  # 提示面板宽度
        self.task_panel_width = 250   # 任务面板宽度
        self.task_panel_height = 200  # 任务面板高度
        self.programming_panel_width = 300  # 编程模式面板宽度
        self.programming_panel_height = 250 # 编程模式面板高度
        
        # 网格区域（动态计算）
        self._update_layout()
        
        # 操作提示面板内容（编程模式区文字内容）
        self.programming_hints = [
            "代码编程模式说明：",
            "────────────────",
            "• 编写Python代码创建机器",
            "• 代码实时生成工厂布局", 
            "• 点击[运行]启动工厂",
            "────────────────",
            "可用机器类型：",
            "  Source(shape, color) - 源头",
            "  Painter(color) - 喷漆机",
            "  Rotator(angle) - 旋转机",
            "  Output() - 输出口",
            "────────────────",
            "连接语法：",
            "  machine1.connect(machine2)"
        ]
        
        # 代码编辑器（python代码区）
        self.code_editor = CodeEditor(10, 60, self.code_panel_width - 20, WINDOW_HEIGHT - 80, self._on_code_change)
        self.code_editor.visible = True
        self.code_editor.title = "Python代码"
        
        # 提示面板（提示区）
        self.hint_panel = HintPanel(WINDOW_WIDTH - self.hint_panel_width - 10, 60, self.hint_panel_width, 200)
        self.hint_panel.visible = True
        
        # 任务面板（任务区 - 位于提示区位置，当提示区退出后显示）
        self.task_panel = Panel(WINDOW_WIDTH - self.hint_panel_width - 10, 60,
                               self.hint_panel_width, 200, "")
        
        # 编程模式面板（编程模式区 - 位于任务区正下方并填满）
        self.programming_panel = Panel(WINDOW_WIDTH - self.hint_panel_width - 10, 
                                     60 + 200 + 10,  # 任务区底部 + 间距
                                     self.hint_panel_width, 
                                     WINDOW_HEIGHT - (60 + 200 + 10) - 10,  # 从任务区底部到窗口底部
                                     "")
        
        # 分割条（可拖动调整大小）
        from ui import Splitter
        self.left_splitter = Splitter(
            self.code_panel_width, 60, WINDOW_HEIGHT - 80,
            orientation='vertical',
            min_pos=150, max_pos=500,
            on_drag=self._on_left_splitter_drag
        )
        # 右侧区域宽度分割条（控制任务区和编程模式区的宽度）
        self.right_area_splitter = Splitter(
            WINDOW_WIDTH - self.hint_panel_width - 10, 60, WINDOW_HEIGHT - 80,
            orientation='vertical',
            min_pos=WINDOW_WIDTH - 400, max_pos=WINDOW_WIDTH - 150,
            on_drag=self._on_right_area_splitter_drag
        )
        
        # 控制按钮
        self._create_control_buttons()
        
        # 状态
        self.selected_machine_type: Optional[str] = None
        self.selected_machine: Optional[Machine] = None
        self.is_connecting = False
        self.connection_start: Optional[Machine] = None
        self.mouse_grid_pos = (0, 0)
        
        # 目标显示
        self.target_shape: Optional[Shape] = None
        
        # 成就对话框
        self.achievement_dialog: Optional[AchievementDialog] = None
        
        # 加载当前关卡信息
        self._load_level_info()
    
    def _create_control_buttons(self):
        btn_y = 15
        btn_size = 36
        
        # 返回按钮（固定左上角）
        self.back_btn = Button(10, btn_y, 70, 32, "← 返回", self._on_back)
        self.back_btn.font_size = 16
        
        # 运行控制按钮组
        self.play_btn = IconButton(0, btn_y, btn_size, "▶", self._on_play, "运行")
        self.pause_btn = IconButton(0, btn_y, btn_size, "⏸", self._on_pause, "暂停")
        self.reset_btn = IconButton(0, btn_y, btn_size, "↺", self._on_reset, "重置")
        
        # 速度控制
        self.speed_label = Label(0, btn_y + 10, "1x", font_size=16)
        self.speed_down_btn = IconButton(0, btn_y, 30, "-", self._speed_down, "减速")
        self.speed_up_btn = IconButton(0, btn_y, 30, "+", self._speed_up, "加速")
        
        # 工具按钮（简化）
        self.code_btn = Button(0, btn_y, 60, 32, "代码", self._toggle_code_editor)
        self.code_btn.font_size = 16
        
        self.hint_btn = Button(0, btn_y, 60, 32, "提示", self._toggle_hints)
        self.hint_btn.font_size = 16
        
        self.save_btn = Button(0, btn_y, 60, 32, "保存", self._save_blueprint)
        self.save_btn.font_size = 16
        
        self.help_btn = Button(0, btn_y, 40, 32, "?", self._show_tutorial)
        self.help_btn.font_size = 16
        
        self.control_buttons = [
            self.back_btn, self.play_btn, self.pause_btn, self.reset_btn,
            self.speed_down_btn, self.speed_up_btn,
            self.code_btn, self.hint_btn, self.save_btn, self.help_btn
        ]
        
        # 立即更新按钮位置
        self._update_button_positions()
    
    def _update_layout(self):
        """更新布局（当分割条拖动或窗口大小变化时调用）"""
        w = self.game.window_width if hasattr(self.game, 'window_width') else WINDOW_WIDTH
        h = self.game.window_height if hasattr(self.game, 'window_height') else WINDOW_HEIGHT
        
        self.grid_x = self.code_panel_width + 15
        self.grid_y = 60
        available_width = w - self.code_panel_width - self.hint_panel_width - 30
        self.grid_width = min(GRID_COLS * GRID_SIZE, available_width)
        self.grid_height = min(GRID_ROWS * GRID_SIZE, h - 100)
    
    def on_resize(self, width: int, height: int):
        """窗口大小变化时更新布局"""
        # 更新代码编辑器高度
        self.code_editor.height = height - 80
        
        # 更新提示面板位置
        self.hint_panel.x = width - self.hint_panel_width - 10
        
        # 更新任务面板位置（与提示面板同步）
        self.task_panel.x = width - self.hint_panel_width - 10
        
        # 更新编程模式面板位置和大小（位于任务区正下方并填满）
        self.programming_panel.x = width - self.hint_panel_width - 10
        self.programming_panel.y = 60 + 200 + 10
        self.programming_panel.width = self.hint_panel_width
        self.programming_panel.height = height - (60 + 200 + 10) - 10
        
        # 更新分割条
        self.left_splitter.height = height - 80
        self.right_area_splitter.height = height - 80
        self.right_area_splitter.center_x = width - self.hint_panel_width - 10
        self.right_area_splitter.x = self.right_area_splitter.center_x - 8
        self.right_area_splitter.visual_x = self.right_area_splitter.center_x - 3
        self.right_area_splitter.max_pos = width - 150
        self.right_area_splitter.min_pos = width - 400
        
        # 更新布局
        self._update_layout()
        self._update_button_positions()
    
    def _on_left_splitter_drag(self, new_x: int):
        """左侧分割条拖动回调（只调整Python代码区宽度，不影响其他UI）"""
        self.code_panel_width = new_x
        
        # 更新代码编辑器大小
        self.code_editor.width = self.code_panel_width - 20
        
        # 更新控制按钮位置
        self._update_button_positions()
    
    def _on_right_area_splitter_drag(self, new_x: int):
        """右侧区域宽度分割条拖动回调（同时调整任务区和编程模式区的宽度）"""
        w = self.game.window_width if hasattr(self.game, 'window_width') else WINDOW_WIDTH
        self.hint_panel_width = w - new_x - 10
        self._update_layout()
        # 更新提示面板位置和大小
        self.hint_panel.x = new_x + 10
        self.hint_panel.width = self.hint_panel_width
        # 更新任务面板位置和大小（与提示面板同步）
        self.task_panel.x = new_x + 10
        self.task_panel.width = self.hint_panel_width
        # 更新编程模式面板位置和大小
        self.programming_panel.x = new_x + 10
        self.programming_panel.width = self.hint_panel_width
        # 更新分割条位置
        self.right_area_splitter.x = new_x
    
    def _update_button_positions(self):
        """更新控制按钮位置 - 紧凑布局"""
        x = self.grid_x + 5
        gap = 5
        
        # 运行控制
        self.play_btn.x = x
        x += self.play_btn.width + gap
        self.pause_btn.x = x
        x += self.pause_btn.width + gap
        self.reset_btn.x = x
        x += self.reset_btn.width + gap + 10
        
        # 速度控制
        self.speed_down_btn.x = x
        x += self.speed_down_btn.width + 2
        self.speed_label.x = x
        x += 25
        self.speed_up_btn.x = x
        x += self.speed_up_btn.width + gap + 10
        
        # 工具按钮
        self.code_btn.x = x
        x += self.code_btn.width + gap
        self.hint_btn.x = x
        x += self.hint_btn.width + gap
        self.save_btn.x = x
        x += self.save_btn.width + gap
        self.help_btn.x = x
    
    def _load_level_info(self):
        if game_engine.current_level:
            level = game_engine.current_level
            self.target_shape = level.get_target_shape()
            self.hint_panel.set_hints(level.hints)
            
            # 使用代码模板
            template = get_template(level.id)
            self.code_editor.set_code(template)
            self.hint_panel.visible = True
            
            # 解析初始代码
            self._on_code_change(template)
        else:
            self.target_shape = None
            self.hint_panel.visible = False
            # 沙盒模式的默认代码
            default_code = '''# 沙盒模式 - 自由创作
source = Source("circle", "white")
output = Output()
source.connect(output)
'''
            self.code_editor.set_code(default_code)
            self._on_code_change(default_code)
    
    def _on_code_change(self, code: str):
        """代码变化时实时解析并更新工厂布局"""
        # 解析代码
        machines, connections, error, error_line = code_parser.parse(code)
        
        # 更新编辑器错误显示
        self.code_editor.error_line = error_line
        self.code_editor.error_msg = error or ""
        
        if error:
            return  # 有错误时不更新工厂

        # 如果解析结果为空且代码不是空（例如正在输入的不完整语句），
        # 则不立即清空工厂，避免输入过程中画面闪烁或消失。
        if not machines and not connections:
            # 代码为空则清空工厂；否则保留当前工厂直到有有效解析
            if not code.strip():
                factory = game_engine.get_current_factory()
                factory.clear()
            return

        # 清空当前工厂（开始用解析结果重建）
        factory = game_engine.get_current_factory()
        # 使用工厂的 clear() 方法以确保 grid 等内部结构也被清理
        factory.clear()

        if DEBUG:
            # 调试输出，便于定位解析与构建问题
            print(f"[DEBUG] _on_code_change: code lines={len(code.splitlines())}, machines_parsed={len(machines)}, connections_parsed={len(connections)}")
        
        # 根据解析结果创建机器
        machine_objects = []
        for m_config in machines:
            machine = create_machine(m_config['type'], m_config['x'], m_config['y'])
            if machine:
                # 设置机器特定参数
                if m_config['type'] == 'source':
                    machine.shape_type = m_config.get('shape_type', 'circle')
                    machine.color = m_config.get('color', 'white')
                elif m_config['type'] == 'painter':
                    machine.target_color = m_config.get('target_color', 'red')
                elif m_config['type'] == 'rotator':
                    machine.rotation_amount = m_config.get('rotation', 90)
                
                added = factory.add_machine(machine)
                if not added:
                    print(f"[WARN] 无法添加机器到工厂: {machine.machine_type} at ({machine.x},{machine.y}) - 位置已被占用")
                else:
                    machine_objects.append(machine)
        
        # 创建连接
        for from_idx, to_idx in connections:
            if from_idx < len(machine_objects) and to_idx < len(machine_objects):
                factory.connect(machine_objects[from_idx], machine_objects[to_idx])

        # 若当前处于关卡模式且关卡定义了目标形状，
        # 将目标形状分配到所有 OutputMachine 上以便匹配计数。
        try:
            if game_engine.mode == 'playing' and game_engine.current_level:
                lvl = game_engine.current_level
                if getattr(lvl, 'target_data', {}) and 'shape' in lvl.target_data:
                    target_shape = lvl._create_target_shape()
                    required = lvl.target_data.get('count', 1)
                    for m in factory.machines:
                        if isinstance(m, OutputMachine):
                            m.set_target(target_shape, required)
                            if DEBUG:
                                print(f"[DEBUG] _on_code_change: set target on OutputMachine at ({m.x},{m.y}) -> {target_shape!r}, count={required}")
        except Exception as e:
            print(f"[DEBUG] _on_code_change: failed to set output target: {e}")
    
    def _on_color_select(self, color: str):
        if self.selected_machine:
            from machines import PainterMachine, SourceMachine
            if isinstance(self.selected_machine, PainterMachine):
                self.selected_machine.target_color = color
                toast.show(f"颜色设置为: {color}")
            elif isinstance(self.selected_machine, SourceMachine):
                self.selected_machine.color = color
                toast.show(f"源头颜色设置为: {color}")
    
    def _on_achievement_auto_action(self):
        """成就对话框自动触发返回回调"""
        # 关闭对话框并返回到关卡选择页面
        self.achievement_dialog = None
        self._on_back()
    
    def _on_achievement_confirm(self):
        """成就对话框确定按钮回调"""
        # 关闭对话框并返回到关卡选择页面
        self.achievement_dialog = None
        self._on_back()
    
    def _on_back(self):
        game_engine.stop_factory()
        if game_engine.mode == 'playing':
            self.game.switch_scene('level_select')
        else:
            self.game.switch_scene('menu')
    
    def _on_play(self):
        game_engine.run_factory()
        toast.show("工厂已启动", 'success')
    
    def _on_pause(self):
        game_engine.stop_factory()
        toast.show("工厂已暂停")
    
    def _on_reset(self):
        game_engine.reset_factory()
        toast.show("工厂已重置")
    
    def _speed_down(self):
        factory = game_engine.get_current_factory()
        factory.speed = max(0.25, factory.speed / 2)
        self.speed_label.text = f"速度: {factory.speed}x"
    
    def _speed_up(self):
        factory = game_engine.get_current_factory()
        factory.speed = min(4.0, factory.speed * 2)
        self.speed_label.text = f"速度: {factory.speed}x"
    
    def _toggle_code_editor(self):
        self.code_editor.visible = not self.code_editor.visible
    
    def _toggle_hints(self):
        self.hint_panel.visible = not self.hint_panel.visible
    
    def _save_blueprint(self):
        if game_engine.save_blueprint("我的蓝图", "自动保存"):
            toast.show("蓝图已保存", 'success')
        else:
            toast.show("保存失败", 'error')
    
    def _show_tutorial(self):
        """显示教程"""
        tutorial.start_tutorial('first_level')
    
    def _screen_to_grid(self, x: int, y: int) -> tuple:
        """屏幕坐标转网格坐标"""
        grid_x = (x - self.grid_x) // GRID_SIZE
        grid_y = (y - self.grid_y) // GRID_SIZE
        return grid_x, grid_y
    
    def _is_in_grid(self, x: int, y: int) -> bool:
        """检查屏幕坐标是否在网格内"""
        return (self.grid_x <= x < self.grid_x + self.grid_width and
                self.grid_y <= y < self.grid_y + self.grid_height)
    
    def handle_event(self, event: pygame.event.Event):
        # 教程优先处理事件
        if tutorial.active:
            if tutorial.handle_event(event):
                return
        
        # 处理分割条事件（优先级最高）
        # 先让所有分割条都处理MOUSEMOTION以更新hover状态
        left_handled = self.left_splitter.handle_event(event)
        right_area_handled = self.right_area_splitter.handle_event(event)
        
        # 如果分割条正在拖动，阻止其他处理
        if (self.left_splitter.dragging or self.right_area_splitter.dragging):
            return
        
        # 处理UI元素事件（代码编辑器优先）
        self.code_editor.handle_event(event)
        self.hint_panel.handle_event(event)
        
        # 处理成就对话框事件
        if self.achievement_dialog:
            self.achievement_dialog.handle_event(event)
        
        for btn in self.control_buttons:
            btn.handle_event(event)
        
        # 处理网格交互
        if event.type == pygame.MOUSEMOTION:
            if self._is_in_grid(*event.pos):
                self.mouse_grid_pos = self._screen_to_grid(*event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self._is_in_grid(*event.pos):
                grid_x, grid_y = self._screen_to_grid(*event.pos)
                factory = game_engine.get_current_factory()
                
                if event.button == 1:  # 左键
                    existing = factory.get_machine_at(grid_x, grid_y)
                    
                    if self.is_connecting:
                        # 完成连接
                        if existing and existing != self.connection_start:
                            factory.connect(self.connection_start, existing)
                            toast.show("已连接")
                        self.is_connecting = False
                        self.connection_start = None
                    elif existing:
                        # 选择现有机器
                        self.selected_machine = existing
                        self.selected_machine_type = None
                        self._show_machine_options(existing)
                    elif self.selected_machine_type:
                        # 放置新机器
                        machine = game_engine.place_machine(
                            self.selected_machine_type, grid_x, grid_y)
                        if machine:
                            toast.show(f"放置了 {MACHINE_TYPES[self.selected_machine_type]['name']}")
                            self.selected_machine = machine
                
                elif event.button == 3:  # 右键
                    existing = factory.get_machine_at(grid_x, grid_y)
                    if existing:
                        if self.is_connecting:
                            # 取消连接
                            self.is_connecting = False
                            self.connection_start = None
                        else:
                            # 开始连接
                            self.is_connecting = True
                            self.connection_start = existing
                            toast.show("拖动到目标机器以连接")
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                # 删除选中的机器
                if self.selected_machine:
                    factory = game_engine.get_current_factory()
                    factory.remove_machine(self.selected_machine)
                    self.selected_machine = None
                    toast.show("已删除机器")
            
            elif event.key == pygame.K_ESCAPE:
                # 取消选择/连接
                self.selected_machine_type = None
                self.selected_machine = None
                self.is_connecting = False
                self.connection_start = None
    
    def _show_machine_options(self, machine: Machine):
        """显示机器选项（代码驱动模式下不显示）"""
        pass  # 代码驱动模式不需要手动选项
    
    def update(self, dt: float):
        game_engine.update(dt)
        
        # 更新成就对话框
        if self.achievement_dialog:
            self.achievement_dialog.update(dt)
        
        # 检查关卡完成
        if game_engine.mode == 'playing' and game_engine.current_level and not self.achievement_dialog:
            if game_engine.current_level.is_completed:
                stars = game_engine.current_level.calculate_stars()
                stars_str = STAR_FULL * stars if stars > 0 else '无'
                # 显示成就对话框
                self.achievement_dialog = AchievementDialog(
                    "关卡完成！", 
                    "恭喜你成功完成了关卡！", 
                    stars,
                    self._on_achievement_auto_action,
                    self._on_achievement_confirm
                )
                game_engine.stop_factory()
    
    def draw(self, surface: pygame.Surface):
        surface.fill(COLORS['background'])
        
        # 绘制网格
        self._draw_grid(surface)
        
        # 绘制机器（捕获异常以避免单个绘制错误导致画面空白）
        factory = game_engine.get_current_factory()
        for machine in factory.machines:
            try:
                machine.draw(surface, self.grid_x, self.grid_y)
            except Exception as e:
                print(f"绘制机器失败: {e} - {getattr(machine, 'machine_type', None)} at ({getattr(machine, 'x', '?')},{getattr(machine, 'y','?')})")
                # 可视化占位，便于定位问题
                try:
                    import pygame as _pygame
                    rx = machine.x * GRID_SIZE + self.grid_x + 4
                    ry = machine.y * GRID_SIZE + self.grid_y + 4
                    _pygame.draw.rect(surface, (120, 20, 20), _pygame.Rect(rx, ry, GRID_SIZE-8, GRID_SIZE-8))
                except Exception:
                    pass

            # 回退绘制：如果机器自身没有绘制其预览，则在此确保 Source/Painter 的可视化
            try:
                cx = machine.x * GRID_SIZE + self.grid_x + GRID_SIZE // 2
                cy = machine.y * GRID_SIZE + self.grid_y + GRID_SIZE // 2
                if getattr(machine, 'machine_type', None) == 'source':
                    try:
                        preview = create_shape(getattr(machine, 'shape_type', 'circle'), getattr(machine, 'color', 'white'))
                        preview.draw(surface, cx, cy, 0.5)
                    except Exception:
                        pass
                elif getattr(machine, 'machine_type', None) == 'painter':
                    try:
                        color_key = f"shape_{getattr(machine, 'target_color', 'red')}"
                        paint_color = COLORS.get(color_key, COLORS.get('shape_white'))
                        pygame.draw.circle(surface, paint_color, (cx, cy), 12)
                        pygame.draw.circle(surface, COLORS['text'], (cx, cy), 12, 2)
                    except Exception:
                        pass
            except Exception:
                pass

            # 机器标签
            try:
                self._draw_machine_label(surface, machine)
            except Exception:
                pass

        # 绘制连接线（放在机器上层以保证可见）
        for conn in factory.connections:
            try:
                conn.draw(surface, self.grid_x, self.grid_y)
            except Exception as e:
                print(f"绘制连接失败: {e}")
        
        # 绘制正在进行的连接
        if self.is_connecting and self.connection_start:
            start_x = self.connection_start.x * GRID_SIZE + GRID_SIZE // 2 + self.grid_x
            start_y = self.connection_start.y * GRID_SIZE + GRID_SIZE // 2 + self.grid_y
            mouse_pos = pygame.mouse.get_pos()
            pygame.draw.line(surface, COLORS['accent'], 
                           (start_x, start_y), mouse_pos, 3)
        
        # 绘制鼠标位置预览
        if self.selected_machine_type and self._is_in_grid(*pygame.mouse.get_pos()):
            preview_x = self.mouse_grid_pos[0] * GRID_SIZE + self.grid_x
            preview_y = self.mouse_grid_pos[1] * GRID_SIZE + self.grid_y
            rect = pygame.Rect(preview_x + 4, preview_y + 4, GRID_SIZE - 8, GRID_SIZE - 8)
            pygame.draw.rect(surface, (*COLORS['accent'], 100), rect, border_radius=8)
        
        # 绘制UI（代码驱动模式）
        self.code_editor.draw(surface)
        self.hint_panel.draw(surface)
        
        # 绘制任务面板（当提示区隐藏时显示）
        if not self.hint_panel.visible:
            self.task_panel.draw(surface)
            self._draw_task_content(surface)
        
        # 绘制编程模式面板（右下角填满）
        self.programming_panel.draw(surface)
        self._draw_programming_content(surface)
        
        # 绘制成就对话框
        if self.achievement_dialog:
            self.achievement_dialog.draw(surface)
        
        # 绘制分割条
        self.left_splitter.draw(surface)
        self.right_area_splitter.draw(surface)
        
        for btn in self.control_buttons:
            btn.draw(surface)
        self.speed_label.draw(surface)
        
        # 绘制错误信息
        if self.code_editor.error_msg:
            self._draw_error_msg(surface)
        
        # 设置教程高亮区域
        if tutorial.active:
            tutorial.set_highlight_rect('machine_selector', 
                pygame.Rect(10, 60, 200, 400))
            tutorial.set_highlight_rect('grid', 
                pygame.Rect(self.grid_x, self.grid_y, self.grid_width, self.grid_height))
            tutorial.set_highlight_rect('target', 
                pygame.Rect(self.task_panel.x + 10, self.task_panel.y + 30, 90, 70))
            tutorial.set_highlight_rect('controls', 
                pygame.Rect(self.grid_x, 10, 400, 50))
            tutorial.set_highlight_rect('hint_btn', 
                pygame.Rect(self.grid_x + 440, 15, 80, 35))
            # 绘制教程覆盖层
            tutorial.draw(surface)
    
    def _draw_grid(self, surface: pygame.Surface):
        """绘制网格"""
        # 网格背景
        grid_rect = pygame.Rect(self.grid_x, self.grid_y, 
                               self.grid_width, self.grid_height)
        pygame.draw.rect(surface, COLORS['grid'], grid_rect)
        
        # 网格线
        for i in range(GRID_COLS + 1):
            x = self.grid_x + i * GRID_SIZE
            pygame.draw.line(surface, COLORS['grid_line'],
                           (x, self.grid_y), (x, self.grid_y + self.grid_height))
        
        for i in range(GRID_ROWS + 1):
            y = self.grid_y + i * GRID_SIZE
            pygame.draw.line(surface, COLORS['grid_line'],
                           (self.grid_x, y), (self.grid_x + self.grid_width, y))
        
        # 网格边框
        pygame.draw.rect(surface, COLORS['panel_border'], grid_rect, 2)
    
    def _draw_op_hints(self, surface: pygame.Surface):
        """绘制操作提示面板（已废弃，由编程模式面板替代）"""
        pass
    
    def _draw_error_msg(self, surface: pygame.Surface):
        """绘制代码错误信息"""
        error_x = 10
        error_y = WINDOW_HEIGHT - 50
        
        # 背景
        rect = pygame.Rect(error_x, error_y, 200, 40)
        pygame.draw.rect(surface, (60, 20, 20), rect, border_radius=5)
        pygame.draw.rect(surface, COLORS['error'], rect, 2, border_radius=5)
        
        # 错误文字
        font = get_font(14)
        text = font.render(f"错误: {self.code_editor.error_msg[:25]}", True, COLORS['error'])
        surface.blit(text, (error_x + 10, error_y + 12))
    
    def _draw_task_content(self, surface: pygame.Surface):
        """绘制任务区内容（原目标显示）"""
        if not self.target_shape:
            return
            
        # 在任务面板内绘制目标
        target_x = self.task_panel.x + 20
        target_y = self.task_panel.y + 40
        
        # 标签
        font = get_font(20)
        text = font.render("任务目标", True, COLORS['success'])
        surface.blit(text, (target_x + 15, target_y - 5))
        
        # 图形
        self.target_shape.draw(surface, target_x + 40, target_y + 40, 0.8)
        
        # 关卡信息
        if game_engine.current_level:
            level = game_engine.current_level
            info_y = target_y + 80
            
            # 关卡标题
            title_font = get_font(18)
            title = title_font.render(level.title, True, COLORS['text'])
            surface.blit(title, (target_x, info_y))
            
            # Python概念
            if level.python_concept:
                concept_font = get_font(16)
                concept = concept_font.render(f"学习: {level.python_concept}", 
                                             True, COLORS['accent'])
                surface.blit(concept, (target_x, info_y + 25))
            
            # 计时
            try:
                if level.factory.running:
                    start = getattr(level, 'start_time', None)
                    now = time.time()
                    if start and now >= start:
                        elapsed = (level.elapsed_time or 0.0) + (now - start)
                    else:
                        elapsed = max(0.0, float(level.elapsed_time or 0.0))
                else:
                    elapsed = float(level.elapsed_time or 0.0)
            except Exception:
                elapsed = 0.0
            
            time_text = f"时间: {elapsed:.1f}s"
            time_label = title_font.render(time_text, True, COLORS['text_secondary'])
            surface.blit(time_label, (target_x, info_y + 45))
    
    def _draw_programming_content(self, surface: pygame.Surface):
        """绘制编程模式区内容（文字说明）"""
        font = get_font(16)
        y = self.programming_panel.y + 35
        x = self.programming_panel.x + 10
        
        for hint in self.programming_hints:
            color = COLORS['accent'] if hint.startswith("代码编程模式") else COLORS['text']
            if hint.startswith("─"):
                color = COLORS['text_secondary']
            elif ":" in hint and not hint.startswith(" "):
                color = COLORS['warning']
            
            text = font.render(hint, True, color)
            surface.blit(text, (x, y))
            y += 20


class AchievementsScene(GameScene):
    """成就场景"""
    
    def __init__(self, game: 'PyFactoryGame'):
        super().__init__(game)
        self._create_ui()
    
    def _create_ui(self):
        w = self.game.window_width if hasattr(self.game, 'window_width') else WINDOW_WIDTH
        h = self.game.window_height if hasattr(self.game, 'window_height') else WINDOW_HEIGHT
        
        self.back_btn = Button(20, 20, 100, 40, "← 返回",
                              lambda: self.game.switch_scene('menu'))
        self.back_btn.font_size = 20
        
        self.title = Label(w // 2, 50, "成就",
                          font_size=48, color=COLORS['accent'], centered=True)
        
        self.achievement_panel = ScrollPanel(50, 100, w - 100, h - 150, "")
        self._load_achievements()
    
    def on_resize(self, width: int, height: int):
        self._create_ui()
    
    def _load_achievements(self):
        achievements = game_engine.get_user_achievements()
        
        y = self.achievement_panel.y + 20
        for ach in achievements:
            unlocked = ach.get('unlocked_at') is not None
            card = self._create_achievement_card(ach, unlocked, 
                                                self.achievement_panel.x + 20, y)
            self.achievement_panel.add_child(card)
            y += 80
        
        self.achievement_panel.content_height = y - self.achievement_panel.y
    
    def _create_achievement_card(self, ach: Dict, unlocked: bool, 
                                 x: int, y: int) -> Panel:
        card = Panel(x, y, self.achievement_panel.width - 60, 70)
        card.bg_color = COLORS['button_hover'] if unlocked else COLORS['panel_bg']
        
        # 图标
        icon = Label(x + 30, y + 25, ach.get('icon', '🏆'), font_size=36)
        card.add_child(icon)
        
        # 标题
        title_color = COLORS['text'] if unlocked else COLORS['text_secondary']
        title = Label(x + 70, y + 15, ach['title'], font_size=24, color=title_color)
        card.add_child(title)
        
        # 描述
        desc = Label(x + 70, y + 42, ach.get('description', ''),
                    font_size=18, color=COLORS['text_secondary'])
        card.add_child(desc)
        
        # 点数
        points = Label(x + card.width - 60, y + 25, 
                      f"+{ach.get('points', 0)}", font_size=20,
                      color=COLORS['success'] if unlocked else COLORS['text_secondary'])
        card.add_child(points)
        
        return card
    
    def handle_event(self, event: pygame.event.Event):
        self.back_btn.handle_event(event)
        self.achievement_panel.handle_event(event)
    
    def draw(self, surface: pygame.Surface):
        surface.fill(COLORS['background'])
        self.back_btn.draw(surface)
        self.title.draw(surface)
        self.achievement_panel.draw(surface)


class BlueprintsScene(GameScene):
    """蓝图管理场景"""
    
    def __init__(self, game: 'PyFactoryGame'):
        super().__init__(game)
        self._create_ui()
    
    def _create_ui(self):
        w = self.game.window_width if hasattr(self.game, 'window_width') else WINDOW_WIDTH
        h = self.game.window_height if hasattr(self.game, 'window_height') else WINDOW_HEIGHT
        
        self.back_btn = Button(20, 20, 100, 40, "← 返回",
                              lambda: self.game.switch_scene('menu'))
        self.back_btn.font_size = 20
        
        self.title = Label(w // 2, 50, "我的蓝图",
                          font_size=48, color=COLORS['accent'], centered=True)
        
        self.blueprint_panel = ScrollPanel(50, 100, w - 100, h - 150, "")
        self._load_blueprints()
    
    def on_resize(self, width: int, height: int):
        self._create_ui()
    
    def _load_blueprints(self):
        if not game_engine.current_user:
            return
        
        blueprints = db.get_user_blueprints(game_engine.current_user['id'])
        
        if not blueprints:
            empty_label = Label(WINDOW_WIDTH // 2, 300, "还没有保存的蓝图",
                               font_size=24, color=COLORS['text_secondary'], centered=True)
            self.blueprint_panel.add_child(empty_label)
            return
        
        y = self.blueprint_panel.y + 20
        for bp in blueprints:
            card = self._create_blueprint_card(bp, self.blueprint_panel.x + 20, y)
            self.blueprint_panel.add_child(card)
            y += 80
        
        self.blueprint_panel.content_height = y - self.blueprint_panel.y
    
    def _create_blueprint_card(self, bp: Dict, x: int, y: int) -> Panel:
        card = Panel(x, y, self.blueprint_panel.width - 60, 70)
        
        # 名称
        name = Label(x + 15, y + 15, bp['name'], font_size=24)
        card.add_child(name)
        
        # 描述
        desc = Label(x + 15, y + 42, bp.get('description', ''),
                    font_size=18, color=COLORS['text_secondary'])
        card.add_child(desc)
        
        # 加载按钮
        load_btn = Button(x + card.width - 160, y + 20, 70, 35, "加载",
                         lambda bid=bp['id']: self._load_blueprint(bid))
        load_btn.font_size = 18
        card.add_child(load_btn)
        
        # 删除按钮
        del_btn = Button(x + card.width - 80, y + 20, 60, 35, "删除",
                        lambda bid=bp['id']: self._delete_blueprint(bid),
                        color=COLORS['error'])
        del_btn.font_size = 18
        card.add_child(del_btn)
        
        return card
    
    def _load_blueprint(self, blueprint_id: int):
        game_engine.start_sandbox()
        if game_engine.load_blueprint(blueprint_id):
            self.game.switch_scene('game')
            toast.show("蓝图已加载", 'success')
        else:
            toast.show("加载失败", 'error')
    
    def _delete_blueprint(self, blueprint_id: int):
        if game_engine.current_user:
            db.delete_blueprint(blueprint_id, game_engine.current_user['id'])
            self._load_blueprints()
            toast.show("蓝图已删除")
    
    def handle_event(self, event: pygame.event.Event):
        self.back_btn.handle_event(event)
        self.blueprint_panel.handle_event(event)
    
    def draw(self, surface: pygame.Surface):
        surface.fill(COLORS['background'])
        self.back_btn.draw(surface)
        self.title.draw(surface)
        self.blueprint_panel.draw(surface)


class HelpScene(GameScene):
    """帮助场景"""
    
    def __init__(self, game: 'PyFactoryGame'):
        super().__init__(game)
        self._create_ui()
    
    def _create_ui(self):
        w = self.game.window_width if hasattr(self.game, 'window_width') else WINDOW_WIDTH
        h = self.game.window_height if hasattr(self.game, 'window_height') else WINDOW_HEIGHT
        
        self.back_btn = Button(20, 20, 100, 40, "← 返回",
                              lambda: self.game.switch_scene('menu'))
        self.back_btn.font_size = 20
        
        self.title = Label(w // 2, 50, "帮助",
                          font_size=48, color=COLORS['accent'], centered=True)
        
        self.help_panel = ScrollPanel(50, 100, w - 100, h - 150, "")
        self._create_help_content()
    
    def on_resize(self, width: int, height: int):
        self._create_ui()
    
    def _create_help_content(self):
        content = [
            ("游戏简介", 
             "PyFactory是一款通过工厂建造来学习Python编程的教学游戏。\n"
             "你的目标是使用各种机器将输入的图形加工成目标形状。"),
            
            ("基本操作",
             "• 左键点击：放置机器或选择机器\n"
             "• 右键拖拽：连接两台机器\n"
             "• Delete键：删除选中的机器\n"
             "• Esc键：取消当前操作"),
            
            ("机器类型",
             "【基础机器】\n"
             "• 源头：产生基础图形\n"
             "• 输出口：收集最终产品\n"
             "• 传送带：传输图形\n\n"
             "【变换机器】\n"
             "• 染色机：改变图形颜色\n"
             "• 切割机：将图形切成两半\n"
             "• 旋转机：旋转图形90度"),
            
            ("编程概念",
             "【分拣器】→ if/else 条件分支\n"
             "根据条件将图形分流到不同路径\n\n"
             "【循环器】→ for/while 循环\n"
             "重复执行相同的加工步骤\n\n"
             "【函数机】→ def 函数定义\n"
             "创建可复用的加工蓝图\n\n"
             "【打包机】→ list 列表\n"
             "将多个图形打包成列表\n\n"
             "【拆包机】→ 解包操作\n"
             "将列表中的图形逐个取出"),
            
            ("学习建议",
             "1. 从基础关卡开始，熟悉机器操作\n"
             "2. 注意观察每个关卡的Python概念\n"
             "3. 尝试用代码编辑器理解逻辑\n"
             "4. 多尝试不同的解法\n"
             "5. 使用沙盒模式自由实验"),
        ]
        
        y = self.help_panel.y + 20
        for title, text in content:
            # 标题
            title_label = Label(self.help_panel.x + 20, y, title, 
                               font_size=28, color=COLORS['accent'])
            self.help_panel.add_child(title_label)
            y += 35
            
            # 内容
            for line in text.split('\n'):
                if line.strip():
                    line_label = Label(self.help_panel.x + 20, y, line,
                                      font_size=20, color=COLORS['text'])
                    self.help_panel.add_child(line_label)
                    y += 25
            
            y += 20
        
        self.help_panel.content_height = y - self.help_panel.y + 50
    
    def handle_event(self, event: pygame.event.Event):
        self.back_btn.handle_event(event)
        self.help_panel.handle_event(event)
    
    def draw(self, surface: pygame.Surface):
        surface.fill(COLORS['background'])
        self.back_btn.draw(surface)
        self.title.draw(surface)
        self.help_panel.draw(surface)


class DemoScene(GameScene):
    """演示场景 - 展示游戏玩法（代码驱动）"""
    
    def __init__(self, game: 'PyFactoryGame'):
        super().__init__(game)
        self._init_layout()
        self._init_demo()
    
    def _init_layout(self):
        w = self.game.window_width if hasattr(self.game, 'window_width') else WINDOW_WIDTH
        h = self.game.window_height if hasattr(self.game, 'window_height') else WINDOW_HEIGHT
        
        # 网格区域（右侧）
        self.grid_x = min(450, w // 3)
        self.grid_y = 100
        self.grid_width = min(GRID_COLS * GRID_SIZE, w - self.grid_x - 50)
        self.grid_height = min(GRID_ROWS * GRID_SIZE, h - 200)
        
        # 返回按钮
        self.back_btn = Button(20, 20, 100, 40, "← 返回",
                              lambda: self.game.switch_scene('menu'))
        self.back_btn.font_size = 20
    
    def _init_demo(self):
        
        # 创建演示工厂
        self.factory = Factory()
        
        # 演示步骤（代码 + 说明）
        self.demo_step = 0
        self.demo_timer = 0
        self.auto_running = False
        
        # 每一步的代码和说明
        self.steps = [
            {
                'title': '游戏目标',
                'desc': '用Python代码建造工厂，\n将图形从[源头]加工后\n送到[输出口]完成关卡！',
                'code': '# 欢迎来到 PyFactory!\n# 这是一个用代码建工厂的游戏\n',
                'machines': []
            },
            {
                'title': '第1步：创建源头',
                'desc': 'Source() 创建源头机器\n它会自动产生图形\n参数: 形状, 颜色',
                'code': '# 创建一个产生白色圆形的源头\nsource = Source("circle", "white")',
                'machines': [('source', 1, 3, {'shape_type': 'circle', 'color': 'white'})]
            },
            {
                'title': '第2步：创建输出口',
                'desc': 'Output() 创建输出口\n图形送到这里就算完成\n',
                'code': '# 创建源头\nsource = Source("circle", "white")\n\n# 创建输出口\noutput = Output()',
                'machines': [
                    ('source', 1, 3, {'shape_type': 'circle', 'color': 'white'}),
                    ('output', 5, 3, {})
                ]
            },
            {
                'title': '第3步：连接机器',
                'desc': '.connect() 连接两个机器\n图形会沿着连线流动\n',
                'code': '# 创建源头\nsource = Source("circle", "white")\n# 创建输出口\noutput = Output()\n\n# 连接：源头 -> 输出口\nsource.connect(output)',
                'machines': [
                    ('source', 1, 3, {'shape_type': 'circle', 'color': 'white'}),
                    ('output', 5, 3, {})
                ],
                'connections': [(0, 1)]
            },
            {
                'title': '第4步：添加染色机',
                'desc': 'Painter() 染色机\n可以把图形染成指定颜色\n',
                'code': 'source = Source("circle", "white")\npainter = Painter("red")  # 染成红色\noutput = Output()\n\nsource.connect(painter)\npainter.connect(output)',
                'machines': [
                    ('source', 1, 3, {'shape_type': 'circle', 'color': 'white'}),
                    ('painter', 3, 3, {'target_color': 'red'}),
                    ('output', 5, 3, {})
                ],
                'connections': [(0, 1), (1, 2)]
            },
            {
                'title': '运行工厂！',
                'desc': '点击[运行]按钮启动工厂\n观察图形如何流动和变化\n\n完成后返回菜单开始游戏！',
                'code': '# 完整代码示例：\nsource = Source("circle", "white")\npainter = Painter("red")\noutput = Output()\n\nsource.connect(painter)\npainter.connect(output)',
                'machines': [
                    ('source', 1, 3, {'shape_type': 'circle', 'color': 'white'}),
                    ('painter', 3, 3, {'target_color': 'red'}),
                    ('output', 5, 3, {})
                ],
                'connections': [(0, 1), (1, 2)]
            }
        ]
        
        self._apply_step(0)
        self._create_buttons()
    
    def _create_buttons(self):
        h = self.game.window_height if hasattr(self.game, 'window_height') else WINDOW_HEIGHT
        
        # 控制按钮
        self.prev_btn = Button(20, h - 70, 100, 45, "← 上一步", self._prev_step)
        self.prev_btn.font_size = 18
        self.next_btn = Button(130, h - 70, 100, 45, "下一步 →", self._next_step,
                              color=COLORS['success'])
        self.next_btn.font_size = 18
        self.run_btn = Button(250, h - 70, 100, 45, "▶ 运行", self._toggle_run,
                             color=COLORS['accent'])
        self.run_btn.font_size = 18
    
    def on_resize(self, width: int, height: int):
        self._init_layout()
        self._create_buttons()
        
    def _apply_step(self, step_idx: int):
        """应用指定步骤的工厂配置"""
        if DEBUG:
            print(f"[DEBUG] DemoScene._apply_step: step={step_idx} applying")
        # 使用 Factory.clear() 确保同时清理 grid、machines 和 connections
        self.factory.clear()
        self.auto_running = False
        
        step = self.steps[step_idx]
        machine_objs = []
        
        # 创建机器
        from machines import PainterMachine, RotatorMachine
        for m_type, x, y, props in step.get('machines', []):
            if m_type == 'source':
                m = SourceMachine(x, y)
                m.shape_type = props.get('shape_type', 'circle')
                m.color = props.get('color', 'white')
            elif m_type == 'painter':
                m = PainterMachine(x, y)
                m.target_color = props.get('target_color', 'red')
            elif m_type == 'output':
                m = OutputMachine(x, y)
                m.required_count = 5
            else:
                continue
            added = self.factory.add_machine(m)
            if DEBUG:
                print(f"[DEBUG] DemoScene._apply_step: created {m.machine_type} at ({m.x},{m.y}) added={added}")
                if not added:
                    # 记录为何添加失败（位置冲突）
                    print(f"[DEBUG] DemoScene._apply_step: add_machine failed at pos=({m.x},{m.y}) existing_grid={self.factory.grid.get((m.x,m.y))}")
            machine_objs.append(m)
        
        # 创建连接
        for from_idx, to_idx in step.get('connections', []):
            if from_idx < len(machine_objs) and to_idx < len(machine_objs):
                conn = self.factory.connect(machine_objs[from_idx], machine_objs[to_idx])
                if DEBUG:
                    print(f"[DEBUG] DemoScene._apply_step: connect {from_idx}->{to_idx} created -> conn={conn is not None}")

        if DEBUG:
            print(f"[DEBUG] DemoScene._apply_step: final machines={len(self.factory.machines)} grid_keys={list(self.factory.grid.keys())} connections={len(self.factory.connections)}")
    
    def _prev_step(self):
        """上一步"""
        if self.demo_step > 0:
            self.demo_step -= 1
            self._apply_step(self.demo_step)
    
    def _next_step(self):
        """下一步"""
        if self.demo_step < len(self.steps) - 1:
            self.demo_step += 1
            self._apply_step(self.demo_step)
        else:
            self.game.switch_scene('menu')
    
    def _toggle_run(self):
        """切换运行状态"""
        if self.auto_running:
            self.auto_running = False
            self.factory.running = False
            self.run_btn.text = "▶ 运行"
        else:
            self.auto_running = True
            self.factory.running = True
            self.run_btn.text = "⏸ 暂停"
    
    def handle_event(self, event: pygame.event.Event):
        self.back_btn.handle_event(event)
        self.prev_btn.handle_event(event)
        self.next_btn.handle_event(event)
        self.run_btn.handle_event(event)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self._prev_step()
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_SPACE:
                self._next_step()
            elif event.key == pygame.K_ESCAPE:
                self.game.switch_scene('menu')
    
    def update(self, dt: float):
        if self.auto_running:
            self.factory.update(dt)
    
    def draw(self, surface: pygame.Surface):
        surface.fill(COLORS['background'])
        
        # 标题
        title_font = get_font(36)
        title = title_font.render("新手教程 - 学习用代码建工厂", True, COLORS['accent'])
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 20))
        
        # 绘制左侧代码面板
        self._draw_code_panel(surface)
        
        # 绘制右侧说明面板
        self._draw_desc_panel(surface)
        
        # 绘制网格
        self._draw_grid(surface)
        
        # 绘制机器（捕获异常）并在失败时绘制占位
        if DEBUG:
            print(f"[DEBUG] DemoScene.draw: machines={len(self.factory.machines)}")
        for machine in self.factory.machines:
            try:
                if DEBUG:
                    try:
                        print(f"[DEBUG] DemoScene.draw: machine={getattr(machine,'machine_type',None)} at ({getattr(machine,'x',None)},{getattr(machine,'y',None)})")
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                # Only draw debug overlay when DEBUG enabled
                if DEBUG:
                    try:
                        dbg_rx = machine.x * GRID_SIZE + self.grid_x + 2
                        dbg_ry = machine.y * GRID_SIZE + self.grid_y + 2
                        dbg_rect = pygame.Rect(dbg_rx, dbg_ry, GRID_SIZE - 4, GRID_SIZE - 4)
                        pygame.draw.rect(surface, (200, 50, 50), dbg_rect, 2)
                    except Exception:
                        pass
                machine.draw(surface, self.grid_x, self.grid_y)
            except Exception as e:
                if DEBUG:
                    print(f"Demo 绘制机器失败: {e} - {getattr(machine,'machine_type',None)} at ({getattr(machine,'x','?')},{getattr(machine,'y','?')})")
                try:
                    import pygame as _pygame
                    rx = machine.x * GRID_SIZE + self.grid_x + 4
                    ry = machine.y * GRID_SIZE + self.grid_y + 4
                    _pygame.draw.rect(surface, (120, 20, 20), _pygame.Rect(rx, ry, GRID_SIZE-8, GRID_SIZE-8))
                except Exception:
                    pass
            # 机器标签
            try:
                self._draw_machine_label(surface, machine)
            except Exception:
                pass

        # 绘制连接（在机器上层）
        for conn in self.factory.connections:
            try:
                conn.draw(surface, self.grid_x, self.grid_y)
            except Exception as e:
                print(f"Demo 绘制连接失败: {e}")
        
        # 绘制进度指示
        self._draw_progress(surface)
        
        # 绘制UI按钮
        self.back_btn.draw(surface)
        self.prev_btn.draw(surface)
        self.next_btn.draw(surface)
        self.run_btn.draw(surface)
    
    def _draw_code_panel(self, surface: pygame.Surface):
        """绘制代码面板"""
        panel_x, panel_y = 20, 70
        panel_w, panel_h = 400, 280
        
        # 背景
        rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=8)
        pygame.draw.rect(surface, COLORS['accent'], rect, 2, border_radius=8)
        
        # 标题
        font = get_font(20)
        title = font.render("Python 代码", True, COLORS['accent'])
        surface.blit(title, (panel_x + 10, panel_y + 10))
        
        # 代码内容
        code_font = get_font(16)
        step = self.steps[self.demo_step]
        code_lines = step['code'].split('\n')
        
        y = panel_y + 45
        for i, line in enumerate(code_lines):
            # 行号
            line_num = code_font.render(f"{i+1:2}", True, COLORS['text_secondary'])
            surface.blit(line_num, (panel_x + 10, y))
            
            # 代码（简单高亮）
            if line.strip().startswith('#'):
                color = COLORS['text_secondary']
            elif '=' in line and 'connect' not in line:
                color = COLORS['success']
            elif '.connect' in line:
                color = COLORS['warning']
            else:
                color = COLORS['text']
            
            code_text = code_font.render(line, True, color)
            surface.blit(code_text, (panel_x + 40, y))
            y += 22
    
    def _draw_desc_panel(self, surface: pygame.Surface):
        """绘制说明面板"""
        panel_x, panel_y = 20, 370
        panel_w, panel_h = 400, 180
        
        # 背景
        rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=8)
        pygame.draw.rect(surface, COLORS['success'], rect, 2, border_radius=8)
        
        step = self.steps[self.demo_step]
        
        # 步骤标题
        title_font = get_font(24)
        title = title_font.render(step['title'], True, COLORS['success'])
        surface.blit(title, (panel_x + 15, panel_y + 15))
        
        # 说明文字
        desc_font = get_font(18)
        # 说明文字（自动换行）
        desc_font = get_font(18)
        y = panel_y + 55
        def _wrap_text_local(text: str, font: pygame.font.Font, max_w: int):
            words = text.split(' ')
            lines = []
            cur = ''
            for w in words:
                test = (cur + ' ' + w) if cur else w
                if font.size(test)[0] <= max_w:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            return lines

        paragraphs = step.get('desc', '').split('\n')
        for para in paragraphs:
            if not para.strip():
                y += 10
                continue
            wrapped = _wrap_text_local(para, desc_font, panel_w - 30)
            for l in wrapped:
                text = desc_font.render(l, True, COLORS['text'])
                surface.blit(text, (panel_x + 15, y))
                y += 26
    
    def _draw_progress(self, surface: pygame.Surface):
        """绘制进度指示"""
        total = len(self.steps)
        progress_y = WINDOW_HEIGHT - 30
        
        font = get_font(16)
        text = font.render(f"步骤 {self.demo_step + 1} / {total}  |  按 ← → 切换", 
                          True, COLORS['text_secondary'])
        surface.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, progress_y))
        
    def _draw_grid(self, surface: pygame.Surface):
        """绘制网格"""
        grid_rect = pygame.Rect(self.grid_x, self.grid_y, 
                               self.grid_width, self.grid_height)
        pygame.draw.rect(surface, COLORS['grid'], grid_rect)
        
        for i in range(GRID_COLS + 1):
            x = self.grid_x + i * GRID_SIZE
            pygame.draw.line(surface, COLORS['grid_line'],
                           (x, self.grid_y), (x, self.grid_y + self.grid_height))
        
        for i in range(GRID_ROWS + 1):
            y = self.grid_y + i * GRID_SIZE
            pygame.draw.line(surface, COLORS['grid_line'],
                           (self.grid_x, y), (self.grid_x + self.grid_width, y))
        
        pygame.draw.rect(surface, COLORS['panel_border'], grid_rect, 2)
    
    def _draw_machine_label(self, surface: pygame.Surface, machine: Machine):
        """绘制机器标签"""
        x = machine.x * GRID_SIZE + self.grid_x + GRID_SIZE // 2
        y = machine.y * GRID_SIZE + self.grid_y - 15
        
        font = get_font(18)
        if machine.machine_type == 'source':
            text = font.render("① 源头", True, COLORS['accent'])
        elif machine.machine_type == 'painter':
            text = font.render("② 染色机", True, COLORS['warning'])
        elif machine.machine_type == 'output':
            text = font.render("③ 输出口", True, COLORS['success'])
        else:
            return
        
        surface.blit(text, (x - text.get_width() // 2, y))
    


class PyFactoryGame:
    """游戏主类"""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)
        
        # 可缩放窗口
        self.window_width = WINDOW_WIDTH
        self.window_height = WINDOW_HEIGHT
        self.min_width = 1024
        self.min_height = 600
        self.screen = pygame.display.set_mode(
            (self.window_width, self.window_height),
            pygame.RESIZABLE
        )
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 场景管理
        self.scenes: Dict[str, GameScene] = {}
        self.current_scene: Optional[GameScene] = None
        
        # 初始化场景
        self._init_scenes()
        self.switch_scene('login')
    
    def _init_scenes(self):
        self.scenes['login'] = LoginScene(self)
        self.scenes['menu'] = MenuScene(self)
        self.scenes['level_select'] = LevelSelectScene(self)
        self.scenes['game'] = GameScene_(self)
        self.scenes['achievements'] = AchievementsScene(self)
        self.scenes['blueprints'] = BlueprintsScene(self)
        self.scenes['help'] = HelpScene(self)
        self.scenes['demo'] = DemoScene(self)
    
    def switch_scene(self, scene_name: str):
        if scene_name in self.scenes:
            # 重新初始化场景以刷新数据
            if scene_name == 'menu':
                self.scenes['menu'] = MenuScene(self)
            elif scene_name == 'level_select':
                self.scenes['level_select'] = LevelSelectScene(self)
            elif scene_name == 'game':
                self.scenes['game'] = GameScene_(self)
            elif scene_name == 'achievements':
                self.scenes['achievements'] = AchievementsScene(self)
            elif scene_name == 'blueprints':
                self.scenes['blueprints'] = BlueprintsScene(self)
            elif scene_name == 'demo':
                self.scenes['demo'] = DemoScene(self)
            
            self.current_scene = self.scenes[scene_name]
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # 处理窗口大小变化
            if event.type == pygame.VIDEORESIZE:
                self._on_resize(event.w, event.h)
                continue
            
            if self.current_scene:
                self.current_scene.handle_event(event)
    
    def _on_resize(self, width: int, height: int):
        """处理窗口大小变化"""
        # 限制最小尺寸
        width = max(self.min_width, width)
        height = max(self.min_height, height)
        
        self.window_width = width
        self.window_height = height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        
        # 通知所有场景更新布局
        for scene in self.scenes.values():
            if hasattr(scene, 'on_resize'):
                scene.on_resize(width, height)
    
    def update(self, dt: float):
        toast.update(dt)
        
        if self.current_scene:
            self.current_scene.update(dt)
    
    def draw(self):
        # 每帧先清除全局 tooltip，再让当前场景在每帧内注册（被悬停的按钮会设置 tooltip）
        try:
            clear_tooltip()
        except Exception:
            pass

        if self.current_scene:
            self.current_scene.draw(self.screen)
        
        # 绘制Toast消息
        toast.draw(self.screen)
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        db.close()
        sys.exit()


def main():
    """主函数"""
    game = PyFactoryGame()
    game.run()


if __name__ == '__main__':
    main()
