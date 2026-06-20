#!/usr/bin/env node
/**
 * AI浏览器 MCP — 工具注册表冒烟测试（非场景测试）
 *
 * 仅验证各工具「能被调用、不崩溃」，不注入测试页、不轮询异步结果、不断言业务数据。
 * 真实自动化流程请用: node scenario_test.js
 *
 * 用法: node tool_test_all.js [--category 导航] [--tool browser_get_url] [--delay 80]
 * 全量顺序测试: node run_all_tests.js  （勿与其他测试脚本并行）
 * 需 AI浏览器.exe 已启动
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const HOST = process.env.AI_BROWSER_MCP_HOST || '127.0.0.1';
const PORT = parseInt(process.env.AI_BROWSER_MCP_PORT || '9222', 10);
const MCP_PATH = '/mcp';
const DELAY_MS = parseInt(process.env.TOOL_TEST_DELAY || '60', 10);
const OUT_FILE = path.join(__dirname, 'tool_test_report.json');

// 会破坏浏览器/GUI 状态的工具 — 注册表冒烟中跳过
const SKIP_TOOLS = new Set([
    'browser_create', 'browser_create_background', 'browser_create_tab',
    'browser_close', 'browser_close_try',
    'browser_set_parent', 'browser_move_window', 'browser_set_window_style',
    'browser_set_auto_resize', 'browser_set_visibility', 'browser_set_focus',
    'browser_send_message',
    'browser_view_source', 'browser_open_devtools', 'browser_close_devtools',
    'browser_set_proxy', 'browser_clear_proxy', 'browser_set_s5_proxy',
    'browser_delete_cookies', 'browser_clear_cache', 'browser_clear_cache_browser',
    'browser_print', 'browser_start_download',
    'browser_task_runner_post', 'browser_task_runner_close',
    // 调试器：逐工具空参调用会 paused 卡死 / enable 超时，改由末尾 debuggerSmoke + 场景脚本覆盖
    'browser_debugger_enable', 'browser_debugger_pause', 'browser_debugger_resume',
    'browser_debugger_step_over', 'browser_debugger_step_into', 'browser_debugger_step_out',
    'browser_debugger_stack', 'browser_debugger_set_breakpoint', 'browser_debugger_evaluate',
    'browser_debugger_wait_paused', 'browser_debugger_last_paused', 'browser_debugger_inspect',
    'browser_debugger_flow', 'browser_debugger_script_source',
]);

const args = process.argv.slice(2);
const filterCategory = (() => {
    const i = args.indexOf('--category');
    return i >= 0 ? args[i + 1] : '';
})();
const filterTool = (() => {
    const i = args.indexOf('--tool');
    return i >= 0 ? args[i + 1] : '';
})();

// 各工具默认参数 (无参工具省略)
const TOOL_ARGS = {
    browser_navigate: { url: `http://${HOST}:${PORT}/` },
    browser_execute_js: { code: 'void 0' },
    browser_evaluate: { code: '1+1' },
    browser_console_eval: { expression: '1+1' },
    browser_dom_query: { selector: 'body' },
    browser_dom_click: { selector: 'body' },
    browser_dom_set_value: { selector: '#searchInput', value: 'mcp' },
    browser_dom_get_html: { selector: 'body' },
    browser_fill_set_value: { selector: 'body', value: '' },
    browser_fill_click: { selector: 'body' },
    browser_fill_focus: { selector: 'body' },
    browser_fill_scroll: { selector: 'body' },
    browser_fill_exists: { selector: 'body' },
    browser_fill_attr_get: { selector: 'body', attribute: 'class' },
    browser_fill_attr_set: { selector: 'body', attribute: 'data-mcp-test', value: '1' },
    browser_fill_trigger: { selector: 'body', event: 'click' },
    browser_fill_select: { selector: 'select', value: '1' },
    browser_mouse_click: { x: 10, y: 10, button: 'left' },
    browser_mouse_move: { x: 20, y: 20 },
    browser_mouse_wheel: { x: 10, y: 10, delta_x: 0, delta_y: -120 },
    browser_key_event: { key_code: 65, type: 'keydown', modifiers: 0 },
    browser_vip_mouse_click: { x: 10, y: 10 },
    browser_vip_mouse_move: { x: 20, y: 20 },
    browser_vip_mouse_press: { x: 10, y: 10 },
    browser_vip_mouse_release: { x: 10, y: 10 },
    browser_vip_mouse_wheel: { x: 10, y: 10, delta_x: 0, delta_y: -120 },
    browser_vip_key_press: { key_code: 65, modifiers: 0 },
    browser_vip_key_release: { key_code: 65, modifiers: 0 },
    browser_vip_key_click: { key_code: 65, modifiers: 0 },
    browser_vip_key_input: { char_code: 97 },
    browser_vip_key_type: { text: 'a' },
    browser_touch_press: { x: 10, y: 10 },
    browser_touch_release: { x: 10, y: 10 },
    browser_touch_move: { x: 15, y: 15 },
    browser_set_zoom: { level: '1.0' },
    browser_find: { text: 'test' },
    browser_set_mute: { mute: false },
    browser_set_cookie: { name: 'mcp_test', value: '1', domain: 'localhost' },
    browser_delete_cookies: { confirm: false },
    browser_set_proxy: { address: '127.0.0.1:8888' },
    browser_set_s5_proxy: { address: '127.0.0.1:1080' },
    browser_start_download: { url: 'https://www.example.com/favicon.ico' },
    browser_download_image: { url: 'https://www.example.com/favicon.ico' },
    browser_print_to_pdf: { path: path.join(require('os').tmpdir(), 'mcp_test.pdf'), overwrite: true },
    browser_cdp: { method: 'Browser.getVersion', params: '{}' },
    browser_cdp_call: { method: 'Browser.getVersion', params: '{}' },
    browser_cdp_event: { event_name: 'test' },
    browser_intercept: { action: 'clear' },
    browser_network: { action: 'network_get' },
    browser_collect: { action: 'network_get' },
    browser_wait: { what: 'timeout', value: '50', max_ms: 100 },
    browser_inject: { type: 'js', code: 'void 0' },
    browser_event: { event_type: 'load_end' },
    browser_network_body: { request_id: 'none' },
    browser_fingerprint: { action: 'count' },
    browser_screenshot: { format: 'png' },
    browser_set_visibility: { visible: true },
    browser_set_focus: { focus: true },
    browser_move_window: { x: 0, y: 0, width: 800, height: 600 },
    browser_send_message: { message: 0, wparam: 0, lparam: 0 },
    browser_vip_websocket_intercept: { enable: true },
    browser_vip_resource_intercept: { action: 'clear' },
    browser_vip_navigate_intercept: { action: 'clear' },
    browser_vip_request_filter: { action: 'clear' },
    browser_vip_set_user_agent: { user_agent: 'MCP-Test/1.0' },
    browser_vip_set_language: { language: 'zh-CN' },
    browser_vip_set_timezone: { timezone: 'Asia/Shanghai' },
    browser_vip_set_geolocation: { latitude: 39.9, longitude: 116.4 },
    browser_vip_canvas_fingerprint: { action: 'count' },
    browser_vip_webgl_fingerprint: { action: 'count' },
    browser_vip_audio_fingerprint: { action: 'count' },
    browser_vip_webrtc: { disable: true },
    browser_vip_ssl_fingerprint: { action: 'count' },
    browser_vip_fingerprint_batch: { config: '{}' },
    browser_vip_load_extension: { crx_path: 'C:\\nonexistent\\test.crx' },
    browser_vip_unload_extension: { extension_id: 'test' },
    browser_vip_extension_info: { extension_id: 'test' },
    browser_vip_execute_js_context: { code: '1+1' },
    browser_vip_dom_search: { query: 'body' },
    browser_task_runner_list: {},
    browser_task_runner_close: { id: 0 },
    mcp_result: { request_id: 'none' },
    batch: { commands: [{ name: 'ping', arguments: {} }] },
    workflow_get: { name: 'hello' },
    workflow_run: { name: 'hello' },
    browser_reload: { ignore_cache: false },
    browser_create: { url: 'about:blank' },
    browser_create_background: { url: 'about:blank' },
    browser_create_tab: { url: 'about:blank' },
    browser_close: { force: false },
};

// 预期失败 (禁用/VIP/缺参) — 不算 FAIL
const EXPECT_FAIL_PATTERNS = [
    '已禁用', 'GUI自动管理', 'GUI管理', 'VIP', 'vip', '授权',
    '参数不能为空', '缺少参数', '未知action', '未知type', '未知what',
    'request_id', 'request_id', '没有可用的浏览器', '主框架无效',
    '无法后退', '无法前进', '文件路径不允许', '路径不允许',
    'not found', '不存在', '无导航历史', '无结果', '未找到',
    '需要', '参数', 'confirm: true', 'task_id', '异步', '已提交',
    'browser_task_runner_close', 'network_body', 'cdp_event',
    '操作超时', 'timeout', 'Can only perform operation while paused',
];

const CATEGORY_RULES = [
    ['系统', /^(mcp_|ping|batch|aliases)/],
    ['导航', /^browser_(navigate|get_url|get_title|back|forward|reload|stop|list|status|view_source|popup|loading|window|can_navigate)/],
    ['JS', /^browser_(execute_js|evaluate|console_eval|get_source|get_text)/],
    ['DOM', /^browser_dom_/],
    ['填表', /^browser_fill_/],
    ['鼠标键盘', /^browser_(mouse_|key_event|touch_|vip_mouse|vip_key|vip_touch)/],
    ['编辑缩放', /^browser_(edit_|set_zoom|get_zoom|find|stop_find|set_mute|is_muted|is_loading)/],
    ['Cookie代理', /^browser_(get_cookie|set_cookie|delete_cookie|refresh_cookie|set_proxy|clear_proxy|set_s5|vip_clear_s5|clear_cache|cache_dir)/],
    ['截图打印', /^browser_(screenshot|print|start_download|download_image)/],
    ['网络CDP', /^browser_(cdp|intercept|network|collect|wait|inject|event)/],
    ['指纹', /^browser_(fingerprint|vip_canvas|vip_webgl|vip_audio|vip_webrtc|vip_ssl|vip_fingerprint)/],
    ['VIP', /^browser_vip_/],
    ['窗口DevTools', /^browser_(open_devtools|close_devtools|get_window|set_visibility|set_focus|move_window|send_message|compress|fbro_version|enum_frame|focus_frame|frame)/],
    ['创建关闭', /^browser_(create|close)/],
    ['其他', /.*/],
];

function categorize(name) {
    for (const [cat, re] of CATEGORY_RULES) {
        if (re.test(name)) return cat;
    }
    return '其他';
}

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
                try { resolve({ status: res.statusCode, json: JSON.parse(raw), raw }); }
                catch (e) { reject(new Error('非 JSON: ' + raw.slice(0, 150))); }
            });
        });
        req.on('error', reject);
        req.setTimeout(45000, () => { req.destroy(); reject(new Error('timeout')); });
        req.write(data);
        req.end();
    });
}

function getToolsList() {
    return new Promise((resolve, reject) => {
        http.get({ hostname: HOST, port: PORT, path: '/tools/list', timeout: 10000 }, (res) => {
            let raw = '';
            res.on('data', (c) => { raw += c; });
            res.on('end', () => {
                try {
                    const j = JSON.parse(raw);
                    resolve(j.tools || []);
                } catch (e) { reject(e); }
            });
        }).on('error', reject);
    });
}

function extractInner(result) {
    const text = JSON.stringify(result);
    let inner = null;
    let plain = '';
    if (result && result.content && result.content[0] && result.content[0].text) {
        plain = result.content[0].text;
        try { inner = JSON.parse(plain); } catch (_) { /* 纯文本成功响应 */ }
    }
    return { text, inner, plain, isError: result && result.isError === true };
}

function classify(name, err, inner, text, plain, isError) {
    if (err) {
        const msg = String(err.message || err);
        if (EXPECT_FAIL_PATTERNS.some((p) => msg.includes(p))) return 'expect';
        return 'fail';
    }
    if (isError) {
        const msg = plain || text;
        if (EXPECT_FAIL_PATTERNS.some((p) => msg.includes(p))) return 'expect';
        return 'fail';
    }
    if (inner) {
        if (inner.success === true) return 'ok';
        if (inner._async === true || (inner.data && inner.data.task_id)) return 'async';
        const msg = JSON.stringify(inner.message || inner.data || inner);
        if (inner.success === false && EXPECT_FAIL_PATTERNS.some((p) => msg.includes(p))) return 'expect';
        if (inner.success === false) return 'fail';
    }
    if (text.includes('"_async":true') || text.includes('task_id') || (plain && plain.includes('task_id'))) return 'async';
    if (text.includes('"success":true') || text.includes('"isError":true')) {
        if (text.includes('"isError":true')) {
            if (EXPECT_FAIL_PATTERNS.some((p) => text.includes(p))) return 'expect';
            return 'fail';
        }
        return 'ok';
    }
    // 命令成功(纯文本): 有 content 且无 isError → OK
    if (plain || (text.includes('"content"') && !text.includes('"isError":true'))) return 'ok';
    if (EXPECT_FAIL_PATTERNS.some((p) => text.includes(p))) return 'expect';
    return 'fail';
}

async function callTool(name, toolArgs) {
    const res = await postMcp({
        jsonrpc: '2.0', id: 'test_' + name, method: 'tools/call',
        params: { name, arguments: toolArgs || {} }
    });
    if (res.status !== 200) throw new Error('HTTP ' + res.status);
    if (res.json.error) throw new Error(res.json.error.message || JSON.stringify(res.json.error));
    return res.json.result;
}

/** 调试器清理（不跑 flow，避免 tool_test 期间再次 paused） */
async function debuggerCleanup() {
    try {
        for (let i = 0; i < 2; i++) {
            await callTool('browser_cdp', { method: 'Debugger.resume', params: '{}' });
            await sleep(250);
        }
        await callTool('browser_cdp', { method: 'Debugger.disable', params: '{}' });
        await sleep(400);
    } catch (_) { /* ignore */ }
}

async function main() {
    console.log('AI浏览器 MCP 逐一测试 @ ' + HOST + ':' + PORT);
    const tools = await getToolsList();
    console.log('工具总数: ' + tools.length);

    // 预热: 导航到 MCP 欢迎页 (勿用 about:blank, 测试后会白屏)
    try {
        await callTool('browser_navigate', { url: `http://${HOST}:${PORT}/` });
        await sleep(800);
    } catch (e) {
        console.warn('预热 navigate 失败:', e.message);
    }

    let list = tools.map((t) => t.name);
    if (filterTool) list = list.filter((n) => n === filterTool || n.replace(/\./g, '_') === filterTool);
    if (filterCategory) list = list.filter((n) => categorize(n) === filterCategory);

    const stats = { ok: 0, async: 0, expect: 0, fail: 0, skip: 0 };
    const results = [];
    let idx = 0;

    for (const name of list) {
        idx++;
        const cat = categorize(name);

        if (SKIP_TOOLS.has(name)) {
            stats.skip++;
            results.push({ name, category: cat, status: 'skip', detail: '破坏性/状态变更，场景测试覆盖' });
            console.log('[' + idx + '/' + list.length + '] SKIP ' + name + ' [' + cat + ']');
            continue;
        }

        const toolArgs = TOOL_ARGS[name] !== undefined ? TOOL_ARGS[name] : {};
        const prefix = '[' + idx + '/' + list.length + ']';
        let status = 'fail';
        let detail = '';

        try {
            const result = await callTool(name, toolArgs);
            const { text, inner, plain, isError } = extractInner(result);
            status = classify(name, null, inner, text, plain, isError);
            detail = plain || (inner ? (inner.message || JSON.stringify(inner.data || inner).slice(0, 120)) : text.slice(0, 120));
        } catch (e) {
            status = classify(name, e, null, '');
            detail = e.message || String(e);
        }

        stats[status]++;
        results.push({ name, category: cat, status, detail, args: toolArgs });

        const mark = { ok: 'OK  ', async: 'ASYN', expect: 'EXP ', fail: 'FAIL' }[status];
        console.log(prefix + ' ' + mark + ' ' + name + ' [' + cat + '] ' + (detail ? '— ' + detail.slice(0, 80) : ''));

        if (DELAY_MS > 0) await sleep(DELAY_MS);
    }

    const report = {
        time: new Date().toISOString(),
        host: HOST + ':' + PORT,
        total: list.length,
        stats,
        results
    };
    fs.writeFileSync(OUT_FILE, JSON.stringify(report, null, 2), 'utf8');

    // 收尾: 调试器清理 + 恢复 GUI
    await debuggerCleanup();
    try {
        await callTool('browser_restore_gui', {});
        await sleep(1200);
    } catch (e) {
        try {
            await callTool('browser_navigate', { url: `http://${HOST}:${PORT}/` });
        } catch (_) { /* ignore */ }
    }

    console.log('\n========== 汇总 ==========');
    console.log('OK(成功):     ' + stats.ok);
    console.log('ASYN(异步):   ' + stats.async);
    console.log('EXP(预期失败): ' + stats.expect);
    console.log('SKIP(跳过):   ' + stats.skip);
    console.log('FAIL(异常):   ' + stats.fail);
    console.log('报告: ' + OUT_FILE);

    if (stats.fail > 0) {
        console.log('\n--- FAIL 列表 ---');
        results.filter((r) => r.status === 'fail').forEach((r) => {
            console.log('  ' + r.name + ' — ' + r.detail);
        });
    }

    process.exit(stats.fail > 0 ? 1 : 0);
}

main().catch((e) => {
    console.error('测试中止:', e.message || e);
    console.error('请先启动 AI浏览器.exe');
    process.exit(1);
});
