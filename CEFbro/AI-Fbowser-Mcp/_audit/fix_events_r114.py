# -*- coding: utf-8 -*-
"""三处修补(全部有实测/取证依据):

① `browser_event` 的**通配查询是坏的**: 工具描述与错误提示都要求用族名 `resource_* / frame_* /
   download_* / focus_* / app_*` 查询, 而 `查询事件日志` 用的是 SQL **精确相等** `event_name=?`
   -> 照文档操作 100% 查不到。改为: 含 `*` 或 `%` 时走 `LIKE ?`(把 `*` 换成 `%`), 否则仍是精确相等。
② 同一分支里应用事件被写死 `限制条数=1`(查询 app_* 时永远只回 1 条) -> 改用调用方给的 evtLimit。
③ `browser_kernel_events_all` 的文案有三个数字在流传(缺参提示 13 / 注释 13 / 成功文案 21),
   而实现实际开关 **26** 个(已逐行数过, enable 与 disable 对称)。改为如实说明。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '事件通配与文案-写入前')
problems = []


def load(p):
    t = open(p, 'rb').read().decode('utf-8')
    return t, ('\r\n' if '\r\n' in t else '\n')


def rep(text, old, new, tag, nl='\n', n=1):
    o = old.replace('\n', nl)
    c = text.count(o)
    if c != n:
        problems.append('%s: 命中 %d 次(应 %d)' % (tag, c, n))
        return text
    for ln in new.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号: %s' % (tag, ln.strip()[:90]))
            return text
    print('   ok %s' % tag)
    return text.replace(o, new.replace('\n', nl), n)


def save(src, text, name):
    os.makedirs(BAK, exist_ok=True)
    dst = os.path.join(BAK, name)
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
    open(src, 'wb').write(text.encode('utf-8'))


# ─────────── ① Server: 事件名通配 ───────────
s, nl = load(os.path.join(SRC, 'MCP_Server.wsv'))
s = rep(s, '''        如果 (事件名 != "")
        {
            paramIdx = paramIdx + 1
            条件SQL = 条件SQL + " AND event_name=?  "
            hasEvent = 真
        }
''', '''        变量 事件名绑定值 <类型 = 文本型>
        事件名绑定值 = 事件名
        如果 (事件名 != "")
        {
            paramIdx = paramIdx + 1
            // 族名通配: 工具描述与错误提示都承诺可用 resource_* / frame_* / download_* / focus_* / app_*,
            // 但这里原本是精确相等 —— 照文档操作必然查不到。含 * 或 % 时改用 LIKE(把 * 当 % 用)。
            如果 (寻找文本 (事件名, "*", 0, 假) != -1 || 寻找文本 (事件名, "%", 0, 假) != -1)
            {
                子文本替换 (事件名绑定值, "*", "%", , , 假)
                条件SQL = 条件SQL + " AND event_name LIKE ?  "
            }
            否则
            {
                条件SQL = 条件SQL + " AND event_name=?  "
            }
            hasEvent = 真
        }
''', 'Server 事件名通配(LIKE)', nl)
s = rep(s, '''        如果 (hasEvent)
        {
            paramIdx = paramIdx + 1
            记录集.置文本参数数据 (paramIdx, 事件名)
        }
''', '''        如果 (hasEvent)
        {
            paramIdx = paramIdx + 1
            记录集.置文本参数数据 (paramIdx, 事件名绑定值)
        }
''', 'Server 绑定通配后的值', nl)
save(os.path.join(SRC, 'MCP_Server.wsv'), s, 'MCP_Server.wsv')

# ─────────── ② Core: 应用事件不再写死 limit=1 ───────────
c, nl2 = load(os.path.join(SRC, 'MCP_Server_Core.wsv'))
c = rep(c, '                    appResult = MCP命令服务器.查询事件日志 ("app_event", evtType, 0, 1)\n',
        '                    // 用调用方给的条数: 原先写死 1, 导致查 app_* 族时永远只回 1 条\n'
        '                    appResult = MCP命令服务器.查询事件日志 ("app_event", evtType, 0, evtLimit)\n',
        'Core 应用事件改用 evtLimit', nl2)
c = rep(c, '下载_*/key_press/focus_* | 应用事件: app_*',
        '下载_*/key_press/focus_* | 应用事件: app_* | 族名可用通配(如 resource_* / frame_* / app_*)',
        'Core 错误提示补通配说明', nl2)
save(os.path.join(SRC, 'MCP_Server_Core.wsv'), c, 'MCP_Server_Core.wsv')

# ─────────── ③ Kernel: 文案数字改为实测值 26 ───────────
k, nl3 = load(os.path.join(SRC, 'MCP_Kernel.wsv'))
k = rep(k, '省略会直接执行 enable 并使13 项监控立即生效',
        '省略会直接执行 enable 并使 26 个监控/记录开关立即生效', 'Kernel 缺参文案', nl3)
k = rep(k, '            // 浏览器事件全开 (13项)\n',
        '            // 浏览器/应用事件族 + 日志 全开(26 个开关, 与 disable 分支逐项对称)\n',
        'Kernel 注释', nl3)
k = rep(k, '"全事件流已开启: 21项浏览器/应用事件族 + 控制台 + 网络详细 | 查询: browser_event / browser_network list / browser_collect console_get"',
        '"全事件流已开启: 26 个开关(13 核心事件族 + 3 日志 + 10 扩展事件族), 与 disable 完全对称 | 查询: browser_event(支持 resource_* 等族名通配) / browser_network list / browser_collect console_get"',
        'Kernel 成功文案', nl3)
save(os.path.join(SRC, 'MCP_Kernel.wsv'), k, 'MCP_Kernel.wsv')

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
