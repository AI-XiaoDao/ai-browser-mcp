# -*- coding: utf-8 -*-
"""静态审计: "成功文案声称做了某事, 但分支里其实没有做" 的工具。

动机(真实案例): browser_antidetect_presets 传未知 preset 时, 没有任何分支命中,
却照样返回 "反检测预设 [x] 已部署 | 持久生效" —— 文案与事实不符。
同类风险还有: 分支里只有 `返回(命令成功("已设置…"))` 而没有任何动作调用。

方法(纯静态, 可与真机测试并行):
  1) 按 `方法名 == "X"` 切出分支;
  2) 在分支里找出**声称状态变更**的成功文案(含 已设置/已启用/已关闭/已启动/已停止/
     已清空/已删除/已提交/已应用/已部署/已执行/已更新/已写入 等词);
  3) 判断分支里是否存在"动作调用" —— 即对 参数JSON/响应构建/命令ID 之外的对象
     调用了变更类方法(.置/.设/.删/.清/.点击/.载入/.滚/.导航/.提交/.执行/.关闭/.开启…);
  4) 两者不匹配 -> 标记: 要么纯谎报, 要么把动作藏在未识别的调用里(需人工复核)。
另外单独列出"分支体只有 返回(分派_xxx(...))" 的委托型分支, 避免误报。
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
CLAIM = re.compile(r'(已设置|已启用|已开启|已关闭|已启动|已停止|已清空|已删除|已提交|'
                   r'已应用|已部署|已执行|已更新|已写入|已切换|已保存|已重置|已还原|已注入|已随机化)')
SUCCESS_MSG = re.compile(r'命令成功[^(]*\([^"]*"([^"]*)"')
# 变更类方法名片段
ACT_PAT = re.compile(r'\.(置|设|删|清|点击|载入|滚|导航|提交|执行|关闭|开启|启动|停止|'
                     r'写|保存|注入|注册|注销|锁定|解锁|添加|移除|随机化|伪装|虚拟|触发|选择|填写)')
IGNORE_OBJ = ('MCP_响应构建', 'MCP命令服务器.yyjson', '参数JSON', '响应构建')


def read(path):
    with io.open(path, encoding='utf-8-sig') as f:
        return f.read().splitlines()


def strip_code(s):
    i = s.find('//')
    return s[:i] if i != -1 else s


def main():
    rows = []
    for name in sorted(os.listdir(SRC)):
        if not name.endswith('.wsv') or '~vbak' in name:
            continue
        lines = read(os.path.join(SRC, name))
        cur, start = None, 0
        branches = []
        for i, ln in enumerate(lines):
            m = BRANCH.match(ln)
            if m:
                if cur:
                    branches.append((cur, start, i))
                cur, start = m.group(1), i
            elif re.match(r'^\s*方法\s+\S+\s*<', ln) and cur:
                branches.append((cur, start, i))
                cur = None
        if cur:
            branches.append((cur, start, len(lines)))

        for tool, a, b in branches:
            body = [strip_code(x) for x in lines[a:b]]
            text = '\n'.join(body)
            claims = []
            for x in body:
                for mm in SUCCESS_MSG.finditer(x):
                    if CLAIM.search(mm.group(1)):
                        claims.append(mm.group(1)[:60])
            if not claims:
                continue
            # 委托型分支: 只有 返回(分派_xxx(...))
            calls = [x.strip() for x in body if x.strip() and not x.strip().startswith('返回')]
            delegate = bool(re.search(r'返回\s*\(\s*分派_\w+', text)) and len(calls) <= 1
            acts = [x.strip() for x in body
                    if ACT_PAT.search(x) and not any(o in x for o in IGNORE_OBJ)]
            if delegate:
                continue
            if not acts:
                rows.append((name, tool, claims[0], '无双动作调用'))
            elif len(acts) == 0:
                rows.append((name, tool, claims[0], '可疑'))

    print('=== 声称状态变更但分支内**没有任何动作调用** (%d) ===' % len(rows))
    print('  说明: 这些分支的"已设置/已启动…"可能来自更下层的分派或被遗漏的调用方式,')
    print('        需逐个人工复核; 也可能是纯谎报(antidetect 案即此类)。')
    for f, tool, claim, why in rows:
        print('  %-26s %-40s %s' % (f, tool, claim))
    with io.open(os.path.join(HERE, 'report_successclaim.txt'), 'w',
                 encoding='utf-8') as fo:
        for f, tool, claim, why in rows:
            fo.write('%s\t%s\t%s\n' % (f, tool, claim))
    print('\n明细已写 report_successclaim.txt')
    return 0


if __name__ == '__main__':
    sys.exit(main())
