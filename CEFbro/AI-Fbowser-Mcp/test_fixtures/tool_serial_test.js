// 串行测试: 255 工具逐个调用, 带节奏间隔与充分超时 (消除重载干扰, 与并行sweep互补)
const http = require('http');
const fs = require('fs');
const HOST = '127.0.0.1', PORT = 9222;
const WELCOME = 'http://127.0.0.1:9222/';

const SKIP = new Set([
  'browser_shutdown', 'browser_close', 'browser_close_try', 'browser_create',
  'browser_clear_cache', 'browser_clear_cache_browser',
  'browser_set_proxy', 'browser_clear_proxy',
  'browser_set_cookie', 'browser_delete_cookies',
  'browser_start_download', 'browser_download_image',
  'browser_print', 'browser_print_to_pdf',
  'browser_open_devtools', 'browser_close_devtools',
  'browser_file_dialog',
  'browser_edit_cut', 'browser_edit_copy', 'browser_edit_paste',
  'browser_set_parent', 'browser_set_window_style',
  'browser_set_preference', 'browser_inject',
  'browser_find', 'browser_stop_find',
  'browser_vip_load_extension', 'browser_vip_unload_extension', 'browser_vip_extension_info',
  'browser_vip_send_devtools_msg', 'browser_vip_disable_debugger',
  'browser_vip_websocket_intercept', 'browser_vip_enable_js_env', 'browser_vip_set_is_trusted',
  'browser_vip_enable_inspector', 'browser_vip_enable_devtools_observer', 'browser_vip_disable_console',
  'browser_vip_execute_js_context',
  'browser_debugger_set_breakpoint', 'browser_debugger_flow', 'browser_debugger_auto',
  'browser_debugger_wait_paused',
  'workflow_run', 'workflow_stop',
  'browser_fingerprint_appname', 'browser_fingerprint_pixel_ratio',
  'browser_fingerprint_cookie_enabled', 'browser_fingerprint_java_enabled',
  'browser_fingerprint_online', 'browser_fingerprint_appcodename',
  'browser_fingerprint_appversion', 'browser_fingerprint_product_sub',
  'browser_fingerprint_vendor_sub', 'browser_fingerprint_screen_xy',
  'browser_vip_set_css_version', 'browser_vip_set_web_version', 'browser_vip_set_v8_version',
  'browser_vip_fingerprint_canvas_fixed', 'browser_vip_fingerprint_webgl_fixed',
  'browser_vip_fingerprint_audio_fixed',
  'browser_vip_mouse_press', 'browser_vip_mouse_release', 'browser_vip_key_input', 'browser_vip_key_type',
]);

const OVERRIDE = {
  'browser_navigate': { url: WELCOME, max_ms: 8000 },
  'browser_click_text': { text: 'zzz不存在的文本zzz' },
  'browser_dom_click': { selector: 'body' },
  'browser_dom_set_value': { selector: 'input', value: 'x' },
  'browser_highlight': { selector: 'body', duration_ms: 300 },
  'browser_console_eval': { expression: '1+1' },
  'browser_base64_encode': { data: 'hello' },
  'browser_base64_decode': { data: 'aGVsbG8=' },
  'browser_uri_encode': { data: 'hello world' },
  'browser_uri_decode': { data: 'hello%20world' },
  'browser_set_zoom': { level: 1.0 },
  'browser_set_mute': { mute: false },
  'browser_set_focus': { focus: true },
  'browser_cdp_call': { method: 'Browser.getVersion' },
  'browser_mouse_move': { x: 10, y: 10 },
  'browser_mouse_click': { x: 10, y: 10 },
  'browser_mouse_wheel': { x: 10, y: 10 },
  'browser_key_event': { key_code: 65 },
  'browser_touch_press': { x: 10, y: 10 },
  'browser_touch_release': { x: 10, y: 10 },
  'browser_touch_move': { x: 20, y: 20 },
  'browser_scrape': { url: WELCOME },
  'browser_frame_by_name': { name: 'main' },
  'browser_is_same': { other_id: -1 },
  'browser_find_by_tag': { tag: 'none' },
  'browser_find_by_hwnd': { hwnd: 0 },
  'browser_send_message': { name: 'ping' },
  'browser_ipc_send_all': { name: 'ping' },
  'browser_ipc_send_to': { process_id: -1, name: 'ping' },
  'browser_create_url_request': { url: WELCOME },
  'browser_fill_click': { selector: 'body' },
  'browser_fill_focus': { selector: 'body' },
  'browser_fill_scroll': { selector: 'body' },
  'browser_fill_exists': { selector: 'body' },
  'browser_fill_trigger': { selector: 'body' },
  'browser_fill_select': { selector: 'body' },
  'browser_fill_attr_get': { selector: 'body', attribute: 'id' },
  'browser_fill_attr_set': { selector: 'body', attribute: 'id', value: 'x' },
  'browser_fill_set_value': { selector: 'input', value: 'x' },
  'browser_dom_query': { selector: 'body' },
  'browser_dom_rect': { selector: 'body' },
  'browser_dom_inner_html': { selector: 'body' },
  'browser_dom_get_html': {},
  'browser_dom_checked': { selector: 'input' },
  'browser_dom_selected': { selector: 'select' },
  'browser_dom_select': { selector: 'body' },
  'browser_get_text': { selector: 'body' },
  'browser_get_source': { max_chars: 2000 },
  'browser_snapshot': { max_items: 5 },
  'browser_element_action': { index: 0, action: 'get_value' },
  'browser_extract': { type: 'links' },
  'browser_event': { limit: 3 },
  'browser_network': { action: 'list' },
  'browser_collect': { action: 'console_get', limit: 5 },
  'browser_intercept': { action: 'clear' },
  'browser_wait': { what: 'timeout', max_ms: 1000 },
  'browser_fingerprint': { action: 'count' },
  'browser_debugger_evaluate': { call_frame_id: '0', expression: '1+1' },
  'browser_debugger_inspect': { expressions: 'document.title' },
  'browser_vip_dom_get_document': { max_items: 3 },
  'browser_vip_dom_search': { selector: 'body' },
  'browser_vip_orientation': {},
  'browser_vip_touch_emulation': {},
  'mcp_result': { request_id: 'task_nonexistent_test' },
  'mcp_help': {},
  'batch': { commands: [{ name: 'ping', arguments: {} }, { name: 'browser_get_url', arguments: {} }] },
};

function postMcp(body, timeoutMs) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = http.request({hostname: HOST, port: PORT, path: '/mcp', method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }},
      res => { let raw=''; res.on('data',c=>raw+=c); res.on('end',()=>{ try { resolve(JSON.parse(raw)); } catch(e){ resolve({_raw:raw.slice(0,120)}); } }); });
    req.on('error', e => reject(e));
    req.setTimeout(timeoutMs || 30000, () => { req.destroy(); reject(new Error('TIMEOUT')); });
    req.write(data); req.end();
  });
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

function buildArgs(tool, name) {
  if (OVERRIDE[name] !== undefined) return Object.assign({}, OVERRIDE[name]);
  const schema = tool.inputSchema || {};
  const props = schema.properties || {};
  const args = {};
  const names = Object.keys(props);
  const req = Array.isArray(schema.required) ? schema.required : names.filter(k => k !== 'async_only' && k !== 'max_ms' && k !== 'wait_for_load');
  const DEFAULTS = {
    url: WELCOME, selector: 'body', text: 'test', data: 'test', name: 'test', value: 'test',
    html: '<b>x</b>', expression: '1+1', code: '1+1', action: 'get', type: 'links',
    what: 'load', method: 'Browser.getVersion', breakpoint: 'test', request_id: 'task_test_none',
    process_id: -1, other_id: -1, tag: 'test', hwnd: 0, address: '127.0.0.1:1080',
    confirm: 'yes', level: 1, key_code: 65, char_code: 65, x: 10, y: 10,
    enable: false, disable: false, mute: false, focus: true, style: 0, version: 'test',
    crx_path: 'none.crx', extension_id: 'none', lat: 0, lng: 0, json: '{}',
    index: 0, max_items: 3, duration_ms: 300,
  };
  for (const k of req) {
    if (k === 'commands') { args[k] = [{ name: 'ping', arguments: {} }]; continue; }
    args[k] = DEFAULTS[k] !== undefined ? DEFAULTS[k] : 'test';
  }
  return args;
}

const KNOWN_ROUTED = new Set(['browser_dom_checked', 'browser_dom_selected']);

function classify(name, res, ms) {
  if (res._raw) return { verdict: 'FAIL', detail: '非JSON响应' };
  if (res.error) {
    const m = (res.error && res.error.message) || '';
    return { verdict: 'FAIL', detail: m.slice(0, 80) };
  }
  const result = res.result || {};
  const txt = (result.content && result.content[0] && result.content[0].text) || '';
  if (result.isError) {
    if (txt.indexOf('超时') !== -1) return { verdict: 'FAIL', detail: txt.slice(0, 80) };
    if (txt.indexOf('无法序列化') !== -1 && KNOWN_ROUTED.has(name)) return { verdict: 'ROUTED', detail: txt.slice(0, 60) };
    return { verdict: 'ROUTED', detail: txt.slice(0, 80) };
  }
  // 超时判断仅对短文本生效 (防 setTimeout 等长HTML误报)
  if (txt.length < 300 && txt.indexOf('超时') !== -1) return { verdict: 'FAIL', detail: txt.slice(0, 80) };
  if (txt.indexOf('没有可用的浏览器') !== -1) return { verdict: 'FAIL', detail: txt.slice(0, 60) };
  if (txt.length < 300 && /缺少|不能为空|需要 .* 参数|未知/.test(txt)) return { verdict: 'ROUTED', detail: txt.slice(0, 60) };
  return { verdict: 'PASS', detail: txt.slice(0, 60) };
}

(async () => {
  const listRes = await postMcp({jsonrpc:'2.0',id:'s0',method:'tools/list',params:{}});
  const tools = listRes.result.tools || [];
  const results = { PASS: [], ROUTED: [], FAIL: [], SKIP: [] };
  let seq = 0;
  for (const t of tools) {
    const name = t.name;
    if (SKIP.has(name)) { results.SKIP.push(name); continue; }
    const args = buildArgs(t, name);
    const t0 = Date.now();
    try {
      const r = await postMcp({jsonrpc:'2.0',id:'s_'+(++seq),method:'tools/call',params:{name,arguments:args}}, 30000);
      const c = classify(name, r, Date.now() - t0);
      results[c.verdict].push(name + (c.verdict === 'PASS' ? '' : ' → ' + c.detail));
    } catch(e) {
      results.FAIL.push(name + ' → ' + e.message);
    }
    await sleep(250); // 节奏间隔, 消除重载干扰
  }
  // 报告
  const lines = [];
  lines.push('=== 串行测试报告 ===');
  lines.push('总数: ' + tools.length + ' | PASS: ' + results.PASS.length + ' | ROUTED: ' + results.ROUTED.length + ' | FAIL: ' + results.FAIL.length + ' | SKIP: ' + results.SKIP.length);
  lines.push('');
  if (results.FAIL.length) { lines.push('--- FAIL ---'); results.FAIL.forEach(x => lines.push('  ' + x)); lines.push(''); }
  if (results.ROUTED.length) { lines.push('--- ROUTED ---'); results.ROUTED.forEach(x => lines.push('  ' + x)); lines.push(''); }
  lines.push('--- PASS ---');
  results.PASS.forEach(x => lines.push('  ' + x));
  const out = lines.join('\n');
  fs.writeFileSync('serial_test_report.txt', out, 'utf8');
  console.log(out.split('\n').slice(0, 3).join('\n'));
  if (results.FAIL.length) { console.log('--- FAIL ---'); results.FAIL.forEach(x => console.log('  ' + x)); }
})().catch(e => { console.error('中止:', e.message); process.exit(1); });
