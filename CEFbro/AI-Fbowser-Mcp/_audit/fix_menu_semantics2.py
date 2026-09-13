# -*- coding: utf-8 -*-
"""续修: 上一轮 7 个锚点因**缩进空格数猜错**(16 vs 17、20 vs 21)未命中。
这次一律"先用唯一子串定位, 再取该行自身缩进"来生成替换, 不再手数空格。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
SERVER = os.path.join(SRC, 'MCP_Server.wsv')
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')
problems = []


def load(path):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % path
    t = data.decode('utf-8')
    return t, ('\r\n' if '\r\n' in t else '\n')


def save(path, text):
    open(path, 'wb').write(text.encode('utf-8'))
    print('   写入 %s' % os.path.basename(path))


def q_ok(txt, tag):
    for ln in txt.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号奇数: %s' % (tag, ln.strip()[:90]))
            return False
    return True


def rep(text, needle, repl, tag, n=1):
    c = text.count(needle)
    if c != n:
        problems.append('%s: 命中 %d 次(应 %d): %r' % (tag, c, n, needle[:60]))
        return text
    if not q_ok(repl, tag):
        return text
    print('   ok %s' % tag)
    return text.replace(needle, repl)


def line_of(text, needle, tag, n=1):
    """返回 (行号列表, 缩进, 整行)。"""
    lines = text.split('\n')
    idx = [i for i, ln in enumerate(lines) if needle in ln]
    if len(idx) != n:
        problems.append('%s: 定位 %d 行(应 %d): %r' % (tag, len(idx), n, needle[:60]))
        return None
    i = idx[0]
    ind = len(lines[i]) - len(lines[i].lstrip(' '))
    return i, ' ' * ind, lines[i]


# ═══════════════════ Server: S13 公共快捷键块读回确认 ═══════════════════
s, nl = load(SERVER)
got = line_of(s, '目标模型.设置快捷键 (条目命令ID, 文本到整数 (键码文本)', 'S13 定位')
if got:
    i, ind, whole = got
    new = (ind + '如果 (目标模型.设置快捷键 (条目命令ID, 文本到整数 (键码文本), 是否Shift, 是否Ctrl, 是否Alt) && 目标模型.存在快捷键 (条目命令ID))\n'
           + ind + '{\n'
           + ind + '    // 读回确认通过才计数(默认项上 设置快捷键 会返回真却实际不留痕)\n'
           + ind + '    如果 (条目类型 == "accel")\n'
           + ind + '    {\n'
           + ind + '        施加条数 = 施加条数 + 1\n'
           + ind + '    }\n'
           + ind + '}\n'
           + ind + '否则\n'
           + ind + '{\n'
           + ind + '    失败条数 = 失败条数 + 1\n'
           + ind + '    失败明细 = 失败明细 + 菜单失败说明 ("accel", 条目命令ID)\n'
           + ind + '}')
    if q_ok(new, 'S13'):
        lines = s.split('\n')
        lines[i] = new
        s = '\n'.join(lines)
        print('   ok S13 公共快捷键块读回确认')

# ═══════════════════ Server: S14 item 创建失败记录 ═══════════════════
got = line_of(s, '如果 (目标模型.添加菜单 (条目命令ID, 条目标签))', 'S14 定位')
if got:
    i, ind, whole = got
    lines = s.split('\n')
    # 找到与该 如果 同缩进的收尾 '}'
    j = None
    for k in range(i + 1, len(lines)):
        if lines[k] == ind + '}':
            j = k
            break
    if j is None:
        problems.append('S14: 找不到收尾大括号')
    else:
        blk = [ind + '否则',
               ind + '{',
               ind + '    失败条数 = 失败条数 + 1',
               ind + '    失败明细 = 失败明细 + "[item " + 到文本 (条目命令ID) + " 创建失败: 命令ID 可能已被占用] "',
               ind + '}']
        if q_ok('\n'.join(blk), 'S14'):
            lines[j + 1:j + 1] = blk
            s = '\n'.join(lines)
            print('   ok S14 item 创建失败记录(插在第 %d 行后)' % (j + 1))
save(SERVER, s)

# ═══════════════════ Core ═══════════════════
c, nl2 = load(CORE)

# C4: 别名类错误文案(该行很长, 用其自身缩进整行替换)
got = line_of(c, '行是修改类(', 'C4 定位')
if got:
    i, ind, whole = got
    new = (ind + '返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行是修改类(" + cm类型 + ")但命令ID无法识别: [" + cm段.取成员 (2) + "] | 修改类必须给出已存在的命令ID: 用你自建项的 26500..28500(别名 back/forward/reload/reload_nocache/stop/undo/redo/cut/copy/paste/delete/selectall/find/print/viewsource/nosuggestions/addtodict 与标准ID 如 back=100 也能解析, 但实测默认项改不动)"))')
    if q_ok(new, 'C4'):
        lines = c.split('\n')
        lines[i] = new
        c = '\n'.join(lines)
        print('   ok C4 别名错误文案校正')

# C9: 两处重置(默认分支 + clear 分支)
c = rep(c, '                MCP命令服务器.菜单最近施加条数 = 0\n',
        '                MCP命令服务器.菜单最近施加条数 = 0\n                MCP命令服务器.菜单施加失败 = ""\n',
        'C9 重置失败字段', 2)

# C10: set 回包加 warnings
c = rep(c, '\\"applied\\":false,',
        '\\"applied\\":false,\\"warnings\\":\\"" + MCP_响应构建.JSON转义文本 (cm警告) + "\\"',
        'C10 set 回包 warnings')

# C11: get 回包加 apply_failed
c = rep(c, '菜单回读不一致) + ",\\"last_apply_time\\":',
        '菜单回读不一致) + ",\\"apply_failed\\":\\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单施加失败) + "\\",\\"last_apply_time\\":',
        'C11 get 回包 apply_failed')

# C12: note 文案
c = rep(c, 'apply_count=右键次数; last_applied_items=上次实际施加成功的条目数(0 或持续不增说明规格为空/被禁用/模型无效)',
        'apply_count=右键次数; last_applied_items=实际生效条数; apply_failed=逐条说明哪条没生效及原因(最常见是指向默认项ID, 实测默认项改不动); verify_mismatch=回读与期望不符',
        'C12 note 文案校正')

save(CORE, c)
print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
