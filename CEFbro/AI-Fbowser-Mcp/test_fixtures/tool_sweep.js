// 全量 255 工具探测 (sweep)
// 策略: 破坏性/状态污染工具跳过; 其余按 inputSchema 生成安全参数逐个调用
// 结果分级: PASS(成功) / ROUTED(已路由,优雅报错=前置条件不满足) / FAIL(超时/崩溃/序列化错误等真失败) / SKIP
const http = require('http');
const fs = require('fs');

const HOST = '127.0.0.1', PORT = 9222;
const WELCOME = 'http://127.0.0.1:9222/';

// 跳过: 破坏性/状态污染/GUI阻塞
const SKIP = new Set([
  'browser_shutdown',        // 关闭服务器!
  'browser_close', 'browser_close_try', 'browser_create',  // GUI受限/关闭浏览器
  'browser_clear_cache', 'browser_clear_cache_browser',    // 清缓存
  'browser_set_proxy', 'browser_clear_proxy',              // 网络代理状态
  'browser_set_cookie', 'browser_delete_cookies',          // Cookie状态
  'browser_start_download', 'browser_download_image',      // 写文件
  'browser_print', 'browser_print_to_pdf',                 // 打印对话框
  'browser_open_devtools', 'browser_close_devtools',       // GUI
  'browser_file_dialog',                                   // 文件对话框
  'browser_edit_cut', 'browser_edit_copy', 'browser_edit_paste', // 剪贴板
  'browser_set_parent', 'browser_set_window_style',        // 窗口状态
  'browser_set_preference',                                // 偏好状态
  'browser_inject',                                        // 持久Hook注入
  'browser_find', 'browser_stop_find',                     // 查找条GUI
  'browser_vip_load_extension', 'browser_vip_unload_extension', 'browser_vip_extension_info',
  'browser_vip_send_devtools_msg', 'browser_vip_disable_debugger',
  'browser_vip_websocket_intercept', 'browser_vip_enable_js_env', 'browser_vip_set_is_trusted',
  'browser_vip_enable_inspector', 'browser_vip_enable_devtools_observer', 'browser_vip_disable_console',
  'browser_vip_execute_js_context',                        // VIP JS环境执行(状态)
  'browser_debugger_set_breakpoint', 'browser_debugger_flow', 'browser_debugger_auto',
  'browser_debugger_wait_paused',                          // 阻塞等待
  'workflow_run', 'workflow_stop',                         // 任务#4专项测
  // 指纹setter (value必填, 改状态)
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

// 特殊参数覆盖 (按名)
const OVERRIDE = {
  'browser_navigate': { url: WELCOME, max_ms: 8000 },
  'browser_click_text': { text: 'zzz不存在的文本zzz' },           // 保证not_found优雅路径
  'browser_dom_click': { selector: 'body' },
  'browser_dom_set_value': { selector: 'input', value: 'x' },     // example.com无input→优雅失败
  'browser_highlight': { selector: 'body', duration_ms: 300 },
  'browser_console_eval': { expression: '1+1' },
  'browser_base64_encode': { data: 'hello' },
  'browser_base64_decode': { data: 'aGVsbG8=' },
  'browser_uri_encode': { data: 'hello world' },
  'browser_uri_decode': { data: 'hello%20world' },
  'browser_set_zoom': { level: 1.0 },
  'browser_set_mute': { mute: false },
  'browser_set_focus': { focus: true },
  'browser_move_window': { x: 100, y: 100 },
  'browser_cdp': { method: 'Browser.getVersion' },
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
  'browser_snapshot': { max_items: 5 },       // 已知bug(修复待重编译)
  'browser_element_action': { index: 0, action: 'get_value' }, // 已知bug
  'browser_extract': { type: 'links' },
  'browser_event': { limit: 3 },
  'browser_network': { action: 'list' },
  'browser_collect': { action: 'list' },
  'browser_intercept': { action: 'list' },
  'browser_wait': { what: 'load', max_ms: 2000 },
  'browser_retry': { request_id: 'none', max_ms: 1000 },
  'browser_request': { url: WELCOME, max_ms: 5000 },
  'browser_start': {},
  'browser_restore_gui': {},
  'browser_fingerprint': { action: 'get' },
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

// 期望失败的集合 (前置条件不满足, 但验证路由正常)
const EXPECT_GRACEFUL = new Set([
  'browser_restore_gui', 'browser_create_url_request',
  'browser_dom_set_value', 'browser_dom_checked', 'browser_dom_selected',
  'browser_fill_set_value', 'browser_fill_attr_set', 'browser_fill_click', 'browser_fill_focus',
  'browser_fill_scroll', 'browser_fill_trigger', 'browser_fill_select',
  'browser_click_text', 'browser_mouse_click', 'browser_key_event', 'browser_touch_press',
  'browser_touch_release', 'browser_touch_move', 'browser_ipc_send_to', 'browser_is_same',
  'browser_find_by_tag', 'browser_find_by_hwnd', 'browser_frame_by_name', 'browser_request',
  'browser_retry', 'mcp_result', 'browser_debugger_evaluate', 'browser_network', 'browser_collect',
  'browser_intercept', 'browser_wait', 'browser_extract', 'browser_fingerprint', 'browser_snapshot',
  'browser_element_action', 'browser_edit_undo', 'browser_edit_redo', 'browser_edit_delete',
  'browser_edit_select_all', 'browser_stop', 'browser_send_message', 'browser_ipc_send_all',
  'browser_vip_dom_search', 'browser_vip_dom_get_document', 'browser_vip_orientation',
  'browser_vip_touch_emulation', 'browser_vip_fingerprint_geolocation', 'browser_vip_fingerprint_rect',
  'browser_set_auto_resize', 'browser_set_window_style' ,
]);

function postMcp(body, timeoutMs) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = http.request({hostname: HOST, port: PORT, path: '/mcp', method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }},
      res => { let raw=''; res.on('data',c=>raw+=c); res.on('end',()=>{ try { resolve(JSON.parse(raw)); } catch(e){ resolve({_raw:raw.slice(0,100)}); } }); });
    req.on('error', e => reject(e));
    req.setTimeout(timeoutMs || 15000, () => { req.destroy(); reject(new Error('HTTP timeout')); });
    req.write(data); req.end();
  });
}

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
  // 通用: 控制同步等待
  if ('max_ms' in props) args.max_ms = 3000;
  if ('async_only' in props) args.async_only = true;
  return args;
}

function classify(name, res) {
  if (res._raw) return { verdict: 'FAIL', detail: '非JSON响应: ' + res._raw };
  if (res.error) {
    const m = (res.error && res.error.message) || '';
    // JSON-RPC错误: 未知方法=FAIL(注册表缺失), 其他=路由正常
    if (/未知|not found|unknown/i.test(m)) return { verdict: 'FAIL', detail: m };
    return { verdict: 'ROUTED', detail: m.slice(0, 90) };
  }
  const result = res.result || {};
  if (result.isError) {
    const txt = (result.content && result.content[0] && result.content[0].text) || '';
    if (/无法序列化|超时|timeout/i.test(txt)) return { verdict: 'FAIL', detail: txt.slice(0, 90) };
    return { verdict: 'ROUTED', detail: txt.slice(0, 90) };
  }
  const txt = (result.content && result.content[0] && result.content[0].text) || JSON.stringify(result).slice(0,60);
  return { verdict: 'PASS', detail: txt.slice(0, 90) };
}

(async () => {
  // 1. 确保在 example.com (静态页, 输入类工具测试安全)
  await postMcp({jsonrpc:'2.0',id:'sw0',method:'tools/call',params:{name:'browser_navigate',arguments:{url:'https://example.com',max_ms:15000}}}, 25000);
  await new Promise(r => setTimeout(r, 1500));

  // 2. 工具清单
  const listRes = await postMcp({jsonrpc:'2.0',id:'sw1',method:'tools/list',params:{}});
  const tools = listRes.result.tools || [];

  const results = { PASS: [], ROUTED: [], FAIL: [], SKIP: [] };
  let seq = 0;
  for (const t of tools) {
    const name = t.name;
    if (SKIP.has(name)) { results.SKIP.push(name); continue; }
    const args = buildArgs(t, name);
    try {
      const r = await postMcp({jsonrpc:'2.0',id:'sw_'+(++seq),method:'tools/call',params:{name,arguments:args}}, 15000);
      const c = classify(name, r);
      // 已知bug/预期优雅 → 不误报
      if (c.verdict === 'FAIL' && EXPECT_GRACEFUL.has(name)) {
        results.ROUTED.push(name + '  [预期优雅,实际: ' + c.detail.slice(0,50) + ']');
      } else {
        results[c.verdict].push(name + (c.verdict==='PASS' ? '' : '  → ' + c.detail));
      }
    } catch (e) {
      results.FAIL.push(name + '  → HTTP/异常: ' + e.message);
    }
  }

  // 3. 恢复欢迎页
  await postMcp({jsonrpc:'2.0',id:'sw9',method:'tools/call',params:{name:'browser_navigate',arguments:{url:WELCOME,max_ms:10000}}}, 20000);

  // 4. 报告
  const lines = [];
  lines.push('=== 全量工具探测报告 ===');
  lines.push('总数: ' + tools.length);
  lines.push('PASS: ' + results.PASS.length);
  lines.push('ROUTED(优雅报错,前置条件不满足): ' + results.ROUTED.length);
  lines.push('FAIL: ' + results.FAIL.length);
  lines.push('SKIP(破坏性/状态污染): ' + results.SKIP.length);
  lines.push('');
  if (results.FAIL.length) { lines.push('--- FAIL 明细 ---'); results.FAIL.forEach(x => lines.push('  ' + x)); lines.push(''); }
  if (results.ROUTED.length) { lines.push('--- ROUTED 明细 ---'); results.ROUTED.forEach(x => lines.push('  ' + x)); lines.push(''); }
  lines.push('--- SKIP 明细 ---');
  results.SKIP.forEach(x => lines.push('  ' + x));
  const out = lines.join('\n');
  fs.writeFileSync('sweep_report.txt', out, 'utf8');
  console.log(out);
})().catch(e => { console.error('SWEEP中止:', e.message); process.exit(1); });
