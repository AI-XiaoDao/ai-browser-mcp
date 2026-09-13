# -*- coding: utf-8 -*-
"""修复 browser_execute_js 丢弃"用户 JS 抛异常"的真原因, 并避免把用户代码**再执行一遍**。

实测现象(verify_reverse_search_and_exc.py 臂①):
    browser_execute_js {code:"throw new Error('mcp-fmt-probe-7d21')"}
  -> "[无法序列化的值] 可能原因: ①JS返回了DOM对象/函数等…"
  该文本来自**原生回退路径**(MCP_Callbacks.wsv:51), 与真实原因无关。

根因(MCP_Server_Core.wsv, browser_execute_js 分支):
    CDP值 = CDP执行JS并等待 (code, …)
    如果 (CDP值 != "" && CDP值 != "undefined" && 是否以 (CDP值, "{\"error\"") == 假)  -> 成功
    // 否则一律继续往下走原生回退
  CDP 侧对异常返回的是 `{"error":"JS异常:<真原因> @line .. col .."}`, 也以 {"error" 开头,
  于是被判成"CDP 不可用"而进入原生回退。后果三条:
    ① 真原因被丢弃(即使格式化器已给出 "Error: mcp-fmt-probe-7d21 @line 0 col ..");
    ② **用户代码被再执行一次**(原生路径) —— 副作用跑两遍, 属安全性问题;
    ③ 最终报成与原因无关的 "[无法序列化的值]"。

修法: 把 "JS异常:" 认定为**终局结论**(CDP 已明确回答), 直接失败返回真原因, 不再回退。
       "CDP执行失败:" 等通道类错误仍照旧走原生回退(那是回退存在的意义)。

本脚本用 chr(92)/chr(34) 拼接, 规避转义歧义; 写前断言锚点唯一; 先备份。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', 'JS异常终局判定-写入前')
B = chr(92)   # 反斜杠
Q = chr(34)   # 双引号

# 锚点: 第279行(不含引号/反斜杠, 可安全字面书写)
ANCHOR = '                CDP值 = MCP命令服务器.CDP执行JS并等待 (code, MCP_常量.同步等待_JS执行超时, 真)'

# Volcano 源码里这一行写作: 如果 (是否以 (CDP值, "{\"error\":\"JS异常:"))
COND = ('                如果 (是否以 (CDP值, ' + Q + '{' + B + Q + 'error' + B + Q + ':'
        + B + Q + 'JS异常:' + Q + '))')

INSERT = '\n'.join([
    '                // ★ 修(正确性+副作用安全, 实测): CDP 已**明确**报出"用户 JS 抛异常"时, 该结论是终局的。',
    '                //   原来它与"CDP 通道不可用"共用同一条判据(只要以 {"error" 开头就继续往下走原生回退),',
    '                //   于是用户代码抛错会: ①真原因被丢弃 ②**在原生路径上再执行一次**(副作用跑两遍)',
    '                //   ③最终报成与原因无关的 "[无法序列化的值]"。',
    '                //   实测: browser_execute_js {code:"throw new Error(...)"} 就是这样掩盖了异常原因的。',
    '                //   注: "CDP执行失败:" 等通道类错误仍照旧回退 —— 那才是回退存在的意义。',
    COND,
    '                {',
    '                    变量 cdp异常解析 <类型 = YYJSON只读对象类>',
    '                    变量 cdp异常文本 <类型 = 文本型>',
    '                    如果 (cdp异常解析.创建自文本 (CDP值))',
    '                    {',
    '                        cdp异常文本 = MCP命令服务器.yyjson取文本 (cdp异常解析, "error")',
    '                    }',
    '                    如果 (cdp异常文本 == "")',
    '                    {',
    '                        cdp异常文本 = CDP值',
    '                    }',
    '                    返回 (MCP_响应构建.命令失败 (命令ID, cdp异常文本 + " | 该异常由你提供的 code 抛出, 属终局结论: CDP 已明确回答, 未再走原生回退(避免把 code 重复执行一遍)"))',
    '                }',
])


def rd(p):
    with io.open(p, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def wr(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def main():
    c = rd(CORE)
    n = c.count(ANCHOR)
    print("[锚点] 出现次数 = %d" % n)
    if n != 1:
        print("!! 预期恰好 1 次, 中止")
        return 1
    if 'JS异常:' in c and 'cdp异常文本' in c:
        print("!! 似乎已打过补丁, 中止")
        return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(CORE, os.path.join(BAK, os.path.basename(CORE)))
    print("已备份到 %s" % BAK)
    c2 = c.replace(ANCHOR, ANCHOR + '\n' + INSERT)
    assert c2.count('cdp异常文本') >= 3
    wr(CORE, c2)
    print("OK: 已插入 JS 异常终局判定 (锚点后 %d 行)" % (INSERT.count('\n') + 1))
    with io.open(CORE, 'rb') as f:
        raw = f.read()
    print("复核: BOM=%s CRLF=%s 字节=%d"
          % (raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
