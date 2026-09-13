# -*- coding: utf-8 -*-
r"""第142轮补丁 R: CDP DOM 族先 `DOM.enable` —— 实测这正是一条**缺失的隐式前置**。

## 实测(两次独立运行, 同一实例)
| 调用序列 | 结果 |
|---|---|
| 工具路径 `get_document` → `get_document` → `remove_attr` → 回读 | **第 3 步之后就全死**: 第 2 次 getDocument 拿不到结果, `remove_attr` 15s 超时, 收尾 `execute_js` 35s |
| **先 `DOM.enable`**, 再同样的工具路径(本次实测) | get_document ×2 各 0.03s, **每次之后 `execute_js` 仍 0.02~0.03s** |

⇒ 与本项目此前两例同源(`Page.addScriptToEvaluateOnNewDocument` 需先 `Page.enable`;
`Runtime.compileScript` 需先 `Runtime.enable`): **CEF 的 CDP 域未启用时, 首次命令能过, 但节点映射没维护,
后续引用 nodeId 的命令会挂住并把整条通道拖死**。故按项目既有"零前置 + auto_prepared 如实上报"惯例补齐。

用法: py -3 _audit\_apply_round142R.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIP = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')
APPLY = '--apply' in sys.argv

ENSURE = '''                // ★ 隐式前置(实测): 必须先 `DOM.enable` —— 域未启用时首条命令能过, 但 CEF 不维护节点映射,
                //   之后引用 nodeId 的命令会挂住, 并把整条 CDP 通道拖死(实测: 第 2 次 getDocument 起全部超时,
                //   收尾 execute_js 35s)。与 Page.enable / Runtime.enable 同一类前置, 故此处补齐并经 auto_prepared 上报。
                变量 dDom域 <类型 = 文本型>
                dDom域 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_den", "DOM.enable", "{}", 5000)
                如果 (MCP命令服务器.CDP同步结果是否成功 (dDom域) == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "DOM.enable 失败, DOM 族无法安全使用: " + MCP命令服务器.取CDP同步结果错误 (dDom域) + " | 可显式改用 via:library(类库开发者DOM 路线; **实测会让本会话 CDP 命令通道失效**)"))
                }
                MCP_响应构建.记录自动补域 ("DOM")
'''

GET_OLD = '''                变量 dParams <类型 = 文本型>
                dParams = "{\\"depth\\":" + 到文本 (dDepth0) + ",\\"pierce\\":" + 选择 (dPierce0, "true", "false") + "}"'''
GET_NEW = ENSURE + '''                变量 dParams <类型 = 文本型>
                dParams = "{\\"depth\\":" + 到文本 (dDepth0) + ",\\"pierce\\":" + 选择 (dPierce0, "true", "false") + "}"'''

NE_OLD = '''            变量 ne结果 <类型 = 文本型>
            ne结果 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_ed", neCdp方法, neParams, 15000)'''
NE_NEW = '''            // ★ 隐式前置(实测): 与 get_document 同理, 节点类命令引用 nodeId, 必须先 DOM.enable(否则会挂住并拖死通道)
            变量 neDom域 <类型 = 文本型>
            neDom域 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_neden", "DOM.enable", "{}", 5000)
            如果 (MCP命令服务器.CDP同步结果是否成功 (neDom域) == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "DOM.enable 失败, 节点编辑无法安全执行: " + MCP命令服务器.取CDP同步结果错误 (neDom域)))
            }
            MCP_响应构建.记录自动补域 ("DOM")
            变量 ne结果 <类型 = 文本型>
            ne结果 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_ed", neCdp方法, neParams, 15000)'''

EDITS = [(VIP, 'R1 get_document 先 DOM.enable', GET_OLD, GET_NEW),
         (VIP, 'R2 node_edit 先 DOM.enable', NE_OLD, NE_NEW)]


def main():
    print('== 第142轮补丁 R (%s) ==' % ('应用' if APPLY else '预演'))
    txt = io.open(VIP, encoding='utf-8', newline='').read()
    for path, tag, old, new in EDITS:
        if old not in txt:
            print('   · %-34s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 命中 %d 次' % (tag, txt.count(old))
        txt = txt.replace(old, new, 1)
        print('   · %s' % tag)
    print('MCP_Server_VIP.wsv: 行数 %d' % len(txt.split('\n')))
    if APPLY:
        io.open(VIP, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
