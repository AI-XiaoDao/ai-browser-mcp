# -*- coding: utf-8 -*-
"""把三个套件里的预言机统一改为"解包 message 信封"。

背景: browser_execute_js 已改为 CDP 优先, 返回**同步信封**
  {"id":"1","success":true,"message":"<值>"}
(与 browser_dom_query 等兄弟工具一致; 原异步链路返回的是裸值, 属少数派形态)。
预言机若不解包, 就会把信封整串当成值, 造成大面积误报。
"""
import io, re, os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

FILES = ["probe_native_reads.py", "probe_coercion.py", "probe_writes.py"]
UNWRAP = '''    import json as _json
    def _unwrap(s):
        s = (s or "").strip()
        try:
            j = _json.loads(s)
            if isinstance(j, dict) and "message" in j:
                return str(j["message"])
        except Exception:
            pass
        return s.strip('"')
'''

for fn in FILES:
    src = io.open(fn, encoding="utf-8").read()
    if "_unwrap" in src:
        print("  %-26s 已处理, 跳过" % fn)
        continue
    # 在每个预言机函数体开头插入解包助手, 并把最终返回改为解包
    n = 0
    for marker in ("def oracle(", ):
        idx = src.find(marker)
        if idx == -1:
            continue
        brace = src.find("\n", src.find('"""', src.find('"""', idx) + 3))  # 跳过 docstring
        # 找到函数体第一行(粗略: def 行之后第一个非注释行前插入)
        body_start = src.find("\n", idx) + 1
        src = src[:body_start] + UNWRAP + src[body_start:]
        n += 1
    # 把裸返回改成解包返回
    src = src.replace("return v.strip().strip('\"')", "return _unwrap(v)")
    src = src.replace("return t.strip().strip('\"')", "return _unwrap(t)")
    src = src.replace("return t.strip()", "return _unwrap(t)")
    io.open(fn, "w", encoding="utf-8").write(src)
    print("  %-26s 已注入解包助手(%d 处)" % (fn, n))
