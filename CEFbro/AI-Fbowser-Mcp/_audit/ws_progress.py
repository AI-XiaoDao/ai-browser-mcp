# -*- coding: utf-8 -*-
"""最小 WebSocket 客户端 — 验证 notifications/progress 是否真的推到 WS 通道。

流程: 握手 -> 发一个带 _meta.progressToken 的 tools/call(慢工具) -> 收帧
       -> 打印所有 notifications/progress 帧 (以及最终响应)。
不依赖第三方库 (手写 RFC6455 握手 + 帧编解码)。
"""
import base64
import json
import os
import socket
import struct
import sys
import time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HOST, PORT = "127.0.0.1", 9222
PATH = "/mcp"


def handshake(s):
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        "GET %s HTTP/1.1\r\n"
        "Host: %s:%d\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: %s\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n" % (PATH, HOST, PORT, key)
    )
    s.sendall(req.encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = s.recv(4096)
        if not chunk:
            raise RuntimeError("握手期间连接被关闭")
        buf += chunk
    head, _, rest = buf.partition(b"\r\n\r\n")
    line = head.split(b"\r\n")[0].decode(errors="replace")
    if "101" not in line:
        raise RuntimeError("握手失败: %s" % line)
    return rest


def send_text(s, text):
    payload = text.encode("utf-8")
    header = bytearray([0x81])
    n = len(payload)
    if n < 126:
        header.append(0x80 | n)
    elif n < 65536:
        header.append(0x80 | 126)
        header += struct.pack(">H", n)
    else:
        header.append(0x80 | 127)
        header += struct.pack(">Q", n)
    mask = os.urandom(4)
    header += mask
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    s.sendall(bytes(header) + masked)


class Reader:
    def __init__(self, s, initial=b""):
        self.s = s
        self.buf = initial

    def _need(self, n, timeout):
        end = time.time() + timeout
        while len(self.buf) < n:
            self.s.settimeout(max(0.05, end - time.time()))
            try:
                chunk = self.s.recv(65536)
            except socket.timeout:
                return False
            if not chunk:
                return False
            self.buf += chunk
        return True

    def frame(self, timeout):
        if not self._need(2, timeout):
            return None
        b0, b1 = self.buf[0], self.buf[1]
        opcode = b0 & 0x0F
        masked = b1 & 0x80
        ln = b1 & 0x7F
        off = 2
        if ln == 126:
            if not self._need(4, timeout):
                return None
            ln = struct.unpack(">H", self.buf[2:4])[0]
            off = 4
        elif ln == 127:
            if not self._need(10, timeout):
                return None
            ln = struct.unpack(">Q", self.buf[2:10])[0]
            off = 10
        if masked:
            off += 4
        if not self._need(off + ln, timeout):
            return None
        payload = self.buf[off:off + ln]
        self.buf = self.buf[off + ln:]
        if masked:
            m = self.buf[off - 4:off] if False else None
        return opcode, payload


SCENARIOS = {
    # 场景名 -> (工具名, 参数)  —— 避免经 shell 传 JSON (引号会被吞)
    "nav": ("browser_navigate", {"url": "https://example.com", "sync_wait": True}),
    "navbaidu": ("browser_navigate", {"url": "https://www.baidu.com", "sync_wait": True}),
    "flow": ("browser_debugger_flow", {"url": "https://example.com", "breakpoint": "document"}),
    "gettext": ("browser_get_text", {"selector": "body", "sync_wait": True}),
    # 保证长时间等待: what=timeout 固定等 max_ms 毫秒 -> 必有大量轮询迭代
    "wait6": ("browser_wait", {"what": "timeout", "max_ms": 6000}),
    "wait12": ("browser_wait", {"what": "timeout", "max_ms": 12000}),
    # 显式走 同步等待异步任务 的工具 (Core:6393 等)
    "snapshot": ("browser_snapshot", {}),
    "forms": ("browser_get_forms", {}),
}


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "nav"
    window = float(sys.argv[2]) if len(sys.argv) > 2 else 45.0
    if name not in SCENARIOS:
        print("未知场景 %s, 可选: %s" % (name, ", ".join(SCENARIOS)))
        return
    tool, args = SCENARIOS[name]

    s = socket.create_connection((HOST, PORT), timeout=10)
    rest = handshake(s)
    print("WS 握手成功 (101)")

    req = {
        "jsonrpc": "2.0", "id": 9001, "method": "tools/call",
        "params": {
            "name": tool,
            "arguments": args,
            "_meta": {"progressToken": "tok-verify-1"},
        },
    }
    send_text(s, json.dumps(req, ensure_ascii=False))
    print("已发送 tools/call: %s %s" % (tool, json.dumps(args, ensure_ascii=False)))

    r = Reader(s, rest)
    prog, other, final = [], [], None
    t0 = time.time()
    while time.time() - t0 < window:
        fr = r.frame(window - (time.time() - t0))
        if fr is None:
            break
        opcode, payload = fr
        if opcode == 0x8:
            print("收到关闭帧")
            break
        if opcode == 0x9:
            continue
        if opcode not in (0x1, 0x2):
            continue
        try:
            obj = json.loads(payload.decode("utf-8"))
        except Exception:
            other.append(payload[:200])
            continue
        el = time.time() - t0
        if obj.get("method") == "notifications/progress":
            prog.append((el, obj))
            print("  [%.2fs] ★ notifications/progress: %s" % (el, json.dumps(obj.get("params"), ensure_ascii=False)))
        elif obj.get("id") == 9001:
            final = obj
            print("  [%.2fs] 最终响应: %s" % (el, json.dumps(obj, ensure_ascii=False)[:400]))
            break
        else:
            other.append(obj)
            print("  [%.2fs] 其它消息: %s" % (el, json.dumps(obj, ensure_ascii=False)[:200]))

    print()
    print("=" * 80)
    print("进度帧数: %d" % len(prog))
    print("最终响应: %s" % ("有" if final else "无"))
    if prog:
        keys = set()
        for _, o in prog:
            keys |= set(o.get("params", {}).keys())
        print("进度帧字段: %s" % ", ".join(sorted(keys)))
        print("✅ notifications/progress 已通过 WebSocket 通道实际推送")
    else:
        print("❌ 未收到进度帧")
    s.close()


if __name__ == "__main__":
    main()
