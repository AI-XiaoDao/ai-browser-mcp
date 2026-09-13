# -*- coding: utf-8 -*-
import importlib.util, sys, time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)
print("=== browser_set_zoom 各输入实测 ===")
for label, args in (("空 {} ", {}),
                    ("level=1.5", {"level": 1.5}),
                    ("level='1.5'", {"level": "1.5"}),
                    ("level=0", {"level": 0}),
                    ("level='abc'", {"level": "abc"}),
                    ("无关键", {"foo": 1})):
    e,t,_ = v4.call("browser_set_zoom", args, 30)
    print("  %-14s err=%-5s %s" % (label, e, t.replace("\n"," ")[:130]))
    time.sleep(0.3)
print()
print("=== get_zoom 读回实际缩放 ===")
e,t,_ = v4.call("browser_get_zoom", {}, 30)
print("  err=%s %s" % (e, t.replace("\n"," ")[:140]))
print()
print("=== 还原 level=1.0 ===")
e,t,_ = v4.call("browser_set_zoom", {"level": 1.0}, 30)
print("  err=%s %s" % (e, t.replace("\n"," ")[:140]))
