"""
Worker 服务 V2 - 多租户连接池版本
支持动态加载、卸载、状态监控
"""
import asyncio
import json
import os
import sys
import httpx
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from connection_pool import get_connection_pool, BotConnection, resolve_dify_url

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://wedbridge:wedbridge@db:5432/wedbridge')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


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
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                outputs = result.get('data', {}).get('outputs', {})
                answer = outputs.get('text', outputs.get('answer', ''))
                if not answer:
                    answer = str(outputs)
                return answer
            else:
                return f"Service temporarily unavailable (HTTP {response.status_code})"
                
    except asyncio.TimeoutError:
        return "Dify response timeout, please try again later"
    except Exception as e:
        error_str = str(e)
        return f"Call error: {error_str}"


async def load_enabled_bots():
    """从数据库加载启用的机器人"""
    try:
        db = SessionLocal()
        result = db.execute(text("""
            SELECT bot_id, wecom_bot_id, wecom_secret,
                   dify_api_base, dify_api_key, dify_workflow_id, owner_id
            FROM bots WHERE enabled = true
        """))
        bots = []
        for row in result:
            bots.append({
                'bot_id': row[0],
                'wecom_bot_id': row[1],
                'wecom_secret': row[2],
                'dify_api_base': resolve_dify_url(row[3] or ''),
                'dify_api_key': row[4],
                'dify_workflow_id': row[5],
                'owner_id': row[6]
            })
        db.close()
        return bots
    except Exception as e:
        print(f"[{datetime.now()}] 加载机器人失败: {e}")
        return []


async def sync_bots(pool, force_sync_event: asyncio.Event):
    """同步数据库和连接池的状态 - 正确处理启用/禁用切换"""
    sync_interval = 5  # 正常同步间隔 5 秒
    
    while True:
        try:
            # 获取数据库中的启用机器人
            db_bots = await load_enabled_bots()
            db_bot_ids = {b['bot_id'] for b in db_bots}
            
            # 获取连接池中的机器人（主连接）
            pool_bots = pool.get_all_connections()
            pool_bot_ids = set(pool_bots.keys())
            
            # 获取所有已订阅的 bot_id（包括共享连接的订阅者）
            subscribed_bot_ids = set()
            subscribed_configs = {}  # bot_id -> (wecom_id, config_index)
            for wecom_id, configs in pool._dify_subscriptions.items():
                for idx, config in enumerate(configs):
                    subscribed_bot_ids.add(config['bot_id'])
                    subscribed_configs[config['bot_id']] = (wecom_id, idx)
            
            # 所有已在池中的 bot_id（主连接 + 订阅）
            all_pool_bot_ids = pool_bot_ids | subscribed_bot_ids
            
            # 需要添加的（在数据库中但不在连接池）
            to_add = db_bot_ids - all_pool_bot_ids
            for bot_id in to_add:
                bot_config = next(b for b in db_bots if b['bot_id'] == bot_id)
                print(f"[{datetime.now()}] 添加机器人: {bot_id}")
                await pool.add_bot(bot_config)
            
            # 修复不一致状态：订阅者存在但主连接丢失（主连接断开后选举失败的情况）
            for wecom_id, configs in list(pool._dify_subscriptions.items()):
                if wecom_id not in pool._wecom_connections:
                    # 有订阅配置但没有主连接，需要重建
                    enabled_configs = [c for c in configs if c['bot_id'] in db_bot_ids]
                    if enabled_configs:
                        rebuild_bot_id = enabled_configs[0]['bot_id']
                        rebuild_config = next((b for b in db_bots if b['bot_id'] == rebuild_bot_id), None)
                        if rebuild_config:
                            print(f"[{datetime.now()}] 修复主连接丢失: 重建 {rebuild_bot_id} 为 WeCom {wecom_id} 的主连接")
                            # 清理旧的订阅列表，让 add_bot 重新初始化
                            del pool._dify_subscriptions[wecom_id]
                            await pool.add_bot(rebuild_config)
                            # 重新添加其他订阅者
                            for c in enabled_configs[1:]:
                                other_config = next((b for b in db_bots if b['bot_id'] == c['bot_id']), None)
                                if other_config:
                                    await pool.add_bot(other_config)
            
            # 需要移除的（主连接在连接池但不在数据库）
            to_remove = pool_bot_ids - db_bot_ids
            for bot_id in to_remove:
                print(f"[{datetime.now()}] 移除机器人: {bot_id}")
                await pool.remove_bot(bot_id)
            
            # 需要移除的订阅配置（订阅在池中但不在数据库=被禁用）
            to_remove_subs = subscribed_bot_ids - db_bot_ids
            for bot_id in to_remove_subs:
                if bot_id in subscribed_configs:
                    wecom_id, idx = subscribed_configs[bot_id]
                    print(f"[{datetime.now()}] 移除禁用机器人的 Dify 配置: {bot_id}")
                    async with pool._lock:
                        if wecom_id in pool._dify_subscriptions:
                            # 找到并移除对应的配置
                            pool._dify_subscriptions[wecom_id] = [
                                c for c in pool._dify_subscriptions[wecom_id] 
                                if c['bot_id'] != bot_id
                            ]
                            # 如果该 WeCom Bot 没有订阅了，可以选择是否断开连接
                            if not pool._dify_subscriptions[wecom_id]:
                                print(f"[{datetime.now()}] WeCom Bot {wecom_id} 没有启用的配置，保持连接等待新配置")
            
            # 打印统计（只在有变更时）
            if to_add or to_remove or to_remove_subs:
                stats = pool.get_stats()
                print(f"[{datetime.now()}] 连接池状态: {stats}")
            
        except Exception as e:
            print(f"[{datetime.now()}] 同步错误: {e}")
            import traceback
            traceback.print_exc()
        
        # 等待同步间隔或强制同步信号
        try:
            await asyncio.wait_for(force_sync_event.wait(), timeout=sync_interval)
            force_sync_event.clear()
            print(f"[{datetime.now()}] 收到强制同步信号，立即执行同步")
        except asyncio.TimeoutError:
            pass  # 正常超时，继续循环


async def health_check_server(pool, force_sync_event: asyncio.Event):
    """HTTP 健康检查服务 - 支持强制同步"""
    from aiohttp import web
    
    async def handle_stats(request):
        """返回连接池统计 - 包含每个机器人的详细状态（包括订阅者）"""
        stats = pool.get_stats()
        
        # 添加每个机器人的详细连接信息
        bots_detail = {}
        
        # 1. 添加主连接（有 WebSocket 连接的机器人）
        for bot_id, conn in pool.get_all_connections().items():
            bots_detail[bot_id] = conn.to_dict()
        
        # 2. 添加订阅者（共享 WeCom 连接的机器人）
        # 订阅者没有自己的连接对象，但共享主连接的状态
        for wecom_id, configs in pool._dify_subscriptions.items():
            # 找到这个 WeCom ID 对应的主连接
            main_conn = None
            for conn in pool.get_all_connections().values():
                if conn.wecom_bot_id == wecom_id:
                    main_conn = conn
                    break
            
            # 为每个订阅者创建状态信息
            for config in configs:
                sub_bot_id = config['bot_id']
                # 如果订阅者还没有被添加（避免重复添加主连接）
                if sub_bot_id not in bots_detail:
                    if main_conn:
                        # 订阅者共享主连接的状态
                        bots_detail[sub_bot_id] = {
                            "bot_id": sub_bot_id,
                            "connected": main_conn.connected,
                            "authenticated": main_conn.authenticated,
                            "message_count": main_conn.message_count,
                            "today_messages": main_conn.today_message_count,
                            "error_count": main_conn.error_count,
                            "last_error": main_conn.last_error,
                            "last_activity": main_conn.last_activity.isoformat() if main_conn.last_activity else None,
                            "uptime_seconds": (datetime.now() - main_conn.created_at).total_seconds(),
                            "last_interaction_success": main_conn.last_interaction_success,
                            "last_started_at": main_conn.last_started_at.isoformat() if main_conn.last_started_at else None,
                            "is_subscriber": True,
                            "shared_wecom_id": wecom_id
                        }
                    else:
                        # 主连接不存在，显示未连接状态
                        bots_detail[sub_bot_id] = {
                            "bot_id": sub_bot_id,
                            "connected": False,
                            "authenticated": False,
                            "message_count": 0,
                            "today_messages": 0,
                            "error_count": 0,
                            "last_error": None,
                            "last_activity": None,
                            "uptime_seconds": 0,
                            "last_interaction_success": None,
                            "last_started_at": None,
                            "is_subscriber": True,
                            "shared_wecom_id": wecom_id
                        }
        
        stats['bots'] = bots_detail
        
        # 添加订阅配置信息
        subscriptions = {}
        for wecom_id, configs in pool._dify_subscriptions.items():
            subscriptions[wecom_id] = [c['bot_id'] for c in configs]
        stats['subscriptions'] = subscriptions
        
        return web.json_response(stats)
    
    async def handle_bot_status(request):
        """返回指定机器人的状态"""
        bot_id = request.match_info.get('bot_id')
        conn = pool.get_connection(bot_id)
        if conn:
            return web.json_response(conn.to_dict())
        return web.json_response({"error": "Bot not found"}, status=404)
    
    async def handle_owner_bots(request):
        """返回某个用户的所有机器人状态"""
        owner_id = int(request.match_info.get('owner_id'))
        conns = pool.get_connections_by_owner(owner_id)
        return web.json_response({
            bot_id: conn.to_dict() 
            for bot_id, conn in conns.items()
        })
    
    async def handle_sync(request):
        """强制同步机器人状态"""
        force_sync_event.set()
        return web.json_response({"message": "Sync triggered"})
    
    app = web.Application()
    app.router.add_get('/stats', handle_stats)
    app.router.add_get('/bot/{bot_id}', handle_bot_status)
    app.router.add_get('/owner/{owner_id}/bots', handle_owner_bots)
    app.router.add_post('/sync', handle_sync)  # 强制同步接口
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8898)
    await site.start()
    print(f"[{datetime.now()}] 健康检查服务已启动: http://0.0.0.0:8898")


async def main():
    """主函数"""
    print("=" * 60)
    print("WEDBRIDGE Worker V2 - 多租户连接池")
    print("=" * 60)
    
    pool = get_connection_pool()
    
    # 创建强制同步事件
    force_sync_event = asyncio.Event()
    
    # 启动连接池健康检查（自动重连断开的机器人）
    await pool.start()
    
    # 启动健康检查服务
    asyncio.create_task(health_check_server(pool, force_sync_event))
    
    # 启动同步任务
    asyncio.create_task(sync_bots(pool, force_sync_event))
    
    print(f"[{datetime.now()}] Worker 已启动，等待机器人...")
    print(f"[{datetime.now()}] 同步间隔: 5秒，支持强制同步接口 POST /sync")
    
    # 保持运行
    while True:
        await asyncio.sleep(60)
        stats = pool.get_stats()
        print(f"[{datetime.now()}] 运行状态: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
