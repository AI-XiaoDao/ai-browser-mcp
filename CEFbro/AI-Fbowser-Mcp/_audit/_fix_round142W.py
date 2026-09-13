# -*- coding: utf-8 -*-
r"""修 node_edit 分支的定稿形态(按**行范围**重建, 不再靠多行锚点):
  · 删掉已无必要的 DOM.enable + 全树预检(实测预检本身会挂住并拖死通道);
  · 删掉过期的重复注释;
  · 用一条语法正确的 `返回 (MCP_响应构建.命令失败 (命令ID, ...))` 作为可行动路由。

用法: py -3 _audit\_fix_round142W.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIP = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')
APPLY = '--apply' in sys.argv

BLOCK = '''            // ★★★ 定稿(第142轮四组对照实测): 引用 nodeId 的 DOM 编辑命令在本项目里**只能由外层 `browser_cdp_call`
            //   那条通道提交** —— 分支内三种等待方式(`执行CDP并同步等待` / 「派发+同步等待」最小原语 / 两段式回执)
            //   **全部**会让命令挂住并把整条 CDP 通道拖死(之后每条 CDP 命令 30s 才靠原生回退返回, 需重启恢复);
            //   而 `browser_cdp_call {method:DOM.removeAttribute|DOM.removeNode}` 实测全程 0.03s 且页面侧回读一致。
            //   故本工具**不自己提交**任何 DOM 命令, 而是返回**可行动**的等价调用 —— 宁可不做, 也不把会话搞残。
            //   另实测: 连**只读的全树枚举**(DOM.getDocument depth=-1 + pierce=true)在含影子树的页面上也会挂住并拖死通道,
            //   故枚举请用**有界 depth**(如 ≤8)。
            返回 (MCP_响应构建.命令失败 (命令ID, "本机限制: 节点编辑必须经 `browser_cdp_call` 提交 | 实测: 在工具分支内提交引用 nodeId 的 DOM 命令会挂住并**打死本会话的 CDP 命令通道**(之后所有 CDP 类工具 30s 才返回, 需重启进程恢复); 而经外层 CDP 通道提交同一命令正常 | 请改用(实测可用): browser_cdp_call method=\\"" + neCdp方法 + "\\" params=" + neParams + " | 其它替代: browser_execute_js 直接改 DOM(el.removeAttribute / el.remove / el.setAttribute) | 只读枚举仍可用: browser_vip_dom_get_document(pierce=true 可见影子树; 含影子树的页面请用有界 depth 如 8)"))'''


def main():
    lines = io.open(VIP, encoding='utf-8', newline='').read().split('\n')
    # 起点: 含 "★ 隐式前置(实测): 与 get_document 同理" 的注释行
    i0 = None
    for i, l in enumerate(lines):
        if '★ 隐式前置(实测): 与 get_document 同理' in l:
            i0 = i
            break
    assert i0 is not None, '未找到起点(DOM.enable 注释)'
    # 终点: 含 "本机限制: 节点编辑必须经" 的那一行
    i1 = None
    for j in range(i0, len(lines)):
        if '本机限制: 节点编辑必须经' in lines[j]:
            i1 = j
            break
    assert i1 is not None, '未找到终点(路由返回行)'
    print('· 将重建第 %d~%d 行(共 %d 行)' % (i0 + 1, i1 + 1, i1 - i0 + 1))
    out = lines[:i0] + BLOCK.split('\n') + lines[i1 + 1:]
    txt = '\n'.join(out)
    print('MCP_Server_VIP.wsv: 行数 %d -> %d' % (len(lines), len(out)))
    if APPLY:
        io.open(VIP, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
