# -*- coding: utf-8 -*-
"""静态审计: **schema 声明为 required 的参数, 代码里到底有没有守卫**。

动机: 服务端**不校验** schema 的 required(它只是给客户端的元数据), 所以我们这一整轮
都在补"缺参守卫"。本脚本把剩余缺口**量化成一个可执行清单**, 避免靠印象决定下一步修谁。

方法(纯静态, 可与其他测试并行):
  1) 解析 添加工具JSON("工具", "描述", schema) 里 `"p1","p2"` 第三参(required 列表);
  2) 切出 `方法名 == "工具"` 分支;
  3) 在该分支里找该参数的守卫迹象:
       · 参数键存在 (参数JSON, "p")      <- 本会话新增的标准守卫
       · "p" == ""  / 删首尾空 (...p...) == ""
       · 取整数(...,"p") 后与 <=0 / <0 比较
       · 是否以 (...) / 寻找文本 等显式校验
  4) 把"声明 required 但**完全找不到守卫**"的参数列出来, 按风险词排序:
     动作/状态类(enable/disable/action/confirm/index/value/level/x/y/set...) 优先。
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

TOOL = re.compile(r'添加工具JSON\s*\(\s*"([^"]+)"\s*,')
BRANCH = re.compile(r'^\s*(?:如果|否则)\s*\(\s*方法名\s*==\s*"([^"]+)"')
PROP = re.compile(r'属性项JSON\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,')
# 危险词: 这些参数缺省会改变状态或触发动作
RISKY = ('enable', 'disable', 'action', 'confirm', 'index', 'value', 'level',
         'x', 'y', 'preset', 'type', 'count', 'timeout_ms', 'max_ms', 'mode',
         'amount', 'percent', 'delay', 'steps', 'fields', 'target')


def read(path):
    with io.open(path, encoding='utf-8-sig') as f:
        return f.read().splitlines()


def strip_code(s):
    i = s.find('//')
    return s[:i] if i != -1 else s


def scan_schemas():
    """工具 -> (required 列表, 全部参数声明)"""
    out = {}
    for ln in read(os.path.join(SRC, 'MCP_Server.wsv')):
        if '添加工具JSON' not in ln:
            continue
        m = TOOL.search(ln)
        if not m:
            continue
        tool = m.group(1)
        props = [(p.group(1), p.group(2)) for p in PROP.finditer(ln)]
        tail = ln[ln.rfind(')'):] if ')' in ln else ''
        # required 列表是 schema 辅助函数的最后一个字符串参数, 形如 "\"a\",\"b\""
        req = []
        for q in re.findall(r'"((?:\\"|\\\\|[^"])*)"\s*\)', ln):
            if '\\"' in q:
                req = [t for t in re.findall(r'\\"([^"\\]+)\\"', q)]
                break
        out[tool] = (req, props)
    return out


def guard_evidence(body, p):
    """该分支里是否存在针对参数 p 的守卫迹象。"""
    pats = [
        re.compile(r'参数键存在\s*\([^)]*"%s"' % re.escape(p)),
        re.compile(r'"%s"\s*\)\s*==\s*""' % re.escape(p)),
        re.compile(r'删首尾空\s*\([^)]*"%s"' % re.escape(p)),
        re.compile(r'"%s"\s*\)\s*(<=|<|>=|>)\s*[01]' % re.escape(p)),
        re.compile(r'是否以\s*\([^)]*"%s"' % re.escape(p)),
    ]
    return any(any(pat.search(x) for x in body) for pat in pats)


def main():
    schemas = scan_schemas()
    branches = {}
    for name in sorted(os.listdir(SRC)):
        if not name.endswith('.wsv') or '~vbak' in name:
            continue
        lines = [strip_code(x) for x in read(os.path.join(SRC, name))]
        cur, start = None, 0
        for i, ln in enumerate(lines):
            m = BRANCH.match(ln)
            if m:
                if cur:
                    branches.setdefault(cur, []).extend(lines[start:i])
                cur, start = m.group(1), i
        if cur:
            branches.setdefault(cur, []).extend(lines[start:])

    risky_hits, other_hits, missing_branch = [], [], []
    n_req = 0
    for tool, (req, _props) in sorted(schemas.items()):
        if not req:
            continue
        body = branches.get(tool)
        if body is None:
            missing_branch.append(tool)
            continue
        for p in req:
            n_req += 1
            if not guard_evidence(body, p):
                (risky_hits if p.lower() in RISKY else other_hits).append((tool, p))

    print('解析到 %d 个工具, 其中声明 required 参数共 %d 个' % (len(schemas), n_req))
    print('分支未匹配(可能是委托/别名) %d 个: %s'
          % (len(missing_branch), ', '.join(missing_branch[:8])))
    print()
    print('=== 高危: required 且属动作/状态类, 但分支内**找不到守卫** (%d) ==='
          % len(risky_hits))
    for tool, p in risky_hits:
        print('  %-44s %s' % (tool, p))
    print()
    print('=== 其余: required 但找不到守卫 (%d) ===' % len(other_hits))
    for tool, p in other_hits[:40]:
        print('  %-44s %s' % (tool, p))
    print()
    print('注: "找不到守卫" 不等于一定有缺陷 —— 有些工具在更下层(委托方法)里校验,')
    print('    或该参数缺省本身无害。本清单用于**排序下一步排查**, 不作为缺陷结论。')
    with io.open(os.path.join(HERE, 'report_required_gap.txt'), 'w',
                 encoding='utf-8') as f:
        for tool, p in risky_hits:
            f.write('HIGH\t%s\t%s\n' % (tool, p))
        for tool, p in other_hits:
            f.write('LOW\t%s\t%s\n' % (tool, p))
    print('\n明细已写 report_required_gap.txt')
    return 0


if __name__ == '__main__':
    sys.exit(main())
