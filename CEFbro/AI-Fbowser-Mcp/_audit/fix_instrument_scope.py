# -*- coding: utf-8 -*-
"""修正插装模板: 我上一版把 forEach 回调换成普通 for 循环, 引入了经典的 var 捕获 bug。

症状(实测): 装上模板后, `a.push(1,2,3)` 得 len:0; `Array.prototype.slice.call(a,1)` 得 "f";
`f.apply(null,[41])` 得 "f"。
根因: `var __orig`/`var __t`/`var __obj`/`var __method` 都是**函数作用域**, 而每个包装器闭包
      引用的都是**同一个** `__orig` 变量 —— 循环结束后它保存的是**最后一个目标**(String.prototype.charAt)
      的原始函数。于是所有包装器都在调 charAt:
        a.push(1,2,3)          -> charAt.call(a,1,2) -> "" (a 没被改)      => len:0
        slice.call(a,1)        -> charAt.call(sliceFn,a,1) -> ToString(sliceFn)="function slice(){[native code]}"
                                  charAt(0) = "f"                            => "f"
        f.apply(null,[41])     -> charAt.call(f,null)     -> "f"             => "f"
      三个"怪值"全部得到解释。
原实现用 `__targets.forEach(function(__t){...})` —— **回调本身就是一次函数调用**, 天然每轮独立作用域,
所以原来没有这个 bug; 是我把 forEach 换掉时引入的。

修法: 循环体改用**显式 IIFE** 传参, 逐轮独立作用域(不依赖 forEach, 也就不怕用户把 forEach 列为目标)。
（保持"日志路径只用 Reflect.apply + 捕获量 + 索引赋值"的自递归修复不变。）
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '插装逐轮作用域修复-写入前')
B = chr(92)
Q = chr(34)

LINE_MARK = 'insCode = "(function(){var __targets='
BODY_START = ';var __ts=Function.prototype.toString'

HINT = ("'Transparent instrumentation installed. toString preserved. Use browser_evaluate "
        + B + Q + "JSON.stringify(window.__mcp_instrument_results)" + B + Q
        + " to read collected data. Trigger target action first.'")

NEW_BODY = (
    ';var __ts=Function.prototype.toString,__split=String.prototype.split,'
    '__sub=String.prototype.substring;'
    'var __count=0;var __max=500;var __results=[];'
    # 日志: 只用捕获量 + Reflect.apply + 索引赋值(不触碰任何可能被包装的原型方法)
    'var __log=function(__t,__args){if(__count>=__max)return;var __s=\'\',__n=__args.length,__li;'
    'for(__li=0;__li<__n;__li++){var __v=__args[__li];'
    '__s+=(__li?\',\':\'\')+((typeof __v===\'string\')?Reflect.apply(__sub,__v,[0,200]):typeof __v)}'
    '__results[__results.length]={target:__t,args:__s,ts:Date.now()};__count++};'
    # 关键: 每轮用 IIFE 建独立作用域, 否则 var 被所有包装器共享 -> 全部指向最后一个目标的原函数
    'for(var __ti=0;__ti<__targets.length;__ti++){(function(__t){'
    'var __parts=Reflect.apply(__split,__t,[\'.\']);var __obj=window;var __ok=1;'
    'for(var __pi=0;__pi<__parts.length-1;__pi++){__obj=__obj[__parts[__pi]];if(!__obj){__ok=0;break}}'
    'if(!__ok)return;var __method=__parts[__parts.length-1];var __orig=__obj[__method];'
    'if(typeof __orig!==\'function\')return;'
    'var __wrapper=function(){__log(__t,arguments);'
    'return Reflect.apply(__orig,this,arguments)};'
    '__wrapper.__mcp_orig=__orig;'
    '__wrapper.toString=function(){return Reflect.apply(__ts,__orig,[])};'
    '__obj[__method]=__wrapper})(__targets[__ti]);}'
    'var __pub={instrumented:__targets.length,results:__results};'
    'Object.defineProperty(__pub,\'calls\',{get:function(){return __count},enumerable:true});'
    'window.__mcp_instrument_results=__pub;'
    'return JSON.stringify({installed:true,targets:__targets.length,hint:' + HINT + '})})()'
)

COMMENT = '\n'.join([
    '                    // ★ 修(第二轮): 上一版把 forEach 回调换成普通 for 循环时引入了经典 var 捕获 bug ——',
    '                    //   __t/__obj/__orig/__method 都是函数作用域, 所有包装器闭包共享同一份, 循环结束后',
    '                    //   它们指向**最后一个目标**的原函数(实测全部变成了调 charAt):',
    '                    //     a.push(1,2,3)  -> charAt -> len:0;  slice.call(a,1) -> "f";  f.apply -> "f"。',
    '                    //   原实现用 forEach 回调(本身就是一次函数调用)天然每轮独立作用域, 所以没这个 bug。',
    '                    //   现改用**显式 IIFE 传参**保证逐轮独立, 且不依赖 forEach(用户可能把 forEach 列为目标)。',
    '                    // ★ 修(第一轮): 日志路径原先用 __results.push / Array.prototype.slice.call /',
    '                    //   __orig.apply —— 这三者都在默认目标表里, 于是记录一次调用就再进包装器、无限自递归',
    '                    //   (实测 RangeError: Maximum call stack size exceeded, 栈帧反复 at __obj.<computed>)。',
    '                    //   现改为: 安装前捕获 split/substring/toString, 一律用 Reflect.apply 调用,',
    '                    //   数组用索引赋值, 结构用普通 for 循环 —— 不再触碰任何可被包装的原型方法。',
    '                    //   另: 原 `calls:__count` 是安装瞬间的快照(恒 0), 已改为 getter 实时读。',
    '                    //   __wrapper.__mcp_orig 保留原函数, 是后续"卸载/还原"入口的前提。',
])


def rd(p):
    with io.open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def main():
    lines = rd(CORE).split('\n')
    hits = [i for i, L in enumerate(lines) if LINE_MARK in L]
    print("[行定位] 命中 %d 行" % len(hits))
    if len(hits) != 1:
        print("!! 预期 1 行, 中止")
        return 1
    i = hits[0]
    old = lines[i]
    # 去掉上一次插入的注释块(它紧邻在该行之前, 以 // ★ 修(实测崩栈根因) 开头)
    if i > 0 and '// ★ 修(实测崩栈根因)' in lines[i - 1]:
        j = i - 1
        while j >= 0 and lines[j].lstrip().startswith('//'):
            j -= 1
        del lines[j + 1:i]
        lines = [L for L in lines]
        hits = [k for k, L in enumerate(lines) if LINE_MARK in L]
        i = hits[0]
        old = lines[i]
        print("   已移除上一版注释块")
    p1 = old.find(BODY_START)
    if p1 == -1:
        print("!! 未找到 JS 主体起点, 中止")
        return 1
    p2 = old.rfind(Q)
    if p2 <= p1:
        print("!! 未找到收尾引号, 中止")
        return 1
    new = old[:p1] + NEW_BODY + Q + old[p2 + 1:]
    lines[i] = COMMENT + '\n' + new
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(CORE, os.path.join(BAK, os.path.basename(CORE)))
    print("已备份到 %s" % BAK)
    wr(CORE, '\n'.join(lines))
    print("OK: 逐轮独立作用域(IIFE) + Reflect.apply 日志路径")
    with io.open(CORE, 'rb') as f:
        raw = f.read()
    print("复核: BOM=%s CRLF=%s 字节=%d"
          % (raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    for bad in ('__results.push', 'Array.prototype.slice.call', '__orig.apply('):
        print("   残留检查 %-28s = %s" % (bad, bad in NEW_BODY))
    return 0


if __name__ == '__main__':
    sys.exit(main())
