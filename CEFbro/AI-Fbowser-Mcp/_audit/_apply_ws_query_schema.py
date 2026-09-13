# -*- coding: utf-8 -*-
r"""第130轮(其二): `browser_reverse_websocket` —— 声明它真读的 `request_id`，并把 `query` 的真实语义写清。

依据(本轮 `_audit/_show_branch_params.py --diff` 实测 + 源码核实 MCP_Server_Reverse.wsv:801-869):
  · 分支读 `action` / `request_id`(另有 `requestId` 写法) → schema 只声明了 `action` ⇒ **MISSING 2**;
  · `action=query` 实际调用的是 **`Network.getResponseBody`**(源码 863 行), 即取"某条请求的**响应体**",
    而工具描述写的是"WebSocket消息拦截/监听所有WS帧" —— 对 `query` 这一支**文实不符**,
    调用方会以为拿到的是解码后的 WS 帧。已按实现如实改写描述（enable 走 WS 帧订阅, query 走响应体）。

用法: py -3 _audit\_apply_ws_query_schema.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

DESC_OLD = '"CDP逆向: WebSocket消息拦截。Network.enable+webSocketFrameReceived—监听所有WS帧(send/receive),用于分析实时通信协议"'
DESC_NEW = ('"CDP逆向: WebSocket 通信分析 | **两个 action 语义不同(如实说明)**: '
            '① action=enable(缺省): Network.enable + webSocketFrameReceived, 订阅**所有 WS 帧**(send/receive)供 browser_event 读取; '
            '② action=query: 实际调用 **Network.getResponseBody** 取**某条请求的响应体文本**(需要 request_id, 取自 '
            'Network.requestWillBeSent 事件; 也可用 browser_network_body 的同名参数自动解析) —— 它**不是**解码后的 WS 帧, '
            '旧描述把 query 也写成\'监听所有WS帧\'属文实不符, 已更正"')

SCHEMA_OLD = '单参数Schema文本 ("action", "text", "enable(默认)/query")'
SCHEMA_NEW = ('多属性Schema文本 (属性项JSON ("action", "text", "enable(默认, 订阅WS帧)/query(取某条请求的响应体, 需 request_id)") + "," + '
              '属性项JSON ("request_id", "text", "action=query 必填: CDP 请求ID(来自 Network.requestWillBeSent 事件); '
              '也可先用 browser_network_body 按 url 自动解析出 id"), "\\"action\\"")')


def main():
    txt = io.open(SERVER, encoding='utf-8').read()
    assert '\r' not in txt
    lines = txt.split('\n')
    idx = [i for i, ln in enumerate(lines) if '添加工具JSON ("browser_reverse_websocket"' in ln]
    assert len(idx) == 1, '注册行 %d' % len(idx)
    i = idx[0]
    for tag, old, new in (('schema', SCHEMA_OLD, SCHEMA_NEW), ('描述', DESC_OLD, DESC_NEW)):
        if new in lines[i]:
            print('   · %s (已存在)' % tag)
            continue
        assert lines[i].count(old) == 1, '%s 锚点 %d' % (tag, lines[i].count(old))
        lines[i] = lines[i].replace(old, new, 1)
        print('   · %s' % tag)
    out = '\n'.join(lines)
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        assert '"request_id"' in c and 'Network.getResponseBody' in c and '\r' not in c
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
