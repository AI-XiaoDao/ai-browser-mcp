#!/usr/bin/env node
/**
 * AI浏览器 MCP — 全量测试编排（必须顺序执行，勿并行）
 *
 * 单浏览器实例 + MCP 全局锁：tool_test / scenario / workflow 会改页面状态，
 * 并行跑会导致 fixture 注入失败、标题错乱等假失败。
 *
 * 用法:
 *   node run_all_tests.js              # 完整套件（约 60–90s）
 *   node run_all_tests.js --quick      # 仅 regression + full_test（约 5s）
 *   node run_all_tests.js --no-tools   # 跳过 217 工具注册表冒烟
 *   node run_all_tests.js --continue   # 某步失败后继续（默认 fail-fast）
 *
 * 卡死恢复: run_all_tests 内置 unfreeze（mcp_client.unfreezeBrowser）
 *
 * 环境: AI_BROWSER_MCP_HOST / AI_BROWSER_MCP_PORT
 * 前置: AI浏览器.exe 已启动
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { unfreezeBrowser } = require('./mcp_client');

const HOST = process.env.AI_BROWSER_MCP_HOST || '127.0.0.1';
const PORT = parseInt(process.env.AI_BROWSER_MCP_PORT || '9222', 10);
const ROOT = __dirname;
const REPORT = path.join(ROOT, 'run_all_tests_report.json');

const args = process.argv.slice(2);
const QUICK = args.includes('--quick');
const NO_TOOLS = args.includes('--no-tools');
const NO_SCENARIO = args.includes('--no-scenario');
const NO_WORKFLOW = args.includes('--no-workflow');
const CONTINUE = args.includes('--continue');

const ALL_STEPS = [
    { id: 'regression', name: '专项回归 sync-wait/workflow', script: 'regression_sync_wait.js', args: [], group: 'core' },
    { id: 'smoke', name: 'HTTP 冒烟', script: 'full_test.js', args: [], group: 'core' },
    { id: 'tools', name: '217 工具注册表冒烟', script: 'tool_test_all.js', args: [], group: 'tools' },
    { id: 'scenario', name: '场景集成测试', script: 'scenario_test.js', args: ['--skip-vip'], group: 'scenario' },
    { id: 'workflow_hello', name: '工作流 hello', script: 'workflow_runner.js', args: ['--server', 'hello'], group: 'workflow' },
    { id: 'workflow_ping', name: '工作流 ping_navigate', script: 'workflow_runner.js', args: ['--server', 'ping_navigate'], group: 'workflow' },
    { id: 'workflow_auto', name: '工作流 automation_form', script: 'workflow_runner.js', args: ['--server', 'automation_form'], group: 'workflow' },
];

function pickSteps() {
    if (QUICK) {
        return ALL_STEPS.filter((s) => s.group === 'core');
    }
    return ALL_STEPS.filter((s) => {
        if (NO_TOOLS && s.group === 'tools') return false;
        if (NO_SCENARIO && s.group === 'scenario') return false;
        if (NO_WORKFLOW && s.group === 'workflow') return false;
        return true;
    });
}

function checkHealth() {
    return new Promise((resolve, reject) => {
        const req = http.get({ hostname: HOST, port: PORT, path: '/health', timeout: 5000 }, (res) => {
            let raw = '';
            res.on('data', (c) => { raw += c; });
            res.on('end', () => {
                try {
                    const j = JSON.parse(raw);
                    if (j.status !== 'ok') return reject(new Error('health status=' + j.status));
                    if ((j.browsers || 0) < 1) return reject(new Error('browsers=0，请先启动 AI浏览器.exe'));
                    resolve(j);
                } catch (e) {
                    reject(new Error('health 非 JSON: ' + raw.slice(0, 120)));
                }
            });
        });
        req.on('error', (e) => reject(new Error('无法连接 MCP ' + HOST + ':' + PORT + ' — ' + e.message)));
        req.on('timeout', () => { req.destroy(); reject(new Error('health 超时')); });
    });
}

function runStep(step, index, total) {
    const scriptPath = path.join(ROOT, step.script);
    if (!fs.existsSync(scriptPath)) {
        return Promise.reject(new Error('脚本不存在: ' + step.script));
    }

    const t0 = Date.now();
    const cmdLine = 'node ' + step.script + (step.args.length ? ' ' + step.args.join(' ') : '');

    console.log('\n' + '─'.repeat(64));
    console.log(`[${index}/${total}] ${step.name}`);
    console.log(`      ${cmdLine}`);
    console.log('─'.repeat(64));

    return new Promise((resolve, reject) => {
        const child = spawn(process.execPath, [scriptPath, ...step.args], {
            cwd: ROOT,
            env: process.env,
            stdio: 'inherit',
            windowsHide: true,
        });

        child.on('error', (err) => reject(err));

        child.on('close', (code) => {
            const ms = Date.now() - t0;
            const result = { id: step.id, name: step.name, script: step.script, args: step.args, ms, exitCode: code ?? -1, ok: code === 0 };
            if (code === 0) resolve(result);
            else reject(Object.assign(new Error(step.name + ' 失败 (exit ' + code + ')'), { result }));
        });
    });
}

function formatMs(ms) {
    if (ms < 1000) return ms + 'ms';
    return (ms / 1000).toFixed(1) + 's';
}

async function main() {
    const steps = pickSteps();
    const started = new Date();
    const results = [];

    console.log('AI浏览器 MCP 全量测试 @ ' + HOST + ':' + PORT);
    console.log('模式: ' + (QUICK ? 'quick' : 'full') +
        (NO_TOOLS ? ' no-tools' : '') +
        (NO_SCENARIO ? ' no-scenario' : '') +
        (NO_WORKFLOW ? ' no-workflow' : '') +
        (CONTINUE ? ' continue-on-fail' : ' fail-fast'));
    console.log('步骤: ' + steps.map((s) => s.id).join(' → '));
    console.log('注意: 单浏览器实例，各套件必须顺序执行，勿与别的测试脚本并行\n');

    let health;
    try {
        health = await checkHealth();
        console.log('health OK — version ' + (health.version || '?') + ', browsers=' + health.browsers);
    } catch (e) {
        console.error('\n前置检查失败: ' + e.message);
        console.error('请先启动 AI浏览器.exe 并确认 MCP 端口 ' + PORT);
        process.exit(2);
    }

    console.log('\n[preflight] 解除可能遗留的 debugger 暂停…');
    try {
        await unfreezeBrowser();
    } catch (e) {
        console.warn('[preflight] unfreeze 警告:', e.message);
    }

    let failed = false;
    try {
    for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        try {
            const r = await runStep(step, i + 1, steps.length);
            results.push(r);
            console.log(`\n✓ ${step.name} (${formatMs(r.ms)})`);
            if (step.id === 'tools') {
                try { await unfreezeBrowser(); } catch (_) {}
            }
        } catch (e) {
            const r = e.result || { id: step.id, name: step.name, script: step.script, ms: 0, exitCode: 1, ok: false, error: e.message };
            results.push(r);
            failed = true;
            console.error(`\n✗ ${step.name} — ${e.message}`);
            try { await unfreezeBrowser(); } catch (_) {}
            if (!CONTINUE) break;
        }
    }
    } finally {
        console.log('\n[cleanup] 测试结束，解除 debugger 暂停…');
        try { await unfreezeBrowser(); } catch (e) { console.warn('[cleanup]', e.message); }
    }

    const totalMs = Date.now() - started.getTime();
    const passed = results.filter((r) => r.ok).length;

    console.log('\n' + '='.repeat(64));
    console.log('全量测试汇总');
    console.log('='.repeat(64));
    for (const r of results) {
        console.log(`  ${r.ok ? 'PASS' : 'FAIL'}  ${r.name.padEnd(28)} ${formatMs(r.ms)}`);
    }
    if (results.length < steps.length) {
        const skipped = steps.slice(results.length);
        for (const s of skipped) {
            console.log(`  SKIP  ${s.name.padEnd(28)} (未执行)`);
        }
    }
    console.log('─'.repeat(64));
    console.log(`合计: ${passed}/${steps.length} 步通过, 总耗时 ${formatMs(totalMs)}`);

    const report = {
        time: started.toISOString(),
        host: HOST + ':' + PORT,
        health,
        mode: { quick: QUICK, noTools: NO_TOOLS, noScenario: NO_SCENARIO, noWorkflow: NO_WORKFLOW, continueOnFail: CONTINUE },
        steps: steps.map((s) => s.id),
        results,
        passed,
        total: steps.length,
        totalMs,
        success: !failed && passed === steps.length,
    };
    fs.writeFileSync(REPORT, JSON.stringify(report, null, 2), 'utf8');
    console.log('报告: ' + REPORT);

    process.exit(failed || passed < steps.length ? 1 : 0);
}

main().catch((e) => {
    console.error('run_all_tests 中止:', e.message || e);
    process.exit(1);
});
