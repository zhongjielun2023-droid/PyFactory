#!/usr/bin/env python3
"""realtime_test.py

测试代码：验证 `code_parser` 将用户输入代码解析并注入 `game_engine` 工厂的能力。
运行此脚本会使用内置的关卡模板作为输入，解析后在当前工厂中创建机器并打印结果。
"""

from code_parser import parser as code_parser, get_template
from game_engine import game_engine, Factory
from machines import create_machine

# 可选渲染依赖
try:
    import pygame
    from config import GRID_COLS, GRID_ROWS, GRID_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False


def apply_code_to_factory(code: str, mutate_global: bool = False):
    """解析代码并把机器应用到本地 Factory（默认不修改全局 game_engine）。

    如果 mutate_global=True 则会修改 `game_engine` 的当前工厂（仅用于手动交互测试）。
    """
    machines, connections, error, error_line = code_parser.parse(code)
    if error:
        print(f"解析错误: {error} (行 {error_line + 1})")
        return False

    if mutate_global:
        factory = game_engine.get_current_factory()
        factory.clear()
    else:
        factory = Factory()

    machine_objs = []
    for m in machines:
        machine = create_machine(m['type'], m['x'], m['y'])
        if not machine:
            print("无法创建机器：", m)
            continue

        if m['type'] == 'source':
            machine.shape_type = m.get('shape_type', 'circle')
            machine.color = m.get('color', 'white')
        elif m['type'] == 'painter':
            machine.target_color = m.get('target_color', 'red')
        elif m['type'] == 'rotator':
            machine.rotation_amount = m.get('rotation', 90)

        factory.add_machine(machine)
        machine_objs.append(machine)

    for f_idx, t_idx in connections:
        if f_idx < len(machine_objs) and t_idx < len(machine_objs):
            factory.connect(machine_objs[f_idx], machine_objs[t_idx])

    print(f"工厂: machines={len(factory.machines)}, connections={len(factory.connections)}")
    for i, m in enumerate(factory.machines):
        print(f"  {i}: {m.machine_type} @ ({m.x},{m.y})")

    return factory


def render_factory_to_png(code: str, out_path: str):
    """解析代码、构建工厂并在离屏 surface 上渲染为 PNG。"""
    if not PYGAME_AVAILABLE:
        raise RuntimeError("pygame 未安装")

    # 初始化 pygame（仅字体）
    pygame.init()
    pygame.font.init()

    # 生成工厂布局
    machines, connections, error, error_line = code_parser.parse(code)
    if error:
        raise RuntimeError(f"解析错误: {error} (行 {error_line + 1})")

    factory = Factory()

    machine_objs = []
    for m in machines:
        machine = create_machine(m['type'], m['x'], m['y'])
        if not machine:
            continue
        # 简单设置参数
        if m['type'] == 'source':
            machine.shape_type = m.get('shape_type', 'circle')
            machine.color = m.get('color', 'white')
        elif m['type'] == 'painter':
            machine.target_color = m.get('target_color', 'red')
        elif m['type'] == 'rotator':
            machine.rotation_amount = m.get('rotation', 90)

        factory.add_machine(machine)
        machine_objs.append(machine)

    for f_idx, t_idx in connections:
        if f_idx < len(machine_objs) and t_idx < len(machine_objs):
            factory.connect(machine_objs[f_idx], machine_objs[t_idx])

    # 创建离屏 surface，尽量与游戏主界面一致
    width = WINDOW_WIDTH
    height = WINDOW_HEIGHT
    surface = pygame.Surface((width, height))

    from config import COLORS

    # 背景
    surface.fill(COLORS['background'])

    # 网格偏移参考 main.GameScene_
    grid_x = 220
    grid_y = 60
    grid_w = GRID_COLS * GRID_SIZE
    grid_h = GRID_ROWS * GRID_SIZE

    # 绘制网格背景
    grid_rect = pygame.Rect(grid_x, grid_y, grid_w, grid_h)
    pygame.draw.rect(surface, (40, 40, 50), grid_rect)
    for i in range(GRID_COLS + 1):
        x = grid_x + i * GRID_SIZE
        pygame.draw.line(surface, (70, 70, 80), (x, grid_y), (x, grid_y + grid_h))
    for j in range(GRID_ROWS + 1):
        y = grid_y + j * GRID_SIZE
        pygame.draw.line(surface, (70, 70, 80), (grid_x, y), (grid_x + grid_w, y))

    # 绘制连接（先于机器）
    # 注意：在渲染时先绘制机器，再绘制连线，保证连线在上层可见
    for m in factory.machines:
        m.draw(surface, offset_x=grid_x, offset_y=grid_y)

    # 绘制连接（在机器之上）
    for conn in factory.connections:
        conn.draw(surface, offset_x=grid_x, offset_y=grid_y)

    # 保存为 PNG
    pygame.image.save(surface, out_path)
    pygame.quit()


def render_factory_instance_to_png(factory, out_path: str):
    """使用已构建的 Factory 实例渲染到 PNG。"""
    if not PYGAME_AVAILABLE:
        raise RuntimeError("pygame 未安装")
    import pygame
    from config import COLORS

    pygame.init()
    pygame.font.init()
    width = WINDOW_WIDTH
    height = WINDOW_HEIGHT
    surface = pygame.Surface((width, height))
    surface.fill(COLORS['background'])

    grid_x = 220
    grid_y = 60
    grid_w = GRID_COLS * GRID_SIZE
    grid_h = GRID_ROWS * GRID_SIZE

    # 网格
    grid_rect = pygame.Rect(grid_x, grid_y, grid_w, grid_h)
    pygame.draw.rect(surface, (40, 40, 50), grid_rect)
    for i in range(GRID_COLS + 1):
        x = grid_x + i * GRID_SIZE
        pygame.draw.line(surface, (70, 70, 80), (x, grid_y), (x, grid_y + grid_h))
    for j in range(GRID_ROWS + 1):
        y = grid_y + j * GRID_SIZE
        pygame.draw.line(surface, (70, 70, 80), (grid_x, y), (grid_x + grid_w, y))

    # 机器（捕获绘制异常以保证渲染继续）
    for m in factory.machines:
        try:
            m.draw(surface, offset_x=grid_x, offset_y=grid_y)
        except Exception:
            pass

    # 连接在上层
    for conn in factory.connections:
        try:
            conn.draw(surface, offset_x=grid_x, offset_y=grid_y)
        except Exception:
            pass

    pygame.image.save(surface, out_path)
    pygame.quit()


def run_factory_simulation(factory, steps: int = 60, dt: float = 0.1):
    """把工厂启动若干步，返回每个 OutputMachine 的收集统计。"""
    # 启动
    factory.start()
    for _ in range(steps):
        factory.update(dt)
    factory.stop()

    outputs = []
    for m in factory.machines:
        from machines import OutputMachine
        if isinstance(m, OutputMachine):
            outputs.append({'x': m.x, 'y': m.y, 'collected': len(m.collected), 'success': m.success_count})
    return outputs


def run_tests():
    tests = [
        ("basics_01", get_template('basics_01'), 2, 1),
        ("basics_02", get_template('basics_02'), 3, 2),
        ("basics_03", get_template('basics_03'), 3, 2),
    ]

    all_ok = True
    for name, code, exp_m, exp_c in tests:
        print(f"\n== 测试 {name} ==")
        factory = apply_code_to_factory(code)
        if not factory:
            all_ok = False
            continue
        m = len(factory.machines)
        c = len(factory.connections)
        if m != exp_m or c != exp_c:
            print(f"  失败: 期望 machines={exp_m}, connections={exp_c}，实际 machines={m}, connections={c}")
            all_ok = False
        else:
            print("  通过")

        # 如果可用，渲染为PNG
        if PYGAME_AVAILABLE:
            out_before = f"pyfactory_render_{name}_before.png"
            out_after = f"pyfactory_render_{name}_after.png"
            try:
                # 渲染初始布局
                render_factory_to_png(code, out_before)
                print(f"  已生成初始渲染图: {out_before}")

                # 运行仿真（本地 factory）并渲染结果
                local_factory = apply_code_to_factory(code)
                sim_outputs = run_factory_simulation(local_factory, steps=80, dt=0.1)
                render_factory_instance_to_png(local_factory, out_after)
                print(f"  已生成运行后渲染图: {out_after}")
                print(f"  输出统计: {sim_outputs}")
            except Exception as e:
                print(f"  渲染/仿真失败: {e}")
        else:
            print("  (跳过渲染，缺少 pygame；可运行 `pip install -r pyfactory/requirements.txt`)" )

    print('\n全部测试结果: ' + ("全部通过" if all_ok else "有测试未通过"))


if __name__ == '__main__':
    run_tests()

