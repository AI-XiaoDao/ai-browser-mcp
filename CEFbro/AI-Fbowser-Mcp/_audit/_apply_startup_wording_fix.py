# -*- coding: utf-8 -*-
r"""口径订正 + 未验证事项如实标注(实测后才敢写的版本)。

1) 白名单外的名: 实现是**只遍历 4 个允许名**, 故"不在白名单里的名"是**被忽略**(连 rejected_switches 都不进),
   只有"名在白名单里但值非法"才进 rejected_switches。原文档把两者混为一句, 属**过度承诺**, 必须改准。
2) 实测发现: 类库 禁用代理 产出的是 `--no-proxy-server=disabled`(带值形态), 而 Chromium 常规写法是无值的
   `--no-proxy-server` —— **是否被内核按预期识别未验证**, 必须在文档里如实标注(不能写"已生效")。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JOBS = [
    # (文件, 旧串, 新串, 期望命中数)
    (os.path.join(ROOT, 'src', 'MCP_Server.wsv'),
     '以及配置里 startup_switches 通过/被拒的条目',
     '以及配置里 startup_switches 通过/被拒的条目(口径: **只有"名在白名单内而值非法"才进被拒表; 不在白名单里的名一律忽略**)',
     1),
    (os.path.join(ROOT, 'mcp_config.README.md'),
     '未通过校验的条目**不生效**，但会如实记入回执 `rejected_switches`',
     '名在白名单里而**值非法**的条目不生效，但会如实记入回执 `rejected_switches`；**不在白名单里的名一律忽略**（白名单即契约）。实测：`lang`/`force-device-scale-factor` 会真实出现在内核命令行里',
     1),
    (os.path.join(ROOT, 'docs', 'MCP工具配置说明书.md'),
     '未通过校验的条目**不生效**，但会被如实记入回执 `rejected_switches`（不静默丢弃）',
     '名在白名单里而**值非法**的条目不生效，但会被如实记入回执 `rejected_switches`（不静默丢弃）；**不在白名单里的名一律忽略**',
     1),
    (os.path.join(ROOT, 'docs', 'MCP工具配置说明书.md'),
     '用途＝代理设坏导致全站打不开时的干净排障手段。**仅启动期生效，改动后必须重启进程**',
     '用途＝代理设坏导致全站打不开时的干净排障手段。⚠ 实测：本机类库给它下发的是 **`--no-proxy-server=disabled`**（带值形态），而 Chromium 常规写法是无值的 `--no-proxy-server` —— **是否被内核按预期识别未验证**。**仅启动期生效，改动后必须重启进程**',
     1),
]


def main():
    for path, old, new, want in JOBS:
        raw = open(path, 'rb').read()
        assert not raw.startswith(b'\xef\xbb\xbf'), '%s 带 BOM' % path
        txt = raw.decode('utf-8')
        term = '\r\r\n' if '\r\r\n' in txt else ('\r\n' if '\r\n' in txt else '\n')
        n = txt.count(old)
        assert n == want, '%s 命中 %d 次(期望 %d): %s' % (os.path.basename(path), n, want, old[:50])
        out = txt.replace(old, new)
        print('%-34s %s' % (os.path.basename(path), 'OK' if n == want else 'FAIL'))
        if '--apply' in sys.argv:
            with io.open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(out)
    if '--apply' in sys.argv:
        print('已写入 %d 个文件' % len(JOBS))
    else:
        print('[dry-run] 未落盘')


main()
