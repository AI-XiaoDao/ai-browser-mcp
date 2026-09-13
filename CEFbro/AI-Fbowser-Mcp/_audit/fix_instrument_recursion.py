# -*- coding: utf-8 -*-
"""修 browser_reverse_instrument 透明插装的**无限自递归**(实测崩栈的根因)。

实测: 用过该工具后, 同页后续任何 JS 都可能崩:
    RangeError: Maximum call stack size exceeded
    at __obj.<computed> (<anonymous>:1:544)   (反复自递归)

静态根因(只读复核 + 我逐条复核): 注入的包装器在**日志路径**上使用了会被它自己包装的内建方法:
    __results.push({...})                      <- 默认目标表里就有 Array.prototype.push
    Array.prototype.slice.call(arguments)      <- 默认目标表里还有 Function.prototype.call
    __orig.apply(this,arguments)               <- 默认目标表里还有 Function.prototype.apply
于是: 记录一次调用 -> 走 push/call 的包装器 -> 包装器又要记录 -> 再走 push/call ... 无限递归;
且 `__count++` 写在 push 之后, 永远执行不到, `__max` 上限也就永远不生效。

修法: 日志路径**只用安装前捕获的原生函数**, 数组用**索引赋值**而不是 push; 结构用普通 for 循环。
同时给包装器补上 `__mcp_orig`(= 原函数), 这是后续"卸载/还原"入口的必要前提(原来原函数只留在
不可达的闭包里, 只能靠刷新页面恢复)。

本脚本按"行内定位锚点"替换, 保留原有的 targets 表达式与提示文案, 只换 JS 主体。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '插装自递归修复-写入前')
B = chr(92)
Q = chr(34)

LINE_MARK = 'insCode = "(function(){var __targets='
BODY_MARK = '+ ";var __count=0;var __max=500;var __results=[];'

HINT = ("'Transparent instrumentation installed. toString preserved. Use browser_evaluate "
        + B + Q + "JSON.stringify(window.__mcp_instrument_results)" + B + Q
        + " to read collected data. Trigger target action first.'")

NEW_BODY = (
    ';var __ts=Function.prototype.toString,__callOrig=Function.prototype.call,'
    '__applyOrig=Function.prototype.apply;var __split=String.prototype.split,'
    '__sub=String.prototype.substring;'
    'var __count=0;var __max=500;var __results=[];'
    # 日志路径: 只用捕获量 + 索引赋值 + 普通循环 —— 不碰任何可能被包装的原型方法
    'var __log=function(__t,__args){if(__count>=__max)return;var __s=\'\',__n=__args.length,__li;'
    'for(__li=0;__li<__n;__li++){var __v=__args[__li];'
    '__s+=(__li?\',\':\'\')+((typeof __v===\'string\')?__callOrig(__sub,__v,0,200):typeof __v)}'
    '__results[__results.length]={target:__t,args:__s,ts:Date.now()};__count++};'
    # 安装: 普通 for 循环 + 捕获的 split
    'for(var __ti=0;__ti<__targets.length;__ti++){var __t=__targets[__ti];'
    'var __parts=__callOrig(__split,__t,\'.\');var __obj=window;var __ok=1;'
    'for(var __pi=0;__pi<__parts.length-1;__pi++){__obj=__obj[__parts[__pi]];if(!__obj){__ok=0;break}}'
    'if(!__ok)continue;var __method=__parts[__parts.length-1];var __orig=__obj[__method];'
    'if(typeof __orig!==\'function\')continue;'
    # 调用原函数用"捕获的 apply + 捕获的 call", 不经被包装的 Function.prototype.call/apply
    'var __wrapper=function(){__log(__t,arguments);'
    'return __callOrig(__applyOrig,__orig,this,arguments)};'
    # 卸载入口的前提: 把原函数挂在包装器上(原来只留在不可达闭包里 -> 只能靠刷新恢复)
    '__wrapper.__mcp_orig=__orig;'
    '__wrapper.toString=function(){return __callOrig(__ts,__orig)};'
    '__obj[__method]=__wrapper}'
    'window.__mcp_instrument_results={instrumented:__targets.length,calls:__count,results:__results};'
    'return JSON.stringify({installed:true,targets:__targets.length,hint:' + HINT + '})})()'
)

COMMENT = '\n'.join([
    '                    // ★ 修(实测崩栈根因): 原实现在**日志路径**上使用了会被自己包装的内建方法 ——',
    '                    //   __results.push(...)(默认目标表含 Array.prototype.push)、',
    '                    //   Array.prototype.slice.call(...)(含 Function.prototype.call)、',
    '                    //   __orig.apply(...)(含 Function.prototype.apply) —— 于是记录一次调用就再进包装器、',
    '                    //   包装器又要记录… 无限自递归; 且 __count++ 在 push 之后, 永远到不了 __max 上限。',
    '                    //   实测症状: 用过后同页 JS 崩 RangeError: Maximum call stack size exceeded,',
    '                    //   栈帧反复 at __obj.<computed>。',
    '                    //   现改为: 安装前捕获原生 apply/call/toString/split/substring, 日志路径只用这些捕获量,',
    '                    //   数组用**索引赋值**代替 push, 结构用普通 for 循环 —— 不再触碰任何可被包装的原型方法。',
    '                    //   同时把原函数挂到 __wrapper.__mcp_orig: 这是后续"卸载/还原"入口的必要前提',
    '                    //   (原来原函数只留在不可达的闭包里, 只能靠刷新页面恢复)。',
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
    print("[行定位] 含 insCode 的行数 = %d" % len(hits))
    if len(hits) != 1:
        print("!! 预期恰好 1 行, 中止")
        return 1
    i = hits[0]
    old = lines[i]
    pos = old.find(BODY_MARK)
    if pos == -1:
        print("!! 未找到 JS 主体起始锚点, 中止")
        print("   该行前 200 字符: %s" % old[:200])
        return 1
    head = old[:pos]          # 含 targets 表达式
    if '__count=0' in head:
        print("!! 头部异常(似乎已改过), 中止")
        return 1
    new = head + NEW_BODY
    lines[i] = COMMENT + '\n' + new
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(CORE, os.path.join(BAK, os.path.basename(CORE)))
    print("已备份到 %s" % BAK)
    wr(CORE, '\n'.join(lines))
    print("OK: 日志路径已改为只用捕获量 + 索引赋值; 并补 __mcp_orig")
    with io.open(CORE, 'rb') as f:
        raw = f.read()
    print("复核: BOM=%s CRLF=%s 字节=%d"
          % (raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    # 复核: 新主体里不应再出现未捕获的 push / slice.call / .apply( 直接调用
    body = NEW_BODY
    for bad in ('__results.push', 'Array.prototype.slice.call', '__orig.apply('):
        print("   残留检查 %-28s = %s" % (bad, bad in body))
    return 0


if __name__ == '__main__':
    sys.exit(main())
