# -*- coding: utf-8 -*-
"""修复 browser_reverse_profiler: 漏调 Profiler.start, 且 stop 的 profile 被丢弃。

实测依据(本机 browser_cdp_call 原始返回, 全新进程):
  Profiler.stop (未 start)            -> {"code":-32000,"message":"No recording profiles found"}
  Profiler.enable -> Profiler.stop    -> 同上(enable 不等于 start, 这就是旧代码的漏洞)
  Profiler.start -> Profiler.stop     -> {"profile":{"nodes":[...]}} 真实剖析数据
即 start 是必需的; 旧代码 start/start_precise 只调 enable, 于是:
  * start 报成功但没开始采样
  * stop 拿不到 profile, 且走 _async 回执把内核错误也吞成 success

顺带修:
  * setSamplingInterval 去掉非该命令字段 maxDepth(实测被忽略, 属噪声);
    并注明必须**先于** start 才生效
  * stop/query 改为同步并回传真实结果(stop 的 profile 截断上限 20 万字符, 明确标注)
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
BAK = os.path.join(ROOT, '备份', '剖析器生命周期-写入前')

OLD = [
    '        如果 (方法名 == "browser_reverse_profile")',
    '        {',
    '            变量 prAction <类型 = 文本型>',
    '            prAction = MCP命令服务器.yyjson取文本 (参数JSON, "action")',
    '            如果 (prAction == "")',
    '            {',
    '                prAction = "start"',
    '            }',
    '            如果 (prAction == "start")',
    '            {',
    '                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "Profiler.enable", "{}"))',
    '            }',
    '            否则 (prAction == "start_precise")',
    '            {',
    '                变量 prPreciseParams <类型 = YYJSON对象类>',
    '                prPreciseParams.创建自文本 ("{}")',
    '                prPreciseParams.加入整数成员 ("interval", 100)',
    '                prPreciseParams.加入整数成员 ("maxDepth", 32)',
    '                变量 prPreciseRes <类型 = 文本型>',
    '                prPreciseRes = MCP命令服务器.执行逆向CDP命令 (命令ID + "_pre", "Profiler.setSamplingInterval", prPreciseParams.到可读文本 (YYJSON格式化选项.压缩))',
    r'                如果 (是否以 (prPreciseRes, "{\"error\""))',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "setSamplingInterval 提交失败: " + prPreciseRes))',
    '                }',
    '                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "Profiler.enable", "{}"))',
    '            }',
    '            否则 (prAction == "stop")',
    '            {',
    '                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "Profiler.stop", "{}"))',
    '            }',
    '            否则 (prAction == "query")',
    '            {',
    '                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "Profiler.getBestEffortCoverage", "{}"))',
    '            }',
    '            返回 (MCP_响应构建.命令失败 (命令ID, "未知action: " + prAction + " | 支持: start/start_precise/stop/query"))',
    '        }',
]

# 纯文本拼接(不建 yyjson 嵌套结构, 规避项目实测的 0xC0000005)
NEW = [
    '        如果 (方法名 == "browser_reverse_profile")',
    '        {',
    '            变量 prAction <类型 = 文本型>',
    '            prAction = MCP命令服务器.yyjson取文本 (参数JSON, "action")',
    '            如果 (prAction == "")',
    '            {',
    '                prAction = "start"',
    '            }',
    '            // 内核实测(本机, 全新进程):',
    '            //   Profiler.stop (未 start)         -> No recording profiles found',
    '            //   Profiler.enable 后 Profiler.stop -> 同样 No recording profiles found',
    '            //   Profiler.start 后 Profiler.stop  -> {"profile":{"nodes":[...]}} 真实数据',
    '            // 即 **enable 不等于 start**; 旧代码只调 enable, 采样从未开始, 而 stop 的错误又被',
    '            // _async 回执吞成 success —— 整个工具族"看似成功、拿不到数据"。故此处全部改同步。',
    '            如果 (prAction == "start")',
    '            {',
    '                变量 prEnRaw <类型 = 文本型>',
    '                prEnRaw = MCP命令服务器.执行CDP并同步等待 (命令ID + "_en", "Profiler.enable", "{}", 10000)',
    '                如果 (MCP命令服务器.CDP同步结果是否成功 (prEnRaw) == 假)',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "Profiler.enable 失败: " + MCP命令服务器.取CDP同步结果错误 (prEnRaw)))',
    '                }',
    '                变量 prStRaw <类型 = 文本型>',
    '                prStRaw = MCP命令服务器.执行CDP并同步等待 (命令ID + "_st", "Profiler.start", "{}", 10000)',
    '                如果 (MCP命令服务器.CDP同步结果是否成功 (prStRaw) == 假)',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "Profiler.start 失败: " + MCP命令服务器.取CDP同步结果错误 (prStRaw)))',
    '                }',
    '                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"start\\",\\"note\\":\\"采样已真正开始(enable+start): 执行目标操作后用 action=stop 取回 profile\\"}"))',
    '            }',
    '            否则 (prAction == "start_precise")',
    '            {',
    '                // 注意顺序: setSamplingInterval 必须**先于** start 才生效',
    '                // 该命令只认 interval; 旧代码多传的 maxDepth 实测被忽略(属另一命令的字段), 已移除',
    '                变量 prIntRaw <类型 = 文本型>',
    '                prIntRaw = MCP命令服务器.执行CDP并同步等待 (命令ID + "_int", "Profiler.setSamplingInterval", "{\\"interval\\":100}", 10000)',
    '                如果 (MCP命令服务器.CDP同步结果是否成功 (prIntRaw) == 假)',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "setSamplingInterval 失败: " + MCP命令服务器.取CDP同步结果错误 (prIntRaw)))',
    '                }',
    '                变量 prEnRaw2 <类型 = 文本型>',
    '                prEnRaw2 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_en", "Profiler.enable", "{}", 10000)',
    '                如果 (MCP命令服务器.CDP同步结果是否成功 (prEnRaw2) == 假)',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "Profiler.enable 失败: " + MCP命令服务器.取CDP同步结果错误 (prEnRaw2)))',
    '                }',
    '                变量 prStRaw2 <类型 = 文本型>',
    '                prStRaw2 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_st", "Profiler.start", "{}", 10000)',
    '                如果 (MCP命令服务器.CDP同步结果是否成功 (prStRaw2) == 假)',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "Profiler.start 失败: " + MCP命令服务器.取CDP同步结果错误 (prStRaw2)))',
    '                }',
    '                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"start_precise\\",\\"interval_us\\":100,\\"note\\":\\"已按 100 微秒间隔开始剖析\\"}"))',
    '            }',
    '            否则 (prAction == "stop")',
    '            {',
    '                变量 prStopRaw <类型 = 文本型>',
    '                prStopRaw = MCP命令服务器.执行CDP并同步等待 (命令ID, "Profiler.stop", "{}", 30000)',
    '                如果 (MCP命令服务器.CDP同步结果是否成功 (prStopRaw) == 假)',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "Profiler.stop 失败: " + MCP命令服务器.取CDP同步结果错误 (prStopRaw) + " | 若为 No recording profiles found, 说明本次没有先成功执行 action=start"))',
    '                }',
    '                // profile 是剖析主体(采样久了可达 MB 级): 截断但**明确标注**, 不静默丢数据',
    '                变量 prProfile <类型 = 文本型>',
    '                prProfile = ""',
    '                变量 prWrap <类型 = YYJSON只读对象类>',
    '                如果 (prWrap.创建自文本 (prStopRaw) == 真)',
    '                {',
    '                    prProfile = MCP命令服务器.yyjson取文本 (prWrap, "result")',
    '                }',
    '                变量 prLen <类型 = 整数>',
    '                prLen = 取文本长度 (prProfile)',
    '                变量 prCap <类型 = 整数>',
    '                prCap = 200000',
    '                如果 (prLen > prCap)',
    '                {',
    '                    prProfile = 取文本左边 (prProfile, prCap)',
    '                }',
    '                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"stop\\",\\"profile_total_chars\\":" + 到文本 (prLen) + ",\\"profile_truncated\\":" + 选择 (prLen > prCap, "true", "false") + ",\\"profile_result\\":" + 选择 (prProfile == "", "null", prProfile) + "}"))',
    '            }',
    '            否则 (prAction == "query")',
    '            {',
    '                变量 prQryRaw <类型 = 文本型>',
    '                prQryRaw = MCP命令服务器.执行CDP并同步等待 (命令ID, "Profiler.getBestEffortCoverage", "{}", 20000)',
    '                如果 (MCP命令服务器.CDP同步结果是否成功 (prQryRaw) == 假)',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "getBestEffortCoverage 失败: " + MCP命令服务器.取CDP同步结果错误 (prQryRaw)))',
    '                }',
    '                变量 prCovText <类型 = 文本型>',
    '                prCovText = ""',
    '                变量 prCovWrap <类型 = YYJSON只读对象类>',
    '                如果 (prCovWrap.创建自文本 (prQryRaw) == 真)',
    '                {',
    '                    prCovText = MCP命令服务器.yyjson取文本 (prCovWrap, "result")',
    '                }',
    '                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"query\\",\\"coverage_result\\":" + 选择 (prCovText == "", "null", prCovText) + "}"))',
    '            }',
    '            返回 (MCP_响应构建.命令失败 (命令ID, "未知action: " + prAction + " | 支持: start/start_precise/stop/query"))',
    '        }',
]


def main():
    data = open(SRC, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '源文件不应有BOM'
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    print('换行: %s' % ('CRLF' if nl == '\r\n' else 'LF'))

    old = nl.join(OLD)
    n = text.count(old)
    print('锚点命中次数: %d' % n)
    if n != 1:
        print('!! 锚点不唯一, 中止')
        return 1

    # 防坑自查: 生成的新行里, ASCII 双引号必须成对且都被 \" 转义(项目已踩过 4 次)
    for ln in NEW:
        if ln.count('\\"') % 2 != 0:
            print('!! 转义双引号数为奇数(疑似漏转义): %s' % ln)
            return 1
        stripped = ln.replace('\\"', '')
        if stripped.count('"') % 2 != 0:
            print('!! 裸双引号数为奇数(会破坏字面量): %s' % ln)
            return 1
    print('自检: ASCII 双引号转义成对')

    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Reverse.wsv'))
    print('备份 -> %s' % BAK)

    open(SRC, 'wb').write(text.replace(old, nl.join(NEW)).encode('utf-8'))
    print('已写入; 行数 %d -> %d' % (len(OLD), len(NEW)))
    return 0


sys.exit(main())
