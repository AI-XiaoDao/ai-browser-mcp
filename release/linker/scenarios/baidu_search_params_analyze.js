/**
 * 百度搜索参数分析 — 健壮版
 * 用法: node scenarios/baidu_search_params_analyze.js [keyword]
 * 特性: 自动重试 / selector 回退 / 条件等待替代死等 / Hook 时机前置
 */
const {
    callToolSync, unwrapData, sleep, parsePayload
} = require('../mcp_client.js');

const KEYWORD = process.argv[2] || '人工智能';
const RETRY_MAX = 3;
const RETRY_DELAY = 2000;

// ---------- 工具函数 ----------

function parseUrlParams(url) {
    try {
        const u = new URL(url);
        const params = {};
        u.searchParams.forEach((v, k) => { params[k] = v; });
        return { base: u.origin + u.pathname, params, raw: url };
    } catch (_) {
        return { base: url, params: {}, raw: url };
    }
}

function isSearchRelated(url) {
    const u = (url || '').toLowerCase();
    return /baidu\.com\/s[\?\/]/.test(u) || /\/s\?/.test(u)
        || /sugrec/.test(u) || /\/sug\?/.test(u) || /\/vsearch\?/.test(u)
        || /\/sf\/vsearch/.test(u)
        || (u.includes('baidu.com') && (u.includes('wd=') || u.includes('word=') || u.includes('query=')));
}

/** 带重试的 MCP 调用 — 遇到超时/错误自动重试 */
async function callWithRetry(tool, args, id, timeoutMs, maxRetry = RETRY_MAX) {
    let lastErr;
    for (let i = 0; i < maxRetry; i++) {
        try {
            const res = await callToolSync(tool, args, id + (i > 0 ? '_r' + i : ''), timeoutMs);
            const data = unwrapData(res);
            // browser_wait 超时会返回 success:false
            if (data && data.success === false && (data.error || '').includes('超时')) {
                lastErr = new Error(data.error || 'wait timeout');
                if (i < maxRetry - 1) { console.log(`  [重试 ${i + 1}/${maxRetry - 1}] ${tool}: ${lastErr.message}`); await sleep(RETRY_DELAY); }
                continue;
            }
            return res;
        } catch (e) {
            lastErr = e;
            if (i < maxRetry - 1) { console.log(`  [重试 ${i + 1}/${maxRetry - 1}] ${tool}: ${e.message}`); await sleep(RETRY_DELAY); }
        }
    }
    throw lastErr || new Error(`${tool} 重试${maxRetry}次仍失败`);
}

/** 尝试多个 selector, 返回第一个成功的 */
async function trySelectors(selectors) {
    for (const sel of selectors) {
        try {
            const res = await callToolSync('browser_fill_exists', { selector: sel }, 'exist_' + sel.slice(0, 10), 5000);
            const d = unwrapData(res);
            if (d && d.exists) return sel;
        } catch (_) { /* next */ }
    }
    return null;
}

// ---------- 主流程 ----------

async function main() {
    console.log(`\n=== 百度搜索参数分析 (健壮版) ===`);
    console.log(`关键词: ${KEYWORD}\n`);

    // ====== 第1步: 预备网络捕获 + 注入 Hook ======
    // 先打开百度首页并启用监控 (Hook 在导航前注入, persist=true 确保搜索结果页也生效)
    console.log('[1/5] 打开百度 + 启用网络监控...');
    await callWithRetry('browser_navigate', { url: 'https://www.baidu.com/' }, 'nav', 45000);
    await sleep(2000);

    // 启用完整网络日志 (在导航搜索结果前开启)
    await callWithRetry('browser_collect', { action: 'reverse_prepare', clear: true }, 'prep', 10000);
    console.log('  网络监控已启用');

    // 注入 XHR/fetch Hook (持久模式, 页面刷新/导航后自动生效)
    const hookCode = `(function(){
  if(window.__MCP_BAIDU_HOOK__) return;
  window.__MCP_BAIDU_HOOK__=true; window.__MCP_REQ_LOG__=[];
  function logReq(t,u,m,b){
    try{window.__MCP_REQ_LOG__.push({type:t,url:u,method:m||'GET',body:typeof b==='string'?b:(b?JSON.stringify(b):''),ts:Date.now()});if(window.__MCP_REQ_LOG__.length>200)window.__MCP_REQ_LOG__.shift()}catch(e){}
  }
  var oO=XMLHttpRequest.prototype.open, oS=XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open=function(m,u){this.__mcp_m=m;this.__mcp_u=u;return oO.apply(this,arguments)};
  XMLHttpRequest.prototype.send=function(b){if(this.__mcp_u&&/baidu\\.com/i.test(this.__mcp_u))logReq('xhr',this.__mcp_u,this.__mcp_m,b);return oS.apply(this,arguments)};
  var oF=window.fetch;
  window.fetch=function(i,init){var u=typeof i==='string'?i:(i&&i.url)||'',m=(init&&init.method)||'GET',b=init&&init.body;if(/baidu\\.com/i.test(u))logReq('fetch',u,m,b);return oF.apply(this,arguments)};
})();`;

    await callWithRetry('browser_inject', {
        type: 'js', code: hookCode, persist: true, inject_id: 'baidu_search_hook'
    }, 'inject', 10000);

    // ====== 第2步: 找到输入框并填入关键词 ======
    console.log('[2/5] 定位搜索框并输入关键词...');
    const inputSel = await trySelectors(['#kw', 'input[name="wd"]', '#word']);
    if (!inputSel) throw new Error('找不到百度搜索输入框 (尝试了 #kw / input[name=wd] / #word)');
    console.log(`  搜索框: ${inputSel}`);
    await callWithRetry('browser_fill_set_value', { selector: inputSel, value: KEYWORD }, 'fill', 8000);

    // ====== 第3步: 点击搜索按钮 ======
    console.log('[3/5] 点击搜索按钮...');
    const btnSel = await trySelectors(['#su', 'input[type="submit"][value="百度一下"]', '#searchBtn']);
    if (!btnSel) throw new Error('找不到百度搜索按钮 (尝试了 #su / input[value=百度一下])');
    console.log(`  搜索按钮: ${btnSel}`);
    await callWithRetry('browser_fill_click', { selector: btnSel }, 'click', 8000);

    // 等待搜索结果页加载 (条件轮询替代死等)
    console.log('  等待搜索结果...');
    await callWithRetry('browser_wait', { what: 'selector', value: '#content_left, #results', max_ms: 20000 }, 'wait_r', 25000);
    await sleep(1500);  // 给 XHR 埋点请求留出发送时间

    // ====== 第4步: 抓取数据 ======
    console.log('[4/5] 抓取网络数据...');
    const urlRes = await callWithRetry('browser_get_url', {}, 'url', 5000);
    const pageUrl = unwrapData(urlRes)?.url || (urlRes.plain || '').replace(/^已获取URL:\s*/i, '').trim();
    console.log('\n--- 当前页面 URL ---');
    console.log(pageUrl);
    const mainParams = parseUrlParams(pageUrl);
    console.log('\n--- 主搜索 URL 参数 (GET) ---');
    for (const [k, v] of Object.entries(mainParams.params)) {
        console.log(`  ${k} = ${v.length > 120 ? v.slice(0, 120) + '…' : v}`);
    }

    // 网络日志
    const netRes = await callWithRetry('browser_network', { action: 'list', limit: 500 }, 'net', 12000);
    const netData = unwrapData(netRes);
    const logs = netData?.network_logs || netData?.logs || [];
    const searchReqs = logs.filter(e => e.type === 'req' && isSearchRelated(e));
    console.log(`\n--- 搜索相关网络请求 (${searchReqs.length} 条) ---`);
    const seen = new Set();
    for (const e of searchReqs) {
        if (seen.has(e.url)) continue;
        seen.add(e.url);
        const parsed = parseUrlParams(e.url);
        console.log(`\n[${e.method || 'GET'}] ${parsed.base}`);
        for (const [k, v] of Object.entries(parsed.params)) {
            console.log(`    ${k} = ${v.length > 100 ? v.slice(0, 100) + '…' : v}`);
        }
    }

    // Hook 捕获的 XHR/fetch (含 POST body)
    const hookRes = await callWithRetry('browser_evaluate', {
        code: 'JSON.stringify(window.__MCP_REQ_LOG__||[])'
    }, 'hook', 10000);
    let hookLogs = [];
    try {
        const raw = unwrapData(hookRes)?.result ?? hookRes.plain ?? '';
        hookLogs = JSON.parse(typeof raw === 'string' ? raw : JSON.stringify(raw));
    } catch (_) { hookLogs = []; }
    const hookSearch = (hookLogs || []).filter(r => isSearchRelated(r) || /baidu\.com/i.test(r.url || ''));
    if (hookSearch.length) {
        console.log(`\n--- Hook 捕获的请求 (${hookSearch.length} 条，含 POST body) ---`);
        for (const r of hookSearch) {
            console.log(`\n[${r.type}/${r.method}] ${r.url}`);
            if (r.body) console.log(`    body: ${r.body.slice(0, 300)}${r.body.length > 300 ? '…' : ''}`);
        }
    }

    // ====== 第5步: 摘要 ======
    console.log('\n=== 参数说明摘要 ===');
    const wd = mainParams.params.wd || mainParams.params.word || KEYWORD;
    console.log(`wd/word  — 搜索关键词: "${decodeURIComponent(wd)}"`);
    if (mainParams.params.ie) console.log(`ie       — 输入编码: ${mainParams.params.ie}`);
    if (mainParams.params.f) console.log(`f        — 搜索类型/来源标识: ${mainParams.params.f}`);
    if (mainParams.params.rsv_bp) console.log(`rsv_bp   — 页面/行为追踪: ${mainParams.params.rsv_bp}`);
    if (mainParams.params.rsv_idx) console.log(`rsv_idx  — 结果页索引标识: ${mainParams.params.rsv_idx}`);
    if (mainParams.params.tn) console.log(`tn       — 入口来源: ${mainParams.params.tn}`);
    if (mainParams.params.oq) console.log(`oq       — 原始查询词: ${decodeURIComponent(mainParams.params.oq)}`);
    if (mainParams.params.rsv_pq) console.log(`rsv_pq   — 前次查询追踪: ${mainParams.params.rsv_pq}`);
    if (mainParams.params.rsv_t) console.log(`rsv_t    — 时间戳类追踪: ${mainParams.params.rsv_t}`);
    console.log('\n完成。\n');
}

main().catch((e) => {
    console.error('分析失败:', e.message || e);
    process.exit(1);
});
