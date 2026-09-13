# -*- coding: utf-8 -*-
"""从 _audit/_tools_list.json 打印指定工具的 schema。用法: py -3 _audit/show_schema.py 工具名 [工具名...]"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_tools_list.json')


def main(argv):
    with io.open(P, encoding='utf-8') as f:
        data = json.load(f)
    idx = {t.get("name"): t for t in data.get("tools") or []}
    if not argv:
        print("共 %d 个工具" % len(idx))
        return 0
    for name in argv:
        t = idx.get(name)
        if not t:
            print("\n== %s: 不存在 ==" % name)
            continue
        sch = t.get("inputSchema") or {}
        props = sch.get("properties") or {}
        req = sch.get("required") or []
        print("\n== %s ==" % name)
        print("   required: %s" % (req if req else "(无)"))
        for pn, ps in props.items():
            ps = ps or {}
            mark = "*" if pn in req else " "
            print("   %s %-16s type=%-8s %s"
                  % (mark, pn, ps.get("type"), (ps.get("description") or "")[:110]))
        if not props:
            print("   (无参数)")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
