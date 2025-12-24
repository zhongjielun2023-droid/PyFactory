"""
PyFactory - Python教学工厂游戏配置文件
"""

# 窗口设置
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "PyFactory - Python工厂教学游戏"
FPS = 60

# 网格设置
GRID_SIZE = 64
GRID_COLS = 12
GRID_ROWS = 8

# 颜色定义
COLORS = {
    'background': (30, 30, 40),
    'grid': (50, 50, 60),
    'grid_line': (70, 70, 80),
    'text': (255, 255, 255),
    'text_secondary': (180, 180, 180),
    'accent': (100, 200, 255),
    'success': (100, 255, 150),
    'error': (255, 100, 100),
    'warning': (255, 200, 100),
    
    # 图形颜色
    'shape_red': (255, 100, 100),
    'shape_green': (100, 255, 150),
    'shape_blue': (100, 150, 255),
    'shape_yellow': (255, 230, 100),
    'shape_purple': (200, 100, 255),
    'shape_orange': (255, 180, 100),
    'shape_white': (255, 255, 255),
    'shape_gray': (150, 150, 150),
    
    # UI颜色
    'panel_bg': (40, 40, 50),
    'panel_border': (80, 80, 100),
    'button_normal': (60, 60, 80),
    'button_hover': (80, 80, 100),
    'button_active': (100, 150, 200),
    'conveyor': (80, 80, 90),
    'machine': (70, 100, 130),
}

# 图形类型
SHAPE_TYPES = ['circle', 'square', 'triangle', 'diamond', 'star', 'hexagon']

# 图形颜色名称
SHAPE_COLORS = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'white', 'gray']

# 通用符号
STAR_FULL = '★'
STAR_EMPTY = '☆'

# 全局调试开关（发布时设为 False）
DEBUG = False

# 机器类型定义
MACHINE_TYPES = {
    'source': {'name': '源头', 'desc': '产生基础图形', 'category': 'basic'},
    'output': {'name': '输出口', 'desc': '收集最终产品', 'category': 'basic'},
    'conveyor': {'name': '传送带', 'desc': '传输图形', 'category': 'basic'},
    
    # 变换机器
    'painter': {'name': '染色机', 'desc': '改变图形颜色', 'category': 'transform'},
    'cutter': {'name': '切割机', 'desc': '将图形切成两半', 'category': 'transform'},
    'rotator': {'name': '旋转机', 'desc': '旋转图形90度', 'category': 'transform'},
    'stacker': {'name': '堆叠机', 'desc': '合并两个图形', 'category': 'transform'},
    
    # 逻辑机器（对应编程概念）
    'splitter': {'name': '分拣器', 'desc': '根据条件分流(if/else)', 'category': 'logic'},
    'looper': {'name': '循环器', 'desc': '重复处理(for/while)', 'category': 'logic'},
    'function': {'name': '函数机', 'desc': '可复用的加工蓝图', 'category': 'logic'},
    
    # 数据结构机器
    'packer': {'name': '打包机', 'desc': '将多个图形打包成列表', 'category': 'data'},
    'unpacker': {'name': '拆包机', 'desc': '拆解列表中的图形', 'category': 'data'},
    'dict_packer': {'name': '标签机', 'desc': '创建带标签的字典', 'category': 'data'},
    'comprehension': {'name': '推导机', 'desc': '批量加工(列表推导式)', 'category': 'data'},
}

# 关卡类别
LEVEL_CATEGORIES = {
    'basics': '基础入门',
    'variables': '变量与赋值',
    'conditionals': '条件分支',
    'loops': '循环结构',
    'functions': '函数定义',
    'data_structures': '数据结构',
    'advanced': '进阶技巧',
}

# 数据库配置
DATABASE_PATH = 'pyfactory.db'

# 默认用户
DEFAULT_USER = {'username': 'x', 'password': '1'}
