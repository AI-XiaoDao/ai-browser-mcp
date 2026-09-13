# -*- coding: utf-8 -*-
"""把临时 diag 分支升级成"真值矩阵": 逐个 setter 记录**返回值**, 再读回 getter。

要一次回答 4 个问题:
  ① 修改类 setter 作用在**浏览器默认菜单项**(标准ID, 如 102)上到底返回真还是假?
  ② 同样的 setter 作用在**我们自建的**项(26501/26502)上返回什么?
  ③ `是否禁止` 与 `置禁止状态` 是不是互为反义(谁是反的那个)?
  ④ `选中状态` 对**普通项**与**勾选项**分别是什么行为(之前普通项上读值永远为假)?
顺序有意设计: 可见测完立刻恢复可见, 避免"隐藏后再改其它状态"把结论搅浑。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '菜单回读诊断件-写入前')

SERVER = os.path.join(SRC, 'MCP_Server.wsv')

OLD = '''            // ── 临时诊断(diag): 对同一 ID 置真/置假各读一次, 记录原始值 ──
            如果 (条目类型 == "diag")
            {
                目标模型.置禁止状态 (条目命令ID, 真)
                变量 dgB1 <类型 = 逻辑型>
                dgB1 = 目标模型.是否禁止 (条目命令ID)
                目标模型.置禁止状态 (条目命令ID, 假)
                变量 dgB2 <类型 = 逻辑型>
                dgB2 = 目标模型.是否禁止 (条目命令ID)
                目标模型.置可见状态 (条目命令ID, 真)
                变量 dgV1 <类型 = 逻辑型>
                dgV1 = 目标模型.是否可见 (条目命令ID)
                目标模型.置可见状态 (条目命令ID, 假)
                变量 dgV2 <类型 = 逻辑型>
                dgV2 = 目标模型.是否可见 (条目命令ID)
                目标模型.选中状态 (条目命令ID, 真)
                变量 dgC1 <类型 = 逻辑型>
                dgC1 = 目标模型.是否选中 (条目命令ID)
                目标模型.选中状态 (条目命令ID, 假)
                变量 dgC2 <类型 = 逻辑型>
                dgC2 = 目标模型.是否选中 (条目命令ID)
                菜单回读不一致 = 菜单回读不一致 + "[diag " + 到文本 (条目命令ID) + " 禁止T->" + 选择 (dgB1, "T", "F") + " 禁止F->" + 选择 (dgB2, "T", "F") + " 可见T->" + 选择 (dgV1, "T", "F") + " 可见F->" + 选择 (dgV2, "T", "F") + " 选中T->" + 选择 (dgC1, "T", "F") + " 选中F->" + 选择 (dgC2, "T", "F") + "] "
                施加条数 = 施加条数 + 1
            }
'''

NEW = '''            // ── 临时诊断(diag): 逐个 setter 记录返回值, 再读回 getter ──
            如果 (条目类型 == "diag")
            {
                变量 dgS <类型 = 文本型>
                变量 dgR1 <类型 = 逻辑型>
                变量 dgR2 <类型 = 逻辑型>
                变量 dgR3 <类型 = 逻辑型>
                变量 dgR4 <类型 = 逻辑型>
                变量 dgR5 <类型 = 逻辑型>
                变量 dgR6 <类型 = 逻辑型>
                变量 dgR7 <类型 = 逻辑型>
                变量 dgR8 <类型 = 逻辑型>
                变量 dgR9 <类型 = 逻辑型>
                变量 dgR10 <类型 = 逻辑型>
                变量 dgR11 <类型 = 逻辑型>
                变量 dgR12 <类型 = 逻辑型>
                变量 dgR13 <类型 = 逻辑型>
                变量 dgR14 <类型 = 逻辑型>
                dgS = "[diag " + 到文本 (条目命令ID)
                dgR1 = 目标模型.置菜单标签 (条目命令ID, "探针")
                dgS = dgS + " relabel=" + 选择 (dgR1, "T", "F")
                dgR2 = 目标模型.置可见状态 (条目命令ID, 真)
                dgR3 = 目标模型.是否可见 (条目命令ID)
                dgR4 = 目标模型.置可见状态 (条目命令ID, 假)
                dgR5 = 目标模型.是否可见 (条目命令ID)
                dgR6 = 目标模型.置可见状态 (条目命令ID, 真)
                dgS = dgS + " visT=" + 选择 (dgR2, "T", "F") + " rdVisT=" + 选择 (dgR3, "T", "F") + " visF=" + 选择 (dgR4, "T", "F") + " rdVisF=" + 选择 (dgR5, "T", "F")
                dgR7 = 目标模型.置禁止状态 (条目命令ID, 真)
                dgR8 = 目标模型.是否禁止 (条目命令ID)
                dgR9 = 目标模型.置禁止状态 (条目命令ID, 假)
                dgR10 = 目标模型.是否禁止 (条目命令ID)
                dgS = dgS + " disT=" + 选择 (dgR7, "T", "F") + " rdDisT=" + 选择 (dgR8, "T", "F") + " disF=" + 选择 (dgR9, "T", "F") + " rdDisF=" + 选择 (dgR10, "T", "F")
                dgR11 = 目标模型.选中状态 (条目命令ID, 真)
                dgR12 = 目标模型.是否选中 (条目命令ID)
                dgR13 = 目标模型.选中状态 (条目命令ID, 假)
                dgR14 = 目标模型.是否选中 (条目命令ID)
                dgS = dgS + " markT=" + 选择 (dgR11, "T", "F") + " rdMarkT=" + 选择 (dgR12, "T", "F") + " markF=" + 选择 (dgR13, "T", "F") + " rdMarkF=" + 选择 (dgR14, "T", "F")
                dgS = dgS + " hasAccel=" + 选择 (目标模型.存在快捷键 (条目命令ID), "T", "F")
                dgS = dgS + " accel=" + 选择 (目标模型.设置快捷键 (条目命令ID, 70, 假, 真, 假), "T", "F")
                dgS = dgS + " hasAccel2=" + 选择 (目标模型.存在快捷键 (条目命令ID), "T", "F")
                dgS = dgS + " noaccel=" + 选择 (目标模型.移除快捷键 (条目命令ID), "T", "F")
                dgS = dgS + "] "
                菜单回读不一致 = 菜单回读不一致 + dgS
                施加条数 = 施加条数 + 1
            }
'''

# Server 侧的修改类判定也要认 diag, 否则标准 ID 会被"创建类越界"检查拦掉
ANCHOR = '条目是修改类 = (条目类型 == "del"'
ANCHOR_NEW = '条目是修改类 = (条目类型 == "diag" || 条目类型 == "del"'


def patch(path, pairs, tag):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % tag
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    norm = [(o.replace('\n', nl), n) for o, n in pairs]
    for o, n in norm:
        c = text.count(o)
        if c != 1:
            print('!! %s 锚点命中 %d 次(应为1): %s' % (tag, c, o.strip()[:70]))
            return False
    for o, n in norm:
        for ln in n.split('\n'):
            if ln.replace('\\"', '').count('"') % 2 != 0:
                print('!! 裸双引号奇数: %s' % ln.strip()[:100])
                return False
    for o, n in norm:
        text = text.replace(o, n.replace('\n', nl), 1)
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(path, os.path.join(BAK, os.path.basename(path)))
    open(path, 'wb').write(text.encode('utf-8'))
    print('   %s 已改(%d 处)' % (os.path.basename(path), len(pairs)))
    return True


# 先把上一次写的旧 diag 块换掉(它已经在文件里了, 备份目录保留最初版本)
ok = patch(SERVER, [(OLD, NEW), (ANCHOR, ANCHOR_NEW)], 'MCP_Server.wsv')
sys.exit(0 if ok else 1)
