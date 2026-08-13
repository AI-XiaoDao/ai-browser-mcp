/**
 * AI浏览器 MCP HTTP 客户端 — 复用 mcp_bridge，供测试编排 require
 */
const bridge = require('./mcp_bridge.js');

const {
    HOST, PORT, sleep, getHealth, assertMcpOnline, callTool, callToolSync, pollMcpResult,
    pollUntil, parsePayload, unwrapData, parseEvaluateJson
} = bridge;

async function sleepWithProgress(ms, label, opts = {}) {
    const interval = opts.intervalMs || 2000;
    const onTick = opts.onTick;
    const start = Date.now();
    let lastLog = 0;
    while (Date.now() - start < ms) {
        const left = ms - (Date.now() - start);
        const now = Date.now();
        if (now - lastLog >= interval || left <= interval) {
            const sec = Math.ceil(left / 1000);
            let extra = '';
            if (typeof onTick === 'function') {
                try { extra = onTick() || ''; } catch (_) { /* ignore */ }
            }
            process.stdout.write(`\r${label}… 剩余约 ${sec}s${extra ? ' | ' + extra : ''}   `);
            lastLog = now;
        }
        await sleep(Math.min(500, left));
    }
    process.stdout.write('\n');
}

async function getBrowserUrl() {
    const p = await callTool('browser_get_url', {});
    const d = unwrapData(p);
    if (d && d.url) return d.url;
    const plain = (p.plain || '').trim();
    if (plain && !plain.startsWith('{')) return plain.replace(/^已获取URL:\s*/i, '').trim();
    return '';
}

async function waitDebuggerPaused(maxMs = 45000) {
    return callToolSync('browser_debugger_wait_paused', { max_ms: maxMs }, 'dbg_wait', maxMs + 5000);
}

async function inspectAtBreakpoint(opts = {}) {
    const args = { expand: true, return_by_value: true };
    if (opts.call_frame_id) args.call_frame_id = opts.call_frame_id;
    if (opts.expressions) args.expressions = opts.expressions;
    else if (opts.expression) args.expression = opts.expression;
    if (opts.expand === false) args.expand = false;
    return callToolSync('browser_debugger_inspect', args, 'dbg_insp', 35000);
}

async function resumeDebugger() {
    return callToolSync('browser_debugger_resume', {}, 'dbg_resume', 15000);
}

async function lastDebuggerPaused() {
    return callTool('browser_debugger_last_paused', { parse: true }, 'dbg_last');
}

async function getDebuggerScriptSource(opts = {}) {
    const args = {
        call_frame_id: opts.call_frame_id,
        script_id: opts.script_id,
        line: opts.line,
        column: opts.column,
        context_lines: opts.context_lines || 3,
        include_source: opts.include_source !== false
    };
    Object.keys(args).forEach((k) => { if (args[k] === undefined) delete args[k]; });
    return callToolSync('browser_debugger_script_source', args, 'dbg_src', 25000);
}

async function runDebuggerFlow(opts = {}) {
    return callToolSync('browser_debugger_flow', {
        url: opts.url || 'https://example.com/',
        breakpoint: opts.breakpoint || 'example\\.com',
        expressions: opts.expressions || '["location.href","document.title","window.__mcp_dbg"]',
        expand: opts.expand !== false,
        return_by_value: opts.return_by_value !== false,
        max_ms: opts.max_ms || 45000,
        resume: opts.resume !== false
    }, 'dbg_flow', 90000);
}

function isJsNetworkEntry(entry) {
    const u = (entry.url || '').toLowerCase();
    const m = (entry.mime || '').toLowerCase();
    return m.includes('javascript') || m.includes('ecmascript') || /\.js(\?|$)/.test(u);
}

function uniqueJsUrls(logs) {
    const res = new Map();
    for (const x of logs || []) {
        if (!isJsNetworkEntry(x)) continue;
        const u = x.url || '';
        if (!u) continue;
        if (x.type === 'res') res.set(u, x);
        else if (!res.has(u)) res.set(u, x);
    }
    return [...res.entries()].map(([url, meta]) => ({ url, ...meta }));
}

async function unfreezeBrowser(opts = {}) {
    const host = opts.host || process.env.AI_BROWSER_MCP_HOST || HOST;
    const navigateHome = opts.navigateHome !== false;
    await getHealth();

    async function cdpSync(method, params = '{}', waitMs = 8000) {
        const id = 'unfreeze_' + method.replace(/\W/g, '_') + '_' + Date.now();
        try {
            return await callToolSync('browser_cdp', { method, params }, id, waitMs);
        } catch (_) {
            return null;
        }
    }

    console.log('[unfreeze] Debugger.resume ×3');
    for (let i = 0; i < 3; i++) {
        await cdpSync('Debugger.resume', '{}', 5000);
        await sleep(150);
    }
    try { await resumeDebugger(); } catch (_) {}

    console.log('[unfreeze] Debugger.disable');
    await cdpSync('Debugger.disable', '{}', 8000);
    await sleep(200);

    if (navigateHome) {
        const port = process.env.AI_BROWSER_MCP_PORT || String(PORT);
        const url = `http://${host}:${port}/`;
        console.log('[unfreeze] navigate →', url);
        try {
            await callTool('browser_navigate', { url });
            await sleep(800);
        } catch (_) {}
        try {
            await callTool('browser_restore_gui', {});
        } catch (_) {}
    }
    console.log('[unfreeze] 完成');
}

const PAGE_SCRIPT_SCAN = `JSON.stringify((() => {
  const scripts = [...document.scripts].map((s, i) => ({
    i, src: s.src || '(inline)', type: s.type || 'text/javascript',
    async: !!s.async, defer: !!s.defer, len: (s.textContent || '').length
  }));
  const perf = performance.getEntriesByType('resource')
    .filter(r => r.initiatorType === 'script' || /\\.js(\\?|$)/i.test(r.name || ''))
    .map(r => ({ url: r.name, type: r.initiatorType, duration_ms: Math.round(r.duration), transferSize: r.transferSize }));
  const globals = [];
  for (const k of ['webpackJsonp', '__NUXT__', 'Vue', 'React', 'angular', 'jQuery', '$']) {
    try { if (typeof globalThis[k] !== 'undefined') globals.push(k); } catch (_) {}
  }
  return {
    url: location.href, title: document.title,
    scriptTags: scripts.length,
    inlineScripts: scripts.filter(s => s.src === '(inline)').length,
    externalScripts: scripts.filter(s => s.src !== '(inline)').length,
    perfJsCount: perf.length, globals, scripts, perfJs: perf
  };
})())`;

module.exports = {
    HOST, PORT, sleep, sleepWithProgress, getHealth, assertMcpOnline, callTool, callToolSync, pollMcpResult,
    parsePayload, unwrapData, parseEvaluateJson, getBrowserUrl, pollUntil,
    isJsNetworkEntry, uniqueJsUrls, PAGE_SCRIPT_SCAN,
    waitDebuggerPaused, inspectAtBreakpoint, resumeDebugger, lastDebuggerPaused, runDebuggerFlow,
    getDebuggerScriptSource, unfreezeBrowser
};
