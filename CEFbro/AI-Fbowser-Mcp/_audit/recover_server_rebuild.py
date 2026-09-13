# -*- coding: utf-8 -*-
"""恢复并重建 MCP_Server.wsv(带精确花括号增量校验)。

事故: delete_dead_methods.py 把 `extract_block` 的 b1 当成"收尾大括号所在行", 实际它是方法体最后一行,
于是每个方法都少删一行 —— 8 个收尾 `}` 残留 => 花括号失衡 => `类 MCP命令服务器` 编译不出来
=> 其它 9 个文件里 `MCP命令服务器.` 引用级联报"没有找到所指定的常量/变量/参数名称"。

本脚本:
 ① 从干净快照 `备份/删除死方法-写入前/MCP_Server.wsv` 恢复;
 ② 用**自己数花括号**定位收尾 `}`, 逐段删除并断言"该段 { 与 } 数量相等";
 ③ 重放本轮 Server 侧的其余 3 组改动(schema ×2 / 注册 ×2 / 事件名通配);
 ④ 校验最终花括号计数 == 快照 - 删掉的 + 重放新增的, 且进出各自配平。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
CLEAN = os.path.join(ROOT, '备份', '删除死方法-写入前', 'MCP_Server.wsv')
BAK2 = os.path.join(ROOT, '备份', '花括号事故恢复-写入前')

TARGETS = [
    ("尝试恢复欢迎页导航", "TryRestoreWelcomePageNavigate"),
    ("尝试导航欢迎页", "TryNavigateWelcomePage"),
    ("CDP获取脚本源", "CDPGetScriptSource"),
    ("分派网络日志命令", "DispatchNetworkLogCommand"),
    ("解析匹配模式", "ParseMatchMode"),
    ("记录网络日志项", "RecordNetworkLogItem"),
    ("规范化URL", "NormalizeURL"),
    ("发送CORS500响应", "SendCORS500Response"),
]


def count_braces(lines):
    o = c = 0
    for ln in lines:
        if ln.lstrip().startswith('@'):
            continue
        body = re.sub(r'"[^"]*"', '""', ln).split('//')[0]
        o += body.count('{')
        c += body.count('}')
    return o, c


def find_close(lines, start):
    j = start
    while j < len(lines) and '{' not in re.sub(r'"[^"]*"', '""', lines[j]):
        j += 1
    depth = 0
    while j < len(lines):
        body = re.sub(r'"[^"]*"', '""', lines[j]).split('//')[0]
        depth += body.count('{') - body.count('}')
        if depth == 0:
            return j
        j += 1
    return None


if not os.path.exists(CLEAN):
    print('!! 找不到干净快照 %s' % CLEAN)
    sys.exit(1)
os.makedirs(BAK2, exist_ok=True)
if os.path.exists(SRC) and not os.path.exists(os.path.join(BAK2, 'MCP_Server.wsv')):
    shutil.copy2(SRC, os.path.join(BAK2, 'MCP_Server.wsv'))

text = open(CLEAN, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split('\n')
base_o, base_c = count_braces(lines)
print('恢复自干净快照: %d 行, 花括号 {%d }%d' % (len(lines), base_o, base_c))

all_text = "\n".join(lines)
for mname, sym in TARGETS:
    if all_text.count(mname) != 1 or all_text.count(sym) != 1:
        print('!! %s 引用计数不为 1, 中止' % mname)
        sys.exit(1)

spans = []
rem_o = rem_c = 0
for mname, sym in TARGETS:
    i0 = next(i for i, ln in enumerate(lines) if re.match(r'\s*方法\s+' + re.escape(mname) + r'\s', ln))
    top = i0
    while top - 1 >= 0 and lines[top - 1].strip().startswith('#'):
        top -= 1
    bot = find_close(lines, i0)
    if bot is None or lines[bot].strip() != '}':
        print('!! %s 收尾大括号定位失败 (bot=%s)' % (mname, bot))
        sys.exit(1)
    seg = lines[top:bot + 1]
    so, sc = count_braces(seg)
    if so != sc:
        print('!! %s 段落花括号不配平 {%d }%d' % (mname, so, sc))
        sys.exit(1)
    spans.append((top, bot, mname, bot - top + 1))
    rem_o += so
    rem_c += sc

for top, bot, mname, n in sorted(spans, key=lambda x: -x[0]):
    del lines[top:bot + 1]
    while top < len(lines) and top - 1 >= 0 and lines[top].strip() == '' and lines[top - 1].strip() == '':
        del lines[top]
    print('   删除 %-18s %2d 行' % (mname, n))
o, c = count_braces(lines)
exp_o, exp_c = base_o - rem_o, base_c - rem_c
print('删除后花括号 {%d }%d, 期望 {%d }%d -> %s' % (o, c, exp_o, exp_c, 'OK' if (o, c) == (exp_o, exp_c) else '★不符'))
if (o, c) != (exp_o, exp_c):
    sys.exit(1)

text = "\n".join(lines)
problems = []
rep_o = rep_c = 0


def rep(t, old, new, tag):
    global rep_o, rep_c
    oo = old.replace('\n', nl)
    if t.count(oo) != 1:
        problems.append('%s: 命中 %d 次' % (tag, t.count(oo)))
        return t
    for ln in new.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号: %s' % (tag, ln.strip()[:80]))
            return t
    a, b = count_braces(old.split('\n'))
    a2, b2 = count_braces(new.split('\n'))
    rep_o += a2 - a
    rep_c += b2 - b
    print('   ok %s (花括号增量 {%+d }%+d)' % (tag, a2 - a, b2 - b))
    return t.replace(oo, new.replace('\n', nl), 1)


lines = text.split('\n')


def insert_after(needle, block, tag):
    """按唯一子串定位行, 用**该行自身缩进**插入(不手数空格)。"""
    global rep_o, rep_c
    idx = [i for i, ln in enumerate(lines) if needle in ln]
    if len(idx) != 1:
        problems.append('%s: 定位 %d 行' % (tag, len(idx)))
        return
    i = idx[0]
    ind = ' ' * (len(lines[i]) - len(lines[i].lstrip(' ')))
    body = [ind + b if b else '' for b in block]
    for b in body:
        if b and b.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号: %s' % (tag, b.strip()[:90]))
            return
    a, c1 = count_braces('\n'.join(body).split('\n'))
    rep_o += a
    rep_c += c1
    lines[i + 1:i + 1] = body
    print('   ok %s (插在第 %d 行后, 花括号 {%+d }%+d)' % (tag, i + 1, a, c1))


def replace_line(needle, new_body, tag):
    global rep_o, rep_c
    idx = [i for i, ln in enumerate(lines) if needle in ln]
    if len(idx) != 1:
        problems.append('%s: 定位 %d 行' % (tag, len(idx)))
        return
    i = idx[0]
    ind = ' ' * (len(lines[i]) - len(lines[i].lstrip(' ')))
    body = ind + new_body
    if body.replace('\\"', '').count('"') % 2 != 0:
        problems.append('%s: 裸引号奇数' % tag)
        return
    a0, c0 = count_braces([lines[i]])
    a1, c1 = count_braces([body])
    rep_o += a1 - a0
    rep_c += c1 - c0
    lines[i] = body
    print('   ok %s (改第 %d 行)' % (tag, i + 1))


insert_after('置整数值 ("browser_frame_by_name"',
             ['命令注册表.置整数值 ("browser_frame_by_id", 1325)'],
             '注册表 frame_by_id')

insert_after('添加工具JSON ("browser_frame_by_name"',
             ['添加工具JSON ("browser_frame_by_id", "按框架ID取框架信息(与 browser_frame_by_name 对称)。'
              'browser_get_frames 给出的 frame_id 可直接用; 找不到框架不算失败, 会回 found:false + hint'
              '(导航/刷新后旧 ID 失效, 请重新取)", '
              '单参数Schema文本 ("frame_id", "text", "框架ID(取自 browser_get_frames)"))'],
             '注册 frame_by_id 工具')

replace_line('添加工具JSON ("browser_uri_encode"',
             '添加工具JSON ("browser_uri_encode", "URI编码(百分号编码, 与 JS encodeURIComponent 基本一致)。'
             '字母数字与 -_.!~* 等少数字符之外都会变成 %XX; 空格默认 %20, use_plus:true 时变成 + (表单语义)", '
             '多属性Schema文本 (属性项JSON ("data", "text", "要编码的文本") + "," + '
             '属性项JSON ("use_plus", "boolean", "true=空格编码为 + / false(默认)=空格编码为 %20"), "\\"data\\""))',
             'uri_encode schema')

replace_line('添加工具JSON ("browser_uri_decode"',
             '添加工具JSON ("browser_uri_decode", "URI解码(百分号还原)。默认把 %20/%26/%3D 等全部还原成字符; '
             'keep_escaped:true 则保留 ASCII 特殊字符的转义(旧行为, 只还原非 ASCII)", '
             '多属性Schema文本 (属性项JSON ("data", "text", "要解码的文本") + "," + '
             '属性项JSON ("to_utf8", "boolean", "true(默认)=把解码结果按 UTF-8 解释") + "," + '
             '属性项JSON ("keep_escaped", "boolean", "true=保留 ASCII 特殊字符转义 / false(默认)=全部还原"), "\\"data\\""))',
             'uri_decode schema')

text = "\n".join(lines)

text = rep(text, '''        如果 (事件名 != "")
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
''', '事件名通配(LIKE)')

text = rep(text, '''        如果 (hasEvent)
        {
            paramIdx = paramIdx + 1
            记录集.置文本参数数据 (paramIdx, 事件名)
        }
''', '''        如果 (hasEvent)
        {
            paramIdx = paramIdx + 1
            记录集.置文本参数数据 (paramIdx, 事件名绑定值)
        }
''', '绑定通配后的值')

if problems:
    print('!! 重放未全部成功, 未写文件: %r' % problems)
    sys.exit(1)

lines = text.split('\n')
o2, c2 = count_braces(lines)
want_o, want_c = exp_o + rep_o, exp_c + rep_c
ok = (o2, c2) == (want_o, want_c) and rep_o == rep_c
print('最终花括号 {%d }%d, 期望 {%d }%d, 重放增量 {%+d }%+d -> %s'
      % (o2, c2, want_o, want_c, rep_o, rep_c, 'OK' if ok else '★不符'))
if not ok:
    sys.exit(1)
open(SRC, 'wb').write(text.encode('utf-8'))
print('重建完成: %d 行' % len(lines))
