"""
PyFactory - 图形系统
定义基础图形及其变换操作
"""

import pygame
import math
from typing import Optional, List, Tuple, Dict, Any
from config import COLORS, SHAPE_TYPES, SHAPE_COLORS
from fonts import get_font


class Shape:
    """基础图形类 - 所有图形的基类"""
    
    def __init__(self, shape_type: str, color: str, size: int = 40):
        self.shape_type = shape_type
        self.color = color
        self.size = size
        self.rotation = 0  # 旋转角度 (0, 90, 180, 270)
        self.layers = []  # 用于堆叠的图层
        self.metadata = {}  # 额外元数据
        
    def get_color_rgb(self) -> Tuple[int, int, int]:
        """获取RGB颜色值"""
        color_key = f'shape_{self.color}'
        return COLORS.get(color_key, COLORS['shape_white'])
    
    def clone(self) -> 'Shape':
        """克隆当前图形"""
        new_shape = Shape(self.shape_type, self.color, self.size)
        new_shape.rotation = self.rotation
        new_shape.layers = [layer.clone() for layer in self.layers]
        new_shape.metadata = self.metadata.copy()
        return new_shape
    
    def rotate(self, degrees: int = 90) -> 'Shape':
        """旋转图形"""
        self.rotation = (self.rotation + degrees) % 360
        return self
    
    def paint(self, new_color: str) -> 'Shape':
        """改变颜色"""
        if new_color in SHAPE_COLORS:
            self.color = new_color
        return self
    
    def stack(self, other: 'Shape') -> 'Shape':
        """堆叠另一个图形"""
        self.layers.append(other.clone())
        return self
    
    def cut(self) -> Tuple['Shape', 'Shape']:
        """切割图形，返回左右两半"""
        left = self.clone()
        right = self.clone()
        left.metadata['half'] = 'left'
        right.metadata['half'] = 'right'
        left.size = self.size // 2
        right.size = self.size // 2
        return left, right
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            'type': self.shape_type,
            'color': self.color,
            'size': self.size,
            'rotation': self.rotation,
            'layers': [layer.to_dict() for layer in self.layers],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Shape':
        """从字典创建图形"""
        shape = cls(data['type'], data['color'], data.get('size', 40))
        shape.rotation = data.get('rotation', 0)
        shape.layers = [cls.from_dict(layer) for layer in data.get('layers', [])]
        shape.metadata = data.get('metadata', {})
        return shape
    
    def matches(self, target: 'Shape') -> bool:
        """检查是否与目标图形匹配"""
        if self.shape_type != target.shape_type:
            return False
        if self.color != target.color:
            return False
        if self.rotation != target.rotation:
            return False
        if len(self.layers) != len(target.layers):
            return False
        for my_layer, target_layer in zip(self.layers, target.layers):
            if not my_layer.matches(target_layer):
                return False
        return True
    
    def draw(self, surface: pygame.Surface, x: int, y: int, scale: float = 1.0):
        """在指定位置绘制图形"""
        color = self.get_color_rgb()
        size = int(self.size * scale)
        half = size // 2
        
        # 绘制底层图形
        self._draw_shape(surface, x, y, size, color)
        
        # 绘制堆叠的图层
        for i, layer in enumerate(self.layers):
            layer_scale = 0.7 ** (i + 1)
            layer.draw(surface, x, y, scale * layer_scale)
    
    def _draw_shape(self, surface: pygame.Surface, x: int, y: int, size: int, color: Tuple):
        """绘制具体形状"""
        half = size // 2
        
        if self.shape_type == 'circle':
            pygame.draw.circle(surface, color, (x, y), half)
            pygame.draw.circle(surface, (255, 255, 255), (x, y), half, 2)
            
        elif self.shape_type == 'square':
            rect = pygame.Rect(x - half, y - half, size, size)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (255, 255, 255), rect, 2)
            
        elif self.shape_type == 'triangle':
            points = self._get_triangle_points(x, y, half)
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
            
        elif self.shape_type == 'diamond':
            points = [
                (x, y - half),
                (x + half, y),
                (x, y + half),
                (x - half, y)
            ]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
            
        elif self.shape_type == 'star':
            points = self._get_star_points(x, y, half)
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
            
        elif self.shape_type == 'hexagon':
            points = self._get_hexagon_points(x, y, half)
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        # 处理半边图形
        if self.metadata.get('half') == 'left':
            pygame.draw.rect(surface, COLORS['background'], 
                           pygame.Rect(x, y - half - 2, half + 4, size + 4))
        elif self.metadata.get('half') == 'right':
            pygame.draw.rect(surface, COLORS['background'], 
                           pygame.Rect(x - half - 4, y - half - 2, half + 4, size + 4))
    
    def _get_triangle_points(self, x: int, y: int, half: int) -> List[Tuple[int, int]]:
        """获取三角形的顶点"""
        base_points = [
            (x, y - half),
            (x + half, y + half),
            (x - half, y + half)
        ]
        return self._rotate_points(base_points, x, y, self.rotation)
    
    def _get_star_points(self, x: int, y: int, half: int) -> List[Tuple[int, int]]:
        """获取五角星的顶点"""
        points = []
        inner_half = half // 2
        for i in range(5):
            # 外顶点
            angle = math.radians(-90 + i * 72)
            points.append((
                int(x + half * math.cos(angle)),
                int(y + half * math.sin(angle))
            ))
            # 内顶点
            angle = math.radians(-90 + i * 72 + 36)
            points.append((
                int(x + inner_half * math.cos(angle)),
                int(y + inner_half * math.sin(angle))
            ))
        return self._rotate_points(points, x, y, self.rotation)
    
    def _get_hexagon_points(self, x: int, y: int, half: int) -> List[Tuple[int, int]]:
        """获取六边形的顶点"""
        points = []
        for i in range(6):
            angle = math.radians(30 + i * 60)
            points.append((
                int(x + half * math.cos(angle)),
                int(y + half * math.sin(angle))
            ))
        return self._rotate_points(points, x, y, self.rotation)
    
    def _rotate_points(self, points: List[Tuple[int, int]], cx: int, cy: int, 
                       degrees: int) -> List[Tuple[int, int]]:
        """旋转点集"""
        if degrees == 0:
            return points
        angle = math.radians(degrees)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        rotated = []
        for px, py in points:
            dx = px - cx
            dy = py - cy
            new_x = cx + dx * cos_a - dy * sin_a
            new_y = cy + dx * sin_a + dy * cos_a
            rotated.append((int(new_x), int(new_y)))
        return rotated
    
    def __repr__(self):
        return f"Shape({self.shape_type}, {self.color}, rot={self.rotation})"


class ShapePackage:
    """图形包 - 对应Python列表/元组"""
    
    def __init__(self, package_type: str = 'list'):
        self.package_type = package_type  # 'list' 或 'tuple'
        self.items: List[Shape] = []
        self.is_mutable = (package_type == 'list')
        
    def append(self, shape: Shape):
        """添加图形"""
        if self.is_mutable:
            self.items.append(shape)
        else:
            raise ValueError("元组不可修改!")
    
    def pop(self) -> Optional[Shape]:
        """弹出最后一个图形"""
        if self.is_mutable and self.items:
            return self.items.pop()
        return None
    
    def get(self, index: int) -> Optional[Shape]:
        """获取指定索引的图形"""
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def unpack(self) -> List[Shape]:
        """解包所有图形"""
        return self.items.copy()
    
    def __len__(self):
        return len(self.items)
    
    def __iter__(self):
        return iter(self.items)
    
    def draw(self, surface: pygame.Surface, x: int, y: int, scale: float = 0.5):
        """绘制包裹"""
        # 绘制包裹外框
        box_width = 60
        box_height = 30 + len(self.items) * 20
        rect = pygame.Rect(x - box_width // 2, y - box_height // 2, 
                          box_width, box_height)
        
        if self.package_type == 'list':
            color = COLORS['accent']
        else:
            color = COLORS['warning']
            
        pygame.draw.rect(surface, COLORS['panel_bg'], rect)
        pygame.draw.rect(surface, color, rect, 2)
        
        # 绘制内部图形缩略图
        for i, shape in enumerate(self.items[:4]):  # 最多显示4个
            shape.draw(surface, x, y - box_height // 2 + 20 + i * 20, 0.3)
        
        if len(self.items) > 4:
            font = get_font(20)
            text = font.render(f"+{len(self.items) - 4}", True, COLORS['text'])
            surface.blit(text, (x + 10, y + box_height // 2 - 15))


class ShapeDict:
    """图形字典 - 对应Python字典"""
    
    def __init__(self):
        self.items: Dict[str, Shape] = {}
        
    def set(self, key: str, shape: Shape):
        """设置键值对"""
        self.items[key] = shape
        
    def get(self, key: str) -> Optional[Shape]:
        """获取指定键的图形"""
        return self.items.get(key)
    
    def keys(self) -> List[str]:
        """获取所有键"""
        return list(self.items.keys())
    
    def values(self) -> List[Shape]:
        """获取所有值"""
        return list(self.items.values())
    
    def items_list(self) -> List[Tuple[str, Shape]]:
        """获取所有键值对"""
        return list(self.items.items())
    
    def draw(self, surface: pygame.Surface, x: int, y: int, scale: float = 0.5):
        """绘制字典"""
        box_width = 80
        box_height = 30 + len(self.items) * 25
        rect = pygame.Rect(x - box_width // 2, y - box_height // 2, 
                          box_width, box_height)
        
        pygame.draw.rect(surface, COLORS['panel_bg'], rect)
        pygame.draw.rect(surface, COLORS['success'], rect, 2)
        
        font = get_font(18)
        for i, (key, shape) in enumerate(list(self.items.items())[:3]):
            # 绘制键
            text = font.render(f"{key}:", True, COLORS['text_secondary'])
            surface.blit(text, (x - box_width // 2 + 5, 
                               y - box_height // 2 + 10 + i * 25))
            # 绘制值
            shape.draw(surface, x + 20, y - box_height // 2 + 20 + i * 25, 0.25)


def create_shape(shape_type: str, color: str) -> Shape:
    """工厂函数：创建图形"""
    if shape_type not in SHAPE_TYPES:
        shape_type = 'circle'
    if color not in SHAPE_COLORS:
        color = 'white'
    return Shape(shape_type, color)


def create_random_shape() -> Shape:
    """创建随机图形"""
    import random
    shape_type = random.choice(SHAPE_TYPES)
    color = random.choice(SHAPE_COLORS)
    return create_shape(shape_type, color)
