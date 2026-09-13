# -*- coding: utf-8 -*-
r"""加两个启动期能力字段 + 配置解析: dpi_aware / v8_max_stack_mb(默认都不改变现有行为)。

- `dpi_aware`(默认假): 为真时启动期调 FBrowser_设置程序DPI模式(-4 按显示器感知V2) —— 进程级, 必须在 FBrowser_初始化 前。
  风险已在注释写明: HiDPI 下窗口 1000x800 按物理像素解释, CSS 视口会变小, 坐标类工具观测值随之变化。
- `v8_max_stack_mb`(默认 0=内核默认): >0 时启动期调 FBrowser_初始化_设置V8环境默认堆栈大小(0, N) —— 只放宽上限。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

FIELD_ANCHOR = '    变量 命令行对象可用 <公开 静态 类型 = 逻辑型 值 = 假'
FIELD_NEW = [
    '    变量 启动DPI感知模式 <公开 静态 类型 = 逻辑型 值 = 假 注释 = "mcp_config.json dpi_aware: 为真时启动期调用 FBrowser_设置程序DPI模式(按显示器感知V2) —— 进程级, 必须在 FBrowser_初始化 前; 副作用: HiDPI 下窗口按物理像素解释, CSS 视口变小, 鼠标/坐标类工具的观测值会随之变化" @输出名 = "StartupDpiAware">',
    '    变量 V8堆栈上限MB <公开 静态 类型 = 整数 值 = 0 注释 = "mcp_config.json v8_max_stack_mb: >0 时启动期调用 FBrowser_初始化_设置V8环境默认堆栈大小(0, N), 只放宽 V8 堆栈上限(深递归逆向页面防渲染进程崩溃); 0 = 内核默认(不改动)" @输出名 = "StartupV8MaxStackMb">',
]

CFG_ANCHOR = '''        如果 (配置解析.取逻辑值 ("ignore_gpu_blocklist"))
        {
            启动开关_忽略GPU禁用清单 = 真
        }'''
CFG_ADD = CFG_ANCHOR + '''

        // ==== 启动期能力(非命令行开关): DPI 感知 / V8 堆栈上限 ====
        // 两者都是**进程级且必须在 FBrowser_初始化 之前**, 且默认值保证"不写配置就与改动前完全一致"。
        // 实测提醒: app_* 事件族在本机不入库(见报告 141 节), 故这些能力只能靠工具面自查(如 browser_get_run_style)。
        如果 (配置解析.取逻辑值 ("dpi_aware"))
        {
            启动DPI感知模式 = 真
        }
        变量 配置V8堆栈 <类型 = 整数>
        配置V8堆栈 = 配置解析.取整数 ("v8_max_stack_mb")
        如果 (配置V8堆栈 > 0 && 配置V8堆栈 <= 4096)
        {
            V8堆栈上限MB = 配置V8堆栈
        }'''


def find_block(lines, block):
    n = len(block)
    return [i for i in range(len(lines) - n + 1)
            if [l.strip() for l in lines[i:i + n]] == [x.strip() for x in block]]


def nets(lines):
    p = b = 0
    for ln in lines:
        st = ln.lstrip()
        if st.startswith('@') or st.startswith('//') or st.startswith('#'):
            continue
        k = 0
        in_str = False
        while k < len(ln):
            c = ln[k]
            if in_str:
                if c == '\\':
                    k += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == '(':
                    p += 1
                elif c == ')':
                    p -= 1
                elif c == '{':
                    b += 1
                elif c == '}':
                    b -= 1
            k += 1
    return p, b


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf')
    assert b'\r\n' not in raw
    lines = raw.decode('utf-8').split('\n')
    assert not any('启动DPI感知模式' in l for l in lines), '已应用过'
    p0, b0 = nets(lines)

    h = [i for i, l in enumerate(lines) if l.startswith(FIELD_ANCHOR)]
    assert len(h) == 1, '字段锚点 %d' % len(h)
    lines = lines[:h[0]] + FIELD_NEW + lines[h[0]:]

    h2 = find_block(lines, CFG_ANCHOR.split('\n'))
    assert len(h2) == 1, '配置锚点 %d' % len(h2)
    i = h2[0]
    lines = lines[:i] + CFG_ADD.split('\n') + lines[i + len(CFG_ANCHOR.split('\n')):]

    p1, b1 = nets(lines)
    assert (p1, b1) == (p0, b0), '净额 %s/%s -> %s/%s' % (p0, b0, p1, b1)
    print('字段锚点 @%d (+%d 行); 配置锚点 @%d (+%d 行); 净额不变'
          % (h[0] + 1, len(FIELD_NEW), h2[0] + 1, len(CFG_ADD.split('\n')) - len(CFG_ANCHOR.split('\n'))))
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines))
        print('已写入 %s' % TARGET)
    else:
        print('[dry-run] 未落盘')


main()
