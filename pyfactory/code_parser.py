"""
代码解析器 - 将Python代码解析为机器布局
实时解析用户输入的代码，生成对应的工厂布局
"""

import re
from typing import List, Dict, Any, Tuple, Optional


class CodeParser:
    """代码解析器 - 解析Python代码生成机器配置"""
    
    def __init__(self):
        self.machines = []
        self.connections = []
        self.variables = {}  # 存储变量名到机器的映射
        self.error = None
        self.error_line = -1
        
    def parse(self, code: str) -> Tuple[List[Dict], List[Tuple], Optional[str], int]:
        """
        解析代码，返回机器列表、连接列表、错误信息、错误行号
        
        支持的语法:
        - source = Source("circle", "white")  # 创建源头
        - painter = Painter("red")  # 创建染色机
        - rotator = Rotator()  # 创建旋转机
        - output = Output()  # 创建输出口
        - source.connect(painter)  # 连接机器
        - painter.connect(output)
        """
        self.machines = []
        self.connections = []
        self.variables = {}
        self.error = None
        self.error_line = -1
        
        lines = code.split('\n')
        machine_x = 1  # 自动布局x位置
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            
            try:
                # 解析变量赋值: var = Machine(...)
                if '=' in line and '.connect' not in line:
                    self._parse_assignment(line, line_num, machine_x)
                    machine_x += 2
                    
                # 解析连接: var1.connect(var2)
                elif '.connect(' in line:
                    self._parse_connection(line, line_num)
                    
            except Exception as e:
                self.error = str(e)
                self.error_line = line_num
                break
        
        return self.machines, self.connections, self.error, self.error_line
    
    def _parse_assignment(self, line: str, line_num: int, x_pos: int):
        """解析变量赋值语句"""
        # 匹配: var = Machine(args)
        match = re.match(r'(\w+)\s*=\s*(\w+)\s*\((.*)\)', line)
        if not match:
            raise ValueError(f"语法错误: {line}")
        
        var_name = match.group(1)
        machine_type = match.group(2).lower()
        args_str = match.group(3)
        
        # 解析参数
        args = self._parse_args(args_str)
        
        # 创建机器配置
        machine_config = {
            'var_name': var_name,
            'type': self._get_machine_type(machine_type),
            'x': x_pos,
            'y': 3,
            'args': args,
            'line': line_num
        }
        
        # 根据机器类型设置特定参数
        if machine_type == 'source':
            machine_config['shape_type'] = args.get(0, 'circle')
            machine_config['color'] = args.get(1, 'white')
        elif machine_type == 'painter':
            machine_config['target_color'] = args.get(0, 'red')
        elif machine_type == 'rotator':
            machine_config['rotation'] = int(args.get(0, 90))
        elif machine_type == 'splitter':
            pass
        elif machine_type == 'output':
            pass
        
        self.machines.append(machine_config)
        self.variables[var_name] = len(self.machines) - 1
    
    def _parse_connection(self, line: str, line_num: int):
        """解析连接语句"""
        # 匹配: var1.connect(var2)
        match = re.match(r'(\w+)\.connect\s*\(\s*(\w+)\s*\)', line)
        if not match:
            raise ValueError(f"连接语法错误: {line}")
        
        from_var = match.group(1)
        to_var = match.group(2)
        
        if from_var not in self.variables:
            raise ValueError(f"未定义的变量: {from_var}")
        if to_var not in self.variables:
            raise ValueError(f"未定义的变量: {to_var}")
        
        from_idx = self.variables[from_var]
        to_idx = self.variables[to_var]
        
        self.connections.append((from_idx, to_idx))
    
    def _parse_args(self, args_str: str) -> Dict[int, str]:
        """解析函数参数"""
        args = {}
        if not args_str.strip():
            return args
        
        parts = args_str.split(',')
        for i, part in enumerate(parts):
            part = part.strip()
            # 去除引号
            if part.startswith('"') and part.endswith('"'):
                part = part[1:-1]
            elif part.startswith("'") and part.endswith("'"):
                part = part[1:-1]
            args[i] = part
        
        return args
    
    def _get_machine_type(self, type_name: str) -> str:
        """获取机器类型标识"""
        type_map = {
            'source': 'source',
            'painter': 'painter',
            'rotator': 'rotator',
            'splitter': 'splitter',
            'output': 'output',
            'looper': 'looper',
            'function': 'function',
            'packer': 'packer',
        }
        if type_name not in type_map:
            raise ValueError(f"未知的机器类型: {type_name}")
        return type_map[type_name]


# 代码模板
CODE_TEMPLATES = {
    'basics_01': '''# 第一关：认识工厂
# 创建源头，产生白色圆形
source = Source("circle", "white")

# 创建输出口
output = Output()

# 连接源头到输出口
source.connect(output)
''',
    'basics_02': '''# 第二关：染色
# 创建源头
source = Source("circle", "white")

# 创建染色机，设置颜色为红色
painter = Painter("red")

# 创建输出口
output = Output()

# 按顺序连接
source.connect(painter)
painter.connect(output)
''',
    'basics_03': '''# 第三关：旋转
# 创建源头，产生蓝色三角形
source = Source("triangle", "blue")

# 创建旋转机，旋转90度
rotator = Rotator(90)

# 创建输出口
output = Output()

# 连接
source.connect(rotator)
rotator.connect(output)
''',
}


def get_template(level_id: str) -> str:
    """获取关卡代码模板"""
    return CODE_TEMPLATES.get(level_id, '''# 在这里编写代码
# 示例:
# source = Source("circle", "white")
# output = Output()
# source.connect(output)
''')


# 全局解析器实例
parser = CodeParser()
