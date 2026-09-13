# -*- coding: utf-8 -*-
"""把 7 个"取数据"的逆向调用点从异步入口改用**既有的同步出口** 执行V8CDP命令。

为什么: `执行逆向CDP命令` 发完命令立刻回 {"success":true,"_async":true,...} 不等 CDP 响应,
于是这些**本该返回数据**的工具只回一句「CDP已提交:xxx」, 数据全丢:
  browser_reverse_runtime {action:evaluate, expression:"1+1"} -> "CDP已提交:Runtime.evaluate"
(台账里它们记成 pass, 实为**假通过**。)

为什么用 执行V8CDP命令 而不是我另写一套: 该方法就是为本问题而生的既有出口, 其注释原文即为
「避免执行逆向CDP命令那种'CDP已提交'的异步回执掩盖失败 —— 那类假成功会让用户以为插装已生效,
实际什么都没挂上」, 且已统一处理: 同步等待 / 域未启用自动重试(auto_prepared) / 可行动错误分支 /
把 result 提取成 cdp_result。属"不重复造轮子"。

**不**改动的调用点(刻意保留异步): 132/143/156/224 设置类断点、381 preload、
394 Network.enable、426 takeHeapSnapshot、430 startSampling
  —— 它们是"装模式/开始"语义, 且 takeHeapSnapshot 在堆大时可能超过同步预算(15s),
     改同步反而会制造假超时。此项作为遗留列出, 不一刀切。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
BAK = os.path.join(ROOT, '备份', '取数据调用改同步-写入前')

# (旧整行, 新整行) —— 用整行做锚点, 保证唯一且不会误伤其它调用点
PAIRS = [
    ('            返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "Runtime.callFunctionOn", cfParamsText))',
     '            // 改用同步出口: 本工具**要返回函数返回值**, 走异步入口只会回「CDP已提交」而丢掉结果\n'
     '            返回 (执行V8CDP命令 (命令ID, "Runtime.callFunctionOn", cfParamsText, "cdp_result 的 result.value 即该函数的返回值(本工具以 returnByValue=true 调用) | 若报 objectId 相关错误, 说明目标函数需要先由 browser_reverse_runtime 取到 objectId"))'),

    ('                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "Network.getResponseBody", wsQueryParams.到可读文本 (YYJSON格式化选项.压缩)))',
     '                // 改用同步出口: query 的**全部价值就是拿回响应体**, 异步入口会把 body 丢掉\n'
     '                返回 (执行V8CDP命令 (命令ID, "Network.getResponseBody", wsQueryParams.到可读文本 (YYJSON格式化选项.压缩), "cdp_result 含 body(响应体文本) 与 base64Encoded(是否base64); 报 No resource with given identifier 说明该请求已不在缓存中(需在请求发生后尽快取)"))'),

    ('                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "HeapProfiler.stopSampling", "{}"))',
     '                // 改用同步出口: stopSampling **返回剖析结果**, 异步入口会丢掉它\n'
     '                返回 (执行V8CDP命令 (命令ID, "HeapProfiler.stopSampling", "{}", "cdp_result 的 profile 即本次内存采样剖析结果 | 若报 No sampling profile 说明没有先执行 action=start_sampling"))'),

    ('                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "HeapProfiler.getObjectByHeapObjectId", hpObjParams.到可读文本 (YYJSON格式化选项.压缩)))',
     '                // 改用同步出口: get_object **返回对象描述**, 异步入口会丢掉它\n'
     '                返回 (执行V8CDP命令 (命令ID, "HeapProfiler.getObjectByHeapObjectId", hpObjParams.到可读文本 (YYJSON格式化选项.压缩), "cdp_result 的 object 为该堆对象的描述(含 className/description) | object_id 从 action=snapshot 的堆快照或 browser_reverse_runtime 的 objectId 获得"))'),

    ('                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "Runtime.getProperties", rtParams.到可读文本 (YYJSON格式化选项.压缩)))',
     '                // 改用同步出口: properties 的**全部价值就是拿回属性列表**, 异步入口会丢掉它\n'
     '                返回 (执行V8CDP命令 (命令ID, "Runtime.getProperties", rtParams.到可读文本 (YYJSON格式化选项.压缩), "cdp_result 的 result 数组即该对象的自有属性(每项含 name/value/objectId); 带 objectId 的属性可继续用本工具下钻或以 browser_reverse_call_fn 调用"))'),

    ('                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "Runtime.evaluate", rtEvalParams.到可读文本 (YYJSON格式化选项.压缩)))',
     '                // 改用同步出口: evaluate **必须把求值结果带回来** —— 否则调用方只会看到\n'
     '                // 「CDP已提交:Runtime.evaluate」而拿不到值, 只能反复换工具重试(实证: 台账里本工具\n'
     '                // 以 action=evaluate 记录成 pass, 但回包里根本没有 1+1 的结果)。\n'
     '                返回 (执行V8CDP命令 (命令ID, "Runtime.evaluate", rtEvalParams.到可读文本 (YYJSON格式化选项.压缩), "cdp_result 的 result 即求值结果: 默认 returnByValue=true 时给 type/value, 传 return_by_value=false 时给 objectId(可直接喂给 browser_reverse_call_fn / properties)"))'),

    ('                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "Runtime.globalLexicalScopeNames", "{}"))',
     '                // 改用同步出口: 本 action **返回全局名字列表**, 异步入口会丢掉它\n'
     '                返回 (执行V8CDP命令 (命令ID, "Runtime.globalLexicalScopeNames", "{}", "cdp_result 的 names 即全局词法作用域中的变量/函数名(混淆脚本里可据此快速发现可疑入口函数)"))'),
]


def main():
    data = open(SRC, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '源文件不应有BOM'
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    print('换行: %s' % ('CRLF' if nl == '\r\n' else 'LF'))

    # 逐行锚点唯一性检查(先全部检查再写, 避免写一半失败)
    for old, new in PAIRS:
        c = text.count(old)
        tag = new.split('执行V8CDP命令 (命令ID, "')[1].split('"')[0]
        print('  锚点 %-42s 命中 %d' % (tag, c))
        if c != 1:
            print('!! 锚点不唯一, 中止(尚未写入)')
            return 1

    # 转义自查: 新增行里的 ASCII 双引号必须成对
    for old, new in PAIRS:
        for ln in new.split('\n'):
            if ln.replace('\\"', '').count('"') % 2 != 0:
                print('!! 裸双引号数为奇数: %s' % ln)
                return 1
    print('自检: 双引号成对')

    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Reverse.wsv'))
    print('备份 -> %s' % BAK)

    for old, new in PAIRS:
        text = text.replace(old, new.replace('\n', nl))
    open(SRC, 'wb').write(text.encode('utf-8'))
    print('已写入 %d 处替换' % len(PAIRS))

    # 复核: 剩余异步调用点
    left = [l.strip()[:96] for l in text.split('\n')
            if '执行逆向CDP命令 (命令ID' in l]
    print('剩余走异步入口的调用点 %d 处:' % len(left))
    for l in left:
        print('   %s' % l)
    return 0


sys.exit(main())
