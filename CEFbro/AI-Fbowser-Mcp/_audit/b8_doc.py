# -*- coding: utf-8 -*-
"""B8 — 生成 C++ 侧交付文档: 输出名对照表"""
import json, os, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = r"C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp"
d = json.load(open(os.path.join(OUT, "english_names.json"), encoding="utf-8"))
inv = json.load(open(os.path.join(OUT, "inventory.json"), encoding="utf-8"))

NS = "rg_volcano_app"
W = []
def w(s=""):
    W.append(s)

w("# AI-Fbowser-Mcp — 火山成员 ↔ C++ 输出名 对照表")
w()
w("> 由 `@输出名` 固定。命名规则：**PascalCase、不带前缀**。")
w("> C++ 命名空间：`%s`（对应火山包 `火山.程序`）" % NS)
w()
w("## 一、使用方法")
w()
w("在 `.wsv` 源码中，每个可改名成员的定义行属性表里已写入 `@输出名`：")
w()
w("```火山")
w('类 MCP_服务器工具 <公开 @全局类 = 真 @输出名 = "MCPServerTool">')
w("    方法 控制台输出 <公开 静态 @输出名 = \"ConsoleOutput\" @强制输出 = 真>")
w('    参数 文本 <类型 = 文本型 @输出名 = "Text">')
w("```")
w()
w("于是 C++ 侧可以这样调用：")
w()
w("```cpp")
w("// 静态方法")
w("rg_volcano_app::MCPServerTool::ConsoleOutput(text);")
w()
w("// 取主浏览器（MCPCommandServer 的静态方法）")
w("auto browser = rg_volcano_app::MCPCommandServer::GetMainBrowser();")
w("```")
w()
w("## 二、关键规则（改名前必读）")
w()
w("### 1. 虚拟覆盖方法**不参与改名**")
w()
w("`@虚拟方法 = 可覆盖` 的方法在 C++ 中靠**同名 virtual 覆盖基类**：")
w()
w("```cpp")
w("// 基类（FBrowser 类库）")
w("virtual void rg_LiuLanQi_ZaiRuJieShu (FBroFrame&, INT);")
w("// 派生类必须同名，否则不构成覆盖")
w("virtual void rg_LiuLanQi_ZaiRuJieShu (FBroFrame&, INT);")
w("```")
w()
w("若改成英文名，覆盖失效 → 基类空实现被调用 → **事件静默失灵**。")
w("因此本项目 **94 个虚拟覆盖方法保留编译器生成的原始符号名**，未写入 `@输出名`。")
w()
w("### 2. `@强制输出 = 真`")
w()
w("火山是**按需编译**的：未被程序直接调用的方法不会生成 C++ 代码。")
w("（实测：`MCP命令服务器` 有 212 个方法，生成头文件中只有 201 个。）")
w("要让 C++ 侧能调用，必须同时加 `@强制输出 = 真` —— 本表已全部加上。")
w()
w("### 3. `启动类` 不参与改名")
w()
w("编译器固定使用 `startup_class` 作为程序入口，改名会破坏入口。")
w()
w("## 三、类名对照")
w()
w("| 火山类名 | C++ 类名 | 文件 |")
w("|---|---|---|")
for c in inv["classes"]:
    e = d["classes"][c["name"]]
    en = e["en"] or "*(保留 `startup_class`)*"
    w("| `%s` | `%s` | %s |" % (c["name"], en, c["file"]))
w()
w("## 四、方法对照（按类分组）")
w()
cur = None
for m in inv["methods"]:
    if m["cls"] != cur:
        cur = m["cls"]
        ce = d["classes"][cur]["en"] or "startup_class"
        w()
        w("### `%s` → `%s`" % (cur, ce))
        w()
        w("| 火山方法 | C++ 输出名 | 备注 |")
        w("|---|---|---|")
    e = d["methods"]["%s.%s" % (m["cls"], m["name"])]
    note = "虚拟覆盖，保留原名" if e["keep"] else ("静态" if e["static"] else "")
    w("| `%s` | `%s` | %s |" % (m["name"], e["en"] or "*(原始符号)*", note))
w()
w("## 五、成员变量/常量对照")
w()
cur = None
for v in inv["vars"]:
    if v["cls"] != cur:
        cur = v["cls"]
        w()
        w("### `%s`" % cur)
        w()
        w("| 火山名 | C++ 输出名 | 种类 |")
        w("|---|---|---|")
    e = d["vars"]["%s.%s" % (v["cls"], v["name"])]
    w("| `%s` | `%s` | %s |" % (v["name"], e["en"], v["kind"]))
w()
w("## 六、参数对照")
w()
w("参数较多（814 个），完整表见 `_audit/english_names.json`（键 `params`）。")
w("此处按方法列出（节选前 120 条）：")
w()
w("| 所属类 | 方法 | 火山参数 | C++ 输出名 |")
w("|---|---|---|---|")
for i, p in enumerate(inv["params"][:120]):
    key = "%s|%s|%s" % (p["cls"], p["method"], p["name"])
    w("| %s | `%s` | `%s` | `%s` |" % (p["cls"], p["method"], p["name"], d["params"][key]["en"]))
w()
w("---")
w()
w("统计：类 %d（改名 %d）｜方法 %d（改名 %d，虚拟覆盖保留 %d）｜成员变量常量 %d｜参数 %d"
  % (len(inv["classes"]), sum(1 for v in d["classes"].values() if not v["keep"]),
     len(inv["methods"]), sum(1 for v in d["methods"].values() if not v["keep"]),
     sum(1 for v in d["methods"].values() if v["keep"]),
     len(inv["vars"]), len(inv["params"])))

p = os.path.join(ROOT, "输出名对照表.md")
open(p, "w", encoding="utf-8", newline="\n").write("\n".join(W))
print("written", p)
print("lines:", len(W))
