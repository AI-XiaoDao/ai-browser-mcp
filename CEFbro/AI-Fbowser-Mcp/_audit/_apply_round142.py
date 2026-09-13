# -*- coding: utf-8 -*-
r"""第142轮补丁: VIP 开发者 DOM 族补齐(并行只读分诊确认的 2 处参数截断 + 3 个真缺口, 另补 4 个同族写动作)。

## 依据(逐字核对 FBroVip.wsv)
| 类库方法 | 出处 | 现状 |
|---|---|---|
| `枚举DOM (深度, 穿透 pierce, 回调)` | :1559-1574 | 项目第 2 参**恒传假** ⇒ shadow DOM 不可枚举 |
| `预查找文本 (查询文本, includeUserAgentShadowDOM, 回调)` | :1684-1691 | 项目第 2 参**恒传假** |
| `移除节点属性 (节点ID, 属性名)` | :1509-1515 | **真缺口**(项目 0 调用) |
| `移除节点 (节点ID)` | :1517-1521 | **真缺口**(类库原文: 子节点一并删除, **不能是根节点**) |
| `清除查找 (查找ID)` | :1553-1557 | **真缺口** |
| `置节点属性值 (节点ID, 属性名, 值)` | :1531 | 真缺口(同族, 一并补上) |
| `置节点属性文本 (节点ID, 属性名, 文本)` | :1523 | 真缺口(同族) |
| `置节点值 (节点ID, 值)` | :1539 | 真缺口(仅文本节点) |
| `置节点源码 (节点ID, 源码文本)` | :1546 | 真缺口(同族) |

## 做法
1. `browser_vip_dom_get_document` 新增 `pierce`; `browser_vip_dom_search` 新增 `ua_shadow` —— 都只是把已有参数透传;
2. 新增 `browser_vip_dom_node_edit`(一个工具 7 个 action, 全走 `取开发者DOM_安全` 同一入口, 不新起第二个 DOM 状态机),
   硬守卫: 节点类动作必须显式 `confirm:true`(真实改写用户页面)、`node_id` 必须 >0 且**不能是根节点(1)**、
   节点类动作**必须先枚举**(描述里写明), 回包如实说明"效果异步、错误经开发者事件上报、用重新枚举回读核对"。

用法: py -3 _audit\_apply_round142.py [--apply]
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

# ── P1: pierce ──
PIERCE_OLD = '''                vipDom.枚举DOM (dDepth, 假, DOM回调)'''
PIERCE_NEW = '''                // 穿透(pierce): 类库第 2 参; 原先**恒传假** ⇒ shadow DOM 内容枚举不到。改为可显式开启。
                变量 dPierce <类型 = 逻辑型>
                dPierce = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "pierce", 假)
                vipDom.枚举DOM (dDepth, dPierce, DOM回调)'''

# ── P2: ua_shadow ──
UA_OLD = '''                        vipDom2.预查找文本 (searchQuery, 假, 预查回调)'''
UA_NEW = '''                        // includeUserAgentShadowDOM: 类库第 2 参; 原先**恒传假** ⇒ 用户代理(UA)影子 DOM 内的文本搜不到。
                        变量 sUaShadow <类型 = 逻辑型>
                        sUaShadow = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "ua_shadow", 假)
                        vipDom2.预查找文本 (searchQuery, sUaShadow, 预查回调)'''

# ── P3: 新工具 browser_vip_dom_node_edit ──
NODE_ANCHOR = '''        否则 (方法名 == "browser_vip_enable_devtools_observer")'''
NODE_NEW = '''        // === VIP 开发者 DOM: 节点编辑(枚举 → 改 → 重新枚举回读核对) ===
        // 覆盖类库 7 个真缺口: 移除节点 / 移除节点属性 / 清除查找 + 置节点属性值 / 置节点属性文本 / 置节点值 / 置节点源码。
        // 硬守卫(照抄类库约束 + 项目惯例):
        //   · 节点类动作必须显式 confirm:true —— 它们**真实改写用户页面**;
        //   · node_id 必须 >0 且不能是根节点(类库原文: 移除节点"不能是根节点");
        //   · 节点类动作的前提是"已枚举过 DOM 拿到 nodeId"(类库原文), 未枚举得到的是无效 id;
        //   · 效果**异步**、失败信息经开发者事件上报, 故回包如实说明并给出回读办法(重新枚举 / 页面侧断言)。
        否则 (方法名 == "browser_vip_dom_node_edit")
        {
            变量 neAction <类型 = 文本型>
            neAction = MCP命令服务器.yyjson取文本 (参数JSON, "action")
            如果 (neAction == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "需要 action | 可用: remove_node(移除节点, 连子节点一并删) / remove_attr(移除属性) / set_attr(置属性值) / set_attr_text(置属性文本) / set_node_value(置节点值, 仅文本节点) / set_outer_html(置节点源码) / discard_search(清除查找, 释放资源)"))
            }
            变量 neDom <类型 = 类_FBrowserVIP_开发者DOM>
            neDom = MCP命令服务器.取开发者DOM_安全 ()
            如果 (neDom.是否为空 ())
            {
                返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_VIP不可用))
            }
            neDom.启用 ("all")
            如果 (neAction == "discard_search")
            {
                变量 dsID <类型 = 文本型>
                dsID = MCP命令服务器.yyjson取文本 (参数JSON, "search_id")
                如果 (dsID == "")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "discard_search 需要 search_id | 它来自 browser_vip_dom_search 的预查找结果(形如 \\"26428.0\\")"))
                }
                neDom.清除查找 (dsID)
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"discard_search\\",\\"search_id\\":\\"" + MCP_响应构建.JSON转义文本 (dsID) + "\\",\\"submitted\\":true,\\"note\\":\\"清除查找已提交(释放该次查找占用的资源) | 失败信息经开发者事件上报(见 browser_event); 再次 browser_vip_dom_search 会重新预查找\\"}"))
            }
            变量 neNodeID <类型 = 整数>
            neNodeID = MCP命令服务器.yyjson取整数 (参数JSON, "node_id")
            如果 (neNodeID <= 0)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "需要 node_id(>0) | 先用 browser_vip_dom_get_document 枚举 DOM 拿到 nodeId —— 类库原文: 未枚举过的 id 无效"))
            }
            如果 (neNodeID == 1)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "node_id=1 是根文档节点 | 类库原文: 移除节点**不能是根节点**; 属性/值类动作对根节点也无意义, 故一律拒绝"))
            }
            如果 (MCP命令服务器.yyjson取逻辑 (参数JSON, "confirm") == 假)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "该动作会**真实改写用户页面**(不可撤销, 只能刷新恢复), 故需显式 confirm:true | 动作: " + neAction + " | 想只读查看请用 browser_vip_dom_get_document / browser_dom_query"))
            }
            变量 neAttr <类型 = 文本型>
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
            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"" + MCP_响应构建.JSON转义文本 (neAction) + "\\",\\"node_id\\":" + 到文本 (neNodeID) + ",\\"submitted\\":true,\\"note\\":\\"已提交(类库该方法效果**异步**) | 回读核对: 重新调 browser_vip_dom_get_document 看节点/属性是否已变; 页面侧可用 browser_dom_query / browser_execute_js 断言 | 失败信息经开发者事件上报: browser_vip_enable_devtools_observer enable=true 后看 browser_event\\"}"))
        }
''' + NODE_ANCHOR

# ── P4: 注册 + schema ──
REG_ANCHOR = '''        命令注册表.置整数值 ("browser_by_index", 1333)'''
REG_NEW = REG_ANCHOR + '''
        命令注册表.置整数值 ("browser_vip_dom_node_edit", 1334)'''

TOOL_ANCHOR = '''添加工具JSON ("browser_json",'''
TOOL_NEW = '''添加工具JSON ("browser_vip_dom_node_edit", "VIP 开发者 DOM **节点编辑**(类库 开发者DOM 族) | action: remove_node(移除节点, 连子节点一并删)/remove_attr(移除属性)/set_attr(置属性值)/set_attr_text(置属性文本)/set_node_value(置节点值, 仅文本节点)/set_outer_html(置节点源码)/discard_search(清除查找释放资源) | **前置**: 节点类动作必须先 browser_vip_dom_get_document 枚举拿到 node_id(类库原文: 未枚举过的 id 无效); 必须显式 confirm:true(**真实改写用户页面**, 不可撤销, 只能刷新恢复); node_id=1(根文档节点)一律拒绝(类库原文: 移除节点不能是根节点) | 实测说明: 类库这些方法效果**异步**, 失败信息经开发者事件上报(browser_vip_enable_devtools_observer enable=true 后看 browser_event); 请用**重新枚举**回读核对", 多属性Schema文本 (属性项JSON ("action", "text", "remove_node/remove_attr/set_attr/set_attr_text/set_node_value/set_outer_html/discard_search") + "," + 属性项JSON ("node_id", "integer", "节点ID(来自 browser_vip_dom_get_document; 不能是 1)") + "," + 属性项JSON ("attr_name", "text", "属性名(remove_attr/set_attr/set_attr_text 需要)") + "," + 属性项JSON ("value", "text", "新值/新源码(set_* 需要)") + "," + 属性项JSON ("search_id", "text", "discard_search 需要(来自 browser_vip_dom_search 的 searchId)") + "," + 属性项JSON ("confirm", "boolean", "节点类动作必填 true: 确认真实改写页面"), "\\"action\\""))
''' + TOOL_ANCHOR

DOC_DESC_OLD = '''"VIP: 开发者DOM - 获取文档节点树'''
DOC_DESC_NEW = '''"VIP: 开发者DOM - 获取文档节点树'''
EDITS = [
    (VIP, 'P1 枚举DOM 透传 pierce', PIERCE_OLD, PIERCE_NEW),
    (VIP, 'P2 预查找文本 透传 ua_shadow', UA_OLD, UA_NEW),
    (VIP, 'P3 新增 browser_vip_dom_node_edit', NODE_ANCHOR, NODE_NEW),
    (SERVER, 'P4a 命令注册表 1334', REG_ANCHOR, REG_NEW),
    (SERVER, 'P4b 注册工具', TOOL_ANCHOR, TOOL_NEW),
]

# 三个文档型工具的描述/schema 追加两个新参数(锚点按各自注册行原文)
DOC_EDITS = [
    ('browser_vip_dom_get_document',
     '''"VIP: CDP获取DOM文档(JSON)", 单参数Schema文本 ("depth", "integer", "深度", 假))''',
     '''"VIP: CDP获取DOM文档(JSON) | 返回 CDP getDocument 形态的节点树(nodeId/attributes/children), nodeId 是后续 browser_vip_dom_node_edit 的入参 | pierce=true 可穿透 shadow DOM(类库该参数原先恒为假, 影子树枚举不到)", 多属性Schema文本 (属性项JSON ("depth", "integer", "枚举深度(默认3, 最大10)") + "," + 属性项JSON ("pierce", "boolean", "true=穿透 shadow DOM(类库 pierce 参数)"), ""))'''),
    ('browser_vip_dom_search',
     '''属性项JSON ("query", "text", ''',
     '''属性项JSON ("ua_shadow", "boolean", "true=同时搜用户代理(UA)影子 DOM(类库 includeUserAgentShadowDOM; 原先恒为假)") + "," + 属性项JSON ("query", "text", '''),
]


def main():
    print('== 第142轮补丁 (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-38s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 命中 %d 次' % (tag, txt.count(old))
        cache[path] = txt.replace(old, new, 1)
        print('   · %s' % tag)
    # 文档型工具 schema 追加(逐行按工具名定位正则更稳: 这里用唯一字面量锚点)
    srv = cache.get(SERVER) or io.open(SERVER, encoding='utf-8', newline='').read()
    lines = srv.split('\n')
    done = []
    for tool, old, new in DOC_EDITS:
        for i, l in enumerate(lines):
            if ('添加工具JSON ("%s"' % tool) in l and old in l:
                lines[i] = l.replace(old, new, 1)
                done.append(tool)
                break
    print('   · 文档型工具 schema 追加: %s' % (done or '(未命中)'))
    cache[SERVER] = '\n'.join(lines)
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
