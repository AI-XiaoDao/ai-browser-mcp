# -*- coding: utf-8 -*-
r"""第125轮: 让 browser_network_body 真正做到"零前置一次成功"(台账里它一直以 TARGET 失败)。

问题(实测+静态核实):
  · `browser_network_body` 只接受 `request_id`, 而**项目里没有任何工具回传 requestId**
    —— `browser_network list` 读的是 CEF 层网络日志(`记录网络请求_详细` 只写 method/url/headers/post_body,
    不含 CDP requestId), 所以调用方只能手工 订阅 + 抓事件 + 手抄, 且要"尽快"调, 否则响应体被回收;
  · 台账实测它失败于 `Network.getResponseBody 失败: No resource with given identifier found`(TARGET),
    本质是**前置缺失**, 正属于目标 A 线要清零的失败类型。

本轮改法(全部复用既有件, 不重复造轮子):
  1) 新增 `确保网络CDP捕获()`: 复用既有 `MCP_内核分派.分派_CDP监控 {action:add, methods:Network.*}`
     (它自带去重、置启用、按前缀自动 `Network.enable`, 并经 auto_prepared 如实上报);
  2) 新增 `查找CDP请求ID()`: 从既有 `查询事件日志("cdp_monitor","Network.requestWillBeSent",0,300)`
     里解析 `requestId`/`request.url`(数组解析复用既有 `取JSON数组自文本`), 给 url 时先精确后包含,
     不给则取最新一条; 返回 JSON 文本(避免火山里没有的按引用出参写法);
  3) `browser_network_body` 接受 `url`/`wait_ms`: 不传 request_id 时自动解析, 命不中则在 wait_ms 内轮询等待;
     仍命不中时给出**可行动**失败(已捕获条数 + 恢复捕获后重发请求的指引), 不再回一句"request_id 缺少参数";
  4) `browser_network` 新增 `action=body` 并在 schema 里声明 url/request_id/wait_ms, 直接转交同一分派(零重复实现)。

用法: py -3 _audit\_apply_network_body_resolve.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')

HELPERS = '''    # ==== 响应体(requestWillBeSent → requestId)的零前置解析 ====
    # 为什么需要(实测+静态核实): `browser_network_body` 原先只收 request_id, 而项目里**没有任何工具
    #   回传 requestId** —— `browser_network list` 读的是 CEF 层网络日志(不含 CDP requestId),
    #   调用方只能手工订阅 + 抓一条事件 + 手抄, 还要"尽快"调用否则响应体被回收 ⇒ 实测失败
    #   "No resource with given identifier found"。故把这两步(开启捕获 / 解析 requestId)做成复用件。

    方法 确保网络CDP捕获 <公开 静态 类型 = 文本型 注释 = "零前置: 确保 CDP 的 Network 域与 Network.* 事件订阅都在(取响应体与解析 requestId 都依赖它)。返回本次**真正补过**什么(空串=本来就绪)" @输出名 = "EnsureNetworkCDPCapture" @强制输出 = 真>
    参数 命令ID <类型 = 文本型 @输出名 = "CommandID">
    {
        变量 已订阅 <类型 = 逻辑型 值 = 假>
        如果 (MCP_内核分派.CDP监控启用)
        {
            计次循环 (MCP_内核分派.CDP监控模式.取成员数 ())
            {
                变量 现有模式 <类型 = 文本型>
                现有模式 = MCP_内核分派.CDP监控模式.取成员 (取循环索引 ())
                如果 (现有模式 == "*" || 现有模式 == "Network.*" || 现有模式 == "Network.requestWillBeSent")
                {
                    已订阅 = 真
                    跳出循环
                }
            }
        }
        如果 (已订阅)
        {
            返回 ("")
        }
        // 复用既有 CDP 监控分派: 它会去重加入模式、置启用、按模式前缀自动 Network.enable,
        // 还会经 auto_prepared 如实上报补过 Network.enable —— 不在这里重写一份。
        变量 监控参数 <类型 = YYJSON只读对象类>
        监控参数.创建自文本 ("{\\"action\\":\\"add\\",\\"methods\\":\\"Network.*\\"}")
        MCP_内核分派.分派_CDP监控 (命令ID + "_netmon", 监控参数)
        返回 ("Network.* 事件订阅 + Network 域(取响应体所需; 此前需手工调 browser_kernel_cdp_monitor)")
    }

    方法 查找CDP请求ID <公开 静态 类型 = 文本型 注释 = "从 CDP 捕获的 Network.requestWillBeSent 事件里解析 requestId, 返回 JSON 文本 {requestId,url,count}(未命中时 requestId 为空串)。给 目标URL 时先精确相等、再退化为包含匹配; 不给则取最新一条" @输出名 = "FindCDPRequestID" @强制输出 = 真>
    参数 目标URL <类型 = 文本型 @默认值 = "" @输出名 = "TargetURL">
    {
        变量 事件数组文本 <类型 = 文本型>
        事件数组文本 = 查询事件日志 ("cdp_monitor", "Network.requestWillBeSent", 0, 300)
        变量 条数 <类型 = 整数>
        条数 = 0
        变量 命中ID <类型 = 文本型>
        命中ID = ""
        变量 命中URL <类型 = 文本型>
        命中URL = ""
        如果 (事件数组文本 != "" && 事件数组文本 != "[]")
        {
            变量 事件数组 <类型 = YYJSON只读数组类>
            事件数组 = 取JSON数组自文本 (事件数组文本, "events")
            条数 = (整数)事件数组.取成员数 ()
            变量 包含ID <类型 = 文本型>
            包含ID = ""
            变量 包含URL <类型 = 文本型>
            包含URL = ""
            计次循环 (条数)
            {
                变量 事件项 <类型 = YYJSON只读对象类>
                事件项 = 事件数组.取成员 (取循环索引 ())
                如果 (事件项.是否为空 ())
                {
                    到循环尾
                }
                变量 该项ID <类型 = 文本型>
                该项ID = yyjson取文本 (事件项, "requestId")
                如果 (该项ID == "")
                {
                    到循环尾
                }
                变量 请求对象 <类型 = YYJSON只读对象类>
                请求对象 = yyjson取对象成员 (事件项, "request")
                变量 该项URL <类型 = 文本型>
                该项URL = ""
                如果 (请求对象.是否为空 () == 假)
                {
                    该项URL = yyjson取文本 (请求对象, "url")
                }
                // 事件按 created_at DESC 返回(最新在前): 第一次命中的即"最新的那个"
                如果 (目标URL == "")
                {
                    如果 (命中ID == "")
                    {
                        命中ID = 该项ID
                        命中URL = 该项URL
                    }
                }
                否则
                {
                    如果 (该项URL == 目标URL)
                    {
                        如果 (命中ID == "")
                        {
                            命中ID = 该项ID
                            命中URL = 该项URL
                        }
                    }
                    否则
                    {
                        如果 (包含ID == "" && 该项URL != "")
                        {
                            如果 (寻找文本 (该项URL, 目标URL, 0, 假) != -1)
                            {
                                包含ID = 该项ID
                                包含URL = 该项URL
                            }
                        }
                    }
                }
            }
            如果 (命中ID == "" && 包含ID != "")
            {
                命中ID = 包含ID
                命中URL = 包含URL
            }
        }
        // 一次性组装(YYJSON对象类只做"加入", 不依赖覆盖/移除这类本项目未用过的成员方法)
        变量 结果对象 <类型 = YYJSON对象类>
        结果对象.创建自文本 ("{}")
        结果对象.加入文本成员 ("requestId", 命中ID)
        结果对象.加入文本成员 ("url", 命中URL)
        结果对象.加入整数成员 ("count", 条数)
        返回 (结果对象.到可读文本 (YYJSON格式化选项.压缩))
    }

'''

ANCHOR_HELPER = '    方法 查询网络日志 <公开 静态 类型 = 文本型 @输出名 = "QueryNetworkLog" @强制输出 = 真>'

BODY_OLD = '        添加工具JSON ("browser_network_body", "获取响应体(VIP)", 单参数Schema文本 ("request_id", "text", "请求ID"))'
BODY_NEW = ('        添加工具JSON ("browser_network_body", "获取某个请求的响应体(Network.getResponseBody)'
            ' | **零前置**: 不传 request_id 时自动开启 Network 域与 Network.* 捕获, 并按 url(先精确后包含)或不带 url 时取最新一条'
            '自动解析 requestId, 解析来源在 resolve_note 里如实回传; 给了 url 但尚未出现时会在 wait_ms(默认2000, 上限15000)内轮询等待'
            ' | 实测限制(如实说明): 响应体只对**本 CDP 会话内、捕获开启之后**发生的请求可取, 且可能已被浏览器回收(此时报错给出可行动指引)'
            ' | 与 browser_network {action:body} 等价", 多属性Schema文本 (属性项JSON ("request_id", "text", "CDP 请求ID(可省略; 省略则按 url 或最新请求自动解析)") + "," + 属性项JSON ("url", "text", "按 URL 解析请求ID(可省略; 与 request_id 二选一, 同时给时以 request_id 为准)") + "," + 属性项JSON ("wait_ms", "integer", "给了 url 时的等待上限毫秒(默认2000, 上限15000)"), ""))')

NET_OLD = '        添加工具JSON ("browser_network", "网络日志 list/enable/clear (list 默认 auto_enable; 亦接受 network_ 前缀别名)", 单参数Schema文本 ("action", "text", "list/get/enable/disable/clear/detail_enable/network_get/network_enable/network_disable/network_clear/network_detail_enable"))'
NET_NEW = ('        添加工具JSON ("browser_network", "网络日志 list/enable/clear, action=body 取响应体(转交 browser_network_body, 零前置自动解析 requestId)'
           ' (list 默认 auto_enable; 亦接受 network_ 前缀别名)", 多属性Schema文本 (属性项JSON ("action", "text", "list/get/enable/disable/clear/detail_enable/body/network_get/network_enable/network_disable/network_clear/network_detail_enable") + "," + 属性项JSON ("request_id", "text", "action=body 时: CDP 请求ID(可省略, 自动解析)") + "," + 属性项JSON ("url", "text", "action=body 时: 按 URL 解析请求ID(可省略)") + "," + 属性项JSON ("wait_ms", "integer", "action=body 时: 等待上限毫秒(默认2000)") + "," + 属性项JSON ("limit", "integer", "list 时的条数(默认500, 上限1000)"), ""))')

CORE_GUARD_OLD = '''            变量 requestId <类型 = 文本型>
            requestId = MCP命令服务器.yyjson取文本 (参数JSON, "request_id")
            如果 (requestId == "")
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "request_id " + MCP_常量.错误_缺少参数))
            }'''

CORE_GUARD_NEW = '''            变量 requestId <类型 = 文本型>
            requestId = MCP命令服务器.yyjson取文本 (参数JSON, "request_id")
            变量 解析说明 <类型 = 文本型>
            解析说明 = ""
            如果 (requestId == "")
            {
                // 零前置: ①确保 Network 域与 Network.* 捕获都开着 ②按 url / 最新请求自动解析 requestId。
                // 为什么必须自动(实测+静态核实): 本工具原先**只能**收 request_id, 而项目里没有任何工具
                //   把 requestId 回传(browser_network list 是 CEF 层日志, 不含 CDP requestId), 调用方只能
                //   手工订阅 + 抓事件 + 手抄, 还要尽快调用否则响应体被回收 —— 正是"反复换方法才成功"的来源。
                解析说明 = MCP命令服务器.确保网络CDP捕获 (命令ID)
                变量 目标URL <类型 = 文本型>
                目标URL = MCP命令服务器.yyjson取文本 (参数JSON, "url")
                变量 等待上限 <类型 = 整数>
                等待上限 = MCP命令服务器.yyjson取整数 (参数JSON, "wait_ms")
                如果 (等待上限 <= 0)
                {
                    等待上限 = 2000
                }
                如果 (等待上限 > 15000)
                {
                    等待上限 = 15000
                }
                变量 等待截止 <类型 = 长整数>
                等待截止 = 取启动时间 () + 等待上限
                变量 解析JSON <类型 = 文本型>
                变量 命中URL <类型 = 文本型>
                变量 候选条数 <类型 = 整数>
                命中URL = ""
                候选条数 = 0
                循环判断首 ()
                {
                    解析JSON = MCP命令服务器.查找CDP请求ID (目标URL)
                    变量 解析对象 <类型 = YYJSON只读对象类>
                    如果 (解析对象.创建自文本 (解析JSON))
                    {
                        requestId = MCP命令服务器.yyjson取文本 (解析对象, "requestId")
                        命中URL = MCP命令服务器.yyjson取文本 (解析对象, "url")
                        候选条数 = MCP命令服务器.yyjson取整数 (解析对象, "count")
                    }
                    如果 (requestId != "")
                    {
                        跳出循环
                    }
                    // 只给了 url 时才等: 等的就是"这一条请求出现", 没给 url 时等下去没有意义
                    如果 (目标URL == "" || 取启动时间 () >= 等待截止)
                    {
                        跳出循环
                    }
                    MCP命令服务器.MCP可中断延时 (250)
                }
                循环判断尾 (真)
                如果 (requestId == "")
                {
                    变量 失败前缀 <类型 = 文本型>
                    失败前缀 = "未能在本会话的 CDP 捕获里解析到 requestId"
                    如果 (目标URL != "")
                    {
                        失败前缀 = 失败前缀 + "(按 url=" + 目标URL + " 未命中)"
                    }
                    失败前缀 = 失败前缀 + " | 本次捕获到的请求条数: " + 到文本 (候选条数)
                    如果 (解析说明 != "")
                    {
                        失败前缀 = 失败前缀 + " | 已自动补齐: " + 解析说明
                    }
                    返回 (MCP_响应构建.命令失败 (命令ID, 失败前缀 + " | 如实说明: 响应体只能对**本 CDP 会话内、捕获开启之后**发生的请求取回 —— 请重新加载页面(或重发该请求)后再调用本工具; 也可显式传 request_id(取自 browser_cdp_event event_name=Network.requestWillBeSent 或 browser_kernel_cdp_monitor action=list 的 events_json)"))
                }
                解析说明 = 解析说明 + "requestId 已自动解析(url=" + 命中URL + ", 捕获请求数=" + 到文本 (候选条数) + ")"
            }'''

CORE_RESULT_OLD = '            body结果.加入文本成员 ("request_id", requestId)'
CORE_RESULT_NEW = '''            body结果.加入文本成员 ("request_id", requestId)
            如果 (解析说明 != "")
            {
                body结果.加入文本成员 ("resolve_note", 解析说明)
            }'''

CORE_ALIAS_OLD = '''            如果 (action == "enable" || action == "network_enable")'''
CORE_ALIAS_NEW = '''            如果 (action == "body" || action == "network_body")
            {
                // 入口别名: 直接转交同一分派, 不在这里重写一份取响应体逻辑(不重复造轮子)
                返回 (分类分派_核心操作 (命令ID, "browser_network_body", 参数JSON))
            }
            如果 (action == "enable" || action == "network_enable")'''


def balance(text):
    ob = cb = op = cp = 0
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('@') or s.startswith('//') or s.startswith('#'):
            continue
        i, instr = 0, False
        while i < len(ln):
            c = ln[i]
            if c == '"':
                instr = not instr
            elif not instr:
                if ln.startswith('//', i):
                    break
                if c == '{':
                    ob += 1
                elif c == '}':
                    cb += 1
                elif c == '(':
                    op += 1
                elif c == ')':
                    cp += 1
            i += 1
    return ob - cb, op - cp


def patch(path, edits, name):
    raw = io.open(path, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '%s 带 BOM' % name
    txt = raw.decode('utf-8')
    b0 = balance(txt)
    n0 = len(txt.split('\n'))
    out = txt
    for old, new in edits:
        cnt = out.count(old)
        assert cnt == 1, '%s 锚点出现 %d 次: %s' % (name, cnt, old.strip()[:60])
        out = out.replace(old, new, 1)
    b1 = balance(out)
    assert b0 == b1, '%s 括号净值变了 %s -> %s' % (name, b0, b1)
    print('%s: 行数 %d -> %d; 括号净值 %s 不变' % (name, n0, len(out.split('\n')), b1))
    return raw, out


def main():
    s_raw, s_out = patch(SERVER, [(ANCHOR_HELPER, HELPERS + ANCHOR_HELPER),
                                  (BODY_OLD, BODY_NEW),
                                  (NET_OLD, NET_NEW)], 'MCP_Server.wsv')
    c_raw, c_out = patch(CORE, [(CORE_GUARD_OLD, CORE_GUARD_NEW),
                                (CORE_RESULT_OLD, CORE_RESULT_NEW),
                                (CORE_ALIAS_OLD, CORE_ALIAS_NEW)], 'MCP_Server_Core.wsv')

    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(s_out)
        io.open(CORE, 'w', encoding='utf-8', newline='\n').write(c_out)
        chk_s = io.open(SERVER, encoding='utf-8').read()
        chk_c = io.open(CORE, encoding='utf-8').read()
        assert '方法 确保网络CDP捕获' in chk_s and '方法 查找CDP请求ID' in chk_s
        assert 'action == "body" || action == "network_body"' in chk_c
        assert 'MCP命令服务器.查找CDP请求ID (目标URL)' in chk_c
        assert '\r' not in chk_s
        assert (b'\r' in io.open(CORE, 'rb').read()) == (b'\r' in c_raw)
        print('已写入 Server + Core 并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
