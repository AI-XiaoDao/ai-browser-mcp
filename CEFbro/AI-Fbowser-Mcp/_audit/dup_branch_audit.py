# -*- coding: utf-8 -*-
"""比对"同一工具在两处分派器里各有一份分支"的**内容差异**。

背景(已确认): 前缀路由器把 browser_reverse_* 直投 MCP_Server_Reverse.wsv,
把 browser_kernel_* 直投 MCP_Kernel.wsv, 其余走 Core。因此 Core 里如果也有
browser_reverse_* 的分支, 那份就是**永不执行的死代码** —— 但反过来, 如果作者/我
把修复写进了死代码那份, 修复就永远不生效。故必须逐工具比对两份内容。
"""
import io
import os
import re
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'src')
BRANCH = re.compile(r'^\s*(?:如果|否则)\s*\(\s*方法名\s*==\s*"([^"]+)"')


def branches(path):
    with io.open(path, encoding='utf-8-sig') as f:
        lines = f.read().splitlines()
    out = {}
    cur, start = None, 0
    for i, ln in enumerate(lines):
        m = BRANCH.match(ln)
        if m:
            if cur:
                out.setdefault(cur, []).append((start, lines[start:i]))
            cur, start = m.group(1), i
    if cur:
        out.setdefault(cur, []).append((start, lines[start:]))
    return out


def norm(body):
    """归一化: 去掉空行与纯注释, 便于比较"实质代码"是否一致。"""
    out = []
    for x in body:
        s = x.strip()
        if not s or s.startswith('//') or s.startswith('#'):
            continue
        out.append(s)
    return out


def main():
    files = ['MCP_Server_Core.wsv', 'MCP_Server_Reverse.wsv', 'MCP_Kernel.wsv']
    allb = {}
    for f in files:
        p = os.path.join(SRC, f)
        if os.path.exists(p):
            allb[f] = branches(p)

    # 找出在多个文件里都出现的工具分支
    seen = {}
    for f, d in allb.items():
        for tool in d:
            seen.setdefault(tool, []).append(f)

    dupes = {t: fs for t, fs in seen.items() if len(fs) > 1}
    print('=== 在多个分派器里重复出现的工具分支: %d 个 ===' % len(dupes))
    for t, fs in sorted(dupes.items()):
        print('  %-40s %s' % (t, ' / '.join(fs)))

    print()
    print('=== 逐工具比对实质代码(去空行/注释) ===')
    same = diff = 0
    for t, fs in sorted(dupes.items()):
        bodies = []
        for f in fs:
            # 取该文件里该工具的第一处分支
            bodies.append((f, norm(allb[f][t][0][1])))
        base_f, base = bodies[0]
        for f, b in bodies[1:]:
            if b == base:
                same += 1
                print('  [一致] %-38s %s == %s (%d 行)' % (t, base_f, f, len(base)))
            else:
                diff += 1
                print('  [!! 不一致] %-34s %s vs %s' % (t, base_f, f))
                # 打印差异行, 便于定位
                sb, sd = set(base), set(b)
                only_base = [x for x in base if x not in sd][:6]
                only_other = [x for x in b if x not in sb][:6]
                for x in only_base:
                    print('       只在 %s: %s' % (base_f, x[:110]))
                for x in only_other:
                    print('       只在 %s: %s' % (f, x[:110]))
    print()
    print('一致 %d 组, 不一致 %d 组' % (same, diff))
    print('注: 路由器按前缀直投 -> Core 里的 browser_reverse_* 分支为**死代码**;')
    print('    若差异出现在那份死代码里, 说明有修复写错了地方(永不生效)。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
