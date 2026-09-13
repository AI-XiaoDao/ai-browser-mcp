# -*- coding: utf-8 -*-
"""给 browser_back / browser_forward 补 wait_for_load（复用 注册加载等待任务，同 navigate/reload）。

动机: 现状是"调用完立刻回 success(已后退)", **等页面载入与否完全不管** ——
AI 紧接着读 DOM/点击时可能还在旧页面(或空白), 属"调用了但没准备好"的观感类问题。
navigate/reload 早就有这套(记录发起时刻 -> 注册加载等待任务 -> 判序 load_end),
back/forward 只是没接上去 => 典型"不重复造轮子"。

默认值: 先与 navigate/reload 保持一致(默认真), 随后**真机验收**:
  若历史导航命中 bfcache 而不触发 load_end, 会表现为超时 -> 再把默认改为假(显式传 true 才等)。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '前后退补等待载入-写入前')

text = io.open(SRC, encoding='utf-8').read()
nl = '\n'

BACK_OLD = '''            如果 (browser.是否为空 () == 假 && browser.可否后退 ())
            {
                browser.后退 ()
                返回 (MCP_响应构建.命令成功 (命令ID, "已后退"))
            }
'''
BACK_NEW = '''            如果 (browser.是否为空 () == 假 && browser.可否后退 ())
            {
                // 与 navigate/reload 同款: **载入前**记录发起时刻, 供 注册加载等待任务 判序
                // load_end 是否属于本次历史导航(否则会把上一次的 load_end 误当成本次完成)。
                变量 后退发起毫秒 <类型 = 长整数>
                后退发起毫秒 = 取启动时间 ()
                browser.后退 ()
                变量 bkWaitLoad <类型 = 逻辑型>
                bkWaitLoad = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "wait_for_load", 真)
                如果 (bkWaitLoad && MCP命令服务器.yyjson取逻辑 (参数JSON, "async_only") == 假)
                {
                    返回 (MCP命令服务器.注册加载等待任务 (命令ID, 参数JSON, browser, "等待后退完成", "已后退 | 等待载入完成, 通过mcp_result查询", 后退发起毫秒))
                }
                返回 (MCP_响应构建.命令成功 (命令ID, "已后退"))
            }
'''

FWD_OLD = '''            如果 (browser.是否为空 () == 假 && browser.可否前进 ())
            {
                browser.前进 ()
                返回 (MCP_响应构建.命令成功 (命令ID, "已前进"))
            }
'''
FWD_NEW = '''            如果 (browser.是否为空 () == 假 && browser.可否前进 ())
            {
                // 同 后退: 记录发起时刻后再前进, 交由 注册加载等待任务 等待本次载入完成
                变量 前进发起毫秒 <类型 = 长整数>
                前进发起毫秒 = 取启动时间 ()
                browser.前进 ()
                变量 fwWaitLoad <类型 = 逻辑型>
                fwWaitLoad = MCP命令服务器.yyjson取逻辑_默认 (参数JSON, "wait_for_load", 真)
                如果 (fwWaitLoad && MCP命令服务器.yyjson取逻辑 (参数JSON, "async_only") == 假)
                {
                    返回 (MCP命令服务器.注册加载等待任务 (命令ID, 参数JSON, browser, "等待前进完成", "已前进 | 等待载入完成, 通过mcp_result查询", 前进发起毫秒))
                }
                返回 (MCP_响应构建.命令成功 (命令ID, "已前进"))
            }
'''

for old, new, tag in ((BACK_OLD, BACK_NEW, 'browser_back'), (FWD_OLD, FWD_NEW, 'browser_forward')):
    c = text.count(old)
    print('%s 锚点命中 %d (应为1)' % (tag, c))
    if c != 1:
        print('!! 中止')
        sys.exit(1)
    for ln in new.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            print('!! 裸双引号奇数: %s' % ln.strip()[:90])
            sys.exit(1)
    text = text.replace(old, new, 1)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Core.wsv'))
open(SRC, 'wb').write(text.encode('utf-8'))
print('已写入; 备份 -> %s' % BAK)
print('复核 注册加载等待任务 调用点数: %d' % text.count('注册加载等待任务 ('))
