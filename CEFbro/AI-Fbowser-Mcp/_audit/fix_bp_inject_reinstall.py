# -*- coding: utf-8 -*-
"""修我自己的前置注入: 幂等判据撒谎导致"注入成功但定时器已死"。

缺陷(实测): 注入脚本的幂等判据是 `if(window.mcpBpTimer)return 'exists';`
—— 但只要有人 `clearInterval(window.mcpBpTimer)`, 那个变量**仍然是个数字(真值)**,
于是判据认为"已注入"而**跳过重装**, 而定时器其实已经死了 -> 断点永远 0 命中。
表现与产品缺陷一模一样, 实际是我的测试前置自己坏掉了。

修法: **无条件重装** —— 先清掉可能存在的旧定时器, 再注入一份全新脚本。
这样无论之前有没有被 clear/导航, 前置都保证"脚本在册且定时器在跑"。

注意: 位置必须放在 mass_probe.py 里 `_BP_INJECT` 定义**之后**(用重新赋值的方式),
避免上一轮那种"定义顺序"问题。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP = os.path.join(ROOT, '_audit', 'mass_probe.py')
BAK = os.path.join(ROOT, '备份', '断点前置无条件重装-写入前')

APPEND = '''

# 修正上面的 _BP_INJECT: 幂等判据不可靠(clearInterval 后变量仍是真值 -> 跳过重装 -> 定时器已死),
# 改为**无条件重装**: 先清旧定时器, 再注入新脚本。放在定义之后重新赋值, 不依赖顺序。
_BP_INJECT = ("browser_execute_js", {
    "code": ("(function(){if(window.mcpBpTimer){try{clearInterval(window.mcpBpTimer)}catch(e){}}"
             "var s=document.createElement('script');s.textContent=%s;"
             "document.body.appendChild(s);return 'installed'})()"
             % __import__('json').dumps(_BP_PROBE_SRC))})
# 前置链里引用的是同一个名字, 重新注册一遍确保取到新值
for _t in ("browser_debugger_auto", "browser_debugger_flow",
           "browser_reverse_return_value", "browser_reverse_set_variable"):
    _chain = list(TOOL_PRE_CALLS.get(_t) or [])
    TOOL_PRE_CALLS[_t] = [(n, (_BP_INJECT[1] if n == "browser_execute_js" else a)) for n, a in _chain]
'''


def main():
    t = io.open(MP, encoding='utf-8', newline='').read()
    if '无条件重装' in t:
        print("!! 似乎已改过, 中止")
        return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(MP, os.path.join(BAK, os.path.basename(MP)))
    print("已备份到 %s" % BAK)
    io.open(MP, 'w', encoding='utf-8', newline='').write(t + APPEND)
    print("OK: 注入改为无条件重装")
    sys.path.insert(0, os.path.dirname(MP))
    import importlib
    mp = importlib.import_module('mass_probe')
    print("自检: import 成功")
    print("自检: auto 前置 = %s" % [x[0] for x in mp.TOOL_PRE_CALLS.get('browser_debugger_auto', [])])
    code = mp.TOOL_PRE_CALLS['browser_debugger_auto'][1][1]['code']
    print("自检: 注入码含 clearInterval = %s ; 含 installed = %s"
          % ('clearInterval' in code, 'installed' in code))
    return 0


if __name__ == '__main__':
    sys.exit(main())
