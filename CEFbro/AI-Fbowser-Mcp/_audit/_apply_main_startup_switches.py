# -*- coding: utf-8 -*-
"""
补丁脚本: 给 src/main.wsv 的 启动类.即将处理命令行 补上 3 类启动期开关 + 命令行对象可用性回执。

只改 src/main.wsv, 不动任何其它文件。
默认 dry-run: 只打印 文件/锚点/旧文本/新文本/行数变化, 绝不写盘。
加 --apply 才写盘 (本脚本由上层代理决定是否执行)。

写入前全部断言, 任一不过 -> 报错退出 (exit 2), 不写盘:
  1. UTF-8 无 BOM
  2. 纯 LF (无 \r)
  3. 锚点命中数 == 1
  4. 字符串字面量之外的 { } 净额, ( ) 净额 前后相同 (跳过 @ 开头嵌入式 C++ 行 与 整行 // 注释)
  5. 插入点位于 `如果 (进程类型 == "")` 之内: 如果行号 < 插入行号 < 该块内 `启动开关命令行 = 命令行.取字符串 ()` 行号
  6. 幂等: 文件里尚不存在 enable_cross_frame; 与 置项值 (
  7. 行数变化 == 预期

依据 (只读查证, 未改):
  - src/main.wsv:480-535   方法 即将处理命令行 / 变量 启动开关清单 / 如果 (进程类型 == "") 门控块
  - src/MCP_Server.wsv:400-405  命令行开关已应用 / 命令行开关原文 / 启动开关_启用跨框架操作模式 /
                                启动开关_禁用代理 / 启动开关_名值表 / 启动开关_被拒表
  - 类库 类_FBrowser_命令行 (FBroLib.wsv:1758 是否为空() -> 逻辑型,
    :1835 置项值(项目名<文本型>, 项目值<文本型>), :1888 启用跨框架操作模式(), :1968 禁用代理())
  - 视窗基本类 w_string_p.wsv:381 取文本长度 / :408 取文本中间 (起始索引从 0 开始) / :880 寻找文本 (未找到返回 -1)
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARGET = os.path.join(ROOT, "src", "main.wsv")
MCP_SERVER = os.path.join(ROOT, "src", "MCP_Server.wsv")

# ---------------------------------------------------------------------------
# 锚点原文 (逐字抄自 src/main.wsv:499-501 与 :526-532)
# ---------------------------------------------------------------------------
ANCHOR_A_OLD = "\n".join([
    '        如果 (进程类型 == "")',
    "        {",
    "            如果 (MCP命令服务器.启动开关_启用摄像头)",
])

ANCHOR_B_OLD = "\n".join([
    "            如果 (MCP命令服务器.启动开关_忽略GPU禁用清单)",
    "            {",
    "                命令行.忽略GPU禁用清单 ()",
    '                启动开关清单 = 启动开关清单 + "ignore_gpu_blocklist;"',
    "            }",
    "            启动开关命令行 = 命令行.取字符串 ()",
    "        }",
])

# ---------------------------------------------------------------------------
# 插入内容
# ---------------------------------------------------------------------------
INS_A = "\n".join([
    '        如果 (进程类型 == "")',
    "        {",
    "            // 启动期回执: 命令行对象是否可用; 为假时 applied_switches 恒为空, 无法区分“没配开关”与“命令行不可用”",
    "            变量 命令行可用 <类型 = 逻辑型>",
    "            命令行可用 = (命令行.是否为空 () == 假)",
    "            如果 (MCP命令服务器.启动开关_启用摄像头)",
])

INS_B = "\n".join([
    "            如果 (MCP命令服务器.启动开关_忽略GPU禁用清单)",
    "            {",
    "                命令行.忽略GPU禁用清单 ()",
    '                启动开关清单 = 启动开关清单 + "ignore_gpu_blocklist;"',
    "            }",
    "            // ==== 启动期开关通道v2 追加①: 跨框架操作模式 (mcp_config.json enable_cross_frame) ====",
    "            如果 (MCP命令服务器.启动开关_启用跨框架操作模式)",
    "            {",
    "                命令行.启用跨框架操作模式 ()",
    '                启动开关清单 = 启动开关清单 + "enable_cross_frame;"',
    "            }",
    "            // ==== 启动期开关通道v2 追加②: 禁用代理 (mcp_config.json disable_proxy) ====",
    "            如果 (MCP命令服务器.启动开关_禁用代理)",
    "            {",
    "                命令行.禁用代理 ()",
    '                启动开关清单 = 启动开关清单 + "disable_proxy;"',
    "            }",
    "            // ==== 启动期开关通道v2 追加③: 名值白名单表逐项施加 (名=值;名=值;) ====",
    "            // 拆分不使用正则库: 按分号切段, 每段按第一个等号切名/值;",
    "            //   值里允许连字符与逗号 (例如 AutomationControlled,SomeFeature), 不按逗号或连字符再切。",
    "            // 段为空跳过; 无等号 / 名为空 / 值为空 的段原样追加进 被拒表, 如实回执不静默丢弃。",
    "            变量 名值表原文 <类型 = 文本型>",
    "            名值表原文 = MCP命令服务器.启动开关_名值表",
    "            变量 名值表长度 <类型 = 整数>",
    "            名值表长度 = 取文本长度 (名值表原文)",
    "            变量 名值段起 <类型 = 整数>",
    "            名值段起 = 0",
    "            判断循环 (名值段起 < 名值表长度)",
    "            {",
    "                变量 名值分隔 <类型 = 整数>",
    '                名值分隔 = 寻找文本 (名值表原文, ";", 名值段起, 假)',
    "                如果 (名值分隔 == -1)",
    "                {",
    "                    名值分隔 = 名值表长度",
    "                }",
    "                变量 名值一段 <类型 = 文本型>",
    "                名值一段 = 取文本中间 (名值表原文, 名值段起, 名值分隔 - 名值段起)",
    "                名值段起 = 名值分隔 + 1",
    '                如果 (名值一段 != "")',
    "                {",
    "                    变量 名值等号 <类型 = 整数>",
    '                    名值等号 = 寻找文本 (名值一段, "=", 0, 假)',
    "                    如果 (名值等号 <= 0)",
    "                    {",
    "                        MCP命令服务器.启动开关_被拒表 = MCP命令服务器.启动开关_被拒表 + 名值一段 + \";\"",
    "                    }",
    "                    否则",
    "                    {",
    "                        变量 名值名 <类型 = 文本型>",
    "                        名值名 = 取文本中间 (名值一段, 0, 名值等号)",
    "                        变量 名值值 <类型 = 文本型>",
    "                        名值值 = 取文本中间 (名值一段, 名值等号 + 1, 取文本长度 (名值一段) - 名值等号 - 1)",
    '                        如果 (名值名 == "" || 名值值 == "")',
    "                        {",
    "                            MCP命令服务器.启动开关_被拒表 = MCP命令服务器.启动开关_被拒表 + 名值一段 + \";\"",
    "                        }",
    "                        否则",
    "                        {",
    "                            // 约束(类库原文): AppendSwitchWithValue 的 name \"默认前面要加 --\"。",
    "                            // 配置里写的是裸名(lang), 必须在此补前缀; 否则内核拿到非 -- 开头的项会静默忽略。",
    "                            变量 名值开关 <类型 = 文本型>",
    "                            如果 (MCP命令服务器.是否以 (名值名, \"--\"))",
    "                            {",
    "                                名值开关 = 名值名",
    "                            }",
    "                            否则",
    "                            {",
    "                                名值开关 = \"--\" + 名值名",
    "                            }",
    "                            命令行.置项值 (名值开关, 名值值)",
    '                            启动开关清单 = 启动开关清单 + 名值名 + ";"',
    "                        }",
    "                    }",
    "                }",
    "            }",
    "            启动开关命令行 = 命令行.取字符串 ()",
    "            MCP命令服务器.命令行对象可用 = 命令行可用",
    "        }",
])

# ---------------------------------------------------------------------------
# 新文本里用于定位断言的整行标记
# ---------------------------------------------------------------------------
MARK_GATE_IF = '        如果 (进程类型 == "")'
MARK_DECL_AVAIL = "            变量 命令行可用 <类型 = 逻辑型>"
MARK_CROSS = '                启动开关清单 = 启动开关清单 + "enable_cross_frame;"'
MARK_PROXY = '                启动开关清单 = 启动开关清单 + "disable_proxy;"'
MARK_NV = '                    名值等号 = 寻找文本 (名值一段, "=", 0, 假)'
MARK_TAKE_STR = "            启动开关命令行 = 命令行.取字符串 ()"
MARK_FIELD_AVAIL = "            MCP命令服务器.命令行对象可用 = 命令行可用"
MARK_GATE_CLOSE = "        }"

FORBID_ALREADY = ["enable_cross_frame;", "置项值 (", "命令行对象可用"]


def fail(msg):
    sys.stderr.write("\n[断言失败] " + msg + "\n")
    sys.stderr.write("未写盘, 已中止。\n")
    raise SystemExit(2)


def count_hits(text, needle):
    return text.count(needle)


def net_balance(text):
    """统计字符串字面量之外的 { } 与 ( ) 净额; 跳过 @ 开头行与整行 // 注释。"""
    brace = 0
    paren = 0
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("@"):
            continue
        if s.startswith("//"):
            continue
        in_str = False
        esc = False
        for ch in line:
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                brace += 1
            elif ch == "}":
                brace -= 1
            elif ch == "(":
                paren += 1
            elif ch == ")":
                paren -= 1
    return brace, paren


def line_index(lines, exact):
    hits = [i for i, ln in enumerate(lines) if ln == exact]
    if len(hits) != 1:
        fail("定位标记命中数 != 1 (命中 %d 次): %r" % (len(hits), exact))
    return hits[0]


def main():
    apply_mode = False
    for arg in sys.argv[1:]:
        if arg == "--apply":
            apply_mode = True
        else:
            fail("未知参数: %r (只支持 --apply)" % arg)

    if not os.path.isfile(TARGET):
        fail("目标文件不存在: " + TARGET)

    raw = open(TARGET, "rb").read()

    # --- 断言 1: 无 BOM ---
    if raw.startswith(b"\xef\xbb\xbf"):
        fail("文件带 UTF-8 BOM (应为无 BOM): " + TARGET)
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        fail("文件是 UTF-16LE/BE, 与本补丁的 UTF-8 假设不符: " + TARGET)

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        fail("文件不是合法 UTF-8: %s" % e)

    # --- 断言 2: 纯 LF ---
    if "\r" in text:
        fail("文件含 CR (非纯 LF), 共 %d 处" % text.count("\r"))
    if not text.endswith("\n"):
        fail("文件未以换行符结尾")

    old_lines = text.split("\n")[:-1]
    old_count = len(old_lines)

    # --- 断言 6: 幂等 ---
    for token in FORBID_ALREADY:
        if token in text:
            fail("疑似已应用过本补丁 (文件里已存在 %r), 拒绝重复施加" % token)

    # --- 断言 3: 锚点唯一 ---
    n_a = count_hits(text, ANCHOR_A_OLD)
    n_b = count_hits(text, ANCHOR_B_OLD)
    if n_a != 1:
        fail("锚点A 命中数 = %d (要求 1)" % n_a)
    if n_b != 1:
        fail("锚点B 命中数 = %d (要求 1)" % n_b)
    if text.count(MARK_GATE_IF) != 1:
        fail("`如果 (进程类型 == \"\")` 非唯一 (命中 %d 次)" % text.count(MARK_GATE_IF))
    if text.count(MARK_TAKE_STR) != 1:
        fail("`启动开关命令行 = 命令行.取字符串 ()` 非唯一 (命中 %d 次)" % text.count(MARK_TAKE_STR))

    # 锚点 A 必须命中 `如果 (进程类型 == "")` 那一行
    idx_a = text.index(ANCHOR_A_OLD)
    if text[:idx_a].count("\n") + 1 != old_lines.index(MARK_GATE_IF) + 1:
        fail("锚点A 起点不是 `如果 (进程类型 == \"\")` 行")

    # --- 断言 4 (前): 净额 ---
    bal_before = net_balance(text)

    new_text = text.replace(ANCHOR_A_OLD, INS_A, 1).replace(ANCHOR_B_OLD, INS_B, 1)
    if new_text == text:
        fail("替换后文本与原文本相同 (替换未生效)")

    # 替换后原锚点片段应消失, 且新标记唯一
    if ANCHOR_A_OLD in new_text or ANCHOR_B_OLD in new_text:
        fail("替换后旧锚点仍存在")
    for m in (MARK_DECL_AVAIL, MARK_CROSS, MARK_PROXY, MARK_NV, MARK_FIELD_AVAIL):
        if new_text.count(m) != 1:
            fail("新标记命中数 != 1 (命中 %d 次): %r" % (new_text.count(m), m))

    # --- 断言 4 (后): 净额相同 ---
    bal_after = net_balance(new_text)
    if bal_before != bal_after:
        fail("配对净额变化: {}/} %d -> %d , (/ ) %d -> %d"
             % (bal_before[0], bal_after[0], bal_before[1], bal_after[1]))

    # --- 断言 7: 行数变化 ---
    new_lines = new_text.split("\n")[:-1]
    new_count = len(new_lines)
    added_a = len(INS_A.split("\n")) - len(ANCHOR_A_OLD.split("\n"))
    added_b = len(INS_B.split("\n")) - len(ANCHOR_B_OLD.split("\n"))
    expected_delta = added_a + added_b
    actual_delta = new_count - old_count
    if actual_delta != expected_delta:
        fail("行数变化 = %d, 预期 %d" % (actual_delta, expected_delta))

    if "\r" in new_text:
        fail("生成文本含 CR")
    if not new_text.endswith("\n"):
        fail("生成文本未以换行符结尾")

    # --- 断言 5: 插入点都落在 如果 (进程类型 == "") 门控块内部, 且在 取字符串 之前 ---
    i_gate = line_index(new_lines, MARK_GATE_IF)
    i_take = line_index(new_lines, MARK_TAKE_STR)
    i_decl = line_index(new_lines, MARK_DECL_AVAIL)
    i_cross = line_index(new_lines, MARK_CROSS)
    i_proxy = line_index(new_lines, MARK_PROXY)
    i_nv = line_index(new_lines, MARK_NV)
    i_field = line_index(new_lines, MARK_FIELD_AVAIL)

    if not (i_gate < i_decl):
        fail("命令行可用探测不在门控块内 (%d !< %d)" % (i_gate, i_decl))
    for name, i in (("enable_cross_frame", i_cross), ("disable_proxy", i_proxy),
                    ("名值表逐项施加", i_nv)):
        if not (i_gate < i < i_take):
            fail("%s 插入点不在 (如果行 %d, 取字符串行 %d) 之间: 实际 %d"
                 % (name, i_gate, i_take, i))
    if not (i_take < i_field):
        fail("命令行对象可用 回执未写在 取字符串 之后 (块尾): %d !< %d" % (i_take, i_field))
    if new_lines[i_take + 1] != MARK_FIELD_AVAIL:
        fail("命令行对象可用 回执未紧跟 取字符串 行")
    if new_lines[i_take + 2] != MARK_GATE_CLOSE:
        fail("门控块闭合括号不在 取字符串 行后第 3 行 (回执可能被写在块外)")

    # --- 附加只读检查: 主代理应已添加 命令行对象可用 字段 ---
    warn_field = ""
    if os.path.isfile(MCP_SERVER):
        mcp_raw = open(MCP_SERVER, "rb").read().decode("utf-8", "replace")
        if "命令行对象可用" not in mcp_raw:
            warn_field = ("src/MCP_Server.wsv 里尚未找到字段 `命令行对象可用` —— "
                          "本补丁会写入 MCP命令服务器.命令行对象可用, 该字段缺失将导致编译报错。")

    # ------------------------------------------------------------------
    # 输出
    # ------------------------------------------------------------------
    out = sys.stdout
    out.write("=" * 78 + "\n")
    out.write("文件: %s\n" % TARGET)
    out.write("模式: %s\n" % ("APPLY (会写盘)" if apply_mode else "DRY-RUN (只打印, 不写盘)"))
    out.write("=" * 78 + "\n")
    out.write("编码检查: UTF-8 无 BOM = 通过 ; 纯 LF (无 CR) = 通过\n")
    out.write("幂等检查: 文中不存在 %s = 通过\n" % " / ".join(repr(t) for t in FORBID_ALREADY))
    out.write("锚点A 命中数 = %d (要求 1) = 通过 | 锚点B 命中数 = %d (要求 1) = 通过\n" % (n_a, n_b))
    out.write("配对净额: {/} 前 %d -> 后 %d ; (/ ) 前 %d -> 后 %d = 相同, 通过\n"
              % (bal_before[0], bal_after[0], bal_before[1], bal_after[1]))
    out.write("\n")

    out.write("---- 锚点A (原 src/main.wsv:499-501) 旧文本 ----\n")
    out.write(ANCHOR_A_OLD + "\n")
    out.write("---- 锚点A 新文本 ----\n")
    out.write(INS_A + "\n\n")

    out.write("---- 锚点B (原 src/main.wsv:526-532) 旧文本 ----\n")
    out.write(ANCHOR_B_OLD + "\n")
    out.write("---- 锚点B 新文本 ----\n")
    out.write(INS_B + "\n\n")

    out.write("行数变化: %d -> %d (delta = +%d ; 锚点A +%d, 锚点B +%d) = 符合预期\n"
              % (old_count, new_count, actual_delta, added_a, added_b))
    out.write("\n")

    out.write("插入点定位断言 (1 基行号, 新文本):\n")
    out.write("  如果 (进程类型 == \"\")                     行 %d\n" % (i_gate + 1))
    out.write("  变量 命令行可用 <类型 = 逻辑型>                行 %d   [门控块入口]\n" % (i_decl + 1))
    out.write("  enable_cross_frame 追加                      行 %d\n" % (i_cross + 1))
    out.write("  disable_proxy 追加                           行 %d\n" % (i_proxy + 1))
    out.write("  名值表逐项施加                                行 %d\n" % (i_nv + 1))
    out.write("  启动开关命令行 = 命令行.取字符串 ()            行 %d\n" % (i_take + 1))
    out.write("  MCP命令服务器.命令行对象可用 = 命令行可用       行 %d   [块尾]\n" % (i_field + 1))
    out.write("  门控块闭合 }                                  行 %d\n" % (i_take + 3))
    out.write("  -> 全部满足 如果行号 < 插入行号 < 取字符串行号, 且回执在门控块内 = 通过\n")

    if warn_field:
        out.write("\n[警告] %s\n" % warn_field)

    out.write("\n")

    if not apply_mode:
        out.write("DRY-RUN 结束: 未写盘。加 --apply 才会写入 (带 newline='\\n', encoding='utf-8', 无 BOM)。\n")
        return

    with io.open(TARGET, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)
    check = open(TARGET, "rb").read()
    if check.startswith(b"\xef\xbb\xbf") or b"\r" in check:
        fail("写盘后复检失败 (BOM 或 CR 出现)")
    out.write("已写盘: %s\n" % TARGET)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    main()
