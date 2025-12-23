"""
PyFactory - 游戏引擎
管理游戏状态、更新逻辑和关卡验证
"""

import json
import time
from typing import Optional, List, Dict, Any, Tuple
from shapes import Shape, ShapePackage, ShapeDict, create_shape
from machines import (
    Machine, Connection, SourceMachine, OutputMachine, ConveyorMachine,
    PainterMachine, CutterMachine, RotatorMachine, StackerMachine,
    SplitterMachine, LooperMachine, FunctionMachine, PackerMachine,
    UnpackerMachine, DictPackerMachine, ComprehensionMachine, create_machine
)
from database import db
from config import GRID_SIZE, GRID_COLS, GRID_ROWS


class Factory:
    """工厂类 - 管理一个工厂的所有机器和连接"""
    
    def __init__(self):
        self.machines: List[Machine] = []
        self.connections: List[Connection] = []
        self.grid: Dict[Tuple[int, int], Machine] = {}
        self.running = False
        self.speed = 1.0
        
    def add_machine(self, machine: Machine) -> bool:
        """添加机器到工厂"""
        pos = (machine.x, machine.y)
        if pos in self.grid:
            return False  # 位置已被占用
        
        self.machines.append(machine)
        self.grid[pos] = machine
        return True
    
    def remove_machine(self, machine: Machine):
        """移除机器"""
        pos = (machine.x, machine.y)
        if pos in self.grid:
            del self.grid[pos]
        
        if machine in self.machines:
            self.machines.remove(machine)
        
        # 移除相关连接
        self.connections = [c for c in self.connections 
                          if c.from_machine != machine and c.to_machine != machine]
        machine.connections_in.clear()
        machine.connections_out.clear()
    
    def get_machine_at(self, x: int, y: int) -> Optional[Machine]:
        """获取指定位置的机器"""
        return self.grid.get((x, y))
    
    def connect(self, from_machine: Machine, to_machine: Machine,
                from_port: str = 'output', to_port: str = 'input') -> Optional[Connection]:
        """连接两台机器"""
        conn = from_machine.connect_to(to_machine, from_port, to_port)
        self.connections.append(conn)
        return conn
    
    def disconnect(self, from_machine: Machine, to_machine: Machine):
        """断开连接"""
        from_machine.disconnect_from(to_machine)
        self.connections = [c for c in self.connections 
                          if not (c.from_machine == from_machine and 
                                 c.to_machine == to_machine)]
    
    def update(self, dt: float):
        """更新工厂状态"""
        if not self.running:
            return
        
        effective_dt = dt * self.speed
        
        for machine in self.machines:
            machine.update(effective_dt)
    
    def start(self):
        """启动工厂"""
        self.running = True
        
    def stop(self):
        """停止工厂"""
        self.running = False
        
    def reset(self):
        """重置工厂状态"""
        self.stop()
        for machine in self.machines:
            machine.input_buffer.clear()
            machine.output_buffer.clear()
            machine.is_processing = False
            machine.current_item = None
            if isinstance(machine, SourceMachine):
                machine.spawn_timer = 0
            elif isinstance(machine, OutputMachine):
                machine.collected.clear()
                machine.success_count = 0
        
        for conn in self.connections:
            conn.items_in_transit.clear()
    
    def clear(self):
        """清空工厂"""
        self.machines.clear()
        self.connections.clear()
        self.grid.clear()
        self.running = False
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'machines': [
                {
                    'type': m.machine_type,
                    'x': m.x,
                    'y': m.y,
                    'config': self._get_machine_config(m)
                }
                for m in self.machines
            ],
            'connections': [
                {
                    'from': self.machines.index(c.from_machine),
                    'to': self.machines.index(c.to_machine),
                    'from_port': c.from_port,
                    'to_port': c.to_port
                }
                for c in self.connections
            ]
        }
    
    def _get_machine_config(self, machine: Machine) -> Dict[str, Any]:
        """获取机器配置"""
        config = {}
        if isinstance(machine, SourceMachine):
            config['shape_type'] = machine.shape_type
            config['color'] = machine.color
        elif isinstance(machine, PainterMachine):
            config['target_color'] = machine.target_color
        elif isinstance(machine, RotatorMachine):
            config['degrees'] = machine.degrees
        elif isinstance(machine, SplitterMachine):
            config['condition_code'] = machine.condition_code
        elif isinstance(machine, LooperMachine):
            config['loop_count'] = machine.loop_count
        elif isinstance(machine, PackerMachine):
            config['pack_size'] = machine.pack_size
        return config
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Factory':
        """从字典反序列化"""
        factory = cls()
        
        # 创建机器
        for m_data in data.get('machines', []):
            machine = create_machine(
                m_data['type'],
                m_data['x'],
                m_data['y']
            )
            config = m_data.get('config', {})
            cls._apply_machine_config(machine, config)
            factory.add_machine(machine)
        
        # 创建连接
        for c_data in data.get('connections', []):
            from_idx = c_data['from']
            to_idx = c_data['to']
            if 0 <= from_idx < len(factory.machines) and 0 <= to_idx < len(factory.machines):
                factory.connect(
                    factory.machines[from_idx],
                    factory.machines[to_idx],
                    c_data.get('from_port', 'output'),
                    c_data.get('to_port', 'input')
                )
        
        return factory
    
    @staticmethod
    def _apply_machine_config(machine: Machine, config: Dict[str, Any]):
        """应用机器配置"""
        if isinstance(machine, SourceMachine):
            machine.shape_type = config.get('shape_type', 'circle')
            machine.color = config.get('color', 'white')
        elif isinstance(machine, PainterMachine):
            machine.target_color = config.get('target_color', 'red')
        elif isinstance(machine, RotatorMachine):
            machine.degrees = config.get('degrees', 90)
        elif isinstance(machine, SplitterMachine):
            machine.condition_code = config.get('condition_code', "True")
        elif isinstance(machine, LooperMachine):
            machine.loop_count = config.get('loop_count', 3)
        elif isinstance(machine, PackerMachine):
            machine.pack_size = config.get('pack_size', 3)


class Level:
    """关卡类 - 管理单个关卡"""
    
    def __init__(self, level_data: Dict[str, Any]):
        self.id = level_data.get('id', '')
        self.category = level_data.get('category', 'basics')
        self.title = level_data.get('title', '未命名关卡')
        self.description = level_data.get('description', '')
        self.difficulty = level_data.get('difficulty', 1)
        self.python_concept = level_data.get('python_concept', '')
        self.code_template = level_data.get('code_template', '')
        
        # 解析目标数据
        target_str = level_data.get('target_data', '{}')
        self.target_data = json.loads(target_str) if isinstance(target_str, str) else target_str
        
        # 解析提示
        hints_str = level_data.get('hints', '[]')
        self.hints = json.loads(hints_str) if isinstance(hints_str, str) else hints_str
        
        # 解析初始数据
        initial_str = level_data.get('initial_data', '{}')
        self.initial_data = json.loads(initial_str) if isinstance(initial_str, str) else initial_str
        
        # 工厂实例
        self.factory = Factory()
        
        # 计时
        self.start_time = 0
        self.elapsed_time = 0
        self.is_completed = False
        
    def setup(self):
        """设置关卡初始状态"""
        self.factory.clear()
        self.is_completed = False
        self.elapsed_time = 0
        
        # 创建初始机器
        self._create_initial_machines()
    
    def _create_initial_machines(self):
        """创建初始机器配置"""
        # 根据目标创建源头
        if 'shape' in self.target_data:
            target = self.target_data['shape']
            source = SourceMachine(1, 3, 'circle', 'white')
            self.factory.add_machine(source)
        
        # 创建输出口
        output = OutputMachine(10, 3)
        if 'shape' in self.target_data:
            target_shape = self._create_target_shape()
            output.set_target(target_shape, self.target_data.get('count', 1))
        self.factory.add_machine(output)
    
    def _create_target_shape(self) -> Shape:
        """从目标数据创建目标图形"""
        if 'shape' in self.target_data:
            shape_data = self.target_data['shape']
            shape = create_shape(
                shape_data.get('type', 'circle'),
                shape_data.get('color', 'white')
            )
            if 'rotation' in shape_data:
                shape.rotation = shape_data['rotation']
            return shape
        return create_shape('circle', 'white')
    
    def get_target_shape(self) -> Optional[Shape]:
        """获取目标图形"""
        return self._create_target_shape()
    
    def start(self):
        """开始关卡"""
        self.start_time = time.time()
        self.factory.start()
    
    def stop(self):
        """停止关卡"""
        self.factory.stop()
        self.elapsed_time = time.time() - self.start_time
    
    def reset(self):
        """重置关卡"""
        self.factory.reset()
        self.is_completed = False
        self.elapsed_time = 0
    
    def update(self, dt: float):
        """更新关卡"""
        self.factory.update(dt)
        
        # 检查是否完成
        if not self.is_completed:
            self.is_completed = self.check_completion()
            if self.is_completed:
                self.elapsed_time = time.time() - self.start_time
    
    def check_completion(self) -> bool:
        """检查关卡是否完成"""
        for machine in self.factory.machines:
            if isinstance(machine, OutputMachine):
                if machine.is_goal_reached():
                    return True
        return False
    
    def calculate_stars(self) -> int:
        """计算获得的星星数"""
        if not self.is_completed:
            return 0
        
        stars = 1  # 完成获得1星
        
        # 时间奖励
        if self.elapsed_time < 60:
            stars += 1
        if self.elapsed_time < 30:
            stars += 1
        
        return min(stars, 3)


class GameEngine:
    """游戏引擎 - 管理整个游戏"""
    
    def __init__(self):
        self.current_user: Optional[Dict] = None
        self.current_level: Optional[Level] = None
        self.sandbox_factory: Factory = Factory()
        self.mode = 'menu'  # 'menu', 'level_select', 'playing', 'sandbox'
        self.selected_machine_type: Optional[str] = None
        self.is_connecting = False
        self.connection_start: Optional[Machine] = None
        
    def login(self, username: str, password: str) -> bool:
        """用户登录"""
        user = db.verify_user(username, password)
        if user:
            self.current_user = user
            return True
        return False
    
    def logout(self):
        """用户登出"""
        self.current_user = None
        self.current_level = None
        self.mode = 'menu'
    
    def get_levels(self) -> List[Dict]:
        """获取所有关卡"""
        return db.get_all_levels()
    
    def get_levels_by_category(self, category: str) -> List[Dict]:
        """获取分类关卡"""
        return db.get_levels_by_category(category)
    
    def load_level(self, level_id: str) -> bool:
        """加载关卡"""
        level_data = db.get_level(level_id)
        if level_data:
            self.current_level = Level(level_data)
            self.current_level.setup()
            self.mode = 'playing'
            return True
        return False
    
    def start_sandbox(self):
        """开始沙盒模式"""
        self.sandbox_factory.clear()
        self.mode = 'sandbox'
    
    def get_current_factory(self) -> Factory:
        """获取当前工厂"""
        if self.mode == 'playing' and self.current_level:
            return self.current_level.factory
        return self.sandbox_factory
    
    def update(self, dt: float):
        """更新游戏状态"""
        if self.mode == 'playing' and self.current_level:
            self.current_level.update(dt)
            
            # 检查完成
            if self.current_level.is_completed:
                self._on_level_completed()
        elif self.mode == 'sandbox':
            self.sandbox_factory.update(dt)
    
    def _on_level_completed(self):
        """关卡完成回调"""
        if not self.current_level or not self.current_user:
            return
        
        stars = self.current_level.calculate_stars()
        
        # 保存进度
        solution = json.dumps(self.current_level.factory.to_dict())
        db.update_progress(
            self.current_user['id'],
            self.current_level.id,
            completed=True,
            stars=stars,
            time_taken=self.current_level.elapsed_time,
            solution_data=solution
        )
        
        # 检查成就
        self._check_achievements()
    
    def _check_achievements(self):
        """检查并解锁成就"""
        if not self.current_user:
            return
        
        user_id = self.current_user['id']
        progress = db.get_user_progress(user_id)
        
        # 第一步成就
        if len(progress) >= 1:
            db.unlock_achievement(user_id, 'first_step')
        
        # 快速学习者
        if self.current_level and self.current_level.elapsed_time < 30:
            db.unlock_achievement(user_id, 'fast_learner')
        
        # 检查分类完成
        completed_levels = {p['level_id'] for p in progress if p['completed']}
        
        loop_levels = {l['id'] for l in db.get_levels_by_category('loops')}
        if loop_levels.issubset(completed_levels):
            db.unlock_achievement(user_id, 'loop_master')
        
        function_levels = {l['id'] for l in db.get_levels_by_category('functions')}
        if function_levels.issubset(completed_levels):
            db.unlock_achievement(user_id, 'function_guru')
        
        data_levels = {l['id'] for l in db.get_levels_by_category('data_structures')}
        if data_levels.issubset(completed_levels):
            db.unlock_achievement(user_id, 'data_wizard')
    
    def place_machine(self, machine_type: str, grid_x: int, grid_y: int) -> Optional[Machine]:
        """在指定位置放置机器"""
        factory = self.get_current_factory()
        
        if factory.get_machine_at(grid_x, grid_y):
            return None  # 位置被占用
        
        machine = create_machine(machine_type, grid_x, grid_y)
        if factory.add_machine(machine):
            return machine
        return None
    
    def remove_machine_at(self, grid_x: int, grid_y: int):
        """移除指定位置的机器"""
        factory = self.get_current_factory()
        machine = factory.get_machine_at(grid_x, grid_y)
        if machine:
            factory.remove_machine(machine)
    
    def start_connection(self, machine: Machine):
        """开始连接"""
        self.is_connecting = True
        self.connection_start = machine
    
    def end_connection(self, machine: Machine) -> bool:
        """结束连接"""
        if self.is_connecting and self.connection_start and self.connection_start != machine:
            factory = self.get_current_factory()
            factory.connect(self.connection_start, machine)
            self.is_connecting = False
            self.connection_start = None
            return True
        self.is_connecting = False
        self.connection_start = None
        return False
    
    def cancel_connection(self):
        """取消连接"""
        self.is_connecting = False
        self.connection_start = None
    
    def run_factory(self):
        """运行工厂"""
        factory = self.get_current_factory()
        factory.start()
        if self.mode == 'playing' and self.current_level:
            self.current_level.start()
    
    def stop_factory(self):
        """停止工厂"""
        factory = self.get_current_factory()
        factory.stop()
        if self.mode == 'playing' and self.current_level:
            self.current_level.stop()
    
    def reset_factory(self):
        """重置工厂"""
        factory = self.get_current_factory()
        factory.reset()
        if self.mode == 'playing' and self.current_level:
            self.current_level.reset()
    
    def set_speed(self, speed: float):
        """设置速度"""
        factory = self.get_current_factory()
        factory.speed = max(0.25, min(4.0, speed))
    
    def save_blueprint(self, name: str, description: str) -> bool:
        """保存蓝图"""
        if not self.current_user:
            return False
        
        factory = self.get_current_factory()
        data = json.dumps(factory.to_dict())
        db.save_blueprint(self.current_user['id'], name, description, data)
        return True
    
    def load_blueprint(self, blueprint_id: int) -> bool:
        """加载蓝图"""
        blueprints = db.get_user_blueprints(self.current_user['id']) if self.current_user else []
        for bp in blueprints:
            if bp['id'] == blueprint_id:
                data = json.loads(bp['machine_data'])
                if self.mode == 'sandbox':
                    self.sandbox_factory = Factory.from_dict(data)
                return True
        return False
    
    def get_user_progress(self) -> Dict[str, Dict]:
        """获取用户进度"""
        if not self.current_user:
            return {}
        
        progress_list = db.get_user_progress(self.current_user['id'])
        return {p['level_id']: p for p in progress_list}
    
    def get_user_achievements(self) -> List[Dict]:
        """获取用户成就"""
        if not self.current_user:
            return []
        return db.get_user_achievements(self.current_user['id'])


# 代码执行引擎
class CodeExecutor:
    """代码执行引擎 - 安全执行用户代码"""
    
    SAFE_BUILTINS = {
        'abs': abs,
        'all': all,
        'any': any,
        'bool': bool,
        'dict': dict,
        'enumerate': enumerate,
        'filter': filter,
        'float': float,
        'int': int,
        'len': len,
        'list': list,
        'map': map,
        'max': max,
        'min': min,
        'print': print,
        'range': range,
        'round': round,
        'set': set,
        'sorted': sorted,
        'str': str,
        'sum': sum,
        'tuple': tuple,
        'type': type,
        'zip': zip,
    }
    
    def __init__(self):
        self.output_log: List[str] = []
        self.error_log: List[str] = []
        self.shapes_created: List[Shape] = []
        
    def reset(self):
        """重置执行状态"""
        self.output_log.clear()
        self.error_log.clear()
        self.shapes_created.clear()
    
    def execute(self, code: str) -> bool:
        """执行代码"""
        self.reset()
        
        # 创建安全的执行环境
        safe_globals = {
            '__builtins__': self.SAFE_BUILTINS,
            'Shape': Shape,
            'Circle': lambda color='white': create_shape('circle', color),
            'Square': lambda color='white': create_shape('square', color),
            'Triangle': lambda color='white': create_shape('triangle', color),
            'Diamond': lambda color='white': create_shape('diamond', color),
            'Star': lambda color='white': create_shape('star', color),
            'Hexagon': lambda color='white': create_shape('hexagon', color),
            'output': self._output_shape,
            'print': self._safe_print,
        }
        
        local_vars = {}
        
        try:
            exec(code, safe_globals, local_vars)
            return True
        except SyntaxError as e:
            self.error_log.append(f"语法错误 (第{e.lineno}行): {e.msg}")
            return False
        except Exception as e:
            self.error_log.append(f"运行错误: {str(e)}")
            return False
    
    def _output_shape(self, shape):
        """输出图形"""
        if isinstance(shape, Shape):
            self.shapes_created.append(shape)
            self.output_log.append(f"输出: {shape}")
        elif isinstance(shape, (list, tuple)):
            for s in shape:
                self._output_shape(s)
        else:
            self.output_log.append(f"输出: {shape}")
    
    def _safe_print(self, *args, **kwargs):
        """安全的print函数"""
        message = ' '.join(str(arg) for arg in args)
        self.output_log.append(message)
    
    def get_output(self) -> str:
        """获取输出日志"""
        return '\n'.join(self.output_log)
    
    def get_errors(self) -> str:
        """获取错误日志"""
        return '\n'.join(self.error_log)


# 全局游戏引擎实例
game_engine = GameEngine()
code_executor = CodeExecutor()
