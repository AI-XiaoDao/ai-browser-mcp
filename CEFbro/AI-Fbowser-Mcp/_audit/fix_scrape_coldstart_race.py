# -*- coding: utf-8 -*-
"""修 browser_scrape 冷启动首调返回**错误页面数据**的竞态。

实测缺陷(第101轮, 全新进程):
  第1次 browser_scrape {url:https://example.com/, extract_selector:h1}
      -> 0.03s 返回 "AI浏览器 MCP Server"   ← 欢迎页的 h1(**静默错数据**, 比报错更危险)
  第2..4 次 -> "Example Domain"             ← 正确
根因(MCP_Server_Core.wsv 爬虫状态机 Phase 0):
  `sFrame.载入地址 (sUrl)` 之后, 容器.取加载状态() **仍为"未加载"**(导航还没真正开始),
  Phase 0 于是立刻认为"加载完成" -> 进 Phase 1/2 -> 从**当前还在显示的欢迎页**提取。
即判据缺了"页面确实换了"这一半。

修法(两处):
  A. 提交任务时记录 target_url 与 prev_url(提交那一刻的页面地址);
  B. Phase 0 增加前置门: 目标与旧地址不同、且当前地址**仍等于旧地址**时 -> 判定页面还没换, 继续等。
     目标==旧地址(就是抓当前页)时不做此判断, 避免永远等不到。
   超时路径保持不变 -> 宁可如实超时, 也不返回错页面的数据。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '爬虫冷启动错页竞态-写入前')

text = io.open(SRC, encoding='utf-8').read()
nl = '\n'          # MCP_Server_Core.wsv 为 LF(已多次核实)
lines = text.split(nl)


def find_line(sub, start=0, end=None):
    end = end if end is not None else len(lines)
    hits = [i for i in range(start, end) if sub in lines[i]]
    return hits


# ---------- A. 捕获 prev_url 并随任务一起存储 ----------
h1 = find_line('sFrame.载入地址 (sUrl)')
print('A1 锚点 sFrame.载入地址 命中 %d 处: %s' % (len(h1), [i + 1 for i in h1]))
if len(h1) != 1:
    print('!! 锚点不唯一, 中止')
    sys.exit(1)
i_load = h1[0]
ind_load = lines[i_load][:len(lines[i_load]) - len(lines[i_load].lstrip())]
ins_a = [ind_load + '// 记录提交前的页面地址: Phase 0 用它判断"页面是否真的换了"(见下方爬虫状态机)',
         ind_load + '变量 sPrevUrl <类型 = 文本型>',
         ind_load + 'sPrevUrl = sFrame.取地址 ()']
lines[i_load:i_load] = ins_a
print('   A1 已在 载入地址 之前插入 prev_url 捕获(%d 行)' % len(ins_a))

h2 = find_line('MCP命令服务器.存储异步结果 (sTaskID, sStore.到可读文本 (YYJSON格式化选项.压缩))')
print('A2 锚点 存储异步结果(sTaskID) 命中 %d 处: %s' % (len(h2), [i + 1 for i in h2]))
if len(h2) != 1:
    print('!! 锚点不唯一, 中止')
    sys.exit(1)
i_store = h2[0]
ind_store = lines[i_store][:len(lines[i_store]) - len(lines[i_store].lstrip())]
ins_b = [ind_store + '// target_url/prev_url: 供爬虫状态机 Phase 0 判断"页面是否真的换了"。',
         ind_store + '// 实测缺陷: 冷启动第一次 scrape 会在 0.03s 内返回**欢迎页**的 h1 —— 因为 载入地址',
         ind_store + '// 刚调用时 容器.取加载状态() 仍是"未加载", Phase 0 立刻以为加载完成就去提取了当前页。',
         ind_store + 'sStore.加入文本成员 ("target_url", sUrl)',
         ind_store + 'sStore.加入文本成员 ("prev_url", sPrevUrl)']
lines[i_store:i_store] = ins_b
print('   A2 已插入 target_url/prev_url 存储(%d 行)' % len(ins_b))

# ---------- B. Phase 0 增加"页面确实换了"的前置门 ----------
anchor = '如果 (浏览器容器.取加载状态 () == 假)'
cand = [i for i in find_line(anchor) if i > i_store]
print('B 锚点 取加载状态 命中(爬虫区之后) %d 处: %s' % (len(cand), [i + 1 for i in cand]))
if len(cand) != 1:
    print('!! 锚点不唯一, 中止')
    sys.exit(1)
i_gate = cand[0]
ind_gate = lines[i_gate][:len(lines[i_gate]) - len(lines[i_gate].lstrip())]
new_gate = [
    ind_gate + '// 必须**先确认页面真的换成了目标页**, 再看加载状态 ——',
    ind_gate + '// 否则导航尚未开始时 取加载状态()=="未加载" 会被误判为"已加载完成",',
    ind_gate + '// 于是从**上一个页面**(冷启动时是欢迎页)提取, 返回静默错数据。',
    ind_gate + '变量 sTargetUrl <类型 = 文本型>',
    ind_gate + 'sTargetUrl = MCP命令服务器.yyjson取文本 (结果解析, "target_url")',
    ind_gate + '变量 sPrevUrl2 <类型 = 文本型>',
    ind_gate + 'sPrevUrl2 = MCP命令服务器.yyjson取文本 (结果解析, "prev_url")',
    ind_gate + '变量 sCurUrl <类型 = 文本型>',
    ind_gate + 'sCurUrl = ""',
    ind_gate + '变量 sCurFrame <类型 = 类_FBrowser_框架>',
    ind_gate + 'sCurFrame = MCP命令服务器.取安全主框架 (scrapeBrowser)',
    ind_gate + '如果 (sCurFrame.是否为空 () == 假)',
    ind_gate + '{',
    ind_gate + '    sCurUrl = sCurFrame.取地址 ()',
    ind_gate + '}',
    ind_gate + '变量 sPageChanged <类型 = 逻辑型>',
    ind_gate + 'sPageChanged = 真',
    ind_gate + '// 目标与旧地址不同, 但当前地址**仍是旧地址** -> 页面还没换过去, 继续等',
    ind_gate + '如果 (sTargetUrl != "" && sPrevUrl2 != "" && sTargetUrl != sPrevUrl2 && sCurUrl == sPrevUrl2)',
    ind_gate + '{',
    ind_gate + '    sPageChanged = 假',
    ind_gate + '}',
    ind_gate + '如果 (sPageChanged && 浏览器容器.取加载状态 () == 假)',
]
lines[i_gate:i_gate + 1] = new_gate
print('   B 已把 Phase 0 判据扩为 sPageChanged && 取加载状态()==假 (%d 行)' % len(new_gate))

out = nl.join(lines)
# 转义自查
for ln in out.split(nl):
    if ln.count('"') % 2 != 0 and (ln.strip().startswith('sStore.') or ln.strip().startswith('sTargetUrl =')
                                   or ln.strip().startswith('sPrevUrl2 =') or ln.strip().startswith('sCurUrl =')):
        print('!! 疑似未配对的裸双引号: %s' % ln.strip()[:100])
        sys.exit(1)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Core.wsv'))
open(SRC, 'wb').write(out.encode('utf-8'))
print('已写入; 备份 -> %s' % BAK)
print('复核: target_url 出现 %d 次, prev_url %d 次, sPageChanged %d 次'
      % (out.count('target_url'), out.count('prev_url'), out.count('sPageChanged')))
