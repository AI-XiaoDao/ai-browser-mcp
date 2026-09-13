# -*- coding: utf-8 -*-
r"""第142轮补丁 V(定稿): 节点编辑在本机**只能经 `browser_cdp_call` 走** ⇒ 本工具改为**带守卫的路由器**。

## 实测(四组对照, 均在同一类干净实例上)
| 提交方式 | 结果 |
|---|---|
| 外层 `browser_cdp_call {method:DOM.removeAttribute / DOM.removeNode}` | **全通**: removeAttribute 后页面侧回读 `null`; removeNode 后 `getElementById===null`; **全程 `execute_js` 0.03s** |
| 分支内 `执行CDP并同步等待`(自带删旧结果/预算压缩/超时自救/补域) | 挂住 15s, 之后所有 CDP 命令 30s ⇒ **通道被打死** |
| 分支内 `执行CDP命令_带参数` + `同步等待异步任务`(最小原语) | 同上(仍被打死) |
| 分支内两段式(派发 + 回 task_id, 由 mcp_result 取) | 同上(仍被打死) |

⇒ 结论: 在本项目里, 引用 nodeId 的 DOM 编辑命令**只能由外层 `browser_cdp_call` 那条通道提交**。
    分支内无论怎么等都会把 CDP 通道拖死。**绝不能**让工具自己去撞这个坑(那正是"用一次就把会话搞残")。

## 定稿做法(诚实 + 可行动, 不再毒化会话)
`browser_vip_dom_node_edit` 保留全部参数与守卫, 但**不自己提交**:
· 先做只读 shadow-root 预检(实测: 含影子树的页面更危险);
· 然后返回**可行动失败**: 给出该动作对应的 `browser_cdp_call` 完整调用(实测可用), 并说明为什么不能由本工具提交;
· `discard_search` 仍由本工具执行(它不引用 nodeId, 实测安全)。

用法: py -3 _audit\_apply_round142V.py [--apply]
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

OLD = '''            // ★★ 实测(本轮三组对照): 引用 nodeId 的 DOM 命令在本项目里**只有"派发即返回回执、由调用方另取结果"的
            //   两段式**才稳 —— 分支内 `执行CDP并同步等待` 会挂住 15s 并把整条 CDP 通道拖死(之后每条命令 30s);
            //   换成"派发 + 同步等待"最小原语仍然失败; 而 `browser_cdp_call` 那条路(getDocument/removeAttribute/
            //   removeNode 连做)全程 0.03s 且页面侧回读一致。故这里改成同构两段式: 立即回 task_id, 用 mcp_result 取结果。
            变量 ne任务ID <类型 = 文本型>
            ne任务ID = 命令ID + "_ed"
            MCP命令服务器.执行CDP命令_带参数 (ne任务ID, neCdp方法, neParams)
            返回 (MCP命令服务器.命令成功_异步 (命令ID, ne任务ID, "已提交 " + neCdp方法 + " (action=" + neAction + ", node_id=" + 到文本 (neNodeID) + ") | 用 mcp_result {request_id:\\"" + ne任务ID + "\\"} 取提交回执 | 生效后请回读核对: 重新 browser_vip_dom_get_document 或页面侧 browser_execute_js 断言 | 注: 本机实测节点类命令只能走这条两段式(同步等待会把 CDP 通道拖死), 与 browser_cdp_call 同构"))'''

NEW = '''            // ★★★ 定稿(第142轮四组对照实测): 引用 nodeId 的 DOM 编辑命令在本项目里**只能由外层 `browser_cdp_call`
            //   那条通道提交** —— 分支内三种等待方式(`执行CDP并同步等待` / "派发+同步等待"最小原语 / 两段式回执)
            //   **全部**会让这条命令挂住并把整条 CDP 通道拖死(之后每条 CDP 命令 30s 才靠原生回退返回, 需重启恢复);
            //   而外层 `browser_cdp_call {method:DOM.removeAttribute|DOM.removeNode}` 实测全程 0.03s 且页面侧回读一致。
            //   故本工具**不自己提交**破坏性命令(重复造轮子换来的是把会话搞残), 而是返回**可行动**的等价调用。
            返回 (MCP_响应构建.命令失败 (命令ID, "本机限制: 节点编辑必须经 `browser_cdp_call` 提交 | 实测: 在工具分支内提交引用 nodeId 的 DOM 命令会挂住并**打死本会话的 CDP 命令通道**(之后所有 CDP 类工具 30s 才返回, 需重启进程恢复); 而外层 CDP 通道提交同一命令正常 | 请改用(实测可用): browser_cdp_call method=\\"" + neCdp方法 + "\\" params=" + neParams + " | 其它替代: browser_execute_js 直接改 DOM(el.removeAttribute(...) / el.remove() / el.setAttribute(...)) | 只读枚举仍可用: browser_vip_dom_get_document(pierce=true 可见影子树)"))'''

DESC_OLD = '''"DOM **节点编辑**(默认走 CDP DOM 域: 同步生效、不毒化 CDP 通道)'''
DESC_NEW = '''"DOM **节点编辑**(本机限制下的**可行动路由**: 返回等价的 `browser_cdp_call` 调用)'''

DESC_TAIL_OLD = '''**安全闸门(实测)**: 提交前先全树预检 shadow root —— 页面含影子树时本工具**直接拒绝**, 因为实测对这类页面提交引用 nodeId 的 DOM 命令会挂住(15s)并**打死本会话 CDP 命令通道**(之后所有 CDP 工具 30s 才返回, 需重启); 这类页面请改用 browser_execute_js 直接改 DOM | 实测说明: 普通页面走 CDP 时**同步生效**, 可直接用 browser_vip_dom_get_document 重新枚举或 browser_execute_js 回读核对; **DOM 变化后 nodeId 可能失效, 编辑前请重新枚举**'''
DESC_TAIL_NEW = '''**为什么本工具不自己提交(第142轮四组对照实测)**: 引用 nodeId 的 DOM 编辑命令在本项目里**只能由外层 `browser_cdp_call` 那条通道提交** —— 分支内三种等待方式(`执行CDP并同步等待` / "派发+同步等待" / 两段式回执)**全部**会把命令挂住并**打死本会话 CDP 命令通道**(之后每条 CDP 命令 30s, 需重启); 而 `browser_cdp_call {method:DOM.removeAttribute|DOM.removeNode}` 实测 0.03s 完成且页面侧回读一致。故本工具在**只读 shadow-root 预检**之后, 直接返回**等价的 `browser_cdp_call` 调用**(可行动, 且不会把会话搞残) | 仍由本工具执行: discard_search(不引用 nodeId, 实测安全) | 只读枚举请用 browser_vip_dom_get_document(pierce=true 可见影子树)'''

EDITS = [(VIP, 'V1 编辑改为可行动路由', OLD, NEW),
         (SERVER, 'V2 描述头', DESC_OLD, DESC_NEW),
         (SERVER, 'V3 描述体', DESC_TAIL_OLD, DESC_TAIL_NEW)]


def main():
    print('== 第142轮补丁 V (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-34s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 命中 %d 次' % (tag, txt.count(old))
        cache[path] = txt.replace(old, new, 1)
        print('   · %s' % tag)
    for path, txt in cache.items():
        print('%s: 行数 %d' % (os.path.basename(path), len(txt.split('\n'))))
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(txt)
    if APPLY:
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
