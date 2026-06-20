#!/usr/bin/env node
/**
 * AI浏览器 MCP — 工作流编排运行器
 *
 * 从 workflows/*.json 读取步骤定义，通过 HTTP MCP 逐步执行。
 * 服务端也可用 workflow_run 工具直接执行（同步）。
 *
 * 用法:
 *   node workflow_runner.js                    # 运行 hello.json
 *   node workflow_runner.js ping_navigate      # 指定工作流名(无 .json)
 *   node workflow_runner.js --list             # 列出 workflows 目录
 *   node workflow_runner.js --inline steps.json
 *   node workflow_runner.js --server hello     # 服务端 workflow_run
 *
 * 环境变量: AI_BROWSER_MCP_HOST / AI_BROWSER_MCP_PORT
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const HOST = process.env.AI_BROWSER_MCP_HOST || '127.0.0.1';
const PORT = parseInt(process.env.AI_BROWSER_MCP_PORT || '9222', 10);
const MCP_PATH = '/mcp';
const WF_DIR = path.join(__dirname, 'workflows');

const args = process.argv.slice(2);

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
                catch (e) { reject(new Error('非 JSON: ' + raw.slice(0, 300))); }
            });
        });
        req.on('error', reject);
        req.setTimeout(120000, () => { req.destroy(); reject(new Error('HTTP timeout')); });
        req.write(data);
        req.end();
    });
}

function parsePayload(result) {
    const plain = (result && result.content && result.content[0] && result.content[0].text) || '';
    let json = null;
    try { json = JSON.parse(plain); } catch (_) { /* plain text from sync-wait or mcp_result message */ }
    return { plain, json, isError: !!(result && result.isError) };
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
    if (text.includes('"success":false') && !text.includes('"_waiting":true')) return true;
    if (text.includes('等待完成')) return true;
    if (text.includes('"_sync_waited":true')) return true;
    if (text.includes('"success":true') && !text.includes('"_async":true')) return true;
    // sync-wait 直返: 纯文本 title/result，无 task_id
    if (!text.includes('task_') && !text.includes('[task_id:') && text.length > 0) return true;
    return false;
}

async function callTool(name, toolArgs, id, options) {
    const opts = options || {};
    const res = await postMcp({
        jsonrpc: '2.0', id: id || ('wf_' + name),
        method: 'tools/call', params: { name, arguments: toolArgs || {} }
    });
    if (res.status !== 200) throw new Error(name + ' HTTP ' + res.status);
    if (res.json.error) throw new Error(res.json.error.message || JSON.stringify(res.json.error));
    const payload = parsePayload(res.json.result);
    const text = payload.plain + JSON.stringify(payload.json || {});
    // mcp_result 轮询: 「未找到」不算 fatal
    if (payload.isError && name === 'mcp_result' && text.includes('未找到任务结果')) {
        return { ...payload, pending: true };
    }
    if (payload.isError && !opts.allowError) throw new Error(payload.plain || 'isError');
    return payload;
}

async function pollAsync(taskId, maxMs) {
    const deadline = Date.now() + (maxMs || 15000);
    while (Date.now() < deadline) {
        const p = await callTool('mcp_result', { request_id: taskId, consume: false }, 'poll_' + taskId, { allowError: true });
        const text = p.plain + JSON.stringify(p.json || {});
        if (p.pending || isPendingAsync(text)) {
            await sleep(250);
            continue;
        }
        if (text.includes('"success":false') && !text.includes('"_waiting":true') && !text.includes('等待中')) {
            throw new Error('async failed: ' + text.slice(0, 200));
        }
        if (isAsyncComplete(text)) return p;
        await sleep(250);
    }
    throw new Error('async timeout task_id=' + taskId);
}

async function runStep(step, index, onError) {
    if (step.skip) {
        console.log('  SKIP step', index);
        return { skipped: true };
    }
    if (step.delay_ms) {
        await sleep(step.delay_ms);
        return { delayed: step.delay_ms };
    }
    const tool = step.tool || step.name;
    if (!tool) throw new Error('step ' + index + ' 缺少 tool/name');
    const toolArgs = step.args || step.arguments || {};
    const maxMs = step.max_ms || 15000;

    console.log('  STEP', index, tool, JSON.stringify(toolArgs).slice(0, 80));
    const p = await callTool(tool, toolArgs, 'wf_s' + index);
    const text = p.plain + JSON.stringify(p.json || {});
    const taskId = extractTaskId(p);
    const alreadySync = isAsyncComplete(text) && !taskId;
    const shouldPoll = !alreadySync && (step.wait_async === true || (step.wait_async !== false && taskId));
    if (shouldPoll && taskId) return pollAsync(taskId, maxMs);
    return p;
}

async function runWorkflow(def) {
    const onError = def.on_error || 'stop';
    const steps = def.steps || [];
    const results = [];
    console.log('Workflow:', def.name || '(inline)', '-', def.description || '');
    console.log('Steps:', steps.length);

    for (let i = 0; i < steps.length; i++) {
        try {
            const r = await runStep(steps[i], i + 1, onError);
            results.push({ index: i + 1, ok: true, result: r.plain || r });
        } catch (e) {
            const msg = e.message || String(e);
            console.log('  FAIL step', i + 1, '-', msg);
            results.push({ index: i + 1, ok: false, error: msg });
            if ((steps[i].on_error || onError) === 'stop') {
                return { success: false, failed_at: i + 1, results };
            }
        }
    }
    return { success: true, total: steps.length, results };
}

function listLocalWorkflows() {
    if (!fs.existsSync(WF_DIR)) return [];
    return fs.readdirSync(WF_DIR).filter((f) => f.endsWith('.json')).map((f) => f.replace(/\.json$/, ''));
}

function loadWorkflow(nameOrPath) {
    let filePath = nameOrPath;
    if (!filePath.endsWith('.json')) {
        filePath = path.join(WF_DIR, nameOrPath + '.json');
    }
    if (!fs.existsSync(filePath)) throw new Error('工作流不存在: ' + filePath);
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

async function main() {
    if (args.includes('--list')) {
        const local = listLocalWorkflows();
        console.log('Local workflows:', local.join(', ') || '(none)');
        try {
            const p = await callTool('workflow_list', {});
            console.log('Server:', p.plain || JSON.stringify(p.json));
        } catch (e) {
            console.log('Server workflow_list:', e.message);
        }
        return;
    }

    if (args.includes('--server')) {
        const name = args[args.indexOf('--server') + 1] || 'hello';
        console.log('Server workflow_run:', name);
        const p = await callTool('workflow_run', { name });
        console.log(p.plain || JSON.stringify(p.json, null, 2));
        return;
    }

    let def;
    if (args.includes('--inline')) {
        def = loadWorkflow(args[args.indexOf('--inline') + 1]);
    } else {
        const name = args[0] || 'hello';
        def = loadWorkflow(name);
    }

    const summary = await runWorkflow(def);
    console.log('\n--- Summary ---');
    console.log(JSON.stringify(summary, null, 2));
    process.exit(summary.success ? 0 : 1);
}

main().catch((e) => {
    console.error('Fatal:', e.message);
    process.exit(1);
});
