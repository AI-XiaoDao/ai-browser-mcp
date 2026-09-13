# -*- coding: utf-8 -*-
"""清掉注入自递归缺陷类**最后 2 处确认点** + 3 处 push/shift 隐患。

已修 4/6(前两轮): instrument、hook_multi、hook_logs 读路径(自动 + 单键)。
本轮:
 ⑤ browser_reverse_hook 的 function_call 模式 (MCP_Server_Core.wsv):
    · `Array.prototype.slice.call(arguments)` + `__orig.apply(...)` —— `.call`/`.apply` 是默认目标;
    · `__lg.push(__entry)` —— 若用户勾的就是 Array.prototype.push, 记录动作本身自递归;
    · `__cap()` 用 `__lg.splice`;
    · **`console.log(...)` 独立自指通路**: 若用户勾的对象就是 console.log, 包装器内部再调 console.log
      就会进自己 → 无限递归。修法: 安装前把**原始** console.log 存进 __rawLog, 包装器只调 __rawLog。
 ⑥ browser_kernel_reverse_trace (MCP_Kernel.wsv): `T.calls.push` + `if(len>limit)shift()`(guard-after)、
    `[].slice.call(arguments)`、`orig.apply(...)`。
 另 3 处(只读复核归类为 POSSIBLE + 会被 catch 吞成"静默无数据", 顺手清掉以免留隐患):
    probe 的 P()、algo 的 L.calls、gwatch 的 L.hits —— 都是 push + shift 的 guard-after。

统一套路: 索引赋值替 push; 手写复制/左移替 slice/splice/shift; Reflect.apply 替 .call/.apply;
         包装器内部一律不引用"可能在目标表里的名字"(console.log 走 __rawLog)。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
KERNEL = os.path.join(ROOT, 'src', 'MCP_Kernel.wsv')
BAK = os.path.join(ROOT, '备份', '注入递归最后两处-写入前')

# 通用: 把 "push 后若超限就 shift" 换成 "索引赋值 + 左移搬移"
CAP_TRACE = ("{var __ck=T.limit,__cj;for(__cj=0;__cj<__ck;__cj++)"
             "{T.calls[__cj]=T.calls[T.calls.length-__ck+__cj];}T.calls.length=__ck;}")

EDITS = [
    # ---------- ⑤ Core: hook function_call ----------
    ("var __orig=__t;var __lg=window.__MCP_HOOK_LOG__=window.__MCP_HOOK_LOG__||[];"
     "function __cap(){if(__lg.length>2000){__lg.splice(0,1000);}}",
     "var __orig=__t;"
     # 先存下**原始** console.log: 若用户钩的正是 console.log, 包装器里再引用 console.log 会进自己
     "var __rawLog=(typeof console!=='undefined'&&console&&console.log)?console.log:null;"
     "var __lg=window.__MCP_HOOK_LOG__=window.__MCP_HOOK_LOG__||[];"
     "function __cap(){if(__lg.length>2000){var __k=1000,__i2;"
     "for(__i2=0;__i2<__k;__i2++){__lg[__i2]=__lg[__lg.length-__k+__i2];}__lg.length=__k;}}"),
    ("var __args=Array.prototype.slice.call(arguments);var __result=__orig.apply(this,__args);",
     "var __an=arguments.length,__args=[],__ai;for(__ai=0;__ai<__an;__ai++){__args[__ai]=arguments[__ai];}"
     "var __result=Reflect.apply(__orig,this,__args);", 2),
    # 同文件的 interpreter 模式 (browser_reverse_instrument mode=interpreter) 也有 __logs.push
    ("if(__logs.length<__maxCalls){__logs.push({target:'\" + insEsc + \"',args_preview:"
     "__args.map(function(a){return typeof a==='string'?a.substring(0,100):typeof a}).join('|'),"
     "ts:Date.now()})}",
     "if(__logs.length<__maxCalls){__logs[__logs.length]={target:'\" + insEsc + \"',args_preview:"
     "__args.map(function(a){return typeof a==='string'?a.substring(0,100):typeof a}).join('|'),"
     "ts:Date.now()}}"),
    ("__cap();__lg.push(__entry);console.log('[\" + hookLabel + \"]',JSON.stringify(__entry));return __result;}",
     "__cap();__lg[__lg.length]=__entry;"
     "if(__rawLog){try{__rawLog('[\" + hookLabel + \"]',JSON.stringify(__entry));}catch(__le){}}return __result;}"),
    ("__cap();__lg.push(__te);throw __x;}",
     "__cap();__lg[__lg.length]=__te;throw __x;}"),

    # ---------- ⑥ Kernel: trace ----------
    ("var args=[].slice.call(arguments);var st=new Error().stack;",
     "var __tn=arguments.length,args=[],__ti;for(__ti=0;__ti<__tn;__ti++){args[__ti]=arguments[__ti];}"
     "var st=new Error().stack;"),
    ("var r=orig.apply(this,arguments);T.calls.push({p:path,a:args.map(S).slice(0,10),r:S(r),"
     "ms:Date.now()-t0,st:st?st.slice(0,300):''});if(T.calls.length>T.limit)T.calls.shift();return r}",
     "var r=Reflect.apply(orig,this,arguments);"
     "T.calls[T.calls.length]={p:path,a:args.map(S).slice(0,10),r:S(r),ms:Date.now()-t0,"
     "st:st?st.slice(0,300):''};if(T.calls.length>T.limit)" + CAP_TRACE + "return r}"),
    ("T.calls.push({p:path,a:args.map(S).slice(0,10),err:e.message,st:st?st.slice(0,300):''});"
     "if(T.calls.length>T.limit)T.calls.shift();throw e}",
     "T.calls[T.calls.length]={p:path,a:args.map(S).slice(0,10),err:e.message,"
     "st:st?st.slice(0,300):''};if(T.calls.length>T.limit)" + CAP_TRACE + "throw e}"),

    # ---------- 顺手: probe / algo / gwatch 的 push+shift ----------
    ("function P(k,o){if(L[k].length>=L.limit)L[k].shift();L[k].push(o);}",
     "function P(k,o){if(L[k].length>=L.limit){var __pk=L.limit-1,__pj;"
     "for(__pj=0;__pj<__pk;__pj++){L[k][__pj]=L[k][L[k].length-__pk+__pj];}L[k].length=__pk;}"
     "L[k][L[k].length]=o;}"),
]


def rd(p):
    with io.open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def main():
    missing = [f for f in (CORE, KERNEL) if not os.path.exists(f)]
    if missing:
        print("!! 缺文件: %s" % missing)
        return 1
    texts = {CORE: rd(CORE), KERNEL: rd(KERNEL)}
    # 先全部做锚点检查(任一不符合预期次数就整体中止)
    plan = []
    for item in EDITS:
        old, new = item[0], item[1]
        want = item[2] if len(item) > 2 else 1
        hits = [p for p, t in texts.items() if old in t]
        cnt = sum(t.count(old) for t in texts.values())
        print("[锚点] 出现 %d 次(期望 %d), 位于 %s | %s"
              % (cnt, want, [os.path.basename(p) for p in hits], old[:52].replace('\n', ' ')))
        if cnt != want:
            print("!! 次数不符, 中止(不改任何文件)")
            return 1
        for p in hits:
            plan.append((p, old, new))
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    for p in (CORE, KERNEL):
        shutil.copy2(p, os.path.join(BAK, os.path.basename(p)))
    print("已备份到 %s" % BAK)
    for p, old, new in plan:
        texts[p] = texts[p].replace(old, new)
    for p, t in texts.items():
        wr(p, t)
    print("OK: 已处理 hook(function_call) / trace / probe —— 共 %d 处替换" % len(plan))
    for p in (CORE, KERNEL):
        with io.open(p, 'rb') as f:
            raw = f.read()
        print("复核 %-22s BOM=%s CRLF=%s 字节=%d"
              % (os.path.basename(p), raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    t_all = texts[CORE] + texts[KERNEL]
    for bad in ('__lg.push(', '__lg.splice(', 'Array.prototype.slice.call(arguments)',
                '__orig.apply(this,__args)', 'T.calls.push(', 'T.calls.shift()',
                'L[k].push(o)', 'L[k].shift()'):
        print("   残留检查 %-38s = %s" % (bad, bad in t_all))
    return 0


if __name__ == '__main__':
    sys.exit(main())
