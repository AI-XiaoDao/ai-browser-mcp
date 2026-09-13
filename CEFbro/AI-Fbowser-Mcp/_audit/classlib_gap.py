# -*- coding: utf-8 -*-
"""以技能书类库的全量 API 面为基准, 反查 MCP 工具面缺口。

用户要求:"扩展目标确保 MCP 所有能力, 而不是我说一点就一点" —— 本脚本即该目标的**系统化度量**:
不从用户提示出发, 而是把 FBrowser 类库(FBroLib/FBroVip/FBroEventControl/...)的**全部方法**抽出来,
逐个对照现有 MCP 工具(名称+描述), 列出"类库有、MCP 未暴露"的候选缺口。

匹配口径(务实且可解释): 类库方法名是中文, MCP 工具名是英文, 无法直接同名匹配;
故用一个方法名是否出现在**任一工具的完整描述文本**里作为"疑似已暴露"的判据 ——
工具描述是详细中文, 覆盖到某能力时通常会用相近措辞。**命中=疑似已覆盖; 未命中=候选缺口**,
候选仍需人工确认(可能被换了措辞, 也可能确实缺失)。

⚠⚠ 重要(第125轮实测结论, 勿再盲目使用本清单)⚠⚠
本脚本的匹配口径**误报与漏报同时存在**(根因就是上面那句"名字出现在描述里即算命中"):
  · 误报: `停止载入/可否前进/重新载入*/开始下载/显示隐藏窗口/清理缓存/移动窗口/设置代理/载入地址`
    等一大批"候选缺口"经逐条核对**其实早已覆盖**;
  · 漏报: `取父框架`、`取主浏览器` 因工具描述里出现过"主浏览器/框架"等字样被判成命中, 实际是缺口/需两步等价。
故本脚本输出**只能当作"待核对索引"**, 不能当作缺口清单。已核对过的结论见:
  · `_audit/_gap_recheck_1.md` (类_FBrowser_浏览器/辅助功能/框架/基础框架: 143 方法, 真缺口 3)
  · `_audit/_gap_menu.md`       (菜单/快捷键族: 63 方法, 可实现 14 / 做不到 13)
  · `_audit/_gap_vip_events.md` (VIP 控制器 + 事件/回调族: 324 方法, 真缺口 2)
  · `_audit/_gap_verified.md`   (**已核对汇总**: 真缺口 + 状态 + 证据, 实施前先看这一份)

用法: py -3 classlib_gap.py
输出: _classlib_gap.md (全量明细) + 控制台摘要
"""
import io
import json
import os
import re
import sys
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = r"C:\Users\cxzxc\.agents\skills\volcano-pc-programming\资料\类库\FBrowser浏览器"
BASE = "http://127.0.0.1:9222"

# 明显是内部实现/类型转换/事件绑定基础设施的方法名, 不构成"用户能力", 排除
NOISE = re.compile(
    r"^(取|置|是否|加入|删除|清空|创建|销毁|初始|_|绑定|触发|调用|发送|接收|处理|转换|复制|比较)"
    r"|回调|内部|私有|反射|序列化|反序列化|构造|析构|参数|成员|索引")


def classlib_methods():
    """抽取 (类名, 方法名) —— 只从类库源码的 `方法` 声明行取, 不误取注释。"""
    out = []
    for fn in sorted(os.listdir(LIB)):
        if not fn.endswith(".wsv"):
            continue
        cls = ""
        with io.open(os.path.join(LIB, fn), encoding="utf-8", errors="replace") as f:
            for ln in f:
                s = ln.strip()
                m = re.match(r"类\s+(\S+)", s)
                if m:
                    cls = m.group(1)
                    continue
                m = re.match(r"方法\s+(\S+)", s)
                if m:
                    out.append((fn, cls, m.group(1)))
    return out


def live_tools():
    r = urllib.request.Request(
        BASE + "/mcp",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode(),
        headers={"Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(r, timeout=25).read().decode())
    return d["result"]["tools"]


def main():
    if not os.path.isdir(LIB):
        print("!! 类库目录不存在: %s" % LIB)
        return 2
    ms = classlib_methods()
    try:
        tools = live_tools()
    except Exception as ex:
        print("!! 读取 tools/list 失败(%s) —— 请先启动程序" % ex)
        return 2

    corpus = "\n".join((t.get("name") or "") + " " + (t.get("description") or "") for t in tools)
    names = set(t.get("name") for t in tools)

    covered, gap, noise = [], [], []
    seen = set()
    for fn, cls, mname in ms:
        key = (cls, mname)
        if key in seen:
            continue
        seen.add(key)
        if NOISE.match(mname) or len(mname) <= 2:
            noise.append((fn, cls, mname))
            continue
        # 命中判据: 方法名整体出现在工具描述里, 或其前 3 字出现在描述里(措辞近似的宽松匹配)
        hit = (mname in corpus) or (len(mname) >= 3 and mname[:3] in corpus)
        (covered if hit else gap).append((fn, cls, mname))

    total = len(covered) + len(gap)
    print("== 类库 API 面 vs MCP 工具面 ==")
    print("类库方法(去重, 含类上下文) = %d   (另排除基础设施类 %d 个)" % (total, len(noise)))
    print("疑似已覆盖 = %d  (%.0f%%)" % (len(covered), 100.0 * len(covered) / max(1, total)))
    print("**候选缺口 = %d**" % len(gap))

    # 按类聚合缺口, 便于逐类补齐
    by_cls = {}
    for fn, cls, mname in gap:
        by_cls.setdefault(cls or "(无类)", []).append(mname)

    md = ["# 类库 API 面 → MCP 工具面 缺口报告\n",
          "> 由 `_audit/classlib_gap.py` 生成。基准 = 技能书 `资料/类库/FBrowser浏览器` 全量方法。\n",
          "\n- 类库方法(去重) = **%d**（另排除基础设施类 %d）" % (total, len(noise)),
          "- 疑似已覆盖 = **%d** (%.0f%%)" % (len(covered), 100.0 * len(covered) / max(1, total)),
          "- **候选缺口 = %d**" % len(gap),
          "\n## 候选缺口（按类聚合）\n"]
    for cls in sorted(by_cls, key=lambda c: -len(by_cls[c])):
        md.append("\n### %s  (%d)\n" % (cls, len(by_cls[cls])))
        md.append("`" + "`  `".join(sorted(set(by_cls[cls]))) + "`")
    md.append("\n\n## 疑似已覆盖（抽样 200）\n")
    for fn, cls, mname in covered[:200]:
        md.append("- %s :: %s" % (cls, mname))
    p = os.path.join(HERE, "_classlib_gap.md")
    with io.open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md))
    print("\n缺口最多的类:")
    for cls in sorted(by_cls, key=lambda c: -len(by_cls[c]))[:12]:
        print("   %-38s %d" % (cls, len(by_cls[cls])))
    print("\n明细已写 _classlib_gap.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
