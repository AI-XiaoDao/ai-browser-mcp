# -*- coding: utf-8 -*-
"""把 browser_reverse_hook 其余 3 个模式(WS/EVAL/COOKIE)的 push/splice/slice.call 一次清干净。

上一脚本只锚定了 function_call 那一个模式; 残留检查当场发现 `__lg.push(` 还剩 4 处、
`__lg.splice` 还剩 3 处 —— 于是本轮补齐。

统一变换(比逐个锚定长 payload 更稳):
  · 在每个 `__lg=window.__X_LOG__=...||[];` 之后插入一个小追加器
        var __put=function(x){__lg[__lg.length]=x;};
  · 全局把 `__lg.push(` 换成 `__put(` —— **右括号保持不变**, 语法天然合法;
  · `__cap()` 里的 `__lg.splice(0,1000)` 换成"索引左移 + 改 length";
  · 剩下 1 处 `Array.prototype.slice.call(arguments)`(EVAL 模式构 Function)换成手写复制循环。
"""
import io
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', 'hook其余模式去push-写入前')

PUT_DEF = "var __put=function(x){__lg[__lg.length]=x;};"
CAP_OLD = "function __cap(){if(__lg.length>2000){__lg.splice(0,1000);}}"
CAP_NEW = ("function __cap(){if(__lg.length>2000){var __k=1000,__i9;"
           "for(__i9=0;__i9<__k;__i9++){__lg[__i9]=__lg[__lg.length-__k+__i9];}__lg.length=__k;}}")
SLICE_OLD = "var a=Array.prototype.slice.call(arguments);"
SLICE_NEW = "var __fn=arguments.length,a=[],__fi;for(__fi=0;__fi<__fn;__fi++){a[__fi]=arguments[__fi];}"
DEF_RE = re.compile(r'__lg=window\.__MCP_[A-Z_]+__=window\.__MCP_[A-Z_]+__\|\|\[\];')


def main():
    t = io.open(CORE, encoding='utf-8', newline='').read()
    n_push = t.count('__lg.push(')
    n_cap = t.count(CAP_OLD)
    n_slice = t.count(SLICE_OLD)
    n_def = len(DEF_RE.findall(t))
    print("变换前: __lg.push( = %d ; __cap(splice) = %d ; slice.call = %d ; __lg 定义锚点 = %d"
          % (n_push, n_cap, n_slice, n_def))
    if n_push == 0 or n_cap == 0 or n_def == 0:
        print("!! 预期数量不符, 中止")
        return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(CORE, os.path.join(BAK, os.path.basename(CORE)))
    print("已备份到 %s" % BAK)
    # 1) 定义锚点后插入追加器
    t2, cnt_def = DEF_RE.subn(lambda m: m.group(0) + PUT_DEF, t)
    # 2) push -> __put(  (右括号不动)
    t2, cnt_push = re.subn(re.escape('__lg.push('), '__put(', t2)
    # 3) cap 去 splice
    t2, cnt_cap = re.subn(re.escape(CAP_OLD), CAP_NEW.replace('\\', '\\\\'), t2)
    # 4) slice.call 去
    t2, cnt_slice = re.subn(re.escape(SLICE_OLD), SLICE_NEW.replace('\\', '\\\\'), t2)
    print("已替换: 定义插入 %d 处 ; push %d 处 ; cap %d 处 ; slice.call %d 处"
          % (cnt_def, cnt_push, cnt_cap, cnt_slice))
    io.open(CORE, 'w', encoding='utf-8', newline='').write(t2)
    print("OK 写入完成")
    with io.open(CORE, 'rb') as f:
        raw = f.read()
    print("复核: BOM=%s CRLF=%s 字节=%d"
          % (raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    for bad in ('__lg.push(', '__lg.splice(', 'Array.prototype.slice.call(arguments)'):
        print("   残留检查 %-38s = %s" % (bad, bad in t2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
