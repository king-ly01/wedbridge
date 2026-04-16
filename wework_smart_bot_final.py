# encoding:utf-8
"""
企业微信智能机器人 + Dify 工作流 桥接服务

依赖：
    pip install wecom-aibot-sdk-python aiohttp --break-system-packages

使用方法：
    1. 编辑 config.json，填入企业微信和 Dify 的配置
    2. 运行: python wework_smart_bot_final.py

Dify HTTP 节点主动通知接口：
    POST http://localhost:{notify_port}/notify
    Body: {"chatid": "{{chatid}}", "content": "消息内容"}
    Response: {"ok": true}
"""

import asyncio
import json
import logging
import os
import aiohttp
from aiohttp import web
from wecom_aibot_sdk import WSClient, generate_req_id, DefaultLogger

# ──────────────────────────────────────────────────────────
# 加载配置
# ──────────────────────────────────────────────────────────
_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config() -> dict:
    with open(_CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)

cfg = load_config()

BOT_ID          = cfg["wecom"]["bot_id"]
SECRET          = cfg["wecom"]["secret"]

DIFY_API_BASE   = cfg["dify"]["api_base"]
DIFY_API_KEY    = cfg["dify"]["api_key"]
DIFY_INPUT_VAR  = cfg["dify"]["input_variable"]
DIFY_OUTPUT_VAR = cfg["dify"]["output_variable"]
DIFY_TIMEOUT    = cfg["dify"].get("timeout", 60)

WELCOME_MSG  = cfg["service"].get("welcome_message", "你好！有什么可以帮你的吗？")
THINKING_MSG = cfg["service"].get("thinking_message", "⏳ 思考中...")
LOG_LEVEL    = getattr(logging, cfg["service"].get("log_level", "INFO").upper(), logging.INFO)
NOTIFY_PORT     = cfg["service"].get("notify_port", 8899)
NOTIFY_URL      = cfg["service"].get("notify_url_for_dify", f"http://172.17.0.1:{cfg['service'].get('notify_port', 8899)}/notify")
DEFAULT_CHATID  = cfg["service"].get("default_chatid", "")

# 全局 client 引用（供 notify 接口使用）
_ws_client: WSClient = None


# ──────────────────────────────────────────────────────────
# Dify 工作流调用
# ──────────────────────────────────────────────────────────
async def call_dify_workflow(query: str, user_id: str, chatid: str) -> str:
    """
    调用 Dify 工作流。
    除了用户输入变量，还会传入 chatid，
    工作流 HTTP 节点可用 chatid 回调 /notify 接口发中间消息。
    """
    url = f"{DIFY_API_BASE}/workflows/run"
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": {
            DIFY_INPUT_VAR: query,
            "chatid": chatid,       # 传给工作流，供 HTTP 节点回调用
        },
        "response_mode": "blocking",
        "user": user_id,
    }

    try:
        timeout = aiohttp.ClientTimeout(total=DIFY_TIMEOUT)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=timeout) as resp:
                result = await resp.json()
                if resp.status == 200:
                    outputs = result.get("data", {}).get("outputs", {})
                    return outputs.get(DIFY_OUTPUT_VAR, str(outputs))
                else:
                    msg = result.get("message", "未知错误")
                    print(f"[Dify] 调用失败 {resp.status}: {msg}")
                    return f"Dify 调用失败: {msg}"
    except asyncio.TimeoutError:
        return "Dify 响应超时，请稍后重试"
    except Exception as e:
        return f"调用出错: {e}"


# ──────────────────────────────────────────────────────────
# Notify HTTP 服务（供 Dify HTTP 节点调用）
# ──────────────────────────────────────────────────────────
async def handle_notify(request: web.Request) -> web.Response:
    """
    POST /notify
    Body JSON: {"chatid": "xxx", "content": "消息内容"}

    Dify HTTP 节点配置示例：
      URL: http://localhost:8899/notify
      Method: POST
      Body: {"chatid": "{{chatid}}", "content": "你好，这是中间消息"}
    """
    global _ws_client
    try:
        # 清除控制字符后再解析（Dify 变量展开后可能含 \n 等）
        raw = await request.text()
        raw = "".join(c for c in raw if c >= " " or c == "\t")
        data = json.loads(raw)
        chatid  = str(data.get("chatid", "")).strip() or DEFAULT_CHATID
        # 兼容两种格式：
        # 新格式: {"content": "xxx"}
        # 企微原生格式: {"msgtype":"text","text":{"content":"xxx"}}
        content = str(data.get("content", "")).strip()
        if not content:
            content = str(data.get("text", {}).get("content", "")).strip()

        if not chatid or not content:
            return web.json_response({"ok": False, "error": "chatid 和 content 不能为空"}, status=400)

        if _ws_client is None or not _ws_client.is_connected:
            return web.json_response({"ok": False, "error": "企业微信未连接"}, status=503)

        await _ws_client.send_message(chatid, {
            "msgtype": "markdown",
            "markdown": {"content": content},
        })

        print(f"[Notify] → {chatid}: {content[:60]}")
        return web.json_response({"ok": True})

    except Exception as e:
        print(f"[Notify] 错误: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def start_notify_server():
    """启动 notify HTTP 服务"""
    app = web.Application()
    app.router.add_post("/notify", handle_notify)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", NOTIFY_PORT)
    await site.start()
    print(f"[Notify] HTTP 服务已启动: http://localhost:{NOTIFY_PORT}/notify")


# ──────────────────────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────────────────────
async def main():
    global _ws_client

    print("=" * 60)
    print("企业微信智能机器人 + Dify 桥接服务")
    print("=" * 60)
    print(f"Bot ID        : {BOT_ID[:20]}...")
    print(f"Dify API      : {DIFY_API_BASE}")
    print(f"输入变量      : {DIFY_INPUT_VAR}")
    print(f"输出变量      : {DIFY_OUTPUT_VAR}")
    print(f"Notify 端口   : {NOTIFY_PORT}")
    print(f"Dify回调URL   : {NOTIFY_URL}")
    print("=" * 60)

    # 启动 notify 服务
    await start_notify_server()

    logger = DefaultLogger(level=LOG_LEVEL)
    client = WSClient({
        "bot_id": BOT_ID,
        "secret": SECRET,
        "logger": logger,
    })
    _ws_client = client

    async def on_connected(*args):
        print("[连接] WebSocket 已连接")

    async def on_authenticated(*args):
        print("[认证] 认证成功，开始接收消息")

    async def on_disconnected(reason):
        print(f"[断开] {reason}")

    async def on_reconnecting(attempt):
        print(f"[重连] 第 {attempt} 次尝试...")

    async def on_enter(frame):
        await client.reply_welcome(frame, {
            "msgtype": "text",
            "text": {"content": WELCOME_MSG},
        })

    async def on_text(frame):
        content = frame.body.get("text", {}).get("content", "").strip()
        sender  = frame.body.get("from", {}).get("userid", "") or frame.body.get("from", {}).get("id", "unknown")
        chatid  = frame.body.get("chatid", sender)

        if not content:
            return

        print(f"\n[收到] {sender} (chatid={chatid}): {content}")

        stream_id = generate_req_id("stream")
        await client.reply_stream(frame, stream_id, THINKING_MSG, finish=False)

        reply = await call_dify_workflow(content, sender, chatid)
        print(f"[回复] {reply[:80]}{'...' if len(reply) > 80 else ''}")

        await client.reply_stream(frame, stream_id, reply, finish=True)

    client.on("connected",        on_connected)
    client.on("authenticated",    on_authenticated)
    client.on("disconnected",     on_disconnected)
    client.on("reconnecting",     on_reconnecting)
    client.on("event.enter_chat", on_enter)
    client.on("message.text",     on_text)

    print("\n[启动] 正在连接企业微信服务器...")
    print("[提示] 按 Ctrl+C 停止\n")

    await client.connect_async()

    try:
        while client.is_connected:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n[停止] 服务已停止")
        client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
