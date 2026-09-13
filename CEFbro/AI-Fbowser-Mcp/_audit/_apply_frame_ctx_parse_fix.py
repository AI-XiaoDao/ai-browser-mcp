# -*- coding: utf-8 -*-
r"""修正 解析框架执行上下文 的 CDP 结果解析 (实测根因: 存储层把 CDP 结果再包了一层字符串)。

依据: MCP_Server.wsv:2212~2248 (收到CDP响应) 存的是
    {"success":true,"messageId":N,"method":"...","result":"<CDP 结果原文>"}
`result` 是**文本成员**, 序列化后内层引号变成 \" 形式 —— 故按原文扫描 `"id":"` 必然全部落空
(实测: 四个臂全部返回 -1, 且与框架清单无关)。

本补丁:
  1) 新增 取CDP结果文本 (存储JSON) -> 文本型: 先按 JSON 取 result, 取不到再解一层转义兜底;
  2) 把 解析框架执行上下文 里的两处"按原文扫描"改成扫描该结果体;
  3) createIsolatedWorld 的结果改用 yyJSON 取 executionContextId(不再手写数字扫描)。

安全断言: 替换区间与插入前, 类内 `{`/`}` 净额(按字符串字面量外的花括号计)必须不变。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

START_MARK = '        // CDP 侧框架树: 按出现顺序抽出所有 frame id(**不引 JSON 数组解析**, 顺序即树序)'
END_MARK = '        返回 (文本到整数 (取文本中间 (建世界结果, 数字起, 数字止 - 数字起)))'
HELPER_BEFORE = '    # 把"目标框架"(CEF 框架ID `6-XXXX` / 框架名 / 序号)解析成 **CDP 执行上下文ID**。'

NEW_BODY = '''        // CDP 框架树: 顺序即树序(主框架在前, 深度优先) —— 与 CEF 侧清单同序, 故按序号对齐即可。
        // 注意: 存储层把 CDP 结果再包了一层(result 是**被转义的 JSON 字符串**),
        // 直接按原文扫描 "id":" 会被转义吃成 \\"id\\":\\" 而全部落空 —— 故先经 取CDP结果文本 解包。
        变量 树文本 <类型 = 文本型>
        树文本 = 执行CDP并同步等待 ("mcp_frametree_" + 到文本 (取启动时间 ()), "Page.getFrameTree", "{}", 8000)
        变量 树体 <类型 = 文本型>
        树体 = 取CDP结果文本 (树文本)
        如果 (树体 == "" || 寻找文本 (树体, "frameTree", 0, 假) == -1)
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
            起点 = 寻找文本 (树体, "\\"id\\":\\"", 扫描位, 假)
            如果 (起点 == -1)
            {
                跳出循环
            }
            变量 值起 <类型 = 整数>
            值起 = 起点 + 6
            变量 终点 <类型 = 整数>
            终点 = 寻找文本 (树体, "\\"", 值起, 假)
            如果 (终点 == -1)
            {
                跳出循环
            }
            如果 (已见 == 目标序号)
            {
                命中ID = 取文本中间 (树体, 值起, 终点 - 值起)
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
        变量 世界体 <类型 = 文本型>
        世界体 = 取CDP结果文本 (建世界结果)
        如果 (世界体 == "")
        {
            返回 (-1)
        }
        变量 世界容器 <类型 = YYJSON只读对象类>
        如果 (世界容器.创建自文本 (世界体) == 假)
        {
            返回 (-1)
        }
        变量 上下文值 <类型 = 整数>
        上下文值 = yyjson取整数 (世界容器, "executionContextId")
        如果 (上下文值 <= 0)
        {
            返回 (-1)
        }
        返回 (上下文值)'''

HELPER = '''    # 从"存储层 CDP 结果"里取出 **CDP 侧结果体**。
    # 依据(源码): 收到CDP响应 存的是 {"success":..,"messageId":..,"result":"<CDP 结果原文>"} ——
    # result 是**文本成员**, 序列化后内层引号呈 \\" 形式; 直接按存储原文扫描模式串会全部落空。
    # 先用 yyJSON 取 result(自动反转义), 取不到再按存储原文解一层转义兜底。
    方法 取CDP结果文本 <公开 静态 类型 = 文本型 @输出名 = "GetCDPResultBody" @强制输出 = 真>
    参数 存储JSON <类型 = 文本型 @输出名 = "StoreJSON">
    {
        如果 (存储JSON == "")
        {
            返回 ("")
        }
        变量 容器 <类型 = YYJSON只读对象类>
        如果 (容器.创建自文本 (存储JSON))
        {
            变量 结果体 <类型 = 文本型>
            结果体 = yyjson取文本 (容器, "result")
            如果 (结果体 != "")
            {
                返回 (结果体)
            }
        }
        变量 归一 <类型 = 文本型>
        归一 = 存储JSON
        子文本替换 (归一, "\\\\\\"", "\\"", , , 假)
        返回 (归一)
    }

'''


def depth_delta(lines):
    """字符串字面量之外的 { } 净额; 跳过 @ 开头的嵌入式 C++ 行。"""
    bal = 0
    for ln in lines:
        k = 0
        if ln.lstrip().startswith('@'):
            continue
        in_str = False
        while k < len(ln):
            c = ln[k]
            if in_str:
                if c == '\\':
                    k += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == '{':
                    bal += 1
                elif c == '}':
                    bal -= 1
            k += 1
    return bal


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '文件带 BOM'
    assert b'\r\n' not in raw, '文件含 CRLF'
    text = raw.decode('utf-8')
    lines = text.split('\n')

    starts = [i for i, l in enumerate(lines) if l == START_MARK]
    ends = [i for i, l in enumerate(lines) if l == END_MARK]
    hpos = [i for i, l in enumerate(lines) if l == HELPER_BEFORE]
    assert len(starts) == 1, 'START 标记命中 %d 次' % len(starts)
    assert len(ends) == 1, 'END 标记命中 %d 次' % len(ends)
    assert len(hpos) == 1, 'HELPER 锚点命中 %d 次' % len(hpos)
    s, e, h = starts[0], ends[0], hpos[0]
    assert h < s < e, '区间顺序异常 h=%d s=%d e=%d' % (h, s, e)

    old_range = lines[s:e + 1]
    new_range = NEW_BODY.split('\n')
    assert depth_delta(old_range) == depth_delta(new_range), \
        '花括号净额变化: %d -> %d' % (depth_delta(old_range), depth_delta(new_range))

    # 插入 helper(在注释锚点之前), 自身必须自平衡
    helper_lines = HELPER.rstrip('\n').split('\n')
    assert depth_delta(helper_lines) == 0, 'helper 自身不平衡: %d' % depth_delta(helper_lines)

    out = lines[:s] + new_range + lines[e + 1:]
    # helper 锚点在替换区间**之前**(h < s), 故此处按原索引 h 插入仍然有效
    h2 = [i for i, l in enumerate(out) if l == HELPER_BEFORE]
    assert len(h2) == 1, '替换后锚点命中 %d 次' % len(h2)
    assert h2[0] == h, '锚点漂移: %d -> %d' % (h, h2[0])
    out = out[:h] + helper_lines + [''] + out[h:]

    whole_before = depth_delta(lines)
    whole_after = depth_delta(out)
    assert whole_before == whole_after == 0, '整文件净额 %d -> %d' % (whole_before, whole_after)

    keys = ('子文本替换 (归一', '寻找文本 (树体', '建世界命令 = ', '取CDP结果文本 (树', '取CDP结果文本 (建')
    if '--dump' in sys.argv and '--apply' not in sys.argv:
        prev = os.path.join(ROOT, '_audit', '_frame_ctx_preview.wsv')
        with io.open(prev, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out))
        print('预览已写出: %s' % prev)
        for i, l in enumerate(out, 1):
            if any(k in l for k in keys):
                print('   %5d | %s' % (i, l))
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out))
        print('已写入 %s (行数 %d -> %d)' % (TARGET, len(lines), len(out)))
    else:
        print('[dry-run] 区间 %d..%d 共 %d 行 -> %d 行; 再插入 helper %d 行; 行数 %d -> %d'
              % (s + 1, e + 1, len(old_range), len(new_range), len(helper_lines),
                 len(lines), len(out)))
        print('花括号净额: 区间 %d -> %d; helper %d; 整文件 %d -> %d'
              % (depth_delta(old_range), depth_delta(new_range),
                 depth_delta(helper_lines), whole_before, whole_after))
        print('提示: 加 --apply 落盘')


main()
