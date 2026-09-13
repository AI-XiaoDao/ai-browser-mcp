# -*- coding: utf-8 -*-
r"""追加报告 §134(第117轮): browser_hash(MD5/文件MD5/XXH128/CRC32) 落地并验证 + 推翻"缺头文件"排除理由。

注意: SEC 必须是**原始字符串** —— 正文含 Windows 路径(`classlib\user\yw`), 普通三引号会把 `\u` 当转义。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = r"""
---

## 134. 第117轮：哈希能力落地（MD5 / 文件MD5 / XXH128 / CRC32，工具 319 → 320），并**推翻**一条被写进计划的排除理由

### 134.1 先推翻"缺头文件"这个排除理由

`_audit/_codec_plan_r115.md` 把 MD5/SHA 列为排除项，理由是"技能资料目录里没有 `md5\md5_.h`、`jjm\include\lz4.c`、
`XxHash\xxhash.hpp`，接线会编译失败"。上一轮我顺带做了只读核对（`_audit/_hash_availability_r116.md`），实测：

| 检查 | 结果 |
|---|---|
| `E:\HSPC\plugins\vprj_win\classlib\user\yw` | **存在**（同一层还有 `piv` / `FC` / `zlib`） |
| `\md5\md5_.h` + `\md5\md5_.cpp` | **都在** |
| `\XxHash\xxhash.hpp`（+ `.h`）、`\jjm\include\lz4.*` | **都在** |
| `仰望模块` 是否在项目里 | **在** `AI-Fbowser-Mcp.vprj` 的模块表里（与 `视窗基本类`/`FBrowser浏览器`/`yyJSON`/`SQLite数据库` 并列） |

⇒ 缺的只是"技能资料的副本"，**不是本机类库**。**一次 `/c` 编译就判定了**：接线成功、0 错误 —— 于是有了本轮的工具。

> 教训（值得记）："某个头文件不在技能资料里"**不能**推出"本机不可用"。同类判断以后一律**先编译一次**再下结论，
> 而不是把"资料缺副本"写成"能力不可用"。

### 134.2 `browser_hash`：能力、实现、诚实性处理

| action | 类库调用（`加密解密库__p.wsv` 原文） | 说明 |
|---|---|---|
| `md5` | `MD5类_.取数据摘要_ (字节集, 是否小写)` (:60) | 文本按 UTF-8 取字节 |
| `md5_file` | `MD5类_.取数据摘要3_ (路径, 是否小写)` (:83) | 类库注明"**支持大文件**" |
| `xxhash` | `XxHash数据摘要类_.取数据摘要_XxHash_数据 (数据, 长度, 种子)` (:10) | XXH128，32 位十六进制 |
| `crc32` | `CRC校验类_.取数据摘要_CRC32 (字节集, 初始值)` (:36) | 走 ntdll，**无需外部头** |

**两处诚实性处理（都不是"照抄类库"就能得到的）**：
1. **文件摘要先校验存在**：类库 `取数据摘要2_` 的实现是 `取数据摘要_ (读入文件 (路径))` —— 文件读不到就是**空字节集**，
   于是会**静默返回空文件的 MD5**（`d41d8cd98f00b204e9800998ecf8427e`）。实测确认这条守卫生效（见 134.3 的用例）。
2. **CRC32 同时给有符号与无符号**：类库返回 `整数`(int32)，故 `crc32("123456789") = -873187034`；
   而 CRC-32/ISO-HDLC 的**标准校验值是 `0xCBF43926` = 3421780262**。两者是同一组 32 位，但用户拿标准值对照会以为算错 ——
   故回包同时给 `crc32`（类库原样）与 `crc32_unsigned`（加 2³² 归一，纯算术实现，不引位运算语义风险）。

**不做 HMAC-MD5**：那一段走 CNG（`bcrypt.h` + `Bcrypt.lib`），本轮不引入新的链接依赖。

### 134.3 验收 **17/17**（`_audit/verify_hash_r117.py`；期望值由 hashlib / zlib **独立算准**）

| 用例 | 期望（独立来源） | 实测 |
|---|---|---|
| `md5("hello")` | `5d41402abc4b2a76b9719d911017c592` | ✔ |
| `md5("abc")` | `900150983cd24fb0d6963f7d28e17f72` | ✔ |
| `md5("中文测试")` | `089b4943ea034acfa445d050c7913e55`（UTF-8） | ✔ |
| `uppercase:true` | 全大写 | ✔ |
| `md5_file`(自造 ~80KB 文件) | `hashlib.md5(同字节)` | ✔ |
| **不存在的文件** | **必须明确报错** | ✔ 且**未**返回 `d41d8cd9…` |
| `crc32("hello")` | 907060870 | ✔（有符号/无符号一致） |
| `crc32("123456789")` | **3421780262 / 0xCBF43926** | ✔（`crc32_unsigned`；有符号同时给 `-873187034`） |
| `xxhash("hello")` | 32 位十六进制 + 确定性 + 区分度 | ✔（**本机无 xxhash 参考实现，故只做性质验证，未用绝对向量** —— 如实记录） |
| 守卫 | 缺 `action` / 缺 `data` / 未知 action | ✔ 三条都可行动（未知 action 列出全部可用值） |

### 134.4 本轮我自己踩的坑（全部被工具或编译器拦住，记录以免重犯）

1. **Python 脚本 docstring 里的 Windows 路径**：`classlib\user\yw` 里的 `\u` 被当成转义，脚本直接
   `SyntaxError: truncated \uXXXX escape` **根本没跑起来**（先是在报告生成脚本上，接着又在补丁脚本上）⇒
   凡 docstring/正文字符串含 Windows 路径，**一律用"原始字符串"**（字符串前缀加字母 r，正文里不要写出那三个引号本身）。
2. **`% TOOL` 前多了一个逗号** ⇒ 语法错（`SyntaxError: invalid syntax`）。
3. **描述串漏了收尾引号**：工具登记行会变成"字符串跨两行"，被我自己的**引号奇偶自检**拦下（未写盘）—— 补做后才写对。
4. **两处编译错误**：本项目**不存在** `到长整数 (整数)`（只有 `文本到长整数`），且 `加入整数成员` 收 `整数`
   会报精度损失 ⇒ 改为**加宽隐式赋值** + 已存在的 `加入长整数成员`（项目里 3 处在用）。
5. **台账探针缺参**：`browser_hash` 首次被记为 fail，原因是探针只给 `action` 不给 `data`，
   被"空串摘要无意义"守卫**正确拒绝** ⇒ 已给 `mass_probe` 补 `{"action":"md5","data":"mcp_probe"}`，重测 **pass**。

### 134.5 回归钉与状态

`_audit/fastcheck.py` 新增 3 条哈希回归钉（MD5 权威值 / CRC32 标准无符号值 / 不存在文件必须报错）：
**51 → 54 项，3.3 秒全绿**。

工具总数 **320**；台账 **320/320**（通过 313 / 失败 7，仍是那 7 条已知探针产物或刻意守卫）；编译 **0 警告**。

### 134.6 本轮并行派发（交付未回，故不含任何"已完成"结论）

1. **启动期开关通道**（摄像头/录音/自动播放/禁用GPU 三连）：走 `main.wsv` 现成的 `即将处理命令行` 钩子 +
   `mcp_config.json` 独立布尔键；**禁走** `取全局命令行`（有失败原文证据）、**禁接** `启用无头模式`（类库复制粘贴 bug）。
2. **"操作备注"清理**（242 条）：要求逐条三选一（删/改/留）并给出依据，**优先保护**那些承载唯一实测结论的注释。
3. **类库缺口刷新**：以当前 320 工具为基线做交叉核对（旧清单已过期），并主动排除历史误报。
"""


def main():
    data = open(REP, 'rb').read()
    if data.startswith(b'\xef\xbb\xbf'):
        print('!! 报告有 BOM')
        return 1
    text = data.decode('utf-8')
    if '\r' in text:
        print('!! 报告含 CR')
        return 1
    if '## 134. 第117轮' in text:
        print('!! §134 已存在')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 134. 第117轮') == 1
    print('已追加 §134; 行数 %d -> %d (无 BOM / 无 CR / 唯一)' % (text.count('\n') + 1, t2.count('\n') + 1))
    return 0


sys.exit(main())
