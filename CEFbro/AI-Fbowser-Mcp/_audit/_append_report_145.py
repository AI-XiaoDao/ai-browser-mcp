# -*- coding: utf-8 -*-
r"""第125轮收尾: ①把"schema↔实现一致性"三份审计的结论与遗留项写进 `_audit/_gap_verified.md`;
②在 `MCP工具可用性检测报告.md` 追加 ## 145 章(本轮审计+修正+验收)。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

GAP_SECTION = '''
## 四、"schema ↔ 实现一致性"专项审计（第125轮新增，**实施前必读**）

三个只读子代理按派发器文件分片，把 **322 个工具**的"schema 声明"与"实现真正读取的参数"做了机械双向 diff
（并对 `MCP命令服务器.X(..., 参数JSON)` 这类委托做深度 4 的传递闭包，避免把"由共享助手读取"误报成缺口）：

| 审计报告 | 范围 | 工具数 | 差异总数 | 其中 `MISSING_IN_SCHEMA`（最严重） |
|----------|------|--------|----------|-----------------------------------|
| `_audit/_schema_audit_A.md` | `MCP_Server_Core.wsv` | 162 | **45** | **29** |
| `_audit/_schema_audit_B.md` | `_Form`/`_System`/`_VIP` | 93 | **31** | **2** |
| `_audit/_schema_audit_C.md` | `_Reverse`/`_Kernel`/`_Workflow` | 65 | **29** | **7** |

**为什么这类缺陷优先级最高**：`MISSING_IN_SCHEMA` = 实现会读的参数**没写进 schema** ⇒ AI 代理**根本看不到它**，
只能猜或反复试错 —— 正是用户抱怨的"要试很多次才成功"。典型：`browser_reverse_instrument_script` 的 `confirm`
是 install 的硬前置却没声明（台账里它长期记 fail，成因就是"参数不可见"）。

### 已修（第125轮，共 28 项，全部编译 0 警告 + 验收通过）
- B 组 15 项：`vip_enable_js_env.confirm`、`vip_touch_cancel.x/y`、`vip_touch_emulation` 的 enable 缺省语义、
  `fill_attr_get/set`、`fill_select`、`set_preference`、`vip_execute_js_context` 的必填表、
  `fingerprint_languages` 二选一、`vip_mouse_wheel` 至少一个滚动量、`get_global_cache_dir`/`send_message`/`get_run_style`
  的描述改为与实现一致、`vip_fingerprint_ssl` **未知 tls 值改为明确拒绝**（原来静默回退成"不限制"却回 success = 假成功）。
- C 组 13 项：`reverse_instrument_script.confirm`、`kernel_events_all action=get`、`kernel_watch action=list`、
  `kernel_cdp_monitor action=list` + `max` 默认值 500→**200** 改准、`kernel_download action=list`、
  `kernel_reactor` 去掉"load_end 永不触发"的错误断言并把 `load_end`/`title_changed` 补进真实事件名清单。
- 验收：`_audit/verify_schema_audit_fixes.py` **17/17**（声明层 tools/list 断言 + 行为层真机调用：
  非法 tls 值必须失败、`fill_attr_get{selector}` 必须成功、`vip_enable_js_env` 不带 confirm 必须给可行动拒绝）。

### 遗留（A 组 Top 15 等，均有 `file:line` 证据，下一轮按序实施）
1. `browser_touch_press/_release/_move`：描述承诺 `kernel:true` 但 schema 只有 x/y（同族 mouse_* 都声明了 → 家族内自相矛盾）
2. `browser_file_dialog`：描述"打开对话框"但实现注释明写**不弹窗**，且 schema 零属性
3. `browser_view_source`：描述"在新标签打开 view-source"，实现只回文本；`max_chars` 未声明
4. `browser_dom_set_value`：报错指引 `allow_empty:1` 但该参数未声明、`value` 又是 required ⇒ **死路**
5. `browser_collect`：描述写了 `keyword`/`limit`，schema 只有 `action`
6. `browser_get_text.max_chars`：声明了但实现**从不读**（截断写死常量）
7. `browser_fingerprint`：6 组 19 个维度参数（min/max/seed、sample_rate、public_ip、latitude…）全部未声明
8. `browser_dom_query.index`：**静默失效**（返回第 1 个匹配，比报错更危险）
9. debugger 家族的 CDP 原生别名（`line_number`/`scriptId`/`url_regex`…）未声明
10. `browser_network.auto_enable`、`browser_inject.inject_id`、`browser_intercept` 的 width/height/x/y、
    `browser_reverse_hook.url_pattern`、`browser_execute_js` 的 `code|file` 二选一与 `code_base64`
11. B 组遗留：`set_css_version/set_web_version/set_v8_version` 数值范围、`vip_orientation` 的 1..4 映射、
    `enable_inspector`/`enable_devtools_observer` 的旧文案、`load_extension` 的 path|crx_path、
    `set_window_style` 的 -16/-20/-12 白名单、`shutdown` 的 1~3 秒钳制
12. C 组遗留：`workflow_run` 的 steps 字段表、`reverse_websocket query` 实为 `Network.getResponseBody`（且需 `request_id`）、
    `scan_crypto`/`detect_obfuscator` 的 `script_index` 声明未用、`workflow_run/get` 的 `file` 别名、
    `kernel_ipc_clear`/`kernel_scheme` 的**静默成功无校验**、`kernel_download` 的 download_id 形态
13. **幽灵工具**：`browser_debugger_pause` 有完整实现分支 + 命令行注册表项，但**没有 `添加工具JSON`** ⇒ 不进 tools/list，
    代理永远看不到（A 组 §表外发现；要么补注册，要么按"刻意禁用"写明理由）
14. 系统性观察：公共层参数几乎没写进 schema（`sync_wait` 322 个注册里声明 **0** 次、`async_only` 1 次、`browser_id` 1 次、
    `max_ms` 8 次）—— 值得单独一轮决定"是否统一声明"（它们由入口统一处理，声明后才可被发现）
'''

REPORT_SECTION = '''
## 145. 第125轮（续）："schema ↔ 实现一致性"全量审计 —— 105 处"代理看不到的参数/动作"落地

### 145.1 为什么要专门做这一层
前几轮修的是**行为**（工具会不会失败、会不会假成功）。本轮转向**可发现性**：代理只看得到 `tools/list` 里的
schema 与描述 —— 参数没声明，代理**根本不会想到传它**，于是"试很多次才成功"（用户原话）就成了必然。
于是按派发器文件分片派三个只读子代理，对 **322 个工具**做"schema 声明集 ↔ 实现读取集"的**机械双向 diff**
（含对 `MCP命令服务器.X(..., 参数JSON)` 委托的深度 4 传递闭包，避免把"由共享助手读取"误报成缺口）：

| 审计报告 | 范围 | 工具数 | 差异 | 其中 MISSING_IN_SCHEMA |
|----------|------|--------|------|------------------------|
| `_schema_audit_A.md` | Core | 162 | **45** | **29** |
| `_schema_audit_B.md` | Form/System/VIP | 93 | **31** | **2** |
| `_schema_audit_C.md` | Reverse/Kernel/Workflow | 65 | **29** | **7** |

### 145.2 本轮已修 28 项（B 组 15 + C 组 13），全部编译 0 警告
- **补上代理看不到的关键参数**：`browser_vip_enable_js_env.confirm`（install 类闸门的硬前置）、
  `browser_vip_touch_cancel.x/y`、`browser_reverse_instrument_script.confirm`（默认动作 install 的硬前置）；
- **必填表与实现对齐**：`browser_fill_attr_get`（去掉误标的 `attribute`）、`fill_attr_set`、`fill_select`、
  `set_preference`、`browser_vip_execute_js_context.code`；
- **补上"实现支持且实现自己推荐"的 action**：`kernel_events_all action=get`、`kernel_watch action=list`、
  `kernel_cdp_monitor action=list`、`kernel_download action=list`；
- **修正会误导推理的描述**：`get_global_cache_dir`（真值来源已改为按启动开关推导 + `cache_dir_source`）、
  `send_message`（主进程路径恒失败，实际广播到渲染进程）、`get_run_style`（"runtime_style 恒为 0"被实测推翻，
  本机为 1 谷歌）、`kernel_cdp_monitor.max`（默认 500→**200**）、`kernel_reactor`（把 `load_end` 当反例是错的，
  它确实是有效事件名且已实测落库）；
- **一处"静默假成功"改成可行动拒绝**：`browser_vip_fingerprint_ssl` 传未知 tls 值时，原先被静默回退成"不限制"
  却回 success（调用方以为已按版本限制）⇒ 现明确拒绝并列出支持值 `0/769/790/791/792`。

### 145.3 验收（`_audit/verify_schema_audit_fixes.py`，17/17）
分两层，缺一层都不算验证：
- **声明层**（读 `tools/list`）：`confirm`/`x,y` 是否真的出现在 schema；必填列表是否与实现守卫一致；
  三条描述是否已不含被实测推翻的旧结论；
- **行为层**（真机调用）：非法 `tls_min=999`/`tls_max=12345` 必须**失败且文案列出支持值**；
  `browser_fill_attr_get {selector}` 必须**成功**（修正前 schema 说必填、实现却允许省略 —— 自相矛盾）；
  `browser_vip_enable_js_env {enable:true}` 必须给出**点名 confirm 的可行动拒绝**（刻意闸门保留，不真启用）。
  另单独核验 `browser_reverse_instrument_script` 默认调用现在会回
  `install 需要显式确认 … 请传 confirm:true …`，即"参数不可见导致的必然失败"已变成"补一个参数即可成功"。

### 145.4 遗留（已入 `_audit/_gap_verified.md` 第四节，均有 file:line 证据）
A 组 Top 15（`touch_*` 的 `kernel`、`file_dialog`/`view_source` 的**描述与实现相反**、`dom_set_value` 的
`allow_empty` **死路**、`dom_query.index` **静默失效**、`browser_fingerprint` 19 个维度参数、debugger CDP 原生别名…）、
B 组 6 项、C 组 7 项，以及两条结构性发现：
① **幽灵工具 `browser_debugger_pause`**（有完整实现分支 + 命令行注册表项，却没有 `添加工具JSON` ⇒ 代理永远看不到）；
② **公共层参数几乎不声明**（`sync_wait` 322 个注册里 0 次、`async_only` 1 次、`browser_id` 1 次、`max_ms` 8 次）。

### 145.5 状态
工具 **322**；台账 **322/322 已测 = 319 通过 / 3 刻意设计**；快检 **56/56**；本轮新增验收
`verify_schema_audit_fixes.py` **17/17**、`verify_frames_parent.py` **11/11**、`verify_navigate_request.py` **12/12**、
`verify_menu_alias.py` **12/12**、`verify_network_body.py` **16/16**；编译 0 警告；卫生扫描**全零**。
'''

# 注: 本字面量内不含三个连续双引号


def main():
    gtxt = io.open(GAP, encoding='utf-8').read()
    if '## 四、"schema ↔ 实现一致性"专项审计' in gtxt:
        print('gap 文件已有该节, 跳过')
    else:
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(gtxt.rstrip('\n') + '\n' + GAP_SECTION)
        print('已追加 _gap_verified.md 第四节 (%d 字符)' % len(GAP_SECTION))
    raw = open(REPORT, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf') and b'\r\n' not in raw
    text = raw.decode('utf-8')
    assert '## 144.' in text, '章节 144 应已存在'
    if '## 145.' in text:
        assert '--replace' in sys.argv
        text = text[:text.index('## 145.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + REPORT_SECTION
    if '--apply' in sys.argv:
        with io.open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('报告: %d -> %d 字符' % (len(raw.decode('utf-8')), len(out)))
    else:
        print('[dry-run] 报告将写入 %d 字符' % len(REPORT_SECTION))


main()
