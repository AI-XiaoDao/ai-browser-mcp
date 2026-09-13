# -*- coding: utf-8 -*-
"""菜单能力收口（第113轮）:
  A. 命令ID 支持 **CEF 标准菜单项别名**(back/reload/copy/…) —— 默认菜单项在类库里**无法按索引反查**
     (类库未封装 GetCommandIdAt), 故只能靠标准ID定位; 让用户记数字不现实, 故给别名。
     数值取自本机 CEF 头 cef_types.h(不是凭记忆): back=100 forward=101 reload=102 reload_nocache=103
     stop=104 undo=110 redo=111 cut=112 copy=113 paste=114 delete=115 selectall=116
     find=130 print=131 viewsource=132 nosuggestions=205 addtodict=206
  B. **回读验证**: 对 vis/dis/mark 三类"有明确期望状态"的操作, 施加后立刻用只读 getter
     (是否可见/是否禁止/是否选中) 读回并与期望比对, 计入 verified_items; 不一致记入 mismatch。
     另记录 `取数量()` 得到的**真实菜单项数**(含默认项) —— 这是第一次能"看见"菜单全貌。
"""
import io
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '菜单别名与回读-写入前')

SERVER = os.path.join(SRC, 'MCP_Server.wsv')
CORE = os.path.join(SRC, 'MCP_Server_Core.wsv')

# ---------- A) 字段 ----------
F_ANCHOR = '    变量 菜单上次错误 <公开 静态 类型 = 文本型 @输出名 = "MenuLastError">\n'
F_NEW = F_ANCHOR + (
    '    # 回读验证结果(写入后立刻用只读 getter 核对, 不只听类库返回值)\n'
    '    变量 菜单最近项数 <公开 静态 类型 = 整数 值 = 0 @输出名 = "MenuLastItemCount">\n'
    '    变量 菜单回读确认条数 <公开 静态 类型 = 整数 值 = 0 @输出名 = "MenuVerifiedCount">\n'
    '    变量 菜单回读不一致 <公开 静态 类型 = 文本型 @输出名 = "MenuVerifyMismatch">\n'
)

# ---------- B) 别名解析方法(放在 构建菜单环境摘要 之前) ----------
M_ANCHOR = '    # 把"右键上下文"(类_FBrowser_菜单环境)取成紧凑 JSON —— **只在 CEF 回调内调用**。\n'
M_NEW = '''    # 把命令ID 列解析成整数: 支持 CEF **标准菜单项别名**(默认菜单项无法按索引反查, 只能靠标准ID定位)。
    # 数值取自本机 CEF 头 cef_types.h 的 cef_menu_id_t, 不是凭记忆写的。

    方法 解析菜单命令ID <公开 静态 类型 = 整数 @输出名 = "ParseMenuCommandID" @强制输出 = 真>
    参数 原始值 <类型 = 文本型 @输出名 = "RawValue">
    {
        变量 键 <类型 = 文本型>
        键 = 删首尾空 (原始值)
        如果 (键 == "")
        {
            返回 (0)
        }
        // 纯数字直接返回(自建项 26500..28500 / 默认项标准ID)
        变量 首位 <类型 = 文本型>
        首位 = 取文本左边 (键, 1)
        如果 (寻找文本 ("0123456789", 首位, 0, 假) != -1)
        {
            返回 (文本到整数 (键))
        }
        如果 (键 == "back")
        {
            返回 (100)
        }
        如果 (键 == "forward")
        {
            返回 (101)
        }
        如果 (键 == "reload")
        {
            返回 (102)
        }
        如果 (键 == "reload_nocache")
        {
            返回 (103)
        }
        如果 (键 == "stop")
        {
            返回 (104)
        }
        如果 (键 == "undo")
        {
            返回 (110)
        }
        如果 (键 == "redo")
        {
            返回 (111)
        }
        如果 (键 == "cut")
        {
            返回 (112)
        }
        如果 (键 == "copy")
        {
            返回 (113)
        }
        如果 (键 == "paste")
        {
            返回 (114)
        }
        如果 (键 == "delete")
        {
            返回 (115)
        }
        如果 (键 == "selectall")
        {
            返回 (116)
        }
        如果 (键 == "find")
        {
            返回 (130)
        }
        如果 (键 == "print")
        {
            返回 (131)
        }
        如果 (键 == "viewsource")
        {
            返回 (132)
        }
        如果 (键 == "nosuggestions")
        {
            返回 (205)
        }
        如果 (键 == "addtodict")
        {
            返回 (206)
        }
        返回 (0)
    }

''' + M_ANCHOR

# ---------- C) 应用菜单规格: 状态类操作后回读 ----------
C1_OLD = ('            否则 (条目类型 == "vis")\n'
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
          '            }\n')
C1_NEW = ('            否则 (条目类型 == "vis")\n'
          '            {\n'
          '                如果 (目标模型.置可见状态 (条目命令ID, 条目参数 == 1))\n'
          '                {\n'
          '                    施加条数 = 施加条数 + 1\n'
          '                    // 回读验证: 期望状态已知, 立刻用只读 getter 核对(不只听类库返回值)\n'
          '                    如果 (目标模型.是否可见 (条目命令ID) == (条目参数 == 1))\n'
          '                    {\n'
          '                        回读条数 = 回读条数 + 1\n'
          '                    }\n'
          '                    否则\n'
          '                    {\n'
          '                        菜单回读不一致 = 菜单回读不一致 + "[vis " + 到文本 (条目命令ID) + " 期望" + 选择 (条目参数 == 1, "可见", "隐藏") + " 实际相反] "\n'
          '                    }\n'
          '                }\n'
          '            }\n'
          '            否则 (条目类型 == "dis")\n'
          '            {\n'
          '                如果 (目标模型.置禁止状态 (条目命令ID, 条目参数 == 1))\n'
          '                {\n'
          '                    施加条数 = 施加条数 + 1\n'
          '                    如果 (目标模型.是否禁止 (条目命令ID) == (条目参数 == 1))\n'
          '                    {\n'
          '                        回读条数 = 回读条数 + 1\n'
          '                    }\n'
          '                    否则\n'
          '                    {\n'
          '                        菜单回读不一致 = 菜单回读不一致 + "[dis " + 到文本 (条目命令ID) + " 期望" + 选择 (条目参数 == 1, "禁用", "启用") + " 实际相反] "\n'
          '                    }\n'
          '                }\n'
          '            }\n'
          '            否则 (条目类型 == "mark")\n'
          '            {\n'
          '                如果 (目标模型.选中状态 (条目命令ID, 条目参数 == 1))\n'
          '                {\n'
          '                    施加条数 = 施加条数 + 1\n'
          '                    如果 (目标模型.是否选中 (条目命令ID) == (条目参数 == 1))\n'
          '                    {\n'
          '                        回读条数 = 回读条数 + 1\n'
          '                    }\n'
          '                    否则\n'
          '                    {\n'
          '                        菜单回读不一致 = 菜单回读不一致 + "[mark " + 到文本 (条目命令ID) + " 期望" + 选择 (条目参数 == 1, "选中", "取消") + " 实际相反] "\n'
          '                    }\n'
          '                }\n'
          '            }\n')

C2_OLD = ('        变量 施加条数 <类型 = 整数>\n'
          '        施加条数 = 0\n')
C2_NEW = ('        变量 施加条数 <类型 = 整数>\n'
          '        施加条数 = 0\n'
          '        变量 回读条数 <类型 = 整数>\n'
          '        回读条数 = 0\n'
          '        菜单回读不一致 = ""\n')

C3_OLD = ('        菜单最近施加条数 = 施加条数\n'
          '        菜单施加次数 = 菜单施加次数 + 1\n')
C3_NEW = ('        // 真实菜单项数(含浏览器默认项): 这是第一次能"看见"菜单全貌\n'
          '        菜单最近项数 = 顶层菜单.取数量 ()\n'
          '        菜单回读确认条数 = 回读条数\n'
          '        菜单最近施加条数 = 施加条数\n'
          '        菜单施加次数 = 菜单施加次数 + 1\n')

# ---------- D) Core: set 里用别名解析 + 错误文案; get 里回传新字段 ----------
D1_OLD = ('                    变量 cmID <类型 = 整数>\n'
          '                    cmID = 文本到整数 (cm段.取成员 (2))\n')
D1_NEW = ('                    变量 cmID <类型 = 整数>\n'
          '                    // 支持 CEF 标准菜单项别名(back/reload/copy/…), 便于对**默认菜单项**做修改类操作\n'
          '                    cmID = MCP命令服务器.解析菜单命令ID (cm段.取成员 (2))\n')

D2_OLD = ('                            返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行是修改类(" + cm类型 + ")但命令ID 为 " + 到文本 (cmID) + " | 修改类必须给出已存在的命令ID: 自建项用你分配的 26500..28500, 浏览器默认项用其 CEF 标准ID(如 后退=100)"))\n')
D2_NEW = ('                            返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行是修改类(" + cm类型 + ")但命令ID无法识别: [" + cm段.取成员 (2) + "] | 修改类必须给出已存在的命令ID: 自建项用你分配的 26500..28500; 浏览器默认项可直接用**别名**(back/forward/reload/reload_nocache/stop/undo/redo/cut/copy/paste/delete/selectall/find/print/viewsource/nosuggestions/addtodict)或对应标准ID(如 back=100)"))\n')

D3_OLD = ('                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行命令ID越界: " + 到文本 (cmID) + " | CEF 自定义菜单命令ID 必须在 26500..28500"))\n')
D3_NEW = ('                        返回 (MCP_响应构建.命令失败 (命令ID, "规格第 " + 到文本 (取循环索引 () + 1) + " 行命令ID越界: " + 到文本 (cmID) + " | 创建类新项的命令ID 必须在 26500..28500(留0自动分配); 若要改**默认菜单项**请用修改类(del/relabel/vis/dis/mark/accel/noaccel)配别名(如 back/reload/copy)"))\n')

D4_OLD = ('"{\\"success\\":true,\\"enabled\\":" + 选择 (MCP命令服务器.菜单已启用, "true", "false") + ",\\"apply_count\\":" + 到文本 (MCP命令服务器.菜单施加次数) + ",\\"last_applied_items\\":" + 到文本 (MCP命令服务器.菜单最近施加条数) + ",\\"last_apply_time\\":\\""')
D4_NEW = ('"{\\"success\\":true,\\"enabled\\":" + 选择 (MCP命令服务器.菜单已启用, "true", "false") + ",\\"apply_count\\":" + 到文本 (MCP命令服务器.菜单施加次数) + ",\\"last_applied_items\\":" + 到文本 (MCP命令服务器.菜单最近施加条数) + ",\\"menu_item_count\\":" + 到文本 (MCP命令服务器.菜单最近项数) + ",\\"verified_items\\":" + 到文本 (MCP命令服务器.菜单回读确认条数) + ",\\"verify_mismatch\\":\\"" + MCP_响应构建.JSON转义文本 (MCP命令服务器.菜单回读不一致) + "\\",\\"last_apply_time\\":\\""')


def patch(path, pairs, tag):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % tag
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    print('   %s 换行=%s' % (tag, 'CRLF' if nl == '\r\n' else 'LF'))
    norm = [(o.replace('\n', nl), n) for o, n in pairs]
    for o, n in norm:
        c = text.count(o)
        if c != 1:
            print('!! %s 锚点命中 %d 次(应为1): %s' % (tag, c, o.strip()[:70]))
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
    return text


if patch(SERVER, [(F_ANCHOR, F_NEW), (M_ANCHOR, M_NEW),
                  (C1_OLD, C1_NEW), (C2_OLD, C2_NEW), (C3_OLD, C3_NEW)], 'MCP_Server.wsv') is None:
    sys.exit(1)
if patch(CORE, [(D1_OLD, D1_NEW), (D2_OLD, D2_NEW), (D3_OLD, D3_NEW), (D4_OLD, D4_NEW)],
         'MCP_Server_Core.wsv') is None:
    sys.exit(1)
print('完成; 备份 -> %s' % BAK)
