# -*- coding: utf-8 -*-
r"""G1b: 让 JS 能在**指定 iframe 的执行上下文**里求值(补上一轮"读不到 iframe"的缺口)。

已实测的配方(见报告 §137.4, `_audit/probe_cdp_frame_id_map.py` 原始回包):
  ① CEF 的框架标识(`6-XXXX`, 来自 `browser.取框架ID ()`)与 **CDP 的 frameId 不是同一套**;
  ② 但两侧框架清单**同序**(实测 5 vs 5, 主框架在前, 深度优先) —— 见 `_audit/probe_frame_mapping.py`;
  ③ 用 CDP frameId 调 `Page.createIsolatedWorld {frameId, worldName, grantUniversalAccess:true}`
     拿到 `executionContextId`, 再 `Runtime.evaluate {expression, contextId, returnByValue}` —— 实测能读到
     iframe(含嵌套 iframe)内部 DOM。

本补丁:
  ① `CDP执行JS并等待` 增加可选第 4 参 `执行上下文ID`(默认 0 = 不指定, **完全向后兼容**);
  ② 新增 `解析框架执行上下文 (浏览器, 目标框架) -> 整数`:
     空/main/主框架 -> 0(主框架); 命中 CEF id 或框架名 -> 该框架的 CDP 上下文; 纯数字 -> 序号;
     找不到 -> -1(调用方须报可行动错误, **不得**静默退回主框架);
  ③ `browser_execute_js` 支持 `frame_id`, 并把它写进描述/schema。
"""
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
BAK = os.path.join(ROOT, '备份', '框架内求值-写入前')
problems = []


def load(p):
    t = open(p, 'rb').read().decode('utf-8')
    return t, ('\r\n' if '\r\n' in t else '\n')


def save(p, text, name):
    os.makedirs(BAK, exist_ok=True)
    dst = os.path.join(BAK, name)
    if not os.path.exists(dst):
        shutil.copy2(p, dst)
    open(p, 'wb').write(text.encode('utf-8'))


def rep(text, old, new, tag, nl='\n'):
    o = old.replace('\n', nl)
    if text.count(o) != 1:
        problems.append('%s: 命中 %d 次' % (tag, text.count(o)))
        return text
    for ln in new.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号: %s' % (tag, ln.strip()[:90]))
            return text
    print('   ok %s' % tag)
    return text.replace(o, new.replace('\n', nl), 1)


# ─────────── Server ───────────
s, nl = load(os.path.join(SRC, 'MCP_Server.wsv'))

# ① 可选上下文参
s = rep(s, '''    参数 JS代码 <类型 = 文本型 @输出名 = "JSCode">
    参数 最大等待毫秒 <类型 = 整数 @默认值 = 15000 @输出名 = "MaxWaitMs">
    参数 返回ByValue <类型 = 逻辑型 @默认值 = 真 @输出名 = "ReturnByValue">
    {
''', '''    参数 JS代码 <类型 = 文本型 @输出名 = "JSCode">
    参数 最大等待毫秒 <类型 = 整数 @默认值 = 15000 @输出名 = "MaxWaitMs">
    参数 返回ByValue <类型 = 逻辑型 @默认值 = 真 @输出名 = "ReturnByValue">
    参数 执行上下文ID <类型 = 整数 @默认值 = 0 注释 = "0=默认上下文(主框架); >0 时在指定执行上下文求值(见 解析框架执行上下文)" @输出名 = "ExecutionContextId">
    {
''', 'CDP执行JS并等待 增加上下文参', nl)

s = rep(s, '''        evalParams.加入逻辑值成员 ("includeCommandLineAPI", 假)
        变量 存储结果 <类型 = 文本型>
''', '''        evalParams.加入逻辑值成员 ("includeCommandLineAPI", 假)
        如果 (执行上下文ID > 0)
        {
            // 实测: 只有带上 contextId, Runtime.evaluate 才会在**该 iframe** 的上下文里求值
            // (否则一律在主框架求值 —— 这正是上一轮"fill_attr_get 带 frame_id 仍读主框架"的根因)
            evalParams.加入整数成员 ("contextId", 执行上下文ID)
        }
        变量 存储结果 <类型 = 文本型>
''', 'CDP执行JS并等待 带上 contextId', nl)

# ② 解析器
HELPER = '''    # 把"目标框架"(CEF 框架ID `6-XXXX` / 框架名 / 序号)解析成 **CDP 执行上下文ID**。
    # 返回: 0 = 主框架(调用方用默认上下文); >0 = 该框架的上下文; -1 = 框架不存在(调用方必须报错, 不得静默回退主框架)。
    # 依据(本机实测): CEF 的框架标识与 CDP frameId **不是同一套**, 但两侧清单**同序**(主框架在前, 深度优先);
    # 故这里按序号把 CEF 清单与 CDP 框架树对齐, 再 createIsolatedWorld 取上下文。
    方法 解析框架执行上下文 <公开 静态 类型 = 整数 @输出名 = "ResolveFrameContextId" @强制输出 = 真>
    参数 浏览器 <类型 = 类_FBrowser_浏览器 @输出名 = "Browser">
    参数 目标框架 <类型 = 文本型 @输出名 = "TargetFrame">
    {
        如果 (目标框架 == "" || 目标框架 == "main" || 目标框架 == "主框架")
        {
            返回 (0)
        }
        如果 (浏览器.是否为空 ())
        {
            返回 (-1)
        }
        变量 id数组 <类型 = FBrowser_文本数组>
        id数组 = 浏览器.取框架ID ()
        变量 name数组 <类型 = FBrowser_文本数组>
        name数组 = 浏览器.取框架名称 ()
        变量 目标序号 <类型 = 整数>
        目标序号 = -1
        变量 帧位 <类型 = 整数>
        计次循环 (id数组.取个数 ())
        {
            帧位 = 取循环索引 ()
            如果 (目标序号 == -1 && id数组.取成员 (帧位) == 目标框架)
            {
                目标序号 = 帧位
            }
            如果 (目标序号 == -1 && 帧位 < name数组.取个数 ())
            {
                变量 该帧名 <类型 = 文本型>
                该帧名 = name数组.取成员 (帧位)
                如果 (该帧名 != "" && 该帧名 == 目标框架)
                {
                    目标序号 = 帧位
                }
            }
        }
        如果 (目标序号 == -1)
        {
            变量 候选序号 <类型 = 整数>
            候选序号 = 文本到整数 (目标框架)
            如果 (候选序号 >= 0 && 候选序号 < id数组.取个数 ())
            {
                目标序号 = 候选序号
            }
        }
        如果 (目标序号 == -1)
        {
            返回 (-1)
        }
        // CDP 侧框架树: 按出现顺序抽出所有 frame id(**不引 JSON 数组解析**, 顺序即树序)
        变量 树文本 <类型 = 文本型>
        树文本 = 执行CDP并同步等待 ("mcp_frametree_" + 到文本 (取启动时间 ()), "Page.getFrameTree", "{}", 8000)
        如果 (树文本 == "" || 寻找文本 (树文本, "frameTree", 0, 假) == -1)
        {
            返回 (-1)
        }
        变量 扫描位 <类型 = 整数>
        扫描位 = 0
        变量 已见 <类型 = 整数>
        已见 = 0
        变量 命中ID <类型 = 文本型>
        命中ID = ""
        判断循环 (真)
        {
            变量 起点 <类型 = 整数>
            起点 = 寻找文本 (树文本, "\\"id\\":\\"", 扫描位, 假)
            如果 (起点 == -1)
            {
                跳出循环
            }
            变量 值起 <类型 = 整数>
            值起 = 起点 + 6
            变量 终点 <类型 = 整数>
            终点 = 寻找文本 (树文本, "\\"", 值起, 假)
            如果 (终点 == -1)
            {
                跳出循环
            }
            如果 (已见 == 目标序号)
            {
                命中ID = 取文本中间 (树文本, 值起, 终点 - 值起)
                跳出循环
            }
            已见 = 已见 + 1
            扫描位 = 终点 + 1
        }
        如果 (命中ID == "")
        {
            返回 (-1)
        }
        变量 建世界命令 <类型 = 文本型>
        建世界命令 = "{\\"frameId\\":\\"" + 命中ID + "\\",\\"worldName\\":\\"mcp_frame\\",\\"grantUniversalAccess\\":true}"
        变量 建世界结果 <类型 = 文本型>
        建世界结果 = 执行CDP并同步等待 ("mcp_world_" + 到文本 (取启动时间 ()), "Page.createIsolatedWorld", 建世界命令, 8000)
        如果 (建世界结果 == "")
        {
            返回 (-1)
        }
        变量 上下文位 <类型 = 整数>
        上下文位 = 寻找文本 (建世界结果, "executionContextId", 0, 假)
        如果 (上下文位 == -1)
        {
            返回 (-1)
        }
        变量 数字起 <类型 = 整数>
        数字起 = -1
        变量 扫描2 <类型 = 整数>
        扫描2 = 上下文位 + 19
        判断循环 (扫描2 < 取文本长度 (建世界结果))
        {
            变量 当前字 <类型 = 文本型>
            当前字 = 取文本中间 (建世界结果, 扫描2, 1)
            如果 (当前字 == ":")
            {
                数字起 = 扫描2 + 1
                跳出循环
            }
            如果 (寻找文本 ("0123456789", 当前字, 0, 假) != -1)
            {
                数字起 = 扫描2
                跳出循环
            }
            扫描2 = 扫描2 + 1
        }
        如果 (数字起 == -1)
        {
            返回 (-1)
        }
        变量 数字止 <类型 = 整数>
        数字止 = 数字起
        判断循环 (数字止 < 取文本长度 (建世界结果))
        {
            变量 数位 <类型 = 文本型>
            数位 = 取文本中间 (建世界结果, 数字止, 1)
            如果 (寻找文本 ("0123456789", 数位, 0, 假) == -1)
            {
                跳出循环
            }
            数字止 = 数字止 + 1
        }
        如果 (数字止 <= 数字起)
        {
            返回 (-1)
        }
        返回 (文本到整数 (取文本中间 (建世界结果, 数字起, 数字止 - 数字起)))
    }

'''
anchor = '    # 解析"要操作哪个填表框架"'
if s.count(anchor) != 1:
    problems.append('解析器插入锚点命中 %d' % s.count(anchor))
else:
    s = s.replace(anchor, HELPER.replace('\n', nl) + anchor, 1)
    print('   ok 解析框架执行上下文 已插入')
save(os.path.join(SRC, 'MCP_Server.wsv'), s, 'MCP_Server.wsv')

print('\n问题: %r' % problems)
sys.exit(1 if problems else 0)
