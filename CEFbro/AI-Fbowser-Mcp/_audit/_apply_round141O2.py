# -*- coding: utf-8 -*-
r"""修 CDP 截图载荷提取(第二轮): 上一版把**文本**直接传给了 `yyjson取文本`(它要 YYJSON 对象), 编译报错
  「无法将数据类型"文本型"转换到"YYJSON只读对象类"」。
本版: 先用既有助手 `取CDP结果对象` 读 `result`; 为空再解析外层对象的 `message`(裸 CDP 通道实测形态),
并把 `message` 里的 JSON 再解析一次取 `data`; 兜底只在"看起来不像 JSON 且够长"时才直接采用。
用法: py -3 _audit\_apply_round141O2.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
APPLY = '--apply' in sys.argv

OLD_START = '''                            // 载荷提取容错: 同步结果里 CDP 的原始载荷可能在 `result`'''
OLD_END = '''                            如果 (cdp结果文本 != "")'''

NEW = '''                            // 载荷提取容错: 同步结果里 CDP 的原始载荷可能在 `result`(包装过的工具)或
                            // `message`(裸 CDP 通道实测形态: {"success":true,"message":"{\\"data\\":\\"<base64>\\"}"}),
                            // 故两个键都试; 载荷本身可能是 JSON 对象(取 data)也可能就是 base64(直接用)。
                            // 注: 本项目读取器 `yyjson取文本` 的**第一参必须是 YYJSON 对象**, 故这里先建对象再取值。
                            变量 cdp载荷文本 <类型 = 文本型>
                            cdp载荷文本 = MCP命令服务器.yyjson取文本 (MCP命令服务器.取CDP结果对象 (cdp截图结果), "data")
                            如果 (cdp载荷文本 == "")
                            {
                                变量 cdp同步对象 <类型 = YYJSON只读对象类>
                                如果 (cdp同步对象.创建自文本 (cdp截图结果))
                                {
                                    变量 cdp消息文本 <类型 = 文本型>
                                    cdp消息文本 = MCP命令服务器.yyjson取文本 (cdp同步对象, "message")
                                    如果 (cdp消息文本 != "")
                                    {
                                        变量 cdp消息对象 <类型 = YYJSON只读对象类>
                                        如果 (cdp消息对象.创建自文本 (cdp消息文本))
                                        {
                                            cdp载荷文本 = MCP命令服务器.yyjson取文本 (cdp消息对象, "data")
                                        }
                                        如果 (cdp载荷文本 == "")
                                        {
                                            cdp载荷文本 = cdp消息文本
                                        }
                                    }
                                }
                            }
                            变量 cdp结果文本 <类型 = 文本型>
                            cdp结果文本 = ""
                            如果 (cdp载荷文本 != "")
                            {
                                // 只接受"看起来像 base64"的载荷: 够长且不含 '{'(否则会把一段 JSON 文本当图片塞回去 = 假成功)
                                如果 (取文本长度 (cdp载荷文本) > 200 && 寻找文本 (取文本左边 (cdp载荷文本, 20), "{", 0, 假) == -1)
                                {
                                    cdp结果文本 = cdp载荷文本
                                }
                            }
                            如果 (cdp结果文本 != "")'''


def main():
    txt = io.open(CORE, encoding='utf-8', newline='').read()
    i0 = txt.find(OLD_START)
    assert i0 >= 0, '未找到起点'
    i1 = txt.find(OLD_END, i0)
    assert i1 >= 0, '未找到终点'
    i1 += len(OLD_END)
    out = txt[:i0] + NEW + txt[i1:]
    print('· 已替换载荷提取块(%d 字符 -> %d 字符)' % (i1 - i0, len(NEW)))
    if APPLY:
        io.open(CORE, 'w', encoding='utf-8', newline='').write(out)
        print('   ✔ 已写入')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
