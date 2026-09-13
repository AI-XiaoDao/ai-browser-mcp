# -*- coding: utf-8 -*-
"""
_audit/_apply_dpi_v8_startup.py  ——  只改 src/main.wsv 的补丁脚本 (默认 dry-run)

三处改动 (全部遵守「默认不改变现有行为」):
  改动1  进程 DPI 感知模式     配置键 dpi_aware        默认 假  -> 不进入分支
  改动2  V8 渲染进程堆栈上限   配置键 v8_max_stack_mb  默认 0   -> 不进入分支
  改动3  订正一处实测证明已陈旧的注释 (app_* 族不会入库) —— 纯注释, 不改代码

绝对约束 (脚本内逐条断言, 任一不过即 SystemExit, 绝不写盘):
  * 只改 src/main.wsv 这一个文件
  * 锚点逐字照抄原文, 命中数必须 == 1
  * 写盘前断言: UTF-8 无 BOM + 纯 LF (无 CR)
  * 写盘前断言: 字符串字面量之外的 { } 与 ( ) 净额前后完全相同
               (跳过 @ 行 与 整行 // 注释; 另额外断言被替换区段的引号奇偶性一致,
                否则字符串状态机可能跨界错位)
  * 断言改动1/2 的插入行号 < 「FBrowser_初始化 (」 所在行号
  * 幂等: 已存在则报错退出
  * 默认 dry-run; 仅当显式传 --apply 才写盘 (本脚本按任务要求只跑 dry-run)

用法:
  py -3 _audit/_apply_dpi_v8_startup.py            # dry-run, 不写盘
  py -3 _audit/_apply_dpi_v8_startup.py --apply    # 写盘 (任务禁止执行)
"""

import difflib
import io
import os
import sys

# 控制台默认按 cp936 编码, 中文会乱码 —— 强制 UTF-8 输出 (仅影响本脚本 stdout)
for _stream in ("stdout", "stderr"):
    try:
        getattr(sys, _stream).reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARGET_REL = "src/main.wsv"
TARGET = os.path.join(ROOT, "src", "main.wsv")

# ----------------------------------------------------------------------------
# 锚点 (逐字照抄 src/main.wsv 原文)
# ----------------------------------------------------------------------------

# 改动1/2 的插入锚点: 紧贴 FBrowser_初始化 之前的独立一行
ANCHOR_INIT_EVT = "        变量 初始化事件 <类型 = 类_FBrowser_事件智能指针>"

# 仅用于校验 (必须存在且唯一)
ANCHOR_INIT_CALL = "        如果真 (FBrowser_初始化 (设置, 初始化事件) == 假)"
ANCHOR_MAIN_METHOD = "    方法 启动方法 <公开 类型 = 整数>"

# 改动3 锚点A: main.wsv:921-922 (断言 app_* 族因缺接线而记不下来 —— 已实测证伪)
ANCHOR_C3_A = (
    "    # 背景: 实测发现 类_MCP_初始化事件 里所有 渲染_* 覆盖, 以及既有的\n"
    "    #   进程间消息_收到主进程消息, 都从未被回调(应用事件因此一条也记不下来)。"
)

# 改动3 锚点B: main.wsv:928 (断言装上事件类后渲染进程浏览器会派发事件到本类 —— 已实测证伪)
ANCHOR_C3_B = "    # 故此处把本项目的事件类装上, 使内部/渲染进程创建的浏览器也派发事件到我们。"

# 幂等哨兵: 这些串出现在原文即说明补丁已打过
SENTINELS = (
    "FBrowser_设置程序DPI模式",
    "FBrowser_初始化_设置V8环境默认堆栈大小",
    "MCP命令服务器.启动DPI感知模式",
    "MCP命令服务器.V8堆栈上限MB",
)

# ----------------------------------------------------------------------------
# 改动1/2 的插入正文 (位于 方法 启动方法 子语句体内 -> 用 // 行注释)
# ----------------------------------------------------------------------------

INSERT_TEXT = (
    "        // ======== 启动期 DPI 感知 (配置键 dpi_aware, 默认 假 = 不改变现有行为) ========\n"
    "        // 接线依据: FBroLib.wsv:260 方法 FBrowser_设置程序DPI模式 <公开 静态 类型 = 逻辑型>\n"
    "        //   参数 DPI模式 <类型 = DPI模式>; 类库注释原文「设置当前程序的DPI感知模式,在程序入口初始化之前调用」。\n"
    "        // 常量依据: FBroConst.wsv:759 类 DPI模式 <公开 @常量类 = 整数>, :767 常量 按显示器感知V2 <公开 值 = -4>\n"
    "        //   (对应 DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)。本文件已有同类「常量类.成员」限定写法先例:\n"
    "        //   :65 目录删除模式.全部删除、:98 日志级别.致命 (日志级别 定义在类库 FBroConst.wsv 包 FBrowser.常量)。\n"
    "        // 副作用(必须知情): DPI 感知是**进程级**的 —— 开启后 HiDPI(缩放 != 100%) 下窗口按物理像素解释,\n"
    "        //   CSS 视口(innerWidth/innerHeight)会随之变小, 鼠标注入坐标/点击落点/元素取矩形类工具的观测值一并改变。\n"
    "        //   默认 假 时不进入本分支, 现有行为一字不变。\n"
    "        如果 (MCP命令服务器.启动DPI感知模式)\n"
    "        {\n"
    "            FBrowser_设置程序DPI模式 (DPI模式.按显示器感知V2)\n"
    "        }\n"
    "        // ======== 启动期 V8 渲染进程堆栈上限 (配置键 v8_max_stack_mb, 默认 0 = 不改变现有行为) ========\n"
    "        // 接线依据: FBroLib.wsv:184 方法 FBrowser_初始化_设置V8环境默认堆栈大小 <公开 静态>\n"
    "        //   参数 初始尺寸 <类型 = 整数 注释=「单位:MB; 不设置或者设置为0及为内核的默认值」>\n"
    "        //   参数 最大尺寸 <类型 = 整数 注释=「单位:MB; ...32位程序允许最大值不能超过4000MB」>;\n"
    "        //   类库注释原文「必须在初始化之前设置, 只针对渲染进程」——故必须在 FBrowser_初始化 之前调用。\n"
    "        // 语义: 首参固定 0 = 内核默认初始尺寸(不动), **只放宽上限, 不改语义**;\n"
    "        //   32 位构建上限 4000MB(类库原文), 配置超过该值不会被内核采纳。\n"
    "        //   默认 0 时不进入本分支, 现有行为一字不变。\n"
    "        如果 (MCP命令服务器.V8堆栈上限MB > 0)\n"
    "        {\n"
    "            FBrowser_初始化_设置V8环境默认堆栈大小 (0, MCP命令服务器.V8堆栈上限MB)\n"
    "        }\n"
)

# ----------------------------------------------------------------------------
# 改动3 的替换正文 (位于类定义体内 -> 只能继续用 # 行注释, // 在类体层不是合法行)
# 事实不得改变: app_* 族不入库; 渲染进程是 SDK 自带 FBroSubprocess.exe;
#               事件不派发到本项目事件覆盖上; 对照臂 load_end/title_changed 正常。
# ----------------------------------------------------------------------------

REPLACE_C3_A = (
    "    # 背景: 本项目为此把事件类接到 获取默认事件 上(见下), 期望内部/渲染进程创建的浏览器也派发事件到这里。\n"
    "    # 实测(报告 141 节): 本机 app_* 族(含 app_render_*/app_v8_*/app_startup_*)不会入库 —— 渲染进程是 SDK 自带的 FBroSubprocess.exe,\n"
    "    # 事件不派发到本项目的事件覆盖上; 对照臂 load_end/title_changed 正常。此处保留接线仅为「若将来换构建即可生效」, 请勿据此承诺事件可用。"
)

REPLACE_C3_B = (
    "    # 故此处把本项目的事件类装上(类_MCP_浏览器事件): 仅完成「正确接线」这一事实, "
    "不构成 app_* 族可用的承诺 —— 按上述实测, 本机该族仍不会入库。"
)

# ----------------------------------------------------------------------------
# 基础设施
# ----------------------------------------------------------------------------

FAILURES = []


def check(cond, msg):
    tag = "[OK]  " if cond else "[FAIL]"
    print("%s %s" % (tag, msg))
    if not cond:
        FAILURES.append(msg)
    return cond


def split_lines(text):
    """返回 (行列表, 是否以换行结尾) —— 行列表不含换行符"""
    trailing = text.endswith("\n")
    body = text[:-1] if trailing else text
    return body.split("\n"), trailing


def count_occurrences(text, needle):
    return text.count(needle)


def line_no_of(text, needle):
    """needle 在 text 中的 1-based 行号列表"""
    hits = []
    for idx, line in enumerate(text.split("\n"), start=1):
        if needle in line:
            hits.append(idx)
    return hits


def balance(text):
    """统计字符串字面量之外的 { } ( ) 个数。

    跳过: 去掉前导空白后以 '@' 开头的行 (嵌入式 C/C++ 行)
          去掉前导空白后以 '//' 开头的行 (整行 // 注释)
    字符串: 以 ASCII 双引号为界, 串内 '\\' 转义下一个字符。
    返回 (open_brace, close_brace, open_paren, close_paren, quotes)
    """
    ob = cb = op = cp = quotes = 0
    in_str = False
    esc = False
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("@") or stripped.startswith("//"):
            continue
        for ch in line:
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                    quotes += 1
                continue
            if ch == '"':
                in_str = True
                quotes += 1
            elif ch == "{":
                ob += 1
            elif ch == "}":
                cb += 1
            elif ch == "(":
                op += 1
            elif ch == ")":
                cp += 1
    return ob, cb, op, cp, quotes, in_str


def count_quotes(text):
    """统计总 ASCII 双引号数 (仅用于比对被替换区段的奇偶性)"""
    return text.count('"')


def show_block(title, text, start_line):
    print("  -- %s (新文件行 %d 起) --" % (title, start_line))
    for i, line in enumerate(text.split("\n")):
        print("  %5d | %s" % (start_line + i, line))


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

def line_contrib(line):
    """单行 (不计状态) 的原始计数: ( { } ( ) 数 ) —— 仅用于诊断定位"""
    return (line.count("{"), line.count("}"), line.count("("), line.count(")"))


def is_skipped(line):
    s = line.lstrip()
    return s.startswith("@") or s.startswith("//")


def diag(old_text, new_text):
    """诊断: 用 SequenceMatcher 定位 平衡额差异 究竟来自哪几行"""
    old_lines, _ = split_lines(old_text)
    new_lines, _ = split_lines(new_text)
    sm = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    print("  [!] 差异区段逐行原始计数 ({}() 计数, 'S'=按规则被跳过):")
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        print("  >>> %s  old[%d:%d] -> new[%d:%d]" % (tag, i1 + 1, i2, j1 + 1, j2))
        o = [0, 0, 0, 0]
        n = [0, 0, 0, 0]
        for k in range(i1, i2):
            c = str(line_contrib(old_lines[k]))
            skipped = is_skipped(old_lines[k])
            if not skipped:
                o = [a + b for a, b in zip(o, line_contrib(old_lines[k]))]
            print("    -%5d %-18s %s %s" % (k + 1, c, "S" if skipped else " ", old_lines[k][:90]))
        for k in range(j1, j2):
            c = str(line_contrib(new_lines[k]))
            skipped = is_skipped(new_lines[k])
            if not skipped:
                n = [a + b for a, b in zip(n, line_contrib(new_lines[k]))]
            print("    +%5d %-18s %s %s" % (k + 1, c, "S" if skipped else " ", new_lines[k][:90]))
        print("      小计(未跳过): old {}=%d }=%d (=%d )=%d | new {}=%d }=%d (=%d )=%d"
              % (o[0], o[1], o[2], o[3], n[0], n[1], n[2], n[3]))
        print("      区段净增: { = %+d, } = %+d, ( = %+d, ) = %+d"
              % (n[0] - o[0], n[1] - o[1], n[2] - o[2], n[3] - o[3]))


def main():
    apply_mode = "--apply" in sys.argv[1:]
    diag_mode = "--diag" in sys.argv[1:]
    bad_args = [a for a in sys.argv[1:] if a not in ("--apply", "--diag")]
    if bad_args:
        print("[FAIL] 未知参数: %s" % " ".join(bad_args))
        return 2

    print("=" * 78)
    print("补丁脚本: _audit/_apply_dpi_v8_startup.py")
    print("模式: %s" % ("APPLY (写盘)" if apply_mode else "DRY-RUN (不写盘)"))
    print("目标: %s" % TARGET)
    print("=" * 78)

    # ---- 读文件 (二进制, 先验 BOM) ----
    if not os.path.isfile(TARGET):
        print("[FAIL] 目标文件不存在: %s" % TARGET)
        return 2
    with io.open(TARGET, "rb") as fh:
        raw = fh.read()
    print("\n[1] 文件事实")
    print("    bytes = %d" % len(raw))
    check(not raw.startswith(b"\xef\xbb\xbf"), "UTF-8 无 BOM (前 3 字节非 EF BB BF)")
    check(not raw.startswith(b"\xff\xfe"), "非 UTF-16LE (前 2 字节非 FF FE)")
    try:
        text = raw.decode("utf-8")
        decoded_ok = True
    except UnicodeDecodeError as exc:
        decoded_ok = False
        print("    解码错误: %r" % (exc,))
    if not check(decoded_ok, "可按 UTF-8 严格解码"):
        print("\n[ABORT] 编码不合法, 未做任何改动。")
        return 2
    cr_count = text.count("\r")
    lines_before, trailing_nl = split_lines(text)
    check(cr_count == 0, "纯 LF (CR 计数 = 0, 实测 %d)" % cr_count)
    check(trailing_nl, "文件以 LF 结尾")
    print("    行数(改前) = %d" % len(lines_before))

    # ---- 幂等哨兵 ----
    print("\n[2] 幂等检查 (以下串必须一个都不存在)")
    for s in SENTINELS:
        n = count_occurrences(text, s)
        check(n == 0, "哨兵不存在: %r (命中 %d)" % (s, n))
    if FAILURES:
        print("\n[ABORT] 补丁疑似已应用 (或字段名冲突), 未做任何改动。")
        return 2

    # ---- 锚点唯一性 ----
    print("\n[3] 锚点唯一性 (命中数必须 == 1)")
    check(count_occurrences(text, ANCHOR_INIT_EVT) == 1,
          "改动1/2 锚点: %r" % ANCHOR_INIT_EVT)
    check(count_occurrences(text, ANCHOR_INIT_CALL) == 1,
          "校验锚点: %r" % ANCHOR_INIT_CALL)
    check(count_occurrences(text, ANCHOR_MAIN_METHOD) == 1,
          "校验锚点: %r" % ANCHOR_MAIN_METHOD)
    check(count_occurrences(text, ANCHOR_C3_A) == 1,
          "改动3 锚点A (main.wsv:921-922, 2 行逐字)")
    check(count_occurrences(text, ANCHOR_C3_B) == 1,
          "改动3 锚点B (main.wsv:928, 1 行逐字)")
    if FAILURES:
        print("\n[ABORT] 锚点校验未通过, 未做任何改动。")
        return 2

    anchor_line = line_no_of(text, ANCHOR_INIT_EVT)[0]
    init_line_before = line_no_of(text, ANCHOR_INIT_CALL)[0]
    method_line = line_no_of(text, ANCHOR_MAIN_METHOD)[0]
    print("    锚点行号: 初始化事件声明 = %d, FBrowser_初始化 调用 = %d, 启动方法 = %d"
          % (anchor_line, init_line_before, method_line))
    check(anchor_line > method_line and anchor_line < init_line_before,
          "锚点位于 启动方法 体内 且 在 FBrowser_初始化 之前 (%d < %d < %d)"
          % (method_line, anchor_line, init_line_before))
    check(lines_before[anchor_line - 1].startswith(" " * 8)
          and not lines_before[anchor_line - 1].startswith(" " * 9),
          "锚点行缩进恰为 8 空格 (方法体一级)")

    # ---- 平衡基线 (改前) ----
    bal_before = balance(text)
    print("\n[4] 结构平衡基线 (跳过 @ 行 与 整行 // 注释)")
    print("    改前: { = %d, } = %d, ( = %d, ) = %d, 引号 = %d, 结束时仍在字符串内 = %s"
          % (bal_before[0], bal_before[1], bal_before[2], bal_before[3],
             bal_before[4], bal_before[5]))
    print("    改前净额: {} = %+d, () = %+d"
          % (bal_before[0] - bal_before[1], bal_before[2] - bal_before[3]))

    # 被替换区段的引号奇偶性 (必须在代码里, 否则字符串状态机会跨界错位)
    removed_text = ANCHOR_C3_A + "\n" + ANCHOR_C3_B
    added_text = REPLACE_C3_A + "\n" + REPLACE_C3_B
    q_removed = count_quotes(removed_text)
    q_added = count_quotes(added_text)
    print("    被替换区段引号: 移除 %d 个, 新增 %d 个 (奇偶性必须一致)" % (q_removed, q_added))
    check(q_removed % 2 == q_added % 2, "替换区段引号奇偶性一致 (1 个 ASCII 双引号也不得引入)")

    # ---- 生成新文本 ----
    new_text = text
    new_text = new_text.replace(ANCHOR_INIT_EVT, INSERT_TEXT + ANCHOR_INIT_EVT, 1)
    new_text = new_text.replace(ANCHOR_C3_A, REPLACE_C3_A, 1)
    new_text = new_text.replace(ANCHOR_C3_B, REPLACE_C3_B, 1)
    check(new_text != text, "新文本与原文不同 (确实产生了改动)")

    # ---- 幂等自证: 打过补丁的文本必须能被步骤[2]的哨兵拦下 ----
    print("\n[4b] 幂等自证 (对改后文本重跑本脚本必须被哨兵拦下)")
    for s in SENTINELS:
        check(count_occurrences(new_text, s) >= 1,
              "改后文本含哨兵 %r (命中 %d) -> 二次运行必被拦" % (s, count_occurrences(new_text, s)))

    lines_after, trailing_after = split_lines(new_text)
    line_delta = len(lines_after) - len(lines_before)

    # ---- 改动1/2 生效位置断言 ----
    print("\n[5] 改动1/2 必须在 FBrowser_初始化 之前 (否则不生效)")
    dpi_hits = line_no_of(new_text, "如果 (MCP命令服务器.启动DPI感知模式)")
    v8_hits = line_no_of(new_text, "如果 (MCP命令服务器.V8堆栈上限MB > 0)")
    check(len(dpi_hits) == 1, "改动1 的 如果 分支恰好 1 处 (行 %s)" % dpi_hits)
    check(len(v8_hits) == 1, "改动2 的 如果 分支恰好 1 处 (行 %s)" % v8_hits)
    init_line_after = line_no_of(new_text, ANCHOR_INIT_CALL)
    check(len(init_line_after) == 1, "FBrowser_初始化 调用仍恰好 1 处")
    if dpi_hits and v8_hits and len(init_line_after) == 1:
        init_ln = init_line_after[0]
        print("    行号: 改动1 = %d, 改动2 = %d, FBrowser_初始化 = %d" % (dpi_hits[0], v8_hits[0], init_ln))
        check(dpi_hits[0] < init_ln, "改动1 插入行 %d < FBrowser_初始化 行 %d" % (dpi_hits[0], init_ln))
        check(v8_hits[0] < init_ln, "改动2 插入行 %d < FBrowser_初始化 行 %d" % (v8_hits[0], init_ln))
        check(v8_hits[0] > dpi_hits[0], "改动2 排在改动1 之后 (顺序稳定)")

    # ---- 平衡校验 (改后) ----
    print("\n[6] 结构平衡校验 (字符串字面量之外的 {}/() 净额前后必须相同)")
    bal_after = balance(new_text)
    print("    改后: { = %d, } = %d, ( = %d, ) = %d, 引号 = %d, 结束时仍在字符串内 = %s"
          % (bal_after[0], bal_after[1], bal_after[2], bal_after[3],
             bal_after[4], bal_after[5]))
    d_ob = bal_after[0] - bal_before[0]
    d_cb = bal_after[1] - bal_before[1]
    d_op = bal_after[2] - bal_before[2]
    d_cp = bal_after[3] - bal_before[3]
    print("    增量: { %+d, } %+d, ( %+d, ) %+d, 引号 %+d"
          % (d_ob, d_cb, d_op, d_cp, bal_after[4] - bal_before[4]))
    print("    净额: {} 改前 %+d -> 改后 %+d | () 改前 %+d -> 改后 %+d"
          % (bal_before[0] - bal_before[1], bal_after[0] - bal_after[1],
             bal_before[2] - bal_before[3], bal_after[2] - bal_after[3]))
    check(bal_after[0] - bal_after[1] == bal_before[0] - bal_before[1],
          "花括号净额完全相同 (%+d == %+d)"
          % (bal_before[0] - bal_before[1], bal_after[0] - bal_after[1]))
    check(bal_after[2] - bal_after[3] == bal_before[2] - bal_before[3],
          "圆括号净额完全相同 (%+d == %+d)"
          % (bal_before[2] - bal_before[3], bal_after[2] - bal_after[3]))
    check(d_ob == d_cb, "新增的 { 与 } 个数相等 (%+d == %+d, 成对闭合)" % (d_ob, d_cb))
    check(d_op == d_cp, "新增的 ( 与 ) 个数相等 (%+d == %+d)" % (d_op, d_cp))
    check(bal_after[4] == bal_before[4], "ASCII 双引号总数不变 (%d == %d) —— 未新增/删除任何字符串字面量"
          % (bal_before[4], bal_after[4]))
    check(bal_after[5] == bal_before[5], "字符串状态机收尾状态一致 (改前 %s / 改后 %s)"
          % (bal_before[5], bal_after[5]))
    if diag_mode and (bal_after[0] - bal_after[1] != bal_before[0] - bal_before[1]
                      or bal_after[2] - bal_after[3] != bal_before[2] - bal_before[3]):
        print("\n  ---- 诊断 (--diag) ----")
        diag(text, new_text)
        print("  ---- 诊断结束 ----")

    # ---- 行数变化 ----
    print("\n[7] 行数变化")
    expected_delta = (
        INSERT_TEXT.count("\n")
        + (REPLACE_C3_A.count("\n") - ANCHOR_C3_A.count("\n"))
        + (REPLACE_C3_B.count("\n") - ANCHOR_C3_B.count("\n"))
    )
    print("    改前 %d 行 -> 改后 %d 行, 净增 %+d 行 (预期 %+d)"
          % (len(lines_before), len(lines_after), line_delta, expected_delta))
    check(len(lines_after) == len(lines_before) + expected_delta,
          "行数增量 == 预期 %+d 行 (改动1/2 插入 %d 行, 改动3 净 %+d 行)"
          % (expected_delta, INSERT_TEXT.count("\n"),
             expected_delta - INSERT_TEXT.count("\n")))

    # ---- 预览 ----
    print("\n[8] 改动预览")
    ins_line = line_no_of(new_text, "如果 (MCP命令服务器.启动DPI感知模式)")[0] - 9
    show_block("改动1/2 插入段", INSERT_TEXT.rstrip("\n"), ins_line)
    c3a_line = line_no_of(new_text, "    # 背景: 本项目为此把事件类接到")[0]
    show_block("改动3 替换段A", REPLACE_C3_A, c3a_line)
    c3b_line = line_no_of(new_text, "    # 故此处把本项目的事件类装上(类_MCP_浏览器事件)")[0]
    show_block("改动3 替换段B", REPLACE_C3_B, c3b_line)

    # ---- 结论 ----
    print("\n" + "=" * 78)
    if FAILURES:
        print("[ABORT] %d 项断言未通过, 未写盘:" % len(FAILURES))
        for m in FAILURES:
            print("   - %s" % m)
        print("=" * 78)
        return 1

    if not apply_mode:
        print("[DRY-RUN] 全部断言通过。未写盘 (未传 --apply)。")
        print("[DRY-RUN] 写盘将使用 io.open(..., 'w', encoding='utf-8', newline='\\n')。")
        print("=" * 78)
        return 0

    # ---- 写盘 ----
    print("[APPLY] 写入 %s ..." % TARGET)
    with io.open(TARGET, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new_text)
    with io.open(TARGET, "rb") as fh:
        raw2 = fh.read()
    text2 = raw2.decode("utf-8")
    post_ok = []
    post_ok.append(check(not raw2.startswith(b"\xef\xbb\xbf"), "落盘后仍无 BOM"))
    post_ok.append(check(text2.count("\r") == 0, "落盘后仍纯 LF"))
    post_ok.append(check(text2 == new_text, "落盘内容与内存文本逐字节一致"))
    post_ok.append(check(balance(text2)[0] - balance(text2)[1]
                         == bal_before[0] - bal_before[1]
                         and balance(text2)[2] - balance(text2)[3]
                         == bal_before[2] - bal_before[3],
                         "落盘后 {}/() 净额仍与改前一致"))
    print("[APPLY] bytes = %d, 行数 = %d" % (len(raw2), len(split_lines(text2)[0])))
    print("[APPLY] 结果: %s" % ("成功" if all(post_ok) else "失败(见上)"))
    print("=" * 78)
    return 0 if all(post_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
