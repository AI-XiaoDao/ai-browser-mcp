# -*- coding: utf-8 -*-
r"""按实测订正 DPI/V8 两个键的文档口径(上一版措辞与实测不符)。

实测(配置驱动 + 页面侧指标, 见 _audit/verify_dpi_v8_e2e.py):
  · `performance.memory.jsHeapSizeLimit`: 默认 **4294705152(≈4GB)** —— 设 v8_max_stack_mb=1024 后变为 **1075314688(≈1GB)**。
    => 该调用**确实生效**(可测), 但它是**设定** V8 堆上限而非"只放宽": x64 上默认已有 ~4GB, 设一个更小的值会**压低**它。
       类库中文名写的是"堆栈大小", 底层 C 函数却是 FBroSetV8DefaultsHeapSize(**堆**) —— 名实不符, 文档必须按实测说清。
  · DPI: 本机 dpr=1(缩放 100%)时视口 984x705 前后**无变化** —— 无可见差异; 风险提示(HiDPI 下视口变小)仍成立但本机测不出。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JOBS = [
    (os.path.join(ROOT, 'mcp_config.README.md'),
     '**只放宽** V8 堆栈上限（深递归/JSVMP 页面防渲染进程崩溃）；`0` = 内核默认（不改动）。上限 4096MB；32 位构建建议 ≤4000。',
     '设定渲染进程 V8 **堆**上限（类库中文名叫"堆栈大小", 底层是 `FBroSetV8DefaultsHeapSize`, 实测改的是 `performance.memory.jsHeapSizeLimit`）。⚠ 实测：本机 x64 默认已是 **≈4GB(4294705152)**，设 1024 会把它**压低到 ≈1GB** —— 它不是"只放宽", 而是设定值；`0` = 内核默认（不改动）。校验范围 1..4096；32 位构建 ≤4000。',
     1),
    (os.path.join(ROOT, 'docs', 'MCP工具配置说明书.md'),
     '**只放宽** V8 堆栈上限（深递归/JSVMP 页面防渲染进程崩溃），`0`=内核默认。校验范围 1..4096。',
     '设定渲染进程 V8 **堆**上限（类库中文名叫"堆栈大小", 底层为 `FBroSetV8DefaultsHeapSize`；实测改的是 `performance.memory.jsHeapSizeLimit`）。⚠ 实测：本机 x64 默认 **≈4GB(4294705152)**，设 1024 会**压低到 ≈1GB** —— 属"设定值"而非"只放宽"。`0`=内核默认。校验范围 1..4096；32 位 ≤4000。',
     1),
    (os.path.join(ROOT, 'docs', 'MCP工具配置说明书.md'),
     '启动期调用 `FBrowser_设置程序DPI模式 (按显示器感知V2)`：进程级 DPI 感知（HiDPI 屏上窗口不再被位图拉伸）。',
     '启动期调用 `FBrowser_设置程序DPI模式 (按显示器感知V2)`：进程级 DPI 感知（HiDPI 屏上窗口不再被位图拉伸）。实测：本机缩放 100%(dpr=1) 时视口 984×705 前后**无变化**, 即该键只在缩放≠100% 的显示器上有可见效果。',
     1),
    (os.path.join(ROOT, 'src', 'MCP_Server.wsv'),
     'V8堆栈上限MB <公开 静态 类型 = 整数 值 = 0 注释 = "mcp_config.json v8_max_stack_mb: >0 时启动期调用 FBrowser_初始化_设置V8环境默认堆栈大小(0, N), 只放宽 V8 堆栈上限(深递归逆向页面防渲染进程崩溃); 0 = 内核默认(不改动)"',
     'V8堆栈上限MB <公开 静态 类型 = 整数 值 = 0 注释 = "mcp_config.json v8_max_stack_mb: >0 时启动期调用 FBrowser_初始化_设置V8环境默认堆栈大小(0, N) —— 注意类库中文名写的是堆栈, 底层是 FBroSetV8DefaultsHeapSize, 实测改的是 performance.memory.jsHeapSizeLimit(本机 x64 默认约4GB, 设1024会压低到约1GB, 即设定值而非只放宽); 0 = 内核默认(不改动)"',
     1),
]


def main():
    for path, old, new, want in JOBS:
        raw = open(path, 'rb').read()
        assert not raw.startswith(b'\xef\xbb\xbf'), '%s BOM' % path
        txt = raw.decode('utf-8')
        n = txt.count(old)
        assert n == want, '%s 命中 %d(期望 %d): %s' % (os.path.basename(path), n, want, old[:60])
        print('%-30s OK' % os.path.basename(path))
        if '--apply' in sys.argv:
            term = '\r\r\n' if '\r\r\n' in txt else ('\r\n' if '\r\n' in txt else '\n')
            with io.open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(txt.replace(old, new))
    print('已写入' if '--apply' in sys.argv else '[dry-run] 未落盘')


main()
