#!/usr/bin/env node
/**
 * AI浏览器 MCP 冒烟测试 (需 AI浏览器.exe 已启动)
 * 用法: node full_test.js
 * 全量顺序测试: node run_all_tests.js
 */
const http = require('http');
const path = require('path');

const HOST = process.env.AI_BROWSER_MCP_HOST || '127.0.0.1';
const PORT = parseInt(process.env.AI_BROWSER_MCP_PORT || '9222', 10);
const MCP_PATH = '/mcp';

let passed = 0;
let failed = 0;

function postMcp(body) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify(body);
        const req = http.request({
            hostname: HOST,
            port: PORT,
            path: MCP_PATH,
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
        }, (res) => {
            let raw = '';
            res.on('data', (c) => { raw += c; });
            res.on('end', () => {
                try {
                    resolve({ status: res.statusCode, json: JSON.parse(raw) });
                } catch (e) {
                    reject(new Error('非 JSON 响应: ' + raw.slice(0, 200)));
                }
            });
        });
        req.on('error', reject);
        req.setTimeout(30000, () => { req.destroy(); reject(new Error('timeout')); });
        req.write(data);
        req.end();
    });
}

function get(path) {
    return new Promise((resolve, reject) => {
        http.get({ hostname: HOST, port: PORT, path, timeout: 5000 }, (res) => {
            let raw = '';
            res.on('data', (c) => { raw += c; });
            res.on('end', () => resolve({ status: res.statusCode, raw }));
        }).on('error', reject);
    });
}

async function assert(name, fn) {
    try {
        await fn();
        passed++;
        console.log('  OK  ' + name);
    } catch (e) {
        failed++;
        console.log('  FAIL ' + name + ' — ' + (e && e.message ? e.message : e));
    }
}

async function callTool(name, args, id) {
    const res = await postMcp({
        jsonrpc: '2.0',
        id: id || name,
        method: 'tools/call',
        params: { name, arguments: args || {} }
    });
    if (res.status !== 200) throw new Error('HTTP ' + res.status);
    if (res.json.error) throw new Error(res.json.error.message || JSON.stringify(res.json.error));
    return res.json.result;
}

async function main() {
    console.log('AI浏览器 MCP full_test @ ' + HOST + ':' + PORT);

    await assert('GET /health', async () => {
        const h = await get('/health');
        if (h.status !== 200) throw new Error('HTTP ' + h.status);
        const j = JSON.parse(h.raw);
        if (j.status !== 'ok') throw new Error('status != ok');
    });

    await assert('tools/list 数量', async () => {
        const h = await get('/tools/list');
        const j = JSON.parse(h.raw);
        if (!Array.isArray(j.tools) || j.tools.length < 100) {
            throw new Error('tools 数量异常: ' + (j.tools && j.tools.length));
        }
    });

    await assert('ping', async () => {
        const r = await callTool('ping', {});
        const text = JSON.stringify(r);
        if (text.indexOf('pong') === -1 && text.indexOf('success') === -1) {
            throw new Error('unexpected: ' + text.slice(0, 120));
        }
    });

    await assert('browser_get_url', async () => {
        await callTool('browser_get_url', {});
    });

    await assert('batch JSON 数组', async () => {
        const r = await callTool('batch', {
            commands: [{ name: 'browser_get_url', arguments: {} }]
        });
        const text = JSON.stringify(r);
        if (text.indexOf('failure_count') !== -1 && text.indexOf('failure_count":0') === -1 && text.indexOf('failure_count\\":0') === -1) {
            throw new Error(text.slice(0, 200));
        }
        if (text.indexOf('success_count') === -1 && text.indexOf('"success":true') === -1) {
            throw new Error('batch 无成功标记: ' + text.slice(0, 200));
        }
    });

    await assert('browser_list', async () => {
        await callTool('browser_list', {});
    });

    await assert('mcp_status', async () => {
        await callTool('mcp_status', {});
    });

    console.log('\n结果: ' + passed + ' 通过, ' + failed + ' 失败');
    process.exit(failed > 0 ? 1 : 0);
}

main().catch((e) => {
    console.error('测试中止:', e.message || e);
    console.error('请先启动 AI浏览器.exe');
    process.exit(1);
});
