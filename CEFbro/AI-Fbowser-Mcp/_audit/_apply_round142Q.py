# -*- coding: utf-8 -*-
r"""第142轮补丁 Q: VIP 开发者 DOM 族改走 **CDP DOM 域**(默认), 类库路线降级为显式选项。

## 实测(本轮, 同一实例)
| 路线 | 枚举/编辑 | **之后的 CDP 命令通道** |
|---|---|---|
| 类库 `开发者DOM`(`启用("all")` + 枚举/移除节点) | 枚举 0.02s 正常 | **被打死**: 之后 `execute_js` 30.2s(原生回退), 连试三次都一样 |
| CDP `DOM.getDocument / setAttributeValue / removeAttribute / removeNode` | 全部正常(nodeId=18 定位 → 改属性回读一致 → 移除后页面侧 `getElementById===null`) | **完全健康**: 收尾 `execute_js` 0.03s |

⇒ 与"类库截图路线"同一类副作用。DOM 族改走 CDP 后: 功能等价、**不再毒化会话**, 且编辑动作由"异步提交 + 无从回读"
变成"同步生效 + 可立即回读"。

## 改动
1. `browser_vip_dom_get_document`: 默认 `DOM.getDocument`(depth/pierce 直接透传, 回包形态不变: `{"root":{...}}`);
   `via:"library"` 才走类库路线, 并在回包里**如实警告**它会让本会话 CDP 命令通道失效。
2. `browser_vip_dom_node_edit`: 6 个节点/属性动作改走 CDP(`DOM.removeNode / removeAttribute / setAttributeValue /
   setAttributesAsText / setNodeValue / setOuterHTML`), 参数用**拼接**构造(本项目 YYJSON 不支持嵌套成员);
   `discard_search` 仍走类库(CDP 无等价物), 并在回包里说明。

用法: py -3 _audit\_apply_round142Q.py [--apply]
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

GET_OLD = '''            变量 vipDom <类型 = 类_FBrowserVIP_开发者DOM>
            vipDom = MCP命令服务器.取开发者DOM_安全 ()
            如果 (vipDom.是否为空 () == 假)
            {
                vipDom.启用 ("all")
                变量 dDepth <类型 = 整数>'''
GET_NEW = '''            变量 dDepth0 <类型 = 整数>
            dDepth0 = MCP命令服务器.yyjson取整数 (参数JSON, "depth")
            如果 (dDepth0 == 0)
            {
                dDepth0 = 3
            }
            如果 (dDepth0 > 10)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "depth 最大为10, 超过会导致性能问题 | 当前值: " + 到文本 (dDepth0)))
            }
            变量 dPierce0 <类型 = 逻辑型>
            dPierce0 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "pierce", 假)
            变量 dVia <类型 = 文本型>
            dVia = MCP命令服务器.yyjson取文本 (参数JSON, "via")
            如果 (dVia == "")
            {
                dVia = "cdp"
            }
            // ★ 默认走 CDP 的 DOM 域: 实测类库路线(`开发者DOM.启用("all")` + 枚举)会把**本会话的 CDP 命令通道打死**
            //   (之后每条 CDP 命令 30s 才靠原生回退返回), 而 CDP 自身的 `DOM.getDocument` 完全无害,
            //   回包形态与类库一致(`{"root":{...}}`), 故对调用方透明。
            如果 (dVia == "cdp")
            {
                变量 dParams <类型 = 文本型>
                dParams = "{\\"depth\\":" + 到文本 (dDepth0) + ",\\"pierce\\":" + 选择 (dPierce0, "true", "false") + "}"
                变量 dCdp结果 <类型 = 文本型>
                dCdp结果 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_gd", "DOM.getDocument", dParams, 15000)
                如果 (MCP命令服务器.CDP同步结果是否成功 (dCdp结果))
                {
                    变量 d载荷 <类型 = 文本型>
                    d载荷 = MCP命令服务器.取CDP载荷文本 (dCdp结果)
                    如果 (d载荷 != "")
                    {
                        返回 (MCP_响应构建.命令成功_原始JSON (命令ID, d载荷))
                    }
                }
                返回 (MCP_响应构建.命令失败 (命令ID, "CDP DOM.getDocument 失败: " + MCP命令服务器.取CDP同步结果错误 (dCdp结果) + " | 可显式改用 via:library(类库开发者DOM 路线; **实测会让本会话 CDP 命令通道失效**)"))
            }
            变量 vipDom <类型 = 类_FBrowserVIP_开发者DOM>
            vipDom = MCP命令服务器.取开发者DOM_安全 ()
            如果 (vipDom.是否为空 () == 假)
            {
                vipDom.启用 ("all")
                变量 dDepth <类型 = 整数>'''

GET_WARN_OLD = '''                返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步DOMID, "DOM文档已提交枚举, 通过mcp_result查询"))'''
GET_WARN_NEW = '''                返回 (MCP命令服务器.命令成功_异步 (命令ID, 异步DOMID, "DOM文档已提交枚举(经类库开发者DOM 路线), 通过mcp_result查询 | ⚠ 实测: 该路线会让本会话的 CDP 命令通道失效(之后 CDP 类工具退化为原生回退, 每次 10~35 秒且可能超时), 需重启进程恢复; 下次请用默认的 via:cdp"))'''

# ── node_edit: 6 个 CDP 动作 ──
NE_OLD = '''            变量 neAttr <类型 = 文本型>
            neAttr = MCP命令服务器.yyjson取文本 (参数JSON, "attr_name")
            变量 neValue <类型 = 文本型>
            neValue = MCP命令服务器.yyjson取文本 (参数JSON, "value")
            如果 (neAction == "remove_attr")
            {
                如果 (neAttr == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "remove_attr 需要 attr_name"))
                }
                neDom.移除节点属性 (neNodeID, neAttr)
            }
            否则 (neAction == "set_attr")
            {
                如果 (neAttr == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "set_attr 需要 attr_name"))
                }
                neDom.置节点属性值 (neNodeID, neAttr, neValue)
            }
            否则 (neAction == "set_attr_text")
            {
                如果 (neAttr == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "set_attr_text 需要 attr_name(第 2 参) 与 value(文本, 第 3 参)"))
                }
                neDom.置节点属性文本 (neNodeID, neAttr, neValue)
            }
            否则 (neAction == "set_node_value")
            {
                neDom.置节点值 (neNodeID, neValue)
            }
            否则 (neAction == "set_outer_html")
            {
                如果 (neValue == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "set_outer_html 需要 value(新的 outerHTML 源码)"))
                }
                neDom.置节点源码 (neNodeID, neValue)
            }
            否则 (neAction == "remove_node")
            {
                neDom.移除节点 (neNodeID)
            }
            否则
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "未知 action: " + neAction + " | 可用: remove_node / remove_attr / set_attr / set_attr_text / set_node_value / set_outer_html / discard_search"))
            }
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"" + MCP_响应构建.JSON转义文本 (neAction) + "\\",\\"node_id\\":" + 到文本 (neNodeID) + ",\\"submitted\\":true,\\"note\\":\\"已提交(类库该方法效果**异步**) | 回读核对: 重新调 browser_vip_dom_get_document 看节点/属性是否已变; 页面侧可用 browser_dom_query / browser_execute_js 断言 | 失败信息经开发者事件上报: browser_vip_enable_devtools_observer enable=true 后看 browser_event\\"}"))'''

NE_NEW = '''            变量 neAttr <类型 = 文本型>
            neAttr = MCP命令服务器.yyjson取文本 (参数JSON, "attr_name")
            变量 neValue <类型 = 文本型>
            neValue = MCP命令服务器.yyjson取文本 (参数JSON, "value")
            // ★ 默认走 CDP 的 DOM 域(实测: 编辑**同步生效**且**不毒化** CDP 通道; 类库开发者DOM 路线会让之后所有
            //   CDP 命令 30s 才返回)。参数用拼接构造 —— 本项目 YYJSON 对象不支持嵌套成员。
            变量 neParams <类型 = 文本型>
            变量 neCdp方法 <类型 = 文本型>
            neCdp方法 = ""
            如果 (neAction == "remove_attr")
            {
                如果 (neAttr == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "remove_attr 需要 attr_name"))
                }
                neCdp方法 = "DOM.removeAttribute"
                neParams = "{\\"nodeId\\":" + 到文本 (neNodeID) + ",\\"name\\":\\"" + MCP_响应构建.JSON转义文本 (neAttr) + "\\"}"
            }
            否则 (neAction == "set_attr")
            {
                如果 (neAttr == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "set_attr 需要 attr_name"))
                }
                neCdp方法 = "DOM.setAttributeValue"
                neParams = "{\\"nodeId\\":" + 到文本 (neNodeID) + ",\\"name\\":\\"" + MCP_响应构建.JSON转义文本 (neAttr) + "\\",\\"value\\":\\"" + MCP_响应构建.JSON转义文本 (neValue) + "\\"}"
            }
            否则 (neAction == "set_attr_text")
            {
                如果 (neAttr == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "set_attr_text 需要 attr_name(第 2 参) 与 value(文本, 第 3 参)"))
                }
                neCdp方法 = "DOM.setAttributesAsText"
                neParams = "{\\"nodeId\\":" + 到文本 (neNodeID) + ",\\"text\\":\\"" + MCP_响应构建.JSON转义文本 (neValue) + "\\",\\"name\\":\\"" + MCP_响应构建.JSON转义文本 (neAttr) + "\\"}"
            }
            否则 (neAction == "set_node_value")
            {
                neCdp方法 = "DOM.setNodeValue"
                neParams = "{\\"nodeId\\":" + 到文本 (neNodeID) + ",\\"value\\":\\"" + MCP_响应构建.JSON转义文本 (neValue) + "\\"}"
            }
            否则 (neAction == "set_outer_html")
            {
                如果 (neValue == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "set_outer_html 需要 value(新的 outerHTML 源码)"))
                }
                neCdp方法 = "DOM.setOuterHTML"
                neParams = "{\\"nodeId\\":" + 到文本 (neNodeID) + ",\\"outerHTML\\":\\"" + MCP_响应构建.JSON转义文本 (neValue) + "\\"}"
            }
            否则 (neAction == "remove_node")
            {
                neCdp方法 = "DOM.removeNode"
                neParams = "{\\"nodeId\\":" + 到文本 (neNodeID) + "}"
            }
            否则
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "未知 action: " + neAction + " | 可用: remove_node / remove_attr / set_attr / set_attr_text / set_node_value / set_outer_html / discard_search"))
            }
            变量 ne结果 <类型 = 文本型>
            ne结果 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_ed", neCdp方法, neParams, 15000)
            如果 (MCP命令服务器.CDP同步结果是否成功 (ne结果) == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, neCdp方法 + " 失败: " + MCP命令服务器.取CDP同步结果错误 (ne结果) + " | 常见原因: nodeId 已失效(**DOM 变化后请重新枚举** browser_vip_dom_get_document) 或节点不存在 | 也可显式改用类库路线(本工具不再提供, 因实测会让 CDP 通道失效)"))
            }
            MCP_响应构建.记录自动处理 ("CDP." + neCdp方法 + "(同步生效, 不毒化 CDP 通道)")
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"" + MCP_响应构建.JSON转义文本 (neAction) + "\\",\\"cdp_method\\":\\"" + neCdp方法 + "\\",\\"node_id\\":" + 到文本 (neNodeID) + ",\\"applied\\":true,\\"note\\":\\"已**同步生效**(CDP DOM 域) | 回读核对: 重新调 browser_vip_dom_get_document 看节点/属性是否已变; 页面侧可用 browser_execute_js / browser_dom_query 断言\\"}"))'''

# ── Server: 取CDP载荷文本 助手 + 描述更新 ──
PAYLOAD_ANCHOR = '''    # 从 `执行CDP并同步等待` 的回包里取出 CDP 的 `result` 对象'''
PAYLOAD_NEW = '''    # 从 `执行CDP并同步等待` 的回包里取出 CDP 载荷**文本**(载荷可能在 `result`(包装过的工具)或
    # `message`(裸 CDP 通道实测形态)里; 本机实测两种都会出现, 故统一在此容错)
    方法 取CDP载荷文本 <公开 静态 类型 = 文本型 @输出名 = "GetCDPPayloadText" @强制输出 = 真>
    参数 同步结果JSON <类型 = 文本型 @输出名 = "SyncResultJSON">
    {
        变量 外层 <类型 = YYJSON只读对象类>
        如果 (外层.创建自文本 (同步结果JSON) == 假)
        {
            返回 ("")
        }
        变量 载荷文本 <类型 = 文本型>
        载荷文本 = yyjson取文本 (外层, "result")
        如果 (载荷文本 == "")
        {
            载荷文本 = yyjson取文本 (外层, "message")
        }
        返回 (载荷文本)
    }

''' + PAYLOAD_ANCHOR

DOC_DESC_OLD = '''"VIP: CDP获取DOM文档(JSON) | 返回 CDP getDocument 形态的节点树(nodeId/attributes/children), nodeId 是后续 browser_vip_dom_node_edit 的入参 | pierce=true 可穿透 shadow DOM(类库该参数原先恒为假, 影子树枚举不到)"'''
DOC_DESC_NEW = '''"获取 DOM 节点树(CDP getDocument 形态: nodeId/attributes/children; nodeId 是 browser_vip_dom_node_edit 的入参) | **默认走 CDP `DOM.getDocument`**(实测: 快且**不毒化** CDP 命令通道; pierce=true 可穿透 shadow DOM —— 实测 pierce=false 25 节点 / true 27 节点且影子节点只在 true 时可见) | `via:\\"library\\"` 才走类库开发者DOM 路线: **实测会让本会话 CDP 命令通道失效**(之后 CDP 类工具退化为原生回退, 每次 10~35 秒), 仅在确知后果时选用"'''

NE_DESC_OLD = '''"VIP 开发者 DOM **节点编辑**(类库 开发者DOM 族)'''
NE_DESC_NEW = '''"DOM **节点编辑**(默认走 CDP DOM 域: 同步生效、不毒化 CDP 通道)'''
NE_DESC_TAIL_OLD = '''实测说明: 类库这些方法效果**异步**, 失败信息经开发者事件上报(browser_vip_enable_devtools_observer enable=true 后看 browser_event); 请用**重新枚举**回读核对"'''
NE_DESC_TAIL_NEW = '''实测说明: 走 CDP 时**同步生效**, 可直接用 browser_vip_dom_get_document 重新枚举或 browser_execute_js 回读核对; **DOM 变化后 nodeId 可能失效, 编辑前请重新枚举** | discard_search 仍走类库(CDP 无等价物): 它是唯一不毒化通道的动作"'''

EDITS = [
    (VIP, 'Q1 get_document 默认走 CDP', GET_OLD, GET_NEW),
    (VIP, 'Q2 类库路线加警告', GET_WARN_OLD, GET_WARN_NEW),
    (VIP, 'Q3 node_edit 6 动作改 CDP', NE_OLD, NE_NEW),
    (SERVER, 'Q4 取CDP载荷文本 助手', PAYLOAD_ANCHOR, PAYLOAD_NEW),
    (SERVER, 'Q5 get_document 描述', DOC_DESC_OLD, DOC_DESC_NEW),
    (SERVER, 'Q6 node_edit 描述头', NE_DESC_OLD, NE_DESC_NEW),
    (SERVER, 'Q7 node_edit 描述尾', NE_DESC_TAIL_OLD, NE_DESC_TAIL_NEW),
]


def main():
    print('== 第142轮补丁 Q (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-36s 锚点未找到(可能已应用)' % tag)
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
