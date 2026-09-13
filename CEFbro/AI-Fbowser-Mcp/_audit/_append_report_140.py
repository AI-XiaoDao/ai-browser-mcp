# -*- coding: utf-8 -*-
r"""追加报告章节: ## 140. 第122轮 —— 类库全量 API 面反向核对(3 个只读代理并行) + 启动开关通道 v2 端到端实测。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SECTION = '''
## 140. 第122轮：类库全量 API 面反向核对 + 启动开关通道 v2（端到端实测 11/11）

### 140.1 三个只读代理并行核对的结果（按文件所有权分工，全部只读、未编译、未调 MCP）
| 核对范围（技能书类库） | 方法数 | 已覆盖 | 不适用/等价 | 真缺口 |
|---|---|---|---|---|
| `类_FBrowser_浏览器` + `FBrowser辅助功能` + `FBrowser初始化控制` | 134 | 111 | 18 + 10 等价 | **5**（DPI感知模式、V8堆栈尺寸、尝试关闭、取窗口运行风格、data URI） |
| `类_FBrowserVIP_控制器` | 115 公开 | 102 | 2 + 9 等价 | **2**（鼠标转触摸事件、创建标签浏览器[项目刻意禁用]） |
| `类_FBrowser_命令行` / `类_FBrowser_菜单模式` / `类_FBrowser_应用事件` | 31 / 36 / 30 | 6(开关)+7(只读) / 18 / 30 全部有接收者 | 见下 | 命令行 **2**（跨框架、禁用代理）+ 受控名值表；菜单 **18 项零调用**；应用事件 **0**（但 17 项"名义覆盖"） |

**本轮纠正的误报（重要）**：
- `停止载入` 不是缺口（早有 `browser_stop`）；`清理缓存`/`移动窗口`/`显示隐藏窗口`/`重新载入_忽略缓存`/`置父窗口`/`Base64编解码`/`URI编解码`/`多浏览器管理` 等**都已覆盖** —— 早期缺口清单里的这些条目是**陈旧**的。
- **`指纹_虚拟Viewport` 实参错位是误报**：类库声明顺序是 `(OffsetTop, OffsetLeft, Height, Width)`，嵌入式体为
  `SetVirViewport (m_class, @<OffsetTop>, @<OffsetLeft>, @<Width>, @<Height>)` —— 用的是**命名引用**，
  与真头文件 `SetVirViewport(x,y,w,h)` 一致；项目调用传 `(top,left,height,width)` 与之自洽。**未做任何"修复"**（避免把非缺陷改坏）。
- 菜单"快照"能力受**类库硬阻塞**：未封装 `GetCommandIdAt/GetLabelAt/GetTypeAt/GetGroupIdAt`（逐名 grep = 0），
  无法按索引枚举默认菜单项 → 该能力只能如实降级，不能靠项目侧补齐。

### 140.2 启动开关通道 v2（新增能力 + 可观测性）
- 新增配置键 **3 个**：`enable_cross_frame`（启动期 `命令行.启用跨框架操作模式 ()`，与 iframe 子框架填表互补）、
  `disable_proxy`（`命令行.禁用代理 ()`，连 Windows 系统自动检测代理一起关，`browser_clear_proxy` 做不到）、
  `startup_switches`（**受控名值表**：只接受代码里写死的 4 个名 `lang` / `force-device-scale-factor` /
  `disable-blink-features` / `disable-features`，各自带值校验；非法值进 `rejected_switches`，白名单外的名一律忽略）。
  三份 `mcp_config.json` 副本同步补齐（保持 CRLF/2 空格缩进/无 BOM，`json.loads` 校验 17→20 键）。
- **新增只读工具 `browser_startup_args`**（321 个工具）：回执 `applied_switches` / `command_line_raw` /
  `cmdline_available` / `name_value_switches` / `rejected_switches` / `enable_cross_frame` / `disable_proxy` / `note`。
  修之前这两个回执字段（`命令行开关已应用` / `命令行开关原文`）**没有任何 MCP 读取入口** —— 开关是否生效对用户与 AI 都不可观测。
- **踩到的两个坑（都靠"接上就编译/就实测"暴露）**：
  1. 类库注释写明 `AppendSwitchWithValue` 的 name **"默认前面要加 --"**，故裸名必须补 `--` 前缀，否则内核静默忽略 → 已在施加处补；
  2. 我自己写的补丁脚本**定义了分派分支却没有插入**（断言只查括号与行数，静默通过）→ 工具"注册了、路由也加了"但调用返回空。
     已补 `_apply_startup_args_dispatch.py` 并新增"插入后文件里必须出现工具名"的断言。
- **端到端实测 11/11（`_audit/verify_startup_switches_e2e.py`）**：改 linker 配置 → 重启 → 用回执核对：
  - `cmdline_available: true` ⇒ **`即将处理命令行` 事件确实被派发**（这一条此前在报告里是"从未被调用"的存疑项，现已定论）；
  - `applied_switches = enable_cross_frame;disable_proxy;lang;force-device-scale-factor;`；
  - **内核命令行里真的出现** `--lang=en-US --force-device-scale-factor=1`（名值表确实落到内核，且 `--lang` 覆盖了类库默认的 `--lang=zh-CN`）；
  - 非法值 `disable-features="Bad Feature!!"` → 进 `rejected_switches`（不静默丢弃）；白名单外的名未下发；
  - 恢复默认后回执归零、命令行不再含该开关（A/B 可逆）。

### 140.3 顺手修掉的真实缺陷与台账噪声
- **`browser_vip_disable_console` 的 performance 伪装有真缺陷**：类库把 `最小值/最大值` 声明为 `@默认值 = 0`，
  而注释写的是"默认值0.3/默认值1"；只传布尔会让内核收到 **0~0** ⇒ `performance.now/mark/measure` 退化成**固定 0**，
  比不伪装更容易被反调试识别。现改为显式下发 0.3/1（并可用 `performance_min_ms`/`performance_max_ms` 覆盖）。
- **台账探针假目标修正**：新增"运行期取值"机制（`mass_probe.DYNAMIC_ARGS`），把 `browser_find_by_hwnd` 的假句柄 1
  换成真实窗口句柄 ⇒ 由"失败"变为**如实通过**（台账 320 项时 313→314 通过）。
- 口径订正：文档里"未通过校验的条目都会进 rejected_switches"属**过度承诺**，已改为"只有名在白名单内而值非法才进；
  白名单外的名一律忽略"；并如实标注 `禁用代理` 在本机类库下发出的是 **`--no-proxy-server=disabled`**（带值形态），
  是否被内核按预期识别**未验证**。

### 140.4 当前状态
工具 **321**；台账 **321/321**（315 通过 / 6 未通过：2 个刻意确认闸门 + 4 个已记录探针假目标）；快检 **56/56**；
卫生扫描全零（操作备注 0 / 死代码备注 0 / 残注释 0 / 零引用方法 0 / 零引用成员 0 / 重复分支 0 / 幽灵注册 0）。

### 140.5 本轮识别、留给后续的候选（都已有 file:line 依据）
1. 启动期一行即可补：**进程 DPI 感知模式**（`FBrowser_设置程序DPI模式`，注意会改变 CSS 视口，坐标类用例需回归）、
   **V8 堆栈尺寸**（`FBrowser_初始化_设置V8环境默认堆栈大小`，深递归逆向页面防渲染进程崩溃）。
2. `高级_设置触发鼠标触摸事件`（**建议走 CDP `Emulation.setEmitTouchEventsForMouse`**，不走内核级注入，避免破坏 CDP 通道）。
3. `browser_close` 增 `try_close`（可被页面 `beforeunload` 否决；回包须区分"已关闭/被拒绝/超时"）。
4. `browser_get_run_style` **名实不符**（描述"窗口运行风格"，实际返回 Win32 GWL_STYLE）→ 增补 CEF `runtime_style` 字段并改描述。
5. VIP 过滤器**按需清空入口**缺失（现只在 `browser_shutdown` 清）；`browser_set_s5_proxy` 缺 `suppress_error`。
6. **应用事件的两处文案互相矛盾**（`MCP_Server_Core.wsv:3862/3867` 称渲染族"永不触发"，`main.wsv:846-855` 称"已修复"），
   至少一处陈旧，应统一口径（避免误导使用者）。
'''
# 注: 本字面量内不含三个连续双引号


def main():
    raw = open(REPORT, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '报告带 BOM'
    assert b'\r\n' not in raw, '报告含 CRLF'
    text = raw.decode('utf-8')
    assert '## 140.' not in text, '章节 140 已存在'
    out = text.rstrip('\n') + '\n' + SECTION
    if '--apply' in sys.argv:
        with io.open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('已追加: %d -> %d 字符' % (len(text), len(out)))
    else:
        print('[dry-run] 将追加 %d 字符' % len(SECTION))


main()
