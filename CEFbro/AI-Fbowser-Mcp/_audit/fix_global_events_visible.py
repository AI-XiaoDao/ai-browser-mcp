# -*- coding: utf-8 -*-
"""让"浏览器无关联"的事件(browser_id=0)也能被查到。

发现路径: 12 个新事件接线后, `devtools_attached` 能查到(它记的是 浏览器.取ID()), 而
`urlreq_start`/`urlreq_download`/`urlreq_auth` 查不到 —— 因为 MCP_Callbacks 里这三处记的是
`记录浏览器事件 ("urlreq_start", 0, …)`(URL 请求没有浏览器上下文, 用 0 表示"与浏览器无关"),
而 `查询事件日志` 是按**当前浏览器ID** 过滤的(`browser_id=?`), 于是这些行**永远查不出来**。

项目里本来就有同类先例: `browser_event` 对 `crash` 事件把查询 ID 置 0(见 Core 里
"crash 事件跨浏览器查询" 的注释)。本改动把那个特例**推广成通则**:
查询某个浏览器时, 同时纳入 browser_id=0 的"全局/无关联"事件。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', '全局事件可查-写入前')

text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'

OLD = '''        如果 (浏览器ID > 0)
        {
            paramIdx = paramIdx + 1
            条件SQL = 条件SQL + " AND browser_id=?  "
            hasBID = 真
        }
'''
NEW = '''        如果 (浏览器ID > 0)
        {
            paramIdx = paramIdx + 1
            // 同时纳入 browser_id=0 的"与浏览器无关"事件(自建 URL 请求 urlreq_*、crash 等)。
            // 这些事件没有浏览器上下文, 记录侧用 0 表示全局; 若这里只按具体ID过滤, 它们**永远查不出来**
            // (实测: urlreq_start 记录成功但 browser_event 查不到)。此前只有 crash 在调用侧特判,
            // 现推广为通则。
            条件SQL = 条件SQL + " AND (browser_id=? OR browser_id=0)  "
            hasBID = 真
        }
'''
if text.count(OLD.replace('\n', nl)) != 1:
    print('!! 锚点命中 %d 次, 未改' % text.count(OLD.replace('\n', nl)))
    sys.exit(1)
text = text.replace(OLD.replace('\n', nl), NEW.replace('\n', nl), 1)

os.makedirs(BAK, exist_ok=True)
dst = os.path.join(BAK, 'MCP_Server.wsv')
if not os.path.exists(dst):
    shutil.copy2(P, dst)
open(P, 'wb').write(text.encode('utf-8'))
print('已改为 AND (browser_id=? OR browser_id=0)')
