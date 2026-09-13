# MCP 功能逐个测试台账

> 由 `_audit/tool_ledger.py` 逐条追加。一次只测一个功能，跨轮累积，不重复测。

| 时间 | 轮次 | 工具 | 状态 | 耗时 | 类别 | 失败性质 | 说明 |
|---|---|---|---|---|---|---|---|
| 09-13 01:26 | 1 | `browser_navigate` | pass | 0.83s | OK |  | 等待条件满足: load_end → https://example.com/ |
| 09-13 01:26 | 1 | `browser_get_url` | pass | 0.01s | OK |  | https://example.com/ |
| 09-13 01:26 | 1 | `browser_get_title` | pass | 0.01s | OK |  | Example Domain |
| 09-13 01:26 | 1 | `browser_back` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"已后退"} |
| 09-13 01:26 | 1 | `browser_forward` | fail | 0.02s | ERR_WEAK | OTHER | 无法前进 — 无导航历史 / 当前页面没有可前进的历史记录 |
| 09-13 01:26 | 1 | `browser_reload` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_26342265_84320_36","message":"页面已刷新 / 等待载入完成, 通过mcp_res |
| 09-13 01:26 | 1 | `browser_stop` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"加载已停止"} |
| 09-13 01:26 | 1 | `browser_execute_js` | fail | 0.01s | ERR_GOOD | OTHER | 缺少参数: 请提供 code(JS代码字符串) 或 file(JS文件路径) |
| 09-13 01:26 | 1 | `browser_evaluate` | fail | 0.00s | ERR_GOOD | OTHER | 缺少参数: 请提供 code(JS代码字符串) 或 file(JS文件路径) |
| 09-13 01:26 | 1 | `browser_get_source` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_26342390_40293_37","message":"源码获取已提交(max=524288)","pol |
| 09-13 01:28 | 2 | `browser_get_text` | pass | 25.65s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_26427468_44331_39","message":"全文获取已提交","poll_hint":"用 m |
| 09-13 01:28 | 2 | `browser_open_devtools` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"DevTools已打开"} |
| 09-13 01:28 | 2 | `browser_close_devtools` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"DevTools已关闭"} |
| 09-13 01:28 | 2 | `browser_create` | pass | 0.34s | OK |  | {"id":"1","success":true,"message":"浏览器已创建: about:blank / 通过 browser_list 查看详情"} |
| 09-13 01:28 | 2 | `browser_list` | pass | 0.00s | OK |  | {"id":"1","success":true,"browsers":[{"id":1,"url":"http://127.0.0.1:9222/"},{"id":3,"url":"about:blank"},{"id |
| 09-13 01:28 | 2 | `browser_set_zoom` | fail | 0.01s | ERR_GOOD | OTHER | level 不是有效数字: mcp_probe / 请传 0~10 的数字, 如 1.0 / 1.5 / 0.8 (0=复位默认100%) |
| 09-13 01:28 | 2 | `browser_get_zoom` | pass | 0.01s | OK |  | {"success":true,"zoom_level":"0"} |
| 09-13 01:28 | 2 | `browser_find` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"查找: mcp-probe"} |
| 09-13 01:28 | 2 | `browser_stop_find` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"查找已停止"} |
| 09-13 01:28 | 2 | `browser_mouse_click` | pass | 8.11s | OK |  | {"id":"1","success":true,"message":"VIP点击 (10,10) / ⚠ 内核级鼠标注入实测会使 CDP 通道失效(CDP 优先工具随后退化为原生路径, 每次白等约10秒且部分返回 nu |
| 09-13 01:28 | 2 | `browser_mouse_move` | pass | 8.03s | OK |  | {"id":"1","success":true,"message":"VIP鼠标移动到 (10,10) / ⚠ 本工具走**内核级鼠标注入**, 实测该调用会使 CDP 通道失效: 之后 browser_dom_que |
| 09-13 01:28 | 2 | `browser_mouse_wheel` | fail | 0.01s | ERR_GOOD | OTHER | 必须提供 delta_y 或 delta_x (滚动量, 正数向下/向右) / 省略会造成滚动 0 像素却报成功 |
| 09-13 01:28 | 2 | `browser_key_event` | pass | 0.08s | OK |  | {"id":"1","success":true,"message":"VIP单击 key_code=1"} |
| 09-13 01:28 | 2 | `browser_print` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"打印已触发"} |
| 09-13 01:28 | 2 | `browser_print_to_pdf` | fail | 0.02s | ERR_GOOD | OTHER | 文件已存在: C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp\_int\AI-Fbowser-Mcp\debug\x64\linker\ |
| 09-13 01:28 | 2 | `browser_get_cookies` | pass | 0.01s | OK |  | {"id":"1","success":true,"_sync_waited":true,"cookies":[],"message":"[]"} |
| 09-13 01:28 | 2 | `browser_set_cookie` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"Cookie已设置: mcp_probe"} |
| 09-13 01:28 | 2 | `browser_delete_cookies` | fail | 0.02s | ERR_GOOD | OTHER | 此操作将清除所有域名下所有Cookie, 请设置 confirm: true 以确认操作 |
| 09-13 01:28 | 2 | `browser_clear_cache` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_26444421_11312_41","message":"全局缓存清理已提交, 通过mcp_result查询 |
| 09-13 01:28 | 2 | `browser_clear_cache_browser` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_26444453_88381_42","message":"浏览器缓存清理已提交, 通过mcp_result查 |
| 09-13 01:28 | 2 | `browser_cache_dir` | pass | 0.01s | OK |  | {"success":true,"cache_dir":"C:\\Users\\cxzxc\\Desktop\\MCP源码\\ai-browser-mcp\\CEFbro\\AI-Fbowser-Mcp\\_int\\A |
| 09-13 01:28 | 2 | `browser_set_mute` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"静音(持久): 0"} |
| 09-13 01:28 | 2 | `browser_is_muted` | pass | 0.02s | OK |  | {"success":true,"muted":false} |
| 09-13 01:39 | 3 | `browser_is_loading` | pass | 0.01s | OK |  | {"success":true,"loading":false} |
| 09-13 01:39 | 3 | `browser_can_navigate` | pass | 0.01s | OK |  | {"success":true,"can_go_back":true,"can_go_forward":false} |
| 09-13 01:39 | 3 | `browser_get_id` | pass | 0.01s | OK |  | {"success":true,"id":1} |
| 09-13 01:39 | 3 | `browser_compress_memory` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"内存已压缩清理"} |
| 09-13 01:39 | 3 | `browser_fbro_version` | pass | 0.01s | OK |  | {"success":true,"fbro_version":"5.36.4101"} |
| 09-13 01:39 | 3 | `browser_meta` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"machine_code":"6E639C75-3F365F65-E518A717-3E194FB8-83FC4C02-7150F5A1-5BA7769 |
| 09-13 01:39 | 3 | `browser_set_proxy` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"S5代理已设置: mcp_probe / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 |
| 09-13 01:39 | 3 | `browser_clear_proxy` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"S5代理已清除 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 01:39 | 3 | `browser_start_download` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"下载已触发: https://example.com"} |
| 09-13 01:39 | 3 | `browser_download_image` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_27122609_43899_17","message":"图片下载已提交, 通过mcp_result查询", |
| 09-13 01:39 | 3 | `browser_edit_undo` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"撤销成功"} |
| 09-13 01:39 | 3 | `browser_edit_redo` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"恢复成功"} |
| 09-13 01:39 | 3 | `browser_edit_cut` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"剪切成功"} |
| 09-13 01:39 | 3 | `browser_edit_copy` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"复制成功"} |
| 09-13 01:39 | 3 | `browser_edit_paste` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"粘贴成功"} |
| 09-13 01:39 | 3 | `browser_edit_delete` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"删除成功"} |
| 09-13 01:39 | 3 | `browser_edit_select_all` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"全选成功"} |
| 09-13 01:39 | 3 | `browser_get_frames` | pass | 0.01s | OK |  | {"id":"1","success":true,"frames":[{"id":"6-534761DF5E9D8934747C9F5912C9002E","name":"","is_main":true}]} |
| 09-13 01:39 | 3 | `browser_frame_names` | pass | 0.01s | OK |  | {"id":"1","success":true,"names":[""]} |
| 09-13 01:39 | 3 | `browser_frame_by_name` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"found":false}} |
| 09-13 01:39 | 3 | `browser_get_focused_frame` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"url":"https://example.com/?cm=1789234782","name":"","frame_id":"6-534761DF5E |
| 09-13 01:39 | 3 | `browser_get_window_handle` | pass | 0.01s | OK |  | {"success":true,"hwnd":"2952610"} |
| 09-13 01:39 | 3 | `browser_set_focus` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"焦点已失去"} |
| 09-13 01:39 | 3 | `browser_set_auto_resize` | fail | 0.00s | ERR_GOOD | CAPABILITY | ⛔ 嵌入式GUI浏览器不支持 set_auto_resize / 尺寸由主窗口 adjust_layout 管理 |
| 09-13 01:39 | 3 | `browser_restore_gui` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"已请求恢复GUI布局与欢迎页 / UI线程将在800ms内执行"} |
| 09-13 01:39 | 3 | `browser_move_window` | fail | 0.02s | ERR_GOOD | CAPABILITY | ⛔ 嵌入式GUI浏览器不支持 move_window / 窗口尺寸由主窗口自动管理 |
| 09-13 01:39 | 3 | `browser_dom_query` | fail | 0.03s | ERR_WEAK | CAPABILITY | 元素不存在或取不到值: #mcp-probe-nonexistent / 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在 |
| 09-13 02:02 | 4 | `browser_dom_click` | fail | 0.02s | ERR_GOOD | PREREQ | element not found: #mcp-probe-nonexistent / 该选择器在当前页面上匹配到 0 个元素 / 建议: 先用 browser_snapshot 或 browser_get_forms  |
| 09-13 02:02 | 4 | `browser_dom_set_value` | fail | 0.03s | ERR_WEAK | CAPABILITY | 元素不存在或取不到值: #mcp-probe-nonexistent / 设置值未执行 / 建议: 先用 browser_snapshot 或 browser_get_forms 确认元素存在 |
| 09-13 02:02 | 4 | `browser_dom_get_html` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_28495625_64248_18","message":"HTML获取(原生)已提交","poll_hint |
| 09-13 02:02 | 4 | `browser_dom_rect` | fail | 0.02s | ERR_WEAK | CAPABILITY | 元素不存在或取不到值: #mcp-probe-nonexistent / 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在 |
| 09-13 02:02 | 4 | `browser_dom_inner_html` | fail | 0.02s | ERR_WEAK | CAPABILITY | 元素不存在或取不到值: #mcp-probe-nonexistent / 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在 |
| 09-13 02:02 | 4 | `browser_dom_set_html` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_28495750_80338_19","message":"DOM innerHTML已提交, 通过mcp_r |
| 09-13 02:02 | 4 | `browser_dom_checked` | fail | 0.03s | ERR_WEAK | CAPABILITY | 元素不存在或取不到值: #mcp-probe-nonexistent / 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在 |
| 09-13 02:02 | 4 | `browser_dom_selected` | fail | 0.03s | ERR_WEAK | CAPABILITY | 元素不存在或取不到值: #mcp-probe-nonexistent / 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在 |
| 09-13 02:02 | 4 | `browser_dom_select` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_28495875_14460_20","message":"DOM select已提交, 通过mcp_resu |
| 09-13 02:02 | 4 | `browser_extract` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_28495906_60770_21","message":"链接提取已提交","poll_hint":"用 m |
| 09-13 02:02 | 4 | `browser_scrape` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_28495937_32617_22","message":"爬虫任务已提交: https://example. |
| 09-13 02:02 | 4 | `browser_console_eval` | pass | 0.02s | OK |  | 1 |
| 09-13 02:02 | 4 | `browser_fingerprint` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"Canvas指纹已随机化 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 brows |
| 09-13 02:02 | 4 | `browser_intercept` | fail | 0.01s | ERR_GOOD | TARGET | 参数 url 不能为空 |
| 09-13 02:02 | 4 | `browser_screenshot` | pass | 0.21s | OK |  | data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA9gAAALBCAIAAAAs5p7BAAAgAElEQVR4nO3df5RWdYH48WcEeXwoHHFwHEnCzGbM |
| 09-13 02:03 | 4 | `browser_collect` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"scenario":"reverse_analyze","tip":"navigate 后 browser_network list + browser |
| 09-13 02:03 | 4 | `browser_network` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"network_enabled":true,"network_detail":true,"network_logs":[{"type":"res","u |
| 09-13 02:03 | 4 | `browser_status` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"is_popup":false,"has_document":true,"can_go_back":false,"can_go_forward":fal |
| 09-13 02:03 | 4 | `browser_window_info` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"title":"AI浏览器 MCP Server — Windows 浏览器自动化 MCP / 265 工具 - Chromium","hwnd":62 |
| 09-13 02:03 | 5 | `browser_view_source` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_28544890_46684_1","message":"源码获取已提交(max=524288)","poll |
| 09-13 02:03 | 5 | `browser_inject` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_28544921_85774_2","message":"JS注入已提交, 通过mcp_result查询"," |
| 09-13 02:03 | 5 | `browser_wait` | fail | 0.01s | ERR_GOOD | TARGET | value 不能为空: what=selector 需要指定等待目标值 |
| 09-13 02:03 | 5 | `browser_cdp` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:mcp_probe"}

[task_id: 1] |
| 09-13 02:03 | 5 | `browser_debugger_enable` | pass | 0.02s | OK |  | {"debuggerId":"-3691281979114842355.9193214708088963779"} |
| 09-13 02:03 | 5 | `browser_debugger_resume` | fail | 0.01s | ERR_GOOD | PREREQ | 页面未处于暂停状态, 无需恢复 / 请先 debugger_flow 或 debugger_enable + 断点 + wait_paused |
| 09-13 02:03 | 5 | `browser_debugger_step_over` | fail | 0.00s | ERR_GOOD | PREREQ | 页面未处于暂停状态 / 请先 debugger_flow 或 debugger_enable + 断点 + wait_paused |
| 09-13 02:03 | 5 | `browser_debugger_step_into` | fail | 0.01s | ERR_GOOD | PREREQ | 页面未处于暂停状态 / 请先 debugger_flow 或 debugger_enable + 断点 + wait_paused |
| 09-13 02:03 | 5 | `browser_debugger_step_out` | fail | 0.01s | ERR_GOOD | PREREQ | 页面未处于暂停状态 / 请先 debugger_flow 或 debugger_enable + 断点 + wait_paused |
| 09-13 02:03 | 5 | `browser_debugger_stack` | fail | 0.01s | ERR_GOOD | PREREQ | 页面未处于暂停状态 / 请先 debugger_flow 或 debugger_enable + 断点 + wait_paused |
| 09-13 02:03 | 5 | `browser_debugger_set_breakpoint` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_result":"{\"breakpointId\":\"2:0:0:https://example.com\", |
| 09-13 02:03 | 5 | `browser_debugger_evaluate` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"ok":false,"error":""}} |
| 09-13 02:04 | 5 | `browser_debugger_wait_paused` | fail | 30.11s | ERR_GOOD | OTHER | 等待 Debugger.paused 超时(30000ms) / 流程: debugger_enable → set_breakpoint → navigate |
| 09-13 02:04 | 5 | `browser_debugger_last_paused` | fail | 0.01s | ERR_GOOD | PREREQ | 尚无 Debugger.paused 事件 / 请先 enable + 断点 + 触发暂停 |
| 09-13 02:04 | 5 | `browser_debugger_inspect` | fail | 0.01s | ERR_GOOD | PREREQ | 缺少 call_frame_id / 请先 browser_debugger_wait_paused 或 browser_debugger_last_paused |
| 09-13 02:04 | 5 | `browser_debugger_flow` | fail | 40.01s | TIMEOUT | OTHER | timed out |
| 09-13 02:04 | 5 | `browser_debugger_script_source` | fail | 0.00s | ERR_GOOD | PREREQ | 未处于暂停状态且未指定 script_id / 请先 debugger_flow / debugger_enable + 断点 + wait_paused |
| 09-13 02:05 | 6 | `browser_debugger_resume` | fail | 0.00s | ERR_GOOD | STATE | 页面未处于暂停状态, 无需恢复 / 请先 debugger_flow 或 debugger_enable + 断点 + wait_paused |
| 09-13 02:05 | 7 | `browser_debugger_wait_paused` | fail(wedge) | 15.00s | TIMEOUT | OTHER | timed out |
| 09-13 02:06 | 8 | `browser_debugger_flow` | fail(wedge) | 15.00s | TIMEOUT | OTHER | timed out |
| 09-13 02:06 | 9 | `browser_debugger_wait_paused` | fail | 15.01s | TIMEOUT | OTHER | timed out |
| 09-13 02:07 | 10 | `browser_debugger_flow` | fail | 15.01s | TIMEOUT | OTHER | timed out |
| 09-13 02:08 | 11 | `browser_debugger_auto` | fail | 15.02s | TIMEOUT | OTHER | timed out |
| 09-13 02:08 | 11 | `browser_network_body` | fail | 0.02s | ERR_GOOD | PARAM | 非法 CDP request_id: mcp_probe / CDP 请求标识为数字串(形如 1000012345.5) / 如何取得有效值: ① browser_kernel_cdp_monitor action=ad |
| 09-13 02:08 | 11 | `browser_touch_press` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"触摸按下"} |
| 09-13 02:08 | 11 | `browser_touch_release` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"触摸放开"} |
| 09-13 02:08 | 11 | `browser_touch_move` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"触摸移动"} |
| 09-13 02:08 | 11 | `browser_base64_encode` | pass | 0.00s | OK |  | {"success":true,"base64":"bWNwX3Byb2Jl"} |
| 09-13 02:08 | 11 | `browser_base64_decode` | fail | 0.00s | ERR_GOOD | OTHER | Base64解码失败 |
| 09-13 02:08 | 11 | `browser_uri_encode` | pass | 0.01s | OK |  | {"success":true,"encoded":"mcp_probe"} |
| 09-13 02:08 | 11 | `browser_uri_decode` | pass | 0.01s | OK |  | {"success":true,"decoded":"mcp_probe"} |
| 09-13 02:08 | 11 | `browser_get_window_title` | pass | 0.01s | OK |  | {"success":true,"title":"AI浏览器 MCP Server — Windows 浏览器自动化 MCP / 265 工具 - Chromium"} |
| 09-13 02:08 | 11 | `browser_set_parent` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"父窗口已设置"} |
| 09-13 02:08 | 11 | `browser_get_main_browser` | pass | 0.01s | OK |  | {"success":true,"opener_hwnd":"0"} |
| 09-13 02:08 | 11 | `browser_is_same` | pass | 0.02s | OK |  | {"success":true,"same":true} |
| 09-13 02:08 | 11 | `browser_is_view` | pass | 0.01s | OK |  | {"success":true,"is_view":false} |
| 09-13 02:08 | 11 | `browser_user_tags` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"tags":[""]}} |
| 09-13 02:08 | 11 | `browser_find_by_tag` | fail | 0.00s | ERR_WEAK | TARGET | 未找到标识为: mcp_probe 的浏览器 / 可能原因: 该标识未被 browser_user_tags 设置过, 或浏览器已关闭 / 建议: 先用 browser_list 查看现有浏览器及其 id |
| 09-13 02:08 | 11 | `browser_find_by_hwnd` | fail | 0.01s | ERR_GOOD | TARGET | 未找到窗口句柄为 1 的浏览器 |
| 09-13 02:11 | 12 | `browser_request_context` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"has_context":true}} |
| 09-13 02:11 | 12 | `browser_file_dialog` | fail | 0.01s | ERR_GOOD | OTHER | 文件对话框已改为程序化选择(不弹窗口) / 请传 path 参数指定目标文件路径 |
| 09-13 02:11 | 12 | `browser_send_message` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"已向全部渲染进程发送消息"} |
| 09-13 02:11 | 12 | `browser_ipc_send_all` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"已向全部渲染进程发送消息"} |
| 09-13 02:11 | 12 | `browser_ipc_send_to` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"已向进程 1 发送消息"} |
| 09-13 02:11 | 12 | `browser_ipc_renderer_count` | pass | 0.01s | OK |  | {"success":true,"count":3} |
| 09-13 02:11 | 12 | `browser_ipc_renderer_ids` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"ids":[9748,4368,4368]}} |
| 09-13 02:11 | 12 | `browser_create_url_request` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_28996937_57695_16","message":"URL请求已提交, 通过mcp_result查询结 |
| 09-13 02:11 | 12 | `browser_vip_websocket_intercept` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"WebSocket拦截已启用"} |
| 09-13 02:11 | 12 | `browser_fill_set_value` | fail | 0.02s | ERR_GOOD | PREREQ | 设置值未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent / 建议: 先用 browser_snapshot 或 browser_get_forms 获取页面可用元素/选择器 |
| 09-13 02:11 | 12 | `browser_fill_click` | fail | 0.01s | ERR_GOOD | PREREQ | 点击未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent / 建议: 先用 browser_snapshot 或 browser_get_forms 获取页面可用元素/选择器; |
| 09-13 02:11 | 12 | `browser_fill_focus` | fail | 0.01s | ERR_GOOD | PREREQ | 设置焦点未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent / 建议: 先用 browser_snapshot 或 browser_get_forms 获取页面可用元素/选择 |
| 09-13 02:11 | 12 | `browser_fill_scroll` | fail | 0.03s | ERR_GOOD | PREREQ | 滚动到元素未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent / 建议: 先用 browser_snapshot 或 browser_get_forms 获取页面可用元素/选 |
| 09-13 02:11 | 12 | `browser_fill_exists` | pass | 0.03s | OK |  | 0 |
| 09-13 02:11 | 12 | `browser_fill_attr_get` | fail | 0.01s | ERR_WEAK | TARGET | 元素不存在或取不到值: #mcp-probe-nonexistent / 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在 |
| 09-13 02:11 | 13 | `browser_fill_attr_set` | fail | 0.01s | ERR_GOOD | TARGET | attribute 不能为空 / 如 style / data-* / aria-* |
| 09-13 02:11 | 13 | `browser_fill_trigger` | fail | 0.03s | ERR_GOOD | PREREQ | 触发事件未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent / 建议: 先用 browser_snapshot 或 browser_get_forms 获取页面可用元素/选择 |
| 09-13 02:11 | 13 | `browser_fill_select` | fail | 0.03s | ERR_GOOD | PREREQ | 设置select选中项未执行: 选择器在当前页面匹配到 0 个元素 -> #mcp-probe-nonexistent / 建议: 先用 browser_snapshot 或 browser_get_forms 获取页面 |
| 09-13 02:11 | 13 | `mcp_status` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"server":"AI浏览器 MCP Server","version":"3.1.0","port":9222,"browser_count":1," |
| 09-13 02:11 | 13 | `mcp_help` | pass | 0.00s | OK |  | {"success":true,"help":"=== AI浏览器 MCP v3.1.0 工具列表 ===\r\n\r\n【导航】navigate(url) get_url get_title back forward  |
| 09-13 02:11 | 13 | `mcp_result` | fail | 0.00s | ERR_GOOD | TARGET | 未找到任务结果: mcp_probe / 可能原因: ①任务仍在执行(2-5秒后重试) ②request_id拼写错误 ③任务已过期被清理 / 💡大多数工具已默认sync-wait(直接返回结果), 无需手动mcp_re |
| 09-13 02:11 | 13 | `ping` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"pong":"29009015","browsers":1,"version":"3.1.0"}} |
| 09-13 02:11 | 13 | `batch` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"total":0,"success_count":0,"failure_count":0,"results":[]}} |
| 09-13 02:11 | 13 | `workflow_list` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"workflows":["automation_form","debugger_breakpoint","debugger_full","hello", |
| 09-13 02:11 | 13 | `workflow_get` | fail | 0.02s | ERR_WEAK | TARGET | 工作流不存在: mcp_probe / 建议: 先用 workflow_list 列出可用工作流名(不含 .json 后缀) |
| 09-13 02:11 | 13 | `workflow_run` | fail | 0.00s | ERR_WEAK | OTHER | 工作流缺少 steps 数组 / steps 须为 JSON 数组, 每项形如 {"tool":"browser_navigate","args":{"url":"https://example.com"}} / 也可用 |
| 09-13 02:11 | 13 | `workflow_stop` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"没有正在运行的工作流, 无需停止"} |
| 09-13 02:11 | 13 | `browser_kernel_cert` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"ignore_errors":false,"errors":"[]"}} |
| 09-13 02:11 | 14 | `browser_kernel_auth` | fail | 0.01s | ERR_GOOD | TARGET | host 不能为空 / 例: example.com |
| 09-13 02:11 | 14 | `browser_kernel_download` | fail | 0.02s | ERR_GOOD | OTHER | url 或 download_id 必填其一 / 先用 action=list 查看进行中的下载 |
| 09-13 02:11 | 14 | `browser_kernel_scheme` | fail | 0.02s | ERR_GOOD | TARGET | domain 不能为空 / 访问形式: mcp://域名/任意路径 |
| 09-13 02:11 | 14 | `browser_kernel_menu` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"已恢复右键快捷菜单"} |
| 09-13 02:11 | 14 | `browser_kernel_reverse_probe` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"动态探针已注入(五维API插桩): __ok / 数据在 window.__MCP_PROBE__, 用 action=get 取回"} |
| 09-13 02:11 | 14 | `browser_kernel_reverse_trace` | fail | 0.01s | ERR_GOOD | TARGET | targets 不能为空 / 例: ["window.fetch","crypto.subtle.encrypt"] |
| 09-13 02:11 | 14 | `browser_kernel_reverse_algo` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"算法Hook已启动(CryptoJS+哈希+base64+WebCrypto) / 数据在 window.__MCP_ALGO_LOG__"} |
| 09-13 02:11 | 14 | `browser_kernel_reverse_functions` | fail | 0.02s | ERR_WEAK | OTHER | 函数提取失败: {"error":"JS异常:Uncaught"} / 页面可能因 CSP 拒绝脚本注入, 或已跨域跳转 |
| 09-13 02:11 | 14 | `browser_kernel_reverse_sources` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"max_len":20000,"scripts":"[]"}} |
| 09-13 02:11 | 14 | `browser_kernel_reverse_watch_global` | fail | 0.01s | ERR_GOOD | TARGET | names 不能为空 / 例: ["token","sign","session"] |
| 09-13 02:11 | 14 | `browser_kernel_ipc_queue` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"queue":"[]"}} |
| 09-13 02:11 | 14 | `browser_kernel_ipc_clear` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"queue":"[]"}} |
| 09-13 02:11 | 14 | `browser_kernel_cdp_monitor` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"CDP监控已添加: * (max=200)"} |
| 09-13 02:25 | 15 | `browser_kernel_reactor` | fail | 0.02s | ERR_GOOD | TARGET | event 不能为空 / 例: load_end / navigate / url_changed / * |
| 09-13 02:25 | 15 | `browser_kernel_watch` | fail | 0.01s | ERR_GOOD | TARGET | expression 不能为空 / 例: document.title / window.__token |
| 09-13 02:25 | 15 | `browser_kernel_events_all` | fail | 0.02s | ERR_WEAK | OTHER | action 须为 enable/disable |
| 09-13 02:25 | 15 | `browser_vip_clear_s5_proxy` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"S5代理已清除 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 02:25 | 15 | `browser_vip_mouse_click` | pass | 0.07s | OK |  | {"id":"1","success":true,"message":"VIP鼠标点击"} |
| 09-13 02:25 | 15 | `browser_vip_mouse_move` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"VIP鼠标移动"} |
| 09-13 02:26 | 15 | `browser_vip_mouse_wheel` | fail | 0.02s | ERR_GOOD | GUARD | 必须提供 delta_y 或 delta_x (滚动量, 正值向下/向右) / 省略会造成滚动 0 像素却报成功 |
| 09-13 02:26 | 15 | `browser_vip_key_press` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"VIP键盘按下: key_code=1"} |
| 09-13 02:26 | 15 | `browser_vip_key_release` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"VIP键盘放开: key_code=1"} |
| 09-13 02:26 | 15 | `browser_vip_key_click` | pass | 0.08s | OK |  | {"id":"1","success":true,"message":"VIP键盘单击: key_code=1"} |
| 09-13 02:26 | 15 | `browser_refresh_cookies` | pass | 1.63s | OK |  | {"id":"1","success":true,"message":"Cookie已刷新到磁盘"} |
| 09-13 02:29 | 16 | `browser_reverse_network_conditions` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Network.emulateNetworkConditions","cdp_result":" |
| 09-13 02:29 | 17 | `browser_reverse_emulate_focus` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Emulation.setFocusEmulationEnabled","cdp_result" |
| 09-13 02:29 | 18 | `browser_reverse_cookie_cdp` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Storage.getCookies","cdp_result":"{\"cookies\":[ |
| 09-13 02:29 | 19 | `browser_reverse_css_coverage` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"CSS.startRuleUsageTracking","cdp_result":"{}","n |
| 09-13 02:29 | 20 | `browser_reverse_trace` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Tracing.start","cdp_result":"{}","note":"trace 已 |
| 09-13 02:29 | 21 | `browser_reverse_layer_tree` | pass | 0.04s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"LayerTree.enable","cdp_result":"{}","note":"合成层上 |
| 09-13 02:29 | 22 | `browser_reverse_input_cdp` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"已派发鼠标事件: type=mouseMoved @(0,0) button=left / type 支持 mouseMoved/mousePres |
| 09-13 02:29 | 23 | `browser_fingerprint_languages` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"语言指纹已恢复默认(传空文本) / 类库无单项复位API, 空文本由库内部按默认处理; 彻底复位请用 browser_fingerprint act |
| 09-13 02:29 | 24 | `browser_fingerprint_webgl_vendor` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"WebGL vendor已设置: mcp_probe / renderer 未提供, 由库内部决定 / 设置已应用! 注意: 指纹/代理/内核变更需 |
| 09-13 02:29 | 25 | `browser_font_randomize` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"字体枚举已随机化: count=0 / 宽偏移=1 / 高偏移=-2 / Canvas字体度量噪点=0.0444807275612659 / see |
| 09-13 02:40 | 26 | `browser_debugger_stack` | pass | 0.06s | OK |  | {"id":"1","success":true,"auto_prepared":"Debugger.pause(页面原本未暂停, 已自动启用调试器域并安排执行点制造暂停点; 用完请 browser_debugger_r |
| 09-13 02:40 | 27 | `browser_debugger_step_over` | pass | 0.04s | OK |  | {} |
| 09-13 02:40 | 28 | `browser_debugger_step_into` | pass | 0.01s | OK |  | {} |
| 09-13 02:41 | 29 | `browser_debugger_step_out` | pass | 0.17s | OK |  | {} |
| 09-13 02:41 | 30 | `browser_debugger_inspect` | pass | 0.18s | OK |  | {"id":"1","success":true,"auto_prepared":"Debugger.pause(页面原本未暂停, 已自动启用调试器域并安排执行点制造暂停点; 用完请 browser_debugger_r |
| 09-13 02:41 | 31 | `browser_debugger_last_paused` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"reason":"other","call_frame_id":"-5823230465752015470.1.0","functionName":"" |
| 09-13 02:41 | 32 | `browser_debugger_script_source` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"ok":true,"call_frame_id":"-5823230465752015470.1.0","scriptId":"6","url":"", |
| 09-13 02:41 | 33 | `browser_kernel_reverse_functions` | pass | 0.04s | OK |  | {"id":"1","success":true,"data":{"success":true,"max":500,"functions":"[{\"p\":\"window.alert\",\"n\":\"alert\ |
| 09-13 02:41 | 34 | `browser_reverse_detect_traps` | pass | 0.13s | OK |  | {"id":"1","success":true,"data":{"success":true,"tool":"browser_reverse_detect_traps","script_id":"5","script_ |
| 09-13 02:41 | 35 | `browser_execute_js` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"AI浏览器 MCP Server — Windows 浏览器自动化 MCP / 265 工具"} |
| 09-13 02:41 | 36 | `browser_evaluate` | pass | 0.05s | OK |  | AI浏览器 MCP Server — Windows 浏览器自动化 MCP / 265 工具 |
| 09-13 02:41 | 37 | `browser_base64_decode` | fail | 0.02s | ERR_GOOD | OTHER | Base64解码失败 |
| 09-13 02:41 | 38 | `browser_kernel_events_all` | fail | 0.02s | ERR_WEAK | OTHER | action 须为 enable/disable |
| 09-13 02:41 | 39 | `browser_set_zoom` | fail | 0.00s | ERR_GOOD | PARAM | level 不是有效数字: mcp_probe / 请传 0~10 的数字, 如 1.0 / 1.5 / 0.8 (0=复位默认100%) |
| 09-13 02:41 | 40 | `browser_print_to_pdf` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_30808031_70511_2","message":"PDF打印已提交, 通过mcp_result查询结果 |
| 09-13 02:41 | 41 | `workflow_run` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"workflow":"mcp_probe","success":true,"stopped":false,"total_steps":1,"succes |
| 09-13 02:41 | 42 | `browser_base64_decode` | pass | 0.00s | OK |  | {"success":true,"decoded":"hello"} |
| 09-13 02:41 | 43 | `browser_kernel_events_all` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"全事件流已关闭"} |
| 09-13 02:41 | 44 | `browser_set_zoom` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"缩放(持久): 1.0"} |
| 09-13 02:41 | 45 | `browser_mouse_wheel` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"滚轮 (100,100) delta:0,300 / 经 CDP 派发(不破坏 CDP 会话) / 如需内核级注入请传 kernel:true"} |
| 09-13 02:41 | 46 | `browser_kernel_download` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"note":"下载进度请用 browser_event 查询 download_progress; 暂停/恢复/取消经本队 |
| 09-13 02:41 | 47 | `browser_delete_cookies` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"Cookie已全部清除"} |
| 09-13 02:42 | 48 | `browser_get_all_cookies` | pass | 0.01s | OK |  | {"id":"1","success":true,"_sync_waited":true,"cookies":[],"message":"[]"} |
| 09-13 02:42 | 48 | `aliases` | pass | 0.01s | OK |  | {"success":true,"aliases":"快捷别名(browser_前缀可省略):\r\nnavigate get_url get_title back forward reload stop\r\neval |
| 09-13 02:42 | 48 | `browser_vip_disable_debugger` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"Debugger开关已设置 / 内核开关修改, 需要刷新页面生效 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 br |
| 09-13 02:42 | 48 | `browser_get_window_style` | pass | 0.01s | OK |  | {"success":true,"style":"382664704"} |
| 09-13 02:42 | 48 | `browser_set_window_style` | fail | 0.01s | ERR_GOOD | PARAM | 非法窗口属性类型(1) / 支持: -16(GWL_STYLE) / -20(GWL_EXSTYLE) / -12(GWL_ID) |
| 09-13 02:42 | 48 | `browser_get_run_style` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"window_style":382664704,"is_popup":false,"browser_id":1}} |
| 09-13 02:42 | 48 | `browser_get_global_cache_dir` | pass | 0.01s | OK |  | {"success":true,"global_cache_dir":"C:\\Users\\cxzxc\\Desktop\\MCP源码\\ai-browser-mcp\\CEFbro\\AI-Fbowser-Mcp\\ |
| 09-13 02:42 | 48 | `browser_get_process_type` | pass | 0.01s | OK |  | {"success":true,"process_type":"0"} |
| 09-13 02:42 | 48 | `browser_fingerprint_plugins` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"Plugins指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 brows |
| 09-13 02:42 | 48 | `browser_fingerprint_appname` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"AppName指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 brows |
| 09-13 02:42 | 48 | `browser_fingerprint_pixel_ratio` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"像素比指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_n |
| 09-13 02:42 | 48 | `browser_fingerprint_touch_enable` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"触摸事件指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_ |
| 09-13 02:42 | 48 | `browser_vip_set_css_version` | fail | 0.01s | ERR_GOOD | PARAM | version 必须为正整数 / 有效范围: 1-65535 |
| 09-13 02:43 | 49 | `browser_debugger_wait_paused` | fail | 15.01s | TIMEOUT | OTHER | [前置] browser_debugger_stack -> OK // timed out |
| 09-13 02:43 | 50 | `browser_vip_set_css_version` | fail | 0.01s | ERR_GOOD | PARAM | version 必须为正整数 / 有效范围: 1-65535 |
| 09-13 02:57 | 51 | `browser_debugger_wait_paused` | pass | 0.03s | OK |  | [前置] browser_debugger_stack -> OK // {"id":"1","success":true,"data":{"reason":"other","call_frame_id":"-42632 |
| 09-13 02:57 | 52 | `browser_reverse_network_conditions` | pass | 0.04s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Network.emulateNetworkConditions","cdp_result":" |
| 09-13 02:57 | 53 | `browser_reverse_get_possible_breakpoints` | pass | 0.04s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Debugger.getPossibleBreakpoints","cdp_result":"{ |
| 09-13 02:57 | 54 | `browser_reverse_compile_script` | pass | 0.06s | OK |  | {"id":"1","success":true,"auto_prepared":"Runtime.enable","data":{"success":true,"cdp_method":"Runtime.compile |
| 09-13 02:57 | 55 | `browser_fingerprint_languages` | fail | 0.01s | ERR_GOOD | TARGET | languages 不能为空, 例: zh-CN,zh,en / 恢复默认请传 reset:true |
| 09-13 02:57 | 56 | `browser_debugger_evaluate` | fail | 0.04s | ERR_GOOD | OTHER | {"code":-32000,"message":"Invalid call frame id"} |
| 09-13 02:57 | 57 | `browser_fingerprint_languages` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"已设置语言: zh-CN,zh,en / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 |
| 09-13 02:58 | 58 | `browser_vip_set_web_version` | fail | 0.01s | ERR_GOOD | PARAM | version 必须为正整数 / 有效范围: 1-65535 |
| 09-13 02:58 | 58 | `browser_vip_set_v8_version` | fail | 0.01s | ERR_GOOD | PARAM | version 必须为正整数 / 有效范围: 1-65535 |
| 09-13 02:58 | 58 | `browser_vip_send_devtools_msg` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"DevTools消息已发送"} |
| 09-13 02:58 | 58 | `browser_fingerprint_screen_xy` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"屏幕XY指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_ |
| 09-13 02:58 | 58 | `browser_vip_mouse_press` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"VIP鼠标按下"} |
| 09-13 02:59 | 58 | `browser_vip_mouse_release` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"VIP鼠标放开"} |
| 09-13 02:59 | 58 | `browser_vip_key_input` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"VIP输入字符"} |
| 09-13 02:59 | 58 | `browser_vip_key_type` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"VIP输入文本"} |
| 09-13 02:59 | 58 | `browser_popup_info` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"is_popup":false,"has_document":true,"is_loading":false,"id":1,"url":"http:// |
| 09-13 02:59 | 58 | `browser_loading_info` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"is_loading":false,"can_go_back":false,"can_go_forward":false,"is_popup":fals |
| 09-13 02:59 | 58 | `browser_cdp_call` | fail | 0.02s | ERR_GOOD | PARAM | 非法 CDP 方法名: mcp_probe / 规范格式为 域.方法, 例: Network.getResponseBody / Runtime.evaluate / Page.navigate / Debugger.e |
| 09-13 02:59 | 58 | `browser_cdp_event` | fail | 0.00s | ERR_WEAK | OTHER | 指定 event_name 或 event 参数，例如 Debugger.paused |
| 09-13 02:59 | 58 | `browser_vip_fingerprint_webrtc` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"WebRTC IP指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 bro |
| 09-13 02:59 | 58 | `browser_fingerprint_cookie_enabled` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"CookieEnabled指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 |
| 09-13 02:59 | 58 | `browser_fingerprint_java_enabled` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"JavaEnabled指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 b |
| 09-13 03:07 | 59 | `browser_vip_set_web_version` | fail | 0.02s | ERR_GOOD | OTHER | 内核版本须为116-135范围内的纯数字(官方API支持值) |
| 09-13 03:07 | 60 | `browser_vip_set_v8_version` | fail | 0.02s | ERR_GOOD | OTHER | 内核版本须为116-135范围内的纯数字(官方API支持值) |
| 09-13 03:07 | 61 | `browser_create` | pass | 0.38s | OK |  | {"id":"1","success":true,"message":"浏览器已创建: about:blank / 通过 browser_list 查看详情"} |
| 09-13 03:08 | 62 | `browser_vip_set_web_version` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"Web内核已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_n |
| 09-13 03:08 | 63 | `browser_vip_set_v8_version` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"V8内核已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 03:26 | 64 | `browser_fingerprint_online` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"OnLine指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browse |
| 09-13 03:26 | 64 | `browser_fingerprint_appcodename` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"AppCodeName指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 b |
| 09-13 03:26 | 64 | `browser_fingerprint_appversion` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"AppVersion指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 br |
| 09-13 03:26 | 64 | `browser_vip_enable_js_env` | fail | 0.01s | ERR_GOOD | OTHER | 启用 JS 执行环境需显式确认 / ⚠ 实测启用后会破坏本会话的 JS 通道: CDP 优先工具(browser_dom_query / browser_dom_rect / browser_get_text 等)会退化 |
| 09-13 03:26 | 64 | `browser_vip_get_js_env_ids` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"count":0,"ids":[]}} |
| 09-13 03:26 | 64 | `browser_vip_set_is_trusted` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"isTrusted已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 brows |
| 09-13 03:26 | 64 | `browser_vip_touch_cancel` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"触摸取消"} |
| 09-13 03:26 | 64 | `browser_vip_enable_inspector` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"监管者事件已设置"} |
| 09-13 03:26 | 64 | `browser_fingerprint_product_sub` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"ProductSub指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 br |
| 09-13 03:26 | 64 | `browser_fingerprint_vendor_sub` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"VendorSub指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 bro |
| 09-13 03:26 | 64 | `browser_vip_fingerprint_canvas_fixed` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"Canvas定值指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 brow |
| 09-13 03:26 | 65 | `browser_vip_touch_emulation` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"触摸模拟已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 03:37 | 66 | `browser_get_text` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"Example Domain\n\nThis domain is for use in documentation examples without |
| 09-13 03:37 | 67 | `browser_dom_inner_html` | fail | 0.02s | ERR_WEAK | TARGET | 元素不存在或取不到值: #mcp-probe-nonexistent / 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在 |
| 09-13 03:37 | 68 | `browser_get_source` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_34188390_81846_16","message":"源码获取已提交(max=524288)","pol |
| 09-13 03:38 | 69 | `browser_vip_fingerprint_canvas_font` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"Canvas字体指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需刷新页面生效 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面 |
| 09-13 03:38 | 69 | `browser_vip_fingerprint_webgl_fixed` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"WebGL定值指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 brows |
| 09-13 03:38 | 69 | `browser_vip_fingerprint_audio_fixed` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"Audio定值指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 brows |
| 09-13 03:38 | 69 | `browser_vip_disable_console` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"Console/Performance禁用已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_re |
| 09-13 03:38 | 69 | `browser_vip_fingerprint_rect` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"Rect指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_ |
| 09-13 03:38 | 69 | `browser_vip_fingerprint_timezone` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"时区指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 03:38 | 69 | `browser_vip_fingerprint_geolocation` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"定位指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 03:38 | 69 | `browser_vip_fingerprint_ssl` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"SSL加密套件已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser |
| 09-13 03:38 | 69 | `browser_vip_fingerprint_canvas` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"Canvas指纹已设置, 随机值: / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或  |
| 09-13 03:47 | 70 | `browser_vip_fingerprint_webgl` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"WebGL指纹已设置, 随机值: / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 b |
| 09-13 03:47 | 70 | `browser_vip_fingerprint_audio` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"Audio指纹已设置, 随机值: / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 b |
| 09-13 03:47 | 70 | `browser_vip_fingerprint_font` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"CSS字体指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser |
| 09-13 03:47 | 70 | `browser_vip_fingerprint_viewport` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"Viewport已虚拟 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browse |
| 09-13 03:47 | 70 | `browser_vip_fingerprint_screen` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"屏幕分辨率指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser |
| 09-13 03:47 | 70 | `browser_vip_fingerprint_hardware` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"硬件指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 03:47 | 70 | `browser_vip_fingerprint_product` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"产品标识指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_ |
| 09-13 03:57 | 71 | `browser_vip_fingerprint_battery` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"电池指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 03:57 | 71 | `browser_vip_fingerprint_media_devices` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"媒体设备指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_ |
| 09-13 03:57 | 71 | `browser_vip_load_extension` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"CRX插件包已提交安装: C:\\Windows\\win.ini"} |
| 09-13 03:57 | 71 | `browser_vip_unload_extension` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"插件已卸载: mcp_probe"} |
| 09-13 03:57 | 71 | `browser_vip_extension_info` | pass | 0.00s | OK |  | {"id":"1","success":true,"data":{"id":"mcp_probe","path":"","url":""}} |
| 09-13 03:58 | 72 | `browser_vip_execute_js_context` | fail | 0.01s | ERR_GOOD | OTHER | 需要code参数 |
| 09-13 03:58 | 72 | `browser_vip_enable_devtools_observer` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"DevTools消息监听已关闭 / ⚠ 全部 CDP 类工具(debugger_*/cdp_*/reverse CDP类)已随之失效, 需重启进程才 |
| 09-13 03:58 | 72 | `browser_vip_dom_get_document` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_35427890_34105_16","message":"DOM文档已提交枚举, 通过mcp_result查 |
| 09-13 03:58 | 72 | `browser_vip_dom_search` | fail | 0.02s | ERR_GOOD | OTHER | 需要query或search_id参数 |
| 09-13 03:58 | 72 | `browser_get_extra_data` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"UserFlag":""}} |
| 09-13 04:05 | 73 | `browser_vip_enable_devtools_observer` | fail | 0.01s | ERR_GOOD | OTHER | enable 取值无法识别: mcp_probe / 只接受: 字符串 true/false/1/0/on/off, 或布尔 true / **不接受缺省**(缺省会被当成关闭) / 无法识别的取值一律拒绝, 不落进'关 |
| 09-13 04:05 | 74 | `browser_vip_enable_inspector` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"监管者事件已设置"} |
| 09-13 04:05 | 75 | `browser_vip_enable_devtools_observer` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"DevTools消息监听已启用(MCP观察者)"} |
| 09-13 04:07 | 76 | `browser_fingerprint_ua` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"UA完整指纹已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_ |
| 09-13 04:07 | 76 | `browser_vip_orientation` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"屏幕方向已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 04:07 | 76 | `browser_reverse_hook` | fail | 0.02s | ERR_GOOD | TARGET | target 不能为空 / 指定函数名/URL正则/选择器 |
| 09-13 04:07 | 76 | `browser_reverse_strings` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"count":1,"results":[{"v":"claude_desktop_config","l":21,"si":0}]}} |
| 09-13 04:07 | 76 | `browser_reverse_verify` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_35958109_78476_1","message":"验证已提交, 通过mcp_result查询","es |
| 09-13 04:07 | 76 | `browser_reverse_cookie_sources` | pass | 0.00s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_35958140_77461_2","message":"Cookie归因已提交(原生Cookie API)  |
| 09-13 04:07 | 76 | `browser_reverse_env` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"message":"原生环境数据 + JS指纹任务已提交","task_id":"task_35958171_66143_ |
| 09-13 04:07 | 76 | `browser_reverse_instrument` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_35958250_32533_4","message":"插桩已提交: mode=transparent /  |
| 09-13 04:07 | 76 | `browser_reverse_search` | fail | 0.02s | ERR_WEAK | OTHER | 脚本搜索错误: JS异常:Uncaught |
| 09-13 04:12 | 77 | `browser_reverse_search` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"query":"sign","found":0,"results":[]}} |
| 09-13 04:12 | 78 | `browser_execute_js` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"Example Domain"} |
| 09-13 04:12 | 79 | `browser_vip_set_css_version` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"CSS内核已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_n |
| 09-13 04:12 | 80 | `browser_vip_set_web_version` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"Web内核已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_n |
| 09-13 04:12 | 81 | `browser_vip_set_v8_version` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"V8内核已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 04:12 | 82 | `browser_vip_enable_devtools_observer` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"DevTools消息监听已启用(MCP观察者)"} |
| 09-13 04:12 | 83 | `browser_vip_enable_inspector` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"监管者事件已设置"} |
| 09-13 04:19 | 84 | `browser_move_window` | pass | 0.33s | OK |  | {"id":"1","success":true,"data":{"requested_x":10,"requested_y":10,"requested_width":1000,"requested_height":8 |
| 09-13 04:19 | 85 | `browser_set_auto_resize` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"enable":true,"min_height":0,"min_width":0,"max_height":0,"max_width":0,"veri |
| 09-13 04:20 | 86 | `browser_debugger_auto` | fail | 12.47s | ERR_GOOD | TARGET | 未捕获到任何断点命中(0 hits) / 停止原因: 等待 Debugger.paused 超时(12000ms): 该窗口内页面未执行到断点位置 / 注: 下断当时该 urlRegex 匹配到 0 个脚本位置(loca |
| 09-13 04:20 | 87 | `browser_reverse_initiator` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_36784546_70532_2","message":"网络溯源Hook已安装:  / 触发目标请求后再次调 |
| 09-13 04:20 | 87 | `browser_reverse_preset` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_36784578_75094_3","message":"预设Hook已安装: all / 通过mcp_res |
| 09-13 04:20 | 87 | `browser_reverse_cdp_hook` | fail | 0.02s | ERR_GOOD | OTHER | 需要 object_id 或 function_name |
| 09-13 04:20 | 87 | `browser_reverse_profile` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Profiler.enable"}

[task_id: 1] |
| 09-13 04:20 | 87 | `browser_reverse_dom_breakpoint` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:DOMDebugger.setXHRBreakpoint"}

[task_i |
| 09-13 04:20 | 87 | `browser_reverse_preload` | pass | 0.00s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Page.addScriptToEvaluateOnNewDocument"} |
| 09-13 04:20 | 87 | `browser_reverse_call_fn` | fail | 0.01s | ERR_GOOD | OTHER | 需要 object_id 或 function_name |
| 09-13 04:21 | 88 | `browser_reverse_cdp_hook` | pass | 0.03s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Debugger.setBreakpointOnFunctionCall"}
 |
| 09-13 04:21 | 89 | `browser_reverse_call_fn` | pass | 0.04s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Runtime.callFunctionOn"}

[task_id: 1] |
| 09-13 04:21 | 90 | `browser_reverse_websocket` | fail | 0.01s | ERR_GOOD | OTHER | 未知action: send / 支持: enable/query |
| 09-13 04:21 | 90 | `browser_reverse_heap` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:HeapProfiler.takeHeapSnapshot"}

[task_ |
| 09-13 04:21 | 90 | `browser_reverse_runtime` | fail | 0.01s | ERR_GOOD | OTHER | properties 需要 object_id |
| 09-13 04:21 | 90 | `browser_reverse_network_intercept` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Network.setRequestInterception"}

[task |
| 09-13 04:21 | 90 | `browser_reverse_setup` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"反检测预配置已设置 / 当前浏览器已应用 + 所有新浏览器自动应用 / disable_debugger:0 UA:(未设置)"} |
| 09-13 04:21 | 90 | `browser_reverse_extract` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"total_scripts":0,"scripts":[]}} |
| 09-13 04:21 | 90 | `browser_antidetect_presets` | pass | 0.05s | OK |  | {"id":"1","success":true,"message":"反检测预设 [basic] 已部署 / ✓ debugger检测已禁用; ✓ 自动化标志已移除; ✓ Canvas/WebGL/Audio指纹已随机 |
| 09-13 04:21 | 90 | `browser_network_export` | pass | 0.02s | OK |  | {"success":true,"network_logs":[{"type":"res","url":"https://example.com/","status":200,"mime":"text/html","ca |
| 09-13 04:21 | 90 | `browser_permission_spoof` | pass | 0.00s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_36816750_73545_17","message":"权限API伪装已注入 / 权限:geolocati |
| 09-13 04:21 | 91 | `browser_reverse_websocket` | fail | 0.00s | ERR_GOOD | OTHER | query 需要 request_id (从Network.requestWillBeSent事件获取) |
| 09-13 04:21 | 92 | `browser_reverse_runtime` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Runtime.evaluate"}

[task_id: 1] |
| 09-13 04:21 | 93 | `browser_reverse_websocket` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Network.enable"}

[task_id: 1] |
| 09-13 04:24 | 94 | `browser_reverse_runtime` | pass | 0.00s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Runtime.evaluate"}

[task_id: 1] |
| 09-13 04:30 | 95 | `browser_reverse_instrument` | pass | 0.00s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_37376812_37439_6","message":"插桩已提交: mode=transparent /  |
| 09-13 04:33 | 96 | `browser_reverse_hook_multi` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"hook_json":"{\"found\":1,\"hooked\":[\"parseInt\"],\"log_key\ |
| 09-13 04:33 | 97 | `browser_reverse_hook_logs` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"logs_json":"{\"count\":0,\"returned\":0,\"keys\":[],\"by_key\ |
| 09-13 04:38 | 98 | `browser_reverse_hook` | fail | 0.01s | ERR_GOOD | TARGET | target 不能为空 / 指定函数名/URL正则/选择器 |
| 09-13 04:38 | 99 | `browser_kernel_reverse_trace` | fail | 0.02s | ERR_GOOD | TARGET | targets 不能为空 / 例: ["window.fetch","crypto.subtle.encrypt"] |
| 09-13 04:38 | 100 | `browser_kernel_reverse_probe` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"动态探针已注入(五维API插桩): __ok / 数据在 window.__MCP_PROBE__, 用 action=get 取回"} |
| 09-13 04:38 | 101 | `browser_kernel_reverse_watch_global` | fail | 0.01s | ERR_GOOD | TARGET | names 不能为空 / 例: ["token","sign","session"] |
| 09-13 04:38 | 102 | `browser_reverse_hook` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_37823015_41240_6","message":"Hook已提交: function_call → p |
| 09-13 04:38 | 103 | `browser_kernel_reverse_trace` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"trace":"{\"calls\":[{\"p\":\"parseInt\",\"a\":[\"7\"],\"r\":\ |
| 09-13 04:38 | 104 | `browser_kernel_reverse_watch_global` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"全局变量追踪已启动: __ok watched=1 / 数据在 window.__MCP_GWATCH__"} |
| 09-13 04:41 | 105 | `browser_debugger_evaluate` | pass | 0.17s | OK |  | {"result":{"type":"number","value":1,"description":"1"}} |
| 09-13 04:41 | 106 | `browser_debugger_flow` | fail | 12.41s | ERR_GOOD | OTHER | debugger_flow 失败: {"ok":false,"step":"wait_paused","error":"timeout","breakpoint":"mcp_probe","waited_ms":1200 |
| 09-13 04:41 | 107 | `browser_debugger_resume` | fail | 0.02s | ERR_GOOD | STATE | 页面未处于暂停状态, 无需恢复 / 请先 debugger_flow 或 debugger_enable + 断点 + wait_paused |
| 09-13 04:42 | 108 | `browser_debugger_resume` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"页面本就未处于暂停状态, 无需恢复(幂等成功, 未执行任何动作)"} |
| 09-13 04:43 | 109 | `browser_retry` | fail | 3.09s | ERR_GOOD | OTHER | 重试3次后仍失败 / tool=mcp_probe / 最后错误已输出 |
| 09-13 04:43 | 109 | `browser_canvas_noise` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_38126421_24181_16","message":"Canvas噪声已注入(level=1) / 通过 |
| 09-13 04:43 | 109 | `browser_event` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"limit":50,"timeline_json":"[{\"event\":\"load_end\",\"browser |
| 09-13 04:43 | 109 | `browser_snapshot` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"snapshot_json":"{\"count\":4,\"total\":4,\"elements\":[{\"i\" |
| 09-13 04:43 | 109 | `browser_click_text` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"result_json":"{\"found\":false,\"error\":\"not_found_text\",\ |
| 09-13 04:43 | 109 | `browser_get_forms` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"forms_json":"{\"count\":1,\"forms\":[{\"index\":0,\"action\": |
| 09-13 04:43 | 109 | `browser_get_scroll` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"scroll_json":"{\"x\":0,\"y\":0,\"max_y\":0,\"max_x\":0}"}} |
| 09-13 04:43 | 109 | `browser_element_action` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"result_json":"{\"ok\":false,\"error\":\"index_not_found(请重新br |
| 09-13 04:43 | 109 | `browser_debugger_list_breakpoints` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"count":0,"breakpoints":"[]"}} |
| 09-13 04:43 | 109 | `browser_debugger_clear_breakpoints` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"removed":0,"failed":0,"note":"若页面仍暂停请 debugger_resume; 未成功移除的 |
| 09-13 04:43 | 109 | `browser_reverse_stack_trace` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"stack_json":"{\"stack\":\"Error: __MCP_STACK__\\n    at <anon |
| 09-13 04:43 | 109 | `browser_scroll_by` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"scroll_json":"{\"x\":0,\"y\":0,\"scrolled_by_x\":0,\"scrolled |
| 09-13 04:43 | 109 | `browser_highlight` | fail | 0.01s | ERR_GOOD | TARGET | selector 参数不能为空 / 请查看工具描述补全必填参数 |
| 09-13 04:43 | 109 | `browser_reverse_scan_crypto` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"scan_json":"{\"count\":0,\"scripts\":[]}"}} |
| 09-13 04:43 | 109 | `browser_reverse_string_refs` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"refs_json":"{\"count\":0,\"refs\":[]}"}} |
| 09-13 04:43 | 110 | `browser_retry` | pass | 0.02s | OK |  | {"id":"1_r1","success":true,"data":{"is_popup":false,"has_document":true,"can_go_back":true,"can_go_forward":f |
| 09-13 04:43 | 111 | `browser_highlight` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"result_json":"{\"highlighted\":1,\"auto_clear_ms\":100}"}} |
| 09-13 04:43 | 112 | `browser_reverse_detect_obfuscator` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"detect_json":"{\"detected\":0,\"items\":[],\"total_len\":0}"} |
| 09-13 04:43 | 112 | `browser_reverse_instrument_script` | fail(wedge) | 6.31s | OK |  | {"id":"1","success":true,"auto_prepared":"Debugger.enable","data":{"success":true,"cdp_method":"Debugger.setIn |
| 09-13 04:43 | 112 | `browser_reverse_pause_on_exceptions` | pass | 0.07s | OK |  | {"id":"1","success":true,"auto_prepared":"Debugger.enable","data":{"success":true,"cdp_method":"Debugger.setPa |
| 09-13 04:43 | 112 | `browser_reverse_blackbox` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Debugger.setBlackboxPatterns","cdp_result":"{}", |
| 09-13 04:43 | 112 | `browser_reverse_async_stack` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Debugger.setAsyncCallStackDepth","cdp_result":"{ |
| 09-13 04:43 | 112 | `browser_reverse_breakpoints_active` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Debugger.setBreakpointsActive","cdp_result":"{}" |
| 09-13 04:43 | 112 | `browser_reverse_skip_pauses` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Debugger.setSkipAllPauses","cdp_result":"{}","no |
| 09-13 04:43 | 112 | `browser_reverse_precise_coverage` | fail | 0.03s | ERR_WEAK | OTHER | Profiler.takePreciseCoverage 失败: Precise coverage has not been started. |
| 09-13 04:43 | 112 | `browser_reverse_return_value` | fail | 0.00s | ERR_WEAK | STATE | 页面未处于暂停态 / 该工具只在 Debugger.paused 时有效: 先设断点/插装并触发暂停, 再用 browser_debugger_wait_paused 确认 |
| 09-13 04:43 | 112 | `browser_reverse_set_variable` | fail | 0.01s | ERR_WEAK | STATE | 页面未处于暂停态且未提供 call_frame_id / 先在断点处暂停, 或用 browser_debugger_get_stack 取 call_frame_id |
| 09-13 04:43 | 112 | `browser_reverse_search_script` | fail | 0.02s | ERR_GOOD | TARGET | query 不能为空 / 例: query="sign"; 若不知有哪些脚本先 action=list |
| 09-13 04:43 | 112 | `browser_reverse_add_binding` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Runtime.addBinding","cdp_result":"{}","note":"已绑 |
| 09-13 04:43 | 112 | `browser_reverse_listeners` | fail | 0.02s | ERR_GOOD | OTHER | 需提供 object_id 或 selector / selector 例: #app 或 document 或 window |
| 09-13 04:43 | 112 | `browser_reverse_dom_resolve` | fail | 0.01s | ERR_GOOD | OTHER | 需提供 expression 或 selector / 例: expression="window.someObj" 或 selector="#app" |
| 09-13 04:49 | 113 | `browser_reverse_search_script` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"count":0,"scripts_json":"[]","hint":"脚本注册表为空 / 先 browser_debu |
| 09-13 04:49 | 114 | `browser_reverse_listeners` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"DOMDebugger.getEventListeners","cdp_result":"{\" |
| 09-13 04:49 | 115 | `browser_reverse_dom_resolve` | fail | 0.02s | ERR_GOOD | TARGET | 求值未取到 objectId(表达式可能返回基本类型或元素不存在): document.querySelector('document') / 基本类型请用 browser_execute_js 直接取返回值 |
| 09-13 04:49 | 116 | `browser_reverse_dom_resolve` | pass | 0.05s | OK |  | {"id":"1","success":true,"data":{"success":true,"expression":"document.querySelector('h1')","object_id":"79263 |
| 09-13 04:49 | 117 | `browser_reverse_instrument_script` | fail | 0.01s | ERR_GOOD | OTHER | install 需要显式确认 / 实测: 装上后本会话的 **JS 通道即被阻塞**(browser_execute_js / browser_debugger_last_paused 等 30s 超时; browser |
| 09-13 04:50 | 118 | `browser_reverse_query_objects` | fail | 0.02s | ERR_GOOD | OTHER | 需提供 prototype_expression(如 window.CryptoJS.AES.prototype) 或 prototype_object_id |
| 09-13 04:50 | 118 | `browser_reverse_bypass_csp` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Page.setBypassCSP","cdp_result":"{}","note":"已绕过 |
| 09-13 04:50 | 118 | `browser_reverse_cache_disable` | pass | 0.04s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Network.setCacheDisabled","cdp_result":"{}","not |
| 09-13 04:50 | 118 | `browser_reverse_evaluate_silent` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Runtime.evaluate","cdp_result":"{\"result\":{\"t |
| 09-13 04:50 | 118 | `browser_reverse_await_promise` | fail | 0.00s | ERR_GOOD | OTHER | 需提供 expression(返回Promise的表达式) 或 promise_object_id |
| 09-13 04:50 | 118 | `browser_fill_form` | fail | 0.01s | ERR_WEAK | OTHER | fields JSON解析失败 / 格式: [{"selector":"#id","value":"文本"},...] |
| 09-13 04:51 | 119 | `browser_reverse_query_objects` | pass | 0.04s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Runtime.queryObjects","cdp_result":"{\"objects\" |
| 09-13 04:51 | 120 | `browser_reverse_await_promise` | pass | 0.05s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Runtime.awaitPromise","cdp_result":"{\"result\": |
| 09-13 04:51 | 121 | `browser_fill_form` | pass | 0.02s | OK |  | [前置] browser_execute_js -> OK // {"id":"1","success":true,"data":{"success":true,"filled":1,"failed":0,"submit |
| 09-13 04:55 | 122 | `browser_show_window` | pass | 0.26s | OK |  | {"id":"1","success":true,"data":{"requested_visible":true,"visible_before":true,"visible_after":true,"style_be |
| 09-13 04:57 | 123 | `browser_dom_query` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"Example Domain"} |
| 09-13 04:57 | 124 | `browser_dom_rect` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"{\"selector\":\"h1\",\"x\":196.796875,\"y\":105.75,\"left\":196.796875,\"t |
| 09-13 04:57 | 125 | `browser_dom_inner_html` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"Example Domain"} |
| 09-13 04:57 | 126 | `browser_dom_click` | pass | 0.02s | OK |  | 已点击(原生): h1 |
| 09-13 04:57 | 127 | `browser_fill_click` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"已点击: h1"} |
| 09-13 04:57 | 128 | `browser_fill_focus` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"焦点已设置: h1"} |
| 09-13 04:57 | 129 | `browser_fill_scroll` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"已滚动到: h1"} |
| 09-13 04:57 | 130 | `browser_fill_trigger` | pass | 0.04s | OK |  | {"id":"1","success":true,"message":"事件已触发: click -> h1"} |
| 09-13 04:57 | 131 | `browser_dom_checked` | pass | 0.03s | OK |  | [前置] browser_execute_js -> OK // {"id":"1","success":true,"message":"{\"selector\":\"#mcpProbeCheck\",\"checke |
| 09-13 04:57 | 132 | `browser_dom_selected` | pass | 0.02s | OK |  | [前置] browser_execute_js -> OK // {"id":"1","success":true,"message":"{\"selector\":\"#mcpProbeSelect\",\"index |
| 09-13 04:57 | 133 | `browser_dom_set_value` | pass | 0.03s | OK |  | [前置] browser_execute_js -> OK // {"id":"1","success":true,"data":{"success":true,"selector":"#mcpProbeInput"," |
| 09-13 04:57 | 134 | `browser_fill_set_value` | pass | 0.03s | OK |  | [前置] browser_execute_js -> OK // {"id":"1","success":true,"message":"已设置: #mcpProbeInput"} |
| 09-13 04:57 | 135 | `browser_fill_select` | pass | 0.03s | OK |  | [前置] browser_execute_js -> OK // {"id":"1","success":true,"message":"select已设置: #mcpProbeSelect = mcpA"} |
| 09-13 04:57 | 136 | `browser_fill_attr_get` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"https://iana.org/domains/example"} |
| 09-13 04:57 | 137 | `browser_fill_attr_set` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"属性已设置: a"} |
| 09-13 04:57 | 138 | `browser_wait` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_38986531_87816_18","message":"等待已提交(what=selector value |
| 09-13 04:57 | 139 | `browser_intercept` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"所有拦截规则已清除(手写过滤器通道)"} |
| 09-13 04:57 | 140 | `browser_file_dialog` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"selected":"C:\\Windows\\win.ini"}} |
| 09-13 04:57 | 141 | `workflow_get` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"name":"hello","definition":"{\r\n  \"name\": \"hello\",\r\n  \"description\" |
| 09-13 04:57 | 142 | `browser_cdp_call` | pass | 0.03s | OK |  | {"result":{"type":"number","value":1,"description":"1"}} |
| 09-13 04:57 | 143 | `browser_kernel_auth` | pass | 0.01s | OK |  | {"success":true,"credentials":"[]"} |
| 09-13 04:57 | 144 | `browser_kernel_scheme` | pass | 0.02s | OK |  | {"success":true,"schemes":"[]"} |
| 09-13 04:57 | 145 | `browser_kernel_reactor` | pass | 0.01s | OK |  | {"success":true,"rules":"[]"} |
| 09-13 04:57 | 146 | `browser_kernel_watch` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"watches":[],"watch_count":0,"changes_json":[]}} |
| 09-13 04:57 | 147 | `browser_vip_execute_js_context` | pass | 0.00s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_38987671_67608_19","message":"JS已提交到指定环境","poll_hint":" |
| 09-13 04:57 | 148 | `browser_vip_dom_search` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_38998343_67444_1","message":"预查找已提交, 通过mcp_result查询, 从结 |
| 09-13 04:58 | 149 | `browser_cdp_event` | pass | 0.02s | OK |  | [前置] browser_debugger_stack -> OK // {"id":"1","success":true,"data":{"event":"Debugger.paused","raw":{"callFr |
| 09-13 04:58 | 150 | `browser_reverse_return_value` | fail | 0.05s | ERR_WEAK | OTHER | [前置] browser_debugger_stack -> OK // Debugger.setReturnValue 失败: Invalid parameters |
| 09-13 04:58 | 151 | `browser_reverse_set_variable` | fail | 0.01s | ERR_GOOD | GUARD | [前置] browser_debugger_stack -> OK // 无法从暂停事件取到 call_frame_id / 请显式传 call_frame_id |
| 09-13 04:58 | 152 | `browser_forward` | fail | 0.01s | ERR_WEAK | OTHER | [前置] browser_navigate -> OK; browser_navigate -> OK; browser_back -> ERR_WEAK // 无法前进 — 无导航历史 / 当前页面没有可前进的历史记录 |
| 09-13 04:58 | 153 | `browser_reverse_return_value` | fail | 0.03s | ERR_WEAK | OTHER | [前置] browser_debugger_stack -> OK // Debugger.setReturnValue 失败: Invalid parameters |
| 09-13 04:58 | 154 | `browser_reverse_set_variable` | fail | 0.02s | ERR_GOOD | GUARD | [前置] browser_debugger_stack -> OK // 无法从暂停事件取到 call_frame_id / 请显式传 call_frame_id |
| 09-13 04:58 | 155 | `browser_forward` | pass | 0.02s | OK |  | [前置] browser_navigate -> OK; browser_navigate -> OK; browser_back -> OK // {"id":"1","success":true,"message": |
| 09-13 05:03 | 156 | `browser_find_by_tag` | pass | 0.00s | OK |  | [前置] browser_create -> OK // {"id":"1","success":true,"data":{"id":2,"url":"","tag":"mcp_probe"}} |
| 09-13 05:03 | 157 | `browser_find_by_hwnd` | fail | 0.02s | ERR_GOOD | TARGET | 未找到窗口句柄为 1 的浏览器 / 如何取得有效句柄: 调 browser_get_window_handle(返回当前浏览器窗口句柄) 或 browser_window_info 看 hwnd 字段; 句柄是**运行时 |
| 09-13 05:03 | 158 | `browser_reverse_precise_coverage` | fail | 0.03s | ERR_GOOD | PREREQ | Profiler.takePreciseCoverage 失败: Precise coverage has not been started. / 该能力需要先开启: 请先调 browser_reverse_precis |
| 09-13 05:04 | 159 | `browser_reverse_precise_coverage` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"messageId":54,"method":"Profiler.takePreciseCoverage","result |
| 09-13 05:32 | 160 | `browser_create` | pass | 0.52s | OK |  | {"id":"1","success":true,"message":"浏览器已创建: about:blank / 通过 browser_list 查看详情"} |
| 09-13 05:32 | 161 | `browser_find_by_tag` | pass | 0.00s | OK |  | [前置] browser_create -> OK // {"id":"1","success":true,"data":{"id":3,"url":"","tag":"mcp_probe"}} |
| 09-13 05:32 | 162 | `browser_user_tags` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"tags":["","","mcp_probe"]}} |
| 09-13 05:32 | 163 | `browser_list` | pass | 0.01s | OK |  | {"id":"1","success":true,"browsers":[{"id":1,"url":"https://example.com/?stale=2"},{"id":2,"url":"about:blank" |
| 09-13 05:32 | 164 | `browser_reverse_precise_coverage` | pass | 0.07s | OK |  | {"id":"1","success":true,"auto_prepared":"browser_reverse_precise_coverage: 精确覆盖率尚未开启, 已自动 Profiler.enable + s |
| 09-13 05:32 | 165 | `browser_reverse_instrument_script` | fail | 0.00s | ERR_GOOD | OTHER | install 需要显式确认 / 实测: 装上后本会话的 **JS 通道即被阻塞**(browser_execute_js / browser_debugger_last_paused 等 30s 超时; browser |
| 09-13 05:32 | 166 | `browser_debugger_evaluate` | pass | 0.77s | OK |  | {"result":{"type":"number","value":1,"description":"1"}} |
| 09-13 05:32 | 167 | `browser_debugger_flow` | fail | 12.40s | ERR_GOOD | OTHER | debugger_flow 失败: {"ok":false,"step":"wait_paused","error":"timeout","breakpoint":"mcp_probe","waited_ms":1200 |
| 09-13 05:32 | 168 | `browser_debugger_resume` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"页面本就未处于暂停状态, 无需恢复(幂等成功, 未执行任何动作)"} |
| 09-13 05:32 | 169 | `browser_move_window` | pass | 0.30s | OK |  | {"id":"1","success":true,"data":{"requested_x":10,"requested_y":10,"requested_width":1000,"requested_height":8 |
| 09-13 05:32 | 170 | `browser_set_auto_resize` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"enable":true,"min_height":0,"min_width":0,"max_height":0,"max_width":0,"veri |
| 09-13 05:32 | 171 | `browser_show_window` | pass | 0.28s | OK |  | {"id":"1","success":true,"data":{"requested_visible":true,"visible_before":true,"visible_after":true,"style_be |
| 09-13 05:32 | 172 | `browser_get_run_style` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"window_style":382664704,"is_popup":false,"browser_id":1}} |
| 09-13 05:32 | 173 | `browser_reverse_hook` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_41075968_46150_3","message":"Hook已提交: function_call → p |
| 09-13 05:32 | 174 | `browser_reverse_hook_multi` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"hook_json":"{\"found\":1,\"hooked\":[\"parseInt\"],\"log_key\ |
| 09-13 05:32 | 175 | `browser_reverse_search` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"query":"sign","found":0,"results":[]}} |
| 09-13 05:32 | 176 | `browser_reverse_runtime` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Runtime.evaluate"}

[task_id: 1] |
| 09-13 05:32 | 177 | `browser_execute_js` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"Example Domain"} |
| 09-13 05:34 | 178 | `browser_debugger_auto` | fail | 8.44s | ERR_GOOD | TARGET | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK // 未捕获到任何断点命中(0 hits) / 停止原因: 等待 Debugger.paused  |
| 09-13 05:34 | 179 | `browser_debugger_flow` | fail | 8.39s | ERR_GOOD | OTHER | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK // debugger_flow 失败: {"ok":false,"step":"wait_pau |
| 09-13 05:35 | 180 | `browser_reverse_return_value` | fail | 0.02s | ERR_WEAK | STATE | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK; browser_debugger_flow -> ERR_GOOD // 页面未处于暂停态 /  |
| 09-13 05:35 | 181 | `browser_reverse_set_variable` | fail | 0.00s | ERR_WEAK | STATE | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK; browser_debugger_flow -> ERR_GOOD // 页面未处于暂停态且未提 |
| 09-13 05:37 | 182 | `browser_debugger_auto` | pass | 1.01s | OK |  | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK // {"id":"1","success":true,"data":{"success":tru |
| 09-13 05:37 | 183 | `browser_debugger_flow` | pass | 0.46s | OK |  | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK // {"id":"1","success":true,"data":{"ok":true,"br |
| 09-13 05:37 | 184 | `browser_reverse_return_value` | fail | 0.03s | ERR_WEAK | OTHER | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK; browser_debugger_flow -> OK // Debugger.setRetur |
| 09-13 05:37 | 185 | `browser_reverse_set_variable` | fail | 0.03s | ERR_GOOD | GUARD | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK; browser_debugger_flow -> ERR_GOOD // 无法从暂停事件取到 c |
| 09-13 05:39 | 186 | `browser_reverse_return_value` | pass | 0.04s | OK |  | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK; browser_debugger_flow -> OK // {"id":"1","succes |
| 09-13 05:39 | 187 | `browser_reverse_set_variable` | fail | 0.02s | ERR_GOOD | GUARD | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK; browser_debugger_flow -> OK // 无法从暂停事件取到 call_fr |
| 09-13 05:41 | 188 | `browser_reverse_set_variable` | pass | 0.04s | OK |  | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK; browser_debugger_flow -> OK // {"id":"1","succes |
| 09-13 05:41 | 189 | `browser_reverse_return_value` | pass | 0.03s | OK |  | [前置] browser_debugger_enable -> OK; browser_execute_js -> OK; browser_debugger_flow -> ERR_GOOD // {"id":"1"," |
| 09-13 05:52 | 190 | `browser_set_preference` | pass | 0.00s | OK_MANUAL |  | [人工受控实测·非探针] 测法: 把 webkit 首选项设成它本来就是的值(不改变任何行为) // 原文: 首选项 webkit.webprefs.javascript_enabled 已设置 // 当时实例存活; 补 |
| 09-13 05:52 | 190 | `browser_set_s5_proxy` | pass | 0.00s | OK_MANUAL |  | [人工受控实测·非探针] 测法: 指向本机无效端口 127.0.0.1:1, 测完立刻重启清掉 // 原文: S5代理已设置: 127.0.0.1:1 ... + 如实给出 needs_reload:true // 当时 |
| 09-13 05:52 | 190 | `browser_reverse_patch` | pass | 0.00s | OK_MANUAL |  | [人工受控实测·非探针] 测法: 用它自带的 dry_run:true (只验证编译不替换) // 原文: dryRun 通过(新源码可编译, 未实际替换) // 当时实例存活; 补记原因: 台账 CLI 对 LETHA |
| 09-13 05:52 | 190 | `browser_close` | pass | 0.00s | OK_MANUAL |  | [人工受控实测·非探针] 测法: 先建第二个后台浏览器, 只关 browser_id=2, 不动主浏览器 // 原文: 浏览器已关闭: id=2 // 当时实例存活; 补记原因: 台账 CLI 对 LETHAL 工具直接 |
| 09-13 05:52 | 190 | `browser_close_try` | pass | 0.00s | OK_MANUAL |  | [人工受控实测·非探针] 测法: 放靠后执行; 文档说它会关浏览器 // 原文: ⛔ 远程关闭浏览器已禁用…(如实拒绝, 未造成影响) // 当时实例存活; 补记原因: 台账 CLI 对 LETHAL 工具直接跳过, 故 |
| 09-13 05:52 | 190 | `browser_shutdown` | pass | 0.00s | OK_MANUAL |  | [人工受控实测·非探针] 测法: 最后一项, confirm:true + 2 秒延迟 // 原文: AI浏览器将在2秒后安全关闭, 感谢使用 (重启后恢复) // 当时实例存活; 补记原因: 台账 CLI 对 LETH |
| 09-13 05:53 | 191 | `browser_reverse_network_intercept` | fail | 0.02s | ERR_GOOD | OTHER | enable 需要 url_pattern: 请显式给出要拦截的 URL 模式(如 */api/* 或 *sign*)。提示: 放行被拦请求用 browser_cdp_call method=Network.contin |
| 09-13 05:53 | 192 | `browser_reverse_profile` | pass | 0.05s | OK |  | {"id":"1","success":true,"data":{"success":true,"action":"start","note":"采样已真正开始(enable+start): 执行目标操作后用 actio |
| 09-13 05:54 | 193 | `browser_reverse_network_intercept` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"action":"enable","url_pattern":"*mcp-probe-never-matches*","n |
| 09-13 05:54 | 194 | `browser_reverse_profile` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"action":"query","coverage_result":{"result":[{"scriptId":"5", |
| 09-13 05:56 | 195 | `browser_reverse_runtime` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Runtime.evaluate","cdp_result":"{\"result\":{\"t |
| 09-13 05:56 | 196 | `browser_reverse_call_fn` | pass | 0.04s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Runtime.callFunctionOn","cdp_result":"{\"result\ |
| 09-13 05:56 | 197 | `browser_reverse_websocket` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Network.enable"}

[task_id: 1] |
| 09-13 05:56 | 198 | `browser_reverse_heap` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:HeapProfiler.takeHeapSnapshot"}

[task_ |
| 09-13 06:02 | 199 | `browser_network_body` | fail | 0.02s | ERR_GOOD | OTHER | Network.getResponseBody 失败: No resource with given identifier found / 常见原因: 该请求的响应体已不在缓存中(要在请求发生后尽快取), 或 reque |
| 09-13 06:13 | 200 | `browser_cdp` | pass | 0.03s | OK |  | {"result":{"type":"string","value":"Example Domain"}} |
| 09-13 06:13 | 201 | `browser_reverse_cdp_hook` | fail | 0.05s | ERR_WEAK | OTHER | Debugger.setBreakpointOnFunctionCall 失败: Breakpoint at specified location already exists. |
| 09-13 06:13 | 202 | `browser_reverse_dom_breakpoint` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"DOMDebugger.setXHRBreakpoint","cdp_result":"{}", |
| 09-13 06:13 | 203 | `browser_reverse_heap` | pass | 0.12s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"HeapProfiler.takeHeapSnapshot","cdp_result":"{}" |
| 09-13 06:13 | 204 | `browser_reverse_preload` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Page.addScriptToEvaluateOnNewDocument","cdp_resu |
| 09-13 06:13 | 205 | `browser_reverse_websocket` | pass | 0.04s | OK |  | {"id":"1","success":true,"data":{"success":true,"cdp_method":"Network.enable","cdp_result":"{}","note":"Networ |
| 09-13 06:14 | 206 | `browser_reverse_cdp_hook` | pass | 0.05s | OK |  | {"id":"1","success":true,"data":{"success":true,"already_armed":true,"cdp_method":"Debugger.setBreakpointOnFun |
| 09-13 06:29 | 207 | `browser_scrape` | pass | 0.08s | OK |  | Example Domain

This domain is for use in documentation examples without needing permission. Avoid use in oper |
| 09-13 06:39 | 208 | `browser_intercept` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"已按 URL 撤销资源替换规则 0 条 / 口径: 请求URL包含规则URL(与命中同口径) / url=https://mcp-probe-nev |
| 09-13 06:42 | 209 | `browser_permission_spoof` | pass | 0.04s | OK |  | Permissions API 已伪装: geolocation,notifications,camera,microphone,midi,clipboard-read,clipboard-write → granted |
| 09-13 06:46 | 210 | `browser_context_menu` | fail | 0.02s | ERR_GOOD | OTHER | set 需要 items(逐行菜单规格) / 格式: 类型/标签/命令ID/参数/父命令ID/快捷键; 类型=item/check/radio/sep/sub; 命令ID 须在 26500..28500(留0自动分配) |
| 09-13 06:46 | 211 | `browser_context_menu` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"enabled":false,"apply_count":0,"last_applied_items":0,"last_a |
| 09-13 06:53 | 212 | `browser_back` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_45930203_44607_10","message":"已后退 / 等待载入完成, 通过mcp_resul |
| 09-13 06:53 | 213 | `browser_forward` | pass | 0.01s | OK |  | [前置] browser_navigate -> OK; browser_navigate -> OK; browser_back -> OK // {"id":"1","success":true,"_async":t |
| 09-13 06:56 | 214 | `browser_back` | pass | 0.01s | OK |  | 等待条件满足: load_end → http://127.0.0.1:9222/ |
| 09-13 06:56 | 215 | `browser_forward` | pass | 0.02s | OK |  | [前置] browser_navigate -> OK; browser_navigate -> OK; browser_back -> ERR_WEAK // 等待条件满足: load_end → https://ex |
| 09-13 07:04 | 216 | `browser_context_menu` | pass | 0.00s | OK |  | {"id":"1","success":true,"data":{"success":true,"enabled":false,"apply_count":1,"last_applied_items":0,"last_a |
| 09-13 07:07 | 217 | `browser_fill_get_text` | fail | 0.03s | ERR_WEAK | TARGET | 元素不存在: #mcp-probe-nonexistent / 建议: 先用 browser_fill_exists 或 browser_snapshot 确认元素存在/选择器正确 |
| 09-13 07:07 | 218 | `browser_fill_set_text` | fail | 0.04s | ERR_WEAK | TARGET | 元素不存在: #mcp-probe-nonexistent |
| 09-13 07:08 | 219 | `browser_fill_get_text` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"Example Domain"} |
| 09-13 07:08 | 220 | `browser_fill_set_text` | pass | 0.05s | OK |  | [前置] browser_execute_js -> OK // {"id":"1","success":true,"message":"innerText 已设置并回读确认: mcp-probe-text"} |
| 09-13 07:23 | 221 | `browser_vip_execute_js_context` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_47738796_65066_2","message":"JS已提交到指定环境","poll_hint":"用 |
| 09-13 08:10 | 222 | `browser_context_menu` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"enabled":false,"apply_count":0,"last_applied_items":0,"menu_i |
| 09-13 08:38 | 223 | `browser_frame_by_id` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"found":false,"frame_id":"mcp_probe","hint":"该 frame_id 不存在或框架已销毁(导航/刷新后 ID 会 |
| 09-13 08:38 | 224 | `browser_uri_decode` | pass | 0.00s | OK |  | {"id":"1","success":true,"data":{"decoded":"mcp_probe","via":"lib:FBrowser_Parser_URI解码"}} |
| 09-13 08:38 | 225 | `browser_uri_encode` | pass | 0.02s | OK |  | {"success":true,"encoded":"mcp_probe"} |
| 09-13 08:38 | 226 | `browser_event` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"limit":50,"timeline_json":"[{\"event\":\"loading_state_change |
| 09-13 08:46 | 227 | `browser_vip_load_extension` | fail | 0.02s | ERR_GOOD | OTHER | 需要 path(已解压插件目录) 或 crx_path(.crx 插件包) 之一 / 类库原文: 载入解压目录效率高于 CRX 安装, 且 CRX 会概率性出现「页面已打开但插件未装完」(装完刷新即生效) |
| 09-13 08:50 | 228 | `browser_collect` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"scenario":"reverse_analyze","tip":"navigate 后 browser_network list + browser |
| 09-13 08:50 | 229 | `browser_kernel_events_all` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"全事件流已关闭"} |
| 09-13 08:50 | 230 | `browser_vip_load_extension` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"CRX插件包已提交安装: mcp_probe.crx / mode=crx / advanced_enabled=true / 类库原文: CRX  |
| 09-13 09:04 | 231 | `browser_codec` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"action":"hex_encode","charset":"utf8","input":"text","output" |
| 09-13 09:04 | 232 | `browser_time_convert` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"action":"now","unit":"s","ole":46278.37778293982,"year":2026, |
| 09-13 09:04 | 233 | `browser_event` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"success":true,"limit":50,"timeline_json":"[{\"event\":\"load_end\",\"browser |
| 09-13 09:04 | 234 | `browser_kernel_events_all` | pass | 0.01s | OK |  | {"id":"1","success":true,"message":"全事件流已关闭"} |
| 09-13 09:10 | 235 | `browser_hash` | fail | 0.00s | ERR_GOOD | GUARD | data 不能为空 / 空串摘要无意义(空文件 MD5 恒为 d41d8cd98f00b204e9800998ecf8427e), 如需请显式传一个空格 |
| 09-13 09:11 | 236 | `browser_hash` | pass | 0.01s | OK |  | {"id":"1","success":true,"data":{"action":"md5","bytes":9,"md5":"c36b0ef39debaa565d723d2473e034b1","algorithm" |
| 09-13 09:33 | 237 | `browser_create_url_request` | pass | 0.01s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_55520765_92076_31","message":"URL请求已提交, 通过mcp_result查询结 |
| 09-13 09:38 | 238 | `browser_fill_set_value` | pass | 0.01s | OK |  | [前置] browser_execute_js -> OK // {"id":"1","success":true,"message":"已设置: #mcpProbeInput"} |
| 09-13 09:38 | 239 | `browser_fill_attr_get` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"https://iana.org/domains/example"} |
| 09-13 09:38 | 240 | `browser_dom_query` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"Example Domain"} |
| 09-13 09:38 | 241 | `browser_get_text` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"Example Domain\n\nThis domain is for use in documentation examples without |
| 09-13 09:58 | 242 | `browser_execute_js` | pass | 0.04s | OK |  | {"id":"1","success":true,"message":"Example Domain"} |
| 09-13 10:44 | 243 | `browser_get_frames` | pass | 0.01s | OK |  | {"id":"1","success":true,"frames":[{"id":"6-9AD200030BF91464D4F36359D0E12C5E","name":"","url":"https://example |
| 09-13 10:44 | 244 | `browser_fill_set_value` | pass | 0.03s | OK |  | [前置] browser_execute_js -> OK // {"id":"1","success":true,"message":"已设置: #mcpProbeInput"} |
| 09-13 10:44 | 245 | `browser_dom_query` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"Example Domain"} |
| 09-13 10:44 | 246 | `browser_get_text` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"Example Domain\n\nThis domain is for use in documentation examples without |
| 09-13 10:44 | 247 | `browser_execute_js` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"Example Domain"} |
| 09-13 10:44 | 248 | `browser_vip_fingerprint_media_devices` | fail | 0.02s | ERR_GOOD | TARGET | type=1 必须同时给 devices 设备清单(非空JSON数组) / 只传 type 时内核收到的清单为空, 设置不会产生任何效果(旧版在这里返回假成功) / 每项字段: device_id(驱动ID, 驱动属性里 |
| 09-13 10:44 | 249 | `browser_fingerprint` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"Canvas指纹已随机化 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 brows |
| 09-13 10:44 | 250 | `browser_get_global_cache_dir` | pass | 0.02s | OK |  | {"success":true,"global_cache_dir":"C:\\Users\\cxzxc\\Desktop\\MCP源码\\ai-browser-mcp\\CEFbro\\AI-Fbowser-Mcp\\ |
| 09-13 10:44 | 251 | `browser_cache_dir` | pass | 0.01s | OK |  | {"success":true,"cache_dir":"C:\\Users\\cxzxc\\Desktop\\MCP源码\\ai-browser-mcp\\CEFbro\\AI-Fbowser-Mcp\\_int\\A |
| 09-13 10:44 | 252 | `browser_fill_set_text` | pass | 0.05s | OK |  | [前置] browser_execute_js -> OK // {"id":"1","success":true,"message":"innerText 已设置并回读确认: mcp-probe-text"} |
| 09-13 10:44 | 253 | `browser_fill_get_text` | pass | 0.03s | OK |  | {"id":"1","success":true,"message":"Example Domain"} |
| 09-13 10:44 | 254 | `browser_vip_fingerprint_media_devices` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"媒体设备指纹已设置: target=audio_input, type=1, 设备数=1 / 类库原文警告: 虚拟媒体设备可能造成浏览器声音或麦克风 |
| 09-13 10:48 | 255 | `browser_find_by_hwnd` | fail | 0.02s | ERR_GOOD | TARGET | 未找到窗口句柄为 1 的浏览器 / 如何取得有效句柄: 调 browser_get_window_handle(返回当前浏览器窗口句柄) 或 browser_window_info 看 hwnd 字段; 句柄是**运行时 |
| 09-13 10:48 | 256 | `browser_find_by_hwnd` | pass | 0.00s | OK |  | {"id":"1","success":true,"data":{"id":1,"url":"https://example.com/?oopiforder=1789267526"}} |
| 09-13 10:59 | 257 | `browser_startup_args` | pass | 0.02s | OK |  | {"success":true,"applied_switches":"","command_line_raw":"\"C:\\Users\\cxzxc\\Desktop\\MCP源码\\ai-browser-mcp\\ |
| 09-13 11:12 | 258 | `browser_get_run_style` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"window_style":382664704,"is_popup":false,"browser_id":1,"runt |
| 09-13 11:12 | 259 | `browser_vip_touch_emulation` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"触摸模拟已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 11:12 | 260 | `browser_startup_args` | pass | 0.02s | OK |  | {"success":true,"applied_switches":"","command_line_raw":"\"C:\\Users\\cxzxc\\Desktop\\MCP源码\\ai-browser-mcp\\ |
| 09-13 12:04 | 261 | `browser_network_body` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"success":true,"request_id":"0FCE845C558867717FBE5980738BE65A","resolve_note" |
| 09-13 12:04 | 262 | `mcp_result` | fail | 0.00s | ERR_GOOD | TARGET | 未找到任务结果: mcp_probe / 可能原因: ①任务仍在执行(2-5秒后重试) ②request_id拼写错误 ③任务已过期被清理 / 💡大多数工具已默认sync-wait(直接返回结果), 无需手动mcp_re |
| 09-13 12:04 | 263 | `browser_set_window_style` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"窗口风格已设置 / 设置已应用! 注意: 指纹/代理/内核变更需要刷新页面才能生效, 请调用 browser_reload 或 browser_na |
| 09-13 12:05 | 264 | `mcp_result` | pass | 0.02s | OK |  | {"success":true,"message":"MCPRESULT_PROBE_992322","data":"{\"id\":\"992322\",\"success\":true,\"message\":\"M |
| 09-13 12:10 | 265 | `browser_menu_alias` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"action":"list","count":17,"aliases":[{"alias":"back","command |
| 09-13 12:14 | 266 | `browser_navigate` | pass | 0.05s | OK |  | 等待条件满足: load_end → https://example.com/ |
| 09-13 13:54 | 267 | `browser_reverse_instrument_script` | fail | 0.03s | ERR_WEAK | OTHER | 该插装已处于启用状态(重复install) / 停止拦截用 action=suppress; 彻底清除用 browser_debugger_disable |
| 09-13 13:55 | 268 | `browser_reverse_instrument_script` | pass | 1.04s | OK |  | {"id":"1","success":true,"auto_prepared":"Debugger.enable,Debugger.resume(页面原卡在断点/插装, 已自动恢复并续等原请求成功)","data":{ |
| 09-13 14:11 | 269 | `browser_debugger_pause` | pass | 0.06s | OK |  | {"id":"1","success":true,"auto_prepared":"Debugger.pause(页面原本未暂停, 已自动启用调试器域并安排执行点制造暂停点; 用完请 browser_debugger_r |
| 09-13 14:45 | 270 | `browser_menu_probe` | pass | 1.94s | OK |  | {"id":"1","success":true,"message":"已武装(30 秒内有效)并在(300,200)派发了一次右键, 但 1.5 秒内没等到菜单回调 / 实测原因: 原生右键菜单是**模态**的 ——  |
| 09-13 15:01 | 271 | `browser_reverse_preload` | pass | 0.05s | OK |  | {"id":"1","success":true,"auto_prepared":"Page.enable","data":{"success":true,"cdp_method":"Page.addScriptToEv |
| 09-13 15:01 | 272 | `browser_inject` | pass | 0.03s | OK |  | null |
| 09-13 15:02 | 273 | `browser_event` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"limit":50,"timeline_json":"[{\"event\":\"loading_state_change |
| 09-13 15:02 | 274 | `browser_collect` | fail | 0.01s | ERR_GOOD | OTHER | 未知action:  / 支持: network_enable/detail_enable/disable/get/clear, cache_enable/clear, console_enable/get/clear, |
| 09-13 15:02 | 275 | `browser_network` | fail | 0.02s | ERR_WEAK | GUARD | action 不能省略 / 可用: list(查询, 不改开关) / enable / detail_enable / disable / clear / get / network_get / 省略会隐式启用网络日志, |
| 09-13 15:02 | 276 | `browser_scrape` | pass | 0.05s | OK |  | Example Domain

This domain is for use in documentation examples without needing permission. Avoid use in oper |
| 09-13 15:02 | 277 | `browser_get_text` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"Example Domain\n\nThis domain is for use in documentation examples without |
| 09-13 15:03 | 278 | `browser_collect` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"network_enabled":true,"network_detail":false,"network_logs":[{"type":"res"," |
| 09-13 15:03 | 279 | `browser_network` | pass | 0.00s | OK |  | {"id":"1","success":true,"data":{"network_enabled":true,"network_detail":false,"network_logs":[{"type":"res"," |
| 09-13 15:35 | 280 | `browser_json` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"valid":false,"input":"text","input_length":10,"options_used": |
| 09-13 15:35 | 281 | `browser_data_uri` | pass | 0.00s | OK |  | {"id":"1","success":true,"data":{"success":true,"mime":"text/plain","data_length":9,"uri_length":35,"data_uri" |
| 09-13 15:35 | 282 | `browser_by_index` | fail | 0.01s | ERR_GOOD | OTHER | 序号 10 没有对应浏览器(当前共 1 个) / index 从 0 开始; 用 browser_list 看全部(它按 ID 清单枚举, **顺序不保证与序号一致**) / 想按 ID/标签/窗口句柄定位: brows |
| 09-13 15:35 | 283 | `browser_screenshot` | pass | 0.08s | OK |  | {"id":"1","success":true,"data":{"success":true,"via":"cdp:Page.captureScreenshot","format":"png","width":1920 |
| 09-13 15:35 | 284 | `browser_wait` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_77267937_94175_2","message":"等待已提交(what=selector value= |
| 09-13 15:36 | 285 | `browser_by_index` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"index":0,"browser_id":1,"is_popup":false,"url":"https://examp |
| 09-13 17:38 | 286 | `browser_vip_dom_node_edit` | pass | 0.06s | OK |  | {"id":"1","success":true,"data":{"action":"set_attr","method":"DOM.setAttributeValue","node_id":221,"submitted |
| 09-13 17:38 | 287 | `browser_vip_dom_search` | pass | 0.06s | OK |  | {"id":"1","success":true,"data":{"searchId":"21160.2","resultCount":2,"returned":2,"nodeIds":[231,239],"note": |
| 09-13 17:38 | 288 | `browser_vip_dom_get_document` | pass | 0.03s | OK |  | {"id":"1","success":true,"data":{"root":{"nodeId":250,"backendNodeId":1,"nodeType":9,"nodeName":"#document","l |
| 09-13 17:50 | 143+ | `browser_close` | pass | - | OK_LIVE |  | 真机实测: verify_round143_close.py 通过 // 受控第二后台浏览器, 12/12; 发现并修复: 关闭异步生效+无回读 -> 提交后轮询<=2.5s确认清单移除 |
| 09-13 17:51 | 143+ | `browser_close_try` | pass | - | OK_LIVE |  | 真机实测: verify_round144_close_try.py 通过 // 受控第二后台浏览器, 15/15; 非主浏览器直关+回读确认, 主窗口守卫拒绝, 负控可行动 |
| 09-13 17:55 | 143+ | `browser_reverse_patch` | pass | - | OK_LIVE |  | 真机实测: verify_round145_patch.py 通过 // 受控注入sourceURL探针脚本, 16/16; dry_run不替换+实改热替换+页面侧V1->V2回读 |
| 09-13 18:00 | 143+ | `browser_set_preference` | pass | - | OK_LIVE |  | 真机实测: verify_round146_preference.py 通过 // 16/16; 发现假成功: 字体类pref对既有/新建浏览器均无页面侧效果且未知名不报错 -> 回包与描述如实声明诚实边界(写入存储,  |
| 09-13 18:03 | 143+ | `browser_set_s5_proxy` | pass | - | OK_LIVE |  | 真机实测: verify_round147_s5.py 通过 // 14/14; 行为级对照: 死端口代理阻断异源导航(错误页)->清除后同导航恢复, CDP不毒化 |
| 09-13 18:06 | 143+ | `browser_shutdown` | pass | - | OK_LIVE |  | 真机实测: verify_round148_shutdown.py 通过 // 9/9; 守卫拒绝->confirm:true回包先返->进程3.6s真退出->重启可恢复 |
| 09-13 18:12 | 143+ | `browser_vip_enable_js_env` | pass | - | OK_LIVE |  | 真机实测: verify_round149_jsenv.py 通过 // 14/14; 启用/关闭双向均毒化CDP(30s)与警告一致, 重启恢复; 补了关闭路径诚实警告(原静默毒化) |
| 09-13 18:19 | 143+ | `browser_vip_mouse_wheel` | pass | - | OK_LIVE |  | 真机实测: verify_round150_wheel.py 通过 // 12/12; 修复: 调用前自动显示窗口(否则默认流程可能静默不滚)+诚实回包; 内核滚轮scrollY=700, 毒化与警告一致, 重启恢复;  |
| 09-13 18:28 | 289 | `browser_vip_get_js_env_ids` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"count":0,"ids_text":[],"ids_int":[],"note":"类库返回文本列表值: ids_te |
| 09-13 18:32 | 290 | `browser_by_id` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"browser_id":1,"is_popup":false,"is_closed":false,"hwnd":38211 |
| 09-13 18:32 | 291 | `browser_count` | pass | 0.02s | OK |  | {"id":"1","success":true,"data":{"success":true,"count":1,"id_list":"1","note":"count 与 id_list 来自两个独立类库出口(取数量 |
| 09-13 18:42 | 292 | `browser_vip_filter_patch_text` | fail | 0.02s | ERR_GOOD | OTHER | set 需要 url 与 find / replace 可留空(把目标文本删除); 对之后加载的资源生效, 刷新/重新导航后验证 |
| 09-13 18:42 | 293 | `browser_vip_filter_replace_data` | fail | 0.02s | ERR_GOOD | OTHER | set 需要 body(替换内容文本, UTF-8) 或 body_base64(二进制内容) |
| 09-13 18:43 | 294 | `browser_vip_filter_patch_text` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"文本改写已设置: https://example.com/mcp-probe-patch.txt / 诚实边界: 类库无读取接口, 无法回读; 对* |
| 09-13 18:43 | 295 | `browser_vip_filter_replace_data` | pass | 0.00s | OK |  | {"id":"1","success":true,"message":"整体资源替换已设置: https://example.com/mcp-probe-replace.txt (9 字节) / 诚实边界: 类库无读取接 |
| 09-13 18:45 | 296 | `browser_vip_filter_replace_file` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"整体资源替换已设置(文件): https://example.com/mcp-probe-replacefile.txt ← mcp_config. |
| 09-13 18:53 | 297 | `browser_vip_execute_js_context` | fail | 0.02s | ERR_GOOD | PREREQ | 未给 context_id 且自动解析环境清单失败(清单为空或解析不到 id) / 请先 browser_vip_enable_js_env 启用执行环境, 再用 browser_vip_get_js_env_ids 取 |
| 09-13 19:00 | 297 | `browser_clear_cache` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_89564750_20957_6","message":"全局缓存清理已提交 / origin= / 清理对象 |
| 09-13 19:00 | 298 | `browser_clear_cache_browser` | pass | 0.02s | OK |  | {"id":"1","success":true,"_async":true,"task_id":"task_89564906_77395_7","message":"浏览器缓存清理已提交 / origin=https: |
| 09-13 19:13 | 299 | `browser_start_download` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"下载已触发: https://example.com / 保存目录=C:\\Users\\cxzxc\\Desktop\\MCP源码\\ai-bro |
| 09-13 19:39 | 300 | `browser_set_proxy` | pass | 0.02s | OK |  | {"id":"1","success":true,"message":"S5代理已设置: mcp_probe / close_s5_error_prompt=false / 设置已应用! 注意: 指纹/代理/内核变更需要 |
| 09-13 19:57 | 301 | `browser_vip_new_tab` | pass | - | OK_LIVE |  | 真机实测: verify_round165_newtab 通过 (9/9) // 空url→高级_创建标签浏览器(browser_list新增id=2, 真实验证)并browser_close readback确认移除; |
