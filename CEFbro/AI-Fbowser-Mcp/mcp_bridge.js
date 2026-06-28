#!/usr/bin/env node
/**
 * MCP Bridge: stdio <-> HTTP for AI Browser MCP Server
 *
 * 模式:
 *   (默认)     Cursor stdio 桥接 — 不写任何文件
 *   --check     连接自检
 *   --call      单次工具调用，结果 stdout: node mcp_bridge.js --call browser_get_url
 *   --feed      抖音精选列表分析（内存执行，不写报告文件）
 *
 * 配置: 环境变量 > mcp_connect.json > 127.0.0.1:9222
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const REQUEST_TIMEOUT_MS = parseInt(process.env.AI_BROWSER_MCP_TIMEOUT || '120000', 10);

// ---------- 配置 ----------

function readJsonFile(filePath) {
    try {
        if (fs.existsSync(filePath)) {
            return JSON.parse(fs.readFileSync(filePath, 'utf8'));
        }
    } catch (_) { /* ignore */ }
    return null;
}

function findConnectJson() {
    const candidates = [];
    if (process.env.AI_BROWSER_MCP_CONNECT) candidates.push(process.env.AI_BROWSER_MCP_CONNECT);
    candidates.push(path.join(__dirname, 'mcp_connect.json'));
    candidates.push(path.join(process.cwd(), 'mcp_connect.json'));
    for (const p of candidates) {
        const data = readJsonFile(p);
        if (data) return { data, path: p };
    }
    return { data: null, path: '' };
}

function parseHttpEndpoint(raw) {
    if (!raw || typeof raw !== 'string') return null;
    try {
        const u = new URL(raw);
        return {
            host: u.hostname || '127.0.0.1',
            port: parseInt(u.port || '9222', 10),
            path: u.pathname && u.pathname !== '/' ? u.pathname : '/mcp'
        };
    } catch (_) {
        return null;
    }
}

function parseWsEndpoint(raw) {
    if (!raw || typeof raw !== 'string') return null;
    try {
        const u = new URL(raw);
        return { host: u.hostname || '127.0.0.1', port: parseInt(u.port || '9222', 10) };
    } catch (_) {
        return null;
    }
}

function loadConfig() {
    const { data: connect } = findConnectJson();
    const postUrl = process.env.AI_BROWSER_MCP_HTTP_POST || (connect && connect.mcp_http_post) || '';
    let cfg = parseHttpEndpoint(postUrl);
    if (!cfg) {
        const wsUrl = process.env.AI_BROWSER_MCP_URL || (connect && connect.mcp_url) || '';
        const ws = parseWsEndpoint(wsUrl);
        const host = process.env.AI_BROWSER_MCP_HOST || (ws && ws.host) || (connect && connect.bind_address) || '127.0.0.1';
        const port = parseInt(
            process.env.AI_BROWSER_MCP_PORT || (ws && String(ws.port)) || (connect && String(connect.port)) || '9222',
            10
        );
        cfg = { host, port, path: '/mcp' };
    }
    const altPath = (connect && connect.mcp_http_post_alt) ? parseHttpEndpoint(connect.mcp_http_post_alt) : null;
    return {
        host: cfg.host,
        port: cfg.port,
        path: cfg.path || '/mcp',
        altPath: altPath ? altPath.path : '/',
        healthUrl: (connect && connect.health_url) || `http://${cfg.host}:${cfg.port}/health`,
        connectFile: connect ? 'loaded' : 'default'
    };
}

const CONFIG = loadConfig();

function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
}

let stdioQuiet = false;

function log(msg) {
    if (stdioQuiet) return;
    process.stderr.write('[MCP-Bridge] ' + msg + '\n');
}

// ---------- HTTP ----------

function errorResponse(id, code, message) {
    return { jsonrpc: '2.0', id: id != null ? id : null, error: { code, message } };
}

function postOnce(request, postPath, cfg, timeoutMs) {
    const payload = JSON.stringify(request);
    const ms = timeoutMs || REQUEST_TIMEOUT_MS;
    return new Promise((resolve) => {
        const req = http.request({
            hostname: cfg.host,
            port: cfg.port,
            path: postPath,
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) },
            timeout: ms
        }, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk.toString(); });
            res.on('end', () => resolve({ status: res.statusCode, data, path: postPath }));
        });
        req.on('error', (err) => resolve({ status: 0, error: err, path: postPath }));
        req.on('timeout', () => { req.destroy(); resolve({ status: 0, error: new Error('timeout'), path: postPath }); });
        req.write(payload);
        req.end();
    });
}

async function forward(request, cfg, timeoutMs) {
    const c = cfg || CONFIG;
    const paths = [c.path];
    if (c.altPath && paths.indexOf(c.altPath) === -1) paths.push(c.altPath);

    let lastErr = null;
    for (const postPath of paths) {
        const result = await postOnce(request, postPath, c, timeoutMs);
        if (result.error) { lastErr = result.error; continue; }
        if (result.status === 404) continue;
        if (result.status === 200 && result.data.length === 0) return null;
        if (result.status === 200 && result.data.length > 0) {
            try { return JSON.parse(result.data); }
            catch (_) {
                return errorResponse(request.id, -32000, 'MCP 服务器返回无效 JSON');
            }
        }
        return errorResponse(request.id, -32000, 'MCP 服务器 HTTP ' + result.status + ' @ ' + postPath);
    }
    const hint = `请先启动 AI浏览器.exe (${c.host}:${c.port}${c.path})`;
    return errorResponse(request.id, -32000, lastErr ? lastErr.message + ' — ' + hint : hint);
}

function httpGet(url, timeoutMs) {
    return new Promise((resolve) => {
        const req = http.get(url, { timeout: timeoutMs || 8000 }, (res) => {
            let data = '';
            res.on('data', (c) => { data += c; });
            res.on('end', () => resolve({ status: res.statusCode, data }));
        });
        req.on('error', (e) => resolve({ status: 0, error: e }));
        req.on('timeout', () => { req.destroy(); resolve({ status: 0, error: new Error('timeout') }); });
    });
}

async function getHealth(cfg) {
    const c = cfg || CONFIG;
    const res = await httpGet(c.healthUrl);
    if (res.error || res.status !== 200) {
        throw new Error(`无法连接 MCP (${c.host}:${c.port}) — ${res.error ? res.error.message : 'HTTP ' + res.status}`);
    }
    const j = JSON.parse(res.data);
    if (j.status !== 'ok') throw new Error('MCP health status=' + j.status);
    return j;
}

async function assertMcpOnline(cfg) {
    const h = await getHealth(cfg);
    if (!h.browsers) throw new Error('MCP 已连接但 browsers=0，请等待浏览器创建完成');
    return h;
}

function parsePayload(result) {
    const plain = (result && result.content && result.content[0] && result.content[0].text) || '';
    let json = null;
    try { json = JSON.parse(plain); } catch (_) { /* plain text */ }
    return { plain, json, isError: !!(result && result.isError), raw: result };
}

function unwrapData(payload) {
    const j = payload && payload.json;
    if (!j) return j;
    if (j.data != null) {
        if (typeof j.data === 'object') return j.data;
        if (typeof j.data === 'string') {
            try { return JSON.parse(j.data); } catch (_) { /* ignore */ }
        }
    }
    return j;
}

function parseEvaluateJson(payload) {
    const raw = (payload && payload.plain) || '';
    if (!raw) return null;
    try {
        const first = JSON.parse(raw);
        if (typeof first === 'string') return JSON.parse(first);
        return first;
    } catch (_) {
        try { return JSON.parse(raw); } catch (e) { return null; }
    }
}

function extractTaskId(payload) {
    const m = payload.plain.match(/task_[\w]+_\d+_\d+/);
    if (m) return m[0];
    const j = payload.json;
    if (j && j.task_id) return j.task_id;
    if (j && j.data && j.data.task_id) return j.data.task_id;
    return '';
}

async function callTool(name, args, id, timeoutMs) {
    const resp = await forward({
        jsonrpc: '2.0',
        id: id || name,
        method: 'tools/call',
        params: { name, arguments: args || {} }
    }, CONFIG, timeoutMs);
    if (resp.error) throw new Error(`[${name}] ${resp.error.message || 'tool error'}`);
    const payload = parsePayload(resp.result);
    if (payload.isError) {
        const j = payload.json;
        const looksLikeJson = payload.plain.startsWith('{') || payload.plain.startsWith('[');
        if (!(looksLikeJson && (!j || j.success !== false))) {
            throw new Error(`[${name}] ${payload.plain || (j && j.error) || 'tool error'}`);
        }
    } else if (payload.json && payload.json.success === false) {
        throw new Error(`[${name}] ${payload.plain || payload.json.error || 'failed'}`);
    }
    return payload;
}

async function pollMcpResult(taskId, maxMs) {
    const start = Date.now();
    while (Date.now() - start < maxMs) {
        const p = await callTool('mcp_result', { request_id: taskId }, 'poll_' + taskId);
        const j = p.json;
        if (j && j.success !== false && !j._async) return p;
        if (p.plain.includes('尚未完成') || p.plain.includes('waiting')) {
            await sleep(400);
            continue;
        }
        return p;
    }
    throw new Error('mcp_result 超时: ' + taskId);
}

async function callToolSync(name, args, id, waitMs) {
    const p = await callTool(name, args, id, waitMs ? waitMs + 5000 : undefined);
    const taskId = extractTaskId(p);
    if (taskId) return pollMcpResult(taskId, waitMs || 15000);
    return p;
}

async function pollUntil(checkFn, maxMs, intervalMs) {
    const start = Date.now();
    while (Date.now() - start < maxMs) {
        const v = await checkFn();
        if (v != null) return v;
        await sleep(intervalMs || 800);
    }
    return null;
}

// ---------- stdio 桥接 ----------

function writeLine(obj) {
    // MCP Stdio 传输规范: Content-Length: N\r\n\r\n{json}\n
    const json = JSON.stringify(obj);
    const len = Buffer.byteLength(json, 'utf8');
    process.stdout.write('Content-Length: ' + len + '\r\n\r\n' + json + '\n');
}

/** Cursor 精简工具集（v2.8: 40个核心工具 + 反检测/逆向高频） */
const CURSOR_TOOL_WHITELIST = new Set([
    // 导航/页面 (7)
    'browser_navigate', 'browser_get_url', 'browser_get_title', 'browser_back', 'browser_forward',
    'browser_reload', 'browser_stop',
    // 等待/状态 (3)
    'browser_wait', 'browser_is_loading', 'browser_status',
    // JS执行/DOM (7)
    'browser_execute_js', 'browser_evaluate', 'browser_get_source', 'browser_get_text',
    'browser_dom_query', 'browser_dom_click', 'browser_dom_set_value',
    'browser_dom_get_html', 'browser_console_eval',
    // 提取/爬虫 (3)
    'browser_extract', 'browser_scrape', 'browser_list',
    // 查找/缩放 (4)
    'browser_find', 'browser_stop_find', 'browser_set_zoom', 'browser_get_zoom',
    // 鼠标键盘 (4)
    'browser_mouse_click', 'browser_mouse_move', 'browser_mouse_wheel', 'browser_key_event',
    // 截图/打印 (2)
    'browser_screenshot', 'browser_print_to_pdf',
    // 网络/拦截/CDP (5)
    'browser_network', 'browser_collect', 'browser_cdp_call', 'browser_intercept', 'browser_inject',
    // DevTools (2)
    'browser_open_devtools', 'browser_close_devtools',
    // Cookie/代理 (6)
    'browser_get_cookies', 'browser_set_cookie', 'browser_delete_cookies',
    'browser_set_proxy', 'browser_clear_proxy',
    // 填表 (6)
    'browser_fill_set_value', 'browser_fill_click', 'browser_fill_focus', 'browser_fill_scroll',
    'browser_fill_exists', 'browser_fill_select',
    // 窗口/框架 (3)
    'browser_get_frames', 'browser_window_info', 'browser_view_source',
    // v2.8 反检测 + 逆向 + 调试器 (10)
    'browser_antidetect_presets', 'browser_reverse_setup',
    'browser_fingerprint', 'browser_fingerprint_ua',
    'browser_reverse_hook', 'browser_reverse_preset',
    'browser_reverse_search', 'browser_reverse_extract',
    'browser_reverse_detect_traps', 'browser_reverse_strings',
    'browser_debugger_enable', 'browser_debugger_pause', 'browser_debugger_resume',
    'browser_debugger_wait_paused', 'browser_debugger_inspect',
    // v2.8 网络导出 + 权限伪装 + 重试 + Canvas噪声 (4)
    'browser_network_export', 'browser_permission_spoof',
    'browser_retry', 'browser_canvas_noise',
    'browser_reverse_patch', 'browser_font_randomize',
    'browser_reverse_skip_pauses', 'browser_reverse_listeners',
    'browser_reverse_query_objects', 'browser_reverse_blackbox',
    'browser_reverse_async_stack', 'browser_reverse_cache_disable',
    'browser_reverse_compile_script', 'browser_reverse_breakpoints_active',
    'browser_reverse_search_script', 'browser_reverse_precise_coverage',
    'browser_reverse_bypass_csp', 'browser_reverse_await_promise',
    'browser_fingerprint_webgl_vendor', 'browser_reverse_cookie_cdp',
    'browser_reverse_network_conditions', 'browser_reverse_dom_resolve',
    'browser_reverse_emulate_focus',
    'browser_reverse_input_cdp', 'browser_reverse_trace',
    'browser_reverse_evaluate_silent',
    'browser_fingerprint_languages', 'browser_reverse_css_coverage',
    'browser_reverse_layer_tree',
    // 批量/工作流/系统 (5)
    'mcp_result', 'mcp_status', 'ping', 'batch',
    'workflow_list', 'workflow_get', 'workflow_run', 'workflow_stop'
]);

function isCursorLiteMode() {
    const v = (process.env.AI_BROWSER_MCP_CURSOR_MODE || '0').toLowerCase();
    return v === '1' || v === 'true' || v === 'on' || v === 'lite';
}

function isStdioBridgeMode() {
    const args = process.argv.slice(2);
    return !args.some((a) => ['--check', '--call', '--feed', '--help', '-h', '--serve'].includes(a));
}

/** MCP 服务端部分工具 schema 使用 type:"text"，Cursor 无法解析 */
function sanitizeJsonSchema(node) {
    if (node == null || typeof node !== 'object') return node;
    if (Array.isArray(node)) return node.map(sanitizeJsonSchema);
    const out = {};
    for (const [k, v] of Object.entries(node)) {
        if (k === 'type' && v === 'text') out[k] = 'string';
        else out[k] = sanitizeJsonSchema(v);
    }
    return out;
}

function normalizeToolSchema(schema) {
    const s = sanitizeJsonSchema(schema);
    if (!s || typeof s !== 'object' || Array.isArray(s)) return { type: 'object', properties: {} };
    if (!s.type) s.type = 'object';
    if (s.type === 'object' && !s.properties) s.properties = {};
    return s;
}

function sanitizeToolEntry(tool) {
    return {
        name: tool.name,
        description: typeof tool.description === 'string' ? tool.description.slice(0, 500) : '',
        inputSchema: normalizeToolSchema(tool.inputSchema)
    };
}

function filterToolsForClient(tools) {
    if (!Array.isArray(tools)) return [];
    let list = tools.map(sanitizeToolEntry);
    // v2.8.1: 移除 Cursor 工具白名单过滤, 动态显示全部工具 (268+)
    // 所有工具均已通过 MCP_Server 端 schema 验证, 无需桥接层精简
    if (isCursorLiteMode() && isStdioBridgeMode()) {
        log(`Cursor 全量模式: ${list.length}/${tools.length} 个工具 (已移除精简限制)`);
    }
    return list;
}

/** Cursor 支持的 MCP 协议版本；服务端为 2026-06-21，经桥接回写客户端请求的 2024-11-05 */
const CURSOR_PROTOCOL_VERSION = '2024-11-05';

function sanitizeMcpResponse(response, request) {
    if (!response || typeof response !== 'object') return response;
    const method = request && request.method;
    if (request && request.id !== undefined && response.id === undefined) {
        response.id = request.id;
    }
    if (response.result && typeof response.result === 'object') {
        delete response.result._req_id;
        if (method === 'initialize') {
            const requested = request.params && request.params.protocolVersion;
            response.result.protocolVersion = requested || CURSOR_PROTOCOL_VERSION;
        }
    }
    if (method === 'tools/list' && response.result && Array.isArray(response.result.tools)) {
        response.result.tools = filterToolsForClient(response.result.tools);
    }
    return response;
}

function shouldRespond(request) {
    if (!request || !request.method) return false;
    if (request.method.startsWith('notifications/')) return false;
    return request.id !== undefined;
}

async function healthCheck() {
    try {
        const j = await getHealth();
        return { ok: true, browsers: j.browsers, version: j.version, uptime_ms: j.uptime_ms };
    } catch (e) {
        return { ok: false, message: e.message };
    }
}

async function runCheck() {
    log(`配置: ${CONFIG.host}:${CONFIG.port} POST ${CONFIG.path} (${CONFIG.connectFile})`);
    const h = await healthCheck();
    if (!h.ok) {
        log('失败: ' + (h.message || '未知'));
        process.exit(1);
    }
    log(`成功 | 版本 ${h.version || '?'} | 浏览器 ${h.browsers != null ? h.browsers : '?'} 个`);
    process.exit(0);
}

async function runStdio() {
    stdioQuiet = process.env.AI_BROWSER_MCP_STDIO_LOG !== '1';

    process.stdin.setEncoding('utf8');
    let buffer = '';
    let pending = 0;
    let stdinEnded = false;

    function maybeExit() {
        if (stdinEnded && pending === 0) process.exit(0);
    }

    function processJsonLine(line) {
        let request;
        try { request = JSON.parse(line); }
        catch (_) {
            writeLine({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } });
            return;
        }
        pending++;
        forward(request).then((response) => {
            if (response !== null && shouldRespond(request)) {
                sanitizeMcpResponse(response, request);
                writeLine(response);
            }
            pending--;
            maybeExit();
        });
    }

    process.stdin.on('data', (chunk) => {
        buffer += chunk;
        while (true) {
            // MCP Stdio 传输规范: Content-Length: N\r\n\r\n{json}
            const headerEnd = buffer.indexOf('\r\n\r\n');
            if (headerEnd !== -1 && buffer.slice(0, headerEnd).startsWith('Content-Length:')) {
                // 解析 Content-Length 格式
                const header = buffer.slice(0, headerEnd);
                const match = header.match(/^Content-Length:\s*(\d+)/i);
                if (match) {
                    const contentLen = parseInt(match[1], 10);
                    const jsonStart = headerEnd + 4;
                    if (buffer.length >= jsonStart + contentLen) {
                        const jsonStr = buffer.slice(jsonStart, jsonStart + contentLen);
                        buffer = buffer.slice(jsonStart + contentLen);
                        // 跳过可选尾随换行符
                        if (buffer.startsWith('\n')) buffer = buffer.slice(1);
                        if (buffer.startsWith('\r\n')) buffer = buffer.slice(2);
                        if (!jsonStr.trim()) continue;
                        processJsonLine(jsonStr);
                        continue;
                    }
                }
                break; // Content-Length 头存在但消息体不完整, 等待更多数据
            }
            // 向后兼容: 纯换行分隔 JSON (旧客户端/旧服务端)
            const nl = buffer.indexOf('\n');
            if (nl === -1) break;
            const line = buffer.slice(0, nl).trim();
            buffer = buffer.slice(nl + 1);
            if (!line) continue;
            processJsonLine(line);
        }
    });
    process.stdin.on('end', () => { stdinEnded = true; maybeExit(); });
    process.stdin.on('error', () => process.exit(1));
}

// ---------- CLI: --call / --feed（不写磁盘）----------

function tryParseCallArgs(raw) {
    // 1. 标准 JSON
    try { return JSON.parse(raw); } catch (_) {}
    // 2. PowerShell/CMD 可能删除外层引号, 尝试修复裸 key/value
    //    {url:https://example.com/,key:val} → {"url":"https://example.com/","key":"val"}
    try {
        const fixed = raw.replace(/([{,]\s*)(\w+)(\s*:)/g, '$1"$2"$3')
            .replace(/:(\s*)([^",\[\]\{\}\s]+)/g, ':$1"$2"');
        return JSON.parse(fixed);
    } catch (_) {}
    // 3. 参数被空格拆分 (argv 多元素), 已由调用方 join 处理
    return null;
}

async function parseCallArgs(argv) {
    const tool = argv[0];
    let args = {};
    // --stdin: 从管道读取 JSON (echo '{...}' | node mcp_bridge.js --call browser_evaluate --stdin)
    if (argv.includes('--stdin')) {
        return new Promise((resolve, reject) => {
            let data = '';
            process.stdin.setEncoding('utf8');
            process.stdin.on('data', c => { data += c; });
            process.stdin.on('end', () => {
                try { args = JSON.parse(data.trim() || '{}'); }
                catch (e) { return reject(new Error('stdin 须为合法 JSON: ' + e.message)); }
                resolve({ tool, args });
            });
            process.stdin.on('error', e => reject(e));
        });
    }
    // --arg-file: 从文件读取 JSON 参数 (绕过 shell 编码/特殊字符问题)
    const fileIdx = argv.indexOf('--arg-file');
    if (fileIdx !== -1 && argv[fileIdx + 1]) {
        const filePath = argv[fileIdx + 1];
        try {
            args = JSON.parse(fs.readFileSync(filePath, 'utf8'));
            return { tool, args };
        } catch (e) {
            throw new Error('--arg-file 读取失败: ' + filePath + ' — ' + e.message);
        }
    }
    // 合并可能被 shell 拆分的参数
    const raw = argv.slice(1).join(' ');
    if (raw.trim()) {
        const parsed = tryParseCallArgs(raw.trim());
        if (!parsed) throw new Error('参数须为 JSON, 当前: ' + raw.slice(0, 200) + '\n  提示: 含中文/正则/箭头函数等特殊字符请用 --arg-file tmp.json');
        args = parsed;
    }
    return { tool, args };
}

async function runCall(argv) {
    const parsed = await parseCallArgs(argv);
    const { tool, args } = parsed;
    if (!tool) {
        console.error('用法: node mcp_bridge.js --call <tool> [json-args]');
        process.exit(1);
    }
    await assertMcpOnline();
    const p = await callToolSync(tool, args, 'cli_call', 120000);
    const out = p.plain || JSON.stringify(unwrapData(p) || p.json || p.raw, null, 2);
    process.stdout.write(out + (out.endsWith('\n') ? '' : '\n'));
}

function buildFeedJs(limit) {
    return `JSON.stringify((() => {
  const cards = [...document.querySelectorAll('[class*="VideoCard"], [class*="videoCard"]')];
  const seen = new Set();
  const items = [];
  for (const card of cards) {
    const img = card.querySelector('img');
    const titleEl = card.querySelector('[class*="tpc3FG9j"]');
    const authorEl = card.querySelector('[class*="vi8H_5ud"]');
    const lines = (card.innerText || '').trim().split(/\\n+/).map(s => s.trim()).filter(Boolean);
    const title = (img && img.alt) || (titleEl && titleEl.innerText.trim()) ||
      lines.find(l => l.length > 8 && !/^\\d{1,2}:\\d{2}$/.test(l) && !/^@/.test(l) && !/^[\\d.]+万?$/.test(l)) || '';
    const author = lines.find(l => l.startsWith('@')) || (authorEl ? '@' + authorEl.innerText.trim() : '');
    if (!title) continue;
    const key = title + '|' + author;
    if (seen.has(key)) continue;
    seen.add(key);
    items.push({
      title: title.split('\\n')[0],
      author,
      duration: lines.find(l => /^\\d{1,2}:\\d{2}$/.test(l)) || '',
      likes: lines.find(l => /^[\\d.]+万$/.test(l) || /^\\d+$/.test(l)) || '',
      date: (lines.find(l => l.includes('月') && l.includes('日')) || '').replace(/^\\s*·\\s*/, '')
    });
    if (items.length >= ${limit}) break;
  }
  return { url: location.href, title: document.title, path: location.pathname, cardCount: cards.length, items };
})())`;
}

function parseFeedArgs(argv) {
    const opts = { url: 'https://www.douyin.com/', limit: 30, waitSec: 12, scroll: false, skipNavigate: false, json: false };
    for (let i = 0; i < argv.length; i++) {
        const a = argv[i];
        if (a === '--skip-navigate') opts.skipNavigate = true;
        else if (a === '--scroll') opts.scroll = true;
        else if (a === '--json') opts.json = true;
        else if (a === '--limit') opts.limit = Math.max(1, parseInt(argv[++i], 10) || 30);
        else if (a === '--wait') opts.waitSec = Math.max(3, parseInt(argv[++i], 10) || 12);
        else if (!a.startsWith('-')) opts.url = a;
    }
    return opts;
}

function firstLine(text, max) {
    const line = String(text || '').split('\n')[0].trim();
    const n = max || 72;
    return line.length > n ? line.slice(0, n - 1) + '…' : line;
}

async function scrollFeedPage() {
    await callToolSync('browser_evaluate', {
        code: `JSON.stringify((() => {
          const el = [...document.querySelectorAll('*')].find(e => {
            const s = getComputedStyle(e);
            return (s.overflowY === 'auto' || s.overflowY === 'scroll') && e.scrollHeight > e.clientHeight + 200;
          });
          if (el) { el.scrollBy(0, el.clientHeight * 0.8); return { scrolled: true }; }
          window.scrollBy(0, 800);
          return { scrolled: true };
        })())`
    }, 'scroll', 15000);
    await sleep(1500);
}

async function runFeed(argv) {
    const opts = parseFeedArgs(argv);
    await assertMcpOnline();

    if (!opts.skipNavigate) {
        log('导航: ' + opts.url);
        await callToolSync('browser_navigate', { url: opts.url }, 'nav', 60000);
    }

    await pollUntil(async () => {
        const p = await callToolSync('browser_evaluate', {
            code: 'JSON.stringify(document.querySelectorAll("[class*=\\"VideoCard\\"], [class*=\\"videoCard\\"]").length)'
        }, 'count', 10000);
        const c = parseEvaluateJson(p);
        return typeof c === 'number' && c > 0 ? c : null;
    }, opts.waitSec * 1000);

    if (opts.scroll) await scrollFeedPage();

    let data = parseEvaluateJson(await callToolSync('browser_evaluate', { code: buildFeedJs(opts.limit) }, 'feed', 30000));
    if (!data || !(data.items || []).length) {
        await scrollFeedPage();
        data = parseEvaluateJson(await callToolSync('browser_evaluate', { code: buildFeedJs(opts.limit) }, 'feed2', 30000));
    }
    if (!data) throw new Error('页面数据解析失败');

    if (opts.json) {
        process.stdout.write(JSON.stringify(data, null, 2) + '\n');
        return;
    }

    const items = data.items || [];
    console.log('\n========== 抖音列表分析 ==========');
    console.log(`页面: ${data.title}`);
    console.log(`路径: ${data.path}  |  卡片: ${data.cardCount}  |  提取: ${items.length}`);
    items.forEach((item, i) => {
        const meta = [item.duration, item.likes ? item.likes + '赞' : '', item.date].filter(Boolean).join(' · ');
        console.log(`${String(i + 1).padStart(2)}. ${firstLine(item.title)}`);
        console.log(`    ${item.author}${meta ? ' | ' + meta : ''}`);
    });
}

function printCliHelp() {
    console.log(`AI浏览器 MCP 桥接

Cursor stdio (默认):
  node mcp_bridge.js

一次性调用（不写文件）:
  node mcp_bridge.js --check
  node mcp_bridge.js --call browser_get_url
  node mcp_bridge.js --call browser_navigate {url:https://www.douyin.com/}
  node mcp_bridge.js --feed [--limit 30] [--scroll] [--skip-navigate] [--json]
  # PowerShell: 在参数前加 --% 阻止解析, 或使用 url:value 简写格式
  # 复杂参数(含中文/正则/箭头函数): echo '{...}' | node mcp_bridge.js --call X --stdin
  #                             或  node mcp_bridge.js --call X --arg-file tmp.json
`);
}

// ---------- 入口 ----------

async function runCli() {
    const args = process.argv.slice(2);
    if (args.includes('--help') || args.includes('-h')) {
        printCliHelp();
        return;
    }
    if (args.includes('--check')) {
        await runCheck();
        return;
    }
    const callIdx = args.indexOf('--call');
    if (callIdx !== -1) {
        await runCall(args.slice(callIdx + 1));
        return;
    }
    const feedIdx = args.indexOf('--feed');
    if (feedIdx !== -1) {
        await runFeed(args.slice(feedIdx + 1));
        return;
    }
    await runStdio();
}

if (require.main === module) {
    runCli().catch((e) => {
        log('错误: ' + (e && e.message ? e.message : e));
        process.exit(1);
    });
}

module.exports = {
    CONFIG,
    HOST: CONFIG.host,
    PORT: CONFIG.port,
    loadConfig,
    sleep,
    getHealth,
    assertMcpOnline,
    callTool,
    callToolSync,
    pollMcpResult,
    pollUntil,
    parsePayload,
    unwrapData,
    parseEvaluateJson,
    forward
};
