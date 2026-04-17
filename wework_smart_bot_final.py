# encoding:utf-8
"""
企业微信智能机器人 + Dify 工作流 多机器人桥接服务

支持多个企微机器人同时运行，每个机器人对应独立的 Dify 工作流。
通过 config.json 的 bots 数组统一配置，token 实现路由认证。

依赖：
    pip install wecom-aibot-sdk-python aiohttp --break-system-packages

使用方法：
    1. 编辑 config.json，在 bots 数组中配置每个机器人
    2. 运行: python wework_smart_bot_final.py

Dify HTTP 节点主动通知接口：
    POST http://<host>:{notify_port}/notify
    Body: {"token": "your-bot-token", "content": "消息内容", "chatid": "可选"}
    Response: {"ok": true}
"""

import asyncio
import json
import logging
import os
import secrets
import aiohttp
from aiohttp import web
from dataclasses import dataclass, field
from typing import Optional
from wecom_aibot_sdk import WSClient, generate_req_id, DefaultLogger


# ──────────────────────────────────────────────────────────
# 配置加载
# ──────────────────────────────────────────────────────────
_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config() -> dict:
    with open(_CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)

cfg = load_config()

SERVICE_CFG  = cfg.get("service", {})
NOTIFY_PORT  = SERVICE_CFG.get("notify_port", 8899)
LOG_LEVEL    = getattr(logging, SERVICE_CFG.get("log_level", "INFO").upper(), logging.INFO)
BOTS_CFG     = cfg.get("bots", [])

if not BOTS_CFG:
    raise ValueError("config.json 中 bots 数组为空，请至少配置一个机器人")


# ──────────────────────────────────────────────────────────
# Bot 上下文（每个机器人一个实例）
# ──────────────────────────────────────────────────────────
@dataclass
class BotContext:
    bot_id:         str
    token:          str
    ws_client:      Optional[WSClient] = field(default=None, repr=False)
    dify_api_base:  str = "http://127.0.0.1/v1"
    dify_api_key:   str = ""
    dify_input_var: str = "input"
    dify_output_var:str = "text"
    dify_timeout:   int = 60
    default_chatid: str = ""
    welcome_msg:    str = "你好！有什么可以帮你的吗？"
    thinking_msg:   str = "⏳ 思考中..."
    description:    str = ""

    @classmethod
    def from_cfg(cls, bot_cfg: dict) -> "BotContext":
        dify = bot_cfg.get("dify", {})
        return cls(
            bot_id         = bot_cfg["id"],
            token          = bot_cfg["token"],
            dify_api_base  = dify.get("api_base",        "http://127.0.0.1/v1"),
            dify_api_key   = dify.get("api_key",         ""),
            dify_input_var = dify.get("input_variable",  "input"),
            dify_output_var= dify.get("output_variable", "text"),
            dify_timeout   = dify.get("timeout",         60),
            default_chatid = bot_cfg.get("default_chatid", ""),
            welcome_msg    = bot_cfg.get("welcome_message", "你好！有什么可以帮你的吗？"),
            thinking_msg   = bot_cfg.get("thinking_message", "⏳ 思考中..."),
            description    = bot_cfg.get("description", ""),
        )


# token → BotContext 路由表
_token_router: dict[str, BotContext] = {}


# ──────────────────────────────────────────────────────────
# Dify 工作流调用
# ──────────────────────────────────────────────────────────
async def call_dify_workflow(query: str, user_id: str, chatid: str, ctx: BotContext) -> str:
    url = f"{ctx.dify_api_base}/workflows/run"
    headers = {
        "Authorization": f"Bearer {ctx.dify_api_key}",
        "Content-Type":  "application/json",
    }
    payload = {
        "inputs": {
            ctx.dify_input_var: query,
            "chatid":           chatid,
        },
        "response_mode": "blocking",
        "user":          user_id,
    }
    try:
        timeout = aiohttp.ClientTimeout(total=ctx.dify_timeout)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=timeout) as resp:
                result = await resp.json()
                if resp.status == 200:
                    outputs = result.get("data", {}).get("outputs", {})
                    return outputs.get(ctx.dify_output_var, str(outputs))
                else:
                    msg = result.get("message", "未知错误")
                    print(f"[{ctx.bot_id}][Dify] 调用失败 {resp.status}: {msg}")
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
    Body JSON:
      {
        "token":   "your-bot-token",   ← 必填，用于路由到对应机器人
        "content": "消息内容",          ← 必填
        "chatid":  "可选，留空用 default_chatid"
      }

    兼容企微原生格式：
      {"token": "...", "msgtype": "text", "text": {"content": "..."}}
    """
    try:
        raw = await request.text()
        raw = "".join(c for c in raw if c >= " " or c == "\t")
        data = json.loads(raw)

        # 1. 通过 token 找到对应 Bot
        token = str(data.get("token", "")).strip()
        if not token:
            return web.json_response({"ok": False, "error": "缺少 token 字段"}, status=400)

        ctx = _token_router.get(token)
        if ctx is None:
            return web.json_response({"ok": False, "error": "token 无效"}, status=401)

        if ctx.ws_client is None or not ctx.ws_client.is_connected:
            return web.json_response({"ok": False, "error": f"机器人 {ctx.bot_id} 未连接"}, status=503)

        # 2. 解析 chatid
        chatid = str(data.get("chatid", "")).strip() or ctx.default_chatid
        if not chatid:
            return web.json_response({"ok": False, "error": "chatid 不能为空且未配置 default_chatid"}, status=400)

        # 3. 解析消息内容（兼容两种格式）
        content = str(data.get("content", "")).strip()
        if not content:
            content = str(data.get("text", {}).get("content", "")).strip()
        if not content:
            return web.json_response({"ok": False, "error": "content 不能为空"}, status=400)

        # 4. 发送到企微
        await ctx.ws_client.send_message(chatid, {
            "msgtype":  "markdown",
            "markdown": {"content": content},
        })
        print(f"[{ctx.bot_id}][Notify] → {chatid}: {content[:60]}")
        return web.json_response({"ok": True})

    except Exception as e:
        print(f"[Notify] 错误: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def start_notify_server():
    app = web.Application()
    app.router.add_post("/notify", handle_notify)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", NOTIFY_PORT)
    await site.start()
    print(f"[Notify] HTTP 服务已启动，端口 {NOTIFY_PORT}")


# ──────────────────────────────────────────────────────────
# 单个 Bot 启动
# ──────────────────────────────────────────────────────────
async def start_bot(bot_raw_cfg: dict):
    ctx = BotContext.from_cfg(bot_raw_cfg)
    _token_router[ctx.token] = ctx

    wecom_cfg = bot_raw_cfg.get("wecom", {})
    logger = DefaultLogger(level=LOG_LEVEL)
    client = WSClient({
        "bot_id": wecom_cfg["bot_id"],
        "secret": wecom_cfg["secret"],
        "logger": logger,
    })
    ctx.ws_client = client

    tag = f"[{ctx.bot_id}]"

    async def on_connected(*args):
        print(f"{tag} WebSocket 已连接")

    async def on_authenticated(*args):
        print(f"{tag} 认证成功，开始接收消息")

    async def on_disconnected(reason):
        print(f"{tag} 断开连接: {reason}")

    async def on_reconnecting(attempt):
        print(f"{tag} 第 {attempt} 次重连...")

    async def on_enter(frame):
        await client.reply_welcome(frame, {
            "msgtype": "text",
            "text":    {"content": ctx.welcome_msg},
        })

    # 用闭包绑定 ctx，避免多 bot 共享同一个引用
    def make_on_text(bound_ctx: BotContext):
        async def on_text(frame):
            content = frame.body.get("text", {}).get("content", "").strip()
            sender  = (frame.body.get("from", {}).get("userid", "")
                       or frame.body.get("from", {}).get("id", "unknown"))
            chatid  = frame.body.get("chatid", sender)

            if not content:
                return

            print(f"\n{tag} 收到消息 {sender} (chatid={chatid}): {content}")

            stream_id = generate_req_id("stream")
            await client.reply_stream(frame, stream_id, bound_ctx.thinking_msg, finish=False)

            reply = await call_dify_workflow(content, sender, chatid, bound_ctx)
            print(f"{tag} 回复: {reply[:80]}{'...' if len(reply) > 80 else ''}")

            await client.reply_stream(frame, stream_id, reply, finish=True)
        return on_text

    client.on("connected",        on_connected)
    client.on("authenticated",    on_authenticated)
    client.on("disconnected",     on_disconnected)
    client.on("reconnecting",     on_reconnecting)
    client.on("event.enter_chat", on_enter)
    client.on("message.text",     make_on_text(ctx))

    print(f"{tag} 正在连接企业微信服务器... ({ctx.description})")
    await client.connect_async()

    # 保持连接
    while client.is_connected:
        await asyncio.sleep(1)


# ──────────────────────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────────────────────
async def main():
    print("=" * 60)
    print("  企业微信智能机器人 + Dify 多工作流桥接服务")
    print("=" * 60)
    print(f"  加载机器人数量: {len(BOTS_CFG)}")
    for b in BOTS_CFG:
        print(f"    - [{b['id']}] {b.get('description', '')}  token={b['token'][:8]}...")
    print(f"  Notify 端口: {NOTIFY_PORT}")
    print("=" * 60)
    print()

    # 启动 HTTP 通知服务
    await start_notify_server()

    # 并发启动所有机器人
    try:
        await asyncio.gather(*[start_bot(b) for b in BOTS_CFG])
    except KeyboardInterrupt:
        print("\n[停止] 服务已停止")


if __name__ == "__main__":
    asyncio.run(main())
