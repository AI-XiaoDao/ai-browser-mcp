# -*- coding: utf-8 -*-
r"""第132轮: `browser_fingerprint` 的 geolocation 坐标参数**名不对**（实现读 `latitude/longitude`，
           而 schema（以及它自己的兄弟工具 `browser_vip_fingerprint_geolocation`）用的是 `lat/lng`）
           ⇒ 代理照文档传 `lat/lng` 会被**静默忽略**（坐标保持 0）—— 属"静默不生效"。

改法(两手都要):
  ① 实现**同时接受两种写法**(`latitude` 优先, 回退 `lat`; `longitude` 回退 `lng`), 走"零前置"思路:
     不让调用方去记两套名字;
  ② schema 里把两个名字都声明出来, 并注明等价关系。

依据: `_audit/_show_branch_params.py --brief --closure` 全量扫描(323 工具)报出
`browser_fingerprint MISSING=['latitude','longitude']`; 源码核实 Core:2527/2529。

用法: py -3 _audit\_apply_round132.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

CORE_OLD = '''                        变量 lat <类型 = 小数>
                        lat = MCP命令服务器.yyjson取小数 (参数JSON, "latitude")
                        变量 lng <类型 = 小数>
                        lng = MCP命令服务器.yyjson取小数 (参数JSON, "longitude")'''
CORE_NEW = '''                        变量 lat <类型 = 小数>
                        lat = MCP命令服务器.yyjson取小数 (参数JSON, "latitude")
                        变量 lng <类型 = 小数>
                        lng = MCP命令服务器.yyjson取小数 (参数JSON, "longitude")
                        // 名称兼容(实测缺陷修正): 兄弟工具 browser_vip_fingerprint_geolocation 用的是 lat/lng,
                        // 而本入口原先只认 latitude/longitude —— 调用方照另一处文档传 lat/lng 会被**静默忽略**
                        // (坐标保持 0 且回 success)。改为两者都接受(专用名优先), 免得调用方去记两套名字。
                        如果 (lat == 0 && MCP命令服务器.参数键存在 (参数JSON, "lat"))
                        {
                            lat = MCP命令服务器.yyjson取小数 (参数JSON, "lat")
                        }
                        如果 (lng == 0 && MCP命令服务器.参数键存在 (参数JSON, "lng"))
                        {
                            lng = MCP命令服务器.yyjson取小数 (参数JSON, "lng")
                        }'''

FP_OLD = '属性项JSON ("offset_h", "integer", "timezone: 时区小时偏移")'
FP_NEW = ('属性项JSON ("latitude", "number", "geolocation: 纬度(本入口用这个名字)") + "," + '
          '属性项JSON ("longitude", "number", "geolocation: 经度(本入口用这个名字)") + "," + '
          '属性项JSON ("lat", "number", "geolocation: 纬度的**别名**(与兄弟工具 browser_vip_fingerprint_geolocation 一致; 实现两者都接受)") + "," + '
          '属性项JSON ("lng", "number", "geolocation: 经度的别名(同上)") + "," + '
          '属性项JSON ("offset_h", "integer", "timezone: 时区小时偏移")')


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
    ctxt = io.open(CORE, encoding='utf-8').read()
    has_cr = '\r' in ctxt
    b0 = balance(ctxt)
    assert ctxt.count(CORE_OLD) == 1, 'Core 锚点 %d' % ctxt.count(CORE_OLD)
    c_out = ctxt.replace(CORE_OLD, CORE_NEW, 1)
    assert balance(c_out) == b0, 'Core 括号净值变了'
    print('MCP_Server_Core.wsv: geolocation 现在同时接受 latitude/longitude 与 lat/lng')

    lines = io.open(SERVER, encoding='utf-8').read().split('\n')
    idx = [i for i, ln in enumerate(lines) if '添加工具JSON ("browser_fingerprint"' in ln]
    assert len(idx) == 1, 'fingerprint 注册行 %d' % len(idx)
    i = idx[0]
    if FP_NEW.split(' + ')[0] in lines[i]:
        print('MCP_Server.wsv: 已声明(幂等)')
    else:
        assert lines[i].count(FP_OLD) == 1, 'Server 锚点 %d' % lines[i].count(FP_OLD)
        lines[i] = lines[i].replace(FP_OLD, FP_NEW, 1)
        print('MCP_Server.wsv: 已声明 latitude/longitude 与 lat/lng 两组名字')
    s_out = '\n'.join(lines)
    if '--apply' in sys.argv:
        io.open(CORE, 'w', encoding='utf-8', newline='\n').write(c_out)
        io.open(SERVER, 'w', encoding='utf-8', newline='\n').write(s_out)
        c = io.open(CORE, encoding='utf-8').read()
        s = io.open(SERVER, encoding='utf-8').read()
        assert '参数键存在 (参数JSON, "lat")' in c and ('\r' in c) == has_cr
        assert '"latitude", "number"' in s and '"lat", "number"' in s and '\r' not in s
        print('已写入 Core + Server 并回读校验通过')
    else:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
