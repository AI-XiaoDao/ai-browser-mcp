# -*- coding: utf-8 -*-
r"""第142轮补丁 U: 节点编辑改为**两段式(async 回执 + mcp_result)** —— 与实测可用的 `browser_cdp_call` 同构。

## 实测依据(本轮)
| 路线 | 结果 |
|---|---|
| `browser_cdp_call {method:DOM.removeAttribute/removeNode}`(**派发后由外层等待, 工具回最终结果**) | **全通**: removeAttribute→页面侧 null; removeNode→页面侧 true; 全程 `execute_js` 0.03s |
| 分支内 `执行CDP并同步等待`(自带删旧结果/预算压缩/超时自救/补域) | 引用 nodeId 的命令**挂住 15s 并拖死通道** |
| 分支内"`执行CDP命令_带参数` + `同步等待异步任务`"最小原语 | 仍失败(与上同) |

⇒ 结论: 在本项目里, 引用 nodeId 的 DOM 命令**只有在"派发即返回回执、由调用方另取结果"的两段式下**才稳。
故把节点编辑改成同一形态: 立即回 `task_id`, 调用方用 `mcp_result` 取结果(与 `browser_cdp_call` 的用法一致)。

用法: py -3 _audit\_apply_round142U.py [--apply]
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

OLD = '''            // ★ 实测: 引用 nodeId 的 DOM 命令**不能**走 `执行CDP并同步等待`(它自带的"删旧结果/预算压缩/超时自救/
            //   反应式补域"等额外动作会让这条命令挂住 15s 并拖死整条通道); 而"派发 + 直接同步等待"这对最小原语
            //   (即 browser_cdp_call 走的那条路)实测完全正常 —— 故此处改用最小原语, 并保留同样可读的失败文案。
            变量 ne结果 <类型 = 文本型>
            MCP命令服务器.执行CDP命令_带参数 (命令ID + "_ed", neCdp方法, neParams)
            ne结果 = MCP命令服务器.同步等待异步任务 (命令ID + "_ed", 15000)
            如果 (MCP命令服务器.CDP同步结果是否成功 (ne结果) == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, neCdp方法 + " 失败: " + MCP命令服务器.取CDP同步结果错误 (ne结果) + " | 常见原因: nodeId 已失效(**DOM 变化后请重新枚举** browser_vip_dom_get_document) 或节点不存在 | 也可显式改用类库路线(本工具不再提供, 因实测会让 CDP 通道失效)"))
            }
            MCP_响应构建.记录自动处理 ("CDP." + neCdp方法 + "(同步生效, 不毒化 CDP 通道)")
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"" + MCP_响应构建.JSON转义文本 (neAction) + "\\",\\"cdp_method\\":\\"" + neCdp方法 + "\\",\\"node_id\\":" + 到文本 (neNodeID) + ",\\"applied\\":true,\\"note\\":\\"已**同步生效**(CDP DOM 域) | 回读核对: 重新调 browser_vip_dom_get_document 看节点/属性是否已变; 页面侧可用 browser_execute_js / browser_dom_query 断言\\"}"))'''

NEW = '''            // ★★ 实测(本轮三组对照): 引用 nodeId 的 DOM 命令在本项目里**只有"派发即返回回执、由调用方另取结果"的
            //   两段式**才稳 —— 分支内 `执行CDP并同步等待` 会挂住 15s 并把整条 CDP 通道拖死(之后每条命令 30s);
            //   换成"派发 + 同步等待"最小原语仍然失败; 而 `browser_cdp_call` 那条路(getDocument/removeAttribute/
            //   removeNode 连做)全程 0.03s 且页面侧回读一致。故这里改成同构两段式: 立即回 task_id, 用 mcp_result 取结果。
            变量 ne任务ID <类型 = 文本型>
            ne任务ID = 命令ID + "_ed"
            MCP命令服务器.执行CDP命令_带参数 (ne任务ID, neCdp方法, neParams)
            返回 (MCP命令服务器.命令成功_异步 (命令ID, ne任务ID, "已提交 " + neCdp方法 + " (action=" + neAction + ", node_id=" + 到文本 (neNodeID) + ") | 用 mcp_result {request_id:\\"" + ne任务ID + "\\"} 取提交回执 | 生效后请回读核对: 重新 browser_vip_dom_get_document 或页面侧 browser_execute_js 断言 | 注: 本机实测节点类命令只能走这条两段式(同步等待会把 CDP 通道拖死), 与 browser_cdp_call 同构"))'''

PRE_OLD_TAIL = '''            如果 (MCP命令服务器.CDP同步结果是否成功 (ne预检))
            {'''
# 预检与 enable 仍保持同步(它们不引用 nodeId, 实测可重复使用); 只改编辑命令

EDITS = [(VIP, 'U1 编辑命令改两段式', OLD, NEW)]


def main():
    print('== 第142轮补丁 U (%s) ==' % ('应用' if APPLY else '预演'))
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
