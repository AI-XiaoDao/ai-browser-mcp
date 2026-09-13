# -*- coding: utf-8 -*-
r"""给 CDP执行JS并等待 装"子框架禁止原生回退"的守卫。

问题(实测+静态可证): CDP执行JS并等待 内部有 5 处 `原生执行JS并等待` 回退, 而该原生路径**只在主框架**
执行(其实现第一句就是 取安全主框架)。于是当调用方传了 执行上下文ID>0(子框架) 时, 一旦 CDP 无回执,
代码会**静默落到主框架**跑同一段 JS —— 那是"看起来成功、其实跑错框架"的错误答案。
(这也是本轮 browser_execute_js{frame_id} 实测出现超时/莫名值时的隐患点。)

本补丁:
  1) 新增 子框架原生回退 (JS代码, 最大等待毫秒, 执行上下文ID): 上下文>0 时直接返回 ""(表示"无回退可用"),
     否则原样转调 原生执行JS并等待 —— 上下文=0 的行为逐字不变;
  2) 把 CDP执行JS并等待 方法体内的 5 处回退调用全部改走它。

安全: 只在该方法行区间内替换, 断言命中恰好 5 处; 花括号净额不变。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
M_START = '    方法 CDP执行JS并等待 <公开 静态 类型 = 文本型 注释 = "通过CDP Runtime.evaluate执行JS并sync-wait取回结果, 绕过不稳定的CEF JS回调; CDP不可用时回退原生同步JS" @输出名 = "CDPExecuteJSAndWait" @强制输出 = 真>'
M_END = '    方法 CDP设置断点结果是否成功 <公开 静态 类型 = 逻辑型 @输出名 = "CDPSetBreakpointResultIsSuccess" @强制输出 = 真>'
HELPER_ANCHOR = '    方法 CDP执行JS并等待 <公开 静态 类型 = 文本型 注释'
OLD = '原生执行JS并等待 (JS代码, 最大等待毫秒)'
NEW = '子框架原生回退 (JS代码, 最大等待毫秒, 执行上下文ID)'

HELPER = '''    # 子框架求值时的"原生回退"闸门。
    # 约束: 原生路径(原生执行JS并等待)只在**主框架**执行; 调用方指定了执行上下文(子框架)时若还回退,
    # 就等于把同一段 JS 放到**错误的框架**里跑 —— 静默错误答案, 比直接失败更糟。故此处一律不放行,
    # 返回 ""(语义 = 无回退可用), 由上层报出明确错误。
    方法 子框架原生回退 <公开 静态 类型 = 文本型 @输出名 = "FrameNativeFallback" @强制输出 = 真>
    参数 JS代码 <类型 = 文本型 @输出名 = "JSCode">
    参数 最大等待毫秒 <类型 = 整数 @默认值 = 10000 @输出名 = "MaxWaitMs">
    参数 执行上下文ID <类型 = 整数 @默认值 = 0 @输出名 = "ExecutionContextId">
    {
        如果 (执行上下文ID > 0)
        {
            返回 ("")
        }
        返回 (原生执行JS并等待 (JS代码, 最大等待毫秒))
    }

'''


def depth_delta(lines):
    bal = 0
    for ln in lines:
        if ln.lstrip().startswith('@'):
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
                elif c == '{':
                    bal += 1
                elif c == '}':
                    bal -= 1
            k += 1
    return bal


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    assert b'\r\n' not in raw, 'CRLF'
    lines = raw.decode('utf-8').split('\n')

    ms = [i for i, l in enumerate(lines) if l == M_START]
    me = [i for i, l in enumerate(lines) if l == M_END]
    ha = [i for i, l in enumerate(lines) if l.startswith(HELPER_ANCHOR)]
    assert len(ms) == 1 and len(me) == 1 and len(ha) == 1, '锚点: %d/%d/%d' % (len(ms), len(me), len(ha))
    s, e, h = ms[0], me[0], ha[0]
    assert s < e and s == h, '顺序异常 s=%d e=%d h=%d' % (s, e, h)
    assert not any('子框架原生回退' in l for l in lines), '已存在同名方法/替换'

    hit = 0
    for k in range(s, e):
        if OLD in lines[k]:
            lines[k] = lines[k].replace(OLD, NEW)
            hit += 1
    assert hit == 5, '方法体内回退调用命中 %d 处(期望 5)' % hit
    # 区间外不得有残留调用
    outside = [i + 1 for i, l in enumerate(lines) if OLD in l and not (s <= i < e)]
    assert not outside, '区间外仍有旧调用: %s' % outside

    helper_lines = HELPER.rstrip('\n').split('\n')
    assert depth_delta(helper_lines) == 0, 'helper 不平衡: %d' % depth_delta(helper_lines)
    before = depth_delta(lines)
    out = lines[:s] + helper_lines + lines[s:]
    assert depth_delta(out) == before == 0, '整文件净额 %d -> %d' % (before, depth_delta(out))

    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out))
        print('已写入 %s (行数 %d -> %d)' % (TARGET, len(lines), len(out)))
    else:
        print('[dry-run] 替换 %d 处回退调用; 在 %d 行前插入 helper %d 行; 行数 %d -> %d'
              % (hit, s + 1, len(helper_lines), len(lines), len(out)))
        for k in range(s, e):
            if NEW in out[k + len(helper_lines)]:
                print('   %6d | %s' % (k + 1, out[k + len(helper_lines)].strip()[:110]))


main()
