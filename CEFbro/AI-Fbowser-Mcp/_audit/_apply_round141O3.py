# -*- coding: utf-8 -*-
r"""修 CDP 截图参数构造(第三轮): 把 `clip` 作为**文本成员**塞进 YYJSON 对象, 于是下发给 CDP 的成了
`"clip":"{\"x\":0,...}"`(字符串) 而不是对象 ⇒ CDP 回 **Invalid parameters**。

修法: 本项目 YYJSON 对象不支持嵌套对象成员(既有做法都是字符串拼接), 故整段 params 用拼接构造,
`clip` 直接内联为对象字面量。

用法: py -3 _audit\_apply_round141O3.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
APPLY = '--apply' in sys.argv

OLD = '''                        变量 cdp截图参数 <类型 = YYJSON对象类>
                        cdp截图参数.创建自文本 ("{}")
                        cdp截图参数.加入文本成员 ("format", fmt)
                        如果 (fmt != "png")
                        {
                            cdp截图参数.加入整数成员 ("quality", 截图质量)
                        }
                        cdp截图参数.加入逻辑值成员 ("fromSurface", 从表面截图)
                        如果 (视窗之外)
                        {
                            cdp截图参数.加入逻辑值成员 ("captureBeyondViewport", 真)
                        }
                        cdp截图参数.加入文本成员 ("clip", cdpClip.到可读文本 (YYJSON格式化选项.压缩))
                        变量 cdp截图结果 <类型 = 文本型>
                        cdp截图结果 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_shot", "Page.captureScreenshot", cdp截图参数.到可读文本 (YYJSON格式化选项.压缩), 20000)'''

NEW = '''                        // ⚠ 参数必须**整段拼接**: 本项目的 YYJSON 对象不支持嵌套对象成员 ——
                        //   用 加入文本成员("clip", "{...}") 会把它变成**字符串**, CDP 直接回 Invalid parameters
                        //   (既有做法也都是字符串拼接, 见 汇总JSON 等)。
                        变量 cdp截图参数文本 <类型 = 文本型>
                        cdp截图参数文本 = "{\\"format\\":\\"" + fmt + "\\""
                        如果 (fmt != "png")
                        {
                            cdp截图参数文本 = cdp截图参数文本 + ",\\"quality\\":" + 到文本 (截图质量)
                        }
                        cdp截图参数文本 = cdp截图参数文本 + ",\\"fromSurface\\":" + 选择 (从表面截图, "true", "false")
                        如果 (视窗之外)
                        {
                            cdp截图参数文本 = cdp截图参数文本 + ",\\"captureBeyondViewport\\":true"
                        }
                        cdp截图参数文本 = cdp截图参数文本 + ",\\"clip\\":" + cdpClip.到可读文本 (YYJSON格式化选项.压缩) + "}"
                        变量 cdp截图结果 <类型 = 文本型>
                        cdp截图结果 = MCP命令服务器.执行CDP并同步等待 (命令ID + "_shot", "Page.captureScreenshot", cdp截图参数文本, 20000)'''


def main():
    txt = io.open(CORE, encoding='utf-8', newline='').read()
    if OLD not in txt:
        print('· 锚点未找到(可能已应用)')
        return
    assert txt.count(OLD) == 1, '命中 %d 次' % txt.count(OLD)
    txt = txt.replace(OLD, NEW, 1)
    print('· 已改为整段拼接构造 CDP 截图参数')
    if APPLY:
        io.open(CORE, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
