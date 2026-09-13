# -*- coding: utf-8 -*-
"""定位新版插装模板里 __callOrig is not a function 的准确位置(col 780)。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')

TARGETS = ("['Function.prototype.apply','Function.prototype.call','Array.prototype.push',"
           "'Array.prototype.pop','String.prototype.indexOf','String.prototype.charAt']")

# 从源码里把 insCode 的**字面量部分**抽出来(替换 选择(...) 为固定 targets), 得到运行时真实 JS
src = io.open(CORE, encoding='utf-8').read()
line = None
for L in src.split('\n'):
    if 'insCode = "(function(){var __targets=' in L:
        line = L
        break
print("找到源码行: %s" % (line is not None))

# 用诊断脚本里的同一段文本做精确定位(与源码逐字一致)
NEW_JS = (
    "(function(){var __targets=" + TARGETS + ";var __ts=Function.prototype.toString,"
    "__callOrig=Function.prototype.call,__applyOrig=Function.prototype.apply;"
    "var __split=String.prototype.split,__sub=String.prototype.substring;"
    "var __count=0;var __max=500;var __results=[];"
    "var __log=function(__t,__args){if(__count>=__max)return;var __s='',__n=__args.length,__li;"
    "for(__li=0;__li<__n;__li++){var __v=__args[__li];"
    "__s+=(__li?',':'')+((typeof __v==='string')?__callOrig(__sub,__v,0,200):typeof __v)}"
    "__results[__results.length]={target:__t,args:__s,ts:Date.now()};__count++};"
    "for(var __ti=0;__ti<__targets.length;__ti++){var __t=__targets[__ti];"
    "var __parts=__callOrig(__split,__t,'.');var __obj=window;var __ok=1;"
    "for(var __pi=0;__pi<__parts.length-1;__pi++){__obj=__obj[__parts[__pi]];if(!__obj){__ok=0;break}}"
    "if(!__ok)continue;var __method=__parts[__parts.length-1];var __orig=__obj[__method];"
    "if(typeof __orig!=='function')continue;"
    "var __wrapper=function(){__log(__t,arguments);"
    "return __callOrig(__applyOrig,__orig,this,arguments)};"
    "__wrapper.__mcp_orig=__orig;"
    "__wrapper.toString=function(){return __callOrig(__ts,__orig)};"
    "__obj[__method]=__wrapper}"
    "window.__mcp_instrument_results={instrumented:__targets.length,calls:__count,results:__results};"
    "return JSON.stringify({installed:true,targets:__targets.length})})()")

print("\nJS 长度 = %d" % len(NEW_JS))
print("col 780 附近: ...%s..." % NEW_JS[750:830])
print("\n首个 __callOrig 出现位置 = %d" % NEW_JS.find('__callOrig'))
print("声明处上下文: ...%s..." % NEW_JS[60:150])

# 关键检查: 声明链是否真的把 __callOrig 赋上了
decl = NEW_JS[NEW_JS.find('var __ts='):NEW_JS.find('var __split=')]
print("\n声明片段: %s" % decl)

# 模拟: 依次包装 apply/call 后, __callOrig 还在不在?
print("\n关键推断检查 —— 目标表里第 1/2 项就是 apply/call:")
print("  target[0] = %s" % TARGETS.split(',')[0])
print("  target[1] = %s" % TARGETS.split(',')[1])
print("  -> 包装 Function.prototype.call 之后, 任何 *后来才求值* 的 `.call` 属性查找都会命中包装器;")
print("     但 __callOrig 是安装前捕获的**值**, 不受影响。")
print("     所以 'is not a function' 只可能来自: __callOrig 未被赋值成功, 或该变量被覆盖/名字写错。")

# 逐字核对源码里出现过的标识符拼写
for name in ('__callOrig', '__callorig', '__callorig', '__callOrig2'):
    print("  源码中 %-14s 出现次数 = %d" % (name, src.count(name)))
