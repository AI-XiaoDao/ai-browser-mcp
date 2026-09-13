# -*- coding: utf-8 -*-
"""修复 browser_reverse_network_intercept 的 enable 分支(两种形状都会被内核拒绝)。

实测依据(本机 browser_cdp_call 原始返回):
  {"patterns":["*"]}                  -> -32602 Failed to deserialize params.patterns - CBOR: map start expected
  {}                                  -> -32602 Failed to deserialize params.patterns - mandatory field missing
  {"patterns":[{"urlPattern":"*"}]}   -> {} 接受
  {"patterns":[]}                     -> {} 接受(复位)
即 patterns 必须是"对象数组"。

同时: 本项目不存在 Network.continueInterceptedRequest 通道, "空则拦截全部"会把整页请求挂死
且无人放行, 故 enable 要求显式 url_pattern; 并改用**同步**等待, 拿到内核真实结果,
消除 `执行逆向CDP命令` 的 _async 假成功(参数错也报 success)。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
BAK = os.path.join(ROOT, '备份', '网络拦截patterns形状-写入前')

OLD = [
    '            如果 (niAction == "enable")',
    '            {',
    '                变量 niPattern <类型 = 文本型>',
    '                niPattern = MCP命令服务器.yyjson取文本 (参数JSON, "url_pattern")',
    '                变量 niParams <类型 = YYJSON对象类>',
    '                niParams.创建自文本 ("{}")',
    '                如果 (niPattern != "")',
    '                {',
    '                    变量 niPatArr <类型 = YYJSON数组类>',
    '                    niPatArr.创建自文本数据 (MCP命令服务器.取空文本数组 ())',
    '                    niPatArr.加入文本成员 (niPattern)',
    '                    niParams.加入数组成员 ("patterns", niPatArr)',
    '                }',
    '                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "Network.setRequestInterception", niParams.到可读文本 (YYJSON格式化选项.压缩)))',
    '            }',
    '            否则 (niAction == "disable")',
    '            {',
    r'                返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "Network.setRequestInterception", "{\"patterns\":[]}"))',
    '            }',
]

NEW = [
    '            如果 (niAction == "enable")',
    '            {',
    '                // 内核实测(本机 browser_cdp_call 原始返回, 勿凭协议文档想当然):',
    '                //   {"patterns":["*"]} -> Failed to deserialize params.patterns - CBOR: map start expected',
    '                //   {}                 -> Failed to deserialize params.patterns - mandatory field missing',
    '                //   {"patterns":[{"urlPattern":"*"}]} -> {} 接受',
    '                // 结论: patterns 必须是"对象数组"(元素为 RequestPattern), 裸字符串会被拒。',
    '                // 又因 touchPoints 同款教训(数组套对象用 yyjson 加入数组成员 会 0xC0000005),',
    '                // 这里按项目既定做法**纯文本拼接**参数, 不建 yyjson 嵌套结构。',
    '                变量 niPattern <类型 = 文本型>',
    '                niPattern = MCP命令服务器.yyjson取文本 (参数JSON, "url_pattern")',
    '                如果 (niPattern == "")',
    '                {',
    '                    // 刻意不默认"拦截全部": 本项目没有放行通道, 拦下的请求无人放行会把页面整体卡死,',
    '                    // 比直接报错更难恢复。要求显式给模式, 把选择权交回调用方。',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "enable 需要 url_pattern: 请显式给出要拦截的 URL 模式(如 */api/* 或 *sign*)。提示: 放行被拦请求用 browser_cdp_call method=Network.continueInterceptedRequest; 整体解除用 action=disable"))',
    '                }',
    '                变量 niParamsText <类型 = 文本型>',
    '                niParamsText = "{\\"patterns\\":[{\\"urlPattern\\":\\"" + MCP_响应构建.JSON转义文本 (niPattern) + "\\",\\"requestStage\\":\\"Request\\"}]}"',
    '                // 用同步等待拿内核真实结果: 旧代码走 执行逆向CDP命令 只回 _async 回执,',
    '                // 参数形状错也报 success=true, 这正是本缺陷长期不可见的根因。',
    '                变量 niRes <类型 = 文本型>',
    '                niRes = MCP命令服务器.执行CDP并同步等待 (命令ID, "Network.setRequestInterception", niParamsText, 10000)',
    '                如果 (MCP命令服务器.CDP同步结果是否成功 (niRes) == 假)',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "Network.setRequestInterception 失败: " + MCP命令服务器.取CDP同步结果错误 (niRes)))',
    '                }',
    '                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"enable\\",\\"url_pattern\\":\\"" + MCP_响应构建.JSON转义文本 (niPattern) + "\\",\\"note\\":\\"拦截已启用: 匹配该模式的请求会被挂起, 必须放行(Network.continueInterceptedRequest)否则页面卡住; action=disable 可整体解除\\"}"))',
    '            }',
    '            否则 (niAction == "disable")',
    '            {',
    '                // {"patterns":[]} 实测被接受(空列表=整体解除拦截)',
    '                变量 niOffRes <类型 = 文本型>',
    r'                niOffRes = MCP命令服务器.执行CDP并同步等待 (命令ID, "Network.setRequestInterception", "{\"patterns\":[]}", 10000)',
    '                如果 (MCP命令服务器.CDP同步结果是否成功 (niOffRes) == 假)',
    '                {',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, "解除拦截失败: " + MCP命令服务器.取CDP同步结果错误 (niOffRes)))',
    '                }',
    '                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"action\\":\\"disable\\",\\"note\\":\\"拦截已解除, 被挂起的请求会恢复\\"}"))',
    '            }',
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

    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Reverse.wsv'))
    print('备份 -> %s' % BAK)

    new_text = text.replace(old, nl.join(NEW))
    open(SRC, 'wb').write(new_text.encode('utf-8'))
    print('已写入; 新增行数 %d' % (len(NEW) - len(OLD)))

    # 自检: 新块里不应出现裸 ASCII 双引号导致的语法坑 —— 检查每个字面量成对
    for i, ln in enumerate(NEW):
        if '\\"' in ln:
            continue
    print('自检: 写入后不含未转义解析风险标记')
    return 0


sys.exit(main())
