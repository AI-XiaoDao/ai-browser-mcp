# -*- coding: utf-8 -*-
"""把第 93 节(第 77 轮)追加到 MCP工具可用性检测报告.md。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, "MCP工具可用性检测报告.md")

SECTION = """
---

## 93. 第 77 轮：为 P1「宿主侧 URL 请求定制」备料(API 事实核清)，并如实推迟实现

### 93.1 本轮做了什么、以及**没做什么**
目标是审计确认的 P1 缺口: `browser_create_url_request` 目前只能设 `url` + `method`,
无法自定义请求头/请求体/cookie 归属域; 根因是 `类_MCP_URL请求回调` **没有 override `开始创建`** ——
而那是唯一能拿到 `URL请求.取请求()` 并设置一切的时机。

本轮把这条路径所需的**类库事实**逐条核清(下表), 但在评估工作量后**决定不在本轮动实现**:
它要新引入 3~4 个类库类型(双文本/双文本数组/POST数据/POST元素/读取流), 且 POST 体要经
`FBrowser_读取流_从数据创建 (数据指针, 数据大小)` —— 从火山侧要拿裸指针, 属**难验证**的那一类。
按本项目纪律(不交付未经验证的能力、不静默假成功), 与其半成品落地, 不如把事实固化下来交下一轮。

### 93.2 已核清的类库事实(可直接用于实现, 全部来自技能资料原文)

| 用途 | 签名(逐字) | 出处 |
|---|---|---|
| 唯一设置时机 | `方法 开始创建 <公开 @虚拟方法 = 可覆盖>` / `参数 标识 <长整数>` / `参数 URL请求 <类_FBrowser_URL请求>` | FBroEventControl.wsv:2282 |
| 取请求对象 | `类_FBrowser_URL请求.取请求 () → 类_FBrowser_请求` | FBroLib.wsv:5572 |
| 整套拼装 | `类_FBrowser_请求.设置 (地址:文本型, 类型:文本型[大写POST/GET], POST数据:类_FBrowser_POST数据, 协议头数据:FBrowser_双文本)` | FBroLib.wsv:2407 |
| 请求标识 | `类_FBrowser_请求.设置标识 (标识:整数)` 注释"参考: 请求标识.xxx" | FBroLib.wsv:2424 |
| cookie 归属域 | `类_FBrowser_请求.设置地址_首件cookie (地址:文本型)` | FBroLib.wsv:2439 |
| POST 体元素 | `类_FBrowser_POST数据.增加元素 (POST元素:类_FBrowser_POST元素)` | FBroLib.wsv:2538 |
| 读回 POST 体 | `类_FBrowser_请求.取POST数据 () → 类_FBrowser_POST数据` | FBroLib.wsv:2342 |

**两条容易踩的类型事实**:
1. `FBrowser_双文本` **只有两个公开字段** `name` / `value`(FBroDataType.wsv:778), 即"一对"键值;
   而 `设置(...)` 的 `协议头数据` 形参类型就是它 —— 故**一次只能带一对头**, 需要多头要另行查是否有数组版入口
   (`FBrowser_双文本数组` 在 FBroDataType.wsv:805 存在, 但 `设置` 的形参不是它)。
2. 我头一次按"类名前缀"抓这个类的方法列表时**抓错了类**: `类_FBrowser_请求` 是
   `类_FBrowser_请求环境` 的前缀, 正则 `^\\s*类 类_FBrowser_请求` 命中的是后者 ——
   列出来的方法全是"请求环境"的(取缓存路径/载入插件路径…)。**取类 API 时必须写成精确类名匹配**,
   否则会拿着另一个类的方法清单去做设计(这类"前缀撞名"在中文类库里很常见)。

### 93.3 本轮的实际产出
- 台账 **234 → 239/312**(以 `--next 10` 推进, 5 条落账、0.2s、无冷重启);
- 上表把 P1 缺口的实现障碍从"要现场摸索"降为"照着签名接",
  并明确标注了唯一的硬骨头(POST 体需要裸指针)与一处待查(多头是否有数组入口)。

### 93.4 诚实结论
**本轮没有新增能力, 只有"备料 + 覆盖推进"。** 之所以专门写下来, 是因为这类"看起来像没干活"的轮次
如果不留证据, 下一轮很容易又从头摸一遍同一批签名; 而"评估后决定推迟"与"做了一半就交"相比,
前者对最终目标(所有能力完整可用)是**更负责任**的一步。

台账指标: **前置缺失类失败维持 0、把实例卡死维持 0**, 剩余失败仍全部落在
目标不存在 / 参数非法 / 本机不支持 / 需编排这些可接受类别。
"""

b = io.open(P, "rb").read()
assert b[:3] != b"\xef\xbb\xbf" and b.count(b"\r\n") == 0
txt = b.decode("utf-8")
assert "## 93." not in txt
io.open(P, "w", encoding="utf-8", newline="\n").write(txt + SECTION)
nb = io.open(P, "rb").read()
print("追加完成: %d -> %d 字节, 行数 %d -> %d"
      % (len(b), len(nb), b.count(b"\n") + 1, nb.count(b"\n") + 1))
