// 模拟 类_MCP_篡改过滤器.修改数据 的算法 (与 wsv 实现逐分支对应), 验证流式行为
class TamperFilter {
  constructor(action, search, replace, initText) {
    this.action = action; this.search = search; this.replace = replace;
    this.tail = ''; this.pending = initText || ''; this.abandoned = false;
  }
  // 输出待输出文本 (返回是否吐完) — 模拟: 输出缓冲无限大
  drain() {
    if (this.pending === '') return true;
    this.outBuf += this.pending;
    this.pending = '';
    return true;
  }
  // 修改数据 单次调用 (输入块)
  filter(chunk) {
    // 待输出未吐完
    if (this.pending !== '') {
      this.drain();
      return 'NEED_MORE';
    }
    if (chunk === null) { // 最终调用
      this.pending = this.pending + this.tail;
      this.tail = '';
      if (this.pending !== '') { this.drain(); return 'NEED_MORE'; }
      return 'DONE';
    }
    if (this.action !== 'modify') return 'DONE'; // 消费输入
    if (this.abandoned) {
      this.outBuf += chunk; // 透传
      return 'NEED_MORE';
    }
    let merged = this.tail + chunk;
    if (merged.length > 100) { // 模拟4MB上限
      this.abandoned = true;
      this.pending += merged;
      this.tail = '';
    } else {
      let replaced = merged;
      if (this.search !== '') replaced = replaced.split(this.search).join(this.replace);
      if (this.search.length > 1) {
        const tl = this.search.length - 1;
        if (replaced.length >= tl) { this.tail = replaced.slice(-tl); replaced = replaced.slice(0, -tl); }
        else { this.tail = replaced; replaced = ''; }
      }
      this.pending += replaced;
    }
    this.drain();
    return 'NEED_MORE';
  }
  run(chunks) {
    this.outBuf = '';
    for (const c of chunks) this.filter(c);
    this.filter(null);
    return this.outBuf;
  }
}

// 测试1: modify 跨块匹配 (chunk 边界切开搜索词)
{
  const f = new TamperFilter('modify', 'secret', 'PUBLIC', '');
  const out = f.run(['hello se', 'cret world, se', 'cret again']);
  console.log('T1 modify跨块:', out);
  console.log('  ', out === 'hello PUBLIC world, PUBLIC again' ? '✓' : '✗');
}
// 测试2: modify 无匹配
{
  const f = new TamperFilter('modify', 'zzz', 'X', '');
  const out = f.run(['abc def ghi']);
  console.log('T2 modify无匹配:', out, out === 'abc def ghi' ? '✓' : '✗');
}
// 测试3: block (初始文本输出, 输入丢弃)
{
  const f = new TamperFilter('block', '', '', '资源已屏蔽');
  const out = f.run(['original body content to discard']);
  console.log('T3 block:', out, out === '资源已屏蔽' ? '✓' : '✗');
}
// 测试4: replace_data
{
  const f = new TamperFilter('replace_data', '', '', 'NEW DATA');
  const out = f.run(['old', 'body']);
  console.log('T4 replace_data:', out, out === 'NEW DATA' ? '✓' : '✗');
}
// 测试5: 放弃后透传 (超大资源)
{
  const f = new TamperFilter('modify', 'abc', 'X', '');
  const big = 'a'.repeat(150) + 'abc' + 'b'.repeat(50);
  const out = f.run([big.slice(0, 80), big.slice(80)]);
  console.log('T5 放弃透传:', out.length === big.length && out.includes('abc') ? '✓ (原样透传)' : '✗ 长度=' + out.length + ' 期望=' + big.length);
}
// 测试6: 尾部文本在末尾被替换 (尾部在最终调用输出)
{
  const f = new TamperFilter('modify', 'END', 'DONE', '');
  const out = f.run(['prefix E', 'ND']);
  console.log('T6 尾块匹配:', out, out === 'prefix DONE' ? '✓' : '✗');
}
