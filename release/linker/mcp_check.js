#!/usr/bin/env node
/**
 * AI浏览器 MCP 一键自检
 * 用法: node mcp_check.js
 * 退出码 0=成功 1=失败
 */
const { spawn } = require('child_process');
const bridge = require('path').join(__dirname, 'mcp_bridge.js');
const child = spawn(process.execPath, [bridge, '--check'], { stdio: 'inherit', windowsHide: true });
child.on('exit', (code) => process.exit(code == null ? 1 : code));
