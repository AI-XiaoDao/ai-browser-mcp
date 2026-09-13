# -*- coding: utf-8 -*-
"""g0_snapshot.py — 把当前 src/*.wsv 冻结成本次审计的只读快照 (写入 _audit/_ghost_snapshot/).
不改动 src/ 下任何文件; 快照文件名带 .snapshot.txt 后缀, 防止被 IDE/编译器误当源码。
"""
import hashlib
import json
import os
import shutil
import time
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

ROOT = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp"
SRC = os.path.join(ROOT, "src")
DST = os.path.join(ROOT, "_audit", "_ghost_snapshot")
os.makedirs(DST, exist_ok=True)

manifest = {"snapshot_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "files": {}}
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".wsv") or "~vbak" in fn:
        continue
    p = os.path.join(SRC, fn)
    data = open(p, "rb").read()
    h = hashlib.md5(data).hexdigest()
    st = os.stat(p)
    manifest["files"][fn] = {
        "md5": h,
        "bytes": len(data),
        "lines": data.decode("utf-8", "replace").count("\n") + 1,
        "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
    }
    with open(os.path.join(DST, fn + ".snapshot.txt"), "wb") as f:
        f.write(data)

with open(os.path.join(DST, "_manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
print(json.dumps(manifest, ensure_ascii=False, indent=1))
