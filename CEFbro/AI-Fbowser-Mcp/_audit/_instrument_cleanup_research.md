# 插装/挂钩 卸载与还原 可行性调研（只读静态分析）

- 调研时间：2026-09-13 04:15–04:18（本地）
- 工作区：`C:\Users\cxzxc\Desktop\MCP源码\ai-browser-mcp\CEFbro\AI-Fbowser-Mcp`
- 方式：**纯静态阅读**。未编译、未调用任何 MCP 工具、未启动/停止任何程序、未修改任何源文件。本文件是本次唯一写入物。
- **本报告所有结论均为静态阅读所得，未经运行验证。** 验证由主 agent 单独进行。

## 0. 快照指纹 —— `MCP_Server_Core.wsv` 正在被并发高频修改（先读这一节）

本次阅读（约 4 分钟）内，`src/MCP_Server_Core.wsv` **被其它进程改了 4 次**（mtime 04:14:34 → 04:16:53 → 04:17:33 → 04:18:05），行数 7298 → 7324 → 7331 → 7449 → **7457**；`src/MCP_Server.wsv` 也被改了 2 次（内容变、行数不变）。**因此行号是错误的定位方式。**

**定位规则（重要）**：请用「锚点片段」（下表左列的 JS/火山代码原文片段）在文件里检索定位；右侧行号只是「截至本报告所取快照」的参考值，只对下表中的 hash 成立。**本报告的 `Core:` 行号对应 hash `FBB1FEFE11349FC5`（行数 7449，mtime 04:17:33），写完后该文件已再次变动（`F506ADF0A68048E5`，7457 行，mtime 04:18:05，增量 +8）——即 Core 行号在当前时刻已整体偏移，必须按锚点重新定位。**

| 文件 | 行数 | sha256（前16位，本报告行号的基准） | 备注 |
|---|---|---|---|
| `src/MCP_Server_Core.wsv` | 7449 | `FBB1FEFE11349FC5` | 承担绝大多数注入模板，**阅读期间被改了 4 次；行号已失效，用锚点** |
| `src/MCP_Server.wsv` | 10986 | `AE74703F15008999` | 仅工具注册/命令注册表，**被改了 2 次** |
| `src/MCP_Kernel.wsv` | 1800 | `7CD3CB1DCB854081` | probe/trace/algo/gwatch/ipc 注入模板（未变） |
| `src/MCP_Server_Reverse.wsv` | 2295 | `2BE0773D02F901E2` | hook_logs / hook_multi / CDP 级族（未变） |
| `src/main.wsv` | 809 | `74368D23E3619743` | IPC 队列下行注入（未变） |

行数用原始字节 LF 计数（`CR=0`），与编辑器/read 工具一致，并经 `read` 读到文件末尾交叉核对（`MCP_Server.wsv` 尾部 10986、`main.wsv` 尾部 809）。
注意 `Get-Content .Count` 本次给的数字偏小（如 `MCP_Server_Core.wsv` 给 7091），**不要用它的行号**。

**`MCP_Server_Core.wsv` 行号漂移实测（同一片段在不同时刻的位置）：**

| 锚点片段（文件内唯一，可 grep 定位） | 04:14 前 | 04:14:34 | 04:16:53 | **04:17:33（本报告采用）** |
|---|---|---|---|---|
| `否则 (方法名 == "browser_reverse_hook")` | 5951 | 5951 | 5958 | **6076** |
| `hookCode = "(function(){var __parts=` … （F5 核心） | 5956 | 5982 | 5989 | **6107** |
| `__obj[__last]=__wrapper`（F5 安装） | 5969 | 5995 | 6002 | **6120** |
| `否则 (方法名 == "browser_reverse_instrument")` | 6215 | 6241 | 6248 | **6366** |
| `insCode = "(function(){var __targets=` …（F1 核心） | 6236 | 6262 | 6269 | **6387** |
| `否则 (方法名 == "browser_reverse_preset")` | 6722 | 6748 | 6755 | **6873** |
| `cnCode = cnCode + "if(!window.__MCP_CANVAS_ORIG__)`（F15） | 3192 | 3192 | 3192 | **3192（全程未变）** |

**最后一次复核（本报告写入后）**：在 hash `F506ADF0A68048E5`（7457 行，mtime 04:18:05）上重查 F1：
`否则 (方法名 == "browser_reverse_instrument")` 在 **6374** 行，`insCode = "(function(){var __targets=…` 在 **6395** 行（即相对本报告采用的 `FBB1FEFE` 整体 **+8**），且注入代码内容**逐字节一致**（仍然没有 `__mcp_orig`、仍然用 `__results.push({target:__t,…})`）→ **F1 的不可还原性与自递归缺陷在最新快照上依然成立**。若主 agent 拿到的行号比本报告大 8，按这个偏移平移即可，或用本节的锚点串直接检索。

**若主 agent 现在动手：(a) 先 `Get-FileHash` 重算基准；(b) 确认没有别的 agent 正在同一批文件上实施「卸载入口」，否则会直接冲突。**

---

## A. 注入点全量清单

「包装对象」= 被替换掉原函数的宿主对象/属性。「可还原」= 注入代码是否把原函数保存在**外部可达**的位置。
表中 `Core:` = `src/MCP_Server_Core.wsv`，`Srv:` = `src/MCP_Server.wsv`，`K:` = `src/MCP_Kernel.wsv`，`Rev:` = `src/MCP_Server_Reverse.wsv`，`main:` = `src/main.wsv`。

### A-1 页面 JS 猴子补丁族（本报告主体）

| # | 工具名（注册处） | 注入创建的 JS 全局 | 被包装的对象·属性 | 注入·file:line | 原函数保存位置 | 可还原 | 现有清理入口 |
|---|---|---|---|---|---|---|---|
| F1 | `browser_reverse_instrument` mode=transparent（`Srv:9833`） | `window.__mcp_instrument_results` | `Function.prototype.apply` / `.call`、`Array.prototype.push` / `.pop`、`String.prototype.indexOf` / `.charAt`（target 为空时的默认表） | `Core:6387`（派发 `:6366`） | 仅 IIFE 内 `forEach` 回调闭包局部量 `__orig` | **否（不可达闭包）** | **无**（dispatcher 只认 `mode`） |
| F2 | `browser_reverse_instrument` mode=interpreter（同 `Srv:9833`） | `window.__mcp_interpreter_logs` | `window[<target>]`（用户指定，必填） | `Core:6393` | 仅 IIFE 闭包局部量 `__orig` | **否（不可达闭包）** | **无** |
| F3 | `browser_reverse_initiator`（`Srv:9835`） | `window.__mcp_initiator_log` | `XMLHttpRequest.prototype.open`、`window.fetch` | `Core:6741`（派发 `:6728`） | 仅 IIFE 闭包 `_origOpen` / `_origFetch` | **否（不可达闭包）** | **无**（只有 `url_pattern`/`request_id`，无 action） |
| F4 | `browser_reverse_preset`（`Srv:9836`） | `window.__mcp_xhr_log` / `__mcp_fetch_log` / `__mcp_cookie_log` / `__mcp_ws_log` / `__mcp_crypto_log` | `XMLHttpRequest.prototype.open`；`window.fetch`；`document.cookie` 描述符；`WebSocket.prototype.send`；`SubtleCrypto.prototype.digest`；`window.setInterval` / `window.setTimeout` | `Core:6889`（xhr）、`:6893`（fetch）、`:6897`（cookie）、`:6901`（ws）、`:6905`（crypto）、`:6909`（debugger bypass）；派发 `:6873` | 全部为 IIFE 内 `var __origXHROpen` / `__origFetch` / `__origCookieDesc`+`__origCookieSet` / `__origWSSend` / `__origDigest` / `__origSetInterval`+`__origSetTimeout` | **否（不可达闭包）** | **无**（只有 `preset` 参数） |
| F5 | `browser_reverse_hook` type=function_call（`Srv:9827`） | `window.__MCP_HOOK_LOG__` | 用户给的 `obj.fn` 点路径 | `Core:6107`（`__orig` 捕获）+ `:6120`（安装）；派发 `:6076` | IIFE 闭包 `__orig`；wrapper 上打了 `__mcp_hooked` 标记 + 伪造 `toString` | **否（标记≠备份）** | **无**（只有 `browser_reverse_hook_logs`，见 C 节） |
| F6 | `browser_reverse_hook` type=xhr_fetch | 无（仅 `console.log`） | `XMLHttpRequest.prototype.open` | `Core:6138` | IIFE 闭包 `__origOpen` | **否** | **无** |
| F7 | `browser_reverse_hook` type=websocket | `window.__MCP_WS_LOG__` | `WebSocket.prototype.send` | `Core:6149` | IIFE 闭包 `__os` | **否** | **无** |
| F8 | `browser_reverse_hook` type=eval_dynamic | `window.__MCP_EVAL_LOG__` | `window.eval`、`window.Function` | `Core:6154` | IIFE 闭包 `__oe` / `__oF` | **否** | **无** |
| F9 | `browser_reverse_hook` type=cookie_set | `window.__MCP_COOKIE_LOG__` | `Document.prototype.cookie` 描述符（整体 `defineProperty` 覆盖） | `Core:6159` | IIFE 闭包 `__d` / `__s` | **否** | **无** |
| F10 | `browser_reverse_hook_multi`（`Srv:9877`） | `window.__MCP_HOOK_LOG__` | 用户给的函数名数组（每个 `obj[last]`） | `Rev:782`（包装）、`:781`（日志）、派发 `:739` | IIFE 闭包 `__orig`（循环每轮重新赋值） | **否** | **无** |
| F11 | `browser_kernel_reverse_probe` action=enable（`Srv:9716`） | `window.__MCP_PROBE__` | `XMLHttpRequest.prototype.open/send`、`window.fetch`、`WebSocket.prototype.send/close`、`window.setTimeout/setInterval`、`EventTarget.prototype.addEventListener` | `K:1278` | IIFE 闭包 `f`（每个 `forEach` 迭代一个）；`L.orig` **声明了但从未写入**（见 B-3） | **否** | `action=disable` 仅 `delete window.__MCP_PROBE__`（`:1315`）、`action=clear` 仅清数组（`:1309`） |
| F12 | `browser_kernel_reverse_trace` action=start（`Srv:9717`） | `window.__MCP_TRACE__` | 用户 `targets` 点路径 | `K:1349` | `wrap()` 内闭包 `orig`；wrapper 打 `__mcp_tr=true` 标记 | **否（标记≠备份）** | `action=stop` 仅 `delete window.__MCP_TRACE__`（`:1379`） |
| F13 | `browser_kernel_reverse_algo` action=start（`Srv:9718`） | `window.__MCP_ALGO_LOG__` | `CryptoJS.<16个算法>`、`window.md5/sha1/sha256/sha512/btoa/atob/encodeURIComponent/decodeURIComponent`、`crypto.subtle.<7个方法>` | `K:1402` | 各 `forEach` 闭包 `fn`；wrapper 打 `__mcp_al=true` 标记 | **否（标记≠备份）** | `action=stop` 仅 `delete window.__MCP_ALGO_LOG__`（`:1436`） |
| F14 | `browser_kernel_reverse_watch_global` action=start（`Srv:9721`） | `window.__MCP_GWATCH__` | `Object.defineProperty(window, <name>, {get,set,configurable:true})` | `K:1542` | 闭包变量 `v` 持有值；**原属性描述符未保存** | **部分可行**（见 B-5） | `action=stop` 仅 `delete window.__MCP_GWATCH__`（`:1572`） |
| F15 | `browser_canvas_noise` action=inject/enable（`Srv:9857`） | `window.__MCP_CANVAS_ORIG__`、`window.__MCP_CANVAS_NOISED__`、`window.__MCP_CANVAS_NOISE_LVL__` | `HTMLCanvasElement.prototype.toDataURL/toBlob`、`CanvasRenderingContext2D.prototype.getImageData` | `Core:3186`–`:3218`（备份在 `:3192`；派发 `:3159`） | **显式存进全局对象 `window.__MCP_CANVAS_ORIG__`** | **是** | `action=remove/disable`：`Core:3227` **真正回写原函数** |
| F16 | `browser_permission_spoof` action=apply/spoof（`Srv:9854`） | 无全局（只在实例上做自有属性遮蔽） | `navigator.permissions.query`、`navigator.mediaDevices.enumerateDevices` | `Core:3327`–`:3348`（派发 `:3295`） | 未替换原型方法，只在实例上新建同名自有属性遮蔽原型 | **是**（`delete` 自有属性即让原型原生实现重新可见） | `action=reset/remove`：`Core:3356` |
| F17 | `browser_reverse_cookie_sources`（`Srv:9831`） | **无 —— 该工具根本不注入 JS** | —— | 派发 `Core:6291`；实现走原生 `FBrowser_Cookie管理器_取全局 ().取地址Cookie(...)` `:6314` | 不适用 | 不适用 | 不需要 |
| F18 | IPC 队列下行（非 Hook，纯数据） | `window.__mcp_ipc_queue` | 无（只 `q.push(...)`） | `main:457`（主进程→页面）、`main:762`（渲染侧事件） | 不适用（无函数替换） | 不适用 | `browser_kernel_ipc_queue` action=clear：`K:552` |

### A-2 CDP/内核级元安装（不是页面 JS 补丁，但有「装机残留」概念）

| 工具名 | 安装对象 | file:line | 卸载入口 |
|---|---|---|---|
| `browser_reverse_preload` | `Page.addScriptToEvaluateOnNewDocument`（对**之后每次加载**都生效） | 派发 `Rev:266`，CDP 调用 `:318` | **未找到**。全文搜索 `removeScriptToEvaluateOnNewDocument` → **not found** |
| `browser_reverse_add_binding` | `Runtime.addBinding` | 派发 `Rev:1471`，CDP `:1493` | **未找到**。搜索 `removeBinding` → **not found** |
| `browser_reverse_instrument_script` | `Debugger.setInstrumentationBreakpoint` | 安装 `Rev:903` | **有**：`action=remove`（`:988` 调 `Debugger.removeInstrumentationBreakpoint`）、`action=suppress`（`:971` 起的止血分支）。`:998` 原文承认本机不支持单独卸载：`"本机Chromium无法单独卸载插装断点(" + MCP命令服务器.取CDP同步结果错误 (ivRmRes) + ") | 立刻止血: action=suppress (插装保留但页面不再暂停, 不丢任何状态) | 彻底清除: browser_debugger_disable (注意它会同时清掉全部断点)"` |
| `browser_reverse_network_intercept` | `Network.setRequestInterception` | `Rev:458` | **有**：`action=disable` → `"{\"patterns\":[]}"`（`:462`） |
| `browser_reverse_cdp_hook` | `Debugger.setBreakpointOnFunctionCall` | 派发 `Rev:97` | **未在本族内实现**；项目另有通用断点管理工具，能否清除未确认（见 F-8） |
| 内核开关族：`browser_reverse_bypass_csp` / `_cache_disable` / `_emulate_focus` / `_layer_tree` / `_breakpoints_active` / `_skip_pauses` | 内核/会话开关 | `Rev:1631` / `:1646` / `:1686` / `:1788` / `:1079` / `:1089` | **有**（成对 `enable/disable` 或 `enabled=true/false` / `active` / `skip`） |
| `browser_inject`（`persist=true`） | 持久 V8 扩展列表（新页面/新 iframe 自动注入，**刷新也不清**） | `Core:2906-2938`（`加入持久V8扩展` 于 `:2920` / `:2937`），注释 `:2908` 原文 `"持久js模式: 存入持久V8扩展列表, 由 渲染_即将创建V8环境 → V8环境.执行JS代码 自动注入"` | 本次未在本族内找到 remove；属独立持久配置族（**未展开**，见 F-7） |

搜索方式（可复现）：对 `src/` 全目录 grep `window\.__`、`__mcp_|__MCP_`、`\.prototype\.|Object\.defineProperty`、`执行JS代码_带返回值|CDP执行JS并等待|提交异步JS任务|执行JS代码并等待`（139 处命中，逐条筛出上表）。`index.html`、`mcp_bridge.js` 内 grep `__mcp_|__MCP_` → **not found**。

---

## B. 逐族「原函数有没有被保存」取证（决定性证据）

### B-1 F1 `browser_reverse_instrument` mode=transparent —— 不可达闭包 + 自递归缺陷

`Core:6387`（我把超长单行折行并加缩进便于阅读；字段名/参数/调用顺序与原文字节一致，`…` 标记我省略的模板拼接部分）：

```js
(function(){var __targets=['Function.prototype.apply','Function.prototype.call','Array.prototype.push',
  'Array.prototype.pop','String.prototype.indexOf','String.prototype.charAt'];
var __count=0;var __max=500;var __results=[];
__targets.forEach(function(__t){var __parts=__t.split('.');var __obj=window;
  for(var __i=0;__i<__parts.length-1;__i++){__obj=__obj[__parts[__i]];if(!__obj)return}
  var __method=__parts[__parts.length-1];var __orig=__obj[__method];
  if(typeof __orig!=='function')return;
  __obj[__method]=function(){if(__count<__max){__results.push({target:__t,
      args:Array.prototype.slice.call(arguments).map(function(a){return typeof a==='string'?a.substring(0,200):typeof a}).join(','),
      ts:Date.now()});__count++}
    return __orig.apply(this,arguments)};
  __obj[__method].toString=function(){return __orig.toString()}});
window.__mcp_instrument_results={instrumented:__targets.length,calls:__count,results:__results};
return JSON.stringify({installed:true,targets:__targets.length,hint:'Transparent instrumentation installed. toString preserved. …'})})()
```

判定依据：
1. `var __orig=__obj[__method];` 是 `forEach` 回调的**局部变量**，只被闭包里的 wrapper 引用；`window.__mcp_instrument_results` 里**只有 `instrumented`/`calls`/`results` 三个字段**，**不含任何原函数引用**。
2. 没有 `obj[name].__mcp_orig = orig` 之类的回填，也没有全局注册表。

**⇒ 原函数不可从外部取回，卸载在「不刷新页面」前提下不可能。**

同时，静态阅读即可解释已观测到的 `RangeError: Maximum call stack size exceeded` / `at __obj.<computed> (<anonymous>:1:544)`：
wrapper 体（所有 target 共用同一段闭包）内部写的是 `__results.push({...})`。当 `Array.prototype.push` 也在 target 表里（默认表第 3 项就有 `'Array.prototype.push'`）时，`__results.push` 解析到的正是**刚被替换掉的 wrapper**，于是 wrapper→push→wrapper 无限自递归；而 `__count++` 写在 `__results.push` **之后**，永不执行，计数永远到不了 `__max`、无法退出。栈帧名 `__obj.<computed>` 与注入代码里 `__obj[__method]=function(){…}` 的形态一一对应。
（这是**静态推断**；其栈帧文本与 `_audit/append_report_95.py:94-95`、`_audit/diag_reverse_search_js.py:92` 记录的实测一致，但我本人未运行验证。）

### B-2 F5 / F10 / F12 / F13 —— 「标记」不是「备份」

F5/F12/F13 只在 wrapper 上打了幂等标记，F10 连标记都没有；**没有任何一族**把原函数写回外部可达位置：

- F5 `Core:6120`：
  ```js
  __obj[__last]=__wrapper;if(__obj[__last]!==__wrapper){return JSON.stringify({found:false,target:'…',error:'not_writable(对象可能被冻结, 无法安装Hook)'})}
  __wrapper.toString=function(){return __orig.toString()};__wrapper.__mcp_hooked=true;
  ```
  `__mcp_hooked=true` 只是重入护栏（`Core:6107` 的 `if(__t.__mcp_hooked){return JSON.stringify({found:true,…,already:true,…})}`），`__orig` 仍在闭包里。
- F12 `K:1349`（`wrap()` 内）：
  ```js
  var f=obj[name];if(typeof f!=='function'||f.__mcp_tr)return;var orig=f;
  obj[name]=function(){…orig.apply(this,arguments)…};obj[name].__mcp_tr=true
  ```
- F13 `K:1402`：
  ```js
  var fn=CryptoJS[n];if(typeof fn==='function'&&!fn.__mcp_al){CryptoJS[n]=function(){…fn.apply(this,arguments)…};CryptoJS[n].__mcp_al=true}
  ```
- F10 `Rev:782`：`var __orig=obj[last];obj[last]=function(){…}` —— 连幂等标记都没有（重复调用会**叠加包装**）。

### B-3 F11 探针：声明了备份位却从未写入

`K:1278` 的对象字面量里有 `orig:{}`：
```js
var L=window.__MCP_PROBE__={xhr:[],fetch:[],ws:[],timers:[],listeners:[],limit:300,orig:{}};
```
对 `src/MCP_Kernel.wsv` 全文 grep `\.orig|orig:` → **只有这 1 处命中**（即只有声明，没有任何 `L.orig[...]=` / `L.orig.x=` 写入）。同一个 IIFE 里原函数是这么拿的：`var f=OX[m];OX[m]=function(){…return f.apply(this,arguments)}` —— 仍是闭包局部量。

**⇒ `orig:{}` 是空壳/死字段，不能作为还原依据。**

### B-4 F11/F12/F13/F14 的 `disable`/`stop` 只删数据对象，而且删完还能再叠一层

- F11 `K:1315-1316`：
  ```js
  MCP命令服务器.CDP执行JS并等待 ("(delete window.__MCP_PROBE__,'ok')", 8000, 真)
  返回 (MCP_响应构建.命令成功 (命令ID, "探针已移除(建议刷新页面彻底清除)"))
  ```
- F12 `K:1379-1380`：
  ```js
  MCP命令服务器.CDP执行JS并等待 ("(delete window.__MCP_TRACE__,'ok')", 8000, 真)
  返回 (MCP_响应构建.命令成功 (命令ID, "追踪已停止(建议刷新页面彻底恢复原函数)"))
  ```
- F13 `K:1436-1437`：
  ```js
  MCP命令服务器.CDP执行JS并等待 ("(delete window.__MCP_ALGO_LOG__,'ok')", 8000, 真)
  返回 (MCP_响应构建.命令成功 (命令ID, "算法Hook已停止(建议刷新页面彻底恢复)"))
  ```
- F14 `K:1572-1573`：
  ```js
  MCP命令服务器.CDP执行JS并等待 ("(delete window.__MCP_GWATCH__,'ok')", 8000, 真)
  返回 (MCP_响应构建.命令成功 (命令ID, "变量追踪已停止(建议刷新页面彻底恢复)"))
  ```

原文里的 `"建议刷新页面彻底清除/恢复"` **就是项目自己承认这些动作不是还原**。

另一个静态副作用：这四个族的重新注入护栏都是 IIFE 第一句 `if(window.__MCP_PROBE__)return'__already'` / `if(window.__MCP_TRACE__)return'__already'` / `if(window.__MCP_ALGO_LOG__)return'__already'` / `if(window.__MCP_GWATCH__)return'__already'`（`K:1278` / `:1349` / `:1402` / `:1542`）。`disable`/`stop` 把这个全局删掉后护栏即失效：
- **F11 探针**：`OX[m]`/`window.fetch`/`OWS[m]`/`window[m]`/`addEventListener` 的替换**没有任何幂等标记**，`disable` 后再 `enable` 会在旧 wrapper 外面**再包一层**（wrapper 链累积，N 次后每次 XHR/fetch/timer 多 N 层）。
- **F12/F13**：`__mcp_tr` / `__mcp_al` 打在 wrapper 上，`stop` 后再 `start` 会被跳过，**不会**重复包装（但旧 wrapper 继续向已被 `delete` 的孤儿 `T`/`L` 对象累积垃圾，`new Error().stack` 的采样开销永久保留）。
以上为静态结论，未运行验证。

### B-5 F14 watch_global：唯一有救回余地的访问器补丁族

`K:1542`：
```js
var names=[…];names.forEach(function(n){try{var v=window[n];
  Object.defineProperty(window,n,{get:function(){return v},
    set:function(nv){try{L.hits.push({n:n,v:S(nv),st:…,ts:Date.now()});…}catch(e){}v=nv},configurable:true})}catch(e){}});
```
`configurable:true` 意味着这个访问器**可以被 `delete` / 重新 `defineProperty`**。原属性描述符没存，但若原本是普通数据属性，可按「先读 `window[n]` 拿当前值 → `delete window[n]` → 重新赋回该值」近似复原；若原本是访问器属性或 `configurable:false`（后者 `defineProperty` 本就会抛错并被 `catch(e){}` 吞掉）则无法完全复原。**当前 `stop` 分支并未这么做。**

### B-6 F15 Canvas 噪声：本仓库唯一一处真正的「备份 + 还原」范式

备份（`Core:3192`）：
```js
cnCode = cnCode + "if(!window.__MCP_CANVAS_ORIG__){window.__MCP_CANVAS_ORIG__={toDataURL:origToDataURL,toBlob:origToBlob,getImageData:origGetImageData};}"
```
还原（`Core:3227`，原文单行）：
```js
cnRemoveCode = "(function(){var o=window.__MCP_CANVAS_ORIG__;if(o){if(o.toDataURL)HTMLCanvasElement.prototype.toDataURL=o.toDataURL;if(o.toBlob)HTMLCanvasElement.prototype.toBlob=o.toBlob;if(o.getImageData)CanvasRenderingContext2D.prototype.getImageData=o.getImageData;delete window.__MCP_CANVAS_ORIG__;}else if(window.__MCP_CANVAS_NOISED__){delete HTMLCanvasElement.prototype.toDataURL;delete HTMLCanvasElement.prototype.toBlob;delete CanvasRenderingContext2D.prototype.getImageData;}delete window.__MCP_CANVAS_NOISED__;delete window.__MCP_CANVAS_NOISE_LVL__;return'Canvas noise removed'})()"
```
旁边的注释（`:3226`）把原则写得很清楚：
```
// 从备份恢复原生实现 (勿直接delete原型属性, 否则原生API连同补丁一起永久消失)
```
**⇒ 这条范式就是新卸载路径应当复制的模板。**

### B-7 F16 permission_spoof：靠「自有属性遮蔽」天然可逆

`Core:3327`–`3348` 用 `navigator.permissions.query=function(desc){…}` / `navigator.mediaDevices.enumerateDevices=function(){…}` 在**实例**上建自有属性遮蔽原型方法（原方法经 `origQuery` / `origEnum` 闭包转发）。`reset` 分支 `Core:3356`：
```js
psResetCode = "(function(){delete navigator.permissions.query;delete navigator.mediaDevices.enumerateDevices;return '权限伪装已移除, 刷新后恢复默认'})()"
```
`delete` 自有属性后，原型上的原生实现重新可见 ⇒ **功能上确实还原**（原函数对象身份未被破坏，因为压根没改原型）。但返回文案 `'刷新后恢复默认'` 与实现不符：这里**不需要**刷新。

---

## C. 现有「卸载/清空/还原」入口全盘点（区分「清数据」与「还原函数」）

搜索词：`卸载|还原|恢复原|uninstall|restore|removeHook|解除Hook|还原原始`、`__mcp_orig|__MCP_ORIG|mcp_unhook|unhook|__mcp_registry|__MCP_HOOKS__`，以及对 `Srv` 中工具名含 `hook|probe|trace|algo|gwatch|instrument|ipc` 的全部注册项逐条核对（该次检索命中 17 条，含 4 个 `browser_ipc_*` 与 2 个 `browser_kernel_ipc_*`）。

### C-1 只清数据、不还原函数（**这就是 crux**）

| 入口 | 动作 | 实际行为 | 证据 |
|---|---|---|---|
| `browser_reverse_hook_logs` action=clear | 清空日志 | **原地截断数组**（`v.length=0` / `v.results.length=0`），**不触碰任何被包装的函数** | `Rev:665`（自动模式）、`:678`（指定 key）、派发 `:640`；工具描述 `Srv:9885` 原文含 `"clear清空(原地截断, 不会让已安装的Hook失效)"` |
| `browser_kernel_reverse_probe` action=clear | 清数组 | `window.__MCP_PROBE__.xhr=[], …listeners=[]` | `K:1309` |
| `browser_kernel_reverse_trace` action=clear | 清数组 | `T.calls=[], T.errors=0` | `K:1374` |
| `browser_kernel_reverse_algo` action=clear | 清数组 | `L.calls=[], L.errors=0` | `K:1431` |
| `browser_kernel_reverse_watch_global` action=clear | 清数组 | `L.hits=[], L.errors=0` | `K:1567` |
| `browser_kernel_ipc_queue` action=clear | 清队列 | `window.__mcp_ipc_queue=[]`（纯数据，无函数替换） | `K:552` |
| `browser_reverse_instrument_script` action=remove/suppress | 内核断点层 | 属 CDP 元对象，非页面 JS 补丁；见 A-2 | `Rev:988` / `:971` |

**`clear` 系列代码里甚至专门写了注释解释为什么必须原地截断**（`Rev:661-662` 原文两行）：
```
// clear 用原地截断(length=0/results.length=0), 不用 window[k]=[] 重新赋值:
// Hook包装器安装时把日志数组捕获进闭包, 重新赋值会让已安装的Hook写进被丢弃的旧数组而静默停止记录
```
—— 这段注释本身就是「Hook 的闭包引用还在」的直接书证：项目清楚这些 wrapper 依然活着，`clear` 只处理数据面。

### C-2 真正还原原函数的入口（**只有 2 个，都不在 hook/instrument 家族**）

| 入口 | 是否真还原 | 证据 |
|---|---|---|
| `browser_canvas_noise` action=remove/disable | **是**，回写 `window.__MCP_CANVAS_ORIG__` 中的原函数 | `Core:3227` |
| `browser_permission_spoof` action=reset/remove | **是**（`delete` 自有属性，原型原生方法复位） | `Core:3356` |

### C-3 明确「不存在」的入口

- **`browser_reverse_instrument` 没有卸载入口**：派发分支（`Core:6366`，锚点 `否则 (方法名 == "browser_reverse_instrument")`）只读 `target`/`mode` 两个参数，非 `transparent`/`interpreter` 一律失败（`Core:6397` 原文 `"未知mode: " + insMode + " | 支持: transparent/interpreter"`）；该分支内 grep `clear|remove|stop|disable|卸载|还原` → **not found**。
- **不存在 `browser_reverse_unhook` / `unhook` / `restore` 类工具**：工具名逐条核对无任何含 uninstall/restore/unhook 的注册项；全局 grep `卸载|还原|恢复原|uninstall|restore|removeHook` 的命中里，与 Hook 有关的只有 `K:1380` 的 `"建议刷新页面彻底恢复原函数"` 文案、`Rev:998` 的 V8 插装断点卸载提示，以及 `_audit/append_report_95.py` 里已登记的缺口待办；**其余全部无关**（`browser_restore_gui` 恢复 GUI 布局、`browser_vip_unload_extension` 卸载扩展、`规则字段反转义` 字符串转义还原等）。
- **不存在全局 Hook 注册表**：grep `__mcp_orig|__MCP_ORIG|__mcp_registry|__MCP_HOOKS__` → **not found**（唯一命中是被搜索词误配的 `__mcp_hooked`）。

### C-4 项目自己已登记该缺口（旁证）

`_audit/append_report_95.py:102-104` 原文：
```
**由此新增一条待办（已记录，未做）**：插装/挂钩类工具（`browser_reverse_instrument`、
`browser_kernel_*` 的注入族）目前**没有卸载/还原**入口，只能靠重载页面清除。这是能力缺口，
也是"同一批测试互相污染"的源头。
```

### C-5 顺带发现的三处「文案 ≠ 实现」（会误导找卸载入口的人）

1. `Srv:9833` 描述 `browser_reverse_instrument` 为 `"mode=transparent仅替换prototype getter保留toString"`；但 `Core:6387` 的注入里**没有任何 `Object.defineProperty` getter**，是直接 `__obj[__method]=function(){…}` 换掉方法本身。
2. `Srv:9827` 描述 `browser_reverse_hook` 为 `"无侵入函数Hook(CDP/V8级)…不修改fn.toString()"`；但 `Core:6107`/`:6120` 明明白白是页面 JS 猴子补丁，并且**改了 toString**（`__wrapper.toString=function(){return __orig.toString()}`）。
3. 四个族的缺参提示让用户去传一个不存在的 action：`K:1273`（probe）、`:1333`（trace）、`:1397`（algo）、`:1527`（gwatch）原文均为 `"…| 查询状态请显式传 action:status"`，而各 dispatcher 末尾只接受 `enable/get/clear/disable`（`:1318`）或 `start/get/clear/stop`（`:1382`/`:1439`/`:1575`）——**`status` 分支 not found**。

---

## D. 逐族卸载可行性判定

| 族 | 判定 | 理由（引用见 B 节） |
|---|---|---|
| F1 instrument/transparent | **必须刷新页面**（当前代码下不可能） | `__orig` 仅在 IIFE 闭包内；`__mcp_instrument_results` 不含原函数。附带自递归缺陷（B-1） |
| F2 instrument/interpreter | **必须刷新页面** | 同上，`__orig` 闭包不可达 |
| F3 initiator | **必须刷新页面** | `_origOpen`/`_origFetch` 闭包不可达 |
| F4 preset（xhr/fetch/cookie/ws/crypto/debugger 六个分支） | **必须刷新页面** | 六个 `__orig*` 全为 IIFE 局部 `var` |
| F5 hook/function_call | **必须刷新页面** | `__orig` 闭包；`__mcp_hooked` 只是标记 |
| F6 hook/xhr_fetch | **必须刷新页面** | `__origOpen` 闭包 |
| F7 hook/websocket | **必须刷新页面** | `__os` 闭包 |
| F8 hook/eval_dynamic | **必须刷新页面** | `__oe`/`__oF` 闭包 |
| F9 hook/cookie_set | **必须刷新页面** | `__d`/`__s` 闭包，且是原型描述符整体覆盖 |
| F10 hook_multi | **必须刷新页面** | `__orig` 闭包，且无幂等标记，重复调用叠加包装 |
| F11 probe | **必须刷新页面** | 闭包 `f`；`L.orig` 空壳；`disable` 只 delete 数据对象，且 delete 后重 enable 会再加一层 |
| F12 trace | **必须刷新页面** | 闭包 `orig`；`__mcp_tr` 只防重复包装 |
| F13 algo | **必须刷新页面** | 闭包 `fn`；`__mcp_al` 只防重复包装 |
| F14 watch_global | **可能**（不改模板也不完美） | `configurable:true` 允许 `delete`；但原描述符未存 ⇒ 只能近似复原数据属性，原访问器属性无法复原 |
| F15 canvas_noise | **已经可以** | 已实现备份+还原（B-6），可直接作为参考实现 |
| F16 permission_spoof | **已经可以** | `delete` 自有属性即复位（B-7） |
| F17 cookie_sources | 不适用 | 不注入 JS |
| F18 IPC 队列 | 不适用 | 纯数据数组 |
| A-2 preload | **未找到卸载入口** | 只有 `Page.addScriptToEvaluateOnNewDocument`（`Rev:318`），无 `removeScript...` |
| A-2 add_binding | **未找到卸载入口** | 只有 `Runtime.addBinding`（`Rev:1493`），无 `removeBinding` |
| A-2 instrument_script | 可卸载（有 `remove`，本机可能失败） | `Rev:988` + `:998` 的错误文案 |

**唯一「不改注入模板」就能救回来的页面补丁族：F14（近似）、F15（已实现）、F16（已实现）。其余 F1–F13 全部属于「不刷新即不可能」。**

---

## E. 推荐的最小卸载设计（基于已读到的代码）

> 以下均为**设计建议，未经编译与运行验证**。验证由主 agent 单独进行。

### E-0 通用原则（从 F15 复制范式）

1. **安装时**：把原函数写到**外部可达**的位置，而不是只留在闭包里；
2. **卸载时**：先取回原函数回写宿主属性，再删全局数据对象；
3. **禁止**用 `delete obj.proto.method` 收尾（`Core:3226` 的注释已给出原因：原生实现会跟着一起永久消失）；
4. **幂等**：卸载必须能重复调用。

### E-1 推荐的统一登记点（一处改动覆盖 F1–F13）

在每个 wrapper 安装处，于 `obj[name]=wrapper` 之后加一行「原函数挂回 wrapper」，把现成的 `__mcp_hooked` / `__mcp_tr` / `__mcp_al` 标记扩成「标记 + 备份」二合一：

```js
__wrapper.__mcp_orig = __orig;        // 新增
__wrapper.__mcp_hooked = true;        // 已有
```

配套再补一个全局登记表（让卸载不必遍历 `window`——很多宿主是 `XMLHttpRequest.prototype` 这类不可枚举对象）：

```js
(window.__MCP_HOOKS__ = window.__MCP_HOOKS__ || []).push({o: __obj, k: __last, orig: __orig, tag: '<族名>'});
```

- F1（transparent）：宿主是 `Function.prototype` 等，光有路径字符串在卸载侧要再解析一次（可解析，但登记引用更稳）。
- F11（probe）：`K:1278` 里的 `orig:{}` 正好可复用为登记位（如 `L.orig['xhr.open']=f`），**字段已存在，不必改结构**。
- F4（preset）/F5–F9（hook 各 type）：`window.__mcp_*_log` 只是数组，建议另开 `window.__MCP_HOOKS__`，不要污染日志数组（`clear` 依赖它们保持数组形态，见 `Rev:665`）。

**这一步必须改注入模板**（每族一行）。在**不改模板**的前提下 F1–F13 无法卸载——不存在只靠新工具「从外部把原函数找回来」的纯服务端方案。

### E-2 卸载动作（新增统一入口，或升级现有动作）

建议新增 `browser_reverse_unhook`（或把 `browser_kernel_reverse_probe` 的 `disable`、`..._trace`/`..._algo`/`..._watch_global` 的 `stop` 从「只删数据」升级为「先还原再删数据」）。卸载 JS 草案：

```js
(function(){
  var out={restored:0,failed:0,deleted:0};
  var failedKeys=[],deletedKeys=[];
  // 1) 优先用登记表
  var reg=window.__MCP_HOOKS__||[];
  for(var i=reg.length-1;i>=0;i--){
    var e=reg[i];
    try{ if(e.o){ e.o[e.k]=e.orig; out.restored++; } }
    catch(x){ failedKeys[failedKeys.length]=e.k; }
  }
  reg.length=0;
  // 2) 兜底: 扫常见宿主上带 __mcp_orig 标记的 wrapper(无登记表时的降级路径); 只能覆盖可枚举到的宿主
  // 3) 删数据对象(注意: 本数组自身不要用 .push —— 真被包装的页面里 push 可能就是递归 wrapper)
  var KS=['__MCP_PROBE__','__MCP_TRACE__','__MCP_ALGO_LOG__','__MCP_GWATCH__',
          '__MCP_HOOK_LOG__','__MCP_WS_LOG__','__MCP_EVAL_LOG__','__MCP_COOKIE_LOG__',
          '__mcp_xhr_log','__mcp_fetch_log','__mcp_cookie_log','__mcp_ws_log','__mcp_crypto_log',
          '__mcp_initiator_log','__mcp_instrument_results','__mcp_interpreter_logs'];
  for(var j=0;j<KS.length;j++){ if(window[KS[j]]!==undefined){ delete window[KS[j]]; deletedKeys[deletedKeys.length]=KS[j]; } }
  out.failed=failedKeys.length; out.deleted=deletedKeys.length;
  return JSON.stringify(out);
})()
```

注意事项（静态阅读得出的约束）：
- `window.__MCP_HOOK_LOG__` 被 `browser_reverse_hook_logs` 依赖，卸载时删它是合理的（Hook 都没了），但要**同时**告诉用户 `action=clear` 仍然只是清数据。
- **F9（cookie_set）/F4（cookie 分支）是原型描述符被 `defineProperty` 整体覆盖**：还原必须用 `Object.defineProperty(Document.prototype,'cookie', 原描述符)`，而不是赋值。`__mcp_orig` 这种「存函数」的通用做法对它不够，需要存**描述符**。这是**不能套用统一 `__mcp_orig` 模板**的那一族。
- **F14**：需额外存 `Object.getOwnPropertyDescriptor(window,n)`，卸载时 `if(prev) Object.defineProperty(window,n,prev); else delete window[n];`。`configurable:true` 是安装时刻意设的，`delete` 一定成功。
- **F1 必须顺带修自递归缺陷**：wrapper 里不能再用 `__results.push(...)`，应在替换 `Array.prototype.push` **之前**先抓干净引用（`var __push=Array.prototype.push;`），改用 `__push.call(__results, entry)`。否则即使加了 `__mcp_orig`，只要 `push` 被包装，页面依然在第一次 `push` 时崩栈，**卸载工具自己都跑不起来**（卸载 JS 里任何 `.push(...)` 都会被自递归吞掉）。因此本报告对实现顺序的关键提醒是：**修自递归应优先于加卸载入口**，否则卸载入口在该状态下的页面里不可用。

### E-3 原生内建的「次优还原」（仅在无法改模板时的降级方案）

F1–F9 命中的宿主**基本都是内建对象**（`Function.prototype.apply/call`、`Array.prototype.push/pop`、`String.prototype.indexOf/charAt`、`XMLHttpRequest.prototype.open/send`、`window.fetch`、`WebSocket.prototype.send`、`window.eval/Function`、`setTimeout/setInterval`、`EventTarget.prototype.addEventListener`、`crypto.subtle.*`）。理论上可从**同源干净 realm**（如临时 `document.createElement('iframe')` 的 `contentWindow`）取回同名原生函数再回写，实现「功能等价还原」。

必须同时说明其局限，**不得当作正确还原**：
- 取回的**不是**被替换掉的那个函数对象，`fn.toString()` / 身份比较 / WeakMap 缓存等不保证一致；
- 页面代码若已把 wrapper 存进变量或事件表（闭包捕获），仍会继续调用 wrapper；
- 对**用户自定义函数**（F2、F5、F10 的常见目标）完全无效。

因此该方案只能作为「改模板前的临时止血」，不能替代 E-1。

### E-4 A-2 两处缺口的对应设计

- `browser_reverse_preload`：CDP `Page.addScriptToEvaluateOnNewDocument` 会返回 `identifier`。设计：安装时保存 `identifier`，卸载时调 `Page.removeScriptToEvaluateOnNewDocument {identifier}`。**本仓库当前既没保存 identifier 也没有该 CDP 调用**（grep → not found），需新增。
- `browser_reverse_add_binding`：对应 `Runtime.removeBinding`，同样需新增（grep `removeBinding` → not found）。

---

## F. 静态分析无法确定的事项（未知项）

1. **运行期到底是哪一次调用把页面打崩的**：我能证明 F1 的模板在「`Array.prototype.push` 被包装」时必然自递归（B-1），但无法从源码确定实测那次 `RangeError` 之前执行了哪些工具、以什么 `target` 组合执行。缺运行日志。
2. **`<anonymous>:1:544` 的列号映射**：注入脚本是单行压缩串，无法静态判断 544 列落在哪条语句上（只能确认 `__obj.<computed>` 的形态与之相符）。
3. **iframe / 子框架是否被同时污染**：注入走的是 `取安全主框架`（`Core:6170` 的 `hookFrame`、`:6400` 的 `insFrame`）或 `提交异步JS任务`，从源码看不出是否遍历全部 frame。若只作用于主框架，则子框架仍干净；反之更糟。**未确定**。
4. **`提交异步JS任务` / `CDP执行JS并等待` 两条通道的注入是否落在同一 V8 上下文**：`Srv:3413` 的方法注释原文为 `"通过CDP Runtime.evaluate执行JS并sync-wait取回结果, 绕过不稳定的CEF JS回调; CDP不可用时回退原生同步JS"`，回退目标见 `Srv:3366` 的 `原生执行JS并等待`。两条路径是否等价、副作用是否一致，静态看不出。
5. **F11 探针 `orig:{}` 是设计意图还是历史残留**：无法判断它是否曾被执行路径写入过。
6. **F13 的 CryptoJS 分支在实测页面上是否真的装上了**（依赖注入时刻页面是否已有 `window.CryptoJS`、`crypto.subtle`），因此该族实际污染面无法静态确定。
7. **`browser_inject persist=true` 的持久 V8 扩展是否可卸载**：本次只在 `Core:2906-2938` 读到「加入持久 V8 扩展」，**未展开**持久配置族的移除路径（是否已有 `browser_config_*` 类工具可清，未查证）。这是另一条**刷新也不会清**的注入面，建议单独排期。
8. **`browser_reverse_cdp_hook`（`Debugger.setBreakpointOnFunctionCall`）的卸载**：未在 `Rev` 该族内找到 `removeBreakpoint`；项目另有通用断点管理工具，**能否清除未确认**。
9. **是否存在 `src/` 之外的注入源**：已 grep `__mcp_|__MCP_` 于 `*.html`/`*.js`（含 `index.html`、`mcp_bridge.js`）→ **not found**；但未逐字节审查 `generated-cpp/` 下生成代码是否含额外脚本注入。
10. **并发修改导致的快照漂移**：`MCP_Server_Core.wsv` 在本次阅读期间被改了 4 次、`MCP_Server.wsv` 2 次（见 §0，Core 行号在本报告写完时已再次失效）。若主 agent 现在动手，**必须先 `Get-FileHash` 重算基准、并按锚点片段重新定位，同时确认没有别的 agent 正在同一批文件上实施「卸载入口」**，否则会直接冲突。

---

## G. 一页结论

- 注入面共登记 **18 个家族条目**（F1–F18）；其中 F17 经查**不注入任何 JS**、F18 是纯数据队列，故**实际会替换页面函数的只有 F1–F14 共 14 个**；A-2 另有 **7 行 CDP/内核级元安装**。
- 这 14 个里，**13 个（F1–F13）把原函数只留在了不可达的 IIFE 闭包里**，因此**在现有代码下无法在不刷新页面的情况下还原**；`disable`/`stop` 只是 `delete window.__X__`，是「删数据」而不是「还原函数」（`K:1315/1379/1436/1572`）。
- **本项目唯一已有的正确还原范式是 `browser_canvas_noise`**（备份 `Core:3192` + 还原 `:3227`），其次是 `browser_permission_spoof`（靠自有属性遮蔽，`:3356` 的 `delete` 即复位）。
- 修复路径的**最低成本改动是「模板加一行 + 一个统一卸载入口」**：安装时 `wrapper.__mcp_orig = orig` 并登记 `{o,k,orig}`，卸载时 `o[k]=orig` 再删数据对象。**这必须改注入模板**；不改模板则不存在纯服务端解法。
- **两个必须先处理的点**：(a) F1 的 `__results.push` 自递归（会连带让卸载脚本自身不可用，应先修）；(b) `Document.prototype.cookie`（F9 / F4-cookie）需要存**描述符**而非函数，不能套统一模板。
- 项目自己已在 `_audit/append_report_95.py:102-104` 把该缺口登记为未做待办；本次调研**未发现任何已有的、被遗漏的卸载入口**。
