# -*- coding: utf-8 -*-
"""追加报告 §132(第115轮): VIP 插件 P0 修复并实证 + 事件全开三套统一 + 补 action=get + 文案/文档对齐。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 132. 第115轮：VIP 插件 P0（装得上但**静默不执行**）已修复并**实证**；"事件全开"三套实现统一

本轮四路并行只读审计（`_audit/_gap_*` 系的后续）＋主代理独占编译与真机验证。

### 132.1 ★P0：插件的 content_scripts.js 此前**从不执行**，且没有任何报错

类库原文（`FBroVip.wsv:109`）：`FBrowser_VIP功能_启用插件高级功能` ——
「VIP功能…**必须在加载插件前启用**，启用插件的高级功能，默认CEF**不支持插件content_scripts.js脚本执行**，
启用高级功能后才能支持」。而全库该开关 **0 命中**，插件三件套（装载/卸载/查询）却早已交付
⇒ 交付形态是"能装 CRX、插件却不干活、失败无提示"。

**修法（两处，幂等）**：
- `main.wsv`：在强制 VIP 标志之后、`FBrowser_初始化` **之前**调用一次（进程内最早可调用点），并置
  `MCP命令服务器.VIP_插件高级功能已启用 = 真`；
- `MCP_Server_VIP.wsv` 的加载分支：加载前再幂等补开，并在回包里**如实回报**
  `advanced_enabled=" + 选择 (标志, true/false)`（一开始我写成硬编码 `true`，属"断言而非回报"，已改）。

**顺带补的能力**：`browser_vip_load_extension` 原先只收 `.crx`；现同时支持 **`path` = 已解压插件目录**
（类库 `FBroLib.wsv:2075 VIP_高级_载入插件路径`，原文注明"CRX 安装效率低，且概率性出现页面已打开但插件未装完"）。
回包带 `mode=unpacked|crx` 与"装完刷新即生效"的指引。

### 132.2 P0 的**决定性验收 5/5**（`_audit/verify_vip_extension_plus.py`）

自建最小解压插件（`_audit/test_extension/`：MV3 `manifest.json` + `content.js`，
内容脚本给 `<html>` 打 `data-mcp-ext=yes` 并改 `document.title`）：

| 臂 | 期望 | 实测 |
|---|---|---|
| 负对照：装插件**前**读标记 | 必须读不到（否则测量方式本身无效） | `{"message":"__NONE__"}` ✔ |
| `load_extension {path}` | 接受解压目录 | `已提交载入插件目录: … | mode=unpacked | advanced_enabled=true` ✔ |
| 装完 reload 后读标记 | `yes` | `{"message":"yes"}` ✔ |
| 标题 | 被内容脚本改写 | `MCP-EXT-CONTENT-SCRIPT-RAN` ✔ |
| 如实回报开关 | 读真实标志 | `advanced_enabled=true`（改前是硬编码）✔ |

> 诚实边界：**没有**做"关掉开关再装插件"的反证实验（开关在进程启动时即置真，运行期无法关闭），
> 所以"该开关是**必要**条件"这一点依据的是**类库原文**，不是我的测量；我实测证明的是
> "按现行实现，插件内容脚本**确实会执行**"。

### 132.3 "事件全开"三套实现不一致 → 统一到**同一 26 项集合**

子代理逐行计数（`_audit/_collect_events_fix_r115.md`）：
`browser_kernel_events_all` enable/disable **各 26 项、双向对称**（基准）；
而 `browser_collect event_all_enable` 只有 **11** 项、`event_all_disable` 却有 **13** 项（多关"资源/键盘焦点"）；
第三处 `关闭全部事件监控` 只有 **14** 项。

用户可见后果：用 collect 开"**全部**事件监控"后，`resource_*`/`key_focus_*`/`context_menu*`/`quick_menu*`/
`nav_intent*`/`ui_*`/`permission_*`/`offscreen_*` 及控制台/网络详细日志等 **15 项仍是关的**；用 collect 关
"全部"后仍有 **13 项为真**（事件继续入库），文案却说"全部已禁用"。

**修法**：以 `MCP_Kernel.wsv` 的 enable 分支为**唯一来源**，用脚本提取那 26 个字段名，重新生成三处赋值块
（collect enable 11→26、collect disable 13→26、`关闭全部事件监控` 14→26），并把两条返回文案改为如实描述。

### 132.4 验收 **5/5**（`_audit/verify_event_all_unified.py`，用**另一个工具**当观测器避免自证）

| 臂 | 判据 | 实测 |
|---|---|---|
| collect `event_all_enable` | 26 项全为真（修前 11） | 真 26 / 假 0 ✔ |
| collect `event_all_disable` | 26 项全为假（修前残留 13 真） | 仍为真的项：无 ✔ |
| kernel `action=enable` | 与 collect 同一集合 | 真 26 ✔ |

### 132.5 验收时**又逮到一个**"文案承诺了不存在的动作"

我原本想用 `browser_kernel_events_all action=get` 当观测器，结果得到
`action 须为 enable/disable` —— 而该工具**自己的缺参提示**里写着「查询状态请显式传 `action:get`」。
即：① 文案承诺了未实现的动作；② **用户/代理此前根本没有任何办法查看 26 个监控开关的真值**。
→ 已实现 `action=get`（141 行，逐项回报 26 个布尔 + `enabled_count`/`total`），文案同步改为
`enable/disable/get`。这也让 132.4 的验收有了独立观测器。

### 132.6 文案/文档与实现对齐（"照文档做"必须等于"实际行为"）

| 位置 | 原文 | 改为 |
|---|---|---|
| kernel 工具描述 | 「一次性打开 **13** 项…」 | 26 项（13 事件族 + 3 日志 + 10 扩展族），并注明与 collect 完全一致 |
| collect 工具描述 | 「`app_enable`(**原有 12 族**)」 | 13 族 |
| `browser_event` 报错文案 | 只列到 `focus_*`，不含菜单/导航意图/界面细节/插件/启动/渲染/权限/离屏 | 补全 6 组族名 + 注明族名可通配 |
| `docs/index.html` | 「`event_all_enable` 开启 **10 项**（不含资源与键盘焦点…）」 | 26 项且与内核一致、disable 逐项对称 |
| `docs/index.html` | **4 处**指向 `/docs/使用技能书.md` —— 该文件**不存在**（404 死链） | 去掉链接，标注"未随包发布"，改指 `tools/list` 与既有文档 |

> 注：上一轮我曾声称改过 kernel 的"13 项"，**实际只改了 `MCP_Kernel.wsv` 内部文案**，工具描述那处漏了；
> 本轮由子代理复核抓出并已改。这是"声称完成"与"逐处核对"的差别，记录下来。

### 132.7 测量工具自身的误报再修两处 → 卫生扫描四项归零

- `_audit/event_gap.py`（子代理重写）：旧正则要求 `<公开…>` **同行闭合**，导致 13 个跨行属性块的事件
  **从未进入分母** —— 数字从此可信：**8 个事件类 135/150 = 90%**（应用 30/30、浏览器 81/88、
  JS交互 0/2、开发者消息 3/5、URL请求 3/7）＋ 回调基类 11/26；旧"105/105"被证实是分母漏数。
- `_audit/cleanup_scan.py`：`DEAD_COMMENT` 里裸写的 `否则` 会把**说明性散文**（如
  `// 否则后续 touch_move 会误以为…`）当成"被注释掉的语句"，实测 7/7 全是误报 → 改为要求 `否则` 后接 `(` 或 `{`。
- 3 条"残注释(已禁用/已移除)"按**叙述改契约**重写（保留实测约束、去掉开发过程叙述）。
- 结果：**操作备注 242（唯一剩余项）/ 死代码备注 0 / 残注释 0 / 零引用方法 0 / 零引用成员 0 /
  重复分支 0 / 幽灵注册 0**。

### 132.8 已就绪但**本轮未做**（不声称完成）

子代理已交付可直接落地的计划 `_audit/_events_patch_plan_r115.md`（617 行），含 12 个事件的粘贴级骨架、
类库签名陷阱与节流写法。其中两条**必须遵守**：
1. **签名陷阱**：`浏览器_即将打开开发者窗口`(`FBroEventControl.wsv:763`) 方法行**没有** `类型 = 逻辑型`
   （"返回值注释"是从 `即将打开新窗口` 抄来的残留，胶水是 `void OnBeforeDevToolsPopup(..., bool*, ...)`）
   ⇒ 覆盖**禁止**写返回类型与 `返回 (假)`；而 `离屏渲染_获取根屏幕矩形` 是**逻辑型**、另两个 `离屏渲染_*` 是 void。
2. **文件格式**：`MCP_BrowserEvents.wsv` 是 **LF + 双倍行距**、`MCP_Callbacks.wsv` 是 **CRLF + 单倍行距**，
   插入必须按各自格式写。
补完 12 个后预计：浏览器事件 88/88、开发者消息 5/5、URL请求 6/7；并**必须重跑** `_audit/event_gap.py` 取数。
另：新增监控开关时要**同时**改进 6 处置真/置假入口（collect enable/disable、kernel enable/disable、
`关闭全部事件监控`、默认值），否则立刻打破 132.3 刚建立的对称不变式。

### 132.9 状态

工具总数 **317**；台账 **317/317**（`browser_vip_load_extension`/`browser_collect`/
`browser_kernel_events_all` 本轮重测均 pass，探针缺参问题已修）；编译 **0 警告**；fastcheck **41/41**；
卫生扫描除"操作备注 242"外全部归零。
"""


def main():
    data = open(REP, 'rb').read()
    if data.startswith(b'\xef\xbb\xbf'):
        print('!! 报告有 BOM')
        return 1
    text = data.decode('utf-8')
    if '\r' in text:
        print('!! 报告含 CR')
        return 1
    if '## 132. 第115轮' in text:
        print('!! §132 已存在')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 132. 第115轮') == 1
    print('已追加 §132; 行数 %d -> %d (无 BOM / 无 CR / 唯一)' % (text.count('\n') + 1, t2.count('\n') + 1))
    return 0


sys.exit(main())
