# -*- coding: utf-8 -*-
"""修 MCP_Server_Reverse.wsv 里同一缺陷类的其余三处(push/slice/splice/apply/slice.call + var 捕获)。

背景: 上一轮修好了 browser_reverse_instrument 的自递归(默认目标即触发)。只读复核指出
同一缺陷类全库共 6 处, 本脚本处理其中**会被常规使用触发**的三处:

 ① browser_reverse_hook_multi (hmCode):
    · 安装期自递归: 装好 obj[last] 包装器后紧接 `found.push(name)` —— 若 fns 含 Array.prototype.push
      就当场递归;
    · var 捕获 bug: `var name`/`var __orig` 都是函数作用域, 循环里所有包装器共享同一份,
      于是全部记录成**最后一个**名字、并调用**最后一个**原函数(与上一轮我在插装上踩的是同一个坑);
    · `Array.prototype.slice.call(arguments)` + `__orig.apply(...)` 都是默认目标;
    · `__cap()` 用 `lg.splice`。
 ② browser_reverse_hook_logs 的自动读路径 (hlCode): 用 `hit.push` / `arr.slice` / `items.push` ——
    而这些方法**很可能已被前面的 hook/instrument 包装**, 于是"读日志"这一步自己会中招。
 ③ 同工具的单键读路径: 用 `v.slice` / `safe.push`。

修法（统一套路, 不需要捕获"当时的原生函数"——因为读路径运行时原生可能已被包掉）:
  · 一律用**索引赋值** `a[a.length]=x` 代替 push;
  · 用**手写复制循环**代替 slice;
  · 用 **Reflect.apply** 代替 `.apply` / `.call`;
  · 用**索引左移 + 改 length** 代替 splice;
  · hmCode 的循环体套 **IIFE 传参**, 保证每轮独立作用域。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
BAK = os.path.join(ROOT, '备份', '逆向注入读写路径去自递归-写入前')

EDITS = [
    # ---- ① hmCode: __cap 不再用 splice ----
    ("function __cap(){if(lg.length>2000){lg.splice(0,1000);}};",
     "function __cap(){if(lg.length>2000){var keep=1000,kk;for(kk=0;kk<keep;kk++){lg[kk]=lg[lg.length-keep+kk];}lg.length=keep;}};"),

    # ---- ① hmCode: 循环体改为 IIFE + 索引赋值 + Reflect.apply + 手写参数复制 ----
    ("for(var i=0;i<fns.length;i++){var name=fns[i];var parts=name.split('.');var obj=window;var ok=true;"
     "for(var j=0;j<parts.length-1;j++){obj=obj[parts[j]];if(!obj){ok=false;break;}}"
     "if(ok&&typeof obj[parts[parts.length-1]]==='function'){var last=parts[parts.length-1];"
     "var __orig=obj[last];obj[last]=function(){var a=Array.prototype.slice.call(arguments);"
     "var e={fn:name,ts:Date.now()};if(CAP){try{e.args=JSON.stringify(a).substring(0,512);}"
     "catch(x){e.args='[unserializable]';}}try{var r=__orig.apply(this,a);"
     "try{e.ret=JSON.stringify(r).substring(0,512);}catch(x){e.ret=String(r).substring(0,512);}"
     "__cap();lg.push(e);return r;}catch(x){__cap();lg.push({fn:name,ts:Date.now(),threw:x.message});"
     "throw x;}};found.push(name);}}",
     "for(var i=0;i<fns.length;i++){(function(name){var parts=name.split('.');var obj=window;var ok=true;"
     "for(var j=0;j<parts.length-1;j++){obj=obj[parts[j]];if(!obj){ok=false;break;}}"
     "if(!(ok&&typeof obj[parts[parts.length-1]]==='function'))return;"
     "var last=parts[parts.length-1];var __orig=obj[last];"
     "obj[last]=function(){var an=arguments.length,a=[],ai;for(ai=0;ai<an;ai++){a[ai]=arguments[ai];}"
     "var e={fn:name,ts:Date.now()};if(CAP){try{e.args=JSON.stringify(a).substring(0,512);}"
     "catch(x){e.args='[unserializable]';}}try{var r=Reflect.apply(__orig,this,a);"
     "try{e.ret=JSON.stringify(r).substring(0,512);}catch(x){e.ret=String(r).substring(0,512);}"
     "__cap();lg[lg.length]=e;return r;}catch(x){__cap();"
     "lg[lg.length]={fn:name,ts:Date.now(),threw:x.message};throw x;}};"
     "found[found.length]=name;})(fns[i]);}"),

    # ---- ② 自动读路径: 不用 push / slice ----
    ("hit.push(k);var p=arr.slice(Math.max(0,arr.length-200));for(var j=0;j<p.length;j++){",
     "hit[hit.length]=k;var st=arr.length-200;if(st<0){st=0;}var p=[];"
     "for(var sk=st;sk<arr.length;sk++){p[p.length]=arr[sk];}for(var j=0;j<p.length;j++){"),
    ("items.push(it);}", "items[items.length]=it;}"),

    # ---- ③ 单键读路径 ----
    ("total=v.length;items=v.slice(Math.max(0,v.length-200));",
     "total=v.length;var st=v.length-200;if(st<0){st=0;}"
     "for(var sk=st;sk<v.length;sk++){items[items.length]=v[sk];}"),
    ("total=v.results.length;items=v.results.slice(Math.max(0,v.results.length-200));",
     "total=v.results.length;var rst=v.results.length-200;if(rst<0){rst=0;}"
     "for(var rk=rst;rk<v.results.length;rk++){items[items.length]=v.results[rk];}"),
    ("safe.push(JSON.parse(JSON.stringify(items[i])))",
     "safe[safe.length]=JSON.parse(JSON.stringify(items[i]))"),
    ("safe.push(String(items[i]).substring(0,300))",
     "safe[safe.length]=String(items[i]).substring(0,300)"),
    ("safe.push('[unserializable]')", "safe[safe.length]='[unserializable]'"),
]


def rd(p):
    with io.open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def main():
    t = rd(REV)
    for i, (old, new) in enumerate(EDITS, 1):
        n = t.count(old)
        print("[编辑%2d] 锚点出现 %d 次  %s" % (i, n, old[:60].replace('\n', ' ')))
        if n != 1:
            print("!! 预期 1 次, 中止(不改任何文件)")
            return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(REV, os.path.join(BAK, os.path.basename(REV)))
    print("已备份到 %s" % BAK)
    for old, new in EDITS:
        t = t.replace(old, new)
    wr(REV, t)
    print("OK: 3 处读写路径已去除 push/slice/splice/.call/.apply, 并修掉 var 捕获")
    with io.open(REV, 'rb') as f:
        raw = f.read()
    print("复核: BOM=%s CRLF=%s 字节=%d"
          % (raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    for bad in ('found.push(name)', 'lg.push(e)', 'hit.push(k)', 'items.push(it)',
                'safe.push(', 'Array.prototype.slice.call(arguments)', '__orig.apply(this,a)',
                'lg.splice('):
        print("   残留检查 %-34s = %s" % (bad, bad in t))
    return 0


if __name__ == '__main__':
    sys.exit(main())
