// 只读: 在 Node 里用桩 window 复现注入 JS 的解析/运行行为, 证明根因链
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync('_audit/_revfunc_runtime.js', 'utf8');

// ---- 桩 window: 覆盖工具枚举的 9 个对象链 + 22 个类 ----
const protoWithBadGetter = {};
Object.defineProperty(protoWithBadGetter, 'body', {
  get() { if (!(this instanceof protoWithBadGetter)) throw new TypeError('Illegal invocation'); return 1; },
  enumerable: false, configurable: true,
});
function FakeResponse() {}
FakeResponse.prototype = protoWithBadGetter;

const win = {
  alphaFn: function alphaFn(a, b) {},
  betaFn: function betaFn() {},
  location: { href: 'about:blank', reload: function () {} },
  navigator: { userAgent: 'x', sendBeacon: function () {} },
  document: { title: 't', write: function () {} },
  history: { back: function () {} },
  crypto: { getRandomValues: function () {} },
  performance: { now: function () {} },
  console: { log: function () {} },
  XMLHttpRequest: function XMLHttpRequest() {},
  WebSocket: function WebSocket() {},
  Promise: Promise,
  Map: Map, Set: Set, Array: Array, Object: Object, String: String, Number: Number,
  Date: Date, RegExp: RegExp, JSON: JSON, WebAssembly: { compile: function () {} },
  URL: URL, Blob: function Blob() {}, FileReader: function FileReader() {},
  FormData: function FormData() {}, Headers: function Headers() {},
  Request: function Request() {}, Response: FakeResponse,
  AbortController: function AbortController() {},
  IntersectionObserver: function IntersectionObserver() {},
  MutationObserver: function MutationObserver() {},
  ResizeObserver: function ResizeObserver() {},
};
// localStorage 访问即抛 SecurityError (模拟禁 cookie/沙箱页面)
Object.defineProperty(win, 'localStorage', {
  get() { throw new Error("SecurityError: Failed to read the 'localStorage' property from 'Window': Access is denied for this document."); },
  enumerable: true, configurable: true,
});
Object.defineProperty(win, 'sessionStorage', {
  get() { throw new Error("SecurityError: Failed to read the 'sessionStorage' property"); },
  enumerable: true, configurable: true,
});
// 一个属性是"抛异常的 getter"的 window 自有属性
Object.defineProperty(win, 'badGetter', {
  get() { throw new Error('boom from throwing getter'); }, enumerable: true, configurable: true,
});

const sandbox = { window: win, console };
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

function run(name, code) {
  try {
    const r = new vm.Script(code).runInContext(sandbox, { timeout: 5000 });
    let n = -1, sample = '';
    try { const arr = JSON.parse(r); n = arr.length; sample = JSON.stringify(arr.slice(0, 3)); } catch (e) { sample = String(r).slice(0, 120); }
    console.log('RUN OK  ', name, '| count=' + n, '| sample=' + sample);
  } catch (e) {
    console.log('RUN FAIL', name, '=>', e.constructor.name + ': ' + e.message);
  }
}

// 变体 1: 原样
run('V1 原始(单行)', src);

// 变体 2: 仅在 return 前插入换行 (触发 ASI)
const iRet = src.indexOf(')return out.slice');
run('V2 只在 return 前插换行', src.slice(0, iRet + 1) + '\n' + src.slice(iRet + 1));

// 变体 3: 只在 return 前插入分号
run('V3 只在 return 前插分号', src.slice(0, iRet + 1) + ';' + src.slice(iRet + 1));

// 变体 4: 两处都插入分号 (真正修复)
const iCls = src.indexOf("})['XMLHttpRequest'");
run('V4 两处都插分号', src.slice(0, iCls + 2) + ';' + src.slice(iCls + 2, iRet + 1) + ';' + src.slice(iRet + 1));
console.log('boundary context @iCls:', JSON.stringify(src.slice(iCls - 20, iCls + 30)));
console.log('boundary context @iRet:', JSON.stringify(src.slice(iRet - 20, iRet + 30)));
