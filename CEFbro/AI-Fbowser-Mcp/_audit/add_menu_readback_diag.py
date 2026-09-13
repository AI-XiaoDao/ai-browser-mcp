# -*- coding: utf-8 -*-
"""临时诊断件: 在回调内对同一 ID 分别"置真/置假"并各读一次, 把**原始布尔值**记下来。

要回答的问题: 回读报出的"期望与实测相反"是
  ① 真的没生效(类库 setter 对新建项/非勾选项无效), 还是
  ② 我的回读用错了 getter(读的量根本不反映那个状态)?
判据: 对同一 ID, 若"置真后读"与"置假后读"**得到不同值**, 说明 setter+getter 这条链是通的,
      那么先前的不一致就是真实的"没生效"; 若两次读**相同**, 则该 getter 不反映该状态(我的回读方式有问题)。
这是一个临时 `diag` 类型, 验证完即撤。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '菜单回读诊断件-写入前')

SERVER = os.path.join(SRC, 'MCP_Server.wsv')
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')

# A) 应用菜单规格: 加 diag 分支
A_OLD = ('            // ── 修改已存在条目(可作用于浏览器默认菜单项) ──\n'
         '            如果 (条目类型 == "del")\n')
A_NEW = ('            // ── 临时诊断(diag): 对同一 ID 置真/置假各读一次, 记录原始值 ──\n'
         '            如果 (条目类型 == "diag")\n'
         '            {\n'
         '                目标模型.置禁止状态 (条目命令ID, 真)\n'
         '                变量 dgB1 <类型 = 逻辑型>\n'
         '                dgB1 = 目标模型.是否禁止 (条目命令ID)\n'
         '                目标模型.置禁止状态 (条目命令ID, 假)\n'
         '                变量 dgB2 <类型 = 逻辑型>\n'
         '                dgB2 = 目标模型.是否禁止 (条目命令ID)\n'
         '                目标模型.置可见状态 (条目命令ID, 真)\n'
         '                变量 dgV1 <类型 = 逻辑型>\n'
         '                dgV1 = 目标模型.是否可见 (条目命令ID)\n'
         '                目标模型.置可见状态 (条目命令ID, 假)\n'
         '                变量 dgV2 <类型 = 逻辑型>\n'
         '                dgV2 = 目标模型.是否可见 (条目命令ID)\n'
         '                目标模型.选中状态 (条目命令ID, 真)\n'
         '                变量 dgC1 <类型 = 逻辑型>\n'
         '                dgC1 = 目标模型.是否选中 (条目命令ID)\n'
         '                目标模型.选中状态 (条目命令ID, 假)\n'
         '                变量 dgC2 <类型 = 逻辑型>\n'
         '                dgC2 = 目标模型.是否选中 (条目命令ID)\n'
         '                菜单回读不一致 = 菜单回读不一致 + "[diag " + 到文本 (条目命令ID) + " 禁止T->" + 选择 (dgB1, "T", "F") + " 禁止F->" + 选择 (dgB2, "T", "F") + " 可见T->" + 选择 (dgV1, "T", "F") + " 可见F->" + 选择 (dgV2, "T", "F") + " 选中T->" + 选择 (dgC1, "T", "F") + " 选中F->" + 选择 (dgC2, "T", "F") + "] "\n'
         '                施加条数 = 施加条数 + 1\n'
         '            }\n'
         '            // ── 修改已存在条目(可作用于浏览器默认菜单项) ──\n'
         '            否则 (条目类型 == "del")\n')

# B) Core: 允许 diag 类型(临时)
B_OLD = '&& cm类型 != "noaccel")\n'
B_NEW = '&& cm类型 != "noaccel" && cm类型 != "diag")\n'


def patch(path, pairs, tag):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % tag
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    norm = [(o.replace('\n', nl), n) for o, n in pairs]
    for o, n in norm:
        c = text.count(o)
        if c != 1:
            print('!! %s 锚点命中 %d 次(应为1): %s' % (tag, c, o.strip()[:60]))
            return None
    for o, n in norm:
        for ln in n.split('\n'):
            if ln.replace('\\"', '').count('"') % 2 != 0:
                print('!! 裸双引号奇数: %s' % ln.strip()[:100])
                return None
        text = text.replace(o, n.replace('\n', nl), 1)
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(path, os.path.join(BAK, os.path.basename(path)))
    open(path, 'wb').write(text.encode('utf-8'))
    print('   %s 已写入(+%d 处)' % (os.path.basename(path), len(pairs)))
    return True


if not patch(SERVER, [(A_OLD, A_NEW)], 'MCP_Server.wsv'):
    sys.exit(1)
if not patch(CORE, [(B_OLD, B_NEW)], 'MCP_Server_Core.wsv'):
    sys.exit(1)
print('诊断件已加入(临时, 验证后撤除)')
