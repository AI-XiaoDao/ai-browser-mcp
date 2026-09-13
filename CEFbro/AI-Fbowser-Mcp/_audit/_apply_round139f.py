# -*- coding: utf-8 -*-
r"""第139轮补丁 F: 修"索引类行被**重复施加**"的缺陷(实测发现)。

## 实测现象(verify_menu_probe 22/22 那轮的回包)
规格 `item|MCP索引测试项|26501|1|0|` + `accelat||17|1|0|70C` + `accelat||0|1|0|70C` 施加后:
  · `verified_items = 2`(新建项 + 索引 17 的 accelat **确实生效了**, 说明按索引写通道可用);
  · 但 `apply_failed` 里出现 **两条本该不存在的** `[accel 17 未生效…]` / `[accel 0 未生效…]`。

## 根因
`应用菜单规格` 的类型分支之后还有一段**公共快捷键块**(给 `accel` 行用的), 它的条件是
`段数组.取成员数()>=6 && 第6列!="" && 条目类型!="sep" && 条目类型!="noaccel"` —— 于是索引类行(第6列有值)
会在自己的分支跑完后又落进这段, 把**索引当成命令ID**再设一次快捷键, 必然失败并污染 `apply_failed`。

## 修法
公共块加 `条目是索引类 == 假 && 条目类型 != "wipe"`(索引类的快捷键由自己的分支用 设置快捷键_索引 处理;
wipe 行没有快捷键概念)。修完 `apply_failed` 只剩**真实**失败(例如内核拒绝在默认菜单项上按索引改快捷键 —— 那是有价值的测量结论)。

用法: py -3 _audit\_apply_round139f.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

OLD = '''            如果 (段数组.取成员数 () >= 6 && 段数组.取成员 (5) != "" && 条目类型 != "sep" && 条目类型 != "noaccel")'''
NEW = '''            // ⚠ 索引类行**不能**再落进这段公共快捷键块: 它们第6列也有值, 但第3列是**索引**而不是命令ID,
            //   上面自己的分支已经用 设置快捷键_索引 处理过; 若在这里再按"命令ID"设一次, 必然失败并污染
            //   apply_failed(实测: 索引行生效了, 却额外多出两条 [accel N 未生效])。wipe 行同理无快捷键概念。
            如果 (段数组.取成员数 () >= 6 && 段数组.取成员 (5) != "" && 条目类型 != "sep" && 条目类型 != "noaccel" && 条目是索引类 == 假 && 条目类型 != "wipe")'''


def main():
    txt = io.open(SERVER, encoding='utf-8', newline='').read()
    if OLD not in txt:
        print('· 锚点未找到(可能已应用)')
    else:
        assert txt.count(OLD) == 1, '命中 %d 次' % txt.count(OLD)
        txt = txt.replace(OLD, NEW, 1)
        print('· 已给公共快捷键块加索引类/wipe 排除条件')
        if APPLY:
            io.open(SERVER, 'w', encoding='utf-8', newline='').write(txt)
            print('   ✔ 已写入')
        else:
            print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
