# `browser_kernel_reverse_functions` 注入 JS 失败根因定位报告

- 审计性质: **只读缺陷定位**(假设 + 代码证据, 非"已验证/已修复")
- 未修改任何 `.wsv`; 未编译; 未调用任何 MCP 接口/HTTP/JSON-RPC; 未启动/重启 `AI-Fbowser-Mcp.exe`
- 产出物: 本报告 + `_audit/_revfunc_*.py|js`(只读抽取与离线复现脚本)
- 审计时刻源码状态: `src\MCP_Kernel.wsv` 共 1800 行, 关键行 1457 未变动; `src\MCP_Server.wsv` 在本次审计过程中被**并发修改**过(总行数 10855 → 10895, 相关行号 3415 → 3455), 故涉及 `MCP_Server.wsv` 的位置一律**以逐字文本锚定**并同时给出"审计当时行号"

---

## 0. 一句话根因

注入的那段 JS **在 `[...].forEach(...)` 之后漏了语句终结符, 且整段注入串是"无任何换行符"的单行**, 于是 ASI(自动分号插入)无法生效 —— `}})return out.slice(0,MAX)` 这一段在**解析期**就抛 `SyntaxError: Unexpected token 'return'`, 与页面、CSP、反调试、内核版本全部无关; 紧接着的 `}})['XMLHttpRequest',...]` 还埋着第二个必炸点(`[].forEach()` 返回 `undefined`, 却被当作对象继续取下标), 只修前一个仍会以 `TypeError` 失败。

**最强证据(原文行, `src\MCP_Kernel.wsv` 第 1457 行 注入代码字面量的尾部):**

```
...C.prototype[k])}catch(e){}})}catch(e){}}catch(e){}})return out.slice(0,MAX)})())
                                                          ^^
                          此处 `)` 之后直接跟 `return`, 中间无 `;` 也无换行
```

第二处:

```
...add(o+'.'+k,obj[k])}catch(e){}})}catch(e){}})['XMLHttpRequest','WebSocket',...
                                              ^^
                    `[].forEach(...)` 的 `)` 之后直接跟 `[`, 被解析成"对 forEach 返回值取下标"
```

**修复要点:** 在运行期注入串的 index 732(类名数组 `[` 之前)与 index 1239(`return` 之前)各插入一个 `;` 即可; 并建议把 8 处 `catch(e){}` 改为 `catch(e){SKIP++}` 如实上报跳过次数, 同时纠偏错误文案(现文案把根因推给 CSP, 属误导)。

---

## 1. 台账(真机)事实与本次定位的边界

`_audit\_tool_ledger.json` / `_tool_ledger.md`(09-13 02:11, round 14, 同一批次):

| 工具 | 结果 | 耗时 | note |
|---|---|---|---|
| `browser_kernel_reverse_probe` (action=enable) | pass | 0.03s | `动态探针已注入(五维API插桩): __ok ...` |
| `browser_kernel_reverse_algo` (action=start) | pass | 0.03s | `算法Hook已启动 ...` |
| **`browser_kernel_reverse_functions`** | **fail** | **0.02s** | `函数提取失败: {"error":"JS异常:Uncaught"} \| 页面可能因 CSP 拒绝脚本注入, 或已跨域跳转` |
| `browser_kernel_reverse_sources` | pass | 0.03s | `{"success":true,"max_len":20000,"scripts":"[]"}` |

关键推论(均为台账直接读出, 非推测):

1. 该次调用的 `args` 为 **`{}`**(既无 `filter` 也无 `max`)→ 走默认 `MAX=500`、`FIL=''` 分支, 不存在"用户传参把 JS 拼坏"的可能。
2. **0.02s 完成且返回"JS 异常"** → 不是超时、不是 CDP 无响应; 是 `Runtime.evaluate` 真的把异常报回来了(与 `_audit\_cold_matrix.json` 里另一种失败"CDP JS 执行无响应(已等待15秒)"是**两个不同故障模式**, 不要混为一谈)。
3. 同批同页面同一时刻, 三个近亲注入工具全部成功 → 排除"整页 CSP / 反调试 / 跨域 / CDP 通道坏了"这类全局原因。
4. 兄弟工具 `reverse_sources` 返回 `scripts:"[]"` → 该页面 `<script>` 数为 0, 与"枚举页面脚本导致超时/异常"的说法自相矛盾。

本次定位**没有**真机执行(禁令), 因此最终链条中"CDP 把该 SyntaxError 回报成 `exceptionDetails.text = "Uncaught"`"这一步属**强推断**(见 §5 第 1 条所需证据); 而"这段 JS 在当前内核族(V8)下必然抛 `SyntaxError`"这一步是**离线可复现的实测**(见 §3.0)。

---

## 2. ① 实现位置与注入 JS 全文

### 2.1 分派与实现位置

| 位置 | 内容(逐字) |
|---|---|
| `src\MCP_Server.wsv:9589` | `添加工具JSON ("browser_kernel_reverse_functions", "动态函数提取: 枚举window全局函数+常用对象链+核心类prototype方法, 输出路径/函数名/参数个数/源码toString。filter按路径关键词过滤, max上限(默认500)", 多属性Schema文本 (属性项JSON ("filter", "text", "路径关键词过滤(可选)") + "," + 属性项JSON ("max", "integer", "上限(默认500,最大1000)"), ""))` |
| `src\MCP_Kernel.wsv:132-135` | `否则 (方法名 == "browser_kernel_reverse_functions")` / `{` / `返回 (分派_函数提取 (命令ID, 参数JSON))` / `}` |
| `src\MCP_Kernel.wsv:1444` | `方法 分派_函数提取 <公开 静态 类型 = 文本型 @输出名 = "DispatchFunctionExtract" @强制输出 = 真>` |
| `src\MCP_Kernel.wsv:1457` | 注入 JS 的 火山 字符串字面量(见 2.2) |
| `src\MCP_Kernel.wsv:1461` | `子文本替换 (注入代码, "var FIL=''", "var FIL='" + MCP命令服务器.简单转义JS (过滤词) + "'", , , 假)` |
| `src\MCP_Kernel.wsv:1464` | `数据 = MCP命令服务器.CDP执行JS并等待 (注入代码, 15000, 真)` |
| `src\MCP_Kernel.wsv:1471` | `返回 (MCP_响应构建.命令失败 (命令ID, "函数提取失败: " + 数据 + " \| 页面可能因 CSP 拒绝脚本注入, 或已跨域跳转"))` |

上下游确认(决定"异常文本为何只有 `Uncaught`"):

- `src\MCP_Server.wsv:3401`(审计当时): `evalParams.加入文本成员 ("expression", JS代码)` —— 表达式**原样发送**, CDP 层没有加任何换行/包裹, 所以字面量里的"单行"性质一直保留到内核里(这是 ASI 失效的前提)。
- `src\MCP_Server.wsv:3442-3456`(审计当时): `exceptionJSON = yyjson取JSON文本 (cdpObj, "exceptionDetails")` → `excText = yyjson取文本 (excObj, "text")` → 非空即 `返回 ("{\"error\":\"JS异常:" + ... + "\"}")`。

### 2.2 `src\MCP_Kernel.wsv:1457` 的注入串(逐字, 火山 字面量形式)

> 注: 该行是**一行超长**源码(整行 1298 字符), 字面量内部**没有任何换行符、没有任何反斜杠转义**(已用脚本核对: `raw contains backslash: False`)。`" + 到文本 (最大数) + "` 是 火山 的字符串拼接, 运行期被替换为 `500`。

```text
        注入代码 = "JSON.stringify((function(){var out=[];var seen={};var MAX=" + 到文本 (最大数) + ";var FIL='' ;function add(p,f){try{if(typeof f!=='function')return;var src=f.toString();if(FIL&&p.indexOf(FIL)<0)return;var k=src.length+'|'+src.slice(0,40);if(seen[k])return;seen[k]=1;out.push({p:p,n:f.name||'',l:f.length,s:src.slice(0,1500)})}catch(e){}}try{Object.keys(window).forEach(function(k){try{if(typeof window[k]==='function')add('window.'+k,window[k])}catch(e){}})}catch(e){}['location','navigator','document','history','crypto','performance','localStorage','sessionStorage','console'].forEach(function(o){try{var obj=window[o];if(!obj)return;Object.keys(obj).forEach(function(k){try{if(typeof obj[k]==='function')add(o+'.'+k,obj[k])}catch(e){}})}catch(e){}})['XMLHttpRequest','WebSocket','Promise','Map','Set','Array','Object','String','Number','Date','RegExp','JSON','WebAssembly','URL','Blob','FileReader','FormData','Headers','Request','Response','AbortController','IntersectionObserver','MutationObserver','ResizeObserver'].forEach(function(c){try{var C=window[c];if(!C||typeof C!=='function')return;add('window.'+c,C);try{Object.getOwnPropertyNames(C.prototype).forEach(function(k){try{add(c+'.prototype.'+k,C.prototype[k])}catch(e){}})}catch(e){}}catch(e){}})return out.slice(0,MAX)})())"
```

### 2.3 运行期真正注入的真串(替换 `到文本 (最大数)` → `500`, 共 1267 字符, 逐字)

```
JSON.stringify((function(){var out=[];var seen={};var MAX=500;var FIL='' ;function add(p,f){try{if(typeof f!=='function')return;var src=f.toString();if(FIL&&p.indexOf(FIL)<0)return;var k=src.length+'|'+src.slice(0,40);if(seen[k])return;seen[k]=1;out.push({p:p,n:f.name||'',l:f.length,s:src.slice(0,1500)})}catch(e){}}try{Object.keys(window).forEach(function(k){try{if(typeof window[k]==='function')add('window.'+k,window[k])}catch(e){}})}catch(e){}['location','navigator','document','history','crypto','performance','localStorage','sessionStorage','console'].forEach(function(o){try{var obj=window[o];if(!obj)return;Object.keys(obj).forEach(function(k){try{if(typeof obj[k]==='function')add(o+'.'+k,obj[k])}catch(e){}})}catch(e){}})['XMLHttpRequest','WebSocket','Promise','Map','Set','Array','Object','String','Number','Date','RegExp','JSON','WebAssembly','URL','Blob','FileReader','FormData','Headers','Request','Response','AbortController','IntersectionObserver','MutationObserver','ResizeObserver'].forEach(function(c){try{var C=window[c];if(!C||typeof C!=='function')return;add('window.'+c,C);try{Object.getOwnPropertyNames(C.prototype).forEach(function(k){try{add(c+'.prototype.'+k,C.prototype[k])}catch(e){}})}catch(e){}}catch(e){}})return out.slice(0,MAX)})())
```

按语句切成 4 段看, 作者的**本意**是 4 条彼此独立的语句:

```
[S0] function add(p,f){...}                                   ← 函数声明
[S1] try{ Object.keys(window).forEach(cb1) }catch(e){}         ← 语句(以 } 结束, 合法)
[S2] ['location',...].forEach(cb2)                             ← 语句(本意, 但被下一段的 [ 吞掉)
[S3] ['XMLHttpRequest',...].forEach(cb3)                       ← 语句(本意, 但首字符 [ 上移成了 S2 的下标)
[S4] return out.slice(0,MAX)                                   ← 语句(前一条以 ) 结束, 必须靠 ; 或换行收尾)
```

实际写出来的文本是 `...cb2)  ['XMLHttpRequest'...cb3)  return ...` —— S2 的 `)` 与 S3 的 `[` 之间没有分隔符, S3 的 `)` 与 S4 的 `return` 之间也没有分隔符。

---

## 3. ② 逐条可疑点(原文 + 为何抛)

### 3.0 致命点 1(已离线实测复现): `)return` 无终结符 + 全串无换行 → ASI 失效 → `SyntaxError`

原文(运行期串 index 1237-1262, 逐字):

```
...Object.getOwnPropertyNames(C.prototype).forEach(function(k){try{add(c+'.prototype.'+k,C.prototype[k])}catch(e){}})}catch(e){}}catch(e){}})return out.slice(0,MAX)})())
```

判定链(V8 = CEF/Chromium 的内核, 离线即可判定, 不依赖真机):

1. `[...].forEach(cb3)` 是**表达式语句**, 以 `)` 结尾; 紧随其后的 `return` 既不能延续该表达式, 又不满足 ASI 触发条件(ASI 第一条要求"违规记号前面有行终结符"; 全串无任何换行), 也不满足"违规记号为 `}` 或 EOF" → **解析期直接 `SyntaxError: Unexpected token 'return'`**。
2. 为什么兄弟工具不炸: 它们相邻语句之间要么写了 `;`, 要么前一句以 `}` 结尾(`}` 能自行终结语句, 无需 ASI)。例如 `分派_动态探针` 的 `...var OX=XMLHttpRequest.prototype;['open','send'].forEach(...)`、`分派_调用追踪` 的 `...}}return'__ok wrapped='+...`(前一句是 `for{}`, 以 `}` 结束)—— 只有本工具跨在"表达式语句 + 无分隔符 + 无换行"这个唯一组合上, 这与"只有这一个工具失败"完全吻合。

实测(本报告脚本 `_audit\_revfunc_bisect.js`, 对 2.3 的真串直接喂 V8):

```
original parses: false
only after ")" : true      ← 只在某个 ")" 后插入一个换行(触发 ASI)即可通过解析
single-newline fixes after ")" at: [ 1239 ctx=")}catch(e){}}catch(e){}})return out.slice(0,MAX)})" ]
```

即: **在 `)` 与 `return` 之间插入一个换行(或一个 `;`)就能通过解析**, 位置唯一 —— 正是 `}})` 与 `return` 之间。

### 3.1 致命点 2(修掉 3.0 后立即暴露): `[].forEach()` 的返回值被当作对象取下标 → `TypeError`

原文(运行期串 index 719-740, 逐字):

```
...Object.keys(obj).forEach(function(k){try{if(typeof obj[k]==='function')add(o+'.'+k,obj[k])}catch(e){}})}catch(e){}})['XMLHttpRequest','WebSocket','Promise','Map','Set',...
```

判定:

1. `[...].forEach(cb2)` 的返回值是 `undefined`; 紧随其后的 `[` 在语法上是**计算成员访问**(且括号内是逗号表达式 `'XMLHttpRequest','WebSocket',...,'ResizeObserver'`, 逗号表达式取**最后一项**) —— 它**不是数组字面量语句**, 而是"对 `undefined` 取属性 `'ResizeObserver'"。
2. 于是运行时抛 `TypeError: Cannot read properties of undefined (reading 'ResizeObserver')`。
3. 该 `TypeError` 发生在**任何 try 之外**(回调此时根本还没被调用), 所以 8 处 `catch(e){}` 一个都救不了它。

实测(`_audit\_revfunc_repro.js`, 桩 `window`, 逐字运行 2.3 的真串及其变体):

```
RUN FAIL V1 原始(单行)                => SyntaxError: Unexpected token 'return'
RUN FAIL V2 只在 return 前插换行       => TypeError: Cannot read properties of undefined (reading 'ResizeObserver')
RUN FAIL V3 只在 return 前插分号       => TypeError: Cannot read properties of undefined (reading 'ResizeObserver')
RUN OK   V4 两处都插分号               | count=177 | sample=[{"p":"window.alphaFn","n":"alphaFn","l":2,...}]
```

→ **两处必须同时修**; 只修 `return` 那一处, 工具会从 `SyntaxError` 变成 `TypeError`, 依然是 100% 失败。

### 3.2 已被逐项 try 兜住的可疑点(不会造成本次失败, 但会静默吞项)

以下每一条都是"确实会抛", 但都在 `try{...}catch(e){}` 内部 —— 我用桩对象实测过它们确实被吞掉(`_audit\_revfunc_repro.js` 的 `count=177` 结果中包含这些场景):

| # | 可疑点 | JS 原文(逐字) | 为什么会抛 | 现状 |
|---|---|---|---|---|
| a | 在**原型对象**上读 getter 属性 | `try{add(c+'.prototype.'+k,C.prototype[k])}catch(e){}` | `Response.prototype.body` / `.ok` / `.url`… 这类 getter 带品牌检查, 在 `this=C.prototype`(非实例)上取值会抛 `TypeError: Illegal invocation` | 内层 try 已兜住(实测), 但**静默丢弃** |
| b | 枚举 window 属性时碰到抛异常的 getter | `try{if(typeof window[k]==='function')add('window.'+k,window[k])}catch(e){}` | 某些自有属性是抛异常的访问器(沙箱/受限文档) | 内层 try 已兜住 |
| c | 访问 `localStorage`/`sessionStorage` | `['location','navigator','document','history','crypto','performance','localStorage','sessionStorage','console'].forEach(function(o){try{var obj=window[o];...}catch(e){}})` | 禁 cookie/沙箱文档下读取 `window.localStorage` 抛 `SecurityError` | 外层 try 已兜住 |
| d | 跨域受限对象 | 同上(只做 `window[o]` 取值与 `Object.keys`, 不深入读跨域属性) | `window.parent`/`window.top` 跨域时**取值本身不抛**, 只有继续读其属性才抛; 本脚本未继续深入 | 不构成风险 |
| e | `f.toString()` / `f.name` / `f.length` 被页面 Hook | `try{if(typeof f!=='function')return;var src=f.toString();...n:f.name||'',l:f.length,s:src.slice(0,1500)...}catch(e){}` | Hook 返回非字符串会使 `src.slice` 抛 `TypeError` | `add` 的 try 已兜住 |
| f | `JSON.stringify` 遇循环引用 | 整串最外层 `JSON.stringify((function(){...})())` | 若页面把 `Function.prototype.name/length` 改成返回对象且该对象自引用, `out` 项内的 `n`/`l` 会带循环引用 → `Converting circular structure to JSON` | 本次**不是**它: 失败发生在解析期, 早于任何求值; 且正常路径下 `n/l/s/p` 都是原始值 |

### 3.3 逐条排除的"环境类"怀疑(每条都给反证)

| 怀疑 | 结论 | 反证(原文/台账) |
|---|---|---|
| 页面 CSP 拒绝注入 | **排除** | ① `Runtime.evaluate` 走 CDP, 不受页面 CSP 约束(DevTools 控制台在严格 CSP 站点上照样能求值); ② 同批 `reverse_probe`/`reverse_algo`/`reverse_sources` 三个同样经 `CDP执行JS并等待` 注入的工具全部 `__ok` / `success`; ③ 本次故障在**解析期**, 连一行页面代码都没执行 |
| 已开启反调试导致 `debugger` 断点/异常 | **排除** | 反调试通常表现为超时或断点暂停; 台账是 0.02s 立即返回 `SyntaxError` 类异常, 且兄弟工具无感 |
| 跨域跳转 | **排除** | 兄弟工具同批成功; 本故障与页面 URL 无关(缺陷在脚本自身文本里, 换任何页面都一样) |
| 内核偏旧, 用了新语法/新 API | **排除(逐字核对)** | 全串只用 ES5: `var`/`function`/`try-catch`/`forEach`/`Object.keys`/`Object.getOwnPropertyNames`/`JSON.stringify`/`String.prototype.slice,indexOf`; **没有**箭头函数、模板串、`let/const`、`Reflect`、`Proxy`、`Symbol`、可选链、`??`, 也没有任何 ES6+ 新 API |
| 页面重写了 `Object.keys`/`Array.prototype.forEach` | **排除** | ① 该页面 `<script>` 数为 0(`scripts:"[]"`); ② 重写 Hook 也影响不到**解析期**; ③ 解析期失败 → 与页面是否 Hook 内置方法无关 |
| `filter` 注入把脚本拼坏 | **排除(已核实无 bug)** | `子文本替换` 是**就地修改首参数**(项目内既有注释即为此: `src\MCP_Server_Core.wsv:2321` `// 保存原始值, 子文本替换会原地修改action`; `src\MCP_Server.wsv:4900` `// 转义 LIKE 通配符, ... (子文本替换就地修改首参数)`), 因此 `src\MCP_Kernel.wsv:1461` 不接收返回值是正确的; 且本次 `args={}`, 该分支根本没执行 |
| `max` 上限/截断造成异常 | **排除(但有"静默不完整"问题)** | `out.slice(0,MAX)` 不抛异常; 但它**静默截断**, 且被吞掉的失败项也不上报(见 §4.2) |

---

## 4. ③ 修复方案

> 全部改动集中在 `src\MCP_Kernel.wsv` 的方法 `分派_函数提取` 内(第 1457 行那一行字面量), 另可选改 `src\MCP_Server.wsv` 的异常文本提取与文案。**本次审计未做任何修改。**

### 4.1 P0(必须, 两处一起改): 补语句终结符

**修改文件/方法:** `src\MCP_Kernel.wsv` → `方法 分派_函数提取` → 第 1457 行的 `注入代码 = "..."` 字面量。
**位置(以运行期真串的字符下标计, 也适用于 .wsv 里同一段文本):** index 732(类名数组 `[` 之前)与 index 1239(`return` 之前)。

**替换 1(逐字, 前后对照):**

```
替换前:  ...add(o+'.'+k,obj[k])}catch(e){}})}catch(e){}})['XMLHttpRequest','WebSocket','Promise',
替换后:  ...add(o+'.'+k,obj[k])}catch(e){}})}catch(e){}});['XMLHttpRequest','WebSocket','Promise',
```

**替换 2(逐字, 前后对照):**

```
替换前:  ...C.prototype[k])}catch(e){}})}catch(e){}}catch(e){}})return out.slice(0,MAX)})())
替换后:  ...C.prototype[k])}catch(e){}})}catch(e){}}catch(e){}});return out.slice(0,MAX)})())
```

**为什么这样能避免异常:**

- 替换 2 让 S2/S3 那条表达式语句以 `;` 明确收尾, `return` 变成一条独立语句 → 消除 `SyntaxError: Unexpected token 'return'`(ASI 失效问题彻底不依赖"是否有换行")。
- 替换 1 让 `['XMLHttpRequest',...]` 由"对 `undefined` 取下标"回到"数组字面量开头的独立语句" → 消除 `TypeError: Cannot read properties of undefined`。
- 实测等价变换已通过: `_audit\_revfunc_runtime_fixed.js`(`fixed parses OK`, 桩环境下 `count=177` 正常产出数组)。若只做替换 2、不做替换 1, 会退化为 §3.1 的 `TypeError`, 仍然 100% 失败。

**加固建议(可选):** 该行其余语句也显式补 `;`(如 `var FIL='' ;` 的散落空格、`catch(e){}` 后紧跟 `[` 的第一处边界), 使整段注入串不再依赖任何 ASI 规则; 或改为 `;(function(){...})()` 风格的分段拼接, 便于后续维护时一眼看出语句边界。

### 4.2 P1(建议): 逐项兜底已有, 但要"如实上报跳过了多少项"

现状是**已经逐项 try**(8 个 `try{` / 8 个 `catch(e){}`, 全部为单点粒度, 不是整段一层), 这符合"一错不全废"的原则; 缺陷是**吞了不报**——调用方无法区分"页面上只有 3 个函数"和"枚举了 900 个、其中 897 个读取失败"。

**改动 1(逐字, 声明计数器):**

```
替换前:  var out=[];var seen={};var MAX=500;var FIL='' ;function add(p,f){
替换后:  var out=[];var seen={};var MAX=500;var FIL='';var SKIP=0;function add(p,f){
```

**改动 2(逐字, 把本行内全部 8 处 `catch(e){}` 改为 `catch(e){SKIP++}`):**

```
替换前:  }catch(e){}
替换后:  }catch(e){SKIP++}
```

**改动 3(逐字, 把上限/跳过数一并返回):**

```
替换前:  ...}});return out.slice(0,MAX)})())
替换后:  ...}});return{list:out.slice(0,MAX),total:out.length,skipped:SKIP,truncated:out.length>MAX}})())
```

**改动 4(可选, 配套的 火山 侧解析, 保持 `functions` 字段向后兼容):** 在 `src\MCP_Kernel.wsv` 方法 `分派_函数提取` 的响应组装处:

```
替换前:
        变量 包 <类型 = YYJSON对象类>
        包.创建自文本 ("{}")
        包.加入逻辑值成员 ("success", 真)
        包.加入整数成员 ("max", 最大数)
        包.加入文本成员 ("functions", 数据)
        返回 (MCP_响应构建.命令成功_原始JSON (命令ID, 包.到可读文本 (YYJSON格式化选项.压缩)))

替换后:
        变量 包 <类型 = YYJSON对象类>
        包.创建自文本 ("{}")
        包.加入逻辑值成员 ("success", 真)
        包.加入整数成员 ("max", 最大数)
        // 注入脚本现返回 {list,total,skipped,truncated}; functions 仍输出"函数数组"本身, 兼容既有调用方
        变量 提取结果 <类型 = YYJSON只读对象类>
        如果 (提取结果.创建自文本 (数据) && MCP命令服务器.yyjson取JSON文本 (提取结果, "list") != "")
        {
            包.加入文本成员 ("functions", MCP命令服务器.yyjson取JSON文本 (提取结果, "list"))
            包.加入整数成员 ("total", MCP命令服务器.yyjson取整数 (提取结果, "total"))
            包.加入整数成员 ("skipped", MCP命令服务器.yyjson取整数 (提取结果, "skipped"))
            包.加入逻辑值成员 ("truncated", MCP命令服务器.yyjson取逻辑 (提取结果, "truncated"))
        }
        否则
        {
            // 注入脚本被页面 Hook 改写等: 如实暴露原始文本, 不假装成功
            包.加入文本成员 ("functions", 数据)
            包.加入文本成员 ("functions_note", "注入脚本返回值非预期结构, 未能拆出 list/skipped")
        }
        返回 (MCP_响应构建.命令成功_原始JSON (命令ID, 包.到可读文本 (YYJSON格式化选项.压缩)))
```

说明: `MCP命令服务器.yyjson取整数 / yyjson取JSON文本 / yyjson取逻辑` 三个调用形式在项目内均有既有用例(`src\MCP_Kernel.wsv:1449`、`:1342`, `src\MCP_Server_System.wsv:124`), 未臆造 API。

**"异常时是否要如实上报跳过多少项"——我的判断: 要, 但必须如实说明计数口径。**
`catch(e){SKIP++}` 统计的是**读取/枚举失败的次数**(粒度 = 单个属性 or 单个对象链), 不等于"被丢弃的函数个数"(一处 `catch` 可能对应一次属性读取失败, 也可能对应整条对象链枚举失败)。因此字段名建议用 `skipped`(而不是 `skipped_functions`), 并在工具描述里写明口径; 同时保留 `success:true`(部分成功不应报成失败), 用 `skipped/truncated` 让调用方自行决定是否要缩小范围重试——这与本项目"不静默假成功、也不能一错全废"的原则一致。

### 4.3 P2(建议, 让"工具自身缺陷"自己暴露): 把异常文本取全 + 注入前语法自检

**(a) 异常文本取全。** 现在 `MCP_Server.wsv` 的 `CDP执行JS并等待` 只读 `exceptionDetails.text`; CDP 约定里运行时/语法异常该字段恒为 `"Uncaught"`, 真正的原因与类名在**嵌套的** `exceptionDetails.exception.description` / `.className` 里 —— 这正好解释了实测文案为什么是信息量为零的 `{"error":"JS异常:Uncaught"}`(末尾什么都没有)。并且现有兜底 `yyjson取文本 (excObj, "description")` 读的是 `exceptionDetails` **顶层**的 `description`, 该键在 CDP 里不存在, 等于兜底也拿不到东西。

```
替换前(审计当时 src\MCP_Server.wsv:3447-3455):
            变量 excText <类型 = 文本型>
            excText = yyjson取文本 (excObj, "text")
            如果 (excText == "")
            {
                excText = yyjson取文本 (excObj, "description")
            }
            如果 (excText != "")
            {
                返回 ("{\"error\":\"JS异常:" + MCP_响应构建.JSON转义文本 (excText) + "\"}")
            }

替换后:
            变量 excText <类型 = 文本型>
            // CDP 约定: exceptionDetails.text 恒为 "Uncaught"(不含真实原因),
            // 真因+类名在嵌套的 exceptionDetails.exception.{className,description} 里。
            // 只读 text 会得到信息量为零的 "JS异常:Uncaught"(实测 browser_kernel_reverse_functions 即如此)。
            变量 excInner <类型 = YYJSON只读对象类>
            excInner = MCP命令服务器.yyjson取对象成员_安全 (excObj, "exception")
            变量 excDesc <类型 = 文本型>
            excDesc = MCP命令服务器.yyjson取文本 (excInner, "description")
            变量 excClass <类型 = 文本型>
            excClass = MCP命令服务器.yyjson取文本 (excInner, "className")
            如果 (excDesc != "")
            {
                excText = excDesc
            }
            否则
            {
                excText = MCP命令服务器.yyjson取文本 (excObj, "text")
            }
            如果 (excClass != "" && 寻找文本 (excText, excClass, 0, 假) == -1)
            {
                excText = excClass + ": " + excText
            }
            如果 (excText != "")
            {
                返回 ("{\"error\":\"JS异常:" + MCP_响应构建.JSON转义文本 (excText) + "\"}")
            }
```

(方法名 `yyjson取对象成员_安全` 见 `src\MCP_Server.wsv:6730`, 项目内既有用例 `src\MCP_Server.wsv:3594/3596`; 未臆造。)

**(b) 注入前语法自检。** 本项目已有 `Runtime.compileScript` 的成熟用法(`src\MCP_Server_Reverse.wsv:1629`, 其工具描述就写着"语法错误会直接报在这里 —— 热补丁前先用它验证源码"); 建议 `分派_函数提取`(以及同族注入型工具)在 `CDP执行JS并等待` 之前, 先对拼装好的 `注入代码` 走一次 `Runtime.compileScript`:

- 编译失败 → 直接返回 `函数提取失败: 注入脚本自身语法错误(<真实报错>) | 与页面 CSP/反调试/跨域无关(本工具在任何页面都会失败) | 请上报脚本缺陷, 重试无意义`;
- 编译通过再 evaluate。

这一条能把"整类工具自身脚本写坏"的故障从"CSP 背锅 + 让用户反复重试"变成"指向真实原因 + 明确不要重试"。

---

## 5. ④ 文案纠偏

### 5.1 现文案是否有误导性?——**有, 且是实质性误导**

现文案(`src\MCP_Kernel.wsv:1471`, 逐字):

```
函数提取失败: {"error":"JS异常:Uncaught"} | 页面可能因 CSP 拒绝脚本注入, 或已跨域跳转
```

问题有 4 层:

1. **因果错置**: 真正的失败发生在 `Runtime.evaluate` 的**解析阶段**, 页面一行 JS 都没执行; 而 CSP 与跨域只可能影响"脚本能否被页面加载/能否读跨域属性", 与 CDP 求值无关(DevTools 控制台在严格 CSP 站点上仍可求值, 这是 CDP 求值不等同于页面注入脚本的常识)。
2. **与本批实测自相矛盾**: 同批 `reverse_probe`/`reverse_algo`/`reverse_sources` 三个同样走 `CDP执行JS并等待` 注入的工具全部成功; 且 `reverse_sources` 显示该页 `<script>` 数为 0 —— 用"CSP 拒绝脚本注入"解释一个"页面上连脚本都没有"的页面, 逻辑上不成立。
3. **引导了错误的排障动作**: 文案暗示"换个页面/确认页面就绪后重试", 但这是 100% 确定性失败(与页面无关), 重试与换页面只浪费时间。
4. **信息量为零**: `JS异常:Uncaught` 根本没给出原因(见 §4.3(a)), 调用方/AI 代理拿到这句话只能猜。

### 5.2 建议文案(替换/分支化, 要求能指向真实原因)

对 `src\MCP_Kernel.wsv:1471` 这一分支:

```
替换前:
            返回 (MCP_响应构建.命令失败 (命令ID, "函数提取失败: " + 数据 + " | 页面可能因 CSP 拒绝脚本注入, 或已跨域跳转"))

替换后(建议):
            变量 异常文本 <类型 = 文本型>
            异常文本 = 数据
            // 归类: 注入脚本自身错误 vs 真·页面/通道问题, 不许把锅甩给 CSP
            如果 (寻找文本 (异常文本, "SyntaxError", 0, 假) != -1)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "函数提取失败: " + 异常文本 + " | 归类: 本工具注入脚本自身语法错误, 与页面 CSP/反调试/跨域无关(同批 reverse_probe/algo/sources 均成功即为反证) | 该故障在任何页面都会复现, 重试/换页面无意义, 请上报脚本缺陷"))
            }
            如果 (寻找文本 (异常文本, "Uncaught", 0, 假) != -1 && 寻找文本 (异常文本, ":", 0, 假) == -1)
            {
                返回 (MCP_响应构建.命令失败 (命令ID, "函数提取失败: " + 异常文本 + " | 归类: 未取到异常原因文本(CDP 只回了 'Uncaught'; 真因在 exceptionDetails.exception.description, 需先修异常文本提取) | 在此之前不要把此失败归因于 CSP"))
            }
            返回 (MCP_响应构建.命令失败 (命令ID, "函数提取失败: " + 异常文本 + " | 归类: 页面内运行时异常(枚举过程中被页面对象/Hook 阻断) | 可先用 filter 缩小范围缩小影响面; 若 skipped 字段非 0 说明为部分成功"))
```

对超时/空串分支(`src\MCP_Kernel.wsv:1469`)的文案也建议纠偏: 现文案 `常见原因: 页面尚未就绪或脚本数量过大导致枚举超时` —— 本工具的枚举对象是 `window`/内置构造器, **与页面脚本数量无关**(且该页 `scripts:"[]"`), 应改为:

```
函数提取失败: CDP JS 执行无响应(已等待15秒) | 归类: CDP 通道无响应(非脚本内容问题; 本工具枚举 window/内置构造器, 与页面脚本数量无关) | 建议: 确认 CDP 监管者事件已注册(可用 browser_vip_enable_inspector enable=true 恢复)后重试
```

一句话原则: **错误文案必须区分"工具自身缺陷 / 页面内运行时异常 / CDP 通道无响应"三类, 并且不能把 CDP 求值失败归因于 CSP。**

---

## 6. ⑤ 我无法确定的点与所需证据

1. **"`exceptionDetails.text == "Uncaught"`"这一步未在真机验证**(本次禁止调用 MCP)。它是"`JS异常:Uncaught` 字面量 + CDP 约定 + 现有代码只读 `text` 且兜底键写错层级"三者推出的强假设。
   *所需证据:* 抓一次真实 `Runtime.evaluate` 的原始返回(例如让 `browser_reverse_evaluate` 求值一个必然语法错误的表达式 `var a = ;`, 看 `exceptionDetails` 原文是否含 `"text":"Uncaught"` 且真因在 `exception.exception.description`)。**注意: 这需要调用 MCP, 本次被禁止, 我未执行。**
2. **运行中的 `AI-Fbowser-Mcp.exe` 是否由本次审计的这份 `src` 构建**(台账 `mcp_status` 显示版本 3.1.0)。虽然旧快照 `_audit\_ghost_snapshot\MCP_Kernel.wsv.snapshot.txt:1444` 里**同一处缺陷逐字存在**(说明该缺陷不是最近引入的回归, 至少跨两个快照版本), 但严格来说仍需确认 exe 与 src 的对应关系。
   *所需证据:* 构建时间/版本号与 `src` 修订的对应记录, 或重新构建后的对照复测(本次禁止编译)。
3. **`filter`/`max` 传入时的行为未真机验证**。我只核实了 `子文本替换` 就地修改语义与默认分支的拼装正确性; `简单转义JS` 对含单引号/反斜杠的 filter 的最终落地文本未在浏览器里跑过。
4. **响应体积风险未量化**: 无 `filter` 时枚举上限 500 项 × 源码截断 1500 字符, 理论上单次结果可达数百 KB 的 JSON 字符串(再被 `包.加入文本成员` 二次转义)。我在代码里没有找到对该路径的显式体积上限(`CDP执行JS并等待` → `同步等待异步任务` 未见长度截断逻辑), 但**没有证据**表明它就是失败原因(本次失败是解析期异常)。若修好语法后出现新的失败模式, 建议优先查这里。
5. **`Object.getOwnPropertyNames(C.prototype)` 在更老的 CEF 内核上是否还有额外差异**未验证; 不过既然 §3.0/§3.1 两处缺陷已足以 100% 解释实测故障, 该点仅是余量排查项。

---

## 7. 复现/复核方法(全部离线, 只读)

```powershell
py -3 _audit\_revfunc_extract2.py     # 从 src\MCP_Kernel.wsv:1457 还原"运行期"注入真串 -> _audit/_revfunc_runtime.js
node    _audit\_revfunc_bisect.js     # 二分证明: 仅在 ")" 后插入单个换行即可通过 V8 解析, 位置唯一(1239)
node    _audit\_revfunc_repro.js      # 桩 window 对照 V1(原始)/V2(仅修return)/V3(仅插分号)/V4(两处都修)
node    _audit\_revfunc_fixpoints.js  # 打印两处修复点的精确字符下标, 生成 _audit/_revfunc_runtime_fixed.js 并验证解析通过
py -3   _audit\_revfunc_freshness.py   # 新鲜度校验: 重新抽取并逐字节比对本报告分析的串 == 当前源码
```

新鲜度校验结果(报告定稿时实测): 当前 `src\MCP_Kernel.wsv` 共 1801 行, 注入串仍在**第 1457 行**; 重新抽取的运行期真串与本次分析所用 `_audit\_revfunc_runtime.js` **逐字节相同**(len=1267, sha256 前 16 位 `f325c2cd79895881`), 且两处缺陷仍在(`}})return out.slice(0,MAX)` / `}})['XMLHttpRequest'` 均命中) —— 即**该缺陷在本次审计期间未被修改**。

产物清单(全部写在 `_audit\` 下, 未触碰 `src\`):

| 文件 | 用途 |
|---|---|
| `_audit\_revfunc_rootcause.md` | 本报告 |
| `_audit\_revfunc_extract.py`, `_revfunc_extract2.py`, `_revfunc_trace.py` | 逐字抽取注入串并做括号/字符串扫描 |
| `_audit\_revfunc_runtime.js` | 运行期注入真串(MAX=500), 逐字还原 |
| `_audit\_revfunc_runtime_fixed.js` | 仅加两处 `;` 的参考串(用于证明修复有效) |
| `_audit\_revfunc_bisect.js`, `_revfunc_toplevel.js`, `_revfunc_tail.js`, `_revfunc_lines.js`, `_revfunc_syntax_check.js` | V8 解析定位/边界二分 |
| `_audit\_revfunc_repro.js` | 桩 window 下的行为复现(含原型 getter、抛异常 getter、`localStorage` SecurityError 等兜底场景) |

---

## 8. 声明

- **未修改任何 `.wsv`**(包括 `MCP_Kernel.wsv` / `MCP_Server.wsv`), 未编译, 未调用任何 MCP 接口, 未启动/重启 `AI-Fbowser-Mcp.exe`。
- 本报告给出的是**根因假设 + 可离线复现的代码证据 + 修复方案**; 其中"这段 JS 在当前 V8/CEF 内核族下必然 `SyntaxError`"已用 V8 离线实测, "CDP 回报文本为 `Uncaught`" 与"运行中 exe 由该 src 构建"两点仍需 §6 所列真机证据。**不代表已修复、已验证。**
