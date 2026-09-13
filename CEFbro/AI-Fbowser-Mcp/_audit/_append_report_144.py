# -*- coding: utf-8 -*-
r"""追加报告章节: ## 144. 第125轮(下) —— 类库缺口"三份逐条核对"落地: 提交式跳转 + 菜单别名 + 缺口台账。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SECTION = '''
## 144. 第125轮（下）：类库缺口"逐条核对"落地 —— 提交式跳转、菜单别名、以及一份可信的缺口台账

### 144.1 为什么先做"逐条核对"而不是直接照着候选表实现
`_audit/_classlib_gap.md`（由 `classlib_gap.py` 生成）给出 533 个类库方法、363 个"候选缺口"，但它的匹配口径是
**"类库方法名是否出现在任一工具的描述文本里"**。三个只读子代理按**文件所有权**分片（浏览器/辅助功能/框架、菜单族、
VIP+事件族）逐条核对后证实：**这个口径的误报与漏报同时存在** ——
- 误报：`停止载入/可否前进/重新载入*/开始下载/显示隐藏窗口/清理缓存/移动窗口/设置代理/载入地址` 等**全部早已覆盖**；
- 漏报：`取父框架`、`取主浏览器` 因为描述里出现过"主浏览器/框架"字样被判成"命中"，实际是缺口/需两步等价。
⇒ 结论已写进 `classlib_gap.py` 的文档头与 `_audit/_gap_verified.md`：**候选清单只能当"待核对索引"**。

三份核对报告（均为逐方法一行、每条附 `file:line` 与锚点原文）：

| 报告 | 范围 | 方法数 | 已覆盖 | 等价覆盖 | **真缺口** | N/A |
|------|------|--------|--------|----------|-----------|-----|
| `_audit/_gap_recheck_1.md` | 浏览器 / 辅助功能 / 框架 / 基础框架 | 143 | 94 | 12 | **3** | 34 |
| `_audit/_gap_vip_events.md` | VIP 控制器 + FBroEventControl 8 类 + 事件基础设施 | 324 | 233 | 43 | **2** | 46 |
| `_audit/_gap_menu.md` | 菜单模式(36) + 菜单环境(21) + 回调(6) | 63 | 36 | — | 可实现 14 / 做不到 13 | — |

### 144.2 缺口 #1 落地：`browser_navigate` 支持**提交式跳转**（补 `载入请求`）
- 缺口依据：类库 `类_FBrowser_框架.载入请求 (请求)`（`FBroLib.wsv:1669`）**全项目 0 调用**，而 `browser_navigate`
  只会 `载入地址`（发 GET）⇒ 无法复现"提交式跳转 / 带签名头接口跳转"这类真实场景。
- 可行性已核实：`类_FBrowser_请求` 有公开 `创建 ()`（`FBroLib.wsv:2279`，`Set(FBroHsRequest_Create())`），
  且 `置地址/置类型/置协议头_名称/置POST数据` **都已在本项目 `browser_create_url_request` 里被真实用过**
  （`MCP_Server_Core.wsv:7198-7251`）—— 故实现是**复用同一套构建逻辑**，不是新造。
- 做法（不重复造轮子）：把头/体解析抽成 `应用请求头文本` / `应用请求体文本` 两个复用件，**两条路径共用一份实现**
  （`browser_create_url_request` 的内联循环已改为调用它们）；新增 `载入框架请求 (框架, url, 方法, 头, 体)`；
  `browser_navigate` 新增 `method`/`headers`/`body`，只给 `body` 时自动按 POST；**自定义请求路径不做同址快速返回**
  （否则"重放提交"会静默变成不做事）。
- 验收（`_audit/verify_navigate_request.py`，**12/12**，预言机 = 本机 HTTP 服务**收到的东西** + 页面回显双证据）：
  GET 回归照旧；POST + 两个自定义头 + 请求体**逐字送达**；只给 body 自动 POST；**同址连续两次 POST 服务端确实收到两次**；
  页面侧回显与请求体一致。

### 144.3 缺口 #2 落地：新增 `browser_menu_alias`（菜单命令ID ⇄ 别名）
- 缺口依据：项目只有 `解析菜单命令ID` 的**正向**链（规格文本写 `copy` → 113），没有反向；而菜单事件
  `context_menu_command` **只回 `command_id` 数字** ⇒ 调用方"记录得到却读不懂"。
- 做法：新增 `菜单命令ID到别名` / `菜单命令ID所属区间` / `取菜单别名清单JSON` / `确保菜单别名候选`，
  反向查表**不建第二份表** —— 拿候选别名逐个调用既有正向链求值，正向链一变这里自动跟随。
  回复带 `caveat` 如实说明"这是 CEF 标准菜单项ID，不是本应用菜单的真实内容，只有标识/诊断价值"。
- 验收（`_audit/verify_menu_alias.py`，**12/12**）：清单与源码正向链**逐项一致**（17/17）、
  **每一项都做往返**（`to_id→to_name`、`to_name→to_id`）、`action` 可省略时自动选择、自建项 26501 如实报
  `recognized:false`+`service_zone`、未知别名/缺参/未知 action 三条失败文案均**可行动**。

### 144.4 可发现性：`browser_event` 补上菜单事件族
其描述此前**漏列**菜单事件族（而服务端自己的失败文案却列了）—— 即"记录得到、却没人知道能查"。
已按源码里的**真实事件名**补入：`context_menu_opening` / `context_menu_run` / `context_menu_command` /
`context_menu_dismissed` / `quick_menu_command` / `quick_menu_dismissed`，并注明需先开 `event_menu` / `event_quickmenu` 族。

### 144.5 剩余缺口（已建台账，`_audit/_gap_verified.md`）
| # | 缺口 | 状态 |
|---|------|------|
| 3 | `类_FBrowser_URL请求事件.上传进度`（FBroEventControl.wsv:2314） | 待做（低成本；对照下载进度覆盖即可，不碰 CDP） |
| 4 | `取父框架`（FBroLib.wsv:1692） | 待做（建议并入 `browser_get_frames` 加 `parent_id`，不新造工具） |
| 5 | `尝试关闭浏览器`（FBroLib.wsv:796） | ⚠️ 复核后二选一：若仍恒假则**删桩**（`browser_close_try` 留着一个"看起来是能力却永不成功"的桩比没有更糟） |
| 6 | `高级_创建标签浏览器`（FBroVip.wsv:1201） | ⛔ 暂不做（项目刻意拒绝 `browser_create_tab`，中高风险） |
| 7 | 菜单只读探针（`取数量`+按索引读快捷键/颜色） | 待做（需把钩子放在 `浏览器_即将打开菜单` 内 `应用菜单规格` **之前**；前提待实测） |
| 8 | 菜单按索引写（`accelat/noaccelat/colorat/checkat` 行） | 待做（并入既有 `browser_context_menu`，避免第二个菜单状态机） |

### 144.6 状态
工具 **322**（新增 `browser_menu_alias`）；台账 **322/322 已测 = 319 通过 / 3 刻意设计**；快检 **56/56**；
编译 **0 警告**；卫生扫描**全零**；本轮新增验证 `verify_navigate_request.py` **12/12**、
`verify_menu_alias.py` **12/12**、`verify_network_body.py` **16/16**。
'''

# 注: 本字面量内不含三个连续双引号


def main():
    raw = open(REPORT, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '报告带 BOM'
    assert b'\r\n' not in raw, '报告含 CRLF'
    text = raw.decode('utf-8')
    assert '## 143.' in text, '章节 143 应已存在'
    if '## 144.' in text:
        assert '--replace' in sys.argv, '章节 144 已存在(要覆盖请加 --replace)'
        text = text[:text.index('## 144.')].rstrip('\n') + '\n'
        print('已截去旧的第 144 章')
    out = text.rstrip('\n') + '\n' + SECTION
    if '--apply' in sys.argv:
        with io.open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('已写入: %d -> %d 字符' % (len(raw.decode('utf-8')), len(out)))
    else:
        print('[dry-run] 将写入 %d 字符' % len(SECTION))


main()
