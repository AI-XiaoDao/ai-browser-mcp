# -*- coding: utf-8 -*-
"""本轮修复(基于截图实证的 4 项):

D1 类库只读 getter `是否禁止` 语义与名字**相反**(实测: 自建项被置禁止后菜单里变灰, 而它读回假;
   说明它返回的是 CEF 的 IsEnabled)。原回读按"期望一致"比对 -> 误报回读不一致。本脚本校正比对方向。
D2 修改类 setter 作用于**浏览器默认菜单项**时**静默失败**(relabel/vis/dis/del 全返回假, 加/删快捷键
   也不生效), 而工具只报 last_applied_items=0 且 last_error 为空, 用户无从得知原因。
   -> 新增 菜单施加失败/apply_failed: 逐条记录哪个类型在哪个ID上没生效 + 可读原因。
   -> 校正 Core 里"默认项可用别名修改"的错误引导, 并在 set 时对指向默认项ID的修改类给出 warnings。
D3 `mark` 只对 check/radio 类条目有意义; 普通项上读回必然相反 -> 回读文案里说明。
D4 "修改类"类型列表在 Core(校验) 与 Server(施加) 各写一份 -> 抽成唯一判定源 是菜单修改类()。
另: 撤除本轮排查用的临时 diag 类型与其脚手架。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '菜单回读语义校正-写入前')

SERVER = os.path.join(SRC, 'MCP_Server.wsv')
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')
problems = []


def load(path):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % path
    t = data.decode('utf-8')
    return t, ('\r\n' if '\r\n' in t else '\n')


def save(path, text):
    os.makedirs(BAK, exist_ok=True)
    dst = os.path.join(BAK, os.path.basename(path))
    if not os.path.exists(dst):
        shutil.copy2(path, dst)
    open(path, 'wb').write(text.encode('utf-8'))
    print('   写入 %s' % os.path.basename(path))


def sub(text, old, new, tag, nl='\n'):
    o = old.replace('\n', nl)
    c = text.count(o)
    if c != 1:
        problems.append('%s: 锚点命中 %d 次(应1)' % (tag, c))
        return text
    for ln in new.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 新文案有裸双引号: %s' % (tag, ln.strip()[:80]))
            return text
    print('   ok %s' % tag)
    return text.replace(o, new.replace('\n', nl), 1)


# ══════════════════════════ MCP_Server.wsv ══════════════════════════
s, nl = load(SERVER)

s = sub(s, '    变量 菜单回读不一致 <公开 静态 类型 = 文本型 @输出名 = "MenuVerifyMismatch">\n',
        '    变量 菜单回读不一致 <公开 静态 类型 = 文本型 @输出名 = "MenuVerifyMismatch">\n'
        '    # 施加失败明细: setter 返回假时逐条记录原因(不再只有 applied=0 而毫无线索)\n'
        '    变量 菜单施加失败 <公开 静态 类型 = 文本型 @输出名 = "MenuApplyFailed">\n',
        'S1 字段 菜单施加失败', nl)

s = sub(s, '    # 把命令ID 列解析成整数: 支持 CEF **标准菜单项别名**',
        '''    # 菜单规格"修改类"类型的**唯一判定源**: 参数校验侧(Core)与施加侧(本类)共用, 避免两份列表漂移。
    方法 是菜单修改类 <公开 静态 类型 = 逻辑型 @输出名 = "IsMenuModifyType" @强制输出 = 真>
    参数 类型名 <类型 = 文本型 @输出名 = "TypeName">
    {
        返回 (类型名 == "del" || 类型名 == "relabel" || 类型名 == "vis" || 类型名 == "dis" || 类型名 == "mark" || 类型名 == "accel" || 类型名 == "noaccel")
    }

    # 统一生成"施加失败"的可读原因(只此一处文案)
    方法 菜单失败说明 <公开 静态 类型 = 文本型 @输出名 = "MenuFailReason" @强制输出 = 真>
    参数 类型名 <类型 = 文本型 @输出名 = "TypeName">
    参数 命令ID <类型 = 整数 @输出名 = "CommandId">
    {
        如果 (命令ID < 26500)
        {
            返回 ("[" + 类型名 + " " + 到文本 (命令ID) + " 未生效: 该ID是浏览器默认菜单项, 实测本应用不支持修改默认项] ")
        }
        返回 ("[" + 类型名 + " " + 到文本 (命令ID) + " 未生效: 条目不存在或类型不匹配] ")
    }

    # 把命令ID 列解析成整数: 支持 CEF **标准菜单项别名**''',
        'S2 是菜单修改类 + 菜单失败说明', nl)

# 撤除 diag 分支(整块删除, 用起止行夹取, 避免逐字长锚点)
start = s.find('            // ── 临时诊断(diag): 逐个 setter 记录返回值, 再读回 getter ──\n')
end = s.find('            // ── 修改已存在条目(可作用于浏览器默认菜单项) ──\n')
if start == -1 or end == -1 or end < start:
    problems.append('S3 diag 块定位失败 start=%d end=%d' % (start, end))
else:
    s = s[:start] + s[end:]
    print('   ok S3 撤除 diag 分支(删 %d 字节)' % (end - start))

s = sub(s, '            条目是修改类 = (条目类型 == "diag" || 条目类型 == "del" || 条目类型 == "relabel" || 条目类型 == "vis" || 条目类型 == "dis" || 条目类型 == "mark" || 条目类型 == "accel" || 条目类型 == "noaccel")\n',
        '            条目是修改类 = MCP命令服务器.是菜单修改类 (条目类型)\n',
        'S4 施加侧改用唯一判定源', nl)

s = sub(s, '        菜单回读不一致 = ""\n',
        '        菜单回读不一致 = ""\n'
        '        菜单施加失败 = ""\n'
        '        变量 失败条数 <类型 = 整数>\n'
        '        失败条数 = 0\n'
        '        变量 失败明细 <类型 = 文本型>\n'
        '        失败明细 = ""\n',
        'S5 失败计数量', nl)

# del / relabel: 补"否则 记失败"
s = sub(s, '''            否则 (条目类型 == "del")
            {
                如果 (目标模型.删除菜单 (条目命令ID))
                {
                    施加条数 = 施加条数 + 1
                }
            }
''', '''            否则 (条目类型 == "del")
            {
                如果 (目标模型.删除菜单 (条目命令ID))
                {
                    施加条数 = 施加条数 + 1
                }
                否则
                {
                    失败条数 = 失败条数 + 1
                    失败明细 = 失败明细 + 菜单失败说明 (条目类型, 条目命令ID)
                }
            }
''', 'S6 del 失败原因', nl)

s = sub(s, '''            否则 (条目类型 == "relabel")
            {
                如果 (目标模型.置菜单标签 (条目命令ID, 条目标签))
                {
                    施加条数 = 施加条数 + 1
                }
            }
''', '''            否则 (条目类型 == "relabel")
            {
                如果 (目标模型.置菜单标签 (条目命令ID, 条目标签))
                {
                    施加条数 = 施加条数 + 1
                }
                否则
                {
                    失败条数 = 失败条数 + 1
                    失败明细 = 失败明细 + 菜单失败说明 (条目类型, 条目命令ID)
                }
            }
''', 'S7 relabel 失败原因', nl)

# vis: 补 否则
s = sub(s, '''                    否则
                    {
                        菜单回读不一致 = 菜单回读不一致 + "[vis " + 到文本 (条目命令ID) + " 期望" + 选择 (条目参数 == 1, "可见", "隐藏") + " 实际相反] "
                    }
                }
            }
''', '''                    否则
                    {
                        菜单回读不一致 = 菜单回读不一致 + "[vis " + 到文本 (条目命令ID) + " 期望" + 选择 (条目参数 == 1, "可见", "隐藏") + " 实际相反] "
                    }
                }
                否则
                {
                    失败条数 = 失败条数 + 1
                    失败明细 = 失败明细 + 菜单失败说明 (条目类型, 条目命令ID)
                }
            }
''', 'S8 vis 失败原因', nl)

# dis: 校正回读方向(是否禁止 实为 IsEnabled) + 补 否则
s = sub(s, '''            否则 (条目类型 == "dis")
            {
                如果 (目标模型.置禁止状态 (条目命令ID, 条目参数 == 1))
                {
                    施加条数 = 施加条数 + 1
                    如果 (目标模型.是否禁止 (条目命令ID) == (条目参数 == 1))
                    {
                        回读条数 = 回读条数 + 1
                    }
                    否则
                    {
                        菜单回读不一致 = 菜单回读不一致 + "[dis " + 到文本 (条目命令ID) + " 期望" + 选择 (条目参数 == 1, "禁用", "启用") + " 实际相反] "
                    }
                }
            }
''', '''            否则 (条目类型 == "dis")
            {
                如果 (目标模型.置禁止状态 (条目命令ID, 条目参数 == 1))
                {
                    施加条数 = 施加条数 + 1
                    // 方向校正: 类库只读 getter "是否禁止" 的名字与语义**相反** —— 实测置禁止(真) 后菜单项
                    // 确实变灰, 而它读回假, 说明它返回的是 CEF 的 IsEnabled(是否可用)。故"期望禁用"比对 假。
                    如果 (目标模型.是否禁止 (条目命令ID) == (条目参数 == 0))
                    {
                        回读条数 = 回读条数 + 1
                    }
                    否则
                    {
                        菜单回读不一致 = 菜单回读不一致 + "[dis " + 到文本 (条目命令ID) + " 期望" + 选择 (条目参数 == 1, "禁用", "启用") + " 实际相反] "
                    }
                }
                否则
                {
                    失败条数 = 失败条数 + 1
                    失败明细 = 失败明细 + 菜单失败说明 (条目类型, 条目命令ID)
                }
            }
''', 'S9 dis 方向校正 + 失败原因', nl)

# mark: 补 否则 + 回读文案说明适用范围
s = sub(s, '''                    否则
                    {
                        菜单回读不一致 = 菜单回读不一致 + "[mark " + 到文本 (条目命令ID) + " 期望" + 选择 (条目参数 == 1, "选中", "取消") + " 实际相反] "
                    }
                }
            }
''', '''                    否则
                    {
                        菜单回读不一致 = 菜单回读不一致 + "[mark " + 到文本 (条目命令ID) + " 期望" + 选择 (条目参数 == 1, "选中", "取消") + " 实际相反: mark 只对 check/radio 类条目有效, 普通 item 类不支持选中] "
                    }
                }
                否则
                {
                    失败条数 = 失败条数 + 1
                    失败明细 = 失败明细 + 菜单失败说明 (条目类型, 条目命令ID)
                }
            }
''', 'S10 mark 回读文案 + 失败原因', nl)

# accel: 不再无条件计数(改到公共块里"读回确认"后计数)
s = sub(s, '''                    菜单上次错误 = "accel 需要第 6 列快捷键(如 70C): " + 行文本
                    到循环尾
                }
                施加条数 = 施加条数 + 1
            }
''', '''                    菜单上次错误 = "accel 需要第 6 列快捷键(如 70C): " + 行文本
                    到循环尾
                }
                // 计数改到下面公共块: 只有"设置后 存在快捷键() 读回为真"才算成功
            }
''', 'S11 accel 不再无条件计数', nl)

# noaccel: 读回确认后才计数
s = sub(s, '''            否则 (条目类型 == "noaccel")
            {
                如果 (目标模型.存在快捷键 (条目命令ID))
                {
                    目标模型.移除快捷键 (条目命令ID)
                }
                施加条数 = 施加条数 + 1
            }
''', '''            否则 (条目类型 == "noaccel")
            {
                如果 (目标模型.存在快捷键 (条目命令ID))
                {
                    // 类库返回值不足以证明生效: 移除后还要用 存在快捷键() 读回确认
                    如果 (目标模型.移除快捷键 (条目命令ID) && 目标模型.存在快捷键 (条目命令ID) == 假)
                    {
                        施加条数 = 施加条数 + 1
                    }
                    否则
                    {
                        失败条数 = 失败条数 + 1
                        失败明细 = 失败明细 + 菜单失败说明 (条目类型, 条目命令ID)
                    }
                }
                否则
                {
                    // 本来就没有快捷键 -> 目标状态已满足, 计为已施加(幂等, 不算失败)
                    施加条数 = 施加条数 + 1
                }
            }
''', 'S12 noaccel 读回确认', nl)

# 公共快捷键块: 设置后读回确认
s = sub(s, '                     目标模型.设置快捷键 (条目命令ID, 文本到整数 (键码文本), 是否Shift, 是否Ctrl, 是否Alt)\n',
        '''                     如果 (目标模型.设置快捷键 (条目命令ID, 文本到整数 (键码文本), 是否Shift, 是否Ctrl, 是否Alt) && 目标模型.存在快捷键 (条目命令ID))
                    {
                        // 读回确认通过才计数(默认项上 设置快捷键 会返回真但实际不留痕)
                        如果 (条目类型 == "accel")
                        {
                            施加条数 = 施加条数 + 1
                        }
                    }
                    否则
                    {
                        失败条数 = 失败条数 + 1
                        失败明细 = 失败明细 + 菜单失败说明 ("accel", 条目命令ID)
                    }
''', 'S13 公共快捷键块读回确认', nl)

# 创建失败也要有记录
s = sub(s, '''                 如果 (目标模型.添加菜单 (条目命令ID, 条目标签))
                 {
                     施加条数 = 施加条数 + 1
                     如果 (条目参数 == 0)
                     {
                         目标模型.置禁止状态 (条目命令ID, 真)
                     }
                 }
''', '''                 如果 (目标模型.添加菜单 (条目命令ID, 条目标签))
                 {
                     施加条数 = 施加条数 + 1
                     如果 (条目参数 == 0)
                     {
                         目标模型.置禁止状态 (条目命令ID, 真)
                     }
                 }
                 否则
                 {
                     失败条数 = 失败条数 + 1
                     失败明细 = 失败明细 + "[item " + 到文本 (条目命令ID) + " 创建失败: 命令ID 可能已被占用] "
                 }
''', 'S14 item 创建失败', nl)

# 收尾: 写失败明细
s = sub(s, '''        菜单最近项数 = 顶层菜单.取数量 ()
        菜单回读确认条数 = 回读条数
''', '''        菜单最近项数 = 顶层菜单.取数量 ()
        菜单回读确认条数 = 回读条数
        菜单施加失败 = 失败明细
''', 'S15 收尾写失败明细', nl)

save(SERVER, s)

# ══════════════════════════ MCP_Server_Core.wsv ══════════════════════════
c, nl2 = load(CORE)

c = sub(c, '                    如果 (cm类型 != "item" && cm类型 != "check" && cm类型 != "radio" && cm类型 != "sep" && cm类型 != "sub" && cm类型 != "del" && cm类型 != "relabel" && cm类型 != "vis" && cm类型 != "dis" && cm类型 != "mark" && cm类型 != "accel" && cm类型 != "noaccel" && cm类型 != "diag")\n',
        '                    如果 (cm类型 != "item" && cm类型 != "check" && cm类型 != "radio" && cm类型 != "sep" && cm类型 != "sub" && MCP命令服务器.是菜单修改类 (cm类型) == 假)\n',
        'C1 去掉 diag 白名单', nl2)

c = sub(c, '                    cm是修改类 = (cm类型 == "del" || cm类型 == "relabel" || cm类型 == "vis" || cm类型 == "dis" || cm类型 == "mark" || cm类型 == "accel" || cm类型 == "noaccel" || cm类型 == "diag")\n',
        '                    cm是修改类 = MCP命令服务器.是菜单修改类 (cm类型)\n',
        'C2 校验侧改用唯一判定源', nl2)

c = sub(c, '''                    // 创建类: item/check/radio/sep/sub(新条目, 需自定义区间ID)
                    // 修改类: del/relabel/vis/dis/mark/accel/noaccel(作用于**已存在**条目, 含浏览器默认项)
''', '''                    // 创建类: item/check/radio/sep/sub(新条目, 需自定义区间ID)
                    // 修改类: del/relabel/vis/dis/mark/accel/noaccel
                    // 实测结论: 修改类只对**本服务自建项**(26500..28500)有效; 浏览器默认菜单项(100..130)
                    // 上 relabel/vis/dis/del 一律返回假、加删快捷键也不生效 —— 施加失败会由 apply_failed 报出。
''', 'C3 注释校正', nl2)

c = sub(c, '''                             返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行是修改类(" + cm类型 + ")但命令ID无法识别: [" + cm段.取成员 (2) + "] | 修改类必须给出已存在的命令ID: 自建项用你分配的 26500..28500; 浏览器默认项可直接用**别名**(back/forward/reload/reload_nocache/stop/undo/redo/cut/copy/paste/delete/selectall/find/print/viewsource/nosuggestions/addtodict)或对应标准ID(如 back=100)"))''',
        '''                             返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行是修改类(" + cm类型 + ")但命令ID无法识别: [" + cm段.取成员 (2) + "] | 修改类必须给出已存在的命令ID: 用你自建项的 26500..28500(别名 back/forward/reload/reload_nocache/stop/undo/redo/cut/copy/paste/delete/selectall/find/print/viewsource/nosuggestions/addtodict 或标准ID 如 back=100 也能解析, 但见下一条说明)"))''',
        'C4 别名错误文案校正', nl2)

c = sub(c, '''                                返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行命令ID越界: " + 到文本 (cmID) + " | 创建类新项的命令ID 必须在 26500..28500(留0自动分配); 若要改**默认菜单项**请用修改类(del/relabel/vis/dis/mark/accel/noaccel)配别名(如 back/reload/copy)"))''',
        '''                                返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行命令ID越界: " + 到文本 (cmID) + " | 创建类新项的命令ID 必须在 26500..28500(留0自动分配) | 修改类(del/relabel/vis/dis/mark/accel/noaccel)只能作用于自建项: 实测浏览器默认菜单项(标准ID/别名)在本应用上改不动"))''',
        'C5 创建类越界文案校正', nl2)

c = sub(c, '                    // 支持 CEF 标准菜单项别名(back/reload/copy/…), 便于对**默认菜单项**做修改类操作\n',
        '                    // 命令ID 列支持 CEF 标准菜单项别名(back/reload/copy/…)便于书写与识别;\n'
        '                    // 但实测**默认菜单项改不动**, 别名在本应用里只有标识/诊断价值。\n',
        'C6 别名注释校正', nl2)

# set 侧: 警告 + 重置失败字段
c = sub(c, '''                变量 cm已用ID <类型 = 整数>
                计次循环 (cm行数组.取成员数 ())
''', '''                变量 cm已用ID <类型 = 整数>
                变量 cm警告 <类型 = 文本型>
                cm警告 = ""
                计次循环 (cm行数组.取成员数 ())
''', 'C7 警告变量', nl2)

c = sub(c, '''                    如果 (cm是修改类)
                    {
'''.replace('如果', '如果'), '''                    如果 (cm是修改类)
                    {
                        // 实测: 指向浏览器默认菜单项(标准ID < 26500)的修改类不会生效, 提前如实告知
                        如果 (cmID > 0 && cmID < 26500)
                        {
                            cm警告 = cm警告 + "[修改类 " + cm类型 + " 指向默认项ID " + 到文本 (cmID) + ": 实测本应用不支持修改浏览器默认项, 右键后不会生效] "
                        }
''', 'C8 set 时默认项警告', nl2)

c = sub(c, '                MCP命令服务器.菜单最近施加条数 = 0\n',
        '                MCP命令服务器.菜单最近施加条数 = 0\n                MCP命令服务器.菜单施加失败 = ""\n',
        'C9 重置失败字段', nl2)

c = sub(c, '''\"note\":\"规格已暂存: 右键一次后可用 action=get 查看施加次数与条数\"}''',
        '''\"warnings\":\"" + MCP_响应构建.JSON转义文本 (cm警告) + "\",\"note\":\"规格已暂存: 右键一次后可用 action=get 查看施加次数/条数与 apply_failed\"}''',
        'C10 set 回包加 warnings', nl2)

c = sub(c, '''\"verify_mismatch\":\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单回读不一致) + "\"''',
        '''\"verify_mismatch\":\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单回读不一致) + "\",\"apply_failed\":\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单施加失败) + "\"''',
        'C11 get 回包加 apply_failed', nl2)

c = sub(c, '''\"note\":\"apply_count=右键次数; last_applied_items=上次实际施加成功的条目数(0 或持续不增说明规格为空/被禁用/模型无效)\"''',
        '''\"note\":\"apply_count=右键次数; last_applied_items=实际生效条数; apply_failed=逐条说明哪条没生效及原因(指向默认项ID是最常见原因, 实测默认项改不动); verify_mismatch=回读与期望不符(注: 只读 getter 是否禁止 语义与名字相反, 已按 IsEnabled 校正, mark 仅对 check/radio 类有效)\"''',
        'C12 get 回包 note 校正', nl2)

save(CORE, c)
print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
