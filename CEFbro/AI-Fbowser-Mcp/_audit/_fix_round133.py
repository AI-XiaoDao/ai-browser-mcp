# -*- coding: utf-8 -*-
r"""第133轮(修补): 上一版把 HINT 追加到了描述字符串**之外**(成了裸文本 ⇒ 编译报"发现字符处于无效位置"),
且 `last_paused` 的 parse 声明因锚点少了 `, 假` 没删掉。这里**整行重写**这三行, 一次改对。

规则(第133轮两次踩坑的教训, 记牢):
  · 往描述里加文字, 锚点**不要包含结尾的引号** —— 否则新文字会落到字符串外面;
  · 删 schema 参数时, 锚点要覆盖到该实参的**全部**(含 `, 假` 这类必填开关);
  · 回读断言不能用"参数名是否出现在这一行"(说明文字里也会提到它), 要用 `属性项JSON ("名"` / `单参数Schema文本 ("名"`。

用法: py -3 _audit\_fix_round133.py [--apply]
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

HINT = (' | 说明(第133轮更正): 本工具**不支持**限定脚本范围 —— 旧 schema 里那个不生效的参数已删除'
        '(传了会被忽略才是更坏的情况); 想只看某个脚本, 请先用 browser_reverse_search_script 或 '
        'browser_reverse_extract mode=scan 拿到脚本, 再用 browser_reverse_extract 的 mode=download(script_index) 取内容')

# 三行的"描述主体"与"尾部 schema"(整行重写, 避免锚点式修改再次落错位置)
PLAN = [
    # (工具名, 描述主体(不含尾引号), 行尾(可空; 形如  ", 空Schema文本 ()"))
    ("browser_debugger_last_paused",
     "最近断点暂停信息(VIP) | 说明(第133轮更正): 本工具**不读** parse 参数(旧 schema 误抄了 evaluate 的参数, 已删除)"
     " —— 它始终返回最近一次暂停的原始信息",
     ""),
    ("browser_reverse_scan_crypto",
     "逆向定位: 加密算法特征扫描。扫描全部已加载脚本, 识别MD5(常量0x67452301)/AES(S-box)/SHA(初始向量)/CryptoJS/"
     "自定义base64编码表/RSA特征, 返回每个命中脚本的特征清单——快速判断sign/token用的什么算法" + HINT,
     ", 空Schema文本 ()"),
    ("browser_reverse_detect_obfuscator",
     "逆向解密: 混淆器类型识别。检测obfuscator.io(_0x十六进制数组)/JsJiami/sojson/JSVMP大switch状态机/自定义编码表/"
     "十六进制字符串数组特征, 给出置信度——选择正确的反混淆策略" + HINT,
     ""),
]


def main():
    lines = io.open(SERVER, encoding='utf-8').read().split('\n')
    done = []
    for tool, desc, tail in PLAN:
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
        i = idx[0]
        assert '"' not in desc, '%s 描述里有 ASCII 双引号(火山里非法)' % tool
        lines[i] = '添加工具JSON ("%s", "%s"%s)' % (tool, desc, tail)
        done.append(tool)
    out = '\n'.join(lines)
    print('MCP_Server.wsv: 整行重写 %d 行:' % len(done))
    for d in done:
        print('   · %s' % d)
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        for tool in ('browser_debugger_last_paused', 'browser_reverse_scan_crypto', 'browser_reverse_detect_obfuscator'):
            ln = [l for l in c.split('\n') if '添加工具JSON ("%s"' % tool in l][0]
            assert not re.search(r'(属性项JSON|单参数Schema文本|多属性Schema文本) \("(parse|script_index)"', ln), \
                '%s 仍声明该参数' % tool
        assert '\r' not in c
        print('已写入并回读校验通过(三行均不再声明 parse/script_index)')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
