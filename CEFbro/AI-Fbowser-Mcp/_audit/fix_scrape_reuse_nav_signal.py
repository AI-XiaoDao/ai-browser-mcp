# -*- coding: utf-8 -*-
"""让 browser_scrape 的 Phase 0 复用**项目已有的正确技术**（不重复造轮子）。

背景: 上一轮已修掉"冷启动首调返回欢迎页数据"的竞态(靠"页面地址变了"判定)。
本轮读源码发现: `browser_navigate` **早就有更硬的判据** ——
  ① 载入地址**之前**记录 `导航发起毫秒`（MCP_Server_Core.wsv:136-139）
  ② 交给 `注册加载等待任务`，其判据是
     `浏览器容器.取加载状态 () == 假 && 导航发起毫秒 > 0 && 浏览器容器.取最后载入结束毫秒 () >= 导航发起毫秒`
     （MCP_Server.wsv:6612）—— 即"**本次导航之后**确实发生过一次载入结束"。
`browser_scrape` 当时是自己手写了一个更弱的 Phase 0，才会漏掉这个竞态。

本改动: 让 scrape 也采同一信号，并与上一轮的"地址已变"取**或**关系 —— 两种证据任一成立即认为导航已发生:
  · 地址变了（覆盖跳转/重定向）
  · 载入结束时刻 >= 本次导航发起时刻（覆盖"目标就是当前页/原地重载，地址不变"的情形）
从而既不误判（拿旧页面数据），也不至于在地址不变时死等。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '爬虫复用导航判据-写入前')

text = io.open(SRC, encoding='utf-8').read()
nl = '\n'

# ---- 1) 外层声明 sNavStart(与 sPrevUrl 同处, 保证块外可见) ----
OLD1 = ('            变量 sPrevUrl <类型 = 文本型>\n'
        '            sPrevUrl = ""\n')
NEW1 = ('            变量 sPrevUrl <类型 = 文本型>\n'
        '            sPrevUrl = ""\n'
        '            // 本次导航发起时刻: 与 browser_navigate 同款判据(载入结束时刻 >= 本时刻 才算"本次导航已完成")\n'
        '            变量 sNavStart <类型 = 长整数>\n'
        '            sNavStart = 0\n')
c1 = text.count(OLD1)
print('锚点1(sPrevUrl 声明) 命中 %d (应为1)' % c1)
if c1 != 1:
    sys.exit(1)
text = text.replace(OLD1, NEW1, 1)

# ---- 2) 导航前记录发起时刻 ----
OLD2 = '                sPrevUrl = sFrame.取地址 ()\n'
NEW2 = ('                sPrevUrl = sFrame.取地址 ()\n'
        '                sNavStart = 取启动时间 ()\n')
c2 = text.count(OLD2)
print('锚点2(sPrevUrl 赋值) 命中 %d (应为1)' % c2)
if c2 != 1:
    sys.exit(1)
text = text.replace(OLD2, NEW2, 1)

# ---- 3) 存进任务 ----
OLD3 = '            sStore.加入文本成员 ("prev_url", sPrevUrl)\n'
NEW3 = ('            sStore.加入文本成员 ("prev_url", sPrevUrl)\n'
        '            sStore.加入长整数成员 ("nav_start_ms", sNavStart)\n')
c3 = text.count(OLD3)
print('锚点3(prev_url 存储) 命中 %d (应为1)' % c3)
if c3 != 1:
    sys.exit(1)
text = text.replace(OLD3, NEW3, 1)

# ---- 4) Phase 0 判据: 地址已变 或 载入已结束 ----
OLD4 = ('                                    如果 (sPageChanged && 浏览器容器.取加载状态 () == 假)\n')
NEW4 = ('                                    // 第二条证据(与 browser_navigate 同款): 本次导航发起之后确实发生过一次载入结束。\n'
        '                                    // 它能覆盖"目标就是当前页/原地重载, 地址不变"的情形, 与地址判据互补。\n'
        '                                    变量 sNavStartMs <类型 = 长整数>\n'
        '                                    sNavStartMs = MCP命令服务器.yyjson取长整数 (结果解析, "nav_start_ms")\n'
        '                                    变量 sLoadEnded <类型 = 逻辑型>\n'
        '                                    sLoadEnded = 假\n'
        '                                    如果 (sNavStartMs > 0 && MCP命令服务器.取最后载入结束毫秒 () >= sNavStartMs)\n'
        '                                    {\n'
        '                                        sLoadEnded = 真\n'
        '                                    }\n'
        '                                    如果 ((sPageChanged || sLoadEnded) && 浏览器容器.取加载状态 () == 假)\n')
c4 = text.count(OLD4)
print('锚点4(Phase0 门) 命中 %d (应为1)' % c4)
if c4 != 1:
    sys.exit(1)
text = text.replace(OLD4, NEW4, 1)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Core.wsv'))
open(SRC, 'wb').write(text.encode('utf-8'))
print('已写入; 备份 -> %s' % BAK)
for k in ('sNavStart', 'nav_start_ms', 'sLoadEnded', '取最后载入结束毫秒'):
    print('  复核 %-20s 出现 %d 次' % (k, text.count(k)))
