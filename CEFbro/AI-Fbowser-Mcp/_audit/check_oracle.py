import importlib.util, sys, time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)
v4.call("browser_navigate", {"url":"https://example.com/","wait_for_load":True}, 60); time.sleep(1.2)
for mod, fn in (("probe_native_reads.py","oracle"),("probe_coercion.py","oracle"),("probe_writes.py","oracle")):
    s=importlib.util.spec_from_file_location(mod.replace(".py",""), mod)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
    v = getattr(m, fn)("document.querySelector('h1').textContent")
    print("  %-24s oracle -> %r" % (mod, v))
