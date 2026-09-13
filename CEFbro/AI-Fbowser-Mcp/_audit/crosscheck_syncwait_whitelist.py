# -*- coding: utf-8 -*-
"""把"返回异步回执"的嫌疑工具与中央 应同步等待 白名单交叉核对。

机制(已核实):
  执行CDP命令_带参数 -> 立即回 {"_async":true,"task_id":...}
  中央 尝试同步跟随异步响应(MCP_Server.wsv:6354) 只在 应同步等待(方法名,参数) 为真时才把它
  换成真实结果(MCP_Server.wsv:5553 起是一张**显式白名单**)。
  => 不在白名单、自己也不做 同步等待异步任务 的工具, 就只能让调用方**再调一次 mcp_result**。

本脚本: 1) 打印白名单全文里的工具名; 2) 检查嫌疑工具是否在名单内; 3) 找 Core:7131 属于哪个工具。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
server = io.open(os.path.join(SRC, 'MCP_Server.wsv'), encoding='utf-8').read().split('\n')

# ---- 1) 抽出 应同步等待 的函数体(从方法声明行到下一个 方法 声明) ----
start = next(i for i, l in enumerate(server) if '方法 应同步等待' in l)
end = next((i for i in range(start + 1, len(server)) if re.match(r'\s*方法 ', server[i])),
           len(server))
body = '\n'.join(server[start:end])
print('应同步等待 函数体行数: %d (%d-%d)' % (end - start, start + 1, end))
names = sorted(set(re.findall(r'规范名 == "([a-z0-9_]+)"', body)))
print('白名单内**显式列出**的工具名 %d 个:' % len(names))
for n in names:
    print('   %s' % n)

SUSPECTS = ['browser_debugger_evaluate', 'browser_debugger_stack', 'browser_network_body',
            'browser_reverse_runtime', 'browser_reverse_call_fn',
            'browser_reverse_websocket', 'browser_reverse_heap',
            'browser_debugger_script_source', 'browser_debugger_inspect']
print('\n== 嫌疑工具是否在白名单 ==')
for s in SUSPECTS:
    print('   %-34s %s' % (s, '在白名单' if s in names else '**不在**'))

# 是否有前缀式/兜底规则
print('\n== 函数体里是否含前缀/兜底规则(否则白名单外一律异步) ==')
for pat, label in [(r'是否以 \(\s*规范名', '前缀判断 是否以(规范名'),
                   (r'寻找文本 \(规范名', '子串判断 寻找文本(规范名'),
                   (r'browser_reverse_, ', 'browser_reverse_ 前缀列表')]:
    hits = [i + start + 1 for i, l in enumerate(server[start:end]) if re.search(pat, l)]
    print('   %-34s 命中行: %s' % (label, hits[:8] or '无'))

# ---- 3) Core:7131 属于哪个工具 ----
core = io.open(os.path.join(SRC, 'MCP_Server_Core.wsv'), encoding='utf-8').read().split('\n')
print('\n== MCP_Server_Core.wsv 中 Profiler.getBestEffortCoverage 的上下文 ==')
for i, l in enumerate(core, 1):
    if 'getBestEffortCoverage' in l:
        # 往上找最近的 否则 (方法名 == "...")
        owner = '?'
        for j in range(i - 1, max(0, i - 400), -1):
            m = re.search(r'否则 \(方法名 == "([a-z0-9_.]+)"', core[j])
            if m:
                owner = m.group(1)
                break
        print('   行 %d -> 所属工具: %s' % (i, owner))
        print('       %s' % l.strip()[:120])
