# -*- coding: utf-8 -*-
"""还原被覆盖的 main.wsv 尾部片段 (捕获到的 GBK 乱码 = UTF-8 字节按 cp936 解读)"""

raw = [
    "娑堟伅鏂囨湰 = UTF8鍒版枃鏈?(娑堟伅鍐呭)",
    "// 娉ㄥ叆闃熷垪: window.__mcp_ipc_queue.push({name, data, ts})",
    "// 娉? 绠€鍗曡浆涔塉S 涓哄崟寮曞彿JS瀛楃涓蹭笂涓嬫枃(涓嶅甫寮曞彿), 椤荤敤鍗曞紩鍙峰寘瑁?",
    "鍙橀噺 娉ㄥ叆浠ｇ爜 <绫诲瀷 = 鏂囨湰鍨?",
    "涓绘鏋?鎵цJS浠ｇ爜 (娉ㄥ叆浠ｇ爜, \"\", 0)",
    "鏂规硶 娓叉煋_鍗冲皢鍒涘缓V8鐜 <鍏紑 娉ㄩ噴 = \"鑻辨枃鍚嶏細OnContextCreated 璇存槑锛氬彧鑳藉湪娓叉煋杩涚▼涓娇鐢? @铏氭嫙鏂规硶 = 鍙鍒?",
    "鍙傛暟 娴忚鍣?<绫诲瀷 = 绫籣FBrowser_娴忚鍣?",
    "鍙傛暟 妗嗘灦 <绫诲瀷 = 绫籣FBrowser_妗嗘灦>",
    "鍙傛暟 V8鐜 <绫诲瀷 = 绫籣FBrowser_V8鐜?",
    "鐖跺璞℃覆鏌揰鍗冲皢鍒涘缓V8鐜 (娴忚鍣? 妗嗘灦, V8鐜?  // 璋冪敤鍩虹被涓殑琚鍒欒櫨鎷熸柟娉?",
]

print("=== 乱码还原结果 (cp936 编码 -> utf-8 解码) ===")
print()
ok = 0
for s in raw:
    try:
        fixed = s.encode("cp936").decode("utf-8")
        ok += 1
    except Exception as e:
        fixed = "<<无法还原: %s>>  raw=%s" % (e, s)
    print("  " + fixed)
print()
print("成功还原 %d / %d 行" % (ok, len(raw)))
print()
print("=== 可重建的方法定义 (按火山语法补全缩进) ===")
print()
print("    方法 渲染_即将创建V8环境 <公开 注释 = \"英文名：OnContextCreated 说明：只能在渲染进程中使用\" @虚拟方法 = 可覆盖>")
print("    参数 浏览器 <类型 = 类_FBrowser_浏览器>")
print("    参数 框架 <类型 = 类_FBrowser_框架>")
print("    参数 V8环境 <类型 = 类_FBrowser_V8环境>")
print("    {")
print("        父对象.渲染_即将创建V8环境 (浏览器, 框架, V8环境)  // 调用基础类中的被覆盖虚拟方法")
print("    }")
