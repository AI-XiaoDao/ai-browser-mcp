# -*- coding: utf-8 -*-
r"""第142轮补丁 S: 节点编辑前**检测 shadow root 并拒绝** —— 实测这类页面会让 DOM 节点命令挂住并拖死会话。

## 实测(可复现, 干净实例, 每步量 execute_js)
| 序列 | 结果 |
|---|---|
| 页面**无** shadow root: get_document → setAttributeValue → get_document → removeAttribute → get_document → removeNode → get_document | 全部成功, 收尾 `execute_js` **0.03s**(裸 CDP 路径) |
| 页面**有** author shadow root: get_document(nodeId=18 ok) → `remove_attr` | **remove_attr 15.27s 超时**, 之后 `execute_js` **35.33s / 30.27s** 持续坏; 再枚举也失败 |
| 工具路径 `get_document` ×3(无 shadow root) | 每次 0.03s, 之后 `execute_js` 均 0.03s ⇒ getDocument 本身无害 |

⇒ 触发条件是"**页面含 shadow root** + 引用 nodeId 的 DOM 编辑命令", 后果是**本会话 CDP 命令通道被打死**。
这不能留给调用方去撞: 工具必须**先检测、再拒绝**, 并指向可行替代(`browser_execute_js` 等)。

## 做法
`browser_vip_dom_node_edit` 在提交前先 `DOM.getDocument {depth:-1, pierce:true}` 递归统计 `shadowRoots`;
>0 则**明确拒绝**(不进任何破坏性命令), 说明实测后果并给出替代: 用 browser_execute_js / browser_dom_query 等。

用法: py -3 _audit\_apply_round142S.py [--apply]
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

ANCHOR = '''            变量 ne结果 <类型 = 文本型>
            ne结果 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_ed", neCdp方法, neParams, 15000)'''
NEW = '''            // ★ 安全闸门(实测): 若页面含 **shadow root**, 引用 nodeId 的 DOM 编辑命令会挂住(15s 超时),
            //   并把**本会话的 CDP 命令通道打死**(之后每条 CDP 命令 30s 才靠原生回退返回, 需重启恢复)。
            //   故先在**不引用 nodeId** 的前提下把整棵树(含影子树)枚举一遍, 统计 shadowRoots:
            //   >0 就拒绝, 并指向不会毒化会话的替代路径。宁可拒绝, 也不让一次编辑把会话搞残。
            变量 ne预检 <类型 = 文本型>
            ne预检 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_pre", "DOM.getDocument", "{\\"depth\\":-1,\\"pierce\\":true}", 15000)
            如果 (MCP命令服务器.CDP同步结果是否成功 (ne预检))
            {
                变量 ne预检文本 <类型 = 文本型>
                ne预检文本 = MCP命令服务器.取CDP载荷文本 (ne预检)
                变量 ne影子数 <类型 = 整数>
                ne影子数 = MCP命令服务器.统计JSON键出现次数 (ne预检文本, "\\"shadowRoots\\":[{")
                如果 (ne影子数 > 0)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "该页面含 shadow root(检测到 " + 到文本 (ne影子数) + " 处影子树), 本工具**拒绝执行节点编辑** | 实测后果: 对含影子树的页面提交引用 nodeId 的 DOM 命令会**挂住(15s 超时)并打死本会话的 CDP 命令通道**(之后所有 CDP 类工具 30s 才返回, 需重启进程恢复) | 替代(不会毒化会话): browser_execute_js 里直接改 DOM(如 el.removeAttribute('x') / el.remove() / el.setAttribute(...)) 或 browser_dom_query / browser_dom_set_value / browser_dom_set_html | 只读枚举仍可用: browser_vip_dom_get_document(pierce=true 能看到影子树)"))
                }
            }
            变量 ne结果 <类型 = 文本型>
            ne结果 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_ed", neCdp方法, neParams, 15000)'''

HELPER_ANCHOR = '''    # 从 `执行CDP并同步等待` 的回包里取出 CDP 载荷**文本**'''
HELPER_NEW = '''    # 统计一段文本里某个标记出现次数(用于"影子树检测"这类**廉价结构判据**; 不做完整 JSON 解析,
    # 因为预检只需要"有没有"这一位信息, 且 CDP 的 getDocument 输出是标准紧凑 JSON)
    方法 统计JSON键出现次数 <公开 静态 类型 = 整数 @输出名 = "CountJSONKeyOccurrences" @强制输出 = 真>
    参数 文本 <类型 = 文本型 @输出名 = "Text">
    参数 标记 <类型 = 文本型 @输出名 = "Marker">
    {
        如果 (文本 == "" || 标记 == "")
        {
            返回 (0)
        }
        变量 次数 <类型 = 整数 值 = 0>
        变量 起点 <类型 = 整数 值 = 0>
        判断循环 (真)
        {
            变量 命中 <类型 = 整数>
            命中 = 寻找文本 (文本, 标记, 起点, 假)
            如果 (命中 == -1)
            {
                跳出循环
            }
            次数 = 次数 + 1
            起点 = 命中 + 取文本长度 (标记)
            如果 (次数 > 500)
            {
                跳出循环
            }
        }
        返回 (次数)
    }

''' + HELPER_ANCHOR

NE_DESC_OLD = '''实测说明: 走 CDP 时**同步生效**, 可直接用 browser_vip_dom_get_document 重新枚举或 browser_execute_js 回读核对; **DOM 变化后 nodeId 可能失效, 编辑前请重新枚举**'''
NE_DESC_NEW = '''**安全闸门(实测)**: 提交前先全树预检 shadow root —— 页面含影子树时本工具**直接拒绝**, 因为实测对这类页面提交引用 nodeId 的 DOM 命令会挂住(15s)并**打死本会话 CDP 命令通道**(之后所有 CDP 工具 30s 才返回, 需重启); 这类页面请改用 browser_execute_js 直接改 DOM | 实测说明: 普通页面走 CDP 时**同步生效**, 可直接用 browser_vip_dom_get_document 重新枚举或 browser_execute_js 回读核对; **DOM 变化后 nodeId 可能失效, 编辑前请重新枚举**'''

EDITS = [
    (VIP, 'S1 影子树安全闸门', ANCHOR, NEW),
    (SERVER, 'S2 统计助手', HELPER_ANCHOR, HELPER_NEW),
    (SERVER, 'S3 描述: 安全闸门', NE_DESC_OLD, NE_DESC_NEW),
]


def main():
    print('== 第142轮补丁 S (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-32s 锚点未找到(可能已应用)' % tag)
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
