# -*- coding: utf-8 -*-
r"""第126轮: 把"MCP HTTP 通道 ~1MB 请求体上限"从**静默断连**变成**可行动错误**。

实测(本轮, `_audit/probe_arg_size_limit.py`):
  · 入参 0.06 / 0.25 / 0.50 / 0.59 / 0.68 / 0.78 / 0.88 / 0.96 / 0.98 / 0.99 / 1.00(1020KB) MB 全部成功;
  · 入参 **1024KB(=1,048,576 字节填充)** 时客户端收到 `RemoteDisconnected: Remote end closed connection
    without response` —— 服务端**直接关连接, 不给任何响应**;
  · 失败后实例仍健康(`health_check` 最慢 0.04s) ⇒ 不是卡死, 是**传输层容量边界**。
成因: 本项目自己的上限是 50MB(`读取HTTP_POST体` 里 `MCP_常量.WS最大消息字节`), 故 1MB 这道墙在
  **类库/CEF 的 HTTP 请求体投递**上(类库无对应可调参数, 已在 FBroLib 里核对过 HTTP 服务器相关方法)。
为什么必须处理: 这种失败对 AI 代理是最坏的一种 —— **没有错误码、没有正文**, 客户端只能看到连接被关,
于是"重试/换个方法试试", 正是用户抱怨的体验。故在读到正文**之前**用 Content-Length 拦下,
回一个标准 JSON-RPC 错误, 把上限、实测症状与两条可行替代(WebSocket 50MB / stdio)说清楚。

落地: `MCP_Server_HTTP.wsv` 的 POST /mcp 分支加前置守卫(该文件归主代理)。
用法: py -3 _audit\_apply_http_body_guard.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTTP = os.path.join(ROOT, 'src', 'MCP_Server_HTTP.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

HELPER_ANCHOR = '    方法 读取HTTP_POST体 <公开 静态 类型 = 文本型 @输出名 = "ReadHTTPPOSTBody" @强制输出 = 真>'

HELPER = '''    # 取请求头里的整数值(用于在**读正文之前**按 Content-Length 做容量守卫)
    # 为什么需要: 第126轮实测 MCP HTTP 通道在 ~1MB 请求体处会被内核直接断开连接, 客户端只能看到"无响应";
    #   要提前拒绝就必须能在不读正文的情况下拿到声明长度 —— 头信息是唯一途径。

    方法 取请求头整数值 <公开 静态 类型 = 长整数 @输出名 = "GetRequestHeaderIntValue" @强制输出 = 真>
    参数 请求 <类型 = 类_FBrowser_请求 @输出名 = "Request">
    参数 头名 <类型 = 文本型 @输出名 = "HeaderName">
    {
        如果 (请求.是否为空 () || 头名 == "")
        {
            返回 (0)
        }
        变量 目标头名 <类型 = 文本型>
        目标头名 = 到小写 (删首尾空 (头名))
        变量 头数组 <类型 = FBrowser_双文本数组>
        头数组 = 请求.取协议头数据 ()
        如果 (头数组.取个数 () <= 0)
        {
            返回 (0)
        }
        头数组.到数组首 ()
        变量 继续 <类型 = 逻辑型 值 = 真>
        循环判断首 ()
        {
            变量 当前头 <类型 = FBrowser_双文本>
            当前头 = 头数组.取当前位置数据 ()
            如果 (到小写 (删首尾空 (当前头.name)) == 目标头名)
            {
                变量 原始值 <类型 = 文本型>
                原始值 = 删首尾空 (当前头.value)
                变量 首位 <类型 = 文本型>
                首位 = ""
                如果 (取文本长度 (原始值) > 0)
                {
                    首位 = 取文本左边 (原始值, 1)
                }
                // 只接受纯数字开头(Content-Length 规范形态); 其它形态(如带逗号的多值)一律当 0 处理, 不猜
                如果 (首位 != "" && 寻找文本 ("0123456789", 首位, 0, 假) != -1)
                {
                    返回 (文本到长整数 (原始值))
                }
                返回 (0)
            }
            继续 = 头数组.到下一个 ()
        }
        循环判断尾 (继续)
        返回 (0)
    }

'''

OLD = '''                变量 请求体JSON <类型 = 文本型>
                请求体JSON = MCP命令服务器.读取HTTP_POST体 (请求)
                如果 (请求体JSON != "")'''

NEW = '''                // ★ 前置守卫(第126轮实测): 本机 MCP HTTP 通道在请求体约 **1MB** 处会被内核直接断开连接,
                //   客户端只看到"无响应"(RemoteDisconnected), **拿不到任何错误码与正文** —— 对 AI 代理是最坏的
                //   失败形态(只能重试/换方法)。故在**读正文之前**按 Content-Length 先拦下, 回标准 JSON-RPC 错误。
                //   实测边界: 1020KB 通过, 1024KB(=1,048,576 字节)失败; 本项目自身上限是 50MB, 那道墙在类库/CEF 侧。
                变量 声明长度 <类型 = 长整数>
                声明长度 = MCP命令服务器.取请求头整数值 (请求, "content-length")
                如果 (声明长度 > MCP_常量.HTTP请求体安全上限)
                {
                    变量 超限对象 <类型 = YYJSON对象类>
                    超限对象.创建自文本 ("{}")
                    超限对象.加入文本成员 ("jsonrpc", "2.0")
                    超限对象.加入文本成员 ("error", "请求体过大: Content-Length=" + 到文本 (声明长度) + " 字节, 超过本通道安全上限 " + 到文本 (MCP_常量.HTTP请求体安全上限) + " 字节 | **实测**: 本机 MCP HTTP 通道在约 1MB(1,048,576 字节)处会被内核直接断开连接 —— 客户端只能看到\\"无响应\\", **不会有错误码**, 故本服务在读到正文前就拒绝, 以免你把它当成随机故障反复重试 | 可行替代: ①把大参数拆小(如分片执行/分段写入) ②改用 WebSocket 通道 ws://<host>:<port>/mcp(上限 50MB) 或 stdio 通道(经 mcp_bridge.js) ③大文件请用文件路径类参数而不是把内容塞进 arguments")
                    超限对象.加入长整数成员 ("content_length", 声明长度)
                    超限对象.加入长整数成员 ("safe_limit", MCP_常量.HTTP请求体安全上限)
                    超限对象.加入文本成员 ("id", "")
                    MCPStdio桥.写日志 ("[MCP] ⚠️ 拒绝超限请求体: Content-Length=" + 到文本 (声明长度))
                    变量 超限字节集 <类型 = 字节集类>
                    超限字节集 = 文本到UTF8 (超限对象.到可读文本 (YYJSON格式化选项.压缩), 假)
                    MCP命令服务器.发送CORS200响应 (服务器, 连接ID, MCP_常量.HTTP_JSON内容类型, 取字节集指针 (超限字节集), 取字节集长度 (超限字节集))
                    返回
                }
                变量 请求体JSON <类型 = 文本型>
                请求体JSON = MCP命令服务器.读取HTTP_POST体 (请求)
                如果 (请求体JSON != "")'''


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


def main():
    # ① MCP_Server.wsv: 新增 取请求头整数值 复用件
    sraw = io.open(SERVER, 'rb').read()
    stxt = sraw.decode('utf-8')
    assert '\r' not in stxt, 'MCP_Server.wsv 应为纯 LF'
    sb0 = balance(stxt)
    assert '方法 取请求头整数值' not in stxt, '已改过'
    assert stxt.count(HELPER_ANCHOR) == 1, '辅助锚点 %d' % stxt.count(HELPER_ANCHOR)
    sout = stxt.replace(HELPER_ANCHOR, HELPER + HELPER_ANCHOR, 1)
    assert balance(sout) == sb0, 'Server 括号净值变了 %s -> %s' % (sb0, balance(sout))
    print('MCP_Server.wsv: 行数 %d -> %d; 括号净值 %s 不变'
          % (len(stxt.split('\n')), len(sout.split('\n')), balance(sout)))

    # ② MCP_Server_HTTP.wsv: POST /mcp 前置容量守卫
    raw = io.open(HTTP, 'rb').read()
    has_cr = b'\r' in raw
    txt = raw.decode('utf-8')
    b0, n0 = balance(txt), len(txt.split('\n'))
    assert txt.count(OLD) == 1, '锚点 %d 次' % txt.count(OLD)
    assert 'HTTP请求体安全上限' not in txt, '已改过'
    out = txt.replace(OLD, NEW, 1)
    assert balance(out) == b0, '括号净值变了 %s -> %s' % (b0, balance(out))
    print('MCP_Server_HTTP.wsv: 行数 %d -> %d (行尾 CR=%s); 括号净值 %s 不变'
          % (n0, len(out.split('\n')), has_cr, balance(out)))
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(sout)
        io.open(HTTP, 'w', encoding='utf-8', newline='\n').write(out)
        chk = io.open(HTTP, encoding='utf-8').read()
        assert '取请求头整数值 (请求, "content-length")' in chk
        assert ('\r' in chk) == has_cr, '行尾风格被改变'
        schk = io.open(SERVER, encoding='utf-8').read()
        assert '方法 取请求头整数值' in schk and '\r' not in schk
        print('已写入 Server + HTTP 并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
