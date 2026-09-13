# -*- coding: utf-8 -*-
"""系统性交叉核对: src 里对**类库方法**的每一次调用, 其实参个数是否落在类库声明的参数个数范围内?

动机: 本项目已发现的两个"100% 失效且被假成功掩盖"的缺陷, 都属于"调用方对接口的假设与实际不符"
(Network.requestId 格式假设、Debugger.setBreakpointOnFunctionCall 参数名写反)。
**参数个数不符**是同一类缺陷里最容易静态发现的一种: 少传/多传实参必然编译不过或运行必错。

口径(务实且可解释):
  · 类库侧: 解析 `类 X` / `方法 Y` / 逐条 `参数 Z <...>`; `@默认值 = ...` 的参数视为可选。
    同名方法可能重载 -> 收集**全部** (最少参数个数, 最多参数个数) 区间, 取并集。
  · src 侧: 找 `接收者.方法名 (` 与 裸 `方法名 (`; 用括号深度 + 字符串状态扫描, 数**顶层逗号**得到实参个数。
  · 只在"实参个数不属于该方法名的**任何**已知区间"且"方法名确实在类库里存在"时报警(候选)。
  · 已知局限: 不同类可能有同名不同参数个数的方法 -> 会有误报, 故一律标为**候选**, 逐条人工核。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"

if not os.path.isdir(LIB):
    print('!! 类库目录不存在: %s' % LIB)
    sys.exit(1)


# ---------------- 1) 类库侧: 方法名 -> 允许的参数个数集合 ----------------
def parse_lib():
    ranges = {}       # 方法名 -> set((min,max))
    owners = {}       # 方法名 -> set(类名)
    files = 0
    for fn in sorted(os.listdir(LIB)):
        p = os.path.join(LIB, fn)
        if not os.path.isfile(p):
            continue
        files += 1
        try:
            lines = io.open(p, encoding='utf-8', errors='replace').read().split('\n')
        except Exception as ex:
            print('!! 读取失败 %s: %s' % (p, ex))
            continue
        cur_cls = ''
        i = 0
        while i < len(lines):
            s = lines[i].strip()
            m = re.match(r'类\s+(\S+)', s)
            if m:
                cur_cls = m.group(1)
            m = re.match(r'方法\s+(\S+)', s)
            if m:
                name = m.group(1)
                # 往后收集紧随的 参数 行
                nreq = 0
                nopt = 0
                j = i + 1
                while j < len(lines):
                    t = lines[j].strip()
                    if t.startswith('参数'):
                        if '@默认值' in t:
                            nopt += 1
                        else:
                            nreq += 1
                        j += 1
                        continue
                    if t == '' or t.startswith('//') or t.startswith('#'):
                        j += 1
                        continue
                    break
                lo, hi = nreq, nreq + nopt
                ranges.setdefault(name, set()).add((lo, hi))
                owners.setdefault(name, set()).add(cur_cls)
                i = j
                continue
            i += 1
    return ranges, owners, files


# ---------------- 2) src 侧: 调用点与实参个数 ----------------
CALL_RE = re.compile(r'([\u4e00-\u9fffA-Za-z_][\u4e00-\u9fffA-Za-z0-9_]*)'      # 方法名
                     r'\s*\(')


def count_args(text, open_idx):
    """open_idx 指向 '('; 返回 (实参个数, 是否成功闭合)。处理嵌套括号与 '...' / "..." 字符串。"""
    depth = 0
    in_str = None
    args = 0
    seen_content = False
    i = open_idx
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in ('"', "'"):
            in_str = ch
            seen_content = True
            i += 1
            continue
        if ch == '(':
            depth += 1
            if depth == 1:
                pass
            i += 1
            continue
        if ch == ')':
            depth -= 1
            if depth == 0:
                return (0 if not seen_content else args + 1), True
            i += 1
            continue
        if ch == ',' and depth == 1:
            args += 1
            i += 1
            continue
        if not ch.isspace():
            seen_content = True
        i += 1
    return args, False


def main():
    ranges, owners, nfiles = parse_lib()
    print('类库文件 %d 个, 方法名 %d 个' % (nfiles, len(ranges)))

    suspect = []
    checked = 0
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith('.wsv') or '~vbak' in fn:
            continue
        text = io.open(os.path.join(SRC, fn), encoding='utf-8').read()
        # 只在"定义行/注释行"之外找调用: 用简单启发式跳过 方法/类 声明行
        for m in CALL_RE.finditer(text):
            name = m.group(1)
            if name not in ranges:
                continue
            # 跳过方法/类定义行
            line_start = text.rfind('\n', 0, m.start()) + 1
            line = text[line_start:text.find('\n', m.start()) if text.find('\n', m.start()) != -1 else len(text)]
            ls = line.strip()
            if ls.startswith('方法 ') or ls.startswith('类 ') or ls.startswith('//') \
                    or ls.startswith('#') or ls.startswith('参数 '):
                continue
            # 跳过"方法声明中的参数默认值"之类
            nargs, closed = count_args(text, m.end() - 1)
            if not closed:
                continue
            checked += 1
            allow = ranges[name]
            if not any(lo <= nargs <= hi for lo, hi in allow):
                ln = text[:m.start()].count('\n') + 1
                suspect.append((fn, ln, name, nargs, sorted(allow),
                                sorted(owners.get(name, set()))[:3], ls[:120]))

    print('核对调用点 %d 个' % checked)
    print('\n== 候选: 实参个数不在类库任何已知区间 (%d 个) ==' % len(suspect))
    for fn, ln, name, nargs, allow, own, txt in suspect:
        print('   %-24s:%-6d %-22s 实参=%d 类库允许=%s 类=%s'
              % (fn, ln, name, nargs, allow, own))
        print('        %s' % txt)


main()
