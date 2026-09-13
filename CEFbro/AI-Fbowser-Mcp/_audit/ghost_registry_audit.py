# -*- coding: utf-8 -*-
"""核对"幽灵注册": 命令注册表里的名字 vs 真正暴露给 AI 的工具名, 双向比对。

目标 C 线说"16 个有号无实现 -> 补齐或删除注册项"。上一轮我还发现**反向**现象:
browser_create_tab / browser_task_runner_post **可被直接调用**(有实现) 却**不在工具清单**里。

本脚本做三向核对:
  ① 命令注册表(置整数值) - 有号
  ② 添加工具JSON - 真正暴露给 AI 的
  ③ 派发分支(否则 方法名 == "x") - 有实现
输出: 
  · 幽灵注册(注册了但没暴露) 
  · 反向幽灵(有实现却没暴露)
  · 注册了但没有派发分支的(真·有号无实现)
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
FILES = ['MCP_Server.wsv', 'MCP_Server_Core.wsv', 'MCP_Server_Reverse.wsv',
         'MCP_Server_VIP.wsv', 'MCP_Server_System.wsv', 'MCP_Server_Form.wsv',
         'MCP_Server_Workflow.wsv', 'MCP_Kernel.wsv', 'MCP_Server_HTTP.wsv',
         'MCP_BrowserEvents.wsv', 'MCP_Callbacks.wsv', 'MCP_ResponseBuilders.wsv',
         'MCP_Server_Stdio.wsv', 'MCP_Server_Utils.wsv', 'MCP_Constants.wsv', 'main.wsv']


def read(fn):
    p = os.path.join(SRC, fn)
    if not os.path.exists(p):
        return ''
    return io.open(p, encoding='utf-8', errors='replace').read()


def norm(n):
    """把别名形式归一到下划线形式。

    注册表里同一个工具常有**两种写法**: `browser.create` 与 `browser_create`
    (项目在分派入口就有 `子文本替换 (方法名, "browser.", "browser_")` 做别名归一)。
    第一版没归一, 于是把 260 个"带点别名"误报成幽灵注册 —— 差点得出完全错误的结论。
    """
    n = n.strip()
    if n.startswith('browser.'):
        n = 'browser_' + n[len('browser.'):]
    return n.strip('.')


def main():
    reg, exposed, branch = set(), set(), set()
    for fn in FILES:
        t = read(fn)
        reg |= {norm(x) for x in re.findall(r'命令注册表\.置整数值 \(\s*"([^"]+)"', t)}
        exposed |= {norm(x) for x in re.findall(r'添加工具JSON \(\s*"([^"]+)"', t)}
        # ★ 派发**不止一种写法**: 除 `否则 (方法名 == "x")` 外, 还有成组的
        #   `如果 (规范名 == "a" || 规范名 == "b" || ...)`(填表/工作流等族就是这种)。
        #   第一版只匹配 `方法名 ==`, 于是把 browser_fill_click 这类**明明有实现**的工具
        #   误报成"有号无实现" —— 连同早期那份"16 个幽灵注册"的结论也属同一误报。
        #   教训: 静态正则判断"有没有实现"很脆弱; 判断"能不能用"应当以**行为**为准(台账调用)。
        for var in ('方法名', '规范名'):
            branch |= {norm(x) for x in
                       re.findall(r'(?:否则|如果) \(' + var + r' == "([^"]+)"\)', t)}
            branch |= {norm(x) for x in
                       re.findall(var + r' == "([^"]+)"', t)}
    reg.discard('')
    exposed.discard('')
    branch.discard('')
    print("命令注册表条目(归一后) = %d ; 暴露工具 = %d ; 有派发分支 = %d"
          % (len(reg), len(exposed), len(branch)))

    ghost = sorted(reg - exposed)
    rev_ghost = sorted((exposed | branch) - reg)
    # ③ 只报"**连别名都算不上**"的: 注册名本身、或加 browser_ 前缀后, 既没暴露也没派发分支。
    #    注册表里大量条目是**短别名**(back/close/evaluate/dom_query…), 它们不是工具,
    #    不加这一步就会把别名误报成"有号无实现"(第一版正是如此, 71 条里绝大多数是别名)。
    def resolvable(n):
        for cand in (n, 'browser_' + n, 'mcp_' + n, n.replace('.', '_')):
            if cand in exposed or cand in branch:
                return True
        return False
    no_branch = sorted(x for x in reg if not resolvable(x))
    exposed_no_branch = sorted(exposed - branch)

    def dump(title, items, limit=60):
        print("\n== %s (%d) ==" % (title, len(items)))
        for i, x in enumerate(items[:limit], 1):
            print("  %2d. %s" % (i, x))
        if len(items) > limit:
            print("  ... 还有 %d 个" % (len(items) - limit))

    dump("① 幽灵注册: 在命令注册表里但**没暴露**给 AI(添加工具JSON)", ghost)
    dump("② 反向幽灵: 有实现/已暴露但**不在命令注册表**", rev_ghost)
    dump("③ 真·有号无实现: 注册了但找不到派发分支", no_branch)
    dump("④ 暴露了但没有派发分支(工具会报未知命令?)", exposed_no_branch)
    return 0


if __name__ == '__main__':
    sys.exit(main())
