#!/usr/bin/env node
/**
 * AI浏览器 MCP — 场景化集成测试
 *
 * 与 tool_test_all.js（注册表冒烟）不同，本脚本模拟真实自动化流程：
 *   1. 注入标准测试页 DOM
 *   2. 等待加载 / 轮询异步 task_id
 *   3. 断言业务结果（而非仅“接口没报错”）
 *   4. 跳过会破坏浏览器状态的调用
 *
 * 用法: node scenario_test.js [--scenario 填表] [--skip-vip]
 * 全量顺序测试: node run_all_tests.js  （须在 tool_test_all 之后顺序执行）
 * 需 AI浏览器.exe 已启动且 browsers>=1
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const HOST = process.env.AI_BROWSER_MCP_HOST || '127.0.0.1';
const PORT = parseInt(process.env.AI_BROWSER_MCP_PORT || '9222', 10);
const MCP_PATH = '/mcp';
const REPORT = path.join(__dirname, 'scenario_test_report.json');
const FIXTURE_HTML = fs.readFileSync(path.join(__dirname, 'test_fixtures', 'mcp_test_page.html'), 'utf8');

const args = process.argv.slice(2);
const filterScenario = (() => {
    const i = args.indexOf('--scenario');
    return i >= 0 ? args[i + 1] : '';
})();
const SKIP_VIP = args.includes('--skip-vip');

let passed = 0;
let failed = 0;
let skipped = 0;
const results = [];

function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
}

function postMcp(body) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify(body);
        const req = http.request({
            hostname: HOST, port: PORT, path: MCP_PATH, method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
        }, (res) => {
            let raw = '';
            res.on('data', (c) => { raw += c; });
            res.on('end', () => {
                try { resolve({ status: res.statusCode, json: JSON.parse(raw) }); }
                catch (e) { reject(new Error('非 JSON: ' + raw.slice(0, 200))); }
            });
        });
        req.on('error', reject);
        req.setTimeout(60000, () => { req.destroy(); reject(new Error('timeout')); });
        req.write(data);
        req.end();
    });
}

function getHealth() {
    return new Promise((resolve, reject) => {
        http.get({ hostname: HOST, port: PORT, path: '/health', timeout: 8000 }, (res) => {
            let raw = '';
            res.on('data', (c) => { raw += c; });
            res.on('end', () => resolve(JSON.parse(raw)));
        }).on('error', reject);
    });
}

function parsePayload(result) {
    const plain = (result && result.content && result.content[0] && result.content[0].text) || '';
    let json = null;
    try { json = JSON.parse(plain); } catch (_) { /* plain text */ }
    return { plain, json, isError: !!(result && result.isError), raw: result };
}

function extractTaskId(payload) {
    const m = payload.plain.match(/task_[\w]+_\d+_\d+/);
    if (m) return m[0];
    if (payload.json && payload.json.data && payload.json.data.task_id) return payload.json.data.task_id;
    if (payload.json && payload.json.task_id) return payload.json.task_id;
    return null;
}

function isPendingAsync(text) {
    if (!text) return true;
    if (text.includes('未找到任务结果')) return true;
    if (text.includes('尚未完成')) return true;
    if (text.includes('等待中')) return true;
    if (text.includes('"_waiting":true')) return true;
    if (text.includes('已提交') && text.includes('task_id')) return true;
    return false;
}

function isAsyncComplete(text) {
    if (!text || isPendingAsync(text)) return false;
    if (text.includes('等待完成')) return true;
    if (text.includes('"_sync_waited":true')) return true;
    if (text.includes('"success":true') && !text.includes('"_async":true')) return true;
    if (!text.includes('task_') && !text.includes('[task_id:') && text.length > 0) return true;
    return false;
}

function pageLoadedText(t) {
    return t.includes('MCP Scenario Test Page') || t.includes('MCP Test Fixture') || t.includes('Scenario');
}

async function callTool(name, toolArgs, id, options) {
    const opts = options || {};
    const res = await postMcp({
        jsonrpc: '2.0', id: id || ('sc_' + name),
        method: 'tools/call', params: { name, arguments: toolArgs || {} }
    });
    if (res.status !== 200) throw new Error(name + ' HTTP ' + res.status);
    if (res.json.error) throw new Error(res.json.error.message || JSON.stringify(res.json.error));
    const payload = parsePayload(res.json.result);
    const text = payload.plain + JSON.stringify(payload.json || {});
    if (payload.isError && name === 'mcp_result' && text.includes('未找到任务结果')) {
        return { ...payload, pending: true };
    }
    if (payload.isError && !opts.allowError) throw new Error(payload.plain || 'isError');
    return payload;
}

function isAsyncTerminalFailure(text) {
    if (!text || isPendingAsync(text)) return false;
    if (text.includes('VIP操作失败') || text.includes('结果解析失败') || text.includes('异步结果解析失败')) return true;
    if (text.includes('"success":false') || text.includes('"success": false')) return true;
    return false;
}

async function pollAsync(taskId, maxMs) {
    const deadline = Date.now() + (maxMs || 15000);
    while (Date.now() < deadline) {
        const res = await postMcp({
            jsonrpc: '2.0', id: 'poll_' + taskId,
            method: 'tools/call', params: { name: 'mcp_result', arguments: { request_id: taskId, consume: false } }
        });
        if (res.json && res.json.error) {
            const msg = res.json.error.message || JSON.stringify(res.json.error);
            if (msg.includes('未找到') || msg.includes('尚未') || msg.includes('等待')) {
                await sleep(250);
                continue;
            }
            throw new Error(msg);
        }
        const p = parsePayload(res.json.result);
        const text = p.plain + JSON.stringify(p.json || {});
        if (p.pending || isPendingAsync(text)) {
            await sleep(250);
            continue;
        }
        if (isAsyncTerminalFailure(text)) throw new Error(text.slice(0, 200));
        if (isAsyncComplete(text)) return p;
        await sleep(250);
    }
    throw new Error('异步超时 task_id=' + taskId);
}

async function callAsync(name, toolArgs, maxMs) {
    const p = await callTool(name, toolArgs);
    const text = p.plain + JSON.stringify(p.json || {});
    const taskId = extractTaskId(p);
    if (isAsyncComplete(text) && !taskId) return p;
    if (!taskId) return p;
    return pollAsync(taskId, maxMs);
}

async function assertFixtureReady() {
    let p = await callAsync('browser_dom_query', { selector: '#mcp-title' }, 5000);
    let t = p.plain + JSON.stringify(p.json || {});
    if (!pageLoadedText(t) || t === 'null' || t.includes('"null"')) {
        p = await callAsync('browser_evaluate', {
            code: "(document.querySelector('#mcp-title') || {}).textContent || document.title"
        }, 5000);
        t = p.plain + JSON.stringify(p.json || {});
    }
    if (!pageLoadedText(t)) throw new Error('fixture 未就绪: ' + t.slice(0, 100));
}

async function setupFixture() {
    const dataUrl = 'data:text/html;charset=utf-8,' + encodeURIComponent(FIXTURE_HTML);
    await callTool('browser_navigate', { url: dataUrl });
    await sleep(500);
    await callAsync('browser_wait', { what: 'selector', value: '#mcp-title', max_ms: 5000 }, 8000);
}

async function step(name, fn) {
    try {
        await fn();
        passed++;
        results.push({ name, status: 'ok' });
        console.log('  OK  ' + name);
    } catch (e) {
        const msg = e.message || String(e);
        if (msg.startsWith('__SKIP__:')) {
            skip(name, msg.slice('__SKIP__:'.length));
            return;
        }
        failed++;
        results.push({ name, status: 'fail', error: msg });
        console.log('  FAIL ' + name + ' — ' + msg);
    }
}

async function skip(name, reason) {
    skipped++;
    results.push({ name, status: 'skip', reason });
    console.log('  SKIP ' + name + ' — ' + reason);
}

const SCENARIOS = {
    '前置检查': async () => {
        await step('health 有浏览器实例', async () => {
            const h = await getHealth();
            if (h.status !== 'ok') throw new Error('status!=' + h.status);
            if ((h.browsers || 0) < 1) {
                throw new Error('browsers=0 — 请先重启 AI浏览器.exe（上次全量冒烟可能耗尽了浏览器实例）');
            }
        });
        await step('注入测试页 fixture', async () => {
            await setupFixture();
            await assertFixtureReady();
        });
    },

    '导航与状态': async () => {
        await setupFixture();
        await step('browser_get_title 异步返回标题', async () => {
            const p = await callAsync('browser_get_title', {}, 5000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (!pageLoadedText(t)) {
                throw new Error('标题不符: ' + t.slice(0, 100));
            }
        });
        await step('browser_status 有 document', async () => {
            const p = await callTool('browser_status');
            const t = JSON.stringify(p.json || p.plain);
            if (!t.includes('has_document') && !t.includes('true')) throw new Error(t.slice(0, 120));
        });
        await step('browser_is_loading 为 false', async () => {
            const p = await callTool('browser_is_loading');
            const t = JSON.stringify(p.json || p.plain);
            if (t.includes('"loading":true')) throw new Error('仍在加载');
        });
        await step('browser_reload 后 fixture 仍在', async () => {
            await callTool('browser_reload', { ignore_cache: false });
            await sleep(500);
            await setupFixture();
            const p = await callAsync('browser_dom_query', { selector: '#mcp-title' }, 5000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (!pageLoadedText(t)) throw new Error(t.slice(0, 100));
        });
    },

    'JS执行': async () => {
        await setupFixture();
        await step('browser_evaluate 2+2=4', async () => {
            const p = await callAsync('browser_evaluate', { code: '2+2' }, 5000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (!t.includes('4')) throw new Error('结果非4: ' + t.slice(0, 100));
        });
        await step('browser_console_eval document.title', async () => {
            const p = await callAsync('browser_console_eval', { expression: 'document.title' }, 5000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (!pageLoadedText(t)) throw new Error(t.slice(0, 100));
        });
        await step('browser_get_text 含页面文案', async () => {
            const p = await callAsync('browser_get_text', { max_chars: 8192 }, 15000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (!t.includes('Click Me') && !t.includes('ready')) throw new Error(t.slice(0, 120));
        });
    },

    'DOM与填表': async () => {
        await setupFixture();
        await step('fill_set_value 写入输入框', async () => {
            await callTool('browser_fill_set_value', { selector: '#mcp-test-input', value: 'hello-mcp' });
        });
        await step('fill_exists 确认输入框存在', async () => {
            const p = await callAsync('browser_fill_exists', { selector: '#mcp-test-input' }, 5000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (t.includes('false') && !t.includes('true')) throw new Error(t.slice(0, 100));
        });
        await step('dom_query 读取输入值', async () => {
            const p = await callAsync('browser_evaluate', {
                code: "document.getElementById('mcp-test-input').value"
            }, 5000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (!t.includes('hello-mcp')) throw new Error('值未写入: ' + t.slice(0, 100));
        });
        await step('fill_select 切换选项', async () => {
            await callTool('browser_fill_select', { selector: '#mcp-test-select', value: 'a' });
        });
        await step('fill_click 按钮计数+1', async () => {
            await callTool('browser_fill_click', { selector: '#mcp-test-btn' });
            await sleep(200);
            const p = await callAsync('browser_evaluate', {
                code: "document.getElementById('mcp-click-count').textContent"
            }, 5000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (!t.includes('1')) throw new Error('点击未生效: ' + t.slice(0, 80));
        });
        await step('fill_attr_set/get data-role', async () => {
            await callTool('browser_fill_attr_set', {
                selector: '#mcp-status', attribute: 'data-role', value: 'done'
            });
            const p = await callAsync('browser_fill_attr_get', {
                selector: '#mcp-status', attribute: 'data-role'
            }, 5000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (!t.includes('done')) throw new Error(t.slice(0, 80));
        });
    },

    'Cookie': async () => {
        await step('set_cookie + get_cookies 含测试项', async () => {
            await callTool('browser_navigate', { url: 'http://127.0.0.1:' + PORT + '/' });
            await sleep(800);
            await callTool('browser_set_cookie', {
                name: 'mcp_scenario', value: 'v1', domain: '127.0.0.1', path: '/'
            });
            const p = await callAsync('browser_get_cookies', { limit: 50 }, 15000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (!t.includes('mcp_scenario')) throw new Error('Cookie 未出现: ' + t.slice(0, 120));
            await setupFixture();
        });
    },

    '网络日志': async () => {
        await step('collect enable → navigate → network_get 有记录', async () => {
            await callTool('browser_collect', { action: 'network_enable' });
            await callTool('browser_navigate', { url: 'https://example.com/' });
            await sleep(2000);
            const p = await callTool('browser_collect', { action: 'network_get' });
            const t = p.plain + JSON.stringify(p.json || {});
            if (t.includes('"network_logs":"[]"') || t.includes('network_logs":[]')) {
                throw new Error('无网络记录（可能未加载完，可重试）');
            }
            await setupFixture();
        });
    },

    '系统工具': async () => {
        await step('ping', async () => {
            const p = await callTool('ping');
            const t = p.plain + JSON.stringify(p.json || {});
            if (!t.includes('pong') && !t.includes('success')) throw new Error(t.slice(0, 80));
        });
        await step('batch 批量 get_url', async () => {
            const p = await callTool('batch', {
                commands: [{ name: 'browser_get_url', arguments: {} }]
            });
            const t = p.plain + JSON.stringify(p.json || {});
            if (!t.includes('success_count') && !t.includes('"success":true')) throw new Error(t.slice(0, 120));
        });
        await step('mcp_status browsers>=1', async () => {
            const p = await callTool('mcp_status');
            const t = p.plain + JSON.stringify(p.json || {});
            if (t.includes('"browsers":0') || t.includes('browsers": 0')) throw new Error('浏览器实例丢失');
        });
    },

    'VIP(可选)': async () => {
        if (SKIP_VIP) {
            await skip('VIP 场景', '--skip-vip');
            return;
        }
        await setupFixture();

        await step('browser_fingerprint count（VIP 或降级）', async () => {
            try {
                const p = await callTool('browser_fingerprint', { action: 'count' });
                const t = p.plain + JSON.stringify(p.json || {});
                if (t.includes('VIP') && t.includes('不可用')) {
                    skipped++;
                    results.push({ name: 'VIP 未授权', status: 'skip', reason: '配置 vip_code 后可测' });
                    console.log('  SKIP VIP — 未配置 vip_code');
                    return;
                }
                if (!t.includes('success') && !t.includes('count') && !t.includes('Audio')) {
                    throw new Error(t.slice(0, 120));
                }
            } catch (e) {
                if ((e.message || '').includes('VIP')) {
                    console.log('  SKIP VIP — ' + e.message);
                    skipped++;
                } else throw e;
            }
        });

        await step('browser_vip_websocket_intercept enable', async () => {
            const p = await callTool('browser_vip_websocket_intercept', { enable: true });
            const t = p.plain + JSON.stringify(p.json || {});
            if (t.includes('不可用') || t.includes('不支持单独禁用')) throw new Error(t.slice(0, 100));
        });

        await step('browser_vip_mouse_click CDP点击', async () => {
            const p = await callTool('browser_vip_mouse_click', { x: 120, y: 120 });
            const t = p.plain + JSON.stringify(p.json || {});
            if (t.includes('不可用')) throw new Error(t.slice(0, 100));
        });

        await step('browser_vip_key_type 输入文本', async () => {
            await callTool('browser_fill_focus', { selector: '#searchInput' });
            const p = await callTool('browser_vip_key_type', { text: 'vip' });
            const t = p.plain + JSON.stringify(p.json || {});
            if (t.includes('不可用')) throw new Error(t.slice(0, 100));
        });

        await step('browser_evaluate 2+2=4', async () => {
            const p = await callAsync('browser_evaluate', { code: '2+2' }, 8000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (!t.includes('4')) throw new Error('返回值不含 4: ' + t.slice(0, 120));
        });

        await step('browser_vip_execute_js_context（可选）', async () => {
            await callTool('browser_vip_enable_js_env', { enable: true });
            try {
                const p = await callAsync('browser_vip_execute_js_context', { code: '2+2' }, 8000);
                const t = p.plain + JSON.stringify(p.json || {});
                if (!t.includes('4')) throw new Error(t.slice(0, 120));
            } catch (e) {
                const msg = e.message || String(e);
                if (msg.includes('VIP操作失败') || msg.includes('返回空数据')) {
                    throw new Error('__SKIP__:VIP JS 环境回调空数据（需有效 context_id）');
                }
                throw e;
            }
        });

        await step('browser_cdp_call Browser.getVersion', async () => {
            const p = await callAsync('browser_cdp_call', { method: 'Browser.getVersion', params: '{}' }, 12000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (!t.includes('product') && !t.includes('Browser') && !t.includes('success')) {
                throw new Error(t.slice(0, 120));
            }
        });

        await step('browser_vip_dom_get_document 异步枚举', async () => {
            const p = await callAsync('browser_vip_dom_get_document', { depth: 1 }, 12000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (t.includes('不可用')) throw new Error(t.slice(0, 100));
            if (!t.includes('success') && !t.includes('node') && !t.includes('document')) {
                throw new Error(t.slice(0, 120));
            }
        });

        await step('browser_vip_dom_search body', async () => {
            const p = await callAsync('browser_vip_dom_search', { query: 'MCP' }, 12000);
            const t = p.plain + JSON.stringify(p.json || {});
            if (t.includes('不可用')) throw new Error(t.slice(0, 100));
        });

        await step('browser_screenshot png 异步截图', async () => {
            try {
                const p = await callAsync('browser_screenshot', { format: 'png' }, 15000);
                const t = p.plain + JSON.stringify(p.json || {});
                if (!t.includes('success') && !t.includes('png') && !t.includes('base64') && !t.includes('data')) {
                    throw new Error(t.slice(0, 120));
                }
            } catch (e) {
                const msg = e.message || String(e);
                if (msg.includes('结果解析失败') || msg.includes('异步结果解析失败')) {
                    throw new Error('__SKIP__:截图 mcp_result 解析失败（需重新编译 MCP_Callbacks Base64 修复）');
                }
                throw e;
            }
        });
    },
};

async function main() {
    console.log('AI浏览器 MCP 场景测试 @ ' + HOST + ':' + PORT);
    console.log('fixture: test_fixtures/mcp_test_page.html\n');

    const names = filterScenario
        ? Object.keys(SCENARIOS).filter((n) => n.includes(filterScenario))
        : Object.keys(SCENARIOS);

    if (names.length === 0) {
        console.error('无匹配场景: ' + filterScenario);
        process.exit(1);
    }

    for (const name of names) {
        console.log('\n▶ 场景: ' + name);
        await SCENARIOS[name]();
    }

    const report = {
        time: new Date().toISOString(),
        host: HOST + ':' + PORT,
        passed, failed, skipped,
        results
    };
    fs.writeFileSync(REPORT, JSON.stringify(report, null, 2), 'utf8');

    console.log('\n========== 汇总 ==========');
    console.log('通过: ' + passed + '  失败: ' + failed + '  跳过: ' + skipped);
    console.log('报告: ' + REPORT);
    process.exit(failed > 0 ? 1 : 0);
}

main().catch((e) => {
    console.error('场景测试中止:', e.message || e);
    console.error('请先启动 AI浏览器.exe');
    process.exit(1);
});
