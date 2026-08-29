#!/usr/bin/env node
// 模拟修复后生成路径: 描述经 JSON 转义后拼接, 校验 tools/list 全部条目合法
const fs = require('fs');
const lines = fs.readFileSync('C:\\Users\\cxzxc\\Desktop\\MCP源码\\ai-browser-mcp\\CEFbro\\AI-Fbowser-Mcp\\src\\MCP_Server.wsv', 'utf8').split(/\r?\n/);
function decodeVolString(src) {
  let i = src.indexOf('"');
  if (i < 0) return null;
  i++; let out = '';
  while (i < src.length) {
    const c = src[i];
    if (c === '\\' && i + 1 < src.length) {
      const n = src[i + 1];
      if (n === '"') { out += '"'; i += 2; continue; }
      if (n === '\\') { out += '\\'; i += 2; continue; }
      out += c; i++; continue;
    }
    if (c === '"') break;
    out += c; i++;
  }
  return out;
}
// 模拟 MCP_响应构建.JSON转义文本 (JSON 标准转义 + 控制符)
function escapeJson(s) {
  return JSON.stringify(String(s)).slice(1, -1);
}
function splitTopLevel(s) {
  const parts = []; let depth = 0, cur = '';
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === '(') depth++;
    if (c === ')') depth--;
    if (c === ',' && depth === 0) { parts.push(cur.trim()); cur = ''; continue; }
    cur += c;
  }
  if (cur.trim()) parts.push(cur.trim());
  return parts;
}
function decodeProps(text) {
  let out = '';
  const re = /属性项JSON \(([^)]*)\)/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const args = splitTopLevel(m[1]);
    if (args.length >= 3) {
      const name = escapeJson(decodeVolString(args[0]));
      const type = escapeJson(decodeVolString(args[1]));
      const desc = escapeJson(decodeVolString(args[2]));
      if (out) out += ',';
      out += '"' + name + '":{"type":"' + type + '","description":"' + desc + '"}';
    }
  }
  return out;
}
function decodeReq(text) {
  if (!text) return '';
  return splitTopLevel(text).map(p => '"' + escapeJson(decodeVolString(p)) + '"').join(',');
}
let ok = 0, bad = 0, badLines = [];
for (let li = 0; li < lines.length; li++) {
  const line = lines[li];
  if (!line.includes('添加工具JSON')) continue;
  const m = line.match(/添加工具JSON \(([^,]+),\s*("[^"]*(?:\\"[^"]*)*")\s*,\s*(.+)\)\s*$/);
  if (!m) continue;
  const toolName = decodeVolString(m[1].trim());
  const toolDesc = decodeVolString(m[2].trim());
  const schemaArg = m[3].trim();
  let schemaJson = null;
  if (schemaArg.startsWith('多属性Schema文本')) {
    const inner = schemaArg.slice('多属性Schema文本'.length).replace(/^\(/, '').replace(/\)$/, '');
    const parts = splitTopLevel(inner);
    if (parts.length >= 1) {
      const propsJson = decodeProps(parts[0]);
      const reqJson = parts.length > 1 ? decodeReq(parts[1]) : '';
      schemaJson = '"inputSchema":{"type":"object","properties":{' + propsJson + '}' + (reqJson ? ',"required":[' + reqJson + ']' : '') + '}';
    }
  } else if (schemaArg.startsWith('单参数Schema文本')) {
    const inner = schemaArg.slice('单参数Schema文本'.length).replace(/^\(/, '').replace(/\)$/, '');
    const parts = splitTopLevel(inner);
    if (parts.length >= 2) {
      const name = escapeJson(decodeVolString(parts[0]));
      const type = escapeJson(decodeVolString(parts[1]));
      const desc = escapeJson(decodeVolString(parts[2] || '""'));
      const must = parts.length > 3 ? parts[3].trim() : '真';
      schemaJson = '"inputSchema":{"type":"object","properties":{"' + name + '":{"type":"' + type + '","description":"' + desc + '"}}' + (must !== '假' ? ',"required":["' + name + '"]' : '') + '}';
    }
  } else if (schemaArg.startsWith('空Schema文本')) {
    schemaJson = '"inputSchema":{"type":"object"}';
  } else if (schemaArg.startsWith('双XY_Schema文本')) {
    schemaJson = '"inputSchema":{"type":"object","properties":{"x":{"type":"integer","description":""},"y":{"type":"integer","description":""}},"required":["x","y"]}';
  }
  if (schemaJson) {
    // 完整工具条目: {"name":...,"description":...,"inputSchema":...}
    const entry = '{"name":"' + escapeJson(toolName) + '","description":"' + escapeJson(toolDesc) + '",' + schemaJson + '}';
    try {
      JSON.parse(entry);
      ok++;
    } catch (e) {
      bad++;
      badLines.push('L' + (li + 1) + ' ' + toolName + ': ' + e.message + ' | ' + entry.slice(0, 150));
    }
  }
}
console.log('工具条目校验(含转义): 合法 ' + ok + ' 个, 非法 ' + bad + ' 个');
if (badLines.length) console.log(badLines.slice(0, 6).join('\n'));
