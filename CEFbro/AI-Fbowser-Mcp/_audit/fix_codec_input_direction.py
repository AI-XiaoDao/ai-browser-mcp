# -*- coding: utf-8 -*-
"""修 browser_codec 的一个真缺陷: **编码方向忽略了 `input`**。

实测(启用前):
  `browser_codec action=hex_encode input=base64 data="qw=="`  -> output `71773d3d`
  = ASCII "qw==" 的十六进制; 期望是 base64 解码后的单字节 0xAB → `ab`。
  `3q2+7w=="` 同理得 `3371322b37773d3d`(原文 hex), 期望 `deadbeef`。
根因: 分支里 `codec是编码` 时**直接按文本取字节**(见 Core "编码方向: data 一律按文本理解"),
把 `input` 参数整条忽略了 —— 而 schema 明写 `input: data怎么读: text(默认)/hex/base64`。

修法: 编码方向也认 `input`:
  · base64 -> 先 `FBrowser_Parser_Base64解码` 得字节, 再走 hex/base64 输出(与解码方向同一套判空);
  · hex    -> 先 `十六进制文本到字节集` 得字节(等价于"规范化 hex"再输出);
  · text   -> 维持原行为(按 action 的字符集取字节)。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '编码方向认input-写入前')

text = open(P, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'

OLD = '''            如果 (codec是编码)
            {
                // 编码方向: data 一律按文本理解, 目标字符集由 action 决定
                如果 (codec是GBK)
                {
                    codec字节 = 文本到多字节 (codec数据, 假)
                }
                否则
                {
                    codec字节 = 文本到UTF8 (codec数据, 假)
                }
            }
'''
NEW = '''            如果 (codec是编码)
            {
                // 编码方向也要认 `input`(schema 原文: data怎么读: text/hex/base64)。
                // 此前这里一律按文本取字节, 于是 `hex_encode input=base64 data="qw=="` 得到的是
                // ASCII "qw==" 的十六进制(71773d3d), 而不是解码后单字节 0xAB 的 "ab" —— 属实测缺陷。
                如果 (codec输入 == "base64")
                {
                    变量 codec编码B64 <类型 = 类_FBrowser_字节集>
                    codec编码B64 = FBrowser_Parser_Base64解码 (codec数据)
                    如果 (codec编码B64.是否为空 ())
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "base64 解码失败: 输入不是合法 base64 文本"))
                    }
                    codec字节 = codec编码B64.取字节集 ()
                }
                否则 (codec输入 == "hex")
                {
                    变量 codec编码清洗 <类型 = 文本型>
                    codec编码清洗 = 删全部空 (codec数据)
                    如果 (取文本长度 (codec编码清洗) == 0 || 取文本长度 (codec编码清洗) % 2 != 0)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "hex 输入必须是非空偶数长度的十六进制文本(每字节两位)"))
                    }
                    codec字节 = 十六进制文本到字节集 (codec编码清洗)
                }
                否则
                {
                    // 文本入: 目标字符集由 action 决定
                    如果 (codec是GBK)
                    {
                        codec字节 = 文本到多字节 (codec数据, 假)
                    }
                    否则
                    {
                        codec字节 = 文本到UTF8 (codec数据, 假)
                    }
                }
            }
'''
if text.count(OLD.replace('\n', nl)) != 1:
    print('!! 锚点命中 %d 次, 未改' % text.count(OLD.replace('\n', nl)))
    sys.exit(1)
text = text.replace(OLD.replace('\n', nl), NEW.replace('\n', nl), 1)

os.makedirs(BAK, exist_ok=True)
dst = os.path.join(BAK, 'MCP_Server_Core.wsv')
if not os.path.exists(dst):
    shutil.copy2(P, dst)
open(P, 'wb').write(text.encode('utf-8'))
print('已修: 编码方向认 input(base64/hex)')
