# -*- coding: utf-8 -*-
"""G6 + G7 指纹补丁脚本 —— 默认 dry-run, 只有显式 --apply 才写盘。

G6: browser_vip_fingerprint_media_devices 的 devices 设备清单**从未传给内核**(假成功)
    · src/MCP_Server_VIP.wsv   分派块改写: 读 devices -> 构造 FBrowser_媒体硬件数组 -> 作为第 2 参传入
    · src/MCP_Server.wsv       Schema: 增 devices 参数 + required 加 type + 描述改写

G7: browser_fingerprint 缺少 action=clear_count(类库 指纹_清空调用计数 在 src 零引用)
    · src/MCP_Server_Core.wsv  新增 clear_count 分支 + 未知action 提示补 clear_count
    · src/MCP_Server.wsv       Schema: action 清单/描述补 clear_count, 并修正 count 的说明

安全约束(全部为硬断言, 任一不满足立即报错退出, 绝不"尽量替换"):
  1. 用"整块唯一锚点文本"定位(逐行精确匹配, 不看行号), 全文件命中数必须恰好 == 1
  2. 字符串字面量之外的 { } 净额必须不变, ( ) 净额必须不变
     (跳过 @ 开头的嵌入式 C++ 行; // 与 # 开头的整行注释跳过; 行尾 // 注释也剔除)
  3. 每处替换的行数变化必须等于声明的期望值; 全文件括号净额前后必须相等
  4. 写盘必须 UTF-8 无 BOM + LF

用法:
    py -3 _audit/_apply_g6g7_fingerprint.py            # dry-run, 只打印
    py -3 _audit/_apply_g6g7_fingerprint.py --apply    # 真实写盘
"""

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = "--apply" in sys.argv


# ---------------------------------------------------------------- 括号/行统计

def code_only(text):
    """去掉字符串字面量与注释后的代码文本(用于括号净额统计)。"""
    out_lines = []
    for line in text.split("\n"):
        s = line.strip()
        # 嵌入式 C++ 行 / 整行注释 / 类库指令行 —— 整行跳过, 免误计括号
        if s.startswith("@") or s.startswith("//") or s.startswith("#") or s.startswith("\\\\"):
            out_lines.append("")
            continue
        buf = []
        i = 0
        n = len(line)
        while i < n:
            c = line[i]
            if c == '"':
                # 字符串字面量: 整段丢弃, 处理 \" 转义
                i += 1
                while i < n:
                    if line[i] == "\\":
                        i += 2
                        continue
                    if line[i] == '"':
                        i += 1
                        break
                    i += 1
                continue
            if c == "/" and i + 1 < n and line[i + 1] == "/":
                break  # 行尾注释
            buf.append(c)
            i += 1
        out_lines.append("".join(buf))
    return "\n".join(out_lines)


def balance(text):
    """返回 (花括号净额, 圆括号净额)。"""
    code = code_only(text)
    return (code.count("{") - code.count("}"), code.count("(") - code.count(")"))


def nlines(text):
    return len(text.split("\n"))


# ---------------------------------------------------------------- G6: 分派块

G6_DISPATCH_OLD = """        否则 (方法名 == "browser_vip_fingerprint_media_devices")
        {
            变量 vipMD <类型 = 类_FBrowserVIP_控制器>
            vipMD = MCP命令服务器.取VIP控制器 ()
            如果 (vipMD.是否为空 () == 假)
            {
                变量 medTarget <类型 = 文本型>
                medTarget = MCP命令服务器.yyjson取文本 (参数JSON, "target")
                如果 (medTarget == "audio_input")
                {
                    vipMD.指纹_虚拟AudioInput设备 (MCP命令服务器.yyjson取整数 (参数JSON, "type"))
                }
                否则 (medTarget == "audio_output")
                {
                    vipMD.指纹_虚拟AudioOutput设备 (MCP命令服务器.yyjson取整数 (参数JSON, "type"))
                }
                否则 (medTarget == "video_input")
                {
                    vipMD.指纹_虚拟VideoInput设备 (MCP命令服务器.yyjson取整数 (参数JSON, "type"))
                }
                否则
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "未知target: " + medTarget + " | 支持 audio_input/audio_output/video_input"))
                }
                返回 (MCP_响应构建.响应_需要刷新 (命令ID, "媒体设备指纹已设置"))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_VIP不可用))
        }"""

G6_DISPATCH_NEW = """        否则 (方法名 == "browser_vip_fingerprint_media_devices")
        {
            变量 vipMD <类型 = 类_FBrowserVIP_控制器>
            vipMD = MCP命令服务器.取VIP控制器 ()
            如果 (vipMD.是否为空 () == 假)
            {
                如果 (MCP命令服务器.参数键存在 (参数JSON, "type") == 假)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "缺少参数 type | 0=清空(不需要 devices), 1=添加设备(需 devices), 2=覆盖设备(需 devices) | type 无默认值: 省略即报错, 以免静默清空已设设备"))
                }
                变量 medType <类型 = 整数>
                medType = MCP命令服务器.yyjson取整数 (参数JSON, "type")
                如果 (medType < 0 || medType > 2)
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "参数 type 无效(" + 到文本 (medType) + ") | 只支持 0清空/1添加/2覆盖"))
                }
                变量 medTarget <类型 = 文本型>
                medTarget = MCP命令服务器.yyjson取文本 (参数JSON, "target")
                如果 (medTarget != "audio_input" && medTarget != "audio_output" && medTarget != "video_input")
                {
                    返回 (MCP_响应构建.命令失败 (命令ID, "未知target: " + medTarget + " | 支持 audio_input/audio_output/video_input"))
                }
                变量 medDevices <类型 = FBrowser_媒体硬件数组>
                变量 medCount <类型 = 整数>
                medCount = 0
                如果 (medType != 0)
                {
                    变量 medDevicesText <类型 = 文本型>
                    medDevicesText = MCP命令服务器.yyjson取JSON文本 (参数JSON, "devices")
                    变量 medArr <类型 = YYJSON只读数组类>
                    medArr = MCP命令服务器.取JSON数组自文本 (medDevicesText, "devices")
                    如果 (medArr.是否为空对象 () || medArr.取成员数 () == 0)
                    {
                        返回 (MCP_响应构建.命令失败 (命令ID, "type=" + 到文本 (medType) + " 必须同时给 devices 设备清单(非空JSON数组) | 只传 type 时内核收到的清单为空, 设置不会产生任何效果(旧版在这里返回假成功) | 每项字段: device_id(驱动ID, 驱动属性里查到的硬件ID; 特殊值 default/communications), label(硬件名, 可选), group_id(分组ID, 可选)"))
                    }
                    计次循环 ((整数)medArr.取成员数 ())
                    {
                        变量 medItem <类型 = YYJSON只读对象类>
                        medItem = medArr.取成员 (取循环索引 ())
                        变量 medDeviceID <类型 = 文本型>
                        medDeviceID = MCP命令服务器.yyjson取文本 (medItem, "device_id")
                        如果 (medDeviceID == "")
                        {
                            medDeviceID = MCP命令服务器.yyjson取文本 (medItem, "driver_id")
                        }
                        如果 (medDeviceID == "")
                        {
                            medDeviceID = MCP命令服务器.yyjson取文本 (medItem, "id")
                        }
                        如果 (medDeviceID == "")
                        {
                            返回 (MCP_响应构建.命令失败 (命令ID, "devices[" + 到文本 (取循环索引 ()) + "] 缺少 device_id(驱动ID) | 类库按 驱动ID/硬件名/分组ID 三元组描述设备, 驱动ID 不能为空(别名 driver_id / id 亦可)"))
                        }
                        变量 medDeviceLabel <类型 = 文本型>
                        medDeviceLabel = MCP命令服务器.yyjson取文本 (medItem, "label")
                        如果 (medDeviceLabel == "")
                        {
                            medDeviceLabel = MCP命令服务器.yyjson取文本 (medItem, "name")
                        }
                        变量 medDeviceGroup <类型 = 文本型>
                        medDeviceGroup = MCP命令服务器.yyjson取文本 (medItem, "group_id")
                        如果 (medDeviceGroup == "")
                        {
                            medDeviceGroup = MCP命令服务器.yyjson取文本 (medItem, "group")
                        }
                        medDevices.加入数据 (medDeviceID, medDeviceLabel, medDeviceGroup)
                        medCount = medCount + 1
                    }
                }
                如果 (medTarget == "audio_input")
                {
                    vipMD.指纹_虚拟AudioInput设备 (medType, medDevices)
                }
                否则 (medTarget == "audio_output")
                {
                    vipMD.指纹_虚拟AudioOutput设备 (medType, medDevices)
                }
                否则
                {
                    vipMD.指纹_虚拟VideoInput设备 (medType, medDevices)
                }
                如果 (medType == 0)
                {
                    返回 (MCP_响应构建.响应_需要刷新 (命令ID, "媒体设备指纹已清空: target=" + medTarget + " | 类库原文警告: 虚拟媒体设备可能造成浏览器声音或麦克风异常, 无法获取真实设备"))
                }
                返回 (MCP_响应构建.响应_需要刷新 (命令ID, "媒体设备指纹已设置: target=" + medTarget + ", type=" + 到文本 (medType) + ", 设备数=" + 到文本 (medCount) + " | 类库原文警告: 虚拟媒体设备可能造成浏览器声音或麦克风异常, 无法获取真实设备"))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, MCP_常量.错误_VIP不可用))
        }"""


# ---------------------------------------------------------------- G7: 分派分支

G7_BRANCH_OLD = """                    否则 (action == "count")
                    {
                        返回 (MCP_响应构建.构建简单JSON ("count", vip_ctrl.指纹_取调用计数 ()))
                    }"""

G7_BRANCH_NEW = """                    否则 (action == "count")
                    {
                        返回 (MCP_响应构建.构建简单JSON ("count", vip_ctrl.指纹_取调用计数 ()))
                    }
                    否则 (action == "clear_count")
                    {
                        vip_ctrl.指纹_清空调用计数 ()
                        变量 清计数回执 <类型 = YYJSON对象类>
                        清计数回执.创建自文本 ("{}")
                        清计数回执.加入逻辑值成员 ("success", 真)
                        清计数回执.加入逻辑值成员 ("cleared", 真)
                        清计数回执.加入文本成员 ("count", vip_ctrl.指纹_取调用计数 ())
                        返回 (清计数回执.到可读文本 (YYJSON格式化选项.压缩))
                    }"""


G7_UNKNOWN_OLD = """                    返回 (MCP_响应构建.命令失败 (命令ID, "未知action: " + action + " | 支持: clear/count/canvas_random/webgl_random/audio_random/audio_param/webrtc/geolocation/timezone/ssl/set_batch"))"""

G7_UNKNOWN_NEW = """                    返回 (MCP_响应构建.命令失败 (命令ID, "未知action: " + action + " | 支持: clear/count/clear_count/canvas_random/webgl_random/audio_random/audio_param/webrtc/geolocation/timezone/ssl/set_batch"))"""


# ---------------------------------------------------------------- G6/G7: Schema

G6_SCHEMA_OLD = """        添加工具JSON ("browser_vip_fingerprint_media_devices", "VIP: 虚拟媒体设备指纹。target选择设备类别(audio_input/audio_output/video_input), type控制动作(0清空/1添加/2覆盖); 设置后需刷新页面生效", 多属性Schema文本 (属性项JSON ("type", "integer", "0清空/1添加/2覆盖") + "," + 属性项JSON ("target", "text", "audio_input/audio_output/video_input"), "\\"target\\""))"""

G6_SCHEMA_NEW = """        添加工具JSON ("browser_vip_fingerprint_media_devices", "VIP: 虚拟媒体设备指纹(麦克风/扬声器/摄像头清单)。target选择设备类别(audio_input/audio_output/video_input), type控制动作(0清空/1添加/2覆盖); type 无默认值必须显式给(省略即报错, 以免静默清空已设设备); type=1或2 必须同时给 devices 设备清单(JSON数组), 否则如实报错 | 只传 type 时内核收到的清单为空, 设置不会产生任何效果(旧版在这里返回假成功); devices 每项 device_id 是驱动ID(驱动属性里查到的硬件ID, 特殊值 default/communications), 另可给 label(硬件名) 与 group_id(分组ID); 类库原文警告: 虚拟媒体设备可能造成浏览器声音或麦克风异常, 无法获取到真实设备; 设置后需刷新页面生效", 多属性Schema文本 (属性项JSON ("target", "text", "audio_input/audio_output/video_input") + "," + 属性项JSON ("type", "integer", "0清空/1添加/2覆盖。0 不需要 devices; 1/2 必须给 devices") + "," + 属性项JSON ("devices", "text", "设备清单 JSON 数组, type=1/2 时必填。每项: {device_id(驱动ID, 驱动属性里查到的硬件ID; 特殊值 default/communications), label(硬件名), group_id(分组ID)}; 别名 driver_id 或 id / name / group 亦可"), "\\"target\\",\\"type\\""))"""

G7_SCHEMA_OLD = """添加工具JSON ("browser_fingerprint", "浏览器指纹总入口(按 action 分派)| canvas_random/webgl_random/audio_random 为随机噪点, audio_param 设音频参数, webrtc/geolocation/timezone/ssl 为对应维度虚拟化, set_batch 批量下发, ua 走 browser_fingerprint_ua, count 查当前生效项数, clear 清空 | 多数改动需刷新页面生效", 多属性Schema文本 (属性项JSON ("action", "text", "canvas_random/webgl_random/audio_random/audio_param/webrtc/geolocation/timezone/ssl/ua/set_batch/count/clear") + "," + 属性项JSON ("config", "text", "JSON配置"), "\\"action\\""))"""

G7_SCHEMA_NEW = """添加工具JSON ("browser_fingerprint", "浏览器指纹总入口(按 action 分派)| canvas_random/webgl_random/audio_random 为随机噪点, audio_param 设音频参数, webrtc/geolocation/timezone/ssl 为对应维度虚拟化, set_batch 批量下发, ua 走 browser_fingerprint_ua, count 读指纹API调用计数(是指纹API被调用的次数, 不是当前生效项数), clear 全清(类库清理数据: 指纹/代理/wss/debugger/isTrusted 全部VIP数据), clear_count 只把调用计数归零(保留已设指纹, 与 clear 语义不同; 回包字段 success/cleared/count) | 多数改动需刷新页面生效", 多属性Schema文本 (属性项JSON ("action", "text", "canvas_random/webgl_random/audio_random/audio_param/webrtc/geolocation/timezone/ssl/ua/set_batch/count/clear_count/clear") + "," + 属性项JSON ("config", "text", "JSON配置"), "\\"action\\""))"""


EDITS = [
    {
        "file": os.path.join("src", "MCP_Server_VIP.wsv"),
        "label": "G6-1 分派块: 真正构造并传入设备清单 (FBrowser_媒体硬件数组)",
        "old": G6_DISPATCH_OLD,
        "new": G6_DISPATCH_NEW,
        "delta": 61,
        "why": "旧代码 3 处只传 type(MCP_Server_VIP.wsv:1064/1068/1072); 类库第 2 参 媒体硬件清单 有 @默认值=空对象, "
               "类库实现体按 IsNullObject() 短路 MapToString(), 于是设备清单恒空却回『已设置』。",
    },
    {
        "file": os.path.join("src", "MCP_Server.wsv"),
        "label": "G6-2 Schema: 增 devices 参数, required 增 type, 描述如实说明",
        "old": G6_SCHEMA_OLD,
        "new": G6_SCHEMA_NEW,
        "delta": 0,
        "why": "旧 Schema 只有 type + target, 根本没有任何字段能携带设备清单。",
    },
    {
        "file": os.path.join("src", "MCP_Server_Core.wsv"),
        "label": "G7-1 分派: 新增 action=clear_count (指纹_清空调用计数)",
        "old": G7_BRANCH_OLD,
        "new": G7_BRANCH_NEW,
        "delta": 10,
        "why": "指纹_清空调用计数(FBroVip.wsv:211) 在 src 零引用; 现有 count 只读, clear 走 清理数据() 会全清伪装。",
    },
    {
        "file": os.path.join("src", "MCP_Server_Core.wsv"),
        "label": "G7-2 分派: 未知action 提示补 clear_count",
        "old": G7_UNKNOWN_OLD,
        "new": G7_UNKNOWN_NEW,
        "delta": 0,
        "why": "否则错误提示与会话可用 action 不一致, 客户端会以为没有 clear_count。",
    },
    {
        "file": os.path.join("src", "MCP_Server.wsv"),
        "label": "G7-3 Schema: action 清单/描述补 clear_count, 并修正 count 的错误说明",
        "old": G7_SCHEMA_OLD,
        "new": G7_SCHEMA_NEW,
        "delta": 0,
        "why": "Schema 里 action 清单缺 clear_count; 且描述把 count 写成『查当前生效项数』, 实际返回的是指纹API调用计数。",
    },
]


def main():
    out = sys.stdout
    out.write("=" * 100 + "\n")
    out.write("G6/G7 指纹补丁%s\n" % ("【APPLY 写盘模式】" if APPLY else "【DRY-RUN 只打印, 不写盘】"))
    out.write("仓库根: %s\n" % ROOT)
    out.write("=" * 100 + "\n")

    # ---- 按文件分组 ----
    by_file = {}
    for e in EDITS:
        by_file.setdefault(e["file"], []).append(e)

    patched = {}
    problems = []

    for rel, edits in by_file.items():
        path = os.path.join(ROOT, rel)
        raw = io.open(path, "rb").read()

        # 硬断言: 源文件必须是 UTF-8 无 BOM + LF
        if raw[:3] == b"\xef\xbb\xbf":
            problems.append("%s: 源文件带 UTF-8 BOM, 拒绝处理" % rel)
            continue
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as ex:
            problems.append("%s: 不是合法 UTF-8 (%s)" % (rel, ex))
            continue
        if "\r" in content:
            problems.append("%s: 源文件含 CR(非纯 LF), 拒绝处理" % rel)
            continue

        base_bal = balance(content)
        base_lines = nlines(content)
        out.write("\n" + "-" * 100 + "\n")
        out.write("文件: %s   (原 %d 行, 花括号净额 %+d, 圆括号净额 %+d)\n" % (rel, base_lines, base_bal[0], base_bal[1]))
        out.write("-" * 100 + "\n")

        cur = content
        for k, e in enumerate(edits, 1):
            out.write("\n>>> [%s / 第 %d 处] %s\n" % (rel, k, e["label"]))
            out.write("    原因: %s\n" % e["why"])

            hits = cur.count(e["old"])
            out.write("    锚点唯一性: 全文件精确匹配次数 = %d (要求恰好 1)\n" % hits)
            if hits != 1:
                problems.append("%s: 锚点『%s』匹配 %d 次(!= 1), 未做任何替换" % (rel, e["label"], hits))
                out.write("    !! 锚点不唯一/未命中 —— 该文件全部替换被放弃(绝不部分替换)\n")
                out.write("    锚点原文(期望):\n")
                for ln in e["old"].split("\n")[:6]:
                    out.write("      | %s\n" % ln)
                out.write("       ...\n")
                cur = None
                break

            # 逐行精确匹配的二次校验(定位串不允许跨行错位)
            lines = cur.split("\n")
            blk = e["old"].split("\n")
            n = len(blk)
            line_hits = sum(1 for i in range(len(lines) - n + 1) if lines[i:i + n] == blk)
            out.write("    整行块匹配次数 = %d (要求恰好 1)\n" % line_hits)
            if line_hits != 1:
                problems.append("%s: 锚点『%s』整行块匹配 %d 次(!= 1)" % (rel, e["label"], line_hits))
                cur = None
                break

            old_bal = balance(e["old"])
            new_bal = balance(e["new"])
            out.write("    片段括号净额: 旧 { %+d } ( %+d )  ->  新 { %+d } ( %+d )   (要求两者相等)\n"
                      % (old_bal[0], old_bal[1], new_bal[0], new_bal[1]))
            if old_bal != new_bal:
                problems.append("%s: 『%s』片段括号净额变化 %s -> %s" % (rel, e["label"], old_bal, new_bal))
                cur = None
                break

            d_old = nlines(e["old"])
            d_new = nlines(e["new"])
            out.write("    行数变化: %d -> %d (实际 %+d, 期望 %+d)\n" % (d_old, d_new, d_new - d_old, e["delta"]))
            if d_new - d_old != e["delta"]:
                problems.append("%s: 『%s』行数变化 %+d != 期望 %+d" % (rel, e["label"], d_new - d_old, e["delta"]))
                cur = None
                break

            out.write("    ---- 旧文本(%d 行) ----\n" % d_old)
            for ln in e["old"].split("\n"):
                out.write("      | %s\n" % ln)
            out.write("    ---- 新文本(%d 行) ----\n" % d_new)
            for ln in e["new"].split("\n"):
                out.write("      | %s\n" % ln)

            cur = cur.replace(e["old"], e["new"], 1)

        if cur is None:
            continue

        # 全文件级硬断言
        new_bal = balance(cur)
        new_lines = nlines(cur)
        out.write("\n    全文件校验: 花括号净额 %+d -> %+d ; 圆括号净额 %+d -> %+d ; 行数 %d -> %d (%+d)\n"
                  % (base_bal[0], new_bal[0], base_bal[1], new_bal[1], base_lines, new_lines, new_lines - base_lines))
        if new_bal != base_bal:
            problems.append("%s: 全文件括号净额变化 %s -> %s" % (rel, base_bal, new_bal))
            continue
        if "\r" in cur:
            problems.append("%s: 结果含 CR" % rel)
            continue

        patched[rel] = cur

    out.write("\n" + "=" * 100 + "\n")
    if problems:
        out.write("!! 存在 %d 个问题, 未写盘:\n" % len(problems))
        for p in problems:
            out.write("   - %s\n" % p)
        out.write("=" * 100 + "\n")
        return 2

    if not APPLY:
        out.write("DRY-RUN 通过: %d 个文件 / %d 处替换全部锚点唯一、括号净额不变、行数变化符合预期。\n"
                  % (len(patched), len(EDITS)))
        out.write("未写任何文件。要真正落盘请加 --apply。\n")
        out.write("=" * 100 + "\n")
        return 0

    for rel, text in patched.items():
        path = os.path.join(ROOT, rel)
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        chk = io.open(path, "rb").read()
        assert chk[:3] != b"\xef\xbb\xbf", rel
        assert b"\r" not in chk, rel
        out.write("已写盘: %s (%d 字节, UTF-8 无 BOM, LF)\n" % (rel, len(chk)))
    out.write("=" * 100 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
