# -*- coding: utf-8 -*-
r"""第129轮: 把 `browser_fingerprint` 与 `browser_collect` 的**实现真读却未声明**的参数补进 schema。

依据(本轮用 `_audit/_show_branch_params.py` 自己复核, 不照抄审计结论):
  · `browser_fingerprint`（Core 2390-2645）读取 19 个参数, schema 只声明了 `action`/`config`
    ⇒ **17 个缺失**: min/max/seed、sample_rate/channels/frames_per_buffer、public_ip/local_ip/host/disable、
      offset_h/offset_m/name/iana、tls_min/tls_max/ciphers（各自类型由读取函数判定: 整数/文本/逻辑）。
  · `browser_collect`（Core 3857-4172）读取 `keyword`/`limit`/`clear`/`max_ms`, schema 只有 `action`:
    描述里明明写了"console_get 支持 keyword…limit 限制条数", 但代理**看不到这两个参数** ⇒ 无法使用。

用法: py -3 _audit\_apply_fingerprint_collect_schema.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

FP_OLD = '属性项JSON ("config", "text", "JSON配置"), "\\"action\\"")'
FP_NEW = ('属性项JSON ("config", "text", "JSON配置") + "," + '
          '属性项JSON ("min", "integer", "canvas_random/webgl_random/audio_random: 最少噪点数") + "," + '
          '属性项JSON ("max", "integer", "同上: 最多噪点数") + "," + '
          '属性项JSON ("seed", "integer", "同上: 随机种子(同种子可复现)") + "," + '
          '属性项JSON ("sample_rate", "integer", "audio_param: 采样率") + "," + '
          '属性项JSON ("channels", "integer", "audio_param: 声道数") + "," + '
          '属性项JSON ("frames_per_buffer", "integer", "audio_param: 每次回调帧数") + "," + '
          '属性项JSON ("public_ip", "text", "webrtc: 虚拟公网IP") + "," + '
          '属性项JSON ("local_ip", "text", "webrtc: 虚拟内网IP") + "," + '
          '属性项JSON ("host", "text", "webrtc: 虚拟主机名") + "," + '
          '属性项JSON ("disable", "boolean", "webrtc: true=禁用该维度(不伪装)") + "," + '
          '属性项JSON ("offset_h", "integer", "timezone: 时区小时偏移") + "," + '
          '属性项JSON ("offset_m", "integer", "timezone: 时区分钟偏移") + "," + '
          '属性项JSON ("name", "text", "timezone: 时区名") + "," + '
          '属性项JSON ("iana", "text", "timezone: 标准 IANA 名") + "," + '
          '属性项JSON ("tls_min", "integer", "ssl: TLS 最小版本(0不限制/769=1.0/790=1.1/791=1.2/792=1.3)") + "," + '
          '属性项JSON ("tls_max", "integer", "ssl: TLS 最大版本(取值同上)") + "," + '
          '属性项JSON ("ciphers", "text", "ssl: 加密套件文本(留空=不改)"), "\\"action\\"")')

FP_DESC_OLD = '| 多数改动需刷新页面生效"'
FP_DESC_NEW = ('| 多数改动需刷新页面生效 | **参数已按实现补齐**(此前 17 个维度参数未在 schema 里声明, 代理看不到): '
               'canvas/webgl/audio 随机噪点用 min/max/seed, audio_param 用 sample_rate/channels/frames_per_buffer, '
               'webrtc 用 public_ip/local_ip/host/disable, timezone 用 offset_h/offset_m/name/iana, ssl 用 tls_min/tls_max/ciphers"')

CL_OLD = '单参数Schema文本 ("action", "text", "network_*/console_*/reverse_prepare'
CL_NEW = ('多属性Schema文本 (属性项JSON ("action", "text", "network_*/console_*/reverse_prepare')

CL_TAIL_OLD = 'event_all_enable/event_all_disable")'
CL_TAIL_NEW = ('event_all_enable/event_all_disable") + "," + '
               '属性项JSON ("keyword", "text", "console_get: 按日志内容搜索(定位 Hook 输出/报错/特征串)") + "," + '
               '属性项JSON ("limit", "integer", "console_get / list: 返回条数上限") + "," + '
               '属性项JSON ("clear", "boolean", "true=清空对应日志后返回") + "," + '
               '属性项JSON ("max_ms", "integer", "等待上限毫秒(取日志前的同步等待)"), "")')

CL_DESC_OLD = '开启后用 browser_event 查询"'
CL_DESC_NEW = ('开启后用 browser_event 查询 | **参数已按实现补齐**: keyword(按内容搜日志)/limit(条数上限)/'
               'clear(先清空再返回)/max_ms —— 此前只有 action 被声明, 描述里的 keyword/limit 代理根本看不到"')


def balance(text):
    ob = cb = op = cp = 0
    for ln in text.split('\n'):
        s = ln.strip()
        if s.startswith('@') or s.startswith('//') or s.startswith('#'):
            continue
        i, instr = 0, False
        while i < len(ln):
            c = ln[i]
            if c == '"':
                instr = not instr
            elif not instr:
                if ln.startswith('//', i):
                    break
                if c == '{':
                    ob += 1
                elif c == '}':
                    cb += 1
                elif c == '(':
                    op += 1
                elif c == ')':
                    cp += 1
            i += 1
    return ob - cb, op - cp


def main():
    txt = io.open(SERVER, encoding='utf-8').read()
    assert '\r' not in txt
    lines = txt.split('\n')
    b0 = balance(txt)
    done = []
    for tool, edits in (('browser_fingerprint', [('schema-17参数', FP_OLD, FP_NEW), ('描述', FP_DESC_OLD, FP_DESC_NEW)]),
                        ('browser_collect', [('schema-4参数', CL_OLD, CL_NEW), ('schema-尾', CL_TAIL_OLD, CL_TAIL_NEW),
                                             ('描述', CL_DESC_OLD, CL_DESC_NEW)])):
        idx = [i for i, ln in enumerate(lines) if ('添加工具JSON ("%s"' % tool) in ln]
        assert len(idx) == 1, '%s 注册行 %d' % (tool, len(idx))
        i = idx[0]
        for tag, old, new in edits:
            if new in lines[i]:
                done.append('%s %s (已存在)' % (tool, tag))
                continue
            assert lines[i].count(old) == 1, '%s / %s 锚点 %d' % (tool, tag, lines[i].count(old))
            lines[i] = lines[i].replace(old, new, 1)
            done.append('%s %s' % (tool, tag))
    out = '\n'.join(lines)
    assert balance(out) == b0, '括号净值变了 %s -> %s' % (b0, balance(out))
    print('MCP_Server.wsv: 行数不变 %d; 完成 %d 项:' % (len(lines), len(done)))
    for d in done:
        print('   · %s' % d)
    if '--apply' in sys.argv:
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(out)
        c = io.open(SERVER, encoding='utf-8').read()
        for must in ('"frames_per_buffer"', '"iana"', '"ciphers"', '"keyword"', '参数已按实现补齐'):
            assert must in c, '缺少 %s' % must
        assert '\r' not in c
        print('已写入并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
