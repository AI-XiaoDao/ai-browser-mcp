# -*- coding: utf-8 -*-
"""补上 VIP 审计排名第 1 的真缺口: UA-CH(userAgentData) 的四个字段。

审计结论(_audit/_vip_gap_analysis.md, 只读复核):
  `browser_fingerprint_ua` 已暴露 8 个 UA 字段, 却**恰好漏掉** UA-CH 里最常被交叉校验的四项:
    navigator.userAgentData.brands / fullVersionList / platformVersion / fullVersion
  后果不是"少伪装一点", 而是**更容易被识别**: 只改 UA 字符串、UA-CH 仍是默认值,
  两者不一致本身就是明显的自动化特征。
  类库侧这四个 setter 在 src 里 **0 命中**(从未被调用)。

本轮实现(三处改动):
  ① MCP_Server.wsv 新增 helper `解析双文本表`: 把紧凑文本 "brand:version,b:2" 解析成
     类库的 `FBrowser_双文本数组`(类库签名: 置Brands/置FullVersionList 要的就是它)。
     **不用 JSON 数组**: 审计提示本项目存在 "YYJSON 嵌套数组" 崩溃风险(MCP_Server.wsv:3257-3258),
     紧凑文本既避开这个坑, 也更好让 AI 生成。
  ② MCP_Server_VIP.wsv 的 browser_fingerprint_ua 分支: 在 指纹_虚拟UserAgent 之前补设这四项。
  ③ schema 增加对应参数。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRV = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
VIP = os.path.join(ROOT, 'src', 'MCP_Server_VIP.wsv')
BAK = os.path.join(ROOT, '备份', 'UA-CH四字段-写入前')

HELPER_ANCHOR = '    方法 从Debugger暂停文本构建摘要 <公开 静态 类型 = 文本型'
HELPER_NEW = '''    方法 解析双文本表 <公开 静态 类型 = FBrowser_双文本数组 @输出名 = "ParseDoubleTextTable" @强制输出 = 真>
    参数 文本 <类型 = 文本型 @输出名 = "Text">
    {
        // 把紧凑写法 "brand:version,brand2:version2" 解析成类库的 FBrowser_双文本数组 ——
        // browser_fingerprint_ua 的 brands / full_version_list 要的就是它。
        // 为什么不用 JSON 数组: 本项目存在 YYJSON 嵌套数组的崩溃风险, 紧凑文本既避开它,
        // 也更好让 AI 生成; 没有冒号的一段按"只有 brand、version 留空"处理。
        变量 结果 <类型 = FBrowser_双文本数组>
        结果.创建 ()
        变量 段数组 <类型 = 文本数组类>
        分割文本 (文本, ",", 段数组, 真, 真)
        变量 段数 <类型 = 整数>
        段数 = 段数组.取成员数 ()
        计次循环 (段数)
        {
            变量 一段 <类型 = 文本型>
            一段 = 删首尾空 (段数组.取成员 (取循环索引 ()))
            如果 (一段 != "")
            {
                变量 项 <类型 = FBrowser_双文本>
                变量 冒号位 <类型 = 整数>
                冒号位 = 寻找文本 (一段, ":", 0, 假)
                如果 (冒号位 == -1)
                {
                    项.name = 一段
                    项.value = ""
                }
                否则
                {
                    项.name = 取文本左边 (一段, 冒号位)
                    项.value = 取文本中间 (一段, 冒号位 + 1, 取文本长度 (一段) - 冒号位 - 1)
                }
                结果.加入成员 (项)
            }
        }
        返回 (结果)
    }

'''

VIP_ANCHOR = '                ua_data.置Wow64 (MCP命令服务器.yyjson取逻辑 (参数JSON, "wow64"))'
VIP_NEW = VIP_ANCHOR + '''
                // ★ 补能力(能力面反查确认的真缺口, VIP 审计排名第 1): 原来只设 8 个 UA 字段,
                //   漏掉 UA-CH(navigator.userAgentData) 的 brands/fullVersionList/platformVersion/fullVersion。
                //   只改 UA 字符串而不改 UA-CH, 两者不一致反而**更容易被识别**, 故必须能一起设。
                //   类库签名(实读): 置PlatformVersion(文本) / 置FullVersion(文本) /
                //   置Brands(FBrowser_双文本数组) / 置FullVersionList(FBrowser_双文本数组)。
                //   品牌表用紧凑文本 "Chromium:120,Google Chrome:120"(见 解析双文本表)。
                如果 (MCP命令服务器.yyjson取文本 (参数JSON, "platform_version") != "")
                {
                    ua_data.置PlatformVersion (MCP命令服务器.yyjson取文本 (参数JSON, "platform_version"))
                }
                如果 (MCP命令服务器.yyjson取文本 (参数JSON, "full_version") != "")
                {
                    ua_data.置FullVersion (MCP命令服务器.yyjson取文本 (参数JSON, "full_version"))
                }
                如果 (MCP命令服务器.yyjson取文本 (参数JSON, "brands") != "")
                {
                    ua_data.置Brands (MCP命令服务器.解析双文本表 (MCP命令服务器.yyjson取文本 (参数JSON, "brands")))
                }
                如果 (MCP命令服务器.yyjson取文本 (参数JSON, "full_version_list") != "")
                {
                    ua_data.置FullVersionList (MCP命令服务器.解析双文本表 (MCP命令服务器.yyjson取文本 (参数JSON, "full_version_list")))
                }'''

SCHEMA_OLD = ('属性项JSON ("wow64", "boolean", "wow64"), ""))')
SCHEMA_NEW = ('属性项JSON ("wow64", "boolean", "wow64") + "," + '
              '属性项JSON ("platform_version", "text", "UA-CH: navigator.userAgentData.platformVersion (如 15.0.0)") + "," + '
              '属性项JSON ("full_version", "text", "UA-CH: navigator.userAgentData.fullVersion (如 120.0.6099.109)") + "," + '
              '属性项JSON ("brands", "text", "UA-CH: navigator.userAgentData.brands。紧凑写法 \\"brand:version,brand2:version2\\" '
              '(例: Chromium:120,Google Chrome:120)。建议与 ua 保持同版本, 两者不一致比不伪装更容易被识别") + "," + '
              '属性项JSON ("full_version_list", "text", "UA-CH: navigator.userAgentData.fullVersionList, 写法同 brands")'
              ', ""))')

EDITS = [
    ('SRV helper', SRV, HELPER_ANCHOR, HELPER_NEW + HELPER_ANCHOR),
    ('VIP 四字段', VIP, VIP_ANCHOR, VIP_NEW),
    ('SRV schema', SRV, SCHEMA_OLD, SCHEMA_NEW),
]


def main():
    texts = {p: io.open(p, encoding='utf-8', newline='').read() for p in (SRV, VIP)}
    for label, path, old, new in EDITS:
        n = texts[path].count(old)
        print("[%-12s] %s 出现 %d 次" % (label, os.path.basename(path), n))
        if n != 1:
            print("   !! 预期 1 次, 中止(不改任何文件)")
            return 1
    if '解析双文本表' in texts[SRV]:
        print("!! 似乎已添加过, 中止")
        return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    for p in (SRV, VIP):
        shutil.copy2(p, os.path.join(BAK, os.path.basename(p)))
    print("已备份到 %s" % BAK)
    for label, path, old, new in EDITS:
        texts[path] = texts[path].replace(old, new)
    for p, t in texts.items():
        io.open(p, 'w', encoding='utf-8', newline='').write(t)
    print("OK: 3 处替换完成")
    for p in (SRV, VIP):
        raw = io.open(p, 'rb').read()
        print("复核 %-24s BOM=%s CRLF=%s 字节=%d"
              % (os.path.basename(p), raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
