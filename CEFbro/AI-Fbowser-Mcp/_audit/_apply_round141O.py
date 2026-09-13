# -*- coding: utf-8 -*-
r"""修 CDP 截图路径的**载荷提取**(实测: 回包有 0.03s 级健康通道但没有图片)。

## 现象(verify_round141N)
CDP 路线确实跑了(截图后 CDP 通道健康 0.03s), 但回包没有 image 字段。

## 根因
`执行CDP并同步等待` 存下来的同步结果里, CDP 的原始载荷在 **`message`** 字段(一段 JSON 文本),
而不是 `result`(项目实测: `browser_cdp_call` 的 mcp_result 形态是
`{"success":true,"message":"{\"data\":\"<base64>\"}"}`)。我上一版只读了 `result`, 于是拿到空串。

## 修法
容错提取: 依次尝试 `result` / `message`, 再把载荷当 JSON 解析取 `data`; 若载荷本身就是 base64 则直接用。

用法: py -3 _audit\_apply_round141O.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
APPLY = '--apply' in sys.argv

OLD = '''                            变量 cdp结果文本 <类型 = 文本型>
                            cdp结果文本 = MCP命令服务器.yyjson取文本 (MCP命令服务器.取CDP结果对象 (cdp截图结果), "data")
                            如果 (cdp结果文本 != "")'''

NEW = '''                            // 载荷提取容错: 同步结果里 CDP 的原始载荷可能在 `result`(包装过的工具)或
                            // `message`(裸 CDP 通道实测形态: {"success":true,"message":"{\\"data\\":\\"<base64>\\"}"}),
                            // 故两个键都试; 载荷本身可能是 JSON 对象(取 data)也可能就是 base64(直接用)。
                            变量 cdp载荷文本 <类型 = 文本型>
                            cdp载荷文本 = MCP命令服务器.yyjson取文本 (cdp截图结果, "result")
                            如果 (cdp载荷文本 == "")
                            {
                                cdp载荷文本 = MCP命令服务器.yyjson取文本 (cdp截图结果, "message")
                            }
                            变量 cdp结果文本 <类型 = 文本型>
                            cdp结果文本 = ""
                            如果 (cdp载荷文本 != "")
                            {
                                变量 cdp载荷对象 <类型 = YYJSON只读对象类>
                                如果 (cdp载荷对象.创建自文本 (cdp载荷文本))
                                {
                                    cdp结果文本 = MCP命令服务器.yyjson取文本 (cdp载荷对象, "data")
                                }
                                如果 (cdp结果文本 == "")
                                {
                                    // 载荷不是 JSON(或没有 data 键) —— 只有整段看起来像 base64 时才直接采用,
                                    // 否则会把一段 JSON 文本当成图片塞进回包(那才是真的假成功)
                                    变量 cdp载荷左边 <类型 = 文本型>
                                    cdp载荷左边 = 取文本左边 (cdp载荷文本, 8)
                                    如果 (寻找文本 (cdp载荷左边, "{", 0, 假) == -1 && 取文本长度 (cdp载荷文本) > 200)
                                    {
                                        cdp结果文本 = cdp载荷文本
                                    }
                                }
                            }
                            如果 (cdp结果文本 != "")'''


def main():
    txt = io.open(CORE, encoding='utf-8', newline='').read()
    if OLD not in txt:
        print('· 锚点未找到(可能已应用)')
        return
    assert txt.count(OLD) == 1, '命中 %d 次' % txt.count(OLD)
    txt = txt.replace(OLD, NEW, 1)
    print('· 已改为 result/message 双键容错提取')
    if APPLY:
        io.open(CORE, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
