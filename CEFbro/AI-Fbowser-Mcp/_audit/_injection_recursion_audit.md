# 注入类自递归缺陷全量审计（injection-recursion audit）

只读审计。**未编译、未运行、未调用任何 MCP 工具、未修改任何源文件**（本文件是本次唯一的写入物）。
所有结论均为**静态**推导；**本报告中的任何修复都未经编译/运行验证**，验证由主 agent 另行完成。

---

## 0. 范围、方法、锚点

### 0.1 引用的文件与哈希锚点（快照时刻）

`src/` 下非备份 `.wsv` 的 SHA256 前 24 位与行数：

| 文件 | SHA256(前24) | 行数 |
|---|---|---|
| `MCP_Server_Core.wsv` | `F506ADF0A68048E50826BE0B` | 7457 |
| `MCP_Server_Reverse.wsv` | `AF60396BB2573BDA4D618097` | 2312 |
| `MCP_Kernel.wsv` | `7CD3CB1DCB854081652DEBAC` | 1800 |
| `main.wsv` | `74368D23E361974356540358` | 809 |
| `MCP_Server.wsv` | `A19617467FCF2315AB1E77A5` | 10986 |

**行号漂移警告（实测）**：审计过程中 `MCP_Server_Reverse.wsv` 被**外部进程改动**（`browser_reverse_preload` 内新增 17 行文件大小预检，见 `MCP_Server_Reverse.wsv:281-297`），导致该文件 281 行之后的全部行号 **+17**（例：`hook_multi` 的包装器由 `:782` 变为 `:799`）。同样 `MCP_Server.wsv` 在审计期间由 10563 行变为 10986 行。因此**引用位置请优先按"锚点字符串"检索**，行号以本表哈希为准。同一位置在别的报告里若相差 +8 / +17，属正常漂移（参见 `_audit/_instrument_cleanup_research.md:38` 已记录 +8 的同类现象）。

### 0.2 检索动作（含"未找到"声明）

1. `grep 'window\.__'`（`src/**.wsv`）：命中 130 处，已逐条归类；**除下列文件外无注入家族**。
2. 对 `src/` 全部 16 个非备份 `.wsv` 逐行正则扫描 `.push( .splice( .forEach( .map( .slice( .apply( .call( .shift( .indexOf( .charAt(`：
   - 有命中：`MCP_Server_Core.wsv`、`MCP_Server_Reverse.wsv`、`MCP_Kernel.wsv`、`main.wsv`、`MCP_Callbacks.wsv`（1 处，`:217`）、`MCP_Server_Form.wsv`（1 处，`:349`）。
   - **0 命中**：`MCP_Server.wsv`、`MCP_Server_VIP.wsv`、`MCP_BrowserEvents.wsv`、`MCP_Server_System.wsv`、`MCP_Server_Utils.wsv`、`MCP_Server_Workflow.wsv`、`MCP_Stdio.wsv`、`MCP_ResponseBuilders.wsv`、`MCP_Constants.wsv`、`MCP_Server_HTTP.wsv`。
     → 结论：这些文件内**没有"注入代码调用被包装方法"的位点**（`MCP_Server.wsv` 是工具注册表，只描述工具，不注入页面 JS）。
3. `grep 'prototype|defineProperty'`（`src/`，排除备份）：包装器安装点**全部**落在 `MCP_Server_Core.wsv:3188-3214 / 6167 / 6395 / 6401 / 6897-6917`、`MCP_Kernel.wsv:1278 / 1349 / 1402 / 1542`、`MCP_Server_Reverse.wsv:799`。`MCP_Server_VIP.wsv`、`MCP_BrowserEvents.wsv` 内 `prototype`/`defineProperty` **not found**。
4. `grep 'Array\.prototype|instrument|插桩'`（`docs/*.md`）：**not found**。→ 用户文档**没有**把 `Array.prototype.*` 列为推荐插桩目标；唯一的目标说明来自工具描述本身（见 §3.1 引用）。
5. 备份文件（`src/*.~vbak.wsv`、`备份/**`）**不在本次审计范围**，仅确认同一缺陷在旧快照同样存在：`MCP_Kernel_1.~vbak.wsv:1140/1198/1244/1363`、`MCP_Kernel_2.~vbak.wsv:1162/1221/1268/1390`、`MCP_Server_Core` 备份中的 `instrument` 模板同形。

### 0.3 分类词汇（沿用任务定义）

- **RECURSION CONFIRMED**：静态可证明必然自递归（默认参数或该工具**明确接受**的目标值即可触发），不依赖其它工具的页面状态。
- **POSSIBLE**：仅当**同一页面**上另有某个注入族把该方法包装掉时才会递归（跨族共享页面状态），单体无法自证。
- **SAFE**：该注入**自己**包装的方法，其自身代码路径不会再次经过这些包装器（给出理由）。

---

## 1. 通用机制（后文引用编号 M1–M6）

- **M1 包装即改原型/宿主属性**：注入代码用 `__obj[__method]=function(){…}` 或 `Object.defineProperty` 原地替换宿主方法（`MCP_Server_Core.wsv:6395` 原文 `__obj[__method]=function(){if(__count<__max){…`）。此后**页面内任何**对同名的调用都解析到包装器。
- **M2 `Function.prototype.call/apply` 是"全局拦截器"**：`fn.apply(...)`、`fn.call(...)` 的属性查找走 `Function.prototype`。一旦 `Function.prototype.apply/call` 被替换（`MCP_Server_Core.wsv:6395` 默认表第 1、2 项就是它们），**任何**函数对象的 `.apply/.call` 都进包装器 —— 包括"已捕获的原函数"的 `.apply`。
- **M3 `Array.prototype.push` 是"日志通道拦截器"**：本项目几乎所有注入族都用 `某数组.push(entry)` 写日志；`Array.prototype.push` 一旦被替换，这些**日志写入本身**进包装器。
- **M4 保护计数器写在递归调用之后**（"guard-after"）：`__results.push({…});__count++`（`MCP_Server_Core.wsv:6395`）—— 计数自增在递归语句**之后**，递归先崩栈，计数永不增长，`__max=500` 这道闸门永不生效。同类写法还见于 `MCP_Kernel.wsv:1349`（`T.calls.push(...);if(T.calls.length>T.limit)T.calls.shift();`）、`MCP_Kernel.wsv:1542`、`MCP_Kernel.wsv:1402`。
- **M5 吞掉异常 ⇒ 静默无记录**：`MCP_Kernel.wsv:1278` 探针的多个 `try{…P(...)}catch(e){}` 会把 `RangeError` 吞掉，症状从"崩栈"变成"探针永远没有数据"。
- **M6 直连原函数的例外（SAFE 的理由）**：`var __orig=obj[name];` 先捕获原函数、再用 `__orig.apply(this,arguments)` 转发 —— 这**不**构成自递归的**唯一**条件是：该注入**没有**同时替换 `Function.prototype.apply`。若同时替换（如 transparent 默认表），则 `__orig.apply` 仍然进包装器（见 §3.1）。

---

## 2. 全量清单表

> "包装"列 = 该注入**自己安装**的函数替换；"自调用被包装方法"列 = 该注入自身代码是否调用上面这些被替换的方法。

### 2.1 `MCP_Server_Core.wsv`

| ID | 工具 / 分支 | 位置 | 包装对象 | 自身调用的被包装方法（关键片段） | 分类 |
|---|---|---|---|---|---|
| C-01 | `browser_set_value` | `:1805` | 无 | `n.set.call(e,v)` | SAFE 自；POSSIBLE 跨（`Function.prototype.call`） |
| C-02 | `browser_get_selected` | `:2028` | 无 | `vs.push(o[i].value);ts.push(...)` | SAFE 自；POSSIBLE 跨（`Array.prototype.push`） |
| C-03 | `browser_wait`（selector/navigate/url_contains） | `:2733`,`:2747`,`:2751` | 无 | `innerText.indexOf(...)`、`h.indexOf(t)` | SAFE 自；POSSIBLE 跨（`String.prototype.indexOf`） |
| C-04 | `browser_extract` links/images/tables | `:2871`,`:2879`,`:2888` | 无 | `r.push(...)`（`tables` 分支 5 处 push） | SAFE 自；POSSIBLE 跨（push） |
| C-05 | Canvas 噪声注入 | `:3186-3218` | `HTMLCanvasElement.prototype.toDataURL`、`toBlob`、`CanvasRenderingContext2D.prototype.getImageData` | `origGetImageData.call(...)`、`origToDataURL.apply(...)`、`origToBlob.apply(...)`、`ctx.getImageData(...)`（指向**同一注入**的补丁，但 `getImageData` 补丁不回调 `toDataURL`，不成环） | SAFE 自；POSSIBLE 跨（`Function.prototype.call/apply`） |
| C-06 | Canvas 噪声移除 | `:3227` | 恢复备份（写回原型） | 无 | SAFE |
| C-07 | 权限伪装（permissions/mediaDevices） | `:3332-3347` | `navigator.permissions.query`、`navigator.mediaDevices.enumerateDevices` | `perms.indexOf(desc.name)`、`perms.join(',')` | SAFE 自；POSSIBLE 跨（`String.prototype.indexOf`） |
| C-08 | `browser_reverse_hook` type=function_call | `:6115`,`:6128` | **用户指定**的任意点路径（含 `Array.prototype.push`/`Function.prototype.apply` 等） | `Array.prototype.slice.call(arguments)`、`__orig.apply(this,__args)`、`__lg.push(__entry)`（正常+catch 两处）、`console.log(...)`、`__lg.splice(0,1000)` | **CONFIRMED（参数门控）**，见 §3.2-1 |
| C-09 | `browser_reverse_hook` type=xhr_fetch | `:6146` | `XMLHttpRequest.prototype.open` | `u.indexOf(__p)`、`__origOpen.apply(...)` | SAFE 自；POSSIBLE 跨 |
| C-10 | `browser_reverse_hook` type=websocket | `:6157` | `WebSocket.prototype.send` | `u.indexOf(__p)`、`__lg.push(...)`、`__lg.splice(...)`、`__os.apply(...)` | SAFE 自；POSSIBLE 跨（push/indexOf 被别族包装时） |
| C-11 | `browser_reverse_hook` type=eval_dynamic | `:6162` | `window.eval`、`window.Function` | `Array.prototype.slice.call(arguments)`、`__lg.push(...)`、`__oe.apply/__oF.apply` | SAFE 自；POSSIBLE 跨 |
| C-12 | `browser_reverse_hook` type=cookie_set | `:6167` | `Document.prototype` 的 `cookie` setter | `__lg.push(...)`、`__s.call(this,v)` | SAFE 自；POSSIBLE 跨 |
| C-13 | `browser_reverse_search` | `:6439` | 无 | `ss.forEach(...)`、`src.indexOf(uf)`、`l.indexOf(q)`、`R.push(...)` | SAFE 自；POSSIBLE 跨 |
| C-14 | `browser_reverse_strings`（suspicious/decrypt_array） | `:6221`,`:6225` | 无 | `R.push(...)` | SAFE 自；POSSIBLE 跨 |
| C-15 | `browser_reverse_verify` | `:6286` | 无 | `R.push(...)`、`R.every(...)` | SAFE 自；POSSIBLE 跨 |
| C-16 | `browser_reverse_extract` scan/analyze | `:6488`,`:6548` | 无 | `ss.forEach(...)`、`R.push(...)`、`src.indexOf(pat)` | SAFE 自；POSSIBLE 跨 |
| C-17 | **`browser_reverse_instrument` mode=transparent** | `:6395`（派发 `:6374`，`target` 读取 `:6377`，`mode` 默认 `:6382`） | **默认表 6 项**：`Function.prototype.apply`、`Function.prototype.call`、`Array.prototype.push`、`Array.prototype.pop`、`String.prototype.indexOf`、`String.prototype.charAt` | `__results.push({...})`、`Array.prototype.slice.call(arguments)`、`….map(...)`、`….join(',')`、`__orig.apply(this,arguments)` | **RECURSION CONFIRMED（默认参数即触发）**，见 §3.1 |
| C-18 | `browser_reverse_instrument` mode=interpreter | `:6401` | `window[target]`（全局函数） | `Array.prototype.slice.call(arguments)`、`__orig.apply(this,__args)`、`__args.map(...)`、`__logs.push(...)` | SAFE 自（自身不包装这 4 个）；POSSIBLE 跨。另见 §3.3 的畸形 target 说明 |
| C-19 | `browser_reverse_initiator` | `:6749` | `XMLHttpRequest.prototype.open`、`window.fetch` | `u.indexOf(p)`、`R.push(...)`、`_origOpen.apply/_origFetch.apply` | SAFE 自；POSSIBLE 跨 |
| C-20 | `browser_reverse_preset`（xhr/fetch/cookie/websocket/crypto/debugger/all） | `:6897`,`:6901`,`:6905`,`:6909`,`:6913`,`:6917`,`:6919` | XHR.open、`window.fetch`、`document.cookie` setter、`WebSocket.prototype.send`、`SubtleCrypto.prototype.digest`、`window.setTimeout/setInterval` | `window.__mcp_*_log.push(...)`（5 处）、`__origXHROpen.apply`、`__origFetch.apply`、`__origCookieDesc.get.call`、`__origWSSend.call`、`__origDigest.call`、`s.indexOf('debugger')`、`__hooks.push('xhr')` 等 | SAFE 自；POSSIBLE 跨 |
| C-21 | `browser_snapshot` | `:6988-6994` | 无 | `out.push(o)`、`out.length` 作上限 | SAFE 自；POSSIBLE 跨 |
| C-22 | 文本点击（`browser_click_text`） | `:7054-7063` | 无 | `cands.push(e)`、`t.indexOf(txt)`、`sugg.push({...})`、`sugg.sort(...)`、`sugg.slice(0,5)` | SAFE 自；POSSIBLE 跨 |
| C-23 | `browser_get_forms` | `:7115-7123` | 无 | `fo.fields.push(fd)`、`out.push(fo)` | SAFE 自；POSSIBLE 跨 |
| C-24 | `browser_highlight` | `:7200-7212` | 无 | `list.push(e)` | SAFE 自；POSSIBLE 跨 |
| C-25 | `browser_element_action` action=set_value | `:7396` | 无 | `n.set.call(el,...)` | SAFE 自；POSSIBLE 跨 |

### 2.2 `MCP_Kernel.wsv`

| ID | 工具 / 分支 | 位置 | 包装对象 | 自身调用的被包装方法 | 分类 |
|---|---|---|---|---|---|
| K-01 | `browser_kernel_reverse_probe` action=enable | `:1278` | `XMLHttpRequest.prototype.open/send`、`window.fetch`、`WebSocket.prototype.send/close`、`window.setTimeout/setInterval`、`EventTarget.prototype.addEventListener` | `L[k].push(o)`、`L[k].shift()`、`f.apply(this,arguments)`、`OE.call(this,t,fn,o)` | SAFE 自；POSSIBLE 跨（并被 `catch(e){}` 吞成静默，见 M5） |
| K-02 | probe get / clear / disable | `:1296`,`:1309`,`:1315` | 无 | 仅 `JSON.stringify`／`=[]` 重新赋值／`delete` | SAFE（无被包装方法调用） |
| K-03 | `browser_kernel_reverse_trace` action=start | `:1349` | **用户 `targets` 点路径**（工具描述示例 `["window.fetch","crypto.subtle.encrypt"]`，但无白名单） | `[].slice.call(arguments)`、`orig.apply(this,arguments)`、`T.calls.push(...)`（正常+catch）、`args.map(S)`、`T.calls.shift()`（在 push 之后，M4） | **CONFIRMED（参数门控）**，见 §3.2-2 |
| K-04 | trace get / clear / stop | `:1361`,`:1374`,`:1379` | 无 | `JSON.stringify`／`=[]`／`delete` | SAFE |
| K-05 | `browser_kernel_reverse_algo` action=start | `:1402` | `CryptoJS` 17 个算法成员、`window.md5/sha1/sha256/sha512/btoa/atob/encodeURIComponent/decodeURIComponent`、`crypto.subtle.encrypt/decrypt/digest/sign/verify/deriveKey/deriveBits` | `args.map(...)`、`[].slice.call(arguments)`、`fn.apply(this,arguments)`、`L.calls.push(...)`、`L.calls.shift()`（在 push 之后）、`res.toString().slice(...)` | SAFE 自（被包装集合里没有它自己调用的 push/map/slice/apply/call）；POSSIBLE 跨 |
| K-06 | `browser_kernel_*` 函数提取（functions） | `:1457` | 无 | `out.push({...})`、`Object.keys(window).forEach(...)`（5 处 forEach） | SAFE 自；POSSIBLE 跨。**注**：同行 `if(FIL&&p.indexOf(FIL)<0)return;` 因 `var FIL='' ;` 恒假值短路，`indexOf` **运行期不执行**（静态确定） |
| K-07 | 脚本源码（sources） | `:1496` | 无 | `Array.prototype.slice.call(document.scripts)`、`ss.map(...)` | SAFE 自；POSSIBLE 跨（`Function.prototype.call`／`Array.prototype.map`） |
| K-08 | `browser_kernel_reverse_watch_global` action=start | `:1542` | `Object.defineProperty(window,name,{get,set})` | `L.hits.push({...})`、`L.hits.shift()`（在 push 之后） | SAFE 自（只包装数据全局量，setter 内部不回调这些名字）；POSSIBLE 跨 |
| K-09 | watch_global get / clear / stop | `:1554`,`:1567`,`:1572` | 无 | `JSON.stringify`／`=[]`／`delete` | SAFE |

### 2.3 `MCP_Server_Reverse.wsv`

| ID | 工具 / 分支 | 位置（**漂移后**行号） | 包装对象 | 自身调用的被包装方法 | 分类 |
|---|---|---|---|---|---|
| V-01 | `browser_reverse_call_fn` | `:256`,`:260` | 无（CDP `functionDeclaration`） | `__f.apply(this,args)` / `this.apply(this,args)` | SAFE 自；POSSIBLE 跨（`Function.prototype.apply`） |
| V-02 | `browser_reverse_preload` | `:266+` | 由用户 JS 决定（不在本项目注入模板内） | — | 不在审计范围（用户代码原样执行） |
| V-03 | `browser_reverse_scan_crypto` | `:494-500` | 无 | `t.indexOf('...')`（6 处）、`out.push({...})` | SAFE 自；POSSIBLE 跨 |
| V-04 | `browser_reverse_string_refs` | `:563` | 无 | `t.indexOf(v,pos)`、`t.charAt(j)`、`out.push({...})` | SAFE 自；POSSIBLE 跨（**`charAt` 是 transparent 默认目标之一**） |
| V-05 | `browser_reverse_detect_obfuscator` | `:612-617` | 无 | `total.indexOf(...)`（多处）、`det.push({...})` | SAFE 自；POSSIBLE 跨 |
| V-06 | `browser_reverse_hook_logs` auto **clear** | `:682` | 无 | **无**：`v.length=0;` / `v.results.length=0;`（原地截断） | **SAFE**（刻意规避，注释见 `:678-679`） |
| V-07 | `browser_reverse_hook_logs` auto **query** | `:686` | 无 | `hit.push(k)`、`arr.slice(Math.max(0,arr.length-200))`、`items.push(it)` | SAFE 自；**POSSIBLE 跨（读路径会被包装吞掉）** |
| V-08 | `browser_reverse_hook_logs` 单键 **clear** | `:695` | 无 | 无（`v.length=0`） | SAFE |
| V-09 | `browser_reverse_hook_logs` 单键 **query** | `:701` | 无 | `items=v.slice(...)`、`v.results.slice(...)`、`safe.push(...)` | SAFE 自；**POSSIBLE 跨（读路径）** |
| V-10 | `browser_reverse_hook_multi` | `:798`,`:799` | **用户 `functions` 点路径数组**（描述示例 `[sign,utils.md5,enc.aesEncrypt]`，无白名单） | 安装期 `found.push(name)`；运行期 `Array.prototype.slice.call(arguments)`、`__orig.apply(this,a)`、`lg.push(e)`（正常+catch）、`lg.splice(0,1000)` | **CONFIRMED（参数门控）**，见 §3.2-3 |

### 2.4 `main.wsv`

| ID | 位置 | 用途 | 包装对象 | 自身调用 | 分类 |
|---|---|---|---|---|---|
| M-01 | `:457` | 主进程→渲染侧消息写入 `window.__mcp_ipc_queue` | 无 | `q.push({...})` | SAFE 自；POSSIBLE 跨（push 被别族包装时 IPC 通道同样失效） |
| M-02 | `:762` | 渲染侧事件写入同一队列 | 无 | `q.push({...})`、`q.splice(0,q.length-600)`（`if(q.length>600)` 在前，非 M4） | SAFE 自；POSSIBLE 跨 |

### 2.5 `MCP_Callbacks.wsv:217` / `MCP_Server_Form.wsv:349`（扫描命中的另 2 处）

两处均为 `n.set.call(e,'...')`（输入框/下拉框 setter 调用），**不包装任何东西**：`SAFE 自；POSSIBLE 跨（`Function.prototype.call`）`。

---

## 3. 现场明细（逐条引用原文）

### 3.1 RECURSION CONFIRMED（默认参数即触发，无需用户提供任何 target）

**C-17 = `browser_reverse_instrument` mode=transparent —— 本缺陷类的"核心炸弹"**

- 工具与位置：`MCP_Server_Core.wsv:6395`（派发分支 `:6374 否则 (方法名 == "browser_reverse_instrument")`）。
- 触发条件**无需任何参数**：`target` 读取于 `:6377`（缺省即空串），`mode` 缺省被 `:6382` 置为 `"transparent"`，而 `:6395` 的默认目标表就包含危险项。工具描述（`MCP_Server.wsv:9833`）原文：

  > `添加工具JSON ("browser_reverse_instrument", "JS逆向: JSVMP解释器透明插桩。mode=transparent仅替换prototype getter保留toString; mode=interpreter Hook VM分发器。不破坏签名计算", 多属性Schema文本 (属性项JSON ("target", "text", "目标函数名(transparent模式可选,interpreter模式必填)") + "," + 属性项JSON ("mode", "text", "transparent(默认)/interpreter"), ""))`

  即 **`target` 在 transparent 模式下是可选参数** —— 只传 `{"mode":"transparent"}`（或干脆 `{}`）就会走默认表。
- 注入代码原文（`MCP_Server_Core.wsv:6395`，`.wsv` 字面量原样）：

```
insCode = "(function(){var __targets=" + 选择 (insTarget == "", "['Function.prototype.apply','Function.prototype.call','Array.prototype.push','Array.prototype.pop','String.prototype.indexOf','String.prototype.charAt']", "['" + insEsc + "']") + ";var __count=0;var __max=500;var __results=[];__targets.forEach(function(__t){var __parts=__t.split('.');var __obj=window;for(var __i=0;__i<__parts.length-1;__i++){__obj=__obj[__parts[__i]];if(!__obj)return}var __method=__parts[__parts.length-1];var __orig=__obj[__method];if(typeof __orig!=='function')return;__obj[__method]=function(){if(__count<__max){__results.push({target:__t,args:Array.prototype.slice.call(arguments).map(function(a){return typeof a==='string'?a.substring(0,200):typeof a}).join(','),ts:Date.now()});__count++}return __orig.apply(this,arguments)};__obj[__method].toString=function(){return __orig.toString()}});window.__mcp_instrument_results={instrumented:__targets.length,calls:__count,results:__results};return JSON.stringify({installed:true,targets:__targets.length,hint:'Transparent instrumentation installed. toString preserved. Use browser_evaluate \"JSON.stringify(window.__mcp_instrument_results)\" to read collected data. Trigger target action first.'})})()"
```

- 它包装的方法：默认 6 项（`Function.prototype.apply`、`Function.prototype.call`、`Array.prototype.push`、`Array.prototype.pop`、`String.prototype.indexOf`、`String.prototype.charAt`）。
- **为什么必然递归**——包装器体 `function(){if(__count<__max){__results.push({target:__t,args:Array.prototype.slice.call(arguments).map(...).join(','),ts:Date.now()});__count++}return __orig.apply(this,arguments)}` 里有 **3 条独立的递归通路**，且都落在默认目标表内：
  1. `__results.push({…})` → `Array.prototype.push` **已在默认表第 3 项被替换** ⇒ 进入自己（M3）。
  2. 同一条语句里求 `Array.prototype.slice.call(arguments)` 时，`.call` 经 `Function.prototype` 解析 ⇒ 命中**第 2 项** `Function.prototype.call` 的包装器（M2）。
  3. `return __orig.apply(this,arguments)` 中的 `.apply` 经 `Function.prototype` 解析 ⇒ 命中**第 1 项** `Function.prototype.apply` 的包装器（M2）。注意 `__orig` 虽然捕获的是原函数，但**属性查找 `apply` 发生在查找时**，与 `__orig` 是不是原函数无关。
- **闸门为什么永不生效**（M4）：`if(__count<__max){ __results.push(…); __count++ }` 的自增在递归语句**之后**。递归在 `__results.push(…)`（或其中的 `.call`/`.apply` 求值）阶段就崩栈，`__count++` 永不执行 ⇒ `__count` 恒为 0 ⇒ `__max=500` 永不命中。这与已确认的实测症状（`RangeError: Maximum call stack size exceeded`、重复帧 `at __obj.<computed> (<anonymous>:1:544)`）完全对应：`__obj[__method]=function(){…}` 正是该帧名的来源。
- **首个被拦截调用落在哪个包装器上**：静态上三者都会崩；具体是哪一条先触发取决于页面第一次调用 6 个方法中的哪一个。我**无法**静态判定实测那次的先后（见 §6）。
- **次生缺陷（同一行、静态确定）**：`window.__mcp_instrument_results={instrumented:__targets.length,calls:__count,results:__results}` 里的 `calls:__count` 是**安装瞬间的值快照**，安装时 `__count===0`，之后对象不再刷新 ⇒ 即便递归被修好，`window.__mcp_instrument_results.calls` **恒为 0**。用户按注入提示 `browser_evaluate "JSON.stringify(window.__mcp_instrument_results)"` 读到的 `calls` 永远是 0，只能靠 `results.length` 推断。这是"计数器在错误时刻被取值"，与 M4 同源。

### 3.2 RECURSION CONFIRMED（参数门控：需调用方给出特定 target，但工具**明确接受**该类值）

#### 3.2-1 C-08 `browser_reverse_hook` type=function_call（`MCP_Server_Core.wsv:6115` + `:6128`）

原文（`:6115` 段）：

```
var __orig=__t;var __lg=window.__MCP_HOOK_LOG__=window.__MCP_HOOK_LOG__||[];function __cap(){if(__lg.length>2000){__lg.splice(0,1000);}}var __wrapper=function(){try{var __args=Array.prototype.slice.call(arguments);var __result=__orig.apply(this,__args);var __entry={target:'…',hook:'…',ts:Date.now()};
```

原文（`:6128` 段）：

```
hookCode = hookCode + "__cap();__lg.push(__entry);console.log('[" + hookLabel + "]',JSON.stringify(__entry));return __result;}catch(__x){var __te={target:'…',hook:'…',ts:Date.now(),threw:__x.message};__cap();__lg.push(__te);throw __x;}};__obj[__last]=__wrapper;…"
```

- 包装对象：**用户 `target`** 指定的任意点路径（`hookEsc`，工具描述：`目标函数名(支持obj.fn点路径)`，`MCP_Server.wsv:9827`）。
- 递归判定（取决于 target 取值，皆为静态可证）：
  - `target='Array.prototype.push'`（或 `'Array.prototype.push'` 的任意前缀写法）：`__lg.push(__entry)` → 命中刚装的包装器 → 包装器体内再次 `__lg.push(__entry)` ⇒ 无限递归。**没有任何计数器**，`__cap()` 只按 `length>2000` 裁剪，无法终止递归。
  - `target='Function.prototype.apply'`：`__orig.apply(this,__args)` → `.apply` 命中自己 ⇒ 递归。
  - `target='Function.prototype.call'`：`Array.prototype.slice.call(arguments)` → `.call` 命中自己 ⇒ 递归（第一条语句就递归）。
  - `target='console.log'`：`:6128` 的 `console.log('[...]',…)` 命中自己 ⇒ 递归（且递归发生在 `__lg.push(__entry)` **之后**，每层还会真实写一条日志，形成"写日志 → 再调 console.log → 再写日志"的栈溢出）。`browser_reverse_hook_multi` 同一问题（见 3.2-3）。
  - `target='Array.prototype.splice'`：`__cap()` 内 `__lg.splice(0,1000)` 命中自己 ⇒ 仅在日志超 2000 条后触发（条件性，但同样无终止手段）。
  - `target='Array.prototype.slice'`：`Array.prototype.slice.call(...)` 命中自己 ⇒ 递归。
- 该族**没有** `__max` 计数器，且 `__cap()` 位于递归语句**之前**（是"裁剪"而非"闸门"），因此**M4 之外还存在"根本没有闸门"的更弱形态**。

#### 3.2-2 K-03 `browser_kernel_reverse_trace` action=start（`MCP_Kernel.wsv:1349`）

原文片段（同一行内）：

```
function wrap(path,obj,name){try{var f=obj[name];if(typeof f!=='function'||f.__mcp_tr)return;var orig=f;obj[name]=function(){var args=[].slice.call(arguments);var st=new Error().stack;var t0=Date.now();try{var r=orig.apply(this,arguments);T.calls.push({p:path,a:args.map(S).slice(0,10),r:S(r),ms:Date.now()-t0,st:st?st.slice(0,300):''});if(T.calls.length>T.limit)T.calls.shift();return r}catch(e){T.calls.push({p:path,a:args.map(S).slice(0,10),err:e.message,st:st?st.slice(0,300):''});if(T.calls.length>T.limit)T.calls.shift();throw e}};obj[name].__mcp_tr=true}catch(e){T.errors++}}var targets=" + 目标文本 + ";…"
```

- 包装对象：**用户 `targets`**（`目标文本` 直接拼进 JS，无白名单；工具描述示例 `["window.fetch","crypto.subtle.encrypt"]`，`MCP_Server.wsv:9717`）。
- 递归判定：
  - `targets` 含 `Array.prototype.push` ⇒ `T.calls.push(...)` 命中自己（正常分支与 catch 分支各一次）⇒ 递归。
  - `targets` 含 `Function.prototype.apply` ⇒ `orig.apply(this,arguments)` 命中自己 ⇒ 递归（`orig` 是原函数但 `.apply` 查找走被替换的 `Function.prototype`）。
  - `targets` 含 `Function.prototype.call` ⇒ `[].slice.call(arguments)` 命中自己 ⇒ 递归。
  - `targets` 含 `Array.prototype.map` ⇒ `args.map(S)` 命中自己 ⇒ 递归。
  - **M4 确认**：`T.calls.push(...); if(T.calls.length>T.limit)T.calls.shift();` —— 裁剪在 push **之后**，push 自递归时 `T.limit` 永不生效。`T.limit=200`。

#### 3.2-3 V-10 `browser_reverse_hook_multi`（`MCP_Server_Reverse.wsv:798-799`）

原文（`:799`，整行）：

```
hmCode = hmCode + "for(var i=0;i<fns.length;i++){var name=fns[i];var parts=name.split('.');var obj=window;var ok=true;for(var j=0;j<parts.length-1;j++){obj=obj[parts[j]];if(!obj){ok=false;break;}}if(ok&&typeof obj[parts[parts.length-1]]==='function'){var last=parts[parts.length-1];var __orig=obj[last];obj[last]=function(){var a=Array.prototype.slice.call(arguments);var e={fn:name,ts:Date.now()};if(CAP){try{e.args=JSON.stringify(a).substring(0,512);}catch(x){e.args='[unserializable]';}}try{var r=__orig.apply(this,a);try{e.ret=JSON.stringify(r).substring(0,512);}catch(x){e.ret=String(r).substring(0,512);}__cap();lg.push(e);return r;}catch(x){__cap();lg.push({fn:name,ts:Date.now(),threw:x.message});throw x;}};found.push(name);}}"
```

配套 `:798`：

```
hmCode = hmCode + "var lg=window.__MCP_HOOK_LOG__=window.__MCP_HOOK_LOG__||[];var found=[];function __cap(){if(lg.length>2000){lg.splice(0,1000);}};"
```

- 包装对象：**用户 `functions`** 数组内的每个点路径（工具描述示例 `例:[sign,utils.md5,enc.aesEncrypt]`，`MCP_Server.wsv:9877`；无白名单）。
- 递归判定（比 C-08 更早发作）：
  - `functions` 含 `'Array.prototype.push'`：**安装期即递归** —— 循环体在装好 `Array.prototype.push` 的包装器后，紧接着执行 `found.push(name)`，该 `push` 命中刚装的包装器；包装器体内又有 `lg.push(e)` ⇒ 栈溢出。也就是说，装到第 N 个目标时就会崩，**不需要页面再调用任何东西**。
  - `functions` 含 `'Function.prototype.call'` ⇒ `Array.prototype.slice.call(arguments)` 递归。
  - `functions` 含 `'Function.prototype.apply'` ⇒ `__orig.apply(this,a)` 递归。
  - `functions` 含 `'console.log'`：本族**没有** console 镜像，故不因此递归（与 C-08 不同，注意区分）。
  - `functions` 含 `'Array.prototype.splice'` ⇒ `__cap()` 超 2000 条时递归。

### 3.3 POSSIBLE：跨族共享页面状态（transparent 一旦装上，别族全线中招）

以下族**自己**不包装 `Array.prototype.push` / `Function.prototype.apply` / `Function.prototype.call` / `String.prototype.indexOf` / `String.prototype.charAt`，因此单跑安全；但 `browser_reverse_instrument mode=transparent`（C-17）一旦安装，这些方法在**同一页面**上被替换，于是它们的注入代码在 `try{}` 里对外**递归**（`RangeError`）或被 `catch(e){}` **静默吞掉**（M5）。涉及：

- 写日志型（`__lg.push` / `window.__mcp_*_log.push`）：C-10、C-11、C-12、C-20（5 处）、K-01（`L[k].push`）、K-05（`L.calls.push`）、K-08（`L.hits.push`）、V-10、M-01、M-02。
- 索引/字符型：C-03、C-09、C-10、C-13、C-16、C-19、C-20（`s.indexOf('debugger')`）、V-03、V-04、V-05、K-06（`p.indexOf(FIL)`——注意该行恒短路，实际不执行）。
- `.apply/.call` 型：C-01、C-05、C-07、C-09、C-11、C-12、C-20、C-25、K-01（`f.apply`/`OE.call`）、K-05、K-07、V-01、`MCP_Callbacks.wsv:217`、`MCP_Server_Form.wsv:349`。
- 数组遍历/切片型：C-13、C-16、C-22、K-06、K-07、V-07、V-09。

**另注（C-18 interpreter 的畸形 target，非递归但是同一"目标表"风险的后果）**：interpreter 分支（`:6401`）把 `window['<target>']` 整体替换为包装器，包装器体第一条语句是 `Array.prototype.slice.call(arguments)`。若 `target='Array'`，则 `window.Array` 变成包装器函数，其 `.prototype` 是包装器自己的空 prototype 对象 ⇒ `Array.prototype.slice` 为 `undefined` ⇒ `undefined.call(...)` 抛 `TypeError`（**不是**无限递归）。这类目标（`Array`/`Object`/`String` 等构造器）会把包装器变成会抛错的黑洞，与本审计的递归类相邻但不同，一并提示。

---

## 4. 伴生 read/clear 路径审计

| 读取/清空路径 | 位置 | 用的方法 | 会不会被包装吞掉 |
|---|---|---|---|
| `browser_reverse_hook_logs` **自动 clear** | `MCP_Server_Reverse.wsv:682` | `byKey[k]=v.length; cleared+=v.length; v.length=0;`、`v.results.length=0` | **SAFE**：全为属性赋值/长度截断，零方法调用。代码注释 `:678-679` 明确写了"clear 用原地截断(length=0/results.length=0), 不用 window[k]=[] 重新赋值"（原因在 `:679`：Hook 闭包持有旧数组引用）。 |
| `browser_reverse_hook_logs` **自动 query** | `:686` | `hit.push(k)`、`arr.slice(Math.max(0,arr.length-200))`、`items.push(it)`、`String(p[j]).substring(0,300)` | **会被吞**：`hit.push`/`items.push` 命中 `Array.prototype.push` 包装器；`arr.slice` 命中 `Array.prototype.slice`（若被包装）。⇒ 查询直接崩栈，用户看到的是失败而不是"日志为空"。 |
| `browser_reverse_hook_logs` 单键 **clear** | `:695` | `n=v.length; v.length=0;` | **SAFE** |
| `browser_reverse_hook_logs` 单键 **query** | `:701` | `items=v.slice(...)`、`v.results.slice(...)`、`safe.push(...)` | **会被吞**：`slice`+`push` 双命中。这也是 `__mcp_instrument_results`（对象型 `{results:[…]}`）的**唯一**服务端读路径（注释 `:699` 明确点名 `__mcp_instrument_results`）⇒ **C-17 的产物在 transparent 状态下连读都读不出来**。 |
| probe `get` / `clear` / `disable` | `MCP_Kernel.wsv:1296` / `:1309` / `:1315` | `JSON.stringify(...)` / `xhr=[]` 等重新赋值 / `delete` | **SAFE**（零被包装方法调用）。注：`clear` 用**重新赋值数组**，`probe` 的 `P()` 闭包引用的是 `L[k]`（`L` 是对象、属性重新赋值后仍指向新数组）⇒ 不会像 Hook 那样丢引用。 |
| trace `get` / `clear` / `stop` | `:1361` / `:1374` / `:1379` | `JSON.stringify` / `calls=[]` / `delete` | **SAFE** |
| algo `get` / `clear` / `stop` | `:1418` / `:1431` / `:1436` | 同上 | **SAFE** |
| watch_global `get` / `clear` / `stop` | `:1554` / `:1567` / `:1572` | 同上 | **SAFE** |
| IPC 队列读取 / 清空 | `MCP_Kernel.wsv:557` / `:552` | `JSON.stringify((window.__mcp_ipc_queue||[]))` / `(window.__mcp_ipc_queue=[])` | **SAFE**（stringify + 重新赋值）。但**写入**路径 M-01/M-02 用 `q.push` ⇒ POSSIBLE 跨（IPC 通道会静默不工作：`q.push` 抛 `RangeError` 后由 CEF 执行 JS 的错误通道吞掉，队列不增长）。 |
| Kernel 函数提取（读取型） | `MCP_Kernel.wsv:1457` | `out.push(...)`、`forEach(...)` | **会被吞**：既是"读页面函数"的路径，又用被包装的 `push`/`forEach` ⇒ transparent 状态下该工具失效。 |
| instrument 结果读取（无服务端工具） | `MCP_Server_Core.wsv:6395` 注入内 hint | 由用户 `browser_evaluate "JSON.stringify(window.__mcp_instrument_results)"` | **SAFE**（`JSON.stringify` 不走被包装原型）；但 `calls` 字段恒 0（§3.1 次生缺陷）。 |

**结论**：clear 路径普遍是安全的（多为长度截断/重新赋值），**query 读路径才是隐藏的第二个雷区**——尤其 `MCP_Server_Reverse.wsv:686/701`。

---

## 5. 修复清单（按严重度排序，含 exact before/after）

> 全部为**建议**，未验证。书写约定：`\\` 表示 `.wsv` 源码里的一个反斜杠（项目约定，见 `MCP_Server.wsv:6903` 的 `JS_REP_BSLASH <值 = "\\\\">`）；下文片段若需嵌入 `.wsv` 字面量，请保持该约定。
> 通用安全原语：`Reflect.apply(fn, thisArg, argsArray)`。它**不在** `Function.prototype` 上，因此替换 `Function.prototype.apply/call` 无法拦截它；在安装任何包装器**之前**捕获（`var __rApply=Reflect.apply;`）即对后续一切包装免疫（包括用户把 `Reflect.apply` 本身列为目标）。

### FIX-1（P0）C-17 `MCP_Server_Core.wsv:6395` —— transparent 包装器去递归 + 闸门前置 + `calls` 实时化

**1a 前置捕获**：把

```
var __count=0;var __max=500;var __results=[];__targets.forEach(
```

改为

```
var __count=0;var __max=500;var __results=[];var __rApply=Reflect.apply;__targets.forEach(
```

**1b 包装器体**（`before` 与 `after` 均为运行期 JS；`before` 原样取自 `:6395`）：

before：

```
__obj[__method]=function(){if(__count<__max){__results.push({target:__t,args:Array.prototype.slice.call(arguments).map(function(a){return typeof a==='string'?a.substring(0,200):typeof a}).join(','),ts:Date.now()});__count++}return __orig.apply(this,arguments)};
```

after：

```
__obj[__method]=function(){if(__count<__max){__count++;var __pv='',__i;for(__i=0;__i<arguments.length;__i++){if(__i>0)__pv+=',';var __s=arguments[__i];if(typeof __s==='string'){var __q='',__k;for(__k=0;__k<__s.length&&__k<200;__k++){__q+=__s[__k]}__pv+=__q}else{__pv+=typeof __s}}__results[__results.length]={target:__t,args:__pv,ts:Date.now()}}return __rApply(__orig,this,arguments)};
```

逐点说明为什么每条改动都是必要的：
- `__count++` 移到最前 ⇒ 修掉 M4（闸门在递归/写日志之前生效，即使将来又出现递归也会在 500 次内停止）。
- `__results.push({...})` → `__results[__results.length]={...}` ⇒ 去掉通路 1（M3），且索引赋值不可能被任何原型包装拦截。
- `Array.prototype.slice.call(arguments).map(...).join(',')` → 手写 `for` 循环 + 字符串 `+=`（含 200 字符手写截断）⇒ 去掉通路 2（`.call`）以及对 `.map`/`.join`/`.substring` 的依赖。**不要**用 `__push.call(...)` 之类的写法：`.call` 自身就是默认目标之一，等于把递归换个位置（`_audit/_instrument_cleanup_research.md:365` 建议的 `__push.call(...)` 有此残留风险）。
- `__orig.apply(this,arguments)` → `__rApply(__orig,this,arguments)` ⇒ 去掉通路 3，且保留 `this` 与 `arguments` 语义（`Reflect.apply` 与 `Function.prototype.apply` 在参数传递上等价）。
- 残留（低危、需用户刻意指定才触发）：`__obj[__method].toString=function(){return __orig.toString()}` 里的 `__orig.toString()` —— 若用户把 `Function.prototype.toString` 列为目标则会递归；`__targets.forEach` 的安装期遍历同理（实测无害：原生 `forEach` 已进入实现，替换 `Array.prototype.forEach` 不影响进行中的迭代）。

**1c `calls` 字段实时化**：把

```
window.__mcp_instrument_results={instrumented:__targets.length,calls:__count,results:__results};
```

改为

```
var __R={instrumented:__targets.length,results:__results};Object.defineProperty(__R,'calls',{get:function(){return __count}});window.__mcp_instrument_results=__R;
```

（`Object.defineProperty` 走的是 `Object` 静态方法，不在默认目标表内；若用户把 `Object.defineProperty` 列为目标，包装器体已是索引赋值 + `__rApply`，不会递归，且此处调用发生在安装循环之后。）

**1d（设计层，建议与 1a-1c 同时做）**：默认目标表不应包含"日志/转发通道"本体。建议把默认表的 `Array.prototype.push`、`Function.prototype.apply`、`Function.prototype.call` 去掉（甚至默认表改为空、强制显式 `target`），并在服务端对 `target` 做拒绝式校验（命中 `Array.prototype.push|apply|call|map|join|splice|slice`、`Function.prototype.apply|call|toString`、`console.log` 时直接返回 `命令失败` 并说明原因）。**这条同时消灭 §3.3 的全部 POSSIBLE 位点**——收益最大。

### FIX-2（P0）V-10 `MCP_Server_Reverse.wsv:798-799` —— hook_multi 去递归

- 在 `:798` 段开头（`var lg=…` 之前）插入：`var __rApply=Reflect.apply;`
- `:798` 的 `function __cap(){if(lg.length>2000){lg.splice(0,1000);}}`

  before：`function __cap(){if(lg.length>2000){lg.splice(0,1000);}}`
  after：`function __cap(){if(lg.length>2000){var __z=0;for(;__z+1000<lg.length;__z++){lg[__z]=lg[__z+1000]}lg.length=(lg.length>1000?lg.length-1000:0);}}`
  （左移 1000 时"写 `lg[__z]`、读 `lg[__z+1000]`"不互相污染；`lg.length` 收尾截断是索引赋值。）
- `:799` 的四处替换：

  | before | after |
  |---|---|
  | `var a=Array.prototype.slice.call(arguments);` | `var a=[],__ai;for(__ai=0;__ai<arguments.length;__ai++){a[a.length]=arguments[__ai]}` |
  | `var r=__orig.apply(this,a);` | `var r=__rApply(__orig,this,a);` |
  | `__cap();lg.push(e);` | `__cap();lg[lg.length]=e;` |
  | `__cap();lg.push({fn:name,ts:Date.now(),threw:x.message});` | `__cap();lg[lg.length]={fn:name,ts:Date.now(),threw:x.message};` |
  | `found.push(name);` | `found[found.length]=name;` |

- 残余（低危）：`e.args=JSON.stringify(a).substring(0,512)`、`String(r).substring(0,512)` 使用 `String.prototype.substring`（不在默认表内；若被列为目标则递归）。若要求"零被包装方法"，把截断改为手写 `for` 循环（同 FIX-1b 的 `__q` 写法）。

### FIX-3（P0）C-08 `MCP_Server_Core.wsv:6115/6128` —— hook(function_call) 去递归 + console 自指

- 在 `:6115` 段 `var __wrapper=function(){` 之前插入 `var __rApply=Reflect.apply;`（位置须在 `__cap` 定义附近、`__wrapper` 之前，保证闭包可见）。
- `:6115` 段：
  before：`var __args=Array.prototype.slice.call(arguments);var __result=__orig.apply(this,__args);`
  after：`var __args=[],__ai;for(__ai=0;__ai<arguments.length;__ai++){__args[__args.length]=arguments[__ai]}var __result=__rApply(__orig,this,__args);`
- `:6128` 段：
  - before：`__cap();__lg.push(__entry);console.log('[...]',JSON.stringify(__entry));return __result;`
    after：`__cap();__lg[__lg.length]=__entry;return __result;`（把 console 镜像整段移出，或按下面"条件发射"保留）
  - before（catch）：`__cap();__lg.push(__te);throw __x;}`
    after：`__cap();__lg[__lg.length]=__te;throw __x;}`
- **console 自指的最小修法（火山侧条件拼接，推荐）**：不要删掉 console 镜像（它是有用的双通道），而是在模板层判断：当目标就是 console.log 时不发射该镜像，例如在 `如果 (captureStack)` 之后加

```
如果 (hookEsc != "console.log" && hookEsc != "window.console.log")
{
    hookCode = hookCode + "console.log('[" + hookLabel + "]',JSON.stringify(__entry));"
}
```

  （把原来硬拼在 `:6128` 字符串里的那段 `console.log(...)` 摘出来做成条件片段；`hookTarget` 若写成 `window.console.log` 需一并判断。）
- `__cap()` 的 `__lg.splice(0,1000)` → 与 FIX-2 相同的索引左移写法。

### FIX-4（P1）K-03 `MCP_Kernel.wsv:1349` —— trace 去递归 + 裁剪去方法调用

| before | after |
|---|---|
| `var args=[].slice.call(arguments);` | `var args=[],__ai;for(__ai=0;__ai<arguments.length;__ai++){args[args.length]=arguments[__ai]}` |
| `var r=orig.apply(this,arguments);` | `var r=__rApply(orig,this,arguments);` |
| `T.calls.push({p:path,a:args.map(S).slice(0,10),r:S(r),ms:Date.now()-t0,st:st?st.slice(0,300):''});if(T.calls.length>T.limit)T.calls.shift();` | `var __A=[],__k2;for(__k2=0;__k2<args.length&&__k2<10;__k2++){__A[__A.length]=S(args[__k2])}T.calls[T.calls.length]={p:path,a:__A,r:S(r),ms:Date.now()-t0,st:st?st.slice(0,300):''};if(T.calls.length>T.limit)T.calls.length=0;` |
| catch 分支同样的 `T.calls.push({...});if(T.calls.length>T.limit)T.calls.shift();` | 同上（索引赋值 + 超限时 `T.calls.length=0`） |

- 需在 IIFE 顶部（`var T=window.__MCP_TRACE__=…` 之后）插入 `var __rApply=Reflect.apply;`。
- `T.calls.length=0` 是"超限即清空"的最简替代（原 `shift()` 是丢最旧一条）；若必须保序丢最旧，用 FIX-2 的索引左移一段。**关键是 `push` 换成索引赋值后，"先写后判"不再有递归风险**。
- 建议同时加服务端目标校验（拒绝 `Array.prototype.push`/`Function.prototype.apply`/`Function.prototype.call` 等）——trace 是"用户随便传 targets"的工具，白名单/黑名单比逐点加固更省事。

### FIX-5（P1）V-07 / V-09 `MCP_Server_Reverse.wsv:686 / :701` —— hook_logs **读路径**去递归

- `:686`：
  - `hit.push(k);` → `hit[hit.length]=k;`
  - `var p=arr.slice(Math.max(0,arr.length-200));` → `var __lo=(arr.length>200?arr.length-200:0);var p=[],__x;for(__x=__lo;__x<arr.length;__x++){p[p.length]=arr[__x]}`
  - `items.push(it);` → `items[items.length]=it;`
- `:701`：
  - `items=v.slice(Math.max(0,v.length-200));` → 同上索引拷贝（`v.results.slice(...)` 同理）
  - `safe.push(JSON.parse(JSON.stringify(items[i])))` → `safe[safe.length]=JSON.parse(JSON.stringify(items[i]))`
  - 两处 `safe.push(String(items[i]).substring(0,300))` / `safe.push('[unserializable]')` → 索引赋值
- clear 分支（`:682`/`:695`）**无需改**（已是 SAFE，且注释解释了为什么必须原地截断——不要为了统一风格把它改成 `push`/`splice`）。

### FIX-6（P1）K-06 `MCP_Kernel.wsv:1457` —— 函数提取读路径

- `out.push({p:p,n:f.name||'',l:f.length,s:src.slice(0,1500)})` → `out[out.length]={p:p,n:f.name||'',l:f.length,s:src.slice(0,1500)}`
- `Object.keys(window).forEach(...)` / `['location',…].forEach(...)` / `Object.getOwnPropertyNames(C.prototype).forEach(...)` → 改为 `for` 循环（`keys[i]` 索引访问）。不改也能跑（`forEach` 不在默认表内），但 `push` 必改。
- **无需改** `if(FIL&&p.indexOf(FIL)<0)return;`：`var FIL='' ;` 恒为假值，整条短路，`indexOf` 运行期不执行（静态确定；若将来把 `FIL` 改成实参，这一行就会变成 `String.prototype.indexOf` 命中点，届时要一起改）。

### FIX-7（P2）POSSIBLE 位点的机械清扫（或直接做 FIX-1d 一劳永逸）

若不做 FIX-1d（缩小默认目标表），则下列注入族应按下表机械替换（这些位点在 transparent 状态下会被吞或崩栈）：

| 位点 | before | after |
|---|---|---|
| `MCP_Server_Core.wsv:2028`、`:2871/2879/2888`、`:6221/6225`、`:6286`、`:6439`、`:6488/6548`、`:6993`、`:7057/7058`、`:7123`、`:7202`；`MCP_Kernel.wsv:1542`；`main.wsv:457/762` | `X.push(y)` | `X[X.length]=y` |
| `MCP_Server_Core.wsv:6439/6488/6548`、`MCP_Kernel.wsv:1457` | `arr.forEach(function(v,i){…})` | `for(var i=0;i<arr.length;i++){var v=arr[i];…}` |
| `MCP_Server_Core.wsv:1805/3202/3206/3209/3211/3214/6905/6909/6913/7396`、`MCP_Kernel.wsv:1278/1402`、`MCP_Server_Reverse.wsv:256/260`、`MCP_Callbacks.wsv:217`、`MCP_Server_Form.wsv:349` | `f.call(thisArg,…)` / `f.apply(thisArg,args)` | `__rApply(f,thisArg,[…])`（`__rApply` 在注入 IIFE 顶部先行捕获） |
| `MCP_Server_Core.wsv:2747/2751`、`MCP_Server_Reverse.wsv:563`、`MCP_Kernel.wsv:1402` | `s.indexOf(t)` / `s.charAt(i)` | 视语境改写（`===` 比较、`for` 逐字符比较、或在注入顶部捕获 `var __idxOf=String.prototype.indexOf;` 再用 `__rApply(__idxOf,s,[t])`） |
| `MCP_Server_Core.wsv:6395`、`MCP_Kernel.wsv:1349/1402/1542` | `A.push(x);if(A.length>limit)A.shift();` | `A[A.length]=x;if(A.length>limit)A.length=0;`（或索引左移） |

---

## 6. 静态无法判定的事项（不要当成已验证）

1. **实测那次 `RangeError` 的首个递归帧具体是 `push`、`apply` 还是 `call`**：我能证明三条通路都会无限递归（§3.1），但"页面第一次调用 6 个方法里的哪一个"取决于运行期，源码不可判定。帧名 `at __obj.<computed> (<anonymous>:1:544)` 只证明命中点在 `__obj[__method]=function(){…}` 形态的包装器上。
2. **transparent 注入本身是否会在安装阶段就抛错**：静态看安装循环与随后语句都不调用 6 个目标方法（`forEach/split/toString/JSON.stringify/typeof` 均不在表内），故推断"注入返回 `installed:true`，崩溃发生在之后第一次调用"。此推断**未运行验证**。
3. **引擎内部调用是否也走被替换的原型方法**：例如 `JSON.stringify`、`console.log`、`Object.keys` 在 V8/Blink 内部是否经由 JS 可见的 `String.prototype.indexOf` 等；若走，破坏面比静态分析更大。未验证（且本项目禁止我运行/编译）。
4. **CEF 构建里 `Reflect.apply` 是否存在**（FIX-1/2/4 依赖它）。现代 Blink 都有，但我没有核对该 CEF 版本；若无，替代方案是在安装前捕获 `var __apply=Function.prototype.apply,__call=Function.prototype.call;` 并用"捕获值 + 一次性的 bind 前绑定"（`var __invoke=Function.prototype.call.bind(Function.prototype.apply)`，同样需在安装前执行）来调用原函数——**该替代方案我未验证**。
5. **跨族"页面状态共享"的真实共现组合**：我按"同一页面 + 先后调用"推断 POSSIBLE，但没有运行日志能确定用户实际把哪些族叠在同一页面（`_audit/_instrument_cleanup_research.md:387` 记录了同样的证据缺口）。
6. **`browser_reverse_preset` 的 `debugger` 分支副作用**：`MCP_Server_Core.wsv:6917` 用 `fn.toString()`/`s.indexOf('debugger')` 判定并 `return 0` 静默丢弃任务；它与本缺陷类无关，但同一族里"静默丢弃"的语义可能掩盖其它问题，我未展开审计。
7. **行号稳定性**：审计期间 `MCP_Server_Reverse.wsv`（+17 行）与 `MCP_Server.wsv`（+423 行）被外部改动；本报告行号对应 §0.1 的哈希快照。后续引用请以锚点串检索（例：`Array.prototype.slice.call(arguments).map(function(a){return typeof a==='string'?a.substring(0,200):typeof a}).join(',')`）。
8. **"+18 个注入家族"的口径**：我按"注入点"枚举得到 **Core 25 处 + Kernel 9 处 + Reverse 10 处 + main 2 处 = 46 个位点**（其中真正**安装包装器**的是 15 个：Core `:3186-3218`、`:6115`、`:6146`、`:6157`、`:6162`、`:6167`、`:6395`、`:6401`、`:6749`、`:6897-6917`；Kernel `:1278`、`:1349`、`:1402`、`:1542`；Reverse `:799`）。家族数与位点数的差异取决于分组口径，我无法判定主 agent 所指的"18"对应哪套分组。

---

## 7. 一句话结论

本缺陷类在代码库里**不止已确认的那一处**：

- **默认参数即递归（1 处）**：`MCP_Server_Core.wsv:6395` `browser_reverse_instrument` transparent —— 三条递归通路（`__results.push` / `Array.prototype.slice.call` 的 `.call` / `__orig.apply`），且 `__count++` 在递归语句之后（M4），`calls` 还恒为 0。
- **参数门控即递归（3 处）**：`MCP_Server_Core.wsv:6115+6128`（`browser_reverse_hook` function_call，含 `console.log` 自指这一条独立通路）、`MCP_Kernel.wsv:1349`（`browser_kernel_reverse_trace`）、`MCP_Server_Reverse.wsv:799`（`browser_reverse_hook_multi`，**安装期**即递归）。
- **读路径第二雷区（2 处）**：`MCP_Server_Reverse.wsv:686` / `:701`（`browser_reverse_hook_logs` query 用 `push`/`slice`），而它的 **clear 路径已刻意做成安全**（`:682`/`:695`）。
- **跨族 POSSIBLE（约 30 个位点）**：由 transparent 的默认 6 项目标表引起，覆盖几乎所有注入族的 `push`/`apply`/`call`/`indexOf`/`charAt` 调用；`MCP_Kernel.wsv:1278` 探针还会被 `catch(e){}` 吞成**静默无数据**（M5）。
- **最高杠杆的修法**：先做 FIX-1（去递归 + 闸门前置 + `calls` 实时化），**并**把默认目标表里的 `Array.prototype.push`、`Function.prototype.apply`、`Function.prototype.call` 去掉/强制显式指定 —— 后者一次性消灭全部 POSSIBLE 位点。
