// 端到端逆向演示 v2: 动态hook → 参数捕获 → 关键词检索 → call_fn 纯算法直调 → 参数解密
// 含异步任务轮询 (hook/call_fn 提交后经 mcp_result 取结果)
const http = require('http');
function postMcp(body, timeoutMs) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = http.request({hostname:'127.0.0.1',port:9222,path:'/mcp',method:'POST',
      headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(data)}},
      res => { let raw=''; res.on('data',c=>raw+=c); res.on('end',()=>{ try { resolve(JSON.parse(raw)); } catch(e){ resolve({_raw:raw.slice(0,150)}); } }); });
    req.on('error', e => reject(e));
    req.setTimeout(timeoutMs || 25000, () => { req.destroy(); reject(new Error('HTTP timeout')); });
    req.write(data); req.end();
  });
}
function call(name, args, t) {
  return postMcp({jsonrpc:'2.0',id:'d_'+name,method:'tools/call',params:{name,arguments:args||{}}}, t);
}
function txt(r) {
  try { return (r.result&&r.result.content&&r.result.content[0]&&r.result.content[0].text)||JSON.stringify(r).slice(0,150); }
  catch(e){ return JSON.stringify(r).slice(0,150); }
}
function inner(r) {
  const t = txt(r);
  const m = t.match(/\{[\s\S]*\}/);
  if (!m) return null;
  try { return JSON.parse(m[0]); } catch(e){ return null; }
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

// 轮询异步任务结果 (mcp_result consume)
async function waitTask(taskId, timeoutMs) {
  const t0 = Date.now();
  while (Date.now() - t0 < (timeoutMs || 15000)) {
    const r = await call('mcp_result', {request_id: taskId, consume: true});
    const t = txt(r);
    if (!/未找到任务|_waiting|任务仍在执行/.test(t)) return t;
    await sleep(400);
  }
  return '(等待超时)';
}

(async () => {
  console.log('【步骤0】准备干净页面');
  await call('browser_navigate', {url:'https://example.com', max_ms:15000}, 25000);
  await sleep(800);

  console.log('【步骤1】注入模拟签名/解密算法 (模拟目标站的加密逻辑)');
  const inject = "(function(){window.__demo_sign=function(p){return btoa('SALT_'+p+'@'+String(Date.now()%100000))};window.__demo_decrypt=function(c){var s=atob(c);return s.replace(/^SALT_/,'').replace(/@\\d+$/,'')};window.__demo_add=function(a,b){return a+b};return JSON.stringify({injected:true,fn:['__demo_sign','__demo_decrypt','__demo_add']})})()";
  console.log(' ', txt(await call('browser_evaluate', {code:inject})));

  console.log('【步骤2】开启控制台采集 + 动态hook __demo_sign (异步注入, 轮询等待)');
  await call('browser_collect', {action:'console_enable'});
  const hook = await call('browser_reverse_hook', {type:'function_call', target:'__demo_sign'});
  console.log('  提交:', txt(hook).slice(0, 130));
  const hInner = inner(hook);
  let hookTaskId = hInner && hInner.task_id;
  if (hookTaskId) {
    const hookResult = await waitTask(hookTaskId, 15000);
    console.log('  注入结果:', hookResult.slice(0, 200));
  } else {
    // 若已同步返回, 直接取文本
    console.log('  注入结果:', txt(hook).slice(0, 200));
  }
  await sleep(600);

  console.log('【步骤3】触发调用 (模拟登录提交), hook 捕获参数');
  await call('browser_evaluate', {code:"(function(){window.__demo_sign('admin123');window.__demo_sign('password456');return JSON.stringify({triggered:2})})()"});
  await sleep(1500);

  console.log('【步骤4】关键词检索控制台 (新功能: keyword=admin123)');
  const search = await call('browser_collect', {action:'console_get', keyword:'admin123', limit:10});
  console.log(' ', txt(search).slice(0, 400));
  if (txt(search).indexOf('admin123') !== -1) console.log('  ✓ 关键词搜索捕获到加密入参');
  else console.log('  ⚠ console 未检索到 (hook 可能未注入或采集未生效)');

  console.log('【步骤5】call_fn 纯算法直调 (新: function_name 免objectId, 轮询取结果)');
  const dec = await call('browser_reverse_call_fn', {function_name:'__demo_decrypt', arguments:['U0FMVF9hZG1pbjEyM0AxMjM0NQ==']});
  const decInner = inner(dec);
  let decTaskId = decInner && decInner.task_id;
  if (decTaskId) {
    const decResult = await waitTask(decTaskId, 15000);
    console.log('  解密结果:', decResult.slice(0, 400));
    if (decResult.indexOf('admin123') !== -1) console.log('  ✓ 参数解密成功: 密文 → admin123');
  } else {
    console.log('  解密结果:', txt(dec).slice(0, 400));
  }

  console.log('【步骤5b】类型保留验证 (新: 数字参数不再降级为字符串)');
  const add = await call('browser_reverse_call_fn', {function_name:'__demo_add', arguments:[1,2]});
  const addInner = inner(add);
  const addTaskId = addInner && addInner.task_id;
  const addResult = addTaskId ? await waitTask(addTaskId, 15000) : txt(add);
  console.log('  __demo_add(1,2) 结果:', addResult.slice(0, 250));
  if (/\"result\":\s*3|:3[,\}\]]/.test(addResult)) console.log('  ✓ 数字类型保留: 1+2=3 (若字符串拼接会得\"12\")');
  else if (addResult.indexOf('"12"') !== -1) console.log('  ✗ 类型降级为字符串: 1+2="12"');
  else console.log('  ⚠ 结果格式待人工确认');

  console.log('【步骤6】hook_logs 直接读捕获数据 (新: function_call 写入 __MCP_HOOK_LOG__)');
  const hl = await call('browser_reverse_hook_logs', {log_key:'__MCP_HOOK_LOG__', action:'query'});
  console.log(' ', txt(hl).slice(0, 400));
  if (txt(hl).indexOf('admin123') !== -1) console.log('  ✓ hook_logs 检索到入参 admin123');
  else console.log('  ⚠ __MCP_HOOK_LOG__ 无记录');

  console.log('DONE');
})().catch(e => { console.error('中止:', e.message); process.exit(1); });
