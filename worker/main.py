"""Worker 服务 - WebSocket 长连接 + Dify 桥接
完全参照 wework_smart_bot_final.py 的实现模式
"""
import asyncio
import json
import os
import sys
import httpx
import logging
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from wecom_aibot_sdk import WSClient, DefaultLogger, generate_req_id

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://wedbridge:wedbridge@db:5432/wedbridge')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def resolve_dify_url(dify_api_base: str) -> str:
    """自动解析 Dify API 地址，处理容器内网络
    
    规则：
    1. 如果用户没填或填了 127.0.0.1/localhost，自动发现 Dify 容器
    2. 如果用户填了自定义地址，优先使用用户的（支持多 Dify 实例）
    3. 自动添加 /v1 后缀（如果用户没填）
    """
    import subprocess
    
    # 首先尝试自动发现 Dify 容器地址（作为默认/备用）
    auto_discovered_url = None
    try:
        result = subprocess.run(
            ["getent", "hosts", "docker-nginx-1"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip().split()[0]
            auto_discovered_url = f"http://{ip}/v1"
    except Exception:
        pass
    
    # 如果用户没填或填了 127.0.0.1/localhost，使用自动发现的地址
    if not dify_api_base or dify_api_base.startswith("http://127.0.0.1") or dify_api_base.startswith("http://localhost"):
        if auto_discovered_url:
            print(f"[Dify] 自动解析地址: '{dify_api_base}' -> '{auto_discovered_url}'")
            return auto_discovered_url
        # 尝试通过 Docker 网关
        try:
            with open('/proc/net/route') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3 and parts[1] == '00000000':
                        hex_ip = parts[2]
                        ip = '.'.join(str(int(hex_ip[i:i+2], 16)) for i in range(6, -1, -2))
                        resolved = f"http://{ip}/v1"
                        print(f"[Dify] 通过网关解析: '{dify_api_base}' -> '{resolved}'")
                        return resolved
        except Exception:
            pass
    else:
        # 用户填了自定义地址，检查是否需要添加 /v1 后缀
        if dify_api_base.endswith('/'):
            dify_api_base = dify_api_base.rstrip('/')
        if not dify_api_base.endswith('/v1'):
            # 如果用户填的是 http://host:port 格式，自动加上 /v1
            if '/v1' not in dify_api_base:
                dify_api_base = f"{dify_api_base}/v1"
                print(f"[Dify] 自动添加 /v1 后缀: '{dify_api_base}'")
        print(f"[Dify] 使用用户配置的地址: '{dify_api_base}'")
        return dify_api_base
    
    return dify_api_base


async def call_dify_workflow(query: str, user_id: str, chatid: str,
                             dify_api_base: str, dify_api_key: str) -> str:
    """调用 Dify 工作流"""
    try:
        url = f"{dify_api_base}/workflows/run"
        headers = {
            "Authorization": f"Bearer {dify_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": {"input": query, "query": query, "chatid": chatid},
            "response_mode": "blocking",
            "user": user_id
        }

        print(f"[Dify] 调用 URL: {url}")
        print(f"[Dify] 调用内容: {query[:50]}...")
        print(f"[Dify] API Key: {dify_api_key[:10]}..." if dify_api_key else "[Dify] API Key: 未设置!")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)

            print(f"[Dify] 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"[Dify] 响应数据: {json.dumps(result, ensure_ascii=False)[:500]}")
                
                outputs = result.get('data', {}).get('outputs', {})
                print(f"[Dify] outputs: {outputs}")
                
                answer = outputs.get('text', outputs.get('answer', ''))
                if not answer:
                    answer = str(outputs) if outputs else "(无输出)"
                    print(f"[Dify] 警告: 未找到 text/answer 字段，使用整个 outputs: {answer[:100]}")
                else:
                    print(f"[Dify] 获取到回复: {answer[:80]}...")
                return answer
            else:
                err_text = response.text[:500]
                print(f"[Dify] 错误响应: HTTP {response.status_code}")
                print(f"[Dify] 错误内容: {err_text}")
                return f"Service temporarily unavailable ({response.status_code})"

    except asyncio.TimeoutError:
        return "Dify response timeout, please try again later"
    except Exception as e:
        error_str = str(e)
        print(f"[Dify] Call exception: {error_str}")
        return f"Call error: {error_str}"


async def run_bot(bot_config: dict):
    """运行单个机器人 - 参照 wework_smart_bot_final.py"""
    bot_id = bot_config['bot_id']
    wecom_bot_id = bot_config['wecom_bot_id']
    wecom_secret = bot_config['wecom_secret']
    dify_api_base = resolve_dify_url(bot_config.get('dify_api_base', ''))
    dify_api_key = bot_config['dify_api_key']

    print(f"[机器人 {bot_id}] WeCom: {wecom_bot_id[:15]}...")
    print(f"[机器人 {bot_id}] Dify: {dify_api_base}")

    logger = DefaultLogger(level=logging.INFO)
    client = WSClient({
        "bot_id": wecom_bot_id,
        "secret": wecom_secret,
        "logger": logger,
    })

    # --- 事件处理器 (直接 async def，和原始代码一致) ---

    async def on_connected(*args):
        print(f"[机器人 {bot_id}] WebSocket 已连接")

    async def on_authenticated(*args):
        print(f"[机器人 {bot_id}] 认证成功，开始接收消息")

    async def on_disconnected(reason):
        print(f"[机器人 {bot_id}] 断开: {reason}")

    async def on_reconnecting(attempt):
        print(f"[机器人 {bot_id}] 第 {attempt} 次重连...")

    async def on_enter(frame):
        await client.reply_welcome(frame, {
            "msgtype": "text",
            "text": {"content": "你好！有什么可以帮你的吗？"},
        })

    # 企微 HTTP API 发送消息
    async def send_via_http_api(user_id: str, content: str) -> bool:
        """使用企微 HTTP API 发送消息"""
        try:
            # 获取 access_token
            token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_bot_id}&corpsecret={wecom_secret}"
            async with httpx.AsyncClient(timeout=30) as http:
                r = await http.get(token_url)
                result = r.json()
                if result.get("errcode") != 0:
                    print(f"[HTTP API] 获取 token 失败: {result}")
                    return False
                token = result["access_token"]
                
                # 发送消息
                send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
                payload = {
                    "touser": user_id,
                    "msgtype": "text",
                    "text": {"content": content}
                }
                r2 = await http.post(send_url, json=payload)
                result2 = r2.json()
                if result2.get("errcode") == 0:
                    print(f"[HTTP API] 发送成功 -> {user_id}")
                    return True
                else:
                    print(f"[HTTP API] 发送失败: {result2}")
                    return False
        except Exception as e:
            print(f"[HTTP API] 异常: {e}")
            return False

    async def on_text(frame):
        content = frame.body.get("text", {}).get("content", "").strip()
        sender = frame.body.get("from", {}).get("userid", "") or frame.body.get("from", {}).get("id", "unknown")
        chatid = frame.body.get("chatid", sender)

        if not content:
            return

        print(f"\n[收到] {sender} (chatid={chatid}): {content}")

        # 立即用 send_message 发送"思考中"
        try:
            await client.send_message(chatid, {
                "msgtype": "markdown",
                "markdown": {"content": "⏳ 思考中..."}
            })
            print("[思考中] 已发送 via send_message")
        except Exception as e:
            print(f"[思考中发送失败] {e}")

        # 调用 Dify
        reply = await call_dify_workflow(content, sender, chatid, dify_api_base, dify_api_key)
        print(f"[回复] {reply[:80]}{'...' if len(reply) > 80 else ''}")

        # 用 SDK 的 send_message 发送最终回复
        for attempt in range(3):
            try:
                if not client.is_connected:
                    print(f"[重连] 等待重连...")
                    await client.connect_async()
                    for _ in range(100):
                        if client.is_authenticated:
                            break
                        await asyncio.sleep(0.1)
                
                await client.send_message(chatid, {
                    "msgtype": "markdown",
                    "markdown": {"content": reply}
                })
                print(f"[发送成功] via send_message")
                break
            except Exception as e:
                print(f"[发送失败] 第{attempt+1}次: {e}")
                await asyncio.sleep(5)

    # --- 注册事件 (和 wework_smart_bot_final.py 完全一致) ---
    client.on("connected", on_connected)
    client.on("authenticated", on_authenticated)
    client.on("disconnected", on_disconnected)
    client.on("reconnecting", on_reconnecting)
    client.on("event.enter_chat", on_enter)
    client.on("message.text", on_text)

    # --- 连接 ---
    print(f"\n[机器人 {bot_id}] 正在连接企业微信服务器...")
    await client.connect_async()

    # 保持运行（SDK 内部处理重连）
    try:
        while True:
            if client.is_connected:
                await asyncio.sleep(1)
            else:
                print(f"[机器人 {bot_id}] 连接断开，等待 SDK 自动重连...")
                await asyncio.sleep(5)
    except asyncio.CancelledError:
        print(f"[机器人 {bot_id}] 已停止")
        client.disconnect()


async def get_enabled_bots():
    """获取启用的机器人列表"""
    try:
        db = SessionLocal()
        result = db.execute(text("""
            SELECT bot_id, wecom_bot_id, wecom_secret,
                   dify_api_base, dify_api_key, default_chatid
            FROM bots WHERE enabled = true
        """))
        bots = []
        for row in result:
            if row[4]:  # 必须有 dify_api_key
                bots.append({
                    'bot_id': row[0],
                    'wecom_bot_id': row[1],
                    'wecom_secret': row[2],
                    'dify_api_base': row[3] or '',
                    'dify_api_key': row[4],
                    'default_chatid': row[5]
                })
        db.close()
        return bots
    except Exception as e:
        print(f"[错误] 获取机器人列表: {e}")
        return []


async def main():
    print("=" * 60)
    print("WEDBRIDGE Worker 服务")
    print("=" * 60)

    # 等待数据库就绪
    for i in range(10):
        bots = await get_enabled_bots()
        if bots:
            break
        print(f"没有启用的机器人，等待 10 秒... ({i+1}/10)")
        await asyncio.sleep(10)

    if not bots:
        print("没有机器人可启动，持续等待...")
        while True:
            await asyncio.sleep(60)
            bots = await get_enabled_bots()
            if bots:
                break

    print(f"启动 {len(bots)} 个机器人")

    # 并发启动所有机器人
    tasks = [asyncio.create_task(run_bot(bot)) for bot in bots]

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n[停止] 服务已停止")
        for t in tasks:
            t.cancel()


if __name__ == "__main__":
    asyncio.run(main())
