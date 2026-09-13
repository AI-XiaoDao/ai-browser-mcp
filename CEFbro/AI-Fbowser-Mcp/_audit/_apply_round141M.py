# -*- coding: utf-8 -*-
r"""第141轮补丁 M: `browser_screenshot` 的 `from_surface` 默认改真 —— 实测"截的是窗口, 传的宽高被忽略"。

## 三臂实测(每臂独立重启, 判据 = **PNG 头解析出的像素尺寸**, 不看回包文案)
| 臂 | 参数 | 得到的图片 |
|---|---|---|
| A | 默认(第4参=假) + width/height=800×600 | **(984, 705)** —— 宽高**被忽略**, 拿到的是窗口/视口那一屏 |
| B | **from_surface=true** + 800×600 | **(800, 600)** ✅ rect 生效 |
| C | from_surface=true + full_page(页面 scrollHeight=5350) | **(984, 5350)** ✅ 整页生效, 高度与 scrollHeight 完全一致 |

⇒ 类库第 4 参 `是否表面`(fromSurface) 决定"截 view(窗口) 还是 surface(按 rect 的区域)";
项目把它**写死成假**, 于是工具对外宣称的 `width/height/x/y/scale` 一直**静默无效** ——
又一次"承诺了却没生效"。默认改真即可让 rect 与 captureBeyondViewport 同时可用;
想回到旧的"只截窗口可见区"行为, 显式传 `from_surface:false`。

用法: py -3 _audit\_apply_round141M.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

CORE_OLD = '''                    变量 从表面截图 <类型 = 逻辑型>
                    从表面截图 = MCP命令服务器.yyjson取逻辑 (参数JSON, "from_surface")'''
CORE_NEW = '''                    // ★ 默认**必须为真**(实测三臂): 第4参(fromSurface)为假时, 类库截的是 **view(窗口可见区)**,
                    //   传入的 width/height/x/y/scale **全部被忽略** —— 实测 800x600 请求拿到的是 984x705(窗口客户区)。
                    //   置真后: ①rect 生效(800x600 → 800x600) ②captureBeyondViewport 生效(整页 → 高度=scrollHeight=5350)。
                    //   想回到旧的"只截窗口可见区"行为请显式传 from_surface:false。
                    变量 从表面截图 <类型 = 逻辑型>
                    从表面截图 = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "from_surface", 真)'''

DESC_OLD = '''from_surface(从表面而非视图捕获)'''
DESC_NEW = '''from_surface(**默认真**, 实测关键项: 为假时类库截的是"窗口可见区"且**宽高/缩放全被忽略** —— 800x600 的请求会拿到 984x705; 为真时 rect 生效。想只截窗口可见区请显式传 false)'''

SCHEMA_OLD = '''属性项JSON ("from_surface", "boolean", "从表面而非视图捕获(fromSurface)")'''
SCHEMA_NEW = '''属性项JSON ("from_surface", "boolean", "默认 true; false=只截窗口可见区(此时 width/height/scale 会被忽略, 实测)")'''

EDITS = [(CORE, 'M1 from_surface 默认改真', CORE_OLD, CORE_NEW),
         (SERVER, 'M2 描述补实测口径', DESC_OLD, DESC_NEW),
         (SERVER, 'M3 schema 说明默认真', SCHEMA_OLD, SCHEMA_NEW)]


def main():
    print('== 第141轮补丁 M (%s) ==' % ('应用' if APPLY else '预演'))
    cache = {}
    for path, tag, old, new in EDITS:
        if path not in cache:
            cache[path] = io.open(path, encoding='utf-8', newline='').read()
        txt = cache[path]
        if old not in txt:
            print('   · %-32s 锚点未找到(可能已应用)' % tag)
            continue
        assert txt.count(old) == 1, '%s: 命中 %d 次' % (tag, txt.count(old))
        cache[path] = txt.replace(old, new, 1)
        print('   · %s' % tag)
    for path, txt in cache.items():
        print('%s: 行数 %d' % (os.path.basename(path), len(txt.split('\n'))))
        if APPLY:
            io.open(path, 'w', encoding='utf-8', newline='').write(txt)
    if APPLY:
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
