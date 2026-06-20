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

function log(msg) {
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
    process.stdout.write(JSON.stringify(obj) + '\n');
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
    log(`已连接 ${CONFIG.host}:${CONFIG.port} POST ${CONFIG.path}`);
    healthCheck().then((h) => {
        if (h.ok) log('服务就绪 | 浏览器: ' + h.browsers);
        else log('警告: ' + (h.message || '请先启动 AI浏览器.exe'));
    });

    process.stdin.setEncoding('utf8');
    let buffer = '';
    let pending = 0;
    let stdinEnded = false;

    function maybeExit() {
        if (stdinEnded && pending === 0) process.exit(0);
    }

    process.stdin.on('data', (chunk) => {
        buffer += chunk;
        while (true) {
            const nl = buffer.indexOf('\n');
            if (nl === -1) break;
            const line = buffer.slice(0, nl).trim();
            buffer = buffer.slice(nl + 1);
            if (!line) continue;
            let request;
            try { request = JSON.parse(line); }
            catch (_) {
                writeLine({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } });
                continue;
            }
            pending++;
            forward(request).then((response) => {
                if (response !== null) writeLine(response);
                pending--;
                maybeExit();
            });
        }
    });
    process.stdin.on('end', () => { stdinEnded = true; maybeExit(); });
    process.stdin.on('error', () => process.exit(1));
}

// ---------- CLI: --call / --feed（不写磁盘）----------

function parseCallArgs(argv) {
    const tool = argv[0];
    let args = {};
    if (argv[1]) {
        try { args = JSON.parse(argv[1]); }
        catch (e) { throw new Error('参数须为 JSON: ' + e.message); }
    }
    return { tool, args };
}

async function runCall(argv) {
    const { tool, args } = parseCallArgs(argv);
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
  node mcp_bridge.js --call browser_navigate '{"url":"https://www.douyin.com/"}'
  node mcp_bridge.js --feed [--limit 30] [--scroll] [--skip-navigate] [--json]
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
