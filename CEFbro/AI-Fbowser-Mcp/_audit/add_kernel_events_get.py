# -*- coding: utf-8 -*-
"""给 `browser_kernel_events_all` 补上 **`action=get`**。

发现路径: 我写验收脚本时想用一个"独立观测器"读那 26 个开关的真值, 调 `action=get` 却得到
"action 须为 enable/disable" —— 而该工具**自己的缺参提示**里明确写着
"查询状态请显式传 action:get"(MCP_Kernel.wsv 内的文案)。即: ① 文案承诺了不存在的动作;
② 用户/代理**根本没有任何办法查看当前哪些事件监控是开的**(只能靠事件有没有进来反推)。

本脚本补 `get`: 回 26 个开关的真值 + enabled_count/total, 使文案成立且状态可观测。
字段清单以 `MCP_Kernel.wsv` enable 分支为唯一来源(26 项)。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Kernel.wsv')
BAK = os.path.join(ROOT, '备份', '内核事件开关get-写入前')

text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'

start = text.find('如果 (动作 == "enable" || 动作 == "")')
end = text.find('全事件流已开启', start)
FIELDS = []
for f in re.findall(r'MCP命令服务器\.(是否\S+|是否记录\S+) = 真', text[start:end]):
    if f not in FIELDS:
        FIELDS.append(f)
print('字段数 = %d' % len(FIELDS))
if len(FIELDS) != 26:
    print('!! 预期 26 项, 中止')
    sys.exit(1)

# 造 get 分支
L = []
L.append('        如果 (动作 == "get")')
L.append('        {')
L.append('            // 只读: 回报 26 个开关的真值(此前工具文案承诺 action:get 但并未实现, 导致状态不可观测)')
L.append('            变量 evt状态 <类型 = YYJSON对象类>')
L.append('            evt状态.创建自文本 ("{}")')
L.append('            变量 evt已开 <类型 = 整数>')
L.append('            evt已开 = 0')
for f in FIELDS:
    L.append('            如果 (MCP命令服务器.%s)' % f)
    L.append('            {')
    L.append('                evt已开 = evt已开 + 1')
    L.append('            }')
for f in FIELDS:
    L.append('            evt状态.加入逻辑值成员 ("%s", MCP命令服务器.%s)' % (f, f))
L.append('            evt状态.加入整数成员 ("enabled_count", evt已开)')
L.append('            evt状态.加入整数成员 ("total", %d)' % len(FIELDS))
L.append('            返回 (MCP_响应构建.命令成功_原始JSON (命令ID, evt状态.到可读文本 (YYJSON格式化选项.压缩)))')
L.append('        }')
GET_BLOCK = "\n".join(L)

OLD_TAIL = '        返回 (MCP_响应构建.命令失败 (命令ID, "action 须为 enable/disable"))\n'
if text.count(OLD_TAIL.replace('\n', nl)) != 1:
    print('!! 收尾锚点命中 %d 次' % text.count(OLD_TAIL.replace('\n', nl)))
    sys.exit(1)
text = text.replace(OLD_TAIL.replace('\n', nl),
                    GET_BLOCK.replace('\n', nl) + nl +
                    '        返回 (MCP_响应构建.命令失败 (命令ID, "action 须为 enable/disable/get"))\n'.replace('\n', nl), 1)

os.makedirs(BAK, exist_ok=True)
dst = os.path.join(BAK, os.path.basename(P))
if not os.path.exists(dst):
    shutil.copy2(P, dst)
open(P, 'wb').write(text.encode('utf-8'))
print('已插入 action=get (共 %d 行)' % (GET_BLOCK.count('\n') + 1))
