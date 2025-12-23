"""
PyFactory - 数据库模块
使用 SQLite 存储用户进度、关卡数据等
"""

import sqlite3
import json
from typing import Optional, List, Dict, Any
from config import DATABASE_PATH, DEFAULT_USER


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.init_database()
        
    def connect(self):
        """连接数据库"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 用户进度表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                level_id TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                stars INTEGER DEFAULT 0,
                best_time REAL DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                solution_data TEXT,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, level_id)
            )
        ''')
        
        # 关卡表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS levels (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                difficulty INTEGER DEFAULT 1,
                order_index INTEGER DEFAULT 0,
                target_data TEXT,
                initial_data TEXT,
                hints TEXT,
                python_concept TEXT,
                code_template TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 自定义蓝图表（用户创建的函数/机器）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blueprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                machine_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 成就表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                icon TEXT,
                points INTEGER DEFAULT 10
            )
        ''')
        
        # 用户成就表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (achievement_id) REFERENCES achievements(id),
                UNIQUE(user_id, achievement_id)
            )
        ''')
        
        # 代码片段表（用户保存的代码）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                level_id TEXT,
                code TEXT NOT NULL,
                is_solution INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        
        # 初始化默认数据
        self._init_default_data()
    
    def _init_default_data(self):
        """初始化默认数据"""
        # 添加默认用户
        self.add_user(DEFAULT_USER['username'], DEFAULT_USER['password'])
        
        # 添加初始关卡
        self._init_levels()
        
        # 添加成就
        self._init_achievements()
    
    def _init_levels(self):
        """初始化关卡数据"""
        levels = [
            # 基础入门
            {
                'id': 'basics_01',
                'category': 'basics',
                'title': '第一步：认识工厂',
                'description': '学习如何放置源头和输出口，让图形从源头流向输出',
                'difficulty': 1,
                'order_index': 1,
                'python_concept': '程序的基本结构：输入和输出',
                'target_data': json.dumps({
                    'shape': {'type': 'circle', 'color': 'white'},
                    'count': 1
                }),
                'hints': json.dumps([
                    '点击源头机器，它会自动产生图形',
                    '将源头连接到输出口',
                    '图形会自动传送到输出口'
                ]),
                'code_template': '# 程序从上到下执行\n# 输入 -> 处理 -> 输出\nshape = input()  # 获取图形\noutput(shape)    # 输出图形'
            },
            {
                'id': 'basics_02',
                'category': 'basics',
                'title': '染色初体验',
                'description': '使用染色机将白色圆形变成红色',
                'difficulty': 1,
                'order_index': 2,
                'python_concept': '变量赋值和修改',
                'target_data': json.dumps({
                    'shape': {'type': 'circle', 'color': 'red'},
                    'count': 1
                }),
                'hints': json.dumps([
                    '放置一个染色机在源头和输出之间',
                    '设置染色机的颜色为红色'
                ]),
                'code_template': '# 变量赋值\nshape = Circle("white")\n# 修改变量的属性\nshape.color = "red"\noutput(shape)'
            },
            {
                'id': 'basics_03',
                'category': 'basics',
                'title': '形状变换',
                'description': '使用旋转机旋转三角形',
                'difficulty': 1,
                'order_index': 3,
                'python_concept': '方法调用',
                'target_data': json.dumps({
                    'shape': {'type': 'triangle', 'color': 'blue', 'rotation': 90},
                    'count': 1
                }),
                'hints': json.dumps([
                    '旋转机每次旋转90度',
                    '连接：源头 -> 旋转机 -> 输出'
                ]),
                'code_template': '# 调用方法\nshape = Triangle("blue")\nshape.rotate(90)  # 旋转90度\noutput(shape)'
            },
            
            # 变量与赋值
            {
                'id': 'variables_01',
                'category': 'variables',
                'title': '储物箱：变量',
                'description': '使用储物箱（变量）暂存图形',
                'difficulty': 2,
                'order_index': 1,
                'python_concept': '变量的概念',
                'target_data': json.dumps({
                    'shape': {'type': 'square', 'color': 'green'},
                    'count': 2
                }),
                'hints': json.dumps([
                    '变量就像储物箱，可以存放和取出物品',
                    '一个变量一次只能存放一个值'
                ]),
                'code_template': '# 变量就像储物箱\nbox = Square("green")  # 存入\nshape1 = box  # 取出使用\nshape2 = box  # 可以多次使用\noutput(shape1)\noutput(shape2)'
            },
            {
                'id': 'variables_02',
                'category': 'variables',
                'title': '多个变量',
                'description': '使用多个变量存储不同的图形',
                'difficulty': 2,
                'order_index': 2,
                'python_concept': '多变量操作',
                'target_data': json.dumps({
                    'shapes': [
                        {'type': 'circle', 'color': 'red'},
                        {'type': 'square', 'color': 'blue'}
                    ],
                    'count': 2
                }),
                'hints': json.dumps([
                    '可以创建多个变量存储不同的图形',
                    '每个变量有自己的名字'
                ]),
                'code_template': '# 多个变量\nshape_a = Circle("red")\nshape_b = Square("blue")\noutput(shape_a)\noutput(shape_b)'
            },
            
            # 条件分支
            {
                'id': 'conditionals_01',
                'category': 'conditionals',
                'title': '分拣器：if语句',
                'description': '使用分拣器根据颜色分流图形',
                'difficulty': 3,
                'order_index': 1,
                'python_concept': 'if 条件语句',
                'target_data': json.dumps({
                    'outputs': {
                        'red': {'type': 'circle', 'color': 'red'},
                        'blue': {'type': 'circle', 'color': 'blue'}
                    }
                }),
                'hints': json.dumps([
                    '分拣器可以根据条件将图形分到不同的路径',
                    '设置条件：shape.color == "red"'
                ]),
                'code_template': '# if 条件语句\nif shape.color == "red":\n    output_a(shape)  # 红色走A口\nelse:\n    output_b(shape)  # 其他走B口'
            },
            {
                'id': 'conditionals_02',
                'category': 'conditionals',
                'title': '多重分拣',
                'description': '使用多个条件进行复杂分拣',
                'difficulty': 3,
                'order_index': 2,
                'python_concept': 'if-elif-else 语句',
                'target_data': json.dumps({
                    'outputs': {
                        'red': {'type': 'any', 'color': 'red'},
                        'blue': {'type': 'any', 'color': 'blue'},
                        'other': {'type': 'any', 'color': 'any'}
                    }
                }),
                'hints': json.dumps([
                    '可以串联多个分拣器',
                    '每个分拣器检查一个条件'
                ]),
                'code_template': '# if-elif-else\nif shape.color == "red":\n    output_a(shape)\nelif shape.color == "blue":\n    output_b(shape)\nelse:\n    output_c(shape)'
            },
            
            # 循环结构
            {
                'id': 'loops_01',
                'category': 'loops',
                'title': '循环器：for循环',
                'description': '使用循环器复制图形',
                'difficulty': 3,
                'order_index': 1,
                'python_concept': 'for 循环',
                'target_data': json.dumps({
                    'shape': {'type': 'circle', 'color': 'red'},
                    'count': 5
                }),
                'hints': json.dumps([
                    '循环器可以将一个图形复制多份',
                    '设置循环次数为5'
                ]),
                'code_template': '# for 循环\nfor i in range(5):\n    shape = Circle("red")\n    output(shape)'
            },
            {
                'id': 'loops_02',
                'category': 'loops',
                'title': '循环加工',
                'description': '在循环中对图形进行加工',
                'difficulty': 4,
                'order_index': 2,
                'python_concept': '循环与加工结合',
                'target_data': json.dumps({
                    'shapes': [
                        {'type': 'circle', 'color': 'red', 'rotation': 0},
                        {'type': 'circle', 'color': 'red', 'rotation': 90},
                        {'type': 'circle', 'color': 'red', 'rotation': 180},
                        {'type': 'circle', 'color': 'red', 'rotation': 270}
                    ]
                }),
                'hints': json.dumps([
                    '每次循环可以进行不同的加工',
                    '使用循环变量 i 来控制旋转角度'
                ]),
                'code_template': '# 循环中加工\nfor i in range(4):\n    shape = Circle("red")\n    shape.rotate(i * 90)\n    output(shape)'
            },
            
            # 函数定义
            {
                'id': 'functions_01',
                'category': 'functions',
                'title': '函数机：创建蓝图',
                'description': '创建一个可复用的加工蓝图',
                'difficulty': 4,
                'order_index': 1,
                'python_concept': '函数定义 def',
                'target_data': json.dumps({
                    'shape': {'type': 'circle', 'color': 'red'},
                    'count': 3
                }),
                'hints': json.dumps([
                    '函数机可以保存一系列加工步骤',
                    '创建蓝图后可以重复使用'
                ]),
                'code_template': '# 定义函数\ndef make_red_circle():\n    shape = Circle("white")\n    shape.paint("red")\n    return shape\n\n# 调用函数\nfor i in range(3):\n    result = make_red_circle()\n    output(result)'
            },
            {
                'id': 'functions_02',
                'category': 'functions',
                'title': '带参数的函数',
                'description': '创建接受参数的加工函数',
                'difficulty': 4,
                'order_index': 2,
                'python_concept': '函数参数',
                'target_data': json.dumps({
                    'shapes': [
                        {'type': 'circle', 'color': 'red'},
                        {'type': 'circle', 'color': 'blue'},
                        {'type': 'circle', 'color': 'green'}
                    ]
                }),
                'hints': json.dumps([
                    '函数可以接受参数',
                    '参数可以控制加工的方式'
                ]),
                'code_template': '# 带参数的函数\ndef paint_circle(color):\n    shape = Circle("white")\n    shape.paint(color)\n    return shape\n\n# 用不同参数调用\ncolors = ["red", "blue", "green"]\nfor c in colors:\n    result = paint_circle(c)\n    output(result)'
            },
            
            # 数据结构
            {
                'id': 'data_structures_01',
                'category': 'data_structures',
                'title': '打包机：列表',
                'description': '使用打包机将多个图形打包成列表',
                'difficulty': 4,
                'order_index': 1,
                'python_concept': '列表 list',
                'target_data': json.dumps({
                    'package': {
                        'type': 'list',
                        'items': [
                            {'type': 'circle', 'color': 'red'},
                            {'type': 'square', 'color': 'blue'},
                            {'type': 'triangle', 'color': 'green'}
                        ]
                    }
                }),
                'hints': json.dumps([
                    '打包机将多个图形打包成一个列表',
                    '列表可以包含多个元素'
                ]),
                'code_template': '# 创建列表\nshapes = [\n    Circle("red"),\n    Square("blue"),\n    Triangle("green")\n]\noutput(shapes)'
            },
            {
                'id': 'data_structures_02',
                'category': 'data_structures',
                'title': '拆包机：解包',
                'description': '使用拆包机将列表解包为单个图形',
                'difficulty': 4,
                'order_index': 2,
                'python_concept': '解包操作',
                'target_data': json.dumps({
                    'shapes': [
                        {'type': 'circle', 'color': 'red'},
                        {'type': 'square', 'color': 'blue'}
                    ]
                }),
                'hints': json.dumps([
                    '拆包机将列表中的元素逐个取出',
                    'Python中可以用 * 解包列表'
                ]),
                'code_template': '# 解包列表\nshapes = [Circle("red"), Square("blue")]\na, b = shapes  # 解包赋值\noutput(a)\noutput(b)'
            },
            {
                'id': 'data_structures_03',
                'category': 'data_structures',
                'title': '标签机：字典',
                'description': '使用标签机创建带标签的图形字典',
                'difficulty': 5,
                'order_index': 3,
                'python_concept': '字典 dict',
                'target_data': json.dumps({
                    'dict': {
                        'head': {'type': 'circle', 'color': 'yellow'},
                        'body': {'type': 'square', 'color': 'blue'}
                    }
                }),
                'hints': json.dumps([
                    '字典使用键值对存储数据',
                    '可以通过键来访问值'
                ]),
                'code_template': '# 创建字典\nrobot = {\n    "head": Circle("yellow"),\n    "body": Square("blue")\n}\noutput(robot["head"])\noutput(robot["body"])'
            },
            
            # 进阶技巧
            {
                'id': 'advanced_01',
                'category': 'advanced',
                'title': '推导机：列表推导式',
                'description': '使用推导机批量加工图形',
                'difficulty': 5,
                'order_index': 1,
                'python_concept': '列表推导式',
                'target_data': json.dumps({
                    'shapes': [
                        {'type': 'circle', 'color': 'red'},
                        {'type': 'circle', 'color': 'red'},
                        {'type': 'circle', 'color': 'red'}
                    ]
                }),
                'hints': json.dumps([
                    '推导式可以一行代码批量处理',
                    '语法：[表达式 for 变量 in 序列]'
                ]),
                'code_template': '# 列表推导式\nwhite_circles = [Circle("white") for _ in range(3)]\nred_circles = [c.paint("red") for c in white_circles]\nfor shape in red_circles:\n    output(shape)'
            },
            {
                'id': 'advanced_02',
                'category': 'advanced',
                'title': '条件推导式',
                'description': '使用带条件的推导式筛选图形',
                'difficulty': 5,
                'order_index': 2,
                'python_concept': '带条件的列表推导式',
                'target_data': json.dumps({
                    'shapes': [
                        {'type': 'circle', 'color': 'red'}
                    ],
                    'filter': 'color == red'
                }),
                'hints': json.dumps([
                    '推导式可以添加条件过滤',
                    '语法：[表达式 for 变量 in 序列 if 条件]'
                ]),
                'code_template': '# 带条件的推导式\nshapes = [Circle("red"), Square("blue"), Circle("red")]\nred_only = [s for s in shapes if s.color == "red"]\nfor shape in red_only:\n    output(shape)'
            },
        ]
        
        conn = self.connect()
        cursor = conn.cursor()
        
        for level in levels:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO levels 
                    (id, category, title, description, difficulty, order_index,
                     python_concept, target_data, hints, code_template)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    level['id'], level['category'], level['title'],
                    level['description'], level['difficulty'], level['order_index'],
                    level['python_concept'], level.get('target_data', '{}'),
                    level.get('hints', '[]'), level.get('code_template', '')
                ))
            except sqlite3.Error:
                pass
        
        conn.commit()
    
    def _init_achievements(self):
        """初始化成就"""
        achievements = [
            ('first_step', '第一步', '完成第一个关卡', '🎯', 10),
            ('fast_learner', '快速学习者', '在30秒内完成一个关卡', '⚡', 20),
            ('loop_master', '循环大师', '完成所有循环关卡', '🔄', 30),
            ('function_guru', '函数达人', '完成所有函数关卡', '📦', 30),
            ('data_wizard', '数据巫师', '完成所有数据结构关卡', '📊', 40),
            ('perfectionist', '完美主义者', '在所有关卡获得3星', '⭐', 100),
            ('coder', '编程达人', '完成全部关卡', '🏆', 50),
        ]
        
        conn = self.connect()
        cursor = conn.cursor()
        
        for ach_id, title, desc, icon, points in achievements:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO achievements (id, title, description, icon, points)
                    VALUES (?, ?, ?, ?, ?)
                ''', (ach_id, title, desc, icon, points))
            except sqlite3.Error:
                pass
        
        conn.commit()
    
    # 用户相关方法
    def add_user(self, username: str, password: str) -> Optional[int]:
        """添加用户"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)',
                (username, password)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error:
            return None
    
    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        """验证用户"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """获取用户信息"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    # 关卡相关方法
    def get_all_levels(self) -> List[Dict]:
        """获取所有关卡"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM levels ORDER BY category, order_index')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_levels_by_category(self, category: str) -> List[Dict]:
        """获取指定类别的关卡"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM levels WHERE category = ? ORDER BY order_index',
            (category,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_level(self, level_id: str) -> Optional[Dict]:
        """获取指定关卡"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM levels WHERE id = ?', (level_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    # 进度相关方法
    def get_user_progress(self, user_id: int) -> List[Dict]:
        """获取用户进度"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM user_progress WHERE user_id = ?',
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_level_progress(self, user_id: int, level_id: str) -> Optional[Dict]:
        """获取用户在指定关卡的进度"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM user_progress WHERE user_id = ? AND level_id = ?',
            (user_id, level_id)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def update_progress(self, user_id: int, level_id: str, completed: bool,
                       stars: int, time_taken: float, solution_data: str = ''):
        """更新用户进度"""
        conn = self.connect()
        cursor = conn.cursor()
        
        existing = self.get_level_progress(user_id, level_id)
        
        if existing:
            # 更新现有记录
            new_stars = max(existing['stars'], stars)
            new_time = existing['best_time']
            if time_taken > 0 and (new_time == 0 or time_taken < new_time):
                new_time = time_taken
            
            cursor.execute('''
                UPDATE user_progress 
                SET completed = ?, stars = ?, best_time = ?, 
                    attempts = attempts + 1, solution_data = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND level_id = ?
            ''', (1 if completed else 0, new_stars, new_time, 
                  solution_data, user_id, level_id))
        else:
            # 创建新记录
            cursor.execute('''
                INSERT INTO user_progress 
                (user_id, level_id, completed, stars, best_time, attempts, solution_data)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            ''', (user_id, level_id, 1 if completed else 0, stars, 
                  time_taken, solution_data))
        
        conn.commit()
    
    # 蓝图相关方法
    def save_blueprint(self, user_id: int, name: str, description: str,
                      machine_data: str) -> int:
        """保存蓝图"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO blueprints (user_id, name, description, machine_data)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, description, machine_data))
        conn.commit()
        return cursor.lastrowid
    
    def get_user_blueprints(self, user_id: int) -> List[Dict]:
        """获取用户的蓝图"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM blueprints WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def delete_blueprint(self, blueprint_id: int, user_id: int):
        """删除蓝图"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM blueprints WHERE id = ? AND user_id = ?',
            (blueprint_id, user_id)
        )
        conn.commit()
    
    # 成就相关方法
    def unlock_achievement(self, user_id: int, achievement_id: str):
        """解锁成就"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO user_achievements (user_id, achievement_id)
                VALUES (?, ?)
            ''', (user_id, achievement_id))
            conn.commit()
        except sqlite3.Error:
            pass
    
    def get_user_achievements(self, user_id: int) -> List[Dict]:
        """获取用户成就"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, ua.unlocked_at 
            FROM achievements a
            LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
        ''', (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    # 代码片段相关方法
    def save_code(self, user_id: int, level_id: str, code: str, 
                  is_solution: bool = False) -> int:
        """保存代码片段"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO code_snippets (user_id, level_id, code, is_solution)
            VALUES (?, ?, ?, ?)
        ''', (user_id, level_id, code, 1 if is_solution else 0))
        conn.commit()
        return cursor.lastrowid
    
    def get_level_code(self, user_id: int, level_id: str) -> Optional[str]:
        """获取用户在某关卡保存的代码"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT code FROM code_snippets 
            WHERE user_id = ? AND level_id = ?
            ORDER BY created_at DESC LIMIT 1
        ''', (user_id, level_id))
        row = cursor.fetchone()
        if row:
            return row['code']
        return None


# 全局数据库实例
db = Database()
