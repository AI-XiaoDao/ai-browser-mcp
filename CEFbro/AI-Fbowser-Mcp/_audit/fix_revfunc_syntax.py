# -*- coding: utf-8 -*-
"""修 browser_kernel_reverse_functions 的"必失败"缺陷: 注入 JS 自身语法错误。

## 根因(独立子代理离线 V8 复现 + 逐字证据)
`MCP_Kernel.wsv` 里 `分派_函数提取` 的注入代码是**无任何换行的单行串**, 而 `[...].forEach(...)`
之后漏写语句终结符, 于是 ASI(自动分号插入)因"整行没有行终结符"无法生效:
  ① `...}})}catch(e){}})['XMLHttpRequest','WebSocket',...]`
     —— `forEach` 的 `)` 后直接跟 `[`, 被解析成"对 forEach 返回值取下标"
        (`[].forEach()` 返回 undefined → TypeError: Cannot read properties of undefined)
  ② `...}catch(e){}})return out.slice(0,MAX)`
     —— `)` 后直接跟 `return` → 解析期 SyntaxError: Unexpected token 'return'
②发生在解析期, 所以**页面一行代码都没执行**就失败了 —— 这就是它 100% 必失败、而近亲
`reverse_probe/algo/sources` 全通过的原因(那些工具的语句以 `}` 结尾或用 `;` 分隔)。

## 同时纠正文案
原失败文案把原因写成"页面可能因 CSP 拒绝脚本注入, 或已跨域跳转" —— 属**误导**:
CDP 的 `Runtime.evaluate` 不受页面 CSP 约束, 且失败在解析期。改为指向真实可能原因。

自带校验: 两处锚点必须各命中 1 次, 否则中止(避免改错位置)。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, "src", "MCP_Kernel.wsv")

S = io.open(P, encoding="utf-8").read()
orig = S

# ---- ① forEach 之后接数组字面量: 补分号 ----
A_OLD = "}})}catch(e){}})['XMLHttpRequest'"
A_NEW = "}})}catch(e){}});['XMLHttpRequest'"
n1 = S.count(A_OLD)
if n1 != 1:
    print("!! 锚点①命中 %d 次(应 1) -> 中止" % n1)
    sys.exit(2)
S = S.replace(A_OLD, A_NEW)
print("已修 ① forEach 后接 '[' (补分号)")

# ---- ② forEach 之后接 return: 补分号 ----
B_OLD = "}})return out.slice(0,MAX)"
B_NEW = "}});return out.slice(0,MAX)"
n2 = S.count(B_OLD)
if n2 != 1:
    print("!! 锚点②命中 %d 次(应 1) -> 中止" % n2)
    sys.exit(2)
S = S.replace(B_OLD, B_NEW)
print("已修 ② forEach 后接 return (补分号)")

# ---- ③ 纠正误导性文案(3 处, 两种变体) ----
# 为何要改: 失败文案把原因写成"页面可能因 CSP 拒绝脚本注入" —— 属**误导**。
# 这些工具都经 CDP 的 Runtime.evaluate 注入, **不受页面 CSP 约束**; 而实测的失败原因
# 恰恰是注入脚本自身的语法错误(见 ①②)。把归因写错会把排查方向带偏(本项目已为此浪费过时间)。
C1_OLD = '页面可能因 CSP 拒绝脚本注入, 或已跨域跳转'
C1_NEW = ('注入脚本自身执行失败(说明: 本工具经 CDP 求值注入, **不受页面 CSP 约束**, 故通常不是 CSP 问题; '
          '若为语法/解析类错误则属本工具注入脚本缺陷, 重试无意义, 请改用 '
          'browser_reverse_search_script / browser_kernel_reverse_sources 交叉确认)')
n3 = S.count(C1_OLD)
if n3 != 2:
    print("!! 文案锚点①命中 %d 次(应 2: 探针 + 函数提取) -> 中止" % n3)
    sys.exit(2)
S = S.replace(C1_OLD, C1_NEW)
print("已修 ③-1 探针/函数提取 的误导文案(2 处)")

C2_OLD = '页面可能因 CSP 拒绝脚本注入; 若页面未使用 CryptoJS/WebCrypto, Hook 本身仍应注入成功'
C2_NEW = ('注入脚本自身执行失败(说明: 经 CDP 求值注入, **不受页面 CSP 约束**; 若为语法/解析类错误则属'
          '本工具注入脚本缺陷, 重试无意义) | 另: 页面未使用 CryptoJS/WebCrypto 时 Hook 本身仍应注入成功, '
          '故本项失败与页面是否用这些库无关')
n4 = S.count(C2_OLD)
if n4 != 1:
    print("!! 文案锚点②命中 %d 次(应 1: 算法Hook) -> 中止" % n4)
    sys.exit(2)
S = S.replace(C2_OLD, C2_NEW)
print("已修 ③-2 算法Hook 的误导文案(1 处)")

io.open(P, "w", encoding="utf-8", newline="\n").write(S)

# ---- 写后自检 ----
chk = io.open(P, encoding="utf-8").read()
bad = 0
for label, s, want in (("① 修复后形态", A_NEW, 1), ("② 修复后形态", B_NEW, 1),
                       ("旧形态①残留", A_OLD, 0), ("旧形态②残留", B_OLD, 0),
                       ("③ 新文案", "不受页面 CSP 约束", 3),
                       ("③ 旧文案残留", "CSP 拒绝脚本注入", 0)):
    c = chk.count(s)
    ok = (c == want)
    print("自检 %-16s 出现 %d 次 (期望 %d) %s" % (label, c, want, "OK" if ok else "!!"))
    if not ok:
        bad += 1
print("OK" if bad == 0 else "!! %d 项自检未通过" % bad)
sys.exit(1 if bad else 0)
