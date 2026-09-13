# Schema 声明 vs 实现读取 —— 参数一致性审计（B 组）

**范围（只读）**：`src/MCP_Server_Form.wsv`（填表族）、`src/MCP_Server_System.wsv`（系统族）、`src/MCP_Server_VIP.wsv`（VIP 族）
**对照来源**：`src/MCP_Server.wsv` 中每工具的 `添加工具JSON ("名", "描述", <schema>)` 注册行
**性质**：纯静态分析。**未编译、未调用 MCP、未访问运行时**；所有结论均给出 file:line 供复核。结论"实现读取了 X"来自源码文本，运行时行为（如 yjson 对非数值节点的取值）已在文中标注为需实测的部分。

---

## 0. 审计口径（先说清 3 个容易搞错的点）

### 0.1 行号口径
`MCP_Server_System.wsv` 与 `MCP_Server_Form.wsv` 行尾为 `CR CR LF`，PowerShell `Select-String` / Python `splitlines` 给出的行号约为本报告行号的 **2 倍**。
本报告全部行号 = **LF 口径**（DSH `read` / `grep`），并在每条差异里附锚点原文便于重定位。
文件内行锚点速查：

| 文件 | 方法声明行 | 首分支行 | 末分支行 | 文件总行数 |
|---|---|---|---|---|
| `src/MCP_Server_Form.wsv` | 7 | 12 `如果 (方法名 == "browser.fill_set_value" \|\| 方法名 == "browser_fill_set_value")` | 465 `否则 (方法名 == "browser_fill_form")` | 706 |
| `src/MCP_Server_System.wsv` | 9 | 16 `如果 (方法名 == "browser_create_tab")` | 197 `否则 (方法名 == "browser_shutdown")` | 229 |
| `src/MCP_Server_VIP.wsv` | 6 | 12 `如果 (方法名 == "browser_vip_websocket_intercept")` | 1919 `否则 (方法名 == "browser_vip_set_is_trusted")` | 1940 |

### 0.2 required 的真实语义（很关键，直接影响 REQUIRED_MISMATCH 的判定）
`MCP_Server.wsv:11763-11782`：
```
方法 单参数Schema文本 ...
参数 必须 <类型 = 逻辑型 @默认值 = 真 @输出名 = "Must">
... 如果 (必须) { s = s + ",\"required\":[\"" + 名 + "\"]" }
```
⇒ **凡是用 `单参数Schema文本(...)` 且没传第 4 个参数的注册行，该参数一律是 `required`**（例如 `browser_fingerprint_appname` 的 `value`、`browser_vip_set_css_version` 的 `version`）。
`双XY_Schema文本` 恒把两参都写进 `required`（`MCP_Server.wsv:11790`）；`多属性Schema文本` 的 required 取决于第 2 参，传 `""` 就是**一个都不必填**（`MCP_Server.wsv:11793-11805`）；`添加工具JSON` 缺省 schema 为 `{"type":"object"}` 无属性（`MCP_Server.wsv:11605`）。

### 0.3 公共层参数检查（避免 DECLARED_UNUSED 误报）
在 `src/MCP_Server.wsv` 全文 grep 公共层参数名的结果：
- `browser_id`：**由公共层读取** —— `MCP_Server.wsv:12131` `请求浏览器ID = yyjson取整数 (参数JSON, "browser_id")`，并 `12133 目标浏览器ID = 请求浏览器ID`。
- `async_only`：公共层 —— `MCP_Server.wsv:1584`、`5960`、`5987`、`6829`。
- `sync_wait`：公共层 —— `MCP_Server.wsv:5964` `如果 (yyjson取逻辑 (参数JSON, "sync_wait"))`。
- `max_ms`：公共层 —— `MCP_Server.wsv:4140`、`7017`。
- `auto_enable`：**在 `MCP_Server.wsv` 中 grep 到 0 处按名读取**（仅出现在 `browser_network` 的描述文本 `11266` 里）；本范围三个文件也都没有任何工具声明它，故不构成差异。
- 结论：本范围 **93 个工具**里，**没有任何一个**声明了 `browser_id / async_only / sync_wait / max_ms / auto_enable`，因此不存在"被公共层读取却被误判为未使用"的情形。

### 0.4 机械取证方式（可复现）
- 分支清单：`grep '方法名 == "browser_'` 三个文件 → Form 12 处、System 10 处（+ `ping` 1 处，共 11 分支）、VIP 72 处。
- 实现读取的参数名：脚本按 `参数JSON, "X"` 抽取去重 → Form 8 个（`attribute event fields frame_id selector submit text value`）、System 7 个（`action confirm data delay_seconds name style type`）、VIP 106 个（含 `confirm`、`x`、`y`、`delta_x`、`delta_y` 等）。
- 注册行属性/必填：脚本解析每条 `添加工具JSON` 行里的 `属性项JSON ("X"` / `单参数Schema文本 ("X"` / `双XY_Schema文本 ("X","Y"`。
- **逐字集对比结果**：Form 的 8 个实现读取名与 Form 12 个工具的声明属性**集合完全相等**（8=8）；System 的 7 个与声明集合**完全相等**（7=7）；VIP 中唯一"实现了读取但所属工具的 schema 未声明"的名字是 `confirm`（属 `browser_vip_enable_js_env`），另有 `x`/`y`（属 `browser_vip_touch_cancel`，该工具 schema 为空，故 `x`/`y` 在全文件尺度上"看似已声明"而逃过集合对比，必须逐工具比对才能发现）。

---

## 1. 扫描覆盖（93 个已注册工具 + 2 个未注册分支）

判定列：`OK` = 声明属性与实现读取逐项一致且无守卫矛盾；`#N` = 见第 2 节差异表第 N 条。

### 1.1 填表族 `src/MCP_Server_Form.wsv`（12 个工具）

| 工具名 | 分派锚点(LF) | 注册行 | schema 属性(必填) | 实现读取(行) | 判定 |
|---|---|---|---|---|---|
| browser_fill_set_value | 12 | 11315 | selector,value,frame_id (selector,value) | selector 15 / value 17 / frame_id 27 | OK |
| browser_fill_click | 43 | 11316 | selector,frame_id (selector) | selector 46 / frame_id 56 | OK |
| browser_fill_focus | 72 | 11317 | selector,frame_id (selector) | selector 75 / frame_id 85 | OK |
| browser_fill_scroll | 101 | 11318 | selector,frame_id (selector) | selector 104 / frame_id 114 | OK |
| browser_fill_exists | 130 | 11319 | selector,frame_id (selector) | selector 133 / frame_id 143 | OK |
| browser_fill_attr_get | 206 | 11320 | selector,attribute,frame_id (**selector,attribute**) | selector 209 / attribute 211 / attr=="" 分支 250 / frame_id 271 | **#1** |
| browser_fill_get_text | 286 | 11321 | selector,frame_id (selector) | selector 289 / frame_id 304 | OK |
| browser_fill_set_text | 326 | 11322 | selector,text,frame_id (selector,text) | selector 329 / text 331 / 参数键存在 text 336 / frame_id 350,363 | OK |
| browser_fill_attr_set | 158 | 11323 | selector,attribute,value,frame_id (**selector**) | selector 161 / attribute 163 / value 165 / frame_id 190 | **#2** |
| browser_fill_trigger | 376 | 11324 | selector,event,frame_id (selector) | selector 379 / event 381(缺省 click 384) / frame_id 395 | OK |
| browser_fill_select | 411 | 11325 | selector,value,frame_id (**selector**) | selector 414 / value 416 / frame_id 426 | **#3** |
| browser_fill_form | 465 | 11539 | fields,submit,frame_id (fields) | fields 469,473 / submit 598 / frame_id 490 | **#14** |

### 1.2 系统族 `src/MCP_Server_System.wsv`（9 个已注册 + 2 个未注册分支）

| 工具名 | 分派锚点(LF) | 注册行 | schema 属性(必填) | 实现读取(行) | 判定 |
|---|---|---|---|---|---|
| browser_create_tab | 16 | **无（未注册）** | — | 无（恒返回失败 18） | 见 §4.1 |
| browser_task_runner_post | 20 | **无（未注册）** | — | 无（恒返回失败 22） | 见 §4.1 |
| browser_send_message | 25 | 11308 | name,data (name) | name 28 / data 34 | **#4** |
| browser_startup_args | 47 | 11373 | action (**无必填**) | action 53（缺省 get 50） | OK |
| browser_get_global_cache_dir | 74 | 11374 | — | 无 | **#5** |
| browser_get_process_type | 110 | 11375 | — | 无 | OK |
| browser_get_window_style | 117 | 11370 | — | 无 | OK |
| browser_set_window_style | 127 | 11371 | type,style (**type,style**) | type 135 / style 参数键存在 141 / style 145 | **#13** |
| browser_get_run_style | 151 | 11372 | — | 无 | **#6** |
| ping | 188 | 11329 | — | 无 | OK |
| browser_shutdown | 197 | 11244 | confirm,delay_seconds (confirm) | confirm 201 / delay_seconds 207 | **#12** |

### 1.3 VIP 族 `src/MCP_Server_VIP.wsv`（72 个工具，全部已注册）

| 工具名 | 分派锚点(LF) | 注册行 | schema 属性(必填) | 实现读取(行) | 判定 |
|---|---|---|---|---|---|
| browser_vip_websocket_intercept | 12 | 11314 | enable (enable) | enable 15 / 参数键存在 enable 24 | OK |
| browser_set_s5_proxy | 44 | 11354 | address,username,password (address) | 47,60 | OK |
| browser_vip_mouse_click | 68 | 11356 | x,y,button (x,y) | 79,81,91 | OK |
| browser_vip_mouse_move | 98 | 11357 | x,y (x,y) | 109,113 | OK |
| browser_vip_key_press | 120 | 11359 | key_code (key_code) | 123 | OK |
| browser_vip_key_release | 143 | 11360 | key_code (key_code) | 146 | OK |
| browser_vip_clear_s5_proxy | 167 | 11355 | — | 无 | OK |
| browser_vip_enable_inspector | 184 | 11416 | enable (enable) | enable 190,192,193,204-222 | **#8 / #9** |
| browser_vip_enable_js_env | 250 | 11411 | enable (enable) | enable 261,267,271 / **confirm 267** | **#A** |
| browser_vip_get_js_env_ids | 285 | 11412 | — | 无 | OK |
| browser_vip_touch_cancel | 321 | 11415 | **(空 schema)** | **x 331 / y 331** | **#B** |
| browser_vip_disable_debugger | 339 | 11369 | disable (disable) | 349 | OK |
| browser_fingerprint_plugins | 357 | 11376 | type,json (无) | 367 | OK（见 §4.2） |
| browser_fingerprint_appname | 374 | 11377 | value (value) | 384 | OK |
| browser_fingerprint_languages | 391 | 11380 | languages,reset (无) | 394,396 | **#10** |
| browser_fingerprint_webgl_vendor | 422 | 11381 | vendor,renderer (vendor) | 425,431 | OK |
| browser_font_randomize | 453 | 11382 | action,count,seed (无) | 456,466,468 | **#16** |
| browser_fingerprint_cookie_enabled | 547 | 11406 | value (value) | 557 | OK |
| browser_fingerprint_java_enabled | 564 | 11407 | value (value) | 574 | OK |
| browser_fingerprint_online | 581 | 11408 | value (value) | 592,596 | OK |
| browser_fingerprint_appcodename | 604 | 11409 | value (value) | 614 | OK |
| browser_fingerprint_appversion | 621 | 11410 | value (value) | 631 | OK |
| browser_fingerprint_product_sub | 638 | 11417 | value (value) | 648 | OK |
| browser_fingerprint_vendor_sub | 655 | 11418 | value (value) | 665 | OK |
| browser_vip_fingerprint_canvas_fixed | 673 | 11419 | value (value) | 683 | OK |
| browser_vip_fingerprint_webgl_fixed | 690 | 11421 | value (value) | 700 | OK |
| browser_vip_fingerprint_audio_fixed | 707 | 11422 | value (value) | 717 | OK |
| browser_vip_fingerprint_rect | 725 | 11424 | x,y,w,h (无) | 735 | OK |
| browser_fingerprint_pixel_ratio | 742 | 11378 | value (**text**) (value) | **752 取小数** | **#17** |
| browser_fingerprint_touch_enable | 759 | 11379 | enable,points (无) | 769 | OK（见 §4.2） |
| browser_fingerprint_screen_xy | 777 | 11387 | x,y (x,y) | 787 | OK |
| browser_vip_mouse_press | 795 | 11388 | x,y (x,y) | 805 | OK |
| browser_vip_mouse_release | 812 | 11389 | x,y (x,y) | 822 | OK |
| browser_vip_mouse_wheel | 829 | 11358 | x,y,delta_x,delta_y (**x,y**) | 840,844,848 | **#11** |
| browser_vip_fingerprint_webrtc | 856 | 11405 | public_ip,local_ip,host,disable (无) | 862 | OK |
| browser_vip_fingerprint_timezone | 867 | 11425 | offset_h,offset_m,name,iana (无) | 873 | OK |
| browser_vip_fingerprint_geolocation | 878 | 11426 | lat,lng,accuracy (lat,lng) | 886,888,890 | **#18** |
| browser_vip_fingerprint_ssl | 908 | 11427 | tls_min,tls_max,ciphers (无) | 918,919,923 | **#7** |
| browser_vip_fingerprint_canvas | 928 | 11428 | min,max,seed (无) | 935 | OK |
| browser_vip_fingerprint_webgl | 940 | 11429 | min,max,seed (无) | 947 | OK |
| browser_vip_fingerprint_audio | 952 | 11430 | min,max,seed (无) | 959 | OK |
| browser_vip_fingerprint_font | 964 | 11431 | font_list,w_offset,h_offset (无) | 970 | OK |
| browser_vip_fingerprint_canvas_font | 975 | 11420 | value (value) | 983 | OK |
| browser_vip_fingerprint_viewport | 988 | 11432 | top,left,width,height (无) | 995 | OK |
| browser_vip_fingerprint_screen | 1000 | 11433 | width,height,avail_w,avail_h,depth,pixel_depth (无) | 1006-1009 | OK |
| browser_vip_fingerprint_hardware | 1014 | 11434 | concurrency,memory (无) | 1020,1021 | OK |
| browser_vip_fingerprint_product | 1026 | 11435 | product,product_sub,vendor,vendor_sub (无) | 1032-1035 | OK |
| browser_vip_fingerprint_battery | 1040 | 11436 | charging,level,charging_time,discharging_time (无) | 1046-1049 | **#19** |
| browser_vip_fingerprint_media_devices | 1054 | 11437 | target,type,devices (**target,type**) | 1060,1065,1071,1082 | **#E** |
| browser_vip_key_click | 1144 | 11361 | key_code (key_code) | 1147 | OK |
| browser_vip_key_input | 1167 | 11392 | char_code (char_code) | 1170 | OK |
| browser_vip_key_type | 1195 | 11393 | text (text) | 1198 | OK |
| browser_vip_set_css_version | 1219 | 11383 | version (version) | 1222 | **#20** |
| browser_vip_set_web_version | 1248 | 11384 | version (version) | 1251 | **#20** |
| browser_vip_set_v8_version | 1277 | 11385 | version (version) | 1280 | **#20** |
| browser_vip_send_devtools_msg | 1306 | 11386 | json (json) | 1317(**取JSON文本**)+1320(取文本回退) | OK |
| browser_refresh_cookies | 1334 | 11362 | — | 无 | OK |
| browser_get_all_cookies | 1339 | 11363 | — | 无 | OK |
| browser_set_preference | 1350 | 11364 | name,value (**name**) | 1362,1363 | **#F** |
| browser_vip_load_extension | 1405 | 11439 | path,crx_path (无) | 1408,1410 | **#G** |
| browser_vip_unload_extension | 1450 | 11440 | extension_id (extension_id) | 1453 | OK |
| browser_vip_extension_info | 1467 | 11441 | extension_id (extension_id) | 1470 | OK |
| browser_vip_execute_js_context | 1493 | 11442 | code,target,frame_index,context_id,frame_id (**无**) | 1496,1504,1506,1508,1510 | **#H** |
| browser_vip_dom_get_document | 1565 | 11444 | depth (**无必填**) | 1573 | **#21** |
| browser_vip_dom_search | 1592 | 11445 | query,search_id (无) | 1595,1603 | OK |
| browser_vip_enable_devtools_observer | 1629 | 11443 | enable (enable) | 1637,1639,1647-1662 | **#9** |
| browser_vip_touch_emulation | 1686 | 11446 | enable,max_points,mode,configuration (无) | 1692,1696,1706,1732 | **#I** |
| browser_fingerprint_ua | 1738 | 11448 | ua,platform,accept_lang,mobile,architecture,bitness,model,wow64,platform_version,full_version,brands,full_version_list (无) | 1746-1793 全部 12 个 | OK |
| browser_vip_orientation | 1801 | 11449 | type,angle (无) | 1810,1811 | **#22** |
| browser_get_extra_data | 1839 | 11447 | — | 无 | OK |
| browser_vip_disable_console | 1868 | 11423 | log,warn,error,debug,info,trace,clear,assert,dir,table,time,count,group,profile,performance,performance_min_ms,performance_max_ms (无) | 1878-1911 全部 17 个 | OK |
| browser_vip_set_is_trusted | 1919 | 11414 | enable (enable) | 1930 | OK |

---

## 2. 差异表（31 条）

**差异类型图例**：`MISSING_IN_SCHEMA`（实现读但未声明，最严重）／`DECLARED_UNUSED`（声明了但实现从不读）／`ACTION_MISMATCH`／`ENUM_MISMATCH`／`DESC_PROMISE`／`REQUIRED_MISMATCH`
**file 图例**：`F=` `src/MCP_Server_Form.wsv`，`S=` `src/MCP_Server_System.wsv`，`V=` `src/MCP_Server_VIP.wsv`，`R=` `src/MCP_Server.wsv`（注册行）。行号均为 LF 口径。

| 工具名 | 差异类型 | 实现读的参数(附 file:line) | schema 声明的属性 | 影响(一句话) | 建议修法(一句话) |
|---|---|---|---|---|---|
| #A browser_vip_enable_js_env | MISSING_IN_SCHEMA | `confirm` — V:267 `如果 (MCP命令服务器.yyjson取逻辑 (参数JSON, "enable") && MCP命令服务器.参数键存在 (参数JSON, "confirm") == 假)` → 返回失败；另 V:274-275 读 enable 维护状态 | R:11411 `单参数Schema文本 ("enable", "boolean", "启用/关闭")` ⇒ properties 只有 enable，**无 confirm**（全文件 grep `"confirm"` 仅命中 R:11212 browser_delete_cookies、R:11244 browser_shutdown，公共层不处理它） | 代理看不到 confirm 这个参数，而 R:11442 与 V:1517 的文案都要求"先调 `{enable:true, confirm:true}`" ⇒ 代理按 schema 只传 enable 必定被拒，无法一次调用成功 | 把 R:11411 改为 `多属性Schema文本(enable + confirm)`，描述写"启用为破坏性操作需 confirm:true"，required 视策略取 `"enable"` 或 `"enable","confirm"` |
| #B browser_vip_touch_cancel | MISSING_IN_SCHEMA | `x`、`y` — V:331 `vip_ctrl.高级触摸_取消 (MCP命令服务器.yyjson取整数 (参数JSON, "x"), MCP命令服务器.yyjson取整数 (参数JSON, "y"))` | R:11415 第 3 参为 `空Schema文本 ()` ⇒ `{"type":"object"}` 无任何属性、无描述参数 | 代理完全不知道能指定取消坐标，只能以缺省(取整数→0)去取消 (0,0) 处的触摸点 ⇒ 取消错位置且工具回"触摸取消"成功(静默无效) | R:11415 改用 `多属性Schema文本(x + y)`，描述写"缺省 0=取消(0,0)处的触摸点" |
| #C browser_vip_touch_emulation | REQUIRED_MISMATCH | `enable` 在 mode=mouse 路径**缺省即被当作 false** — V:1705-1706 `转触摸启用 = MCP命令服务器.yyjson取逻辑 (参数JSON, "enable")`；V:1712-1715 走 `{"enabled":false}`；V:1726 回成功文案"已关闭鼠标转触摸(CDP)" | R:11446 `enable`(boolean,"启用(true)/撤销(false)") + max_points + mode + configuration，**required 为空**(第 2 参 `""`) | 代理只传 `{mode:"mouse"}`（最自然的写法，因为描述说"mode=mouse 时走 CDP"）会把已开启的鼠标转触摸**静默关掉**，且回包是 success ⇒ 反向操作被当成成功 | 描述里写明"mode=mouse 时 enable 必须显式传 true"，或实现把缺省改为 `真`（`yyjson取逻辑_默认(参数JSON,"enable",真)`） |
| #7 browser_vip_fingerprint_ssl | ENUM_MISMATCH | V:918-919 取整数 tls_min/tls_max → V:921-922 `MCP_服务器工具.整数到TLS版本`；映射只认 0/769/790/791/792（`MCP_Server_Utils.wsv:43-65`，常量值见 `MCP_Constants.wsv:59-62`），**未知值静默返回 TLS版本.空**（Utils:63-65 仅控制台打警告） | R:11427 描述只有 "TLS最小版本" / "TLS最大版本"（integer），无取值表 | 代理按直觉传 1/2/3 会拿到"SSL加密套件已设置"成功文案，但内核实际**不限制 TLS 版本**（假成功，且是安全语义上最危险的一类静默降级） | 描述补 "0=不限/769=TLS1.0/790=TLS1.1/791=TLS1.2/792=TLS1.3"，并把未知值从"静默回退"改为明确报错 |
| #1 browser_fill_attr_get | REQUIRED_MISMATCH | `attribute` **可省略** — F:225 `如果 (attr != "")` 走 HTML 属性；F:250-269 `否则` 走 textContent（哨兵 `__MCP_TEXT__`），F:233/257 用 attribute 判断框架错误分支 | R:11320 required = `"selector","attribute"`，而同一行描述明写"**省略 attribute 则返回元素文本(textContent)**" | schema 与自己的描述直接矛盾：严格 MCP 客户端会强制要求 attribute ⇒ 代理无法使用描述承诺的"省略取 textContent"路径，只能用另一套工具绕行 | 注册行的 required 去掉 attribute（保留 selector） |
| #2 browser_fill_attr_set | REQUIRED_MISMATCH | `attribute` 实现**硬要求非空** — F:170-174 `如果 (删首尾空 (attr) == "") { 返回 (... "attribute 不能为空 ...") }`；F:177-184 还按值做安全白名单拒绝 | R:11323 required 只有 `"selector"`（attribute/value 都可选） | 代理按 schema 省略 attribute 会立刻拿到失败响应（白跑一轮），而 schema 本可以提前拦住 | required 加 attribute（value 亦建议加，见下条同型） |
| #3 browser_fill_select | REQUIRED_MISMATCH | `value` 实现**硬要求非空** — F:435-438 `如果 (value == "") { 返回 (... "value 不能为空 ...") }` | R:11325 required 只有 `"selector"` | 代理省略 value 时只会在运行期失败，多一轮试错 | required 加 value |
| #F browser_set_preference | REQUIRED_MISMATCH | `value` 实现**硬要求非空** — V:1368-1371 `如果 (值文本 == "") { 返回 (... "缺少参数: value(首选项值)") }` | R:11364 required 只有 `"name"` | 代理省略 value 时运行期才失败，多一轮试错 | required 加 value |
| #H browser_vip_execute_js_context | REQUIRED_MISMATCH | `code` 必填 — V:1496-1497 `如果 (jsCode != "")` 与 V:1562 `返回 (... "需要code参数")`；`frame_index` 在 target=frame_index 时必填 — V:1541-1546 `如果 (frmIndex < 0) { 返回 (... "需要 frame_index ...") }` | R:11442 required 为空（第 2 参 `""`）；描述只写 "需 frame_index" 但未标必填 | 代理漏 code 或漏 frame_index 会在运行期失败一次；而 code 是本工具唯一必填项，schema 却标可选 | required 加 code，并在 frame_index 描述里写明"target=frame_index 时必填" |
| #10 browser_fingerprint_languages | REQUIRED_MISMATCH | 二者**至少给一个** — V:394 reset(缺省假) + V:396 languages；V:397-400 `如果 (langReset == 假 && langText == "") { 返回 (... "languages 不能为空 ... 恢复默认请传 reset:true") }` | R:11380 required 为空（languages / reset 都标可选） | 代理空参调用直接失败，schema 无法表达"二选一"，只能读描述 | 描述写"languages 与 reset 至少给一个"，或用 anyOf 表达 |
| #11 browser_vip_mouse_wheel | REQUIRED_MISMATCH | `delta_x` 或 `delta_y` **至少一个** — V:844-847 `如果 (参数键存在 (参数JSON,"delta_y") == 假 && 参数键存在 (参数JSON,"delta_x") == 假) { 返回 (... "必须提供 delta_y 或 delta_x ...") }`；V:840 还要求 x、y 同时存在 | R:11358 required 只有 `"x","y"`（delta_x/delta_y 皆可选） | 代理只传 x,y 想"滚一点"必定失败，schema 未提示"必须给滚动量" | 描述写明"delta_x/delta_y 至少给一个"，或用 anyOf 表达 |
| #E browser_vip_fingerprint_media_devices | REQUIRED_MISMATCH | `devices` 在 type=1/2 时**硬要求非空** — V:1079 `如果 (medType != 0)` → V:1082 取 devices → V:1085-1088 空则返回失败 "type=N 必须同时给 devices 设备清单(非空JSON数组)" | R:11437 required 只有 `"target","type"`（devices 可选） | 描述里确实写了"type=1或2 必须同时给 devices"，但**机器可读的 schema 未表达** ⇒ 只读 schema 的客户端/代理会漏 | 用 `if target/type` 的 JSON Schema 条件（或 allOf/anyOf）表达 devices 的条件必填 |
| #G browser_vip_load_extension | REQUIRED_MISMATCH | `path` 或 `crx_path` **至少一个** — V:1411-1414 `如果 (extCRX == "" && ext目录 == "") { 返回 (... "需要 path ... 或 crx_path ... 之一") }` | R:11439 required 为空（两者皆可选） | 代理空参调用直接失败；schema 无法表达"二选一" | 描述写"两者给其一即可"（已有）+ 用 anyOf 表达 |
| #4 browser_send_message | DESC_PROMISE | 实现**只能广播到渲染进程** — S:41 `browser.进程间消息_发送数据_到全部渲染进程 (msgName, 文本到UTF8 (msgData, 假))`；S:39-40 注释明写"发送数据_到主进程 为渲染进程专用API(**主进程调用恒失败**); 主进程应经 发送数据_到全部渲染进程 下发" | R:11308 描述 = "**向主进程发消息**"（name 必填 + data） | 代理以为主进程会收到消息，实际消息只到渲染进程，且渲染侧必须自己注册 `进程间消息_收到主进程消息` 事件才看得到 ⇒ 按描述构造的调用语义与实现不符 | 描述改为"向**全部渲染进程**广播消息(主进程无法接收, 见 S:39-41)" |
| #5 browser_get_global_cache_dir | DESC_PROMISE | 实现**不调类库**，按启动开关推导路径并新增字段 — S:83-84 `是否Stdio = MCPStdio桥.是否为Stdio模式 ()`、S:86-93 拼 `CacheData\GlobalData_Stdio` 或 `CacheData\GlobalData`、S:94-95 `缓存目录来源 = "derived: ... 非内核回报值"`、S:106 回包加入 `cache_dir_source`；S:81-82 注释："类库 FBrowser_取初始化缓存目录() 本机**编译不过**(FBroLib.v:155 error C3861 IsEmpty), 故此处不做类库读取" | R:11374 描述 = "**真值取自类库 FBrowser_取初始化缓存目录()**; ... | 旧实现硬编码 GlobalData, stdio 分支下会静默返回错值"（未提 cache_dir_source 字段） | 描述把推导值说成"类库真值"，代理会把该路径当权威值用于比对/清理；且不知道回包里多出的 `cache_dir_source` 字段的语义 | 描述改为"按 main.wsv 同一开关(是否为Stdio模式)**推导**的路径, 类库读取器本机编译不过(见 S:81-82); 回包 cache_dir_source 标明来源" |
| #6 browser_get_run_style | DESC_PROMISE | 实现回包里的 note 明确写**实测为 1** — S:183 `加入文本成员 ("runtime_style_note", "runtime_style 来自 CEF CefRuntimeStyle(0默认/1谷歌/2经典); 本机实测为 1(谷歌) —— 该值由类库默认给出, 本项目未显式设置 窗口信息.运行风格; ...")`；S:167-171 取枚举并转整数 | R:11372 描述 = "...以及 CEF 的 runtime_style(0默认/1谷歌/2经典, 附 runtime_style_name)。注意: 本项目创建浏览器时未设置 窗口信息.运行风格, **故 runtime_style 当前恒为 0**" | 描述断言"恒为 0"、实现注释断言"实测为 1"，两者直接冲突；代理若按描述写死 0 做判断（如"等于0说明是默认风格"）会误判 | 把 R:11372 的描述改为与 S:183 一致（"实测为 1(谷歌)，由类库默认给出"） |
| #9 browser_vip_enable_inspector | DESC_PROMISE | 实现成功文案**推翻**了描述 — V:242 `返回 (... "监管者事件已关闭 | 已注销 CDP 观察者(cdp_ready=false) | 实测纠正: 下一次 CDP 调用会自动重新注册观察者并自愈, 通常无需重启(旧文案'需重启进程才能恢复'与实测不符)")` | R:11416 描述 = "⚠ **关闭后全部 CDP 类工具(debugger_*/cdp_*/reverse CDP类)立即失效, 需重启进程才能恢复。**因此本工具要求显式表态: ..." | 描述把"关闭"描述成不可逆的致命操作，代理会因此**不敢关闭/不敢调用本工具**，而实测可自愈；描述与实现的回包文案互相打脸，代理无法判断该信谁 | 描述改为"关闭会注销 CDP 观察者(cdp_ready=false)，下一次 CDP 调用会自动重新注册并自愈，通常无需重启；仅重注册失败时需重启" |
| #9b browser_vip_enable_devtools_observer | DESC_PROMISE | 实现成功文案**推翻**了描述 — V:1680 `返回 (... "DevTools消息监听已关闭 | ... 实测纠正: 关闭**不是**永久的 —— 下一次 CDP 调用会自动重新注册观察者(cdp_ready 回到 true), 通道自愈, 通常无需重启进程(旧文案声称'需重启进程才能恢复', 与实测不符) | 仅当重注册失败(控制器侧仍持有旧观察者)时 CDP 类工具才持续不可用 ...")` | R:11443 描述 = "⚠ **关闭会使全部 CDP 类工具(debugger_*/cdp_*/reverse CDP类)失效且需重启进程才能恢复**, 故关闭必须显式传 enable 的字符串值 false; ..." | 与 #9 同因：描述里的"需重启"是旧文案；代理被劝阻去关闭观察者 | 同 #9 的修法 |
| #8 browser_vip_enable_inspector | ENUM_MISMATCH | 取值白名单比描述**更宽** — V:204-213 `如果 (开关文本 == "false" \|\| 开关文本 == "0" \|\| 开关文本 == "off") {...} 否则 (开关文本 == "true" \|\| 开关文本 == "1" \|\| 开关文本 == "on")`；另有 V:214-221 `否则 (开关文本 == "")` 分支 | R:11416 描述只写 "启用传字符串 true(或布尔 true), 关闭必须传字符串 false"（单参数类型 "string"） | 影响较小（偏宽松方向）：代理不知道 `1/0/on/off` 也可用，遇到"必须传字符串 false"的限制时可能放弃；同型缺陷见 browser_vip_enable_devtools_observer V:1647-1662 | 描述补 "也接受 1/0/on/off" |
| #20 browser_vip_set_css_version | ENUM_MISMATCH | 只接受 **116~135 的纯数字字符串** — V:1237 `如果 (cssVer < MCP_常量.内核版本最小 \|\| cssVer > MCP_常量.内核版本最大 \|\| 到文本 (cssVer) != cssVerText) { 返回 (... "内核版本须为116-135范围内的纯数字(官方API支持值)") }`；常量 `MCP_Constants.wsv:51-52`(116/135) | R:11383 `单参数Schema文本 ("version","text","版本号")` ⇒ 描述只有"版本号"三个字 | 代理不知道取值范围与"必须纯数字"，传 `"120.0"`/`100`/`136` 才在运行期被拒，白跑一轮且报错文案里才有范围 | 描述写 "116~135 的纯数字字符串(官方API支持值)" |
| #20b browser_vip_set_web_version | ENUM_MISMATCH | 同 #20 — V:1266 同一守卫 | R:11384 `单参数Schema文本 ("version","text","版本号")` | 同 #20 | 同 #20 |
| #20c browser_vip_set_v8_version | ENUM_MISMATCH | 同 #20 — V:1295 同一守卫 | R:11385 `单参数Schema文本 ("version","text","版本号")` | 同 #20 | 同 #20 |
| #22 browser_vip_orientation | ENUM_MISMATCH | 取值表**只存在于代码里** — V:1813-1832 `如果 (orient_int == 1) 竖屏16_9 / ==2 竖屏4_3 / ==3 横屏16_9 / ==4 横屏4_3 / 否则 默认` | R:11449 `属性项JSON ("type","integer","方向类型")` + `angle` | 代理无法知道 1..4 分别是什么方向，只能试错；传 0 或 5 会**静默落到"默认"**并回成功 | 描述补 "1=竖屏16:9 / 2=竖屏4:3 / 3=横屏16:9 / 4=横屏4:3 / 其它=默认" |
| #21 browser_vip_dom_get_document | ENUM_MISMATCH | 缺省 3、上限 10 — V:1573 `dDepth = yyjson取整数 (参数JSON,"depth")`、V:1574-1577 `如果 (dDepth == 0) { dDepth = 3 }`、V:1578-1581 `如果 (dDepth > 10) { 返回 (... "depth 最大为10 ...") }` | R:11444 `单参数Schema文本 ("depth","integer","深度", 假)` ⇒ 描述仅"深度"，且标为**非必填** | 代理不知道缺省是 3、更不知道 >10 会直接失败，取大页面结构时容易踩上限 | 描述写 "缺省3, 上限10(超过会失败)" |
| #16 browser_font_randomize | ENUM_MISMATCH | `count` 上限 = 候选池 20 个，超出被**静默钳制** — V:499 候选池 20 个字体、V:505-508 `如果 (frCount > fr剩余.取成员数 ()) { frCount = fr剩余.取成员数 () }` | R:11382 `count`("随机挑选的字体个数(默认0=用库默认)") | 代理传 count=50 以为设了 50 个字体，实际只设 20 个（回包 count 会显示 20，需自行比对才能发现） | 描述写 "上限=候选池大小(20)，超出会被钳制" |
| #18 browser_vip_fingerprint_geolocation | ENUM_MISMATCH | 取值范围**未声明**且按小数读取 — V:891-902 `如果 (geoLat < -90 \|\| geoLat > 90) {...失败}`、`如果 (geoLng < -180 \|\| geoLng > 180)`、`如果 (geoAcc < 0)`；V:886-890 三者均 `yyjson取小数` | R:11426 `lat`/`lng`(text, required) + `accuracy`(text) | 代理不知道范围，也不知道必须传**数值**（schema 标 text，实现按小数读）⇒ 越界或传字符串都要多跑一轮 | lat/lng/accuracy 类型改 number 并在描述里写范围(-90~90 / -180~180 / >=0) |
| #17 browser_fingerprint_pixel_ratio | ENUM_MISMATCH | 按**小数**读取 — V:752 `vip_ctrl.指纹_虚拟DevicePixelRatio (MCP命令服务器.yyjson取小数 (参数JSON, "value"))` | R:11378 `单参数Schema文本 ("value","text","如1.5")` ⇒ 类型是 **text**，示例是字符串 "如1.5" | 代理按 schema 传字符串 `"1.5"`，实现却走"取小数"路径：对非数值节点的取值行为需实测确认，若不成立则会把像素比设成 0（静默错值） | 类型改 `number`（或实现加 `文本到小数` 兼容字符串） |
| #19 browser_vip_fingerprint_battery | ENUM_MISMATCH | 三个字段按**小数**读取 — V:1047-1049 `指纹_虚拟BatteryManagerLevel (…yyjson取小数 (参数JSON,"level"))`、`…ChargingTime (…"charging_time")`、`…DischargingTime (…"discharging_time")` | R:11436 `level`("电量0-1")、`charging_time`("充电时间")、`discharging_time`("放电时间") **三者类型均为 text** | 同 #17：按 schema 传字符串会被"取小数"处理，可能得到 0（电池指纹被设成 0/0/0，比不设置更异常） | 三者类型改 `number` |
| #13 browser_set_window_style | ENUM_MISMATCH | `type` 白名单只认 3 个值 — S:136-139 `如果 (窗口类型 != MCP_常量.窗口样式_GWL_STYLE && != GWL_EXSTYLE && != GWL_ID) { 返回 (... "非法窗口属性类型(...) \| 支持: ...") }`；常量值 `MCP_Constants.wsv:53-55` = -16 / -20 / -12 | R:11371 `属性项JSON ("type","integer","风格类型")` ⇒ 描述只写"风格类型"，无取值表 | 代理只能猜 Win32 GWL 索引值；好在猜错会收到带合法值的失败文案（可自诊断），但仍白跑一轮 | 描述补 "-16=GWL_STYLE / -20=GWL_EXSTYLE / -12=GWL_ID" |
| #12 browser_shutdown | ENUM_MISMATCH | `delay_seconds` 被**静默钳制**到 1~3 — S:208-216 `如果 (延迟秒 <= 0) { 延迟秒 = 1 }` / `如果 (延迟秒 > 3) { 延迟秒 = 3 }`（S:212 注释"产品保留最长3秒关闭延迟"） | R:11244 `属性项JSON ("delay_seconds","integer","延迟秒")` ⇒ 描述无范围 | 代理传 `delay_seconds: 10` 以为有 10 秒缓冲（够自己收尾/落盘），实际 3 秒后进程就关闭 ⇒ 且关闭不可回退 | 描述写 "1~3 秒(小于1按1、大于3按3钳制)" |
| #14 browser_fill_form | ENUM_MISMATCH | fields 上限 500 + 存在性预检语义未声明 — F:501-504 `如果 (ff总数 > 500) { 返回 (... "fields 字段数超过上限(500)") }`；F:505-549 阶段A 用单次内核 JS 批量探测存在性，F:562-571 不存在的字段直接计入失败且**不执行置入** | R:11539 描述 = "按字段清单批量填写表单。fields为JSON数组[{selector,value},...], 逐个用原生填表框架置入内容并模拟输入事件, 返回每字段成败" | 代理不知道 500 上限，也不知道"先批量探测、not_found 的字段根本不会被置入"（描述读起来像逐字段直接填） | 描述补 "上限500字段; 先批量探测存在性, 未命中的字段计入 failed(不置入)" |

### 2.1 空类型说明（已核查，非漏项）
- **DECLARED_UNUSED：0 条。** 核查方式：按 0.4 的逐字集对比 —— Form 12 个工具的声明属性并集 = 实现读取名并集（8 个名字完全相同，无多无少）；System 9 个已注册工具同样 7=7 完全相同；VIP 全部 106 个实现读取名逐个回落到所属工具的声明属性上都能对上，唯一多出来的 `confirm` 属 MISSING_IN_SCHEMA（#A）。公共层参数（`browser_id` 等）已按 §0.3 排除误报。
- **ACTION_MISMATCH：0 条。** 本范围只有两个 action 型工具：`browser_startup_args`（描述 `get/list` ↔ 实现 V… S:53-58 只认 `list`、否则走 get 全量，与"action 缺省=get"一致）与 `browser_font_randomize`（描述 `random(默认)/reset` ↔ V:456-464 只接受这两值并报错提示），集合一致。
- 其余 4 类均已列出：MISSING_IN_SCHEMA 2、ENUM_MISMATCH 14、DESC_PROMISE 5、REQUIRED_MISMATCH 10。

---

## 3. 小结

- **扫描工具数**：**93 个已注册工具**（填表族 12 + 系统族 9 + VIP 族 72），另有 **2 个"有分派分支但未注册为 MCP 工具"**（`browser_create_tab`、`browser_task_runner_post`，见 §4.1），合计 95 个分派分支。
- **差异条数：31 条**，按类型：
  - `MISSING_IN_SCHEMA` **2**（#A browser_vip_enable_js_env 的 confirm、#B browser_vip_touch_cancel 的 x/y）
  - `DECLARED_UNUSED` **0**
  - `ACTION_MISMATCH` **0**
  - `ENUM_MISMATCH` **14**（#7 ssl、#8 enable_inspector、#12 shutdown、#13 set_window_style、#14 fill_form、#16 font_randomize、#17 pixel_ratio、#18 geolocation、#19 battery、#20/#20b/#20c css/web/v8_version、#21 dom_get_document、#22 orientation）
  - `DESC_PROMISE` **5**（#4 send_message、#5 get_global_cache_dir、#6 get_run_style、#9 enable_inspector、#9b enable_devtools_observer）
  - `REQUIRED_MISMATCH` **10**（#1 fill_attr_get、#2 fill_attr_set、#3 fill_select、#C touch_emulation、#E media_devices、#F set_preference、#G load_extension、#H execute_js_context、#10 languages、#11 mouse_wheel）

### Top 15 待修清单（按影响排序）

| 排名 | 工具 | 类型 | 为什么排这么前（影响） | 一句话修法 |
|---|---|---|---|---|
| 1 | browser_vip_enable_js_env | MISSING_IN_SCHEMA | 描述本身要求传 `confirm:true`，schema 却看不到该参数 ⇒ VIP JS 环境**根本启用不了**，且 enable_js_env 是 execute_js_context 三个 target 的前置，卡住一整条 VIP 链路 | R:11411 补 confirm 属性（描述+required） |
| 2 | browser_vip_touch_cancel | MISSING_IN_SCHEMA | 空 schema ⇒ 代理只能以缺省 0,0 取消触摸，取消错点还回"成功"(静默无效) | R:11415 补 x/y 属性与"缺省=0,0"说明 |
| 3 | browser_vip_touch_emulation | REQUIRED_MISMATCH | 只传 `{mode:"mouse"}` 会把已开启的鼠标转触摸**静默关掉**并回成功（反向操作） | 描述写明 enable 必填，或实现缺省改真 |
| 4 | browser_vip_fingerprint_ssl | ENUM_MISMATCH | 未知 tls 值**静默回退为"不限制"**且报成功 ⇒ 安全语义上的假成功（描述无取值表，代理极易传 1/2/3） | 描述给 0/769/790/791/792，未知值改为报错 |
| 5 | browser_fill_attr_get | REQUIRED_MISMATCH | schema 的 required 与同一行描述**自相矛盾**（required 要 attribute，描述说可省略），严格客户端会锁死 textContent 路径 | required 去掉 attribute |
| 6 | browser_fill_attr_set | REQUIRED_MISMATCH | attribute 实际必填却标可选 ⇒ 代理按 schema 省略后运行期失败 | required 加 attribute |
| 7 | browser_fill_select | REQUIRED_MISMATCH | value 实际必填却标可选 ⇒ 多一轮试错（选择项设置失败后代理常改道 DOM 工具，链路变长） | required 加 value |
| 8 | browser_set_preference | REQUIRED_MISMATCH | value 实际必填却标可选 ⇒ 首选项设置静默走空值失败路径 | required 加 value |
| 9 | browser_vip_execute_js_context | REQUIRED_MISMATCH | `code` 是本工具唯一必填项却标可选；frame_index 条件必填也未声明 | required 加 code + 描述写条件必填 |
| 10 | browser_fingerprint_languages | REQUIRED_MISMATCH | "languages 与 reset 二选一"无法从 schema 读出，空参直接失败 | 描述写明二选一 / anyOf |
| 11 | browser_vip_mouse_wheel | REQUIRED_MISMATCH | 必须给 delta_x/delta_y 才能滚，schema 完全没提示 | 描述写明 + anyOf |
| 12 | browser_vip_fingerprint_media_devices | REQUIRED_MISMATCH | devices 条件必填只写在描述里，机器可读 schema 缺失 | 用条件 schema 表达 |
| 13 | browser_get_global_cache_dir | DESC_PROMISE | 描述把"按开关推导值"说成"类库真值"⇒ 代理会把该路径当权威值用于路径比对/清理；且不知道 `cache_dir_source` 字段含义 | 描述改成"推导值 + cache_dir_source" |
| 14 | browser_send_message | DESC_PROMISE | 描述"向主进程发消息"但实现只能广播到渲染进程（S:39-41 注释自证主进程路径恒失败）⇒ 代理按描述发送后收不到任何回执 | 描述改为"广播到全部渲染进程" |
| 15 | browser_get_run_style | DESC_PROMISE | 描述"runtime_style 恒为 0"与实现回包 note"实测为 1"冲突 ⇒ 代理按 0 写死判断必误判 | 描述与 S:183 口径统一 |

紧接着的次优先项：`browser_vip_set_css_version` / `set_web_version` / `set_v8_version`（116~135 范围未声明，3 条同型）、`browser_vip_orientation`（1..4 方向映射未声明）、`browser_vip_enable_inspector` + `browser_vip_enable_devtools_observer`（"需重启才能恢复"旧文案，两条）、`browser_vip_load_extension`（path/crx_path 二选一未表达）、`browser_set_window_style`（GWL 白名单未声明）、`browser_shutdown`（1~3 秒钳制未声明）。

---

## 4. 备注与边缘发现（**不属于上面 6 类差异表**，供主代理判断是否处理）

### 4.1 两个"有实现、有注册表项、但没有 MCP 注册行"的系统族工具
- `browser_create_tab`：分派分支 `S:16-19`（恒返回失败"远程创建标签页已禁用"）；`MCP_Server.wsv:1300-1301` 的 `命令注册表.置整数值 ("browser.create_tab", 1141)` / `("browser_create_tab", 1141)` 都存在，`MCP_Server.wsv:12157` 的路由条件里也列了它 —— 但**全文没有 `添加工具JSON ("browser_create_tab", ...)`**（grep 结果为 0 命中）。
- `browser_task_runner_post`：同上，分支 `S:20-23`，注册表 `MCP_Server.wsv:1319-1320`。
- 影响：这两个名字**永远不出现在 `tools/list`**，代理看不到也不会调用；对 schema 一致性审计而言不是差异（无声明可比），但说明"分派分支 + 命令注册表 + 工具注册表"三处口径不一致。是否清理分支或补注册，请主代理定。

### 4.2 未构成差异、但属"静默缺省"隐患的两处（无 schema 冲突，故未入表）
- `browser_fingerprint_plugins`（V:367）：只读 `yyjson取JSON文本 (参数JSON, "json")`，**没有像 `browser_vip_send_devtools_msg`（V:1317 取JSON文本 + V:1320 取文本兜底）那样的文本回退**。schema 把 `json` 声明为 **text**（R:11376），若客户端按 schema 传字符串，取值路径是否成立**未实测**（同型问题在填表族有先例：`F:469-474` 注释"MCP客户端按schema传数组时取文本为空"，故那里加了双路径兜底）。建议主代理安排一次运行期验证。
- `browser_fingerprint_touch_enable`（V:769）：`enable`/`points` 在 schema 里都非必填（R:11379 required 为空），实现**无任何缺省守卫** ⇒ 省略 `enable` 会走 `取逻辑→假`，可能把触摸指纹静默设为"关闭、0 点"。同族的 `browser_fingerprint_online`（V:592-595）与 `browser_vip_set_is_trusted`（V:1929-1930 注释）都为此加了守卫或注释，本工具没有。

### 4.3 别名与分派口径（非参数差异，仅记录）
- 填表族实现同时接受 `browser.fill_*` 与 `browser_fill_*` 两套名字（F:12/43/72/101/130/158/206/286/326/376/411），入口分层前还有 `子文本替换 (方法名, "browser.", "browser_", , , 假)`（F:11 位置在 S:14、V:11 亦有）。但 `添加工具JSON` 只注册了 `browser_fill_*`（R:11315-11325），`MCP_Server.wsv:1278-1298` 的 `命令注册表` 也是**点号形式**（`browser.fill_set_value` 等）。即两套名字各自只在一处出现，代理只能看到下划线形式，属可发现性上的历史包袱，不影响本次参数一致性结论。

---

## 5. 复核锚点（原文摘录，便于行号漂移后重定位）

**#A（confirm）**
- `src/MCP_Server_VIP.wsv:267`：`如果 (MCP命令服务器.yyjson取逻辑 (参数JSON, "enable") && MCP命令服务器.参数键存在 (参数JSON, "confirm") == 假)`
- `src/MCP_Server.wsv:11411`：`添加工具JSON ("browser_vip_enable_js_env", "VIP: 启用JS执行环境", 单参数Schema文本 ("enable", "boolean", "启用/关闭"))`
- 交叉引用（同样要求传 confirm 的地方）：`src/MCP_Server.wsv:11442` 描述"**需先 browser_vip_enable_js_env {enable:true, confirm:true}**"；`src/MCP_Server_VIP.wsv:1517` 失败文案 "请先调 browser_vip_enable_js_env {enable:true, confirm:true}"

**#B（touch_cancel 的 x/y）**
- `src/MCP_Server_VIP.wsv:331`：`vip_ctrl.高级触摸_取消 (MCP命令服务器.yyjson取整数 (参数JSON, "x"), MCP命令服务器.yyjson取整数 (参数JSON, "y"))`
- `src/MCP_Server.wsv:11415`：`添加工具JSON ("browser_vip_touch_cancel", "VIP: 取消触摸 | **警告: ...", 空Schema文本 ())`

**#C（touch_emulation 反向）**
- `src/MCP_Server_VIP.wsv:1706`：`转触摸启用 = MCP命令服务器.yyjson取逻辑 (参数JSON, "enable")`
- `src/MCP_Server_VIP.wsv:1714`：`转触摸参数 = "{\"enabled\":false}"`
- `src/MCP_Server_VIP.wsv:1726`：`返回 (MCP_响应构建.命令成功 (命令ID, "已关闭鼠标转触摸(CDP)"))`

**#7（SSL 未知值静默回退）**
- `src/MCP_Server_Utils.wsv:63-65`：`// 未知值: 返回空(不设置), 避免静默降级到1.2掩盖错误` / `控制台输出 ("[MCP] 警告: 未知TLS版本值 " + 到文本 (整数值) + ", 回退为TLS版本.空")` / `返回 (TLS版本.空)`
- `src/MCP_Constants.wsv:59-62`：`TLS指纹_1_0 = 769` / `1_1 = 790` / `1_2 = 791` / `1_3 = 792`

**#1（fill_attr_get 的 required 自相矛盾）**
- `src/MCP_Server.wsv:11320`：`..., "\"selector\",\"attribute\""))`；同一行描述含 `省略 attribute 则返回元素文本(textContent)`
- `src/MCP_Server_Form.wsv:225`：`如果 (attr != "")`；`src/MCP_Server_Form.wsv:250`：`否则`（textContent 路径）

**#5（cache_dir 描述 vs 实现）**
- `src/MCP_Server.wsv:11374`：`..., "获取全局缓存目录路径(CEF用户数据根目录)| 真值取自类库 FBrowser_取初始化缓存目录(); ..."`
- `src/MCP_Server_System.wsv:81-82`：`// 注: 类库 FBrowser_取初始化缓存目录() 本机**编译不过**(FBroLib.v:155 error C3861 IsEmpty),` / `// 故此处不做类库读取, 而是如实标注取值来源 cache_dir_source, 让调用方知道这是推导值而非内核回报值。`

**#6（runtime_style 恒为 0 vs 实测 1）**
- `src/MCP_Server.wsv:11372`：`... 故 runtime_style 当前恒为 0"`
- `src/MCP_Server_System.wsv:183`：`风格对象.加入文本成员 ("runtime_style_note", "runtime_style 来自 CEF CefRuntimeStyle(0默认/1谷歌/2经典); 本机实测为 1(谷歌) ...`

**#9 / #9b（"需重启才能恢复"旧文案）**
- `src/MCP_Server.wsv:11416`：`... ⚠ 关闭后全部 CDP 类工具(debugger_*/cdp_*/reverse CDP类)立即失效, 需重启进程才能恢复。...`
- `src/MCP_Server_VIP.wsv:242`：`... 实测纠正: 下一次 CDP 调用会自动重新注册观察者并自愈, 通常无需重启(旧文案'需重启进程才能恢复'与实测不符)`
- `src/MCP_Server.wsv:11443`：`... ⚠ 关闭会使全部 CDP 类工具(debugger_*/cdp_*/reverse CDP类)失效且需重启进程才能恢复, ...`
- `src/MCP_Server_VIP.wsv:1680`：`... 实测纠正: 关闭**不是**永久的 ... 通常无需重启进程(旧文案声称'需重启进程才能恢复', 与实测不符)`

**#4（send_message 只能到渲染进程）**
- `src/MCP_Server_System.wsv:39-41`：`// 发送数据_到主进程 为渲染进程专用API(主进程调用恒失败);` / `// 主进程应经 发送数据_到全部渲染进程 下发, 渲染侧由 进程间消息_收到主进程消息 事件接收` / `browser.进程间消息_发送数据_到全部渲染进程 (msgName, 文本到UTF8 (msgData, 假))`

**required 语义的公共实现（用于复核 §0.2 的所有 REQUIRED_MISMATCH 判定）**
- `src/MCP_Server.wsv:11767`：`参数 必须 <类型 = 逻辑型 @默认值 = 真 @输出名 = "Must">`
- `src/MCP_Server.wsv:11776-11779`：`如果 (必须) { s = s + ",\"required\":[\"" + 名 + "\"]" }`
- `src/MCP_Server.wsv:11790`（双XY 恒 required）、`11793-11805`（多属性 required 由第 2 参决定）、`11605`（添加工具JSON 的缺省空 schema）

---

**报告结束。** 本报告仅覆盖 `MCP_Server_Form.wsv` / `MCP_Server_System.wsv` / `MCP_Server_VIP.wsv` 三个文件；`MCP_Server.wsv` 只作对照读取，未做任何修改。
