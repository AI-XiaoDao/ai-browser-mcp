#!/usr/bin/env node
/** Cursor stdio 握手自检：协议版本、id、schema、工具数量 */
const { spawn } = require('child_process');
const path = require('path');
const lite = (process.env.AI_BROWSER_MCP_CURSOR_MODE || '0') === '1';
const bridge = path.join(__dirname, '..', 'mcp_bridge.js');
const child = spawn(process.execPath, [bridge], {
  stdio: ['pipe', 'pipe', 'pipe'],
  env: { ...process.env, AI_BROWSER_MCP_CURSOR_MODE: lite ? '1' : '0' }
});
const reqs = [
  { jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'cursor-test', version: '1' } } },
  { jsonrpc: '2.0', method: 'notifications/initialized' },
  { jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} }
];
let stdout = '';
child.stdout.on('data', (c) => { stdout += c; });
child.stdin.write(reqs.map((r) => JSON.stringify(r)).join('\n') + '\n');
child.stdin.end();
child.on('close', (code) => {
  try {
    const lines = stdout.trim().split('\n');
    const init = JSON.parse(lines[0]);
    const toolsResp = JSON.parse(lines[lines.length - 1]);
    const bad = toolsResp.result.tools.filter((t) => {
      const walk = (n) => {
        if (!n || typeof n !== 'object') return false;
        if (Array.isArray(n)) return n.some(walk);
        if (n.type === 'text') return true;
        return Object.values(n).some(walk);
      };
      return walk(t.inputSchema);
    });
    const count = toolsResp.result.tools.length;
    const ok = bad.length === 0 && !toolsResp.result._req_id
      && init.id === 1 && toolsResp.id === 2
      && init.result.protocolVersion === '2024-11-05'
      && (lite ? count <= 60 : count >= 200);
    console.log(JSON.stringify({
      ok, lite, tools: count, badSchema: bad.length,
      initId: init.id, toolsId: toolsResp.id,
      protocolVersion: init.result.protocolVersion
    }));
    process.exit(ok ? 0 : 1);
  } catch (e) {
    console.error('verify failed:', e.message);
    process.exit(1);
  }
});
