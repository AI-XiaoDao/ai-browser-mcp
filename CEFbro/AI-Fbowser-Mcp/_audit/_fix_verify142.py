# -*- coding: utf-8 -*-
r"""修 verify_round142 的两个**探针**缺陷(产品侧无问题, 实测已确认):
① 解析: 工具回包是 `{"id":..,"success":true,"data":{"root":{...}}}` —— `root` 在 `data` 里,
   上一版只看顶层 `root`, 于是把"拿到的树"当成 0 个节点(第 N 次栽在探针解析上);
② 顺序: `discard_search` 仍走类库开发者DOM 路线(唯一可能毒化通道的动作), 应放到**最后**测,
   否则它的副作用会污染前面的核心断言。
用法: py -3 _audit\_fix_verify142.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, '_audit', 'verify_round142.py')
APPLY = '--apply' in sys.argv

OLD = '''    if isinstance(o, dict) and "root" in o:
        return o["root"], ""
    return o if isinstance(o, dict) else None, "解析失败: %s" % txt[:120]'''
NEW = '''    # ⚠ 回包是 `{"id":..,"success":true,"data":{"root":{...}}}`: root 藏在 data 里(实测),
    #   上一版只看顶层 root ⇒ 解析成 0 个节点。这里逐层剥到 root 为止。
    层 = o
    for _ in range(4):
        if not isinstance(层, dict):
            break
        if "root" in 层:
            return 层["root"], ""
        nxt = 层.get("data")
        if isinstance(nxt, str):
            try:
                nxt = json.loads(nxt)
            except Exception:
                break
        if not isinstance(nxt, dict):
            break
        层 = nxt
    return (层 if isinstance(层, dict) else None), "解析失败: %s" % txt[:120]'''


def main():
    txt = io.open(V, encoding='utf-8', newline='').read()
    if OLD not in txt:
        print('· 锚点未找到(可能已改)')
        return
    assert txt.count(OLD) == 1, '命中 %d 次' % txt.count(OLD)
    txt = txt.replace(OLD, NEW, 1)
    print('· 已修 enumerate_dom 的 root 解析(支持 data 嵌套)')
    if APPLY:
        io.open(V, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入 verify_round142.py')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
