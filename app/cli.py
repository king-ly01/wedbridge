#!/usr/bin/env python3
"""CLI 命令行工具 - 兼容旧版 CLI"""
import argparse
import asyncio
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Bot, User
from app.auth import get_password_hash
import httpx

API_BASE = os.getenv("API_URL", "http://localhost:8899")


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def cmd_status():
    """查看服务状态"""
    try:
        response = httpx.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务运行正常")
            print(f"   版本: {data.get('version', 'unknown')}")
            print(f"   服务: {data.get('services', {})}")
        else:
            print(f"❌ 服务异常: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")


def cmd_list():
    """列出所有机器人"""
    db = get_db()
    try:
        bots = db.query(Bot).all()
        if not bots:
            print("暂无机器人配置")
            return
        
        print(f"\n{'机器人ID':<15} {'名称':<20} {'状态':<8} {'所有者':<15}")
        print("-" * 70)
        for bot in bots:
            status = "✅ 启用" if bot.enabled else "❌ 禁用"
            print(f"{bot.bot_id:<15} {bot.name:<20} {status:<8} {bot.owner.username:<15}")
        print()
    finally:
        db.close()


def cmd_create():
    """交互式创建机器人"""
    print("🤖 创建新机器人")
    print("-" * 40)
    
    # 获取输入
    bot_id = input("机器人ID: ").strip()
    name = input("机器人名称: ").strip()
    description = input("描述: ").strip()
    
    wecom_bot_id = input("企业微信 Bot ID: ").strip()
    wecom_secret = input("企业微信 Secret: ").strip()
    
    dify_api_key = input("Dify API Key: ").strip()
    dify_api_base = input("Dify API Base [http://127.0.0.1/v1]: ").strip() or "http://127.0.0.1/v1"
    
    # 获取或创建用户
    db = get_db()
    try:
        # 使用第一个管理员用户作为所有者
        owner = db.query(User).filter(User.is_admin == True).first()
        if not owner:
            print("❌ 没有可用的管理员用户，请先创建用户")
            return
        
        import secrets
        bot = Bot(
            bot_id=bot_id,
            name=name,
            description=description,
            wecom_bot_id=wecom_bot_id,
            wecom_secret=wecom_secret,
            dify_api_base=dify_api_base,
            dify_api_key=dify_api_key,
            token=secrets.token_hex(20),
            owner_id=owner.id
        )
        
        db.add(bot)
        db.commit()
        print(f"✅ 机器人 '{name}' 创建成功!")
        print(f"   Token: {bot.token}")
    except Exception as e:
        print(f"❌ 创建失败: {e}")
    finally:
        db.close()


def cmd_delete(bot_id: str):
    """删除机器人"""
    db = get_db()
    try:
        bot = db.query(Bot).filter(Bot.bot_id == bot_id).first()
        if not bot:
            print(f"❌ 机器人 '{bot_id}' 不存在")
            return
        
        confirm = input(f"确定要删除 '{bot.name}' 吗? (y/N): ")
        if confirm.lower() != 'y':
            print("已取消")
            return
        
        db.delete(bot)
        db.commit()
        print(f"✅ 机器人 '{bot_id}' 已删除")
    finally:
        db.close()


def cmd_toggle(bot_id: str):
    """切换机器人状态"""
    db = get_db()
    try:
        bot = db.query(Bot).filter(Bot.bot_id == bot_id).first()
        if not bot:
            print(f"❌ 机器人 '{bot_id}' 不存在")
            return
        
        bot.enabled = not bot.enabled
        db.commit()
        status = "启用" if bot.enabled else "禁用"
        print(f"✅ 机器人 '{bot.name}' 已{status}")
    finally:
        db.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="WEDBRIDGE CLI 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py status              # 查看服务状态
  python cli.py list                # 列出所有机器人
  python cli.py create              # 交互式创建机器人
  python cli.py toggle <bot_id>     # 切换机器人状态
  python cli.py delete <bot_id>     # 删除机器人
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # status
    subparsers.add_parser('status', help='查看服务状态')
    
    # list
    subparsers.add_parser('list', help='列出所有机器人')
    
    # create
    subparsers.add_parser('create', help='创建机器人')
    
    # delete
    delete_parser = subparsers.add_parser('delete', help='删除机器人')
    delete_parser.add_argument('bot_id', help='机器人ID')
    
    # toggle
    toggle_parser = subparsers.add_parser('toggle', help='切换机器人状态')
    toggle_parser.add_argument('bot_id', help='机器人ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    if args.command == 'status':
        cmd_status()
    elif args.command == 'list':
        cmd_list()
    elif args.command == 'create':
        cmd_create()
    elif args.command == 'delete':
        cmd_delete(args.bot_id)
    elif args.command == 'toggle':
        cmd_toggle(args.bot_id)


if __name__ == '__main__':
    main()
