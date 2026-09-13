# -*- coding: utf-8 -*-
"""追加报告第 94 节(第78轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = "## 94. 第78轮：VIP 开关类工具「无法识别的取值 -> 破坏性兜底」缺陷（2 例同族）+ 一条与实测不符的文案"

SECTION = """

---

%s

### 94.1 缺陷 A（安全性）：`browser_vip_enable_devtools_observer` 的破坏性分支是兜底

旧实现结构（`MCP_Server_VIP.wsv`，`browser_vip_enable_devtools_observer` 分支）：

```
目标状态 = 开关布尔                        # 非布尔节点取逻辑 -> 假
如果 ("false"/"0"/"off")  目标状态 = 假
否则 ("true"/"1"/"on")    目标状态 = 真
如果 (开关文本 == "" 且 开关布尔 == 假) -> 拒绝
enableObs = 目标状态
```

问题在于那条守卫**只覆盖了"空文本"这一种情况**。传 `enable:"mcp_probe"` 时：

1. `开关文本` 非空 → 守卫不触发；
2. 既不匹配 true 形式、也不匹配 false 形式 → 两个分支都不进；
3. `目标状态` 保持初始值 `开关布尔`，而类库对**非布尔节点**取逻辑一律给假；
4. 于是落到 `否则 { 注销CDP观察者() }` —— **最危险的取值成了兜底**。

台账实录（第77轮那批）正是如此：`enable:"mcp_probe"` 得到 `DevTools消息监听已关闭 | ⚠ …`。

修法：把"认不认得出"与"目标是开还是关"分开，取值走**显式白名单**，认不出就拒绝：

```
取值已识别 = 假
如果 ("false"/"0"/"off")  -> 目标状态=假; 取值已识别=真
否则 ("true"/"1"/"on")    -> 目标状态=真; 取值已识别=真
否则 (开关文本=="" 且 开关布尔) -> 目标状态=真; 取值已识别=真     # 布尔 true 仍可用
如果 (取值已识别 == 假) -> 返回可行动的失败(列出合法取值 + 说明为何拒绝)
```

副作用特性：本修法**同时**兼容"`yyjson取文本` 对布尔节点返回空"与"返回 true/false 字面量"两种实现，
因为两条路径都被白名单显式接住 —— 不依赖那个不确定行为。

### 94.2 缺陷 B（同族横扫）：`browser_vip_enable_inspector` 是同一缺陷类的第二个实例

它的守卫是 `参数键存在(参数JSON,"enable") == 假`，**只挡键缺失**，因此 `enable:"mcp_probe"`
同样一路走到 `目标状态 = 开关布尔 = 假` → `注销CDP观察者()`。已按同一白名单修法修掉。

**横扫结论（修复一个点之后必须横扫同族，否则等于没修）：**

| 检索目标 | 结果 |
|---|---|
| `开关文本` / `开关布尔` 惯用法 | 全库**仅 2 处**（`MCP_Server_VIP.wsv` 两个分支），均已修 |
| `注销CDP观察者()` 调用点 | 活工具路径仅上述 2 处；`main.wsv` 与 `MCP_Server.wsv:8470` 均在关闭序列内（`MCP正在关闭 = 真` 之后），合法 |
| 其它 `enable/disable` 逻辑参数（websocket_intercept / js_env / disable_debugger / touch / event_istrusted / webrtc_ip） | 无法识别时默认假 = **什么都不做**，是**失败安全**，不属同一缺陷类 |

### 94.3 缺陷 C（独立发现）：`关闭后需重启进程才能恢复` 与实测不符

关闭分支的文案声称"全部 CDP 类工具已随之失效，需重启进程才能恢复"。实测**不成立**：

- ⑥ `enable:"false"` → 关闭成功，被动观测 `cdp_ready=False`；
- ⑦ 紧接着一次真实 CDP 派发 → **成功**（`Runtime.evaluate` 返回 2），且 `cdp_ready` 回到 `True`。

原因是 CDP 分派入口（`MCP_Server.wsv` `执行CDP命令_带参数`）在 `CDP观察者已注册 == 假` 时会
**自动重新注册观察者**（其自身注释即"CDP通道自动就绪"）。所以关闭**不是**永久的，通道自愈。

必须同时纠正本报告早前的一处归因：第77轮把"台账那批之后紧跟的冷重启"记作被这个动作打坏、
必须重启才能恢复 —— 该归因**不成立**（可自愈；那次重启是预防性的）。仅当**重注册失败**
（控制器侧仍持有旧观察者）时 CDP 类工具才持续不可用，那条路径 `MCP_Server.wsv` 会给出
"恢复: 重启 AI-Fbowser-Mcp.exe"，那里的重启建议才是对的。两处文案已改为实测行为。

### 94.4 方法论：观测动作会改变被观测对象（本轮最值钱的一条）

本验证的第一版用 `browser_cdp_call` 当"CDP 是否存活"的探针。⑥ 号正对照当场把它否掉：
关闭之后探针**依然成功**。原因就是 94.3 的自愈 —— 探针把要测的东西修好了。

结论顺序很重要：**正对照失败时先怀疑探针，不要先怀疑修复。**

改用 `/health` 的 `cdp_ready`（`MCP_Server_HTTP.wsv`，纯 HTTP 只读、不经 MCP 派发、无副作用）
作为被动观测后：⑥ 关闭 → `cdp_ready=False`（正对照成立），②③ 的"仍在册"才具备判别力。

### 94.5 测试资产侧

`mass_probe.py` 的通用兜底值 `mcp_probe` 对这两个工具现在会被**正确拒绝**，于是探针只测到守卫、
测不到实现（台账会误记 fail）。已新增 `TOOL_ARG_OVERRIDES`：`enable=True`（只重新注册观察者，幂等无害）。
关闭分支**故意不**进批量探针 —— 它会把 CDP 观察者注销，污染同批其它 CDP 工具的测量；
该路径由专用脚本承担，并带正对照。

新增验证脚本 `_audit/verify_vip_observer_whitelist.py`：**27/27 通过**，覆盖两个工具 ×
{缺省、无法识别、布尔 true、文本 true、布尔 false、文本 false} × {拒绝文案、是否仍被动在册}，
其中 ⑥/⑪ 为**正对照**（关闭动作必须被被动观测到）。

### 94.6 指标

| 项 | 值 |
|---|---|
| 工具数 | 312 |
| 台账 | 244/312 已测（两个工具已重测 = pass） |
| 本轮新修 | 2 处安全缺陷（同族）+ 3 处与实测不符的文案 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
""" % HEAD


def main():
    with io.open(REPORT, 'r', encoding='utf-8', newline='') as f:
        cur = f.read()
    assert not cur.startswith(u'\ufeff'), "报告带 BOM"
    assert '\r' not in cur, "报告含 CRLF"
    assert HEAD not in cur, "该节已存在, 拒绝重复追加"
    with io.open(REPORT, 'a', encoding='utf-8', newline='') as f:
        f.write(SECTION)
    with io.open(REPORT, 'r', encoding='utf-8', newline='') as f:
        new = f.read()
    assert not new.startswith(u'\ufeff') and '\r' not in new, "追加后编码被破坏"
    print("已追加: %s" % HEAD)
    print("行数: %d -> %d" % (cur.count('\n') + 1, new.count('\n') + 1))


if __name__ == '__main__':
    sys.exit(main())
