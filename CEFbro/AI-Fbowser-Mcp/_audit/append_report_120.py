# -*- coding: utf-8 -*-
"""追加报告第 120 节（第 103 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 120. 第103轮：`browser_intercept` 新增 `unmodify`/`unreplace`（按 URL 撤销单条规则）+ 顺带证实整个拦截通道是好的

### 120.1 能力缺口：以前**只能全清、不能撤一条**

`browser_intercept` 的 13 个 action 里，`clear` 是**整体清零**；改错一条规则就得推倒重建全部规则。
类库侧其实有 `过滤器_取消修改内容`/`过滤器_取消替换资源`（只收一个 `目标地址`、无索引 ⇒ 按 URL 撤销），
但那是 **VIP 过滤器**通道，而本项目 `browser_intercept` 走的是**手写 ResponseFilter 通道**，
VIP 添加侧全树零调用（第100轮子代理已证实）⇒ 只需给手写通道补"按 URL 删行"。

### 120.2 实现（不重复造轮子：直接照 `添加资源替换规则` 的存储格式来）

- **新 helper** `MCP命令服务器.删除资源替换规则 (目标URL, 限定动作) → 整数`（返回实际删除条数）
  落在 `MCP_Server.wsv`，紧接 `添加资源替换规则` 之后。要点：
  · 全程持 `规则锁`（照抄 add 的加解锁）；
  · `分割文本 (…, "\\n", …, 真, 假)` 拆行、`分割文本 (…, "|", …, 假, 假)` 拆段（照抄匹配器）；
  · **URL 段必须先 `规则字段反转义` 再比较** —— 存储时 URL 是转义过的，
    否则带 `%` / `|` / 换行的 URL 永远删不掉；
  · `目标URL == ""` 直接返回 0（防"空串子串匹配到全部"把规则误删光）；
  · 限定动作为空=删所有动作类，传 `"replace_file"` 则只删文件替换类（供 `unreplace`）。
- **两个 action** 落在 `MCP_Server_Core.wsv` 的 `browser_intercept` 分派链尾部
  （`line_replace` 之后、未知 action 之前），因此**自动继承既有的 `url` 必填校验**。

**口径（刻意与"命中"完全一致）**：请求URL **包含** 规则URL 即算该规则 ——
与 `匹配资源篡改规则` 的 `寻找文本 (目标URL, 规则URL, 0, 假)` 同一条判据。
返回文本里**显式写出**了这条口径、以及"作用域: 手写过滤器通道(不含 VIP 过滤器)"。

**撤销不存在的规则 = 幂等成功 + 如实回报 0 条**（不报失败）：
与项目既有惯例一致（`clear` 无条件成功、`popup_disable` 同理），
且"该 URL 不再被改"这一目标状态本已达成 —— 报失败只会诱发 AI 反复重试。

三处对外描述同步更新：schema 的 action 枚举与描述、`browser_intercept` 帮助文本、未知 action 的错误枚举。

### 120.3 验收：7/7（行为级回读）

`_audit/verify_unmodify2.py`（**7/7**）：

| 臂 | 期望 | 实测 |
|---|---|---|
| A 基线（全新 URL） | 未被屏蔽 | `Example Domain` ✔ |
| B 加 `block` 规则 | 被屏蔽 | `资源已屏蔽 (MCP intercept block)` ✔ |
| C `unmodify`（完整 URL 指定） | 报**撤销 1 条** | `…撤销资源替换规则 1 条…` ✔ |
| D 撤销后访问**另一个全新 URL** | 恢复正常 | `Example Domain` ✔ |
| E 再 `unmodify`（规则已不存在） | 幂等成功 + 报 **0 条** | ✔ |
| F `unreplace`（无 replace_file 规则） | 幂等成功 + 报 0 条 | ✔ |
| G `replace_data` 规则也能被 `unmodify` 撤销 | 动作不限 | 改前 `REPLACED-BODY` → 撤销后 `Example Domain` ✔ |

### 120.4 ★探针自坑（第四次）：**浏览器缓存**把拦截效果盖掉了

第一版验收的对照臂 B 判"block 无效"。若就此下结论，就会把**好端端的功能**报成坏掉。
实际原因是**缓存**：对**同一个 URL** 反复导航会命中缓存，过滤器根本不会被调用。
用捕获 stderr 的进程日志一看，通道完全正常：

```
[MCP] 资源Hook已激活, 规则:block|example.com
[MCP] 手写篡改已挂载: block → https://example.com/?diag=1
[MCP篡改] 初始化 动作=block
```

且页面上确实出现了屏蔽页正文。修正做法：**每一步都用各不相同的 URL**（规则用子串
`example.com/?unmod` 去匹配 `?unmod=1/2/3/4`），从此缓存不再是变量。

**教训（写进纪律）**：验证"改写响应"类能力时，**同 URL 重复导航是无效操作** ——
必须换 URL 或强制 `browser_reload` 重新发起请求；否则会把缓存命中误判成"功能失效"。

### 120.5 顺带证实：`browser_intercept` 的拦截能力**是真的**

第98轮的台账把它记为 `pass`，但那只是 `action=clear` 这一最平凡分支。
本轮用行为回读证明 **block / modify / replace_data 三条主路径都真实生效**
（屏蔽页正文、`REPLACED-BODY` 替换正文均实见于页面），并已把台账探针改为
`action=unmodify` 指向一个**永不匹配**的域名（幂等 0 条、不改状态，却能真正走一遍规则解析路径），
使台账不再只测到平凡分支。

### 120.6 状态与下一步

台账 **313/313** 已测，通过 306 / 失败 7（TARGET 3 / OTHER 2 / GUARD 1 / PARAM 1），
**前置缺失 0、能力缺失 0、卡死 0**；编译 0 警告；fastcheck 41/41。

1. **`browser_context_menu`（方案甲）**：CEF 头逐字禁止回调外持引用 → 预置规格 + 在
   `浏览器_即将打开菜单` 回调内一次性施加。
2. **修 `将异步结果转为命令响应` 的载荷形状覆盖**后把 `browser_permission_spoof` 也纳入同步
   （第100轮因 20s 超时撤回）。
3. 复查 `browser_back`/`browser_forward` 是否补 `wait_for_load`（能力增强，按真实调用频率定夺）。
"""


def main():
    data = open(REP, 'rb').read()
    if data.startswith(b'\xef\xbb\xbf'):
        print('!! 有 BOM, 中止')
        return 1
    text = data.decode('utf-8')
    if '\r' in text:
        print('!! 含 CR, 中止')
        return 1
    if '## 120. 第103轮' in text:
        print('!! §120 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 120. 第103轮') == 1
    print('已追加 §120; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
