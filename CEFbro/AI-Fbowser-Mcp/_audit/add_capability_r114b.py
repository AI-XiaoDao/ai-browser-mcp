# -*- coding: utf-8 -*-
"""Server 侧 4 处补做(上一次锚点把缩进猜成 9 空格, 实际是 8 —— 改用"定位行再自取缩进")。"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
BAK = os.path.join(ROOT, '备份', 'URI解码与按ID取框架-写入前')

text = open(SERVER, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in text else '\n'
lines = text.split('\n')
problems = []


def insert_after(needle, block, tag):
    idx = [i for i, ln in enumerate(lines) if needle in ln]
    if len(idx) != 1:
        problems.append('%s: 定位 %d 行' % (tag, len(idx)))
        return
    i = idx[0]
    ind = ' ' * (len(lines[i]) - len(lines[i].lstrip(' ')))
    body = [ind + b if b else '' for b in block]
    for b in body:
        if b and b.replace('\\"', '').count('"') % 2 != 0:
            problems.append('%s: 裸双引号: %s' % (tag, b.strip()[:90]))
            return
    lines[i + 1:i + 1] = body
    print('   ok %s (插在第 %d 行后)' % (tag, i + 1))


def replace_line(needle, new_body, tag):
    idx = [i for i, ln in enumerate(lines) if needle in ln]
    if len(idx) != 1:
        problems.append('%s: 定位 %d 行' % (tag, len(idx)))
        return
    i = idx[0]
    ind = ' ' * (len(lines[i]) - len(lines[i].lstrip(' ')))
    body = ind + new_body
    if body.replace('\\"', '').count('"') % 2 != 0:
        problems.append('%s: 裸双引号奇数' % tag)
        return
    lines[i] = body
    print('   ok %s (改第 %d 行)' % (tag, i + 1))


insert_after('置整数值 ("browser_frame_by_name"',
             ['命令注册表.置整数值 ("browser_frame_by_id", 1325)'],
             '注册表 browser_frame_by_id=1325')

insert_after('添加工具JSON ("browser_frame_by_name"',
             ['添加工具JSON ("browser_frame_by_id", "按框架ID取框架信息(与 browser_frame_by_name 对称)。'
              'browser_get_frames 给出的 frame_id 可直接用; 找不到框架不算失败, 会回 found:false + hint'
              '(导航/刷新后旧 ID 失效, 请重新取)", '
              '单参数Schema文本 ("frame_id", "text", "框架ID(取自 browser_get_frames)"))'],
             '注册 browser_frame_by_id 工具')

replace_line('添加工具JSON ("browser_uri_encode"',
             '添加工具JSON ("browser_uri_encode", "URI编码(百分号编码, 与 JS encodeURIComponent 基本一致)。'
             '字母数字与 -_.!~* 等少数字符之外都会变成 %XX; 空格默认 %20, use_plus:true 时变成 + (表单语义)", '
             '多属性Schema文本 (属性项JSON ("data", "text", "要编码的文本") + "," + '
             '属性项JSON ("use_plus", "boolean", "true=空格编码为 + / false(默认)=空格编码为 %20"), "\\"data\\""))',
             'uri_encode schema')

replace_line('添加工具JSON ("browser_uri_decode"',
             '添加工具JSON ("browser_uri_decode", "URI解码(百分号还原)。默认把 %20/%26/%3D 等全部还原成字符; '
             'keep_escaped:true 则保留 ASCII 特殊字符的转义(旧行为, 只还原非 ASCII)", '
             '多属性Schema文本 (属性项JSON ("data", "text", "要解码的文本") + "," + '
             '属性项JSON ("to_utf8", "boolean", "true(默认)=把解码结果按 UTF-8 解释") + "," + '
             '属性项JSON ("keep_escaped", "boolean", "true=保留 ASCII 特殊字符转义 / false(默认)=全部还原"), "\\"data\\""))',
             'uri_decode schema')

if problems:
    print('!! 未写文件: %r' % problems)
    sys.exit(1)
os.makedirs(BAK, exist_ok=True)
dst = os.path.join(BAK, 'MCP_Server.wsv')
if not os.path.exists(dst):
    shutil.copy2(SERVER, dst)
open(SERVER, 'wb').write(nl.join(lines).encode('utf-8'))
print('Server 侧 4 处已写入')
