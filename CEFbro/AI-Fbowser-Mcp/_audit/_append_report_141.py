# -*- coding: utf-8 -*-
r"""追加报告章节: ## 141. 第123轮 —— app_* 族定论 / 鼠标转触摸(CDP) / DPI+V8 启动能力实测。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SECTION = '''
## 141. 第123轮：`app_*` 事件族定论、鼠标转触摸(CDP 路线)、DPI 感知与 V8 堆上限实测

### 141.1 ★`app_*` 事件族到底会不会入库 —— 用实测终结两处互相矛盾的文案
项目里有**两处相反**的说明：`MCP_Server_Core.wsv`(工具回包)称"渲染进程是 SDK 自带的 FBroSubprocess.exe，事件不会派发到本项目，
`app_render_*` 不会产生任何记录"；而 `main.wsv`(注释)称"补了 `获取默认事件` 之后事件就能到"。至少一处陈旧。
- 实测（`_audit/probe_render_events.py` + `_audit/probe_app_family.py`）：开启 `event_render_enable/event_renderws_enable/event_app_enable/event_lifecycle_enable`
  并用 `browser_kernel_events_all action=enable` 一次全开，然后**故意**制造 ①未捕获 JS 异常 ②焦点元素变化 ③URL 变化 + 两次导航：
  - 时间线（300 条）里 **一条 `app_*` 记录都没有**；
  - 对照臂正常：`load_end`=5、`title_changed`=10、`browser_created`=1、`frame/url/resource/favicon` 均有记录。
- 结论：**`app_*` 族（含 `app_render_*`/`app_v8_*`/`app_startup_*`）在本机不入库** —— 与 `MCP_Server_Core` 的口径一致，`main.wsv` 那两处断言**已被证伪**，
  本轮按实测订正（保留接线，但注明"仅为将来换构建即可生效，勿据此承诺可用"）。
- 顺带修掉一个**误导性错误文案**：此前无论开关有没有开，查 `app_*` 一律回"请先 browser_collect action=event_app_enable" ——
  即使开关**已经开着**也这么说，用户会一直以为"忘了开"。现在区分两种成因：开关未开 → 提示打开；**开关已开仍无记录** → 说明该族天生不来 + 给出可用替代
  （浏览器事件族 + `browser_execute_js`/`browser_network` + CDP 类工具）。

### 141.2 新能力：鼠标事件转触摸事件（**走 CDP，不走内核级注入**）
- 缺口依据：类库 `高级_设置触发鼠标触摸事件`（= CEF `Emulation.setEmitTouchEventsForMouse`）在全项目**零调用**，
  项目只有"触摸仿真开关"。项目已实测**内核级注入会让本会话 CDP 通道失效**，故本轮走 CDP 路线：挂在 `browser_vip_touch_emulation` 上新增 `mode=mouse`，
  用 `Emulation.setEmitTouchEventsForMouse`（不需要启用 JS 执行环境、不需要刷新、不破坏 CDP 通道）。
- 实测（`_audit/verify_round122_fixes.py`）：
  - CDP 调用成功并可撤销（`enable=false` 走同一命令）；`configuration` 非法值被明确拒绝；
  - **页面侧真证据**：开启后在页面上装 `touchstart/mousedown` 监听，再用 `browser_mouse_click` 点一下 →
    页面收到 **`touchstart`**（对照：关闭后同一操作收到的是 `mousedown`、**没有** `touchstart`）。
    即"鼠标事件确实被转成触摸事件"是**可观测**的，不是"CDP 回了 OK 就算"。

### 141.3 DPI 感知 / V8 堆上限（两个启动期能力，均默认不改行为）
- 新增配置键 `dpi_aware`（启动期 `FBrowser_设置程序DPI模式 (按显示器感知V2)`）与 `v8_max_stack_mb`
  （启动期 `FBrowser_初始化_设置V8环境默认堆栈大小 (0, N)`），并在 `browser_startup_args` 回执里给出解析值以便自查。
- 实测（`_audit/verify_dpi_v8_e2e.py`，配置驱动 + 重启 + 页面侧指标，**3/3 通过**）：
  - **V8 确实生效且可测**：`performance.memory.jsHeapSizeLimit` 默认 **4294705152(≈4GB)** → 设 `v8_max_stack_mb=1024` 后 **1075314688(≈1GB)**；
    还原后回到 ≈4GB。⇒ 这是**设定值**而非"只放宽上限"（x64 默认已有 ~4GB，填小值会**压低**）；
    且类库中文名叫"堆栈大小"、底层 C 函数是 `FBroSetV8DefaultsHeapSize`（**堆**）—— 名实不符，文档已按实测改正。
  - **DPI 本机无可见差异**：缩放 100%(dpr=1) 时视口 984×705 前后一致 ⇒ 该键只在缩放≠100% 的显示器上有可见效果（风险提示保留）；配置可逆（还原后与基线一致）。
- 编译细节：`取窗口运行风格 ()` 返回的是**枚举** `FBrowser.常量.窗口运行风格` 而非整数，直接赋给整数变量编译不过
  （错误原文：无法将数据类型"FBrowser.常量.窗口运行风格"转换到"整数"）→ 改为先接枚举再 `(整数)` 显式转换。

### 141.4 口径订正：`browser_get_run_style` 名实不符
- 该工具描述写"获取窗口运行风格"，实际只回 Win32 `GWL_STYLE` + `is_popup`。现**保留**原字段并**新增**
  `runtime_style` / `runtime_style_name` / `runtime_style_note`（真值取自类库 `取窗口运行风格`，此前零调用）。
- 实测该值在本机是 **1(谷歌)**，而注释初稿写的是"未设置故恒为 0" —— **被实测打脸后已改正**（值由类库默认给出）。
  描述也已改准（明确区分 Win32 样式与 CEF 运行风格）。

### 141.5 状态与遗留
工具 **321**；台账 **321/321**（315 通过 / 6 未通过 = 2 个刻意确认闸门 + 4 个已记录探针假目标）；快检 **56/56**；卫生扫描**全零**
（本轮顺手清掉 3 条"注释里引用类库签名被当成死代码"的误报，做法是给这类注释加 `(签名)` 前缀）。
仍待做（均有 `file:line` 依据）：菜单快照受类库硬阻塞只能降级、`browser_close` 增 `try_close`、
VIP 过滤器按需清空入口、`browser_set_s5_proxy` 的 `suppress_error`、以及 `启用单进程模式`（类库自述不建议）等的取舍。
'''
# 注: 本字面量内不含三个连续双引号


def main():
    raw = open(REPORT, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '报告带 BOM'
    assert b'\r\n' not in raw, '报告含 CRLF'
    text = raw.decode('utf-8')
    assert '## 141.' not in text, '章节 141 已存在'
    out = text.rstrip('\n') + '\n' + SECTION
    if '--apply' in sys.argv:
        with io.open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('已追加: %d -> %d 字符' % (len(text), len(out)))
    else:
        print('[dry-run] 将追加 %d 字符' % len(SECTION))


main()
