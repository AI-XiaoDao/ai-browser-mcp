# -*- coding: utf-8 -*-
r"""第142轮补丁 V(修正版): ①把节点编辑的提交块换成"可行动路由" ②修描述里的 ASCII 引号(编译报错 11818)。

上一版 V1 锚点没命中(U 补丁后的实际文本是"派发+同步等待"那一版), 描述里又误用了 ASCII 引号。
本脚本按**行范围**精确替换提交块, 并把描述里的 `"派发+同步等待"` 改成 `「派发+同步等待」`。

用法: py -3 _audit\_apply_round142V2.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIP = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

ROUTER = '''            // ★★★ 定稿(第142轮四组对照实测): 引用 nodeId 的 DOM 编辑命令在本项目里**只能由外层 `browser_cdp_call`
            //   那条通道提交** —— 分支内三种等待方式(`执行CDP并同步等待` / 「派发+同步等待」最小原语 / 两段式回执)
            //   **全部**会让命令挂住并把整条 CDP 通道拖死(之后每条 CDP 命令 30s 才靠原生回退返回, 需重启恢复);
            //   而 `browser_cdp_call {method:DOM.removeAttribute|DOM.removeNode}` 实测全程 0.03s 且页面侧回读一致。
            //   故本工具**不自己提交**破坏性命令(那不是省事, 是把会话搞残), 而是返回**可行动**的等价调用。
            返回 (MCP_响应构建.命令失败 (命令ID, "本机限制: 节点编辑必须经 `browser_cdp_call` 提交 | 实测: 在工具分支内提交引用 nodeId 的 DOM 命令会挂住并**打死本会话的 CDP 命令通道**(之后所有 CDP 类工具 30s 才返回, 需重启进程恢复); 而外层 CDP 通道提交同一命令正常 | 请改用(实测可用): browser_cdp_call method=\\"" + neCdp方法 + "\\" params=" + neParams + " | 其它替代: browser_execute_js 直接改 DOM(el.removeAttribute / el.remove / el.setAttribute) | 只读枚举仍可用: browser_vip_dom_get_document(pierce=true 可见影子树)"))'''

DESC_FIX_OLD = '''(`执行CDP并同步等待` / "派发+同步等待" / 两段式回执)'''
DESC_FIX_NEW = '''(`执行CDP并同步等待` / 「派发+同步等待」 / 两段式回执)'''


def main():
    txt = io.open(VIP, encoding='utf-8', newline='').read()
    lines = txt.split('\n')
    # 定位提交块: 从含 "变量 ne结果 <类型 = 文本型>" 起, 到该分支的 `返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\"success\":true,\"action\":\"` 行为止
    i0 = None
    for i, l in enumerate(lines):
        if l.strip().startswith('变量 ne结果 <类型 = 文本型>'):
            i0 = i
            break
    assert i0 is not None, '未找到提交块起点'
    i1 = None
    for j in range(i0, len(lines)):
        if '命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\"' in lines[j]:
            i1 = j
            break
    assert i1 is not None, '未找到提交块终点'
    out = lines[:i0] + ROUTER.split('\n') + lines[i1 + 1:]
    print('· 已把节点编辑提交块(%d 行)替换为可行动路由' % (i1 - i0 + 1))
    vip_txt = '\n'.join(out)
    if APPLY:
        io.open(VIP, 'w', encoding='utf-8', newline='').write(vip_txt)
        print('   ✔ 已写入 MCP_Server_VIP.wsv')

    srv = io.open(SERVER, encoding='utf-8', newline='').read()
    if DESC_FIX_OLD in srv:
        srv = srv.replace(DESC_FIX_OLD, DESC_FIX_NEW, 1)
        print('· 已把描述里的 ASCII 引号改为「」')
        if APPLY:
            io.open(SERVER, 'w', encoding='utf-8', newline='').write(srv)
            print('   ✔ 已写入 MCP_Server.wsv')
    else:
        print('· 描述里未找到 ASCII 引号(可能已修)')


if __name__ == '__main__':
    main()
