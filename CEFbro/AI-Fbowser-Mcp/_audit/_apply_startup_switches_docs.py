# -*- coding: utf-8 -*-
r"""启动期开关通道 —— 文档 + 三份 mcp_config.json 副本 补齐补丁（本任务唯一交付脚本）。

补什么（只改文档与配置副本，绝不碰 .wsv/.vprj/.vsln 等源码）：
  1) `mcp_config.README.md` 字段简表：补齐 9 个启动期开关键（6 个既有 + 3 个新增）；
  2) `docs/MCP工具配置说明书.md`：新增 §2.4「启动期开关」小节（同一组内容）；
  3) 三份 `mcp_config.json` 副本（根目录 / src / _int/.../linker）：各追加 3 个键
     `enable_cross_frame` / `disable_proxy` / `startup_switches`（缺别的既有键也不顺手补）。

硬约束（脚本自己保证）：
  · 默认 dry-run，只有显式 `--apply` 才落盘；任何一处校验不过 -> **一个字节都不写**；
  · 每个锚点必须命中**恰好 1 次**（命中数 != 1 立即报错退出）；
  · 行尾（CRLF/LF）与编码（utf-8/gbk）按**文件原样**保留：全程走 bytes -> decode -> 插入
    -> encode，不统一行尾、不转码、不静默去 BOM；
  · JSON 追加后必须 `json.loads` 通过，并打印键数前后对比；
  · 幂等：目标键/小节已存在则跳过并说明；**部分存在**视为歧义状态，直接报错退出（不猜）；
  · dry-run 逐文件打印「文件 / 锚点 / 旧文本 / 新文本」。

用法：
    py -3 _audit/_apply_startup_switches_docs.py                # dry-run（本任务只跑这个）
    py -3 _audit/_apply_startup_switches_docs.py --selftest     # dry-run + 内存内幂等自证（仍不写盘）
    py -3 _audit/_apply_startup_switches_docs.py --apply        # 落盘（本次**未执行**）

未验证声明：本脚本只做文本级补齐 + JSON 合法性/行尾编码保真校验，**不编译、不启动 exe、
不调用 MCP 接口**。因此「文档描述与运行期行为一致」这件事**没有被本脚本验证**。
"""
import json
import os
import re
import sys

# ---------- 控制台 UTF-8 兜底（与 _audit/_console.py 同款，避免打印中文时崩掉） ----------
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

README = os.path.join(ROOT, "mcp_config.README.md")
DOC = os.path.join(ROOT, "docs", "MCP工具配置说明书.md")
JSON_FILES = [
    os.path.join(ROOT, "mcp_config.json"),
    os.path.join(ROOT, "src", "mcp_config.json"),
    os.path.join(ROOT, "_int", "AI-Fbowser-Mcp", "debug", "x64", "linker", "mcp_config.json"),
]

NEW_JSON_KEYS = [
    ("enable_cross_frame", "false"),
    ("disable_proxy", "false"),
    ("startup_switches", "{}"),
]

RESTART = "**仅启动期生效，改动后必须重启进程**"

# ---------- README: 9 行简表（README 表只有 3 列 -> 类型与默认值合并在第 2 格） ----------
README_ROWS = [
    "| `enable_media_stream` | `false`（bool） | 启动期对内核命令行调用 `命令行.启用摄像头`，放开摄像头/麦克风媒体流采集。" + RESTART + " |",
    "| `enable_speech_input` | `false`（bool） | 启动期对内核命令行调用 `命令行.启用录音`，放开语音输入/麦克风采集。" + RESTART + " |",
    "| `enable_autoplay` | `false`（bool） | 启动期对内核命令行调用 `命令行.启用自动播放`，放开带声自动播放策略。" + RESTART + " |",
    "| `disable_gpu` | `false`（bool） | 启动期对内核命令行调用 `命令行.禁用GPU`，GPU 异常时的排障开关（渲染/截图可能变慢）。" + RESTART + " |",
    "| `disable_gpu_cache` | `false`（bool） | 启动期对内核命令行调用 `命令行.禁用GPU缓存`，绕开 GPU 着色器缓存损坏。" + RESTART + " |",
    "| `ignore_gpu_blocklist` | `false`（bool） | 启动期对内核命令行调用 `命令行.忽略GPU禁用清单`，强制启用被内核拉黑的 GPU。" + RESTART + " |",
    "| `enable_cross_frame` | `false`（bool） | **新增**。启动期调用 `命令行.启用跨框架操作模式 ()`，解除「框架之间不能直接操作」的内核限制"
    "（与 iframe 子框架填表互补；**不改同源策略**）。风险：类库自述**「存在不安全性」**，按需短开、用完改回 `false` 重启。" + RESTART + " |",
    "| `disable_proxy` | `false`（bool） | **新增**。启动期调用 `命令行.禁用代理 ()`，**连 Windows 系统自动检测代理一起关掉**"
    "（`browser_clear_proxy` 做不到这点）。用途：代理设坏导致全站打不开时的干净排障手段。" + RESTART + " |",
    "| `startup_switches` | `{}`（对象） | **新增**。受控的「名→值」白名单表，启动期逐项调用 `命令行.置项值 (名, 值)`。"
    "**只接受代码里写死的 4 个名**：`lang`（语言标签，≤32 字符）、`force-device-scale-factor`（必须在 0.5~4 之间）、"
    "`disable-blink-features`、`disable-features`（后两者只允许字母/数字/下划线/连字符/逗号）。"
    "未通过校验的条目**不生效**，但会如实记入回执 `rejected_switches`。" + RESTART + " |",
]

README_NOTES = [
    "",
    "**启动期开关共用说明**：上表 9 个键**只在启动期**由 `启动类.即将处理命令行` 施加到 CEF 内核命令行，"
    "改了必须**重启进程**才生效，运行期没有补做手段。施加结果可调只读工具 **`browser_startup_args` 自查**"
    "（`action` 缺省 `get`，可传 `list`）：回执含 `applied_switches`（本次实际应用过的开关）、"
    "`command_line_raw`（内核命令行原文）、`name_value_switches`（通过校验的名值对）、"
    "`rejected_switches`（被拒条目）、`enable_cross_frame`、`disable_proxy`、`note`。",
]

# ---------- docs: §2.4 小节（该文档表格是 4 列：字段 | 类型 | 默认 | 说明） ----------
DOC_ROWS = [
    "| `enable_media_stream` | bool | `false` | 启动期调用 `命令行.启用摄像头`：放开摄像头/麦克风媒体流采集。" + RESTART + " |",
    "| `enable_speech_input` | bool | `false` | 启动期调用 `命令行.启用录音`：放开语音输入/麦克风采集。" + RESTART + " |",
    "| `enable_autoplay` | bool | `false` | 启动期调用 `命令行.启用自动播放`：放开带声自动播放策略。" + RESTART + " |",
    "| `disable_gpu` | bool | `false` | 启动期调用 `命令行.禁用GPU`：GPU 异常时的排障开关（渲染/截图可能变慢）。" + RESTART + " |",
    "| `disable_gpu_cache` | bool | `false` | 启动期调用 `命令行.禁用GPU缓存`：绕开 GPU 着色器缓存损坏。" + RESTART + " |",
    "| `ignore_gpu_blocklist` | bool | `false` | 启动期调用 `命令行.忽略GPU禁用清单`：强制启用被内核拉黑的 GPU。" + RESTART + " |",
    "| `enable_cross_frame` | bool | `false` | **新增**。启动期调用 `命令行.启用跨框架操作模式 ()`：解除「框架之间不能直接操作」的内核限制"
    "（与 iframe 子框架填表互补；**不改同源策略**）；风险＝类库自述「存在不安全性」。" + RESTART + " |",
    "| `disable_proxy` | bool | `false` | **新增**。启动期调用 `命令行.禁用代理 ()`：**连 Windows 系统自动检测代理一起关掉**"
    "（`browser_clear_proxy` 做不到这点）；用途＝代理设坏导致全站打不开时的干净排障手段。" + RESTART + " |",
    "| `startup_switches` | object | `{}` | **新增**。受控的「名→值」白名单表，逐项 `命令行.置项值 (名, 值)`；"
    "**只接受 4 个写死的名**（约束见下），未过校验的条目不生效但记入回执 `rejected_switches`。" + RESTART + " |",
]

DOC_SECTION = [
    "",
    "### 2.4 启动期开关（" + RESTART + "）",
    "",
    "这些键在 **`启动类.即将处理命令行`** 施加（`src/main.wsv`，`进程类型 == \"\"` 的浏览器进程分支），"
    "结果见只读工具 **`browser_startup_args`**。运行期**无法补做**：改了 `mcp_config.json` 必须**重启 AI浏览器.exe**。",
    "",
    "| 字段 | 类型 | 默认 | 说明 |",
    "|------|------|------|------|",
] + DOC_ROWS + [
    "",
    "**施加结果自查（`browser_startup_args`，`action` 缺省 `get`、可传 `list`）**：回执字段 `applied_switches`"
    "（本次实际应用过的开关）、`command_line_raw`（内核命令行原文）、`name_value_switches`（通过校验的名值对）、"
    "`rejected_switches`（被拒条目）、`enable_cross_frame`、`disable_proxy`、`note`。",
    "",
    "**新增 3 键的风险与限制**",
    "",
    "- **`enable_cross_frame`**（bool，默认 `false`）：启动期调用 `命令行.启用跨框架操作模式 ()`，"
    "解除「框架之间不能直接操作」的内核限制（与 iframe 子框架填表互补；**不改同源策略**）。"
    "风险：类库自述**「存在不安全性」** —— 按需短开，用完改回 `false` 重启。",
    "- **`disable_proxy`**（bool，默认 `false`）：启动期调用 `命令行.禁用代理 ()`，"
    "**连 Windows 系统自动检测代理一起关掉**（`browser_clear_proxy` 做不到这点）。"
    "用途：代理设坏导致全站打不开时的干净排障手段；排障完改回 `false` 重启。",
    "- **`startup_switches`**（对象，默认 `{}`）：受控的「名→值」白名单表，启动期逐项调用 `命令行.置项值 (名, 值)`。"
    "**只接受代码里写死的 4 个名**：`lang`（语言标签，≤32 字符）、`force-device-scale-factor`（必须在 0.5~4 之间）、"
    "`disable-blink-features`、`disable-features`（后两者只允许字母/数字/下划线/连字符/逗号）。"
    "未通过校验的条目**不生效**，但会被如实记入回执 `rejected_switches`（不静默丢弃）。"
    "不裸透传任意 `--xxx` 串：一个 `--single-process` 就能让内核不可用。",
    "",
    "```json",
    "{",
    "  \"enable_cross_frame\": false,",
    "  \"disable_proxy\": false,",
    "  \"startup_switches\": { \"lang\": \"zh-CN\", \"force-device-scale-factor\": \"1.25\" }",
    "}",
    "```",
]

# --- 锚点（全部为**行首前缀**，插入点取该行行尾，避免行内中段插入把表格行切坏） ---
README_ANCHOR = "| `auto_dismiss_js_dialog`"
DOC_ANCHOR = "| `window_width` / `window_height`"
JSON_ANCHOR = '"ignore_gpu_blocklist"'


def die(msg):
    print("")
    print("[ABORT] " + msg)
    print("[ABORT] 未写入任何文件。")
    sys.exit(1)


class Source(object):
    """按原样读取一个文件：bytes -> decode(原编码) -> 插入 -> encode(原编码)。"""

    def __init__(self, path):
        self.path = path
        if not os.path.isfile(path):
            die("文件不存在: " + path)
        self.raw = open(path, "rb").read()
        self.bom = self.raw.startswith(b"\xef\xbb\xbf")
        body = self.raw[3:] if self.bom else self.raw
        self.text = None
        self.enc = None
        for enc in ("utf-8", "gbk"):
            try:
                self.text = body.decode(enc)
                self.enc = enc
                break
            except UnicodeDecodeError:
                continue
        if self.enc is None:
            die("既非 utf-8 也非 gbk，拒绝猜测编码: " + path)
        self.crlf = self.text.count("\r\n")
        self.lone_lf = len(re.findall(r"(?<!\r)\n", self.text))
        self.lone_cr = len(re.findall(r"\r(?!\n)", self.text))
        if self.crlf and self.lone_lf:
            self.mixed = True
        else:
            self.mixed = False
        self.dominant_eol = "\r\n" if self.crlf >= self.lone_lf and self.crlf else "\n"

    @classmethod
    def stub(cls, path, text, enc="utf-8", bom=False):
        """内存内 Source（不读盘）：给 --selftest 做"二次规划 = 应幂等跳过"的自证。"""
        o = cls.__new__(cls)
        o.path = path
        o.raw = None
        o.text = text
        o.enc = enc
        o.bom = bom
        o.crlf = text.count("\r\n")
        o.lone_lf = len(re.findall(r"(?<!\r)\n", text))
        o.lone_cr = len(re.findall(r"\r(?!\n)", text))
        o.mixed = bool(o.crlf and o.lone_lf)
        o.dominant_eol = "\r\n" if o.crlf >= o.lone_lf and o.crlf else "\n"
        return o

    def size(self):
        return -1 if self.raw is None else len(self.raw)

    def diag(self):
        return ("编码 %s / BOM %s / CRLF %d / 纯LF %d / 纯CR %d / 行尾风格 %s"
                % (self.enc, "有" if self.bom else "无", self.crlf, self.lone_lf, self.lone_cr,
                   "混合(!)" if self.mixed else ("CRLF" if self.dominant_eol == "\r\n" else "LF")))

    def eol_of_line(self, j):
        """j = 该行最后一个字符之后的位置；返回该行自身的行尾序列（行尾缺失则回退到全文件主流行尾）。"""
        if self.text.startswith("\r\n", j):
            return "\r\n"
        if self.text.startswith("\n", j):
            return "\n"
        if self.text.startswith("\r", j):
            return "\r"
        return self.dominant_eol

    def encode(self, new_text):
        return (b"\xef\xbb\xbf" if self.bom else b"") + new_text.encode(self.enc)


class Edit(object):
    def __init__(self, path, kind, anchor, anchor_hits, line_no, old_text, new_block, new_text):
        self.path = path
        self.kind = kind
        self.anchor = anchor
        self.anchor_hits = anchor_hits
        self.line_no = line_no
        self.old_text = old_text
        self.new_block = new_block
        self.new_text = new_text


def anchor_line_end(src, anchor, what):
    """锚点必须**恰好命中 1 次**；返回 (插入点=该行行尾位置, 行号, 该行原文)。"""
    hits = src.text.count(anchor)
    if hits != 1:
        die("%s 锚点命中 %d 次（要求恰好 1 次）: %r" % (what, hits, anchor))
    i = src.text.find(anchor)
    line_start = src.text.rfind("\n", 0, i) + 1
    if src.text[line_start:i].strip() != "":
        die("%s 锚点不在行首: %r" % (what, anchor))
    j = i + len(anchor)
    while j < len(src.text) and src.text[j] not in "\r\n":
        j += 1
    line_no = src.text.count("\n", 0, i) + 1
    return j, line_no, src.text[line_start:j]


def plan_markdown(src, anchor, block_lines, marker, what, extra_checks):
    """markdown 插入：在锚点行之后整块插入；插入块内每行都按该行原有行尾拼接。"""
    if marker in src.text:
        return "幂等跳过（已含 %s）" % marker
    j, line_no, line = anchor_line_end(src, anchor, what)
    eol = src.eol_of_line(j)
    block = "".join(eol + ln for ln in block_lines)
    new_text = src.text[:j] + block + src.text[j:]
    for name, cond, detail in extra_checks:
        if not cond(new_text):
            die("%s 应用后自检失败: %s (%s)" % (what, name, detail))
    ed = Edit(src.path, what, anchor, 1, line_no, line, block, new_text)
    ed.kind_args = ("md", anchor, block_lines, marker, what, extra_checks)
    return ed


def plan_json(src, what):
    present = [n for n, _ in NEW_JSON_KEYS if ('"%s"' % n) in src.text]
    if len(present) == len(NEW_JSON_KEYS):
        return "幂等跳过（已含 %s）" % ", ".join(present)
    if present:
        die("%s 只存在部分目标键 %s —— 状态歧义，拒绝猜测，请人工确认" % (what, ", ".join(present)))
    if src.bom:
        die("%s 带 UTF-8 BOM（要求保持无 BOM），不静默去 BOM、也不带 BOM 写回" % what)
    if src.enc != "utf-8":
        die("%s 编码为 %s（要求 UTF-8），拒绝转码" % (what, src.enc))
    if src.mixed:
        die("%s 行尾混合（CRLF+LF），拒绝猜测" % what)

    j_end, line_no, line = anchor_line_end(src, JSON_ANCHOR, what)
    tail = src.text[j_end:]
    if not re.match(r"\s*\}\s*$", tail):
        die("%s 锚点键 %s 之后不是收尾 `}`（说明它后面还有别的键），拒绝插入: %r"
            % (what, JSON_ANCHOR, tail[:40]))
    if line.rstrip().endswith(","):
        die("%s 锚点行已带尾逗号，拒绝二次加逗号: %r" % (what, line))
    indent = re.match(r"[ \t]*", line).group(0)

    try:
        before = json.loads(src.text)
    except Exception as exc:
        die("%s 追加前就不是合法 JSON（不动它）: %s" % (what, exc))

    eol = src.eol_of_line(j_end)
    parts = []
    for idx, (name, val) in enumerate(NEW_JSON_KEYS):
        comma = "," if idx < len(NEW_JSON_KEYS) - 1 else ""
        parts.append(eol + indent + '"%s": %s%s' % (name, val, comma))
    block = "".join(parts)
    new_text = src.text[:j_end] + "," + block + src.text[j_end:]

    try:
        after = json.loads(new_text)
    except Exception as exc:
        die("%s 追加后不是合法 JSON（不写盘）: %s" % (what, exc))
    if len(after) != len(before) + len(NEW_JSON_KEYS):
        die("%s 键数异常: %d -> %d" % (what, len(before), len(after)))
    for k in before:
        if k not in after:
            die("%s 追加后丢了原键 %s" % (what, k))
    for name, val in NEW_JSON_KEYS:
        if name not in after:
            die("%s 追加后仍缺 %s" % (what, name))
    if list(after.keys())[-len(NEW_JSON_KEYS):] != [n for n, _ in NEW_JSON_KEYS]:
        die("%s 新增键未落在文件末尾: %s" % (what, list(after.keys())[-4:]))
    if sorted(before.keys()) != sorted([k for k in after.keys() if k not in dict(NEW_JSON_KEYS)]):
        die("%s 键集合变化超出预期" % what)

    ed = Edit(src.path, what, JSON_ANCHOR, 1, line_no, line, block, new_text)
    ed.kind_args = ("json",)
    ed.keys_before = list(before.keys())
    ed.keys_after = list(after.keys())
    ed.indent = indent
    return ed


def main():
    argv = [a for a in sys.argv[1:]]
    for a in argv:
        if a not in ("--apply", "--dry-run", "--selftest"):
            die("未知参数 %r（只支持 --apply / --dry-run / --selftest）" % a)
    apply_mode = "--apply" in argv
    self_test = "--selftest" in argv

    print("=" * 100)
    print("启动期开关通道 —— 文档 + 配置副本补齐补丁")
    print("根目录: %s" % ROOT)
    print("模式  : %s" % ("APPLY（会落盘）" if apply_mode else "DRY-RUN（只打印，不写盘）"))
    print("=" * 100)

    edits = []
    skipped = []

    # ---------- 1) mcp_config.README.md ----------
    print("")
    print("-" * 100)
    print("[1/5] %s" % README)
    src = Source(README)
    print("      字节 %d / %s" % (src.size(), src.diag()))
    print("      现有启动期开关键: %s"
          % (", ".join(k for k in ("enable_media_stream", "enable_speech_input", "enable_autoplay",
                                   "disable_gpu", "disable_gpu_cache", "ignore_gpu_blocklist",
                                   "enable_cross_frame", "disable_proxy", "startup_switches")
                       if "`%s`" % k in src.text) or "（一个都没有）"))
    res = plan_markdown(
        src, README_ANCHOR, README_ROWS + README_NOTES, "enable_cross_frame",
        "README 字段简表",
        [("9 行键齐备", lambda t: all("`%s`" % k in t for k in
                                     ("enable_media_stream", "enable_speech_input", "enable_autoplay",
                                      "disable_gpu", "disable_gpu_cache", "ignore_gpu_blocklist",
                                      "enable_cross_frame", "disable_proxy", "startup_switches")), "缺键"),
         ("重启提示 9 处", lambda t: t.count(RESTART) >= 9, "重启提示不足 9 处"),
         ("browser_startup_args 自查句", lambda t: "browser_startup_args" in t, "缺自查句")])
    if isinstance(res, Edit):
        edits.append(res)
    else:
        skipped.append((README, res))
        print("      %s" % res)

    # ---------- 2) docs/MCP工具配置说明书.md ----------
    print("")
    print("-" * 100)
    print("[2/5] %s" % DOC)
    src = Source(DOC)
    print("      字节 %d / %s" % (src.size(), src.diag()))
    has_24 = "### 2.4" in src.text
    print("      已有 §2.4 小节: %s / 已有 启动期 字样: %d 处 / 已有 browser_startup_args: %d 处"
          % ("是" if has_24 else "否", src.text.count("启动期"), src.text.count("browser_startup_args")))
    res = plan_markdown(
        src, DOC_ANCHOR, DOC_SECTION, "enable_cross_frame",
        "docs §2.4 启动期开关",
        [("9 行键齐备", lambda t: all("`%s`" % k in t for k in
                                     ("enable_media_stream", "enable_speech_input", "enable_autoplay",
                                      "disable_gpu", "disable_gpu_cache", "ignore_gpu_blocklist",
                                      "enable_cross_frame", "disable_proxy", "startup_switches")), "缺键"),
         ("施加点写法", lambda t: "`启动类.即将处理命令行`" in t, "缺 施加点"),
         ("施加结果见工具", lambda t: "browser_startup_args" in t, "缺 browser_startup_args"),
         ("4 个允许名", lambda t: all(x in t for x in
                                      ("`lang`", "`force-device-scale-factor`", "`disable-blink-features`",
                                       "`disable-features`")), "缺允许名"),
         ("跨框架风险", lambda t: "不安全性" in t, "缺风险"),
         ("禁用代理用途", lambda t: "排障" in t, "缺用途")])
    if isinstance(res, Edit):
        edits.append(res)
    else:
        skipped.append((DOC, res))
        print("      %s" % res)

    # ---------- 3) 三份 mcp_config.json ----------
    for idx, path in enumerate(JSON_FILES):
        print("")
        print("-" * 100)
        print("[%d/5] %s" % (3 + idx, path))
        src = Source(path)
        print("      字节 %d / %s" % (src.size(), src.diag()))
        try:
            keys = list(json.loads(src.text).keys())
        except Exception as exc:
            die("%s 当前不是合法 JSON: %s" % (path, exc))
        print("      现有键 %d 个: %s" % (len(keys), ", ".join(keys)))
        res = plan_json(src, "mcp_config.json 副本")
        if isinstance(res, Edit):
            edits.append(res)
            print("      缩进风格: %r（%d 格）" % (res.indent, len(res.indent)))
        else:
            skipped.append((path, res))
            print("      %s" % res)

    # ---------- 预览 ----------
    print("")
    print("=" * 100)
    print("变更预览（文件 / 锚点 / 旧文本 / 新文本）")
    print("=" * 100)
    for ed in edits:
        print("")
        print("【%s】%s" % (ed.kind, ed.path))
        print("  锚点        : %r（命中 %d 次，锚点行 %d）" % (ed.anchor, ed.anchor_hits, ed.line_no))
        print("  旧文本（锚点整行）:")
        print("      " + ed.old_text)
        print("  新文本（紧随锚点行插入的块，行尾/缩进按该文件原样）:")
        for ln in ed.new_block.splitlines() or [""]:
            print("      " + ln)
        if hasattr(ed, "keys_before"):
            print("  JSON 键数   : %d -> %d" % (len(ed.keys_before), len(ed.keys_after)))
            print("  JSON 键序   : %s" % ", ".join(ed.keys_after))
        print("  字节数      : %d -> %d" % (Source(ed.path).size(),
                                            len(Source(ed.path).encode(ed.new_text))))

    print("")
    print("-" * 100)
    if skipped:
        print("幂等跳过 %d 项:" % len(skipped))
        for p, why in skipped:
            print("  · %s -> %s" % (p, why))
    else:
        print("无跳过项。")
    print("待应用变更 %d 项。" % len(edits))

    if self_test:
        print("")
        print("-" * 100)
        print("--selftest：把每个新文本装回内存 Source 再规划一次（证明幂等；不写盘）")
        print("-" * 100)
        for ed in edits:
            stub = Source.stub(ed.path, ed.new_text)
            if ed.kind_args[0] == "md":
                _, anchor, block, marker, what, checks = ed.kind_args
                res2 = plan_markdown(stub, anchor, block, marker, what, checks)
            else:
                res2 = plan_json(stub, "mcp_config.json 副本")
            if isinstance(res2, Edit):
                die("幂等自检失败：%s 二次规划仍产生变更" % ed.path)
            print("  · %s -> %s" % (ed.path, res2))

    if not apply_mode:
        print("")
        print("[dry-run] 未写入任何文件。要落盘请显式加 --apply。")
        return

    # ---------- 落盘（本任务未执行） ----------
    print("")
    print("=" * 100)
    print("APPLY：写盘 + 回读校验")
    print("=" * 100)
    for ed in edits:
        src = Source(ed.path)
        with open(ed.path, "wb") as f:
            f.write(src.encode(ed.new_text))
        chk = Source(ed.path)
        if chk.bom != src.bom or chk.enc != src.enc or chk.dominant_eol != src.dominant_eol:
            die("写盘后 BOM/编码/行尾发生变化: " + ed.path)
        if chk.text != ed.new_text:
            die("写盘后内容与预期不一致: " + ed.path)
        if ed.path.endswith(".json"):
            after = json.loads(chk.text)
            print("  · %s -> 键数 %d，行尾 %s，编码 %s，BOM %s，合法 JSON 是"
                  % (ed.path, len(after), "CRLF" if chk.dominant_eol == "\r\n" else "LF",
                     chk.enc, "有" if chk.bom else "无"))
        else:
            print("  · %s -> 字节 %d，行尾 %s，编码 %s，BOM %s"
                  % (ed.path, chk.size(), "CRLF" if chk.dominant_eol == "\r\n" else "LF",
                     chk.enc, "有" if chk.bom else "无"))
    print("")
    print("已写入 %d 个文件。" % len(edits))


main()
