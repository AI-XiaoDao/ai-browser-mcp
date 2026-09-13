# -*- coding: utf-8 -*-
"""纠正"URL 协议"相关文案: 现状说 data: 全允许, 实际只允许**图片 MIME**。

## 依据(读码 + 逐种实测)
`MCP_Server.wsv` 的 `验证URL安全` 是一套**有意的安全策略**:
  · 拒绝 javascript:/vbscript:(并处理控制字符、null 字节、百分号编码绕过)
  · 拒绝 file:
  · data: **只放行图片 MIME**(image/png|jpeg|gif|webp|bmp|x-icon),
    明确拒绝 data:text/html 与 data:application/javascript —— 注释写明目的是"防 text/html XSS / script 注入"。
实测(本轮): `about:blank` 通过; `data:text/plain,hi`、`data:text/html,<b>hi</b>`、
`data:text/html;base64,...` 全部被拒 —— 与策略一致。

## 因此要改的是"文案", 不是策略
策略是对的, 但**错误信息与 4 处工具描述都在说"仅允许 http/https/about/data/ftp"**,
会让调用方以为 data: 随便用; 撞墙后既不知道**为什么**被拒, 也不知道**data: 只支持图片**,
只能反复换写法试 —— 正是本目标要消灭的体验。

改法: 常量文案 + 3 处工具描述 + 1 处源码注释, 统一写成"允许 http/https/about/ftp;
data: 仅图片类型(为防脚本注入, data:text/html 被拒)"。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

NEW_CONST = ("不支持的URL协议 | 允许: http/https/about/ftp | data: **仅图片类型**"
             "(image/png|jpeg|gif|webp|bmp|x-icon) —— 为防脚本注入, data:text/html 与 "
             "data:application/javascript 一律被拒 | 示例: browser_navigate {url:'https://www.baidu.com/'}")

NEW_DESC = (" | 允许 http/https/about/ftp; data: 仅图片类型(image/png|jpeg|gif|webp|bmp|x-icon), "
            "data:text/html 等可执行类型被拒(防脚本注入)")

JOBS = [
    (r"src\MCP_Constants.wvs", None, None),  # 占位, 下面按真实文件名处理
]

edits = []
# ① 常量文案
edits.append((r"src\MCP_Constants.wsv",
              "不支持的URL协议 | 仅允许 http/https/about/data/ftp | 示例: browser_navigate {url:'https://www.baidu.com/'}",
              NEW_CONST))
# ② 三处工具描述(各自带前缀语境, 只替换"仅支持 http/https/about/data/ftp 协议"这一短语)
PH = "仅支持 http/https/about/data/ftp 协议"
for f in (r"src\MCP_Server.wsv",):
    edits.append((f, PH, "仅支持 http/https/about/ftp 协议; data: 仅图片类型(image/png|jpeg|gif|webp|bmp|x-icon), 为防脚本注入 data:text/html 被拒"))
# ③ 源码注释
edits.append((r"src\MCP_Server_Core.wsv",
              "// 安全: 仅允许 http/https/about/data/ftp 协议",
              "// 安全: 允许 http/https/about/ftp; data: 仅图片 MIME(见 验证URL安全 的白名单)"))
# ④ 函数内注释
edits.append((r"src\MCP_Server.wsv",
              "// 5. 拒绝危险的URL协议: javascript:, file:, data:(非image/png|jpeg|gif|webp)",
              "// 5. 拒绝危险的URL协议: javascript:, file:, data:(仅放行 image/png|jpeg|gif|webp|bmp|x-icon)"))

bad = 0
for rel, old, new in edits:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        print("!! 文件不存在: %s" % rel); bad += 1; continue
    S = io.open(p, encoding="utf-8").read()
    n = S.count(old)
    if n == 0:
        print("!! 未找到锚点(%s): %s" % (rel, old[:60])); bad += 1; continue
    print("%-28s 锚点命中 %d 次 -> 替换" % (os.path.basename(rel), n))
    S = S.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="\n").write(S)

print("\n== 写后自检 ==")
for rel in (r"src\MCP_Constants.wsv", r"src\MCP_Server.wsv", r"src\MCP_Server_Core.wsv"):
    S = io.open(os.path.join(ROOT, rel), encoding="utf-8").read()
    left = S.count("http/https/about/data/ftp")
    print("  %-26s 旧文案残留 %d 处 %s" % (os.path.basename(rel), left,
                                          "OK" if left == 0 else "!! 仍有残留"))
    if left:
        bad += 1
S = io.open(os.path.join(ROOT, r"src\MCP_Constants.wsv"), encoding="utf-8").read()
c = S.count("仅图片类型")
print("  常量新文案出现 %d 次 %s" % (c, "OK" if c == 1 else "!!"))
if c != 1:
    bad += 1
S = io.open(os.path.join(ROOT, r"src\MCP_Server.wsv"), encoding="utf-8").read()
c2 = S.count("data: 仅图片类型")
print("  描述新文案出现 %d 次 (期望 3: navigate/create/scrape) %s"
      % (c2, "OK" if c2 == 3 else "!!"))
if c2 != 3:
    bad += 1
print("OK" if bad == 0 else "!! %d 项未通过" % bad)
sys.exit(1 if bad else 0)
