"""
PyFactory - 工具函数模块
提供各种辅助功能
"""

import os
import json
import time
from typing import Any, Dict, List, Optional, Tuple


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将值限制在指定范围内"""
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """线性插值"""
    return a + (b - a) * clamp(t, 0, 1)


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """计算两点间的距离"""
    import math
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def format_time(seconds: float) -> str:
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}分{secs}秒"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}小时{mins}分"


def wrap_text(text: str, max_chars: int) -> List[str]:
    """文本自动换行"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line = current_line + " " + word if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines


def get_resource_path(filename: str) -> str:
    """获取资源文件路径"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'resources', filename)


def save_json(data: Any, filepath: str) -> bool:
    """保存JSON文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存JSON失败: {e}")
        return False


def load_json(filepath: str) -> Optional[Any]:
    """加载JSON文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载JSON失败: {e}")
        return None


class Timer:
    """计时器类"""
    
    def __init__(self):
        self.start_time = 0
        self.pause_time = 0
        self.is_running = False
        self.is_paused = False
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.is_running = True
        self.is_paused = False
    
    def pause(self):
        """暂停计时"""
        if self.is_running and not self.is_paused:
            self.pause_time = time.time()
            self.is_paused = True
    
    def resume(self):
        """恢复计时"""
        if self.is_paused:
            pause_duration = time.time() - self.pause_time
            self.start_time += pause_duration
            self.is_paused = False
    
    def stop(self):
        """停止计时"""
        self.is_running = False
    
    def reset(self):
        """重置计时"""
        self.start_time = 0
        self.pause_time = 0
        self.is_running = False
        self.is_paused = False
    
    def get_elapsed(self) -> float:
        """获取经过的时间"""
        if not self.is_running:
            return 0
        if self.is_paused:
            return self.pause_time - self.start_time
        return time.time() - self.start_time


class EventEmitter:
    """简单的事件发射器"""
    
    def __init__(self):
        self.listeners: Dict[str, List[callable]] = {}
    
    def on(self, event: str, callback: callable):
        """注册事件监听器"""
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
    
    def off(self, event: str, callback: callable):
        """移除事件监听器"""
        if event in self.listeners:
            self.listeners[event] = [cb for cb in self.listeners[event] if cb != callback]
    
    def emit(self, event: str, *args, **kwargs):
        """触发事件"""
        if event in self.listeners:
            for callback in self.listeners[event]:
                callback(*args, **kwargs)
    
    def clear(self, event: str = None):
        """清除事件监听器"""
        if event:
            self.listeners[event] = []
        else:
            self.listeners.clear()


class StateMachine:
    """简单的状态机"""
    
    def __init__(self, initial_state: str = None):
        self.current_state = initial_state
        self.states: Dict[str, Dict] = {}
        self.transitions: Dict[str, Dict[str, str]] = {}
    
    def add_state(self, name: str, on_enter: callable = None, 
                  on_exit: callable = None, on_update: callable = None):
        """添加状态"""
        self.states[name] = {
            'on_enter': on_enter,
            'on_exit': on_exit,
            'on_update': on_update
        }
    
    def add_transition(self, from_state: str, event: str, to_state: str):
        """添加状态转换"""
        if from_state not in self.transitions:
            self.transitions[from_state] = {}
        self.transitions[from_state][event] = to_state
    
    def trigger(self, event: str):
        """触发事件，可能导致状态转换"""
        if self.current_state in self.transitions:
            if event in self.transitions[self.current_state]:
                new_state = self.transitions[self.current_state][event]
                self._change_state(new_state)
    
    def _change_state(self, new_state: str):
        """改变状态"""
        if new_state not in self.states:
            return
        
        # 退出当前状态
        if self.current_state in self.states:
            on_exit = self.states[self.current_state].get('on_exit')
            if on_exit:
                on_exit()
        
        # 进入新状态
        self.current_state = new_state
        on_enter = self.states[new_state].get('on_enter')
        if on_enter:
            on_enter()
    
    def update(self, dt: float):
        """更新当前状态"""
        if self.current_state in self.states:
            on_update = self.states[self.current_state].get('on_update')
            if on_update:
                on_update(dt)


def count_python_lines(directory: str) -> int:
    """统计目录下Python文件的代码行数"""
    total_lines = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 只计算非空行
                        code_lines = [l for l in lines if l.strip()]
                        total_lines += len(code_lines)
                except:
                    pass
    
    return total_lines


if __name__ == '__main__':
    # 测试代码行数统计
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    lines = count_python_lines(current_dir)
    print(f"PyFactory项目Python代码行数: {lines}")
