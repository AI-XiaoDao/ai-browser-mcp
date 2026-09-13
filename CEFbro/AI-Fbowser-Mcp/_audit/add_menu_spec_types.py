# -*- coding: utf-8 -*-
"""扩展 browser_context_menu 规格类型（A 组第 2 缺口，8 条菜单写方法）。

新增 7 种"修改已存在条目"的类型:
  del      删除菜单(命令ID)
  relabel  置菜单标签(命令ID, 标签)
  vis      置可见状态(命令ID, 参数 1=可见 0=隐藏)
  dis      置禁止状态(命令ID, 参数 1=禁用 0=启用)
  mark     选中状态(命令ID, 参数 1=选中)
  accel    设置快捷键(第 6 列, 如 70C)
  noaccel  移除快捷键(命令ID)
保留原有 5 种创建类型: item / check / radio / sep / sub

★关键语义差别(否则功能不可用): 创建类型是"新条目", 命令ID 必须落在 CEF 自定义区间 26500..28500
(留 0 由服务端分配); 而**修改类型作用于已存在的条目**, 包括**浏览器默认菜单项**
(它们的命令ID 是 CEF 标准ID, 如 后退=100), 故必须**允许标准区间**, 不能套用自定义区间校验。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '菜单规格类型扩展-写入前')

SERVER = os.path.join(SRC, 'MCP_Server.wsv')
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')

# ---------- A) MCP_Server.wsv: 应用菜单规格 里的类型判定与分支 ----------
A1_OLD = ('            // 除分隔栏外, 命令ID 必须落在 CEF 允许的自定义区间; 越界直接跳过并记错误\n'
          '            如果 (条目类型 != "sep" && (条目命令ID < 26500 || 条目命令ID > 28500))\n'
          '            {\n'
          '                菜单上次错误 = "跳过命令ID越界的条目(须在26500..28500): " + 行文本\n'
          '                到循环尾\n'
          '            }\n')
A1_NEW = ('            // 创建类 vs 修改类: 前者是"新条目"故 ID 必须落在 CEF 自定义区间;\n'
          '            // 后者作用于**已存在**的条目(含浏览器默认菜单项, 其 ID 是 CEF 标准ID), 故允许标准区间。\n'
          '            变量 条目是修改类 <类型 = 逻辑型>\n'
          '            条目是修改类 = (条目类型 == "del" || 条目类型 == "relabel" || 条目类型 == "vis" || 条目类型 == "dis" || 条目类型 == "mark" || 条目类型 == "accel" || 条目类型 == "noaccel")\n'
          '            如果 (条目是修改类)\n'
          '            {\n'
          '                如果 (条目命令ID < 1)\n'
          '                {\n'
          '                    菜单上次错误 = "修改类条目需要已存在的命令ID: " + 行文本\n'
          '                    到循环尾\n'
          '                }\n'
          '            }\n'
          '            否则\n'
          '            {\n'
          '                如果 (条目类型 != "sep" && (条目命令ID < 26500 || 条目命令ID > 28500))\n'
          '                {\n'
          '                    菜单上次错误 = "跳过命令ID越界的条目(须在26500..28500): " + 行文本\n'
          '                    到循环尾\n'
          '                }\n'
          '            }\n')

A2_OLD = ('            如果 (条目类型 == "sep")\n'
          '            {\n'
          '                如果 (目标模型.添加分隔栏 ())\n')
A2_NEW = ('            // ── 修改已存在条目(可作用于浏览器默认菜单项) ──\n'
          '            如果 (条目类型 == "del")\n'
          '            {\n'
          '                如果 (目标模型.删除菜单 (条目命令ID))\n'
          '                {\n'
          '                    施加条数 = 施加条数 + 1\n'
          '                }\n'
          '            }\n'
          '            否则 (条目类型 == "relabel")\n'
          '            {\n'
          '                如果 (目标模型.置菜单标签 (条目命令ID, 条目标签))\n'
          '                {\n'
          '                    施加条数 = 施加条数 + 1\n'
          '                }\n'
          '            }\n'
          '            否则 (条目类型 == "vis")\n'
          '            {\n'
          '                如果 (目标模型.置可见状态 (条目命令ID, 条目参数 == 1))\n'
          '                {\n'
          '                    施加条数 = 施加条数 + 1\n'
          '                }\n'
          '            }\n'
          '            否则 (条目类型 == "dis")\n'
          '            {\n'
          '                如果 (目标模型.置禁止状态 (条目命令ID, 条目参数 == 1))\n'
          '                {\n'
          '                    施加条数 = 施加条数 + 1\n'
          '                }\n'
          '            }\n'
          '            否则 (条目类型 == "mark")\n'
          '            {\n'
          '                如果 (目标模型.选中状态 (条目命令ID, 条目参数 == 1))\n'
          '                {\n'
          '                    施加条数 = 施加条数 + 1\n'
          '                }\n'
          '            }\n'
          '            否则 (条目类型 == "accel")\n'
          '            {\n'
          '                // 实际设置在下面公共块完成(与创建类共用同一段快捷键解析), 这里只校验必须有第 6 列\n'
          '                如果 (段数组.取成员数 () < 6 || 段数组.取成员 (5) == "")\n'
          '                {\n'
          '                    菜单上次错误 = "accel 需要第 6 列快捷键(如 70C): " + 行文本\n'
          '                    到循环尾\n'
          '                }\n'
          '                施加条数 = 施加条数 + 1\n'
          '            }\n'
          '            否则 (条目类型 == "noaccel")\n'
          '            {\n'
          '                如果 (目标模型.存在快捷键 (条目命令ID))\n'
          '                {\n'
          '                    目标模型.移除快捷键 (条目命令ID)\n'
          '                }\n'
          '                施加条数 = 施加条数 + 1\n'
          '            }\n'
          '            // ── 创建新条目 ──\n'
          '            否则 (条目类型 == "sep")\n'
          '            {\n'
          '                如果 (目标模型.添加分隔栏 ())\n')

A3_OLD = ('            如果 (段数组.取成员数 () >= 6 && 段数组.取成员 (5) != "" && 条目类型 != "sep")\n')
A3_NEW = ('            如果 (段数组.取成员数 () >= 6 && 段数组.取成员 (5) != "" && 条目类型 != "sep" && 条目类型 != "noaccel")\n')

# ---------- B) MCP_Server_Core.wsv: set 动作的校验与类型白名单 ----------
B1_OLD = ('                    如果 (cm类型 != "item" && cm类型 != "check" && cm类型 != "radio" && cm类型 != "sep" && cm类型 != "sub")\n'
          '                    {\n'
          '                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行类型非法: " + cm类型 + " | 支持 item/check/radio/sep/sub"))\n'
          '                    }\n')
B1_NEW = ('                    // 创建类: item/check/radio/sep/sub(新条目, 需自定义区间ID)\n'
          '                    // 修改类: del/relabel/vis/dis/mark/accel/noaccel(作用于**已存在**条目, 含浏览器默认项)\n'
          '                    如果 (cm类型 != "item" && cm类型 != "check" && cm类型 != "radio" && cm类型 != "sep" && cm类型 != "sub" && cm类型 != "del" && cm类型 != "relabel" && cm类型 != "vis" && cm类型 != "dis" && cm类型 != "mark" && cm类型 != "accel" && cm类型 != "noaccel")\n'
          '                    {\n'
          '                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行类型非法: " + cm类型 + " | 创建类: item/check/radio/sep/sub; 修改类: del/relabel/vis/dis/mark/accel/noaccel"))\n'
          '                    }\n'
          '                    变量 cm是修改类 <类型 = 逻辑型>\n'
          '                    cm是修改类 = (cm类型 == "del" || cm类型 == "relabel" || cm类型 == "vis" || cm类型 == "dis" || cm类型 == "mark" || cm类型 == "accel" || cm类型 == "noaccel")\n')

B2_OLD = ('                    如果 (cm类型 != "sep")\n'
          '                    {\n'
          '                        如果 (cmID == 0 || cmID < 26500 || cmID > 28500)\n')
B2_NEW = ('                    如果 (cm是修改类)\n'
          '                    {\n'
          '                        // 修改类引用**已存在**的条目: 允许 CEF 标准区间(如浏览器默认菜单项), 但不允许 0\n'
          '                        如果 (cmID < 1)\n'
          '                        {\n'
          '                            返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行是修改类(" + cm类型 + ")但命令ID 为 " + 到文本 (cmID) + " | 修改类必须给出已存在的命令ID: 自建项用你分配的 26500..28500, 浏览器默认项用其 CEF 标准ID(如 后退=100)"))\n'
          '                        }\n'
          '                    }\n'
          '                    否则 (cm类型 != "sep")\n'
          '                    {\n'
          '                        如果 (cmID == 0 || cmID < 26500 || cmID > 28500)\n')

# ---------- C) schema 描述 ----------
C_OLD = ('规格为逐行文本, 每行: 类型|标签|命令ID|参数|父命令ID|快捷键 —— 类型=item/check/radio/sep/sub; ')
C_NEW = ('规格为逐行文本, 每行: 类型|标签|命令ID|参数|父命令ID|快捷键 —— '
         '创建类: item/check/radio/sep/sub; **修改已存在条目**: del(删除)/relabel(改标签)/vis(显示隐藏)/dis(禁用启用)/mark(勾选)/accel(设快捷键)/noaccel(移除快捷键) —— '
         '创建类命令ID 须在 26500..28500(留0自动分配); **修改类**的 命令ID 指向已存在条目, 浏览器默认菜单项用其 CEF 标准ID(如 后退=100); ')


def patch(path, pairs, tag):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % tag
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    for old, new in pairs:
        c = text.count(old)
        if c != 1:
            print('!! %s 锚点命中 %d 次(应为1): %s' % (tag, c, old.strip()[:70]))
            return False
    for old, new in pairs:
        for ln in new.split('\n'):
            if ln.replace('\\"', '').count('"') % 2 != 0:
                print('!! 裸双引号奇数: %s' % ln.strip()[:100])
                return False
        text = text.replace(old, new.replace('\n', nl), 1)
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(path, os.path.join(BAK, os.path.basename(path)))
    open(path, 'wb').write(text.encode('utf-8'))
    print('   %s 已写入(+%d 处)' % (os.path.basename(path), len(pairs)))
    return True


if not patch(SERVER, [(A1_OLD, A1_NEW), (A2_OLD, A2_NEW), (A3_OLD, A3_NEW), (C_OLD, C_NEW)],
             'MCP_Server.wsv'):
    sys.exit(1)
if not patch(CORE, [(B1_OLD, B1_NEW), (B2_OLD, B2_NEW)], 'MCP_Server_Core.wsv'):
    sys.exit(1)
print('完成; 备份 -> %s' % BAK)
