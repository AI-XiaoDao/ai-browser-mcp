#!/usr/bin/env node
/**
 * MCP Launcher — 通过 Node.js 启动/停止 AI-Fbowser-Mcp.exe
 *
 * 用法:
 *   node mcp_launcher.js start              # 启动浏览器
 *   node mcp_launcher.js stop               # 通过 MCP 安全关闭
 *   node mcp_launcher.js stop --force       # 强制杀进程
 *   node mcp_launcher.js restart            # 重启
 *   node mcp_launcher.js status             # 检查运行状态
 *   node mcp_launcher.js health             # 健康检查
 *   node mcp_launcher.js --wait             # 启动并等待就绪后退出
 *
 * 环境变量:
 *   AI_BROWSER_EXE_PATH    exe路径 (默认: ./AI浏览器.exe)
 *   AI_BROWSER_MCP_HOST    绑定地址 (默认: 127.0.0.1)
 *   AI_BROWSER_MCP_PORT    端口 (默认: 9222)
 *   AI_BROWSER_STARTUP_MS  启动超时ms (默认: 30000)
 */

const { spawn, execSync } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

// ── 配置 ──
const HOST = process.env.AI_BROWSER_MCP_HOST || '127.0.0.1';
const PORT = parseInt(process.env.AI_BROWSER_MCP_PORT || '9222', 10);
const EXE_PATH = process.env.AI_BROWSER_EXE_PATH || findExe();
const STARTUP_TIMEOUT = parseInt(process.env.AI_BROWSER_STARTUP_MS || '30000', 10);
const HEALTH_URL = `http://${HOST}:${PORT}/health`;
const MCP_URL = `http://${HOST}:${PORT}/mcp`;
const PID_FILE = path.join(__dirname, '.ai_browser.pid');

// ── 查找 exe ──
function findExe() {
    const candidates = [
        path.join(__dirname, 'AI-Fbowser-Mcp.exe'),
        path.join(__dirname, '_int', 'AI浏览器', 'debug', 'x64', 'linker', 'AI-Fbowser-Mcp.exe'),
        path.join(__dirname, '_int', 'AI浏览器', 'release', 'x64', 'linker', 'AI-Fbowser-Mcp.exe'),
    ];
    for (const p of candidates) {
        if (fs.existsSync(p)) return p;
    }
    // fallback: search linker directory
    const base = path.resolve(__dirname, '..', '..');
    const results = findFiles(base, 'AI-Fbowser-Mcp.exe');
    return results[0] || 'AI-Fbowser-Mcp.exe';
}

function findFiles(dir, name) {
    const results = [];
    try {
        for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
            if (entry.isDirectory() && entry.name !== 'node_modules' && !entry.name.startsWith('.')) {
                results.push(...findFiles(path.join(dir, entry.name), name));
            } else if (entry.name === name) {
                results.push(path.join(dir, entry.name));
            }
        }
    } catch (_) { /* skip inaccessible dirs */ }
    return results;
}

// ── HTTP 请求 ──
function httpPost(body, timeout = 10000) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify(body);
        const req = http.request(MCP_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) },
            timeout,
        }, (res) => {
            let buf = '';
            res.on('data', (c) => buf += c);
            res.on('end', () => {
                try { resolve(JSON.parse(buf)); } catch (_) { resolve(buf); }
            });
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
        req.write(data);
        req.end();
    });
}

function healthCheck(timeout = 5000) {
    return new Promise((resolve) => {
        const req = http.get(HEALTH_URL, { timeout }, (res) => {
            let buf = '';
            res.on('data', (c) => buf += c);
            res.on('end', () => {
                try { resolve(JSON.parse(buf)); } catch (_) { resolve(null); }
            });
        });
        req.on('error', () => resolve(null));
        req.on('timeout', () => { req.destroy(); resolve(null); });
    });
}

// ── 等待就绪 ──
async function waitForReady(timeoutMs = STARTUP_TIMEOUT) {
    const start = Date.now();
    process.stdout.write('等待 AI浏览器 就绪');
    while (Date.now() - start < timeoutMs) {
        const health = await healthCheck(3000);
        if (health && health.status === 'ok' && health.browsers >= 0) {
            process.stdout.write(' ✓\n');
            return health;
        }
        process.stdout.write('.');
        await sleep(1000);
    }
    process.stdout.write(' ✗\n');
    return null;
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

// ── 保存 / 读取 PID ──
function savePid(pid) {
    try { fs.writeFileSync(PID_FILE, String(pid)); } catch (_) {}
}
function readPid() {
    try { return parseInt(fs.readFileSync(PID_FILE, 'utf8'), 10); } catch (_) { return 0; }
}
function deletePid() {
    try { fs.unlinkSync(PID_FILE); } catch (_) {}
}

function isProcessRunning(pid) {
    try {
        if (os.platform() === 'win32') {
            // tasklist 即使未匹配到任何进程也返回 exit code 0,
            // 所以需要解析输出判断 PID 是否真实存在
            const out = execSync(`tasklist /NH /FI "PID eq ${pid}"`, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
            return out.includes(String(pid));
        }
        process.kill(pid, 0);
        return true;
    } catch (_) {
        return false;
    }
}

// ── 启动 ──
async function start() {
    // 检查是否已运行
    const existing = await healthCheck(2000);
    if (existing && existing.status === 'ok') {
        console.log(`AI浏览器 已在运行: ${HEALTH_URL}`);
        console.log(`  browsers: ${existing.browsers}, uptime: ${Math.round(existing.uptime_ms / 1000)}s`);
        return existing;
    }

    // 检查残留PID
    const oldPid = readPid();
    if (oldPid && isProcessRunning(oldPid)) {
        console.log(`检测到运行中的进程 PID=${oldPid}, 等待健康检查...`);
        const health = await waitForReady(10000);
        if (health) return health;
    }
    deletePid();

    console.log(`启动: ${EXE_PATH}`);
    const args = process.argv.includes('--headless') ? ['--headless'] : [];
    const child = spawn(EXE_PATH, args, {
        detached: false,
        stdio: ['ignore', 'pipe', 'pipe'],
        windowsHide: false,
    });

    child.on('error', (err) => {
        console.error('启动失败:', err.message);
        process.exit(1);
    });

    child.stdout?.on('data', (d) => process.stdout.write(`[exe] ${d}`));
    child.stderr?.on('data', (d) => process.stderr.write(`[exe-err] ${d}`));

    savePid(child.pid);
    console.log(`PID: ${child.pid}`);

    const health = await waitForReady();
    if (health) {
        console.log(`就绪: v${health.version}, browsers=${health.browsers}, port=${PORT}`);
        console.log(`MCP: ${MCP_URL}`);
        console.log(`PID文件: ${PID_FILE}`);
    } else {
        console.error('启动超时! 请检查 AI浏览器.exe 是否正常');
        // 杀掉孤儿子进程, 防止其成为不可追踪的僵尸进程
        try { child.kill(); } catch (_) {}
        deletePid();
        process.exit(1);
    }

    return health;
}

// ── 停止 ──
async function stop(force = false) {
    if (force) {
        const pid = readPid();
        if (pid && isProcessRunning(pid)) {
            console.log(`强制终止 PID=${pid}`);
            try { process.kill(pid, 'SIGTERM'); } catch (_) {
                try { execSync(`taskkill /PID ${pid} /F 2>nul`, { stdio: 'ignore' }); } catch (__) {}
            }
            await sleep(2000);
            if (isProcessRunning(pid)) {
                try { execSync(`taskkill /F /PID ${pid} 2>nul`, { stdio: 'ignore' }); } catch (_) {}
            }
        }
        deletePid();
        return;
    }

    // 优雅关闭: 通过 MCP 工具
    const health = await healthCheck(2000);
    if (!health || health.status !== 'ok') {
        console.log('AI浏览器 未运行');
        deletePid();
        return;
    }

    try {
        console.log('发送 browser_shutdown...');
        const res = await httpPost({
            jsonrpc: '2.0',
            id: 'launcher_stop',
            method: 'tools/call',
            params: { name: 'browser_shutdown', arguments: { confirm: true, delay_seconds: 1 } }
        }, 5000);
        const text = res?.result?.content?.[0]?.text || JSON.stringify(res);
        console.log('  →', text);
    } catch (e) {
        console.error('MCP关闭失败, 尝试强制终止:', e.message);
        await stop(true);
    }

    await sleep(3000);
    deletePid();

    // 确认已停止
    const postCheck = await healthCheck(2000);
    if (!postCheck) {
        console.log('AI浏览器 已停止');
    } else {
        console.log('进程可能仍在运行, 请用 --force 强制终止');
    }
}

// ── 重启 ──
async function restart() {
    await stop();
    await sleep(2000);
    await start();
}

// ── 状态 ──
async function status() {
    const health = await healthCheck(2000);
    if (health && health.status === 'ok') {
        console.log('状态: 运行中');
        console.log(`  版本: ${health.version}`);
        console.log(`  浏览器: ${health.browsers}`);
        console.log(`  运行时间: ${Math.round(health.uptime_ms / 1000)}s`);
        console.log(`  速率限制: ${health.rate_limit_per_min || 0}/min (已用: ${health.rate_limit_used || 0})`);
        console.log(`  异步任务: ${health.async_tasks || 0}`);
        console.log(`  MCP: ${MCP_URL}`);
        const pid = readPid();
        if (pid) console.log(`  PID: ${pid}`);
    } else {
        console.log('状态: 未运行');
        const pid = readPid();
        if (pid && isProcessRunning(pid)) {
            console.log(`  发现残留进程 PID=${pid}, 但健康检查失败`);
        }
    }
}

// ── CLI ──
async function main() {
    const cmd = process.argv[2] || 'status';
    const force = process.argv.includes('--force');
    const waitMode = process.argv.includes('--wait');

    switch (cmd) {
        case 'start':
            await start();
            if (waitMode) {
                // --wait 模式: 启动后就绪后直接退出
                process.exit(0);
            }
            // 保持运行; Ctrl+C 时优雅关闭
            console.log('\n按 Ctrl+C 停止...');
            process.on('SIGINT', async () => {
                console.log('\n正在关闭...');
                await stop();
                process.exit(0);
            });
            process.on('SIGTERM', async () => {
                console.log('\n收到SIGTERM, 正在关闭...');
                await stop();
                process.exit(0);
            });
            // 保持进程存活 (不占用CPU)
            process.stdin.resume();
            break;
        case 'stop':
            await stop(force);
            break;
        case 'restart':
            await restart();
            break;
        case 'status':
            await status();
            break;
        case 'health':
            const h = await healthCheck();
            console.log(h ? JSON.stringify(h, null, 2) : '未运行');
            break;
        default:
            console.log('用法: node mcp_launcher.js <start|stop|restart|status|health>');
            console.log('  start      启动 AI浏览器.exe');
            console.log('  stop       通过 MCP 安全关闭');
            console.log('  stop --force  强制杀进程');
            console.log('  restart    重启');
            console.log('  status     查看运行状态');
            console.log('  health     健康检查JSON');
            console.log('  --wait     启动后等待就绪即退出');
            console.log('  --headless 无窗口模式启动');
            process.exit(1);
    }
}

main().catch((e) => { console.error(e); process.exit(1); });
