"""
PyFactory - 机器系统
定义各种加工机器，每种机器对应一个编程概念
"""

import pygame
import math
from typing import Optional, List, Dict, Any, Callable, Tuple
from abc import ABC, abstractmethod
from shapes import Shape, ShapePackage, ShapeDict, create_shape
from config import COLORS, MACHINE_TYPES, GRID_SIZE
from fonts import get_font

# 调试开关：在发布时设为 False
DEBUG = False


class Connection:
    """连接类 - 表示机器之间的连接"""
    
    def __init__(self, from_machine: 'Machine', to_machine: 'Machine', 
                 from_port: str = 'output', to_port: str = 'input'):
        self.from_machine = from_machine
        self.to_machine = to_machine
        self.from_port = from_port
        self.to_port = to_port
        self.items_in_transit: List[Tuple[Any, float]] = []  # (item, progress)
        self.speed = 1.0  # 传输速度
        
    def update(self, dt: float):
        """更新传输中的物品"""
        completed = []
        for i, (item, progress) in enumerate(self.items_in_transit):
            new_progress = progress + dt * self.speed
            if new_progress >= 1.0:
                completed.append(i)
                # 调试输出：记录传递事件（受 DEBUG 控制）
                if DEBUG:
                    try:
                        print(f"[DEBUG] Connection: delivering {item!r} from {self.from_machine.machine_type} -> {self.to_machine.machine_type} (port={self.to_port})")
                    except Exception:
                        print("[DEBUG] Connection: delivering item (repr failed)")
                self.to_machine.receive(item, self.to_port)
            else:
                self.items_in_transit[i] = (item, new_progress)
        
        # 移除已完成的物品
        for i in reversed(completed):
            self.items_in_transit.pop(i)
    
    def send(self, item: Any):
        """发送物品"""
        self.items_in_transit.append((item, 0.0))
    
    def draw(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """绘制连接线和传输中的物品（带发光效果）"""
        start_x = self.from_machine.x * GRID_SIZE + GRID_SIZE // 2 + offset_x
        start_y = self.from_machine.y * GRID_SIZE + GRID_SIZE // 2 + offset_y
        end_x = self.to_machine.x * GRID_SIZE + GRID_SIZE // 2 + offset_x
        end_y = self.to_machine.y * GRID_SIZE + GRID_SIZE // 2 + offset_y
        
        # 发光效果（有物品传输时更亮）
        glow_intensity = 0.3 if self.items_in_transit else 0.1
        for i in range(3, 0, -1):
            alpha = int(60 * glow_intensity * (1 - i / 3))
            glow_color = (*COLORS['accent'][:3], alpha)
            glow_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            pygame.draw.line(glow_surface, glow_color,
                           (start_x, start_y), (end_x, end_y), 4 + i * 3)
            surface.blit(glow_surface, (0, 0))
        
        # 主连接线
        pygame.draw.line(surface, COLORS['conveyor'], 
                        (start_x, start_y), (end_x, end_y), 4)
        
        # 绘制箭头
        self._draw_arrow(surface, start_x, start_y, end_x, end_y)
        
        # 绘制传输中的物品（带平滑插值）
        for item, progress in self.items_in_transit:
            # 使用缓动函数让移动更平滑
            smooth_progress = self._ease_out_quad(progress)
            item_x = int(start_x + (end_x - start_x) * smooth_progress)
            item_y = int(start_y + (end_y - start_y) * smooth_progress)
            
            # 物品发光
            if isinstance(item, Shape):
                self._draw_item_glow(surface, item_x, item_y, item.get_color_rgb())
                item.draw(surface, item_x, item_y, 0.5)
    
    def _ease_out_quad(self, t: float) -> float:
        """缓出二次方缓动"""
        return 1 - (1 - t) ** 2
    
    def _draw_item_glow(self, surface: pygame.Surface, x: int, y: int, 
                        color: Tuple[int, int, int]):
        """绘制物品发光效果"""
        for i in range(4, 0, -1):
            alpha = int(40 * (1 - i / 4))
            glow_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*color, alpha), (15, 15), 8 + i * 2)
            surface.blit(glow_surface, (x - 15, y - 15))
    
    def _draw_arrow(self, surface: pygame.Surface, x1: int, y1: int, 
                    x2: int, y2: int):
        """绘制箭头"""
        angle = math.atan2(y2 - y1, x2 - x1)
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        
        arrow_size = 10
        p1 = (mid_x - arrow_size * math.cos(angle - 0.5),
              mid_y - arrow_size * math.sin(angle - 0.5))
        p2 = (mid_x - arrow_size * math.cos(angle + 0.5),
              mid_y - arrow_size * math.sin(angle + 0.5))
        
        pygame.draw.polygon(surface, COLORS['accent'], 
                           [(mid_x, mid_y), p1, p2])


class Machine(ABC):
    """机器基类 - 所有机器的抽象基类"""
    
    def __init__(self, machine_type: str, x: int, y: int):
        self.machine_type = machine_type
        self.x = x
        self.y = y
        self.input_buffer: List[Any] = []
        self.output_buffer: List[Any] = []
        self.connections_out: List[Connection] = []
        self.connections_in: List[Connection] = []
        self.processing_time = 0.5  # 处理时间
        self.current_process_time = 0
        self.is_processing = False
        self.current_item = None
        self.enabled = True
        self.code = ""  # 关联的代码
        
        # 动画状态
        self.anim_time = 0.0
        self.pulse_intensity = 0.0
        self.scale = 1.0
        
    def get_info(self) -> Dict[str, str]:
        """获取机器信息"""
        return MACHINE_TYPES.get(self.machine_type, {
            'name': '未知机器',
            'desc': '未知描述',
            'category': 'unknown'
        })
    
    def connect_to(self, other: 'Machine', from_port: str = 'output', 
                   to_port: str = 'input') -> Connection:
        """连接到另一台机器"""
        conn = Connection(self, other, from_port, to_port)
        self.connections_out.append(conn)
        other.connections_in.append(conn)
        return conn
    
    def disconnect_from(self, other: 'Machine'):
        """断开与另一台机器的连接"""
        self.connections_out = [c for c in self.connections_out 
                               if c.to_machine != other]
        other.connections_in = [c for c in other.connections_in 
                               if c.from_machine != self]
    
    def receive(self, item: Any, port: str = 'input'):
        """接收物品"""
        self.input_buffer.append(item)
    
    def send(self, item: Any, port: str = 'output'):
        """发送物品到所有输出连接"""
        if self.connections_out:
            for conn in self.connections_out:
                if conn.from_port == port:
                    conn.send(item)
        else:
            self.output_buffer.append(item)
    
    @abstractmethod
    def process(self, item: Any) -> Optional[Any]:
        """处理物品 - 子类必须实现"""
        pass
    
    def update(self, dt: float):
        """更新机器状态"""
        # 更新动画
        self.anim_time += dt
        
        if not self.enabled:
            return
            
        # 更新处理中的物品
        if self.is_processing:
            self.current_process_time += dt
            self.pulse_intensity = 0.5 + 0.5 * math.sin(self.anim_time * 8)
            if self.current_process_time >= self.processing_time:
                result = self.process(self.current_item)
                if result is not None:
                    if isinstance(result, tuple):
                        for item in result:
                            self.send(item)
                    else:
                        self.send(result)
                self.is_processing = False
                self.current_item = None
                self.current_process_time = 0
                self.pulse_intensity = 0
        else:
            self.pulse_intensity = max(0, self.pulse_intensity - dt * 3)
        
        # 开始处理新物品
        if not self.is_processing and self.input_buffer:
            self.current_item = self.input_buffer.pop(0)
            self.is_processing = True
            self.current_process_time = 0
        
        # 更新输出连接
        for conn in self.connections_out:
            conn.update(dt)
    
    def draw(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """绘制机器（带发光和动画效果）"""
        x = self.x * GRID_SIZE + offset_x
        y = self.y * GRID_SIZE + offset_y
        center_x = x + GRID_SIZE // 2
        center_y = y + GRID_SIZE // 2
        
        # 绘制机器背景
        rect = pygame.Rect(x + 4, y + 4, GRID_SIZE - 8, GRID_SIZE - 8)
        info = self.get_info()
        
        # 根据类别选择颜色
        category = info.get('category', 'basic')
        if category == 'logic':
            color = COLORS['accent']
        elif category == 'data':
            color = COLORS['success']
        elif category == 'transform':
            color = COLORS['warning']
        else:
            color = COLORS['machine']
        
        # 发光效果（处理中更亮）
        glow_intensity = 0.2 + self.pulse_intensity * 0.5
        self._draw_glow(surface, rect, color, glow_intensity)
        
        # 主体
        pygame.draw.rect(surface, color, rect, border_radius=10)
        pygame.draw.rect(surface, COLORS['text'], rect, 2, border_radius=10)
        
        # 处理进度条
        if self.is_processing:
            progress = self.current_process_time / self.processing_time
            bar_width = int((GRID_SIZE - 16) * progress)
            bar_rect = pygame.Rect(x + 8, y + GRID_SIZE - 12, bar_width, 4)
            pygame.draw.rect(surface, COLORS['success'], bar_rect, border_radius=2)
    
    def _draw_glow(self, surface: pygame.Surface, rect: pygame.Rect, 
                   color: Tuple[int, int, int], intensity: float):
        """绘制发光效果"""
        if intensity <= 0:
            return
        for i in range(4, 0, -1):
            alpha = int(40 * intensity * (1 - i / 4))
            glow_rect = rect.inflate(i * 4, i * 4)
            glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*color, alpha), 
                           glow_surface.get_rect(), border_radius=12 + i)
            surface.blit(glow_surface, glow_rect.topleft)


class SourceMachine(Machine):
    """源头机器 - 产生基础图形"""
    
    def __init__(self, x: int, y: int, shape_type: str = 'circle', 
                 color: str = 'white'):
        super().__init__('source', x, y)
        self.shape_type = shape_type
        self.color = color
        self.spawn_interval = 2.0  # 生成间隔
        self.spawn_timer = 0
        self.auto_spawn = True
        
    def process(self, item: Any) -> Optional[Any]:
        return item
    
    def update(self, dt: float):
        """更新并自动生成图形"""
        super().update(dt)
        
        if self.auto_spawn and self.enabled:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                new_shape = create_shape(self.shape_type, self.color)
                self.send(new_shape)
                self.spawn_timer = 0
    
    def set_output(self, shape_type: str, color: str):
        """设置输出的图形类型"""
        self.shape_type = shape_type
        self.color = color
    
    def draw(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """绘制源头机器 - 显示产出的图形"""
        super().draw(surface, offset_x, offset_y)
        
        x = self.x * GRID_SIZE + offset_x
        y = self.y * GRID_SIZE + offset_y
        center_x = x + GRID_SIZE // 2
        center_y = y + GRID_SIZE // 2
        
        # 绘制产出的图形预览
        preview_shape = create_shape(self.shape_type, self.color)
        if preview_shape:
            preview_shape.draw(surface, center_x, center_y, 0.5)
        
        # 显示机器名称
        font = get_font(14)
        text = font.render("源头", True, COLORS['text'])
        surface.blit(text, (x + 4, y + 4))


class OutputMachine(Machine):
    """输出机器 - 收集最终产品"""
    
    def __init__(self, x: int, y: int):
        super().__init__('output', x, y)
        self.collected: List[Any] = []
        self.target_shape: Optional[Shape] = None
        self.required_count = 1
        self.success_count = 0
        
    def process(self, item: Any) -> Optional[Any]:
        # 记录到已收集列表
        self.collected.append(item)

        # 调试：打印收到的物品与匹配检查结果（受 DEBUG 控制）
        if DEBUG:
            try:
                target_repr = repr(self.target_shape) if self.target_shape is not None else 'None'
                is_shape = isinstance(item, Shape)
                matches = item.matches(self.target_shape) if (is_shape and self.target_shape) else 'N/A'
                print(f"[DEBUG] OutputMachine.process: received {item!r}; is_shape={is_shape}; target={target_repr}; matches={matches}; before_success={self.success_count}")
            except Exception as e:
                print(f"[DEBUG] OutputMachine.process: debug print failed: {e}")

        # 检查是否匹配目标
        if self.target_shape and isinstance(item, Shape):
            if item.matches(self.target_shape):
                self.success_count += 1
                if DEBUG:
                    print(f"[DEBUG] OutputMachine: success_count incremented -> {self.success_count}")

        return None  # 输出机器不输出
    
    def set_target(self, shape: Shape, count: int = 1):
        """设置目标图形"""
        self.target_shape = shape
        self.required_count = count
        self.success_count = 0
        
    def is_goal_reached(self) -> bool:
        """检查是否达成目标"""
        return self.success_count >= self.required_count
    
    def draw(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """绘制输出机器"""
        super().draw(surface, offset_x, offset_y)
        
        x = self.x * GRID_SIZE + offset_x
        y = self.y * GRID_SIZE + offset_y
        center_x = x + GRID_SIZE // 2
        center_y = y + GRID_SIZE // 2
        
        # 绘制目标图形预览（如果已设置），并把箭头放在更下方以避免覆盖
        if self.target_shape:
            try:
                # 以较大比例绘制目标，放在机器中央偏上
                self.target_shape.draw(surface, center_x, center_y - 6, 0.6)
            except Exception:
                pass

            # 当有目标时，绘制一个更小且更靠下的箭头，避免覆盖目标预览
            pygame.draw.polygon(surface, COLORS['success'], [
                (center_x, center_y + 32),
                (center_x - 6, center_y + 8),
                (center_x + 6, center_y + 8)
            ])
        else:
            # 没有目标时，绘制默认大小的箭头
            pygame.draw.polygon(surface, COLORS['success'], [
                (center_x, center_y + 12),
                (center_x - 10, center_y - 5),
                (center_x + 10, center_y - 5)
            ])
        
        # 显示机器名称
        font = get_font(14)
        text = font.render("输出", True, COLORS['text'])
        surface.blit(text, (x + 4, y + 4))
        
        # 显示收集进度
        count_font = get_font(16)
        count_text = count_font.render(f"{self.success_count}/{self.required_count}", 
                          True, COLORS['success'])
        surface.blit(count_text, (x + GRID_SIZE - count_text.get_width() - 4, y + GRID_SIZE - 18))


class ConveyorMachine(Machine):
    """传送带 - 传输物品"""
    
    def __init__(self, x: int, y: int, direction: str = 'right'):
        super().__init__('conveyor', x, y)
        self.direction = direction  # 'up', 'down', 'left', 'right'
        self.processing_time = 0.2
        
    def process(self, item: Any) -> Optional[Any]:
        return item  # 直接传递


class PainterMachine(Machine):
    """染色机 - 改变图形颜色"""
    
    def __init__(self, x: int, y: int, target_color: str = 'red'):
        super().__init__('painter', x, y)
        self.target_color = target_color
        
    def process(self, item: Any) -> Optional[Any]:
        if isinstance(item, Shape):
            return item.paint(self.target_color)
        return item
    
    def set_color(self, color: str):
        """设置目标颜色"""
        self.target_color = color
    
    def draw(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """绘制染色机 - 显示目标颜色"""
        super().draw(surface, offset_x, offset_y)
        
        x = self.x * GRID_SIZE + offset_x
        y = self.y * GRID_SIZE + offset_y
        center_x = x + GRID_SIZE // 2
        center_y = y + GRID_SIZE // 2
        
        # 绘制目标颜色圆圈
        color_key = f'shape_{self.target_color}'
        paint_color = COLORS.get(color_key, COLORS.get('shape_white', (255, 255, 255)))
        pygame.draw.circle(surface, paint_color, (center_x, center_y), 15)
        pygame.draw.circle(surface, COLORS['text'], (center_x, center_y), 15, 2)
        
        # 显示机器名称
        font = get_font(14)
        text = font.render("染色", True, COLORS['text'])
        surface.blit(text, (x + 4, y + 4))


class CutterMachine(Machine):
    """切割机 - 将图形切成两半"""
    
    def __init__(self, x: int, y: int):
        super().__init__('cutter', x, y)
        
    def process(self, item: Any) -> Optional[Any]:
        if isinstance(item, Shape):
            return item.cut()  # 返回两个半边
        return item


class RotatorMachine(Machine):
    """旋转机 - 旋转图形"""
    
    def __init__(self, x: int, y: int, degrees: int = 90):
        super().__init__('rotator', x, y)
        self.degrees = degrees
        
    def process(self, item: Any) -> Optional[Any]:
        if isinstance(item, Shape):
            return item.rotate(self.degrees)
        return item


class StackerMachine(Machine):
    """堆叠机 - 合并两个图形"""
    
    def __init__(self, x: int, y: int):
        super().__init__('stacker', x, y)
        self.second_input: List[Any] = []
        
    def receive(self, item: Any, port: str = 'input'):
        if port == 'input2':
            self.second_input.append(item)
        else:
            self.input_buffer.append(item)
    
    def process(self, item: Any) -> Optional[Any]:
        if isinstance(item, Shape) and self.second_input:
            second = self.second_input.pop(0)
            if isinstance(second, Shape):
                return item.stack(second)
        return item


class SplitterMachine(Machine):
    """分拣器 - 对应 if/else 分支"""
    
    def __init__(self, x: int, y: int):
        super().__init__('splitter', x, y)
        self.condition_code = "shape.color == 'red'"  # 条件代码
        self.true_connections: List[Connection] = []
        self.false_connections: List[Connection] = []
        
    def set_condition(self, code: str):
        """设置分拣条件"""
        self.condition_code = code
        
    def evaluate_condition(self, item: Any) -> bool:
        """评估条件"""
        try:
            # 安全地执行条件代码
            local_vars = {'shape': item, 'item': item}
            result = eval(self.condition_code, {"__builtins__": {}}, local_vars)
            return bool(result)
        except:
            return False
    
    def process(self, item: Any) -> Optional[Any]:
        return item
    
    def send(self, item: Any, port: str = 'output'):
        """根据条件发送到不同输出"""
        if self.evaluate_condition(item):
            # 条件为真，发送到 output_true
            for conn in self.connections_out:
                if conn.from_port == 'output_true':
                    conn.send(item)
                    return
        else:
            # 条件为假，发送到 output_false
            for conn in self.connections_out:
                if conn.from_port == 'output_false':
                    conn.send(item)
                    return
        
        # 默认输出
        super().send(item, port)


class LooperMachine(Machine):
    """循环器 - 对应 for/while 循环"""
    
    def __init__(self, x: int, y: int):
        super().__init__('looper', x, y)
        self.loop_count = 3  # 循环次数
        self.current_loop = 0
        self.loop_code = "for i in range(3):"  # 循环代码示例
        
    def set_loop_count(self, count: int):
        """设置循环次数"""
        self.loop_count = count
        
    def process(self, item: Any) -> Optional[Any]:
        # 克隆并输出多份
        if isinstance(item, Shape):
            results = []
            for i in range(self.loop_count):
                clone = item.clone()
                clone.metadata['loop_index'] = i
                results.append(clone)
            return tuple(results)
        return item


class FunctionMachine(Machine):
    """函数机 - 对应 Python 函数"""
    
    def __init__(self, x: int, y: int, name: str = "my_function"):
        super().__init__('function', x, y)
        self.function_name = name
        self.function_code = ""
        self.inner_machines: List[Machine] = []
        self.inner_connections: List[Connection] = []
        
    def set_function(self, name: str, code: str):
        """设置函数"""
        self.function_name = name
        self.function_code = code
        
    def add_inner_machine(self, machine: Machine):
        """添加内部机器"""
        self.inner_machines.append(machine)
        
    def process(self, item: Any) -> Optional[Any]:
        # 通过内部机器处理
        current = item
        for machine in self.inner_machines:
            if current is not None:
                current = machine.process(current)
        return current


class PackerMachine(Machine):
    """打包机 - 对应 Python 列表"""
    
    def __init__(self, x: int, y: int, pack_size: int = 3):
        super().__init__('packer', x, y)
        self.pack_size = pack_size
        self.package_type = 'list'
        self.current_package: Optional[ShapePackage] = None
        
    def set_pack_size(self, size: int):
        """设置打包数量"""
        self.pack_size = size
        
    def process(self, item: Any) -> Optional[Any]:
        if self.current_package is None:
            self.current_package = ShapePackage(self.package_type)
        
        if isinstance(item, Shape):
            self.current_package.append(item)
        
        if len(self.current_package) >= self.pack_size:
            result = self.current_package
            self.current_package = None
            return result
        
        return None  # 还没装满


class UnpackerMachine(Machine):
    """拆包机 - 对应 Python 解包"""
    
    def __init__(self, x: int, y: int):
        super().__init__('unpacker', x, y)
        
    def process(self, item: Any) -> Optional[Any]:
        if isinstance(item, ShapePackage):
            return tuple(item.unpack())
        elif isinstance(item, ShapeDict):
            return tuple(item.values())
        return item


class DictPackerMachine(Machine):
    """标签机 - 对应 Python 字典"""
    
    def __init__(self, x: int, y: int):
        super().__init__('dict_packer', x, y)
        self.key_generator = lambda i: f"item_{i}"
        self.current_dict: Optional[ShapeDict] = None
        self.item_count = 0
        self.target_size = 3
        
    def process(self, item: Any) -> Optional[Any]:
        if self.current_dict is None:
            self.current_dict = ShapeDict()
            self.item_count = 0
        
        if isinstance(item, Shape):
            key = self.key_generator(self.item_count)
            self.current_dict.set(key, item)
            self.item_count += 1
        
        if self.item_count >= self.target_size:
            result = self.current_dict
            self.current_dict = None
            return result
        
        return None


class ComprehensionMachine(Machine):
    """推导机 - 对应 Python 列表推导式"""
    
    def __init__(self, x: int, y: int):
        super().__init__('comprehension', x, y)
        self.transform_code = "shape.paint('red')"
        self.filter_code = "True"
        
    def set_comprehension(self, transform: str, filter_cond: str = "True"):
        """设置推导式"""
        self.transform_code = transform
        self.filter_code = filter_cond
        
    def process(self, item: Any) -> Optional[Any]:
        if isinstance(item, ShapePackage):
            result = ShapePackage()
            for shape in item:
                try:
                    # 检查过滤条件
                    local_vars = {'shape': shape}
                    if eval(self.filter_code, {"__builtins__": {}}, local_vars):
                        # 应用变换
                        transformed = shape.clone()
                        exec(f"transformed = {self.transform_code}", 
                             {"__builtins__": {}, 'shape': transformed}, 
                             local_vars)
                        result.append(local_vars.get('transformed', transformed))
                except:
                    result.append(shape)
            return result
        return item


# 机器工厂函数
def create_machine(machine_type: str, x: int, y: int, **kwargs) -> Machine:
    """创建机器的工厂函数"""
    machine_classes = {
        'source': SourceMachine,
        'output': OutputMachine,
        'conveyor': ConveyorMachine,
        'painter': PainterMachine,
        'cutter': CutterMachine,
        'rotator': RotatorMachine,
        'stacker': StackerMachine,
        'splitter': SplitterMachine,
        'looper': LooperMachine,
        'function': FunctionMachine,
        'packer': PackerMachine,
        'unpacker': UnpackerMachine,
        'dict_packer': DictPackerMachine,
        'comprehension': ComprehensionMachine,
    }
    
    machine_class = machine_classes.get(machine_type, ConveyorMachine)
    return machine_class(x, y, **kwargs)
