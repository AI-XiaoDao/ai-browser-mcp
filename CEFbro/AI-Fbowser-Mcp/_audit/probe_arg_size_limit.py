# -*- coding: utf-8 -*-
r"""量"MCP HTTP 传输层能承载多大的 arguments" —— 上一轮 verify_urlreq_upload 用 3MB body 时
连接被服务端直接关闭(RemoteDisconnected, 无任何响应), 需判定是**传输层容量上限**还是那个工具的问题。

做法: 对一个**无害且与大小无关**的工具(`browser_execute_js`, 把填充放进注释)逐步加大入参,
记录每个尺寸的结果; 第一个失败点即实际容量。失败时**打印原始异常**, 不写"失败"了事。
先测小尺寸, 一旦失败就停(避免把实例搞卡)。

用法: py -3 _audit\probe_arg_size_limit.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
# 允许命令行覆盖(便于二分定位): py -3 probe_arg_size_limit.py --kb 600 700 800 900
if "--kb" in sys.argv:
    SIZES = [int(x) * 1024 for x in sys.argv[sys.argv.index("--kb") + 1:]] or [64 * 1024]
else:
    SIZES = [64 * 1024, 256 * 1024, 512 * 1024, 1024 * 1024, 2 * 1024 * 1024]


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    data = json.dumps(b, ensure_ascii=False).encode("utf-8")
    r = urllib.request.Request(BASE + "/mcp", data=data,
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


print('== 逐步加大入参, 观察 MCP HTTP 传输层容量 ==')
for n in SIZES:
    code = "/*" + ("p" * n) + "*/ 1+1"
    try:
        e, t = call("browser_execute_js", {"code": code})
        print('   %8.2f MB -> err=%s %s' % (n / 1048576.0, e, t.replace('\n', ' ')[:60]))
    except Exception as ex:
        print('   %8.2f MB -> !! 异常: %r' % (n / 1048576.0, ex))
        print('   ⇒ 该尺寸已超出传输层能力, 停止加大(避免实例异常)')
        break
    # 每次返回后确认实例仍健康
    try:
        _e, _t = call("browser_status", {})
    except Exception as ex:
        print('   !! 之后实例已不可用: %r' % ex)
        break
