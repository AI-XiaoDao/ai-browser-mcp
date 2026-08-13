// 模拟 line_replace 行跟踪状态机 (与 wsv 实现逐分支对应)
class LineReplacer {
  constructor(start, end, repl) { this.start = start; this.end = end; this.repl = repl; this.lineNo = 0; this.tail = ''; this.out = ''; }
  feed(text) {
    const merged = this.tail + text;
    const parts = merged.split('\n');
    const n = parts.length;
    const tailPartial = n > 0 && !merged.endsWith('\n');
    let processCount = n;
    if (tailPartial) processCount = n - 1;
    else if (n > 0) processCount = n - 1; // 末尾空段剔除
    let chunkOut = '';
    for (let i = 0; i < processCount; i++) {
      this.lineNo++;
      const line = parts[i];
      if (this.lineNo >= this.start && this.lineNo <= this.end) {
        if (this.lineNo === this.start) chunkOut += this.repl + '\n';
        // 区间内其余行丢弃
      } else {
        chunkOut += line + '\n';
      }
    }
    if (tailPartial) this.tail = parts[n - 1];
    else this.tail = '';
    this.out += chunkOut;
  }
  finish() { this.out += this.tail; this.tail = ''; return this.out; }
}

// T1: 基本区间替换
{
  const r = new LineReplacer(2, 3, 'REPLACED');
  r.feed('line1\nline2\nline3\nline4\n');
  const out = r.finish();
  console.log('T1 基本区间:', JSON.stringify(out));
  console.log('  ', out === 'line1\nREPLACED\nline4\n' ? '✓' : '✗');
}
// T2: 跨块区间 (行3在块边界)
{
  const r = new LineReplacer(2, 3, 'R');
  r.feed('a\nb\nc');
  r.feed('\nd\ne\n');
  const out = r.finish();
  console.log('T2 跨块:', JSON.stringify(out));
  console.log('  ', out === 'a\nR\nd\ne\n' ? '✓' : '✗');
}
// T3: 区间到末尾 (最后行无换行)
{
  const r = new LineReplacer(2, 99, 'R');
  r.feed('a\nb\nc');
  const out = r.finish();
  console.log('T3 区间到EOF:', JSON.stringify(out));
  console.log('  ', out === 'a\nR\n' ? '✓' : '✗');
}
// T4: 空行与连续换行
{
  const r = new LineReplacer(1, 2, 'R');
  r.feed('\n\nx\n');
  const out = r.finish();
  console.log('T4 空行:', JSON.stringify(out));
  console.log('  ', out === 'R\nx\n' ? '✓' : '✗');
}
// T5: 区间外全文 (start=99 无命中)
{
  const r = new LineReplacer(99, 100, 'R');
  r.feed('a\nb\n');
  const out = r.finish();
  console.log('T5 无命中:', JSON.stringify(out), out === 'a\nb\n' ? '✓' : '✗');
}
