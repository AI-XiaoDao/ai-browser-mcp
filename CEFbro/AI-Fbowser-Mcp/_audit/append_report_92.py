# -*- coding: utf-8 -*-
"""把第 92 节(第 76 轮)追加到 MCP工具可用性检测报告.md。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, "MCP工具可用性检测报告.md")

SECTION = """
---

## 92. 第 76 轮：清理缓存补上"按对象粒度"能力，并揪出一个**静默无效**

### 92.1 缺口来源
独立审计指出: `browser_clear_cache_browser` 的实现是 `browser.清理缓存 (, , , 清理回调)` —— 三个过滤参数全缺省,
于是类库文档里那套**按位或挑对象**的粒度(例如"只清 localStorage/IndexedDB 而保留 Cookies")**完全无法表达**,
用户只能去手写 `browser_cdp_call{Storage.clearDataForOrigin}`。本轮把它参数化了。

### 92.2 实现
- 新增三个可选参数: `origin`(文本) / `targets`(逗号分隔对象名) / `storage_types`(逗号分隔类型);
  **缺省值与旧行为完全一致**, 老调用不受影响。
- 新增两个掩码助手 `取清理对象掩码` / `取缓存类型掩码`(单项名称 → 类库 `清理缓存.*` / `缓存类型.*` 常量,
  名称不识别返回 -1)。调用方分词累加, 任一名字不认识就**整体失败并指名** —— 不静默忽略
  (静默忽略会让"只清了一半"看起来像成功)。
- 响应用 `命令成功_异步` 回执并**回显 origin / 对象掩码 / 类型掩码**, 便于核对到底清了什么。

### 92.3 ★ 顺带揪出一个静默无效(这是本轮最有价值的发现)
判别式实测(同一页面同时布置 localStorage 与 cookie, 只清其中一种, 断言**另一种必须活着**):

| 调用 | localStorage | cookie |
|---|---|---|
| `targets=localstorage`(**无 origin**) | **仍在**(清前后都是 1) | 仍在 |
| `targets=localstorage` + `origin=https://example.com` | **已清** | 仍在 ✅ |
| `origin` 末尾带斜杠 | **已清** | — |
| `targets=all`(**无 origin**) | **仍在** | — |

⇒ **不给 origin 时, 按源存储的那几类(localStorage 等)清不掉, 而且不报任何错** —— 连 `targets=all` 也一样。
这正是"用户什么都没做错却毫无效果"的典型形态。

**修法(零前置)**: 未传 `origin` 时**自动取当前页面的 origin**(`scheme://host[:port]`, 不含路径 ——
类库明确要求根域名不带网址后的路径), 并经 `auto_prepared` 如实上报"补了什么"。

### 92.4 验收（`_audit/verify_clear_cache_granular.py`，10/10 PASS）

| 用例 | 判据 | 结果 |
|---|---|---|
| 只清 localstorage | localStorage 变 NONE **且 cookie 仍是 COOKIE** | `NONE\\|COOKIE` ✅ |
| 只清 cookies | cookie 变 NOCOOKIE | ✅ |
| 未知对象名 | **明确失败并指名** `nosuchthing` | ✅ |
| 组合掩码 + storage_types | 接受并由响应回显掩码 | ✅ |

构建 0 警告 0 错误; `fastcheck` 41/41。

### 92.5 本轮定位那个类构建失败的过程(三次假设、两次被自己证伪)
症状很反直觉: 编译器只在 **MCP_Server.wsv** 报 3 条 `没有找到"MCP_核心分派"`, Core 里**一条错都不报**。
用"改一处 → 编译 → 看是否消失"的二分逐个排除:

| 假设 | 做法 | 结果 |
|---|---|---|
| 两个掩码助手有问题 | 移除助手、留分支 | **仍失败** → 证伪(助手无罪) |
| 类库常量类引用有问题(`清理缓存.全部`) | 把常量全换成等值数字 | **仍失败** → 证伪 |
| 分支体有问题 | 留助手、还原分支 | **通过** → 真因在分支体 |
| **局部文本变量写了 `值 = ""`** | 只去掉这两处 `值 = ""` | **通过** ✅ 确认 |

**方言结论(重要, 已就地写进注释)**: **局部**文本变量不能写 `值 = ""` 初始化(只有 `公开 静态` 成员变量可以)。
后果不是本行报错, 而是**整个类构建失败**, 编译器在**别的文件**里报级联错误 —— 报错位置毫无指向性。
另: 单行 `如果 (c) { 返回 (x) }` 我一开始也怀疑是元凶(它在项目里没有先例), 二分证明**不是**它;
但顺手已全部改成多行形式(项目通行写法), 并**没有**把它当作已证实的结论写进报告。

### 92.6 台账进度
**227 → 234/312**(本轮以 `--next 12` 推进, 7 条落账、0.2s、无冷重启);
**前置缺失类失败维持 0、把实例卡死维持 0**。
"""

b = io.open(P, "rb").read()
assert b[:3] != b"\xef\xbb\xbf" and b.count(b"\r\n") == 0
txt = b.decode("utf-8")
assert "## 92." not in txt
io.open(P, "w", encoding="utf-8", newline="\n").write(txt + SECTION)
nb = io.open(P, "rb").read()
print("追加完成: %d -> %d 字节, 行数 %d -> %d"
      % (len(b), len(nb), b.count(b"\n") + 1, nb.count(b"\n") + 1))
