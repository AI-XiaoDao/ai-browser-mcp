#!/usr/bin/env node
/**
 * 回归 — sync-wait / workflow / batch / DOM 语义
 *
 * 用法: node regression_sync_wait.js
 * 全量顺序测试: node run_all_tests.js
 * 环境: AI_BROWSER_MCP_HOST / AI_BROWSER_MCP_PORT
 */
const http = require('http');

const HOST = process.env.AI_BROWSER_MCP_HOST || '127.0.0.1';
const PORT = parseInt(process.env.AI_BROWSER_MCP_PORT || '9222', 10);
const MCP_PATH = '/mcp';

const results = [];
let seq = 0;

function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
}

function postMcp(body) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify(body);
        const t0 = Date.now();
        const req = http.request({
            hostname: HOST, port: PORT, path: MCP_PATH, method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
        }, (res) => {
            let raw = '';
            res.on('data', (c) => { raw += c; });
            res.on('end', () => {
                let json = null;
                try { json = JSON.parse(raw); } catch (_) {}
                resolve({ status: res.statusCode, json, raw, ms: Date.now() - t0 });
            });
        });
        req.on('error', reject);
        req.setTimeout(120000, () => { req.destroy(); reject(new Error('HTTP timeout')); });
        req.write(data);
        req.end();
    });
}

async function callTool(name, args, id) {
    const res = await postMcp({
        jsonrpc: '2.0', id: id || ('reg_' + (++seq)),
        method: 'tools/call', params: { name, arguments: args || {} }
    });
    const result = res.json && res.json.result;
    const plain = (result && result.content && result.content[0] && result.content[0].text) || '';
    let inner = null;
    try { inner = JSON.parse(plain); } catch (_) {}
    return {
        ms: res.ms,
        isError: !!(result && result.isError),
        plain,
        inner,
        text: plain + JSON.stringify(inner || {})
    };
}

function pass(id, note) {
    results.push({ id, ok: true, note });
    console.log('  PASS', id, note ? '- ' + note : '');
}

function fail(id, note) {
    results.push({ id, ok: false, note });
    console.log('  FAIL', id, '-', note);
}

function skip(id, note) {
    results.push({ id, ok: null, note });
    console.log('  SKIP', id, '-', note);
}

async function testPing() {
    const p = await callTool('ping', {});
    if (!p.isError && p.text.includes('pong')) pass('ping');
    else fail('ping', p.plain.slice(0, 80));
}

async function testWorkflowList() {
    const p = await callTool('workflow_list', {});
    const data = p.inner && p.inner.data;
    const count = data && data.count;
    const names = data && data.workflows;
    if (count >= 2 && Array.isArray(names) && names.includes('hello') && names.includes('ping_navigate')) {
        pass('workflow_list', 'count=' + count);
    } else if (count === 0) {
        fail('workflow_list', 'count=0 (需重编译或检查 linker/workflows)');
    } else {
        fail('workflow_list', 'workflows=' + JSON.stringify(names));
    }
}

function parseWorkflowData(payload) {
    if (payload.json && payload.json.data) return payload.json.data;
    try {
        const o = JSON.parse(payload.plain);
        if (o && o.data) return o.data;
        if (o && o.workflow) return o;
    } catch (_) {}
    return null;
}

async function testWorkflowRun(name, minSteps) {
    const p = await callTool('workflow_run', { name });
    const data = parseWorkflowData(p);
    if (!data) return fail('workflow_run_' + name, 'no data: ' + (p.plain || '').slice(0, 100));
    if (data.success !== true) return fail('workflow_run_' + name, 'success=false: ' + (p.plain || '').slice(0, 200));
    if ((data.total_steps || 0) < minSteps) return fail('workflow_run_' + name, 'total_steps=' + data.total_steps);
    pass('workflow_run_' + name, 'steps=' + data.total_steps);
}

async function testGetTitleSync() {
    const p = await callTool('browser_get_title', {});
    if (p.isError) return fail('get_title_sync', 'isError');
    if (p.text.includes('task_') && p.text.includes('"_async":true')) {
        return fail('get_title_sync', '仍返回 async task_id');
    }
    if (p.plain.length > 0) pass('get_title_sync', p.plain.slice(0, 40));
    else fail('get_title_sync', 'empty');
}

async function testGetTitleAsyncOnly() {
    const p = await callTool('browser_get_title', { async_only: true });
    if (!p.text.includes('task_')) return fail('get_title_async_only', '无 task_id');
    pass('get_title_async_only');
}

async function testDomClickFail() {
    const p = await callTool('browser_dom_click', { selector: '#__mcp_nonexistent_xyz__' });
    if (p.isError || (p.inner && p.inner.success === false) || p.text.includes('"success":false')) {
        pass('dom_click_bad_selector', '正确失败');
    } else if (p.text.includes('element not found') && !p.text.includes('"success":false')) {
        fail('dom_click_bad_selector', 'P0-3 未生效: element not found 但 success:true');
    } else {
        fail('dom_click_bad_selector', p.plain.slice(0, 120));
    }
}

async function testBatchPartialFail() {
    const p = await callTool('batch', {
        commands: [
            { name: 'ping', arguments: {} },
            { name: 'browser_dom_click', arguments: { selector: '#__mcp_nonexistent_xyz__' } }
        ]
    });
    if (p.isError || (p.inner && p.inner.success === false)) {
        pass('batch_partial_fail', '外层 success:false / isError');
    } else if (p.inner && p.inner.data && p.inner.data.failure_count > 0 && p.inner.success === false) {
        pass('batch_partial_fail', 'failure_count=' + p.inner.data.failure_count);
    } else {
        fail('batch_partial_fail', '子失败但外层仍 success — P1-1 未生效: ' + p.plain.slice(0, 150));
    }
}

async function testStringArguments() {
    // 通过 raw POST 传字符串 arguments
    const res = await postMcp({
        jsonrpc: '2.0', id: 'str_args',
        method: 'tools/call',
        params: {
            name: 'browser_get_title',
            arguments: '{"async_only":true}'
        }
    });
    const plain = (res.json.result && res.json.result.content && res.json.result.content[0].text) || '';
    if (plain.includes('task_')) pass('string_arguments');
    else fail('string_arguments', 'async_only 未生效: ' + plain.slice(0, 80));
}

async function testConcurrentPingDuringSyncWait() {
    const slow = callTool('browser_get_title', { max_ms: 8000 });
    await sleep(80);
    const ping = await postMcp({ jsonrpc: '2.0', id: 'ping_during', method: 'ping' });
    await slow;
    if (ping.ms < 500) pass('concurrent_ping_during_sync', ping.ms + 'ms');
    else fail('concurrent_ping_during_sync', 'ping 耗时 ' + ping.ms + 'ms (P1-2 锁未释放?)');
}

async function testEvaluateJsonStructure() {
    const p = await callTool('browser_evaluate', { code: 'JSON.stringify({a:1,b:[2,3]})' });
    const hasStruct = p.text.includes('"a":1') || p.text.includes('"a": 1');
    if (hasStruct && p.text.includes('"_sync_waited"')) pass('evaluate_json_structure');
    else if (hasStruct) pass('evaluate_json_structure', '有 JSON 结构(未标记 _sync_waited)');
    else if (p.isError) fail('evaluate_json_structure', p.plain.slice(0, 80));
    else fail('evaluate_json_structure', p.plain.slice(0, 80));
}

async function testWorkflowDomFailStop() {
    const p = await callTool('workflow_run', {
        name: 'inline_dom_fail',
        on_error: 'stop',
        steps: [
            { tool: 'browser_dom_click', args: { selector: '#__mcp_nonexistent_xyz__' } }
        ]
    });
    const data = parseWorkflowData(p);
    if (!data) return fail('workflow_dom_fail_stop', (p.plain || '').slice(0, 100));
    const steps = data.steps || [];
    const step0 = steps[0];
    if (data.success === false && data.failure_count >= 1 && step0 && step0.success === false) {
        pass('workflow_dom_fail_stop', 'on_error:stop 联动');
    } else {
        fail('workflow_dom_fail_stop', JSON.stringify({ success: data.success, step0: step0 }).slice(0, 120));
    }
}

async function testBatchSyncWait() {
    const p = await callTool('batch', {
        commands: [{ name: 'browser_get_title', arguments: {} }]
    });
    if (p.isError) return fail('batch_sync_wait', 'isError');
    if (p.text.includes('task_') && p.text.includes('"_async":true') && !p.text.includes('"_sync_waited"')) {
        return fail('batch_sync_wait', '子命令未 sync-wait');
    }
    if (p.plain.length > 0) pass('batch_sync_wait');
    else fail('batch_sync_wait', 'empty');
}

async function runTest(id, fn) {
    try {
        await fn();
    } catch (e) {
        fail(id, e.message);
    }
}

async function main() {
    console.log('MCP regression @', HOST + ':' + PORT);
    console.log('---');

    try {
        await runTest('ping', testPing);
        await runTest('workflow_list', testWorkflowList);
        await runTest('get_title_sync', testGetTitleSync);
        await runTest('get_title_async_only', testGetTitleAsyncOnly);
        await runTest('string_arguments', testStringArguments);
        await runTest('dom_click_bad_selector', testDomClickFail);
        await runTest('batch_partial_fail', testBatchPartialFail);
        await runTest('batch_sync_wait', testBatchSyncWait);
        await runTest('concurrent_ping_during_sync', testConcurrentPingDuringSyncWait);
        await runTest('evaluate_json_structure', testEvaluateJsonStructure);
        await runTest('workflow_dom_fail_stop', testWorkflowDomFailStop);
        await runTest('workflow_run_hello', () => testWorkflowRun('hello', 5));
        await runTest('workflow_run_ping_navigate', () => testWorkflowRun('ping_navigate', 5));
    } catch (e) {
        fail('fatal', e.message);
    }

    const passed = results.filter((r) => r.ok === true).length;
    const failed = results.filter((r) => r.ok === false).length;
    const skipped = results.filter((r) => r.ok === null).length;
    console.log('---');
    console.log(`Done: ${passed} pass, ${failed} fail, ${skipped} skip`);
    process.exit(failed > 0 ? 1 : 0);
}

main();
