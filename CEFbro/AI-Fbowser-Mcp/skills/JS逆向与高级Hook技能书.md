---
name: AI浏览器 JS逆向与高级Hook
description: JS逆向工程全链路能力 — 函数Hook/调用追踪/闭包探查/字符串解密/网络溯源/验证闭环
version: 2.6.1
trigger: JS逆向|逆向分析|hook函数|sign算法|加密参数|debugger|断点|调用栈|字符串解密|反混淆|网络溯源|AST
---

# AI浏览器 — JS 逆向与高级 Hook 技能书

> 基于 CDP 协议的深度运行时分析能力 | 参考：Ghostwire / Wirebrowser / jshookmcp / JSReverser-MCP  
> 配套：[AI浏览器MCP.md](./AI浏览器MCP.md) · [场景与Hook测试.md](./场景与Hook测试.md) · [使用技能书.md](./使用技能书.md)

---

## 一、JS 逆向能力全景

```
┌─────────────────────────────────────────────────────────┐
│                   AI浏览器 JS逆向流程                      │
│                                                         │
│  ① 信息收集       ② 函数Hook        ③ 调用追踪           │
│  browser_network   reverse_hook      browser_reverse_preset │
│  browser_event     debugger_flow     debugger_stack      │
│  browser_collect   browser_inject    debugger_inspect    │
│                                                         │
│  ④ 数据提取       ⑤ 插桩分析        ⑥ 验证闭环           │
│  reverse_strings   reverse_instrument reverse_verify     │
│  debugger_eval     browser_evaluate  mcp_result          │
│  network_body      extract           workflow_run        │
└─────────────────────────────────────────────────────────┘
```

---

## 二、工具矩阵

### 🎯 函数 Hook（无侵入式）

| 工具 | 能力 | 对标 |
|------|------|------|
| `browser_reverse_hook` | CDP 级函数断点，不修改 `fn.toString()` | Ghostwire `setBreakpointOnFunctionCall` |
| `browser_inject {type:"js", persist:true}` | V8 预注入持久 Hook | JSReverser `addScriptToEvaluateOnNewDocument` |
| `browser_intercept {action:"modify"}` | 资源替换（拦截/修改 JS 文件） | Wirebrowser resource override |

**使用姿势**：
```json
// 方式1: JS函数Hook（无侵入，不触发toString检测）
browser_reverse_hook {
  target: "function_name",      // 目标函数名(全局变量或window属性)
  type: "function_call",        // function_call | xhr_fetch | websocket
  capture_args: true,           // 捕获参数(默认true)
  capture_return: true,         // 捕获返回值(默认true)
  capture_stack: true           // 捕获调用栈(默认false)
}

// 方式2: XHR/fetch 拦截Hook
browser_reverse_hook {
  type: "xhr_fetch",
  target: "/api/",             // 匹配的URL模式(或url_pattern参数)
  capture_args: true
}

// 方式3: WebSocket 消息拦截
browser_reverse_hook {
  type: "websocket",
  target: "wss://..."
}
```

---

### 🔍 调用追踪

| 工具 | 能力 |
|------|------|
| `browser_debugger_auto` | 自动断点求值循环：断点命中→执行JS→resume→循环收集 |
| `browser_debugger_stack` | 当前断点的完整调用栈 |
| `browser_debugger_inspect` | 断点处批量求值（检查变量/对象/闭包） |
| `browser_reverse_hook {type:"function_call"}` | CDP函数Hook记录参数/返回值/调用栈 |

**使用姿势**：
```json
// 自动断点追踪（持续收集调用数据）
browser_debugger_auto {
  breakpoint: "encrypt\\.js",    // URL正则匹配目标脚本
  line: 0,
  expressions: ["arguments[0]", "arguments[1]", "this"],
  max_hits: 50,                  // 最大命中次数(默认5, 最大100)
  max_ms: 60000                  // 每次等待超时
}

// 函数级Hook追踪（CDP无侵入）
browser_reverse_hook {
  target: "encryptData",
  type: "function_call",
  capture_args: true,
  capture_return: true,
  capture_stack: true
}
```

---

### 🔐 字符串与数据提取

| 工具 | 能力 |
|------|------|
| `browser_reverse_strings` | 自动提取 JS 中的可疑字符串（加密/BASE64/HEX/密钥模式） |
| `browser_evaluate` | 执行 JS 表达式并返回结果 |
| `browser_network_body` | 获取网络请求的完整响应体 |
| `browser_debugger_evaluate` | 在断点帧内求值（访问闭包变量） |

**使用姿势**：
```json
// 提取页面中的可疑字符串(长字符串/Base64/HEX)
browser_reverse_strings {
  mode: "suspicious",            // suspicious | decrypt_array
  min_length: 20,
  max_results: 200
}

// 解密字符串数组（自动识别 var _0x = [...] 模式）
browser_reverse_strings {
  mode: "decrypt_array"
}
```

---

### 🌐 网络溯源

| 工具 | 能力 |
|------|------|
| `browser_reverse_initiator` | Hook XHR+fetch，捕获匹配URL的请求调用栈 |
| `browser_network detail_enable` | 详细网络日志（含响应头） |
| `browser_network_body` | 获取网络响应体 |
| `browser_reverse_network_intercept` | CDP网络拦截（可修改/重定向/阻塞请求） |

**使用姿势**：
```json
// 溯源：哪个JS函数发起了特定网络请求
browser_reverse_initiator {
  url_pattern: "/api/sign",     // 匹配的URL片段
  request_id: "12435.67890"     // 或使用网络请求ID(可选)
}
// 结果通过 browser_evaluate "JSON.stringify(window.__mcp_initiator_log)" 读取

// CDP级网络拦截
browser_reverse_network_intercept {
  action: "enable",
  url_pattern: "*/api/*"
}
```

---

### 🧪 去混淆辅助

| 工具 | 能力 |
|------|------|
| `browser_reverse_strings {mode:"decrypt_array"}` | 自动提取解密字符串数组 |
| `browser_reverse_instrument {mode:"transparent"}` | JSVMP解释器透明插桩（不破坏toString） |
| `browser_evaluate` | 在页面上下文中执行去混淆逻辑 |
| `browser_debugger_script_source` | 获取断点处脚本完整源码 |
| `browser_reverse_search` | 全局脚本关键词搜索(sign/encrypt/md5/aes) |

**使用姿势**：
```json
// 透明插桩分析VM解释器（保留fn.toString签名）
browser_reverse_instrument {
  mode: "transparent",
  target: ""                     // 空=默认目标(Function.apply/call, Array.push/pop等)
}

// 搜索加密相关代码
browser_reverse_search {
  query: "sign",                 // 搜索关键词
  script_url: "app.js"           // 限定脚本URL片段(可选)
}
```

---

### ✅ 验证闭环

| 步骤 | 工具 |
|------|------|
| ① 假设 | AI 阅读源码 → 提出签名算法假设 |
| ② 捕获 | `browser_reverse_hook` → 记录真实输入/输出 |
| ③ 重实现 | `browser_evaluate` → 在页面中执行重写算法 |
| ④ 验证 | `browser_reverse_verify` → 比对真实结果 vs 重写结果 |
| ⑤ 迭代 | AI 根据差异修正，循环至 diff 为空 |

**使用姿势**：
```json
// 验证重实现是否与原始函数一致
browser_reverse_verify {
  original: "window.sign",           // 原始函数
  reimplementation: "function sign(data){return md5(data+'_secret')}",
  test_inputs: ["test1", "test2"],    // 测试用例
  compare_mode: "strict"              // strict(===) | lenient(JSON序列化比对)
}
```

---

## 三、逆向工作流模板

### Workflow 1: POST 参数加密逆向

```json
{
  "name": "reverse_post_encrypt",
  "on_error": "continue",
  "steps": [
    {"tool": "browser_navigate", "args": {"url": "{{TARGET_URL}}"}},
    {"tool": "browser_wait", "args": {"what": "load_end", "max_ms": 10000}},
    {"tool": "browser_network", "args": {"action": "detail_enable"}},
    {"tool": "browser_reverse_initiator", "args": {"url_pattern": "{{API_PATTERN}}"}},
    {"tool": "browser_reverse_hook", "args": {"target": "{{SUSPECT_FUNC}}", "type": "function_call", "capture_args": true, "capture_return": true}},
    {"tool": "browser_debugger_auto", "args": {"breakpoint": "{{FILE_REGEX}}", "expressions": "[\"arguments\"]", "max_hits": 10}},
    {"tool": "browser_reverse_strings", "args": {"mode": "suspicious", "min_length": 16}}
  ]
}
```

### Workflow 2: 断点→Hook→验证闭环

```json
{
  "name": "reverse_verify_loop",
  "steps": [
    {"tool": "browser_debugger_flow", "args": {"url": "{{TARGET}}", "breakpoint": "{{FILE_REGEX}}", "line": 0, "expressions": "[\"arguments\",\"this\"]"}},
    {"tool": "browser_reverse_hook", "args": {"target": "{{FUNCTION}}", "type": "function_call", "capture_args": true, "capture_return": true}},
    {"tool": "browser_reverse_verify", "args": {"original": "{{ORIGINAL}}", "reimplementation": "{{REIMPL}}", "test_inputs": "{{INPUTS}}"}}
  ]
}
```

### Workflow 3: 字符串数组自动解密

```json
{
  "name": "reverse_deobf_string_array",
  "steps": [
    {"tool": "browser_navigate", "args": {"url": "{{TARGET}}"}},
    {"tool": "browser_wait", "args": {"what": "load_end", "max_ms": 15000}},
    {"tool": "browser_reverse_strings", "args": {"mode": "decrypt_array"}},
    {"tool": "browser_reverse_instrument", "args": {"mode": "transparent"}}
  ]
}
```

---

## 四、高级 Hook 脚本模板

### Hook 模板 1: XHR/fetch 拦截

```javascript
// browser_inject {type:"js", code:"...", persist:true}
(function() {
  var _fetch = window.fetch;
  window.fetch = function(url, opts) {
    var args = Array.from(arguments);
    console.log('[Hook] fetch', url, opts);
    return _fetch.apply(this, args).then(function(r) {
      r.clone().text().then(function(body) {
        console.log('[Hook] fetch response', url, body.substring(0, 500));
      });
      return r;
    });
  };
})();
```

### Hook 模板 2: Crypto API 拦截

```javascript
// browser_inject {type:"js", code:"...", persist:true}
(function() {
  var _digest = SubtleCrypto.prototype.digest;
  SubtleCrypto.prototype.digest = function(algo, data) {
    console.log('[Hook] crypto.digest', algo.name, new Uint8Array(data));
    return _digest.call(this, algo, data);
  };
})();
```

### Hook 模板 3: WebSocket 消息拦截

```javascript
// browser_inject {type:"js", code:"...", persist:true}
(function() {
  var _send = WebSocket.prototype.send;
  WebSocket.prototype.send = function(data) {
    console.log('[Hook] WS send', data);
    return _send.call(this, data);
  };
  var _onmsg = Object.getOwnPropertyDescriptor(WebSocket.prototype, 'onmessage');
  // ...
})();
```

---

## 五、与业界工具对标

| 能力 | AI浏览器 | Ghostwire | jshookmcp | Wirebrowser | JSReverser |
|------|---------|-----------|-----------|-------------|------------|
| CDP 断点 Hook | ✅ debugger_flow/set_breakpoint | ✅ setBreakpointOnFunctionCall | ✅ | ✅ | ✅ |
| 无侵入函数 Hook | ✅ reverse_hook(新) | ✅ | ✅ | ✅ | ✅ |
| 调用栈追踪 | ✅ debugger_auto/reverse_hook | ✅ auto-trace | ✅ | ✅ Origin Trace | ✅ |
| 字符串解密 | ✅ reverse_strings(新) | ✅ rotated arrays | ✅ LLM+AST | — | ✅ Babel |
| 网络溯源 | ✅ reverse_initiator(新) | — | ✅ | ✅ Network→Runtime | ✅ |
| 闭包探查 | ✅ debugger_inspect | ✅ CDP eval | ✅ | ✅ | ✅ |
| 验证闭环 | ✅ reverse_verify(新) | ✅ gw_verify | ✅ | — | ✅ risk_panel |
| 去混淆 | ✅ reverse_instrument(新) | ✅ runtime | ✅ Babel AST | — | ✅ webcrack |
| 反检测 | ✅ fingerprint/intercept | ✅ pipe transport | ✅ Camoufox | — | ✅ Patchright |
| MCP 集成 | ✅ 完整 MCP | ✅ MCP server | ✅ 402+ tools | — | ✅ MCP |

---

## 六、稳定性须知

1. **CDP 断点高频场景**：`browser_reverse_hook` 在加密函数高频调用时可能产生大量事件，默认限制 500 次/秒
2. **持久 Hook vs 页面刷新**：`browser_inject {persist:true}` 在页面刷新后自动重新注入
3. **调试器恢复**：断点操作后可能遗留 `Debugger.paused` 状态，使用 `browser_debugger_resume` 恢复
4. **大站点性能**：使用 `browser_debugger_auto` 自动追踪时建议设置 `max_hits` 限制（默认5, 最大100）
5. **内存管理**：长期Hook的数据通过 `window.__mcp_*_log` 存储，定期 `browser_evaluate "delete window.__mcp_*_log"` 清理

## 七、JSVMP 专项技能（MCP浏览器研究提取）

> 来源：[CSDN-JSVMP炼化大全](https://blog.csdn.net/qq_53444631/article/details/160980302) · [JSVMP技术解析](https://ghbbhc.github.io/2026/01/07/JS%E9%80%86%E5%90%91-JSVMP/) · [V2EX工具清单](https://www.v2ex.com/t/1205748)

### 7.1 JSVMP 识别特征

JSVMP（JavaScript Virtual Machine Protect）将原始代码转为自定义字节码，由自写解释器执行。识别特征：
- 存在 `switch-case` 或 `while + if-else` 链分发器（50+ opcode）
- 自定义 opcode 映射表（如 `_0x01d2c1` = LOAD, `_0x01d2c2` = ADD）
- 虚拟栈操作（push/pop 模拟寄存器）
- 超长字符串作为入参（混淆后的字节码）
- `X.$` 虚拟方法表（将 `call/apply/push/pop` 编号化）

### 7.5 JSVMP 四板斧分析法（hello_js_reverse_skill）

> 来源：[WhiteNightShadow/hello_js_reverse_skill](https://github.com/WhiteNightShadow/hello_js_reverse_skill) — v2.5.0 新增第四板斧

| 板斧 | 方法 | 原理 | 适用 |
|------|------|------|------|
| **① Hook** | 拦截目标函数调用,记录参数和返回值 | `hook_function(mode='intercept')` | 定位签名入口 |
| **② 插桩** | 在关键位置注入日志代码 | `instrumentation(action='install', mode=\"ast\")` | 追踪数据流 |
| **③ 日志** | 分析Console/网络日志交叉验证 | `hook_jsvmp_interpreter(mode=\"transparent\")` | 还原字节码语义 |
| **④ 源码级插桩(新)** | HTTP层改写VMP + hot_keys指纹学习 | `instrumentation(action='install', mode=\"ast\")` — esprima实现 | RS5/6, Akamai, webmssdk, obfuscator.io |

**关键技术**:
- `hook_jsvmp_interpreter(mode=\"transparent\")` — 仅替换prototype getter,不破坏签名计算
- `analyze_cookie_sources` — 融合HTTP Set-Cookie + JS document.cookie日志,一次性解答"这个Cookie到底是谁写的"
- `navigate` 返回 `redirect_chain/final_status` — 秒识反爬类型

### 7.6 反爬类型三档决策框架

| 类型 | 示例 | 路径 | 关键原则 |
|------|------|------|---------|
| **签名型** | RS/Akamai | A: 纯算法还原 | **不Hook请求本身** — Observer Effect会破坏签名 |
| **行为型** | TK/JY | B: 环境伪装 | 重点是环境一致性,不是算法 |
| **纯混淆** | obfuscator.io | C: AST反混淆 | 先还原代码结构,再分析逻辑 |

### 7.7 补环境核心变量清单

| 方法 | 原理 | 适用场景 | 工具 |
|------|------|---------|------|
| **补环境** | 在Node.js中模拟浏览器环境变量，直接执行JSVMP代码 | 环境检测较少、算法独立 | Proxy自吐脚本、`browser_inject` |
| **纯算还原** | 通过插桩日志推断算法逻辑，用Python/JS重写 | 算法逻辑清晰、魔改较少 | `browser_reverse_instrument`、`browser_debugger_auto` |
| **RPC远程调用** | 在真实浏览器中执行JSVMP函数，通过WebSocket/HTTP返回结果 | 反检测强、环境复杂 | JsRPC、Sekiro、`browser_reverse_hook` |

### 7.3 补环境核心变量清单

```javascript
// ① 必须手动置空的Node.js特有变量
"undefined" != typeof exports ? exports : void 0  →  void 0
"undefined" != typeof module ? module : void 0    →  void 0

// ② 浏览器环境变量
var document = { referrer: "https://target.com/" }
var location = { href: "...", protocol: "https:" }
var window = globalThis
var navigator = { userAgent: "...", platform: "..." }

// ③ 存储（需从浏览器提取真实值）
localStorage = { ... }   // 用 localStorage.getItem 代理
sessionStorage = { ... }

// ④ 关键检测点
- length 属性缺失 → 条件断点追查上一步操作
- protocol → 来自 location.protocol
- S/R/A 参数 → 分别在浏览器和Node中比对位数
```

### 7.4 Proxy 环境自吐脚本

```javascript
// 在浏览器中注入此脚本，自动记录所有环境变量访问
function getEnv(proxy_array) {
    for(let i=0; i<proxy_array.length; i++){
        handler = `{
            get: function(target, property, receiver) {
                console.log('GET', '${proxy_array[i]}', property, typeof target[property]);
                return target[property];
            },
            set: function(target, property, value, receiver){
                console.log('SET', '${proxy_array[i]}', property, typeof target[property]);
                return Reflect.set(...arguments);
            }
        }`;
        eval(`${proxy_array[i]} = new Proxy(${proxy_array[i]}, ${handler});`);
    }
}
getEnv(['window','document','location','navigator','history','screen']);
```

> 来源：https://www.cnblogs.com/a438842265/p/18332426

### 7.5 JSVMP 插桩分析流程

```
① 浏览器加载页面 → browser_navigate
② 注入Proxy自吐脚本 → browser_inject {type:"js", code:"...", persist:false}
③ 触发目标操作（点击/请求）
④ 查看Console日志 → browser_collect {action:"console_get"}
⑤ 对比浏览器 vs Node环境的环境变量差异
⑥ 补全缺失的环境 → 写入补环境代码
⑦ 扣下JSVMP代码 → browser_get_source 或 browser_debugger_script_source
⑧ 本地Node.js运行 → 验证signature长度一致
⑨ 汇总skills → 保存为可复用技能文件
```

### 7.6 实战案例

| 目标 | 算法 | 方法 | 参考 |
|------|------|------|------|
| 某程Token | — | JSVMP炼化 | [CSDN](https://blog.csdn.net/qq_53444631/article/details/160980302) |
| Testab | — | JSVMP炼化 | 同上 |
| 某东H5st 5.3 | — | JSVMP炼化 | 同上 |
| 头条_signature | byted_acrawler.sign() | 补环境+Proxy自吐 | [ghbbhc博客](https://ghbbhc.github.io/2026/01/07/JS%E9%80%86%E5%90%91-JSVMP/) |
| a_bogus | 大VMP+多小VMP嵌套 | Claude识别→Hook分析→21分钟完成 | [V2EX](https://www.v2ex.com/t/1205748) |

---

## 八、AI逆向工具生态系统（MCP浏览器整理）

> 来源：[awesome-ai-reverse](https://github.com/darbra/awesome-ai-reverse) · [V2EX工具清单](https://www.v2ex.com/t/1205748)

### JS逆向类

| 工具 | 能力 | GitHub |
|------|------|--------|
| **jshookmcp** | 402+工具/36域/CDP/网络/反检测 | `vmoranv/jshookmcp` |
| **js-reverse-mcp** | JS逆向全链路MCP | `NoOne-hub/JSReverser-MCP` |
| **reverse-skill** | AST混淆恢复/JSVMP/wasm/worker | `715494637/reverse-skill` |
| **camoufox-reverse** | Camoufox反检测浏览器+逆向 | `WhiteNightShadow/hello_js_reverse_skill` |
| **hello_js_reverse_skill** | JSVMP四板斧/反爬决策/双语言还原/Cookie归因 | `WhiteNightShadow/hello_js_reverse_skill` |
| **AI浏览器 MCP** | 243工具/CEF内核/CDP/VIP/指纹 | `AI-XiaoDao/ai-browser-mcp` |

### 二进制逆向类

| 工具 | 能力 |
|------|------|
| IDA Pro MCP | IDA反编译器MCP接入 |
| GhidraMCP | Ghidra MCP接入 |
| Binary Ninja MCP | Binary Ninja反编译器MCP |
| Frida MCP | Frida动态插桩MCP |

### Android安全类

| 工具 | 能力 |
|------|------|
| JADX-AI-MCP | APK反编译+AI分析 |
| ADB MCP | ADB调试MCP接入 |
| Android抓包MCP | 移动端流量捕获 |

### 浏览器自动化类

| 工具 | 能力 |
|------|------|
| DrissionPage MCP | Python浏览器自动化 |
| Camoufox MCP | 反检测浏览器 |
| Charles MCP | 抓包代理 |
| **AI浏览器 MCP** | CEF内核+243工具+MCP服务 |

---

## 九、相关文档

- [AI浏览器MCP.md](./AI浏览器MCP.md) — 243 个工具完整参考
- [场景与Hook测试.md](./场景与Hook测试.md) — 场景脚本与测试
- [客户使用手册.md](./客户使用手册.md) — 终端客户安装与使用
- [使用技能书.md](./使用技能书.md) — 技术/Agent 实操指南
- [awesome-ai-reverse](https://github.com/darbra/awesome-ai-reverse) — AI逆向工具大全（20+项目持续更新）

---

> 版本 2.6.1 · 在线研究日期：2026-06-24  
> 来源：Bing搜索 + CSDN + GitHub + V2EX + 技术博客  
> QQ: 212577526 | QQ群: 737680767 | 微信: XSMZAS1  
> GitHub: https://github.com/AI-XiaoDao/ai-browser-mcp
