"""FastAPI 主应用"""
import os
import json
import asyncio
import socket
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import engine, get_db
from app.models import Base, User, Bot, Message
from app.schemas import (
    UserCreate, UserResponse, UserLogin, UserUpdate, Token,
    BotCreate, BotUpdate, BotResponse, BotDetail,
    MessageResponse, MessageListResponse,
    HealthCheck
)
from app.auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_active_user, decode_token
)
from app.wecom import test_wecom_connection, wait_for_chatid, send_welcome_message, send_text_message

# 创建数据库表
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建默认管理员账户
    db = next(get_db())
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@wedbridge.com",
                hashed_password=get_password_hash("admin"),
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print("✅ 默认管理员账户已创建: admin / admin")
    finally:
        db.close()
    yield
    # 关闭时的清理工作


app = FastAPI(
    title="WEDBRIDGE API",
    description="企业微信 + Dify 智能桥接平台 API",
    version="1.2.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 健康检查 ====================

@app.get("/health", response_model=HealthCheck)
def health_check():
    """健康检查端点"""
    return HealthCheck(
        status="healthy",
        services={
            "api": "up",
            "database": "up",
            "redis": "up"
        }
    )


# ==================== 认证相关 ====================

@app.post("/api/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建新用户
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@app.post("/api/auth/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    
    return Token(
        access_token=access_token,
        user=user
    )


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user


@app.put("/api/auth/me", response_model=UserResponse)
def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息（仅支持头像更新）"""
    if user_data.avatar is not None:
        current_user.avatar = user_data.avatar
    
    db.commit()
    db.refresh(current_user)
    return current_user


@app.delete("/api/auth/me")
def delete_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """注销当前用户账户 - 删除用户及其所有机器人"""
    user_id = current_user.id
    username = current_user.username
    
    # 删除用户的所有机器人
    db.query(Bot).filter(Bot.owner_id == user_id).delete()
    
    # 删除用户
    db.delete(current_user)
    db.commit()
    
    return {"message": f"用户 {username} 及其所有数据已删除"}


# ==================== 企微连接测试 ====================

class WecomTestRequest(BaseModel):
    bot_id: str
    secret: str


class WaitChatidRequest(BaseModel):
    bot_id: str
    secret: str
    timeout: int = 60


class SendWelcomeRequest(BaseModel):
    bot_id: str
    secret: str
    chatid: str
    owner: str
    bot_name: str


@app.post("/api/bots/test-wecom")
def api_test_wecom(
    data: WecomTestRequest,
    current_user: User = Depends(get_current_active_user)
):
    """测试企微连接"""
    success, msg = test_wecom_connection(data.bot_id, data.secret)
    return {"success": success, "message": msg}


@app.post("/api/bots/test-wecom-wait")
def api_test_wecom_wait(
    data: WaitChatidRequest,
    current_user: User = Depends(get_current_active_user)
):
    """测试企微连接 - 等待用户发送消息并回复成功消息"""
    # 等待用户发送消息
    success, result = wait_for_chatid(data.bot_id, data.secret, data.timeout)
    
    if success:
        chatid = result
        # 发送连接成功消息
        welcome_msg = """🎉 恭喜您！Bridge 连接成功！ 🎉

👋 『用户姓名』，您好
🤖 机器人「测试机器人」已成功连接到 Bridge！

✨ Bridge 的强大功能：
• 无缝连接企业微信与 Dify AI
• 支持多个机器人同时运行
• 智能消息路由，自动回复
• 实时连接，秒级响应

🚀 您的 AI 助手已就绪，随时可以为您服务！

💡 下一步： 在 Dify 中配置 HTTP 节点，开始使用吧！"""
        
        send_text_message(data.bot_id, data.secret, chatid, welcome_msg)
        return {"success": True, "chatid": chatid}
    
    return {"success": False, "message": result}


@app.post("/api/bots/wait-chatid")
def api_wait_chatid(
    data: WaitChatidRequest,
    current_user: User = Depends(get_current_active_user)
):
    """等待获取 chatid"""
    success, result = wait_for_chatid(data.bot_id, data.secret, data.timeout)
    if success:
        return {"success": True, "chatid": result}
    return {"success": False, "message": result}


@app.post("/api/bots/send-welcome")
def api_send_welcome(
    data: SendWelcomeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """发送欢迎消息"""
    success = send_welcome_message(
        data.bot_id, data.secret, data.chatid, data.owner, data.bot_name
    )
    return {"success": success}


@app.post("/api/bots/{bot_id}/wait-message")
def api_wait_message(
    bot_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """等待用户发送测试消息 - 用于连接测试"""
    bot = db.query(Bot).filter(
        Bot.bot_id == bot_id,
        Bot.owner_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    # 使用 wait_for_chatid 等待用户发送消息
    success, result = wait_for_chatid(bot.wecom_bot_id, bot.wecom_secret, timeout=60)
    
    if success:
        # 发送连接成功消息给用户
        send_text_message(
            bot.wecom_bot_id,
            bot.wecom_secret,
            result,
            "🎉 连接测试成功！\n\nBridge 已正确配置，可以正常接收和发送消息。"
        )
        return {"success": True, "chatid": result}
    
    return {"success": False, "message": result}


# ==================== 机器人管理 ====================

@app.get("/api/bots", response_model=list[BotResponse])
def list_bots(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的机器人列表"""
    bots = db.query(Bot).filter(Bot.owner_id == current_user.id).all()
    return bots


@app.post("/api/bots")
def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建机器人"""
    # 检查 bot_id 是否已存在
    if db.query(Bot).filter(Bot.bot_id == bot_data.bot_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人 ID 已存在"
        )
    
    # 生成 token
    token = secrets.token_hex(20)
    
    # 准备数据，如果没有 name 则使用 bot_id
    bot_dict = bot_data.model_dump()
    if not bot_dict.get('name'):
        bot_dict['name'] = bot_dict['bot_id']
    
    db_bot = Bot(
        **bot_dict,
        token=token,
        owner_id=current_user.id
    )
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    
    # 生成 notify URL
    # Dify 和 WEDBRIDGE 在同一个 Docker 网络中，使用容器名访问
    # 外部访问时使用 host.docker.internal 或网关 IP
    port = int(os.getenv('API_PORT', '8899'))
    
    # 尝试获取宿主机 IP (供外部访问)
    host_ip = None
    try:
        with open('/proc/net/route', 'r') as f:
            for line in f.readlines()[1:]:
                parts = line.strip().split()
                if parts[1] == '00000000':
                    gateway_hex = parts[2]
                    gateway_ip = '.'.join(
                        str(int(gateway_hex[i:i+2], 16)) 
                        for i in (6, 4, 2, 0)
                    )
                    host_ip = gateway_ip
                    break
    except Exception:
        pass
    
    if not host_ip:
        host_ip = 'host.docker.internal'
    
    notify_url = f"http://{host_ip}:{port}/notify?token={token}"
    
    # 返回包含 notify_url 的响应
    result = BotDetail.model_validate(db_bot)
    return {
        **result.model_dump(),
        "notify_url": notify_url,
        "created_at": str(result.created_at),
        "updated_at": str(result.updated_at)
    }


@app.get("/api/bots/{bot_id}", response_model=BotDetail)
def get_bot(
    bot_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取机器人详情"""
    bot = db.query(Bot).filter(
        Bot.bot_id == bot_id,
        Bot.owner_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )
    
    return bot


@app.put("/api/bots/{bot_id}", response_model=BotResponse)
def update_bot(
    bot_id: str,
    bot_data: BotUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新机器人"""
    bot = db.query(Bot).filter(
        Bot.bot_id == bot_id,
        Bot.owner_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )
    
    # 更新字段
    for field, value in bot_data.model_dump(exclude_unset=True).items():
        setattr(bot, field, value)
    
    db.commit()
    db.refresh(bot)
    
    return bot


@app.delete("/api/bots/{bot_id}")
def delete_bot(
    bot_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除机器人"""
    # 尝试精确匹配
    bot = db.query(Bot).filter(
        Bot.bot_id == bot_id,
        Bot.owner_id == current_user.id
    ).first()
    
    # 如果没有找到，尝试去除空格匹配（兼容旧数据）
    if not bot:
        bot = db.query(Bot).filter(
            Bot.bot_id == bot_id.strip(),
            Bot.owner_id == current_user.id
        ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )
    
    db.delete(bot)
    db.commit()
    
    return {"message": "机器人已删除"}


@app.post("/api/bots/{bot_id}/toggle")
def toggle_bot(
    bot_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """切换机器人启用/禁用状态"""
    bot = db.query(Bot).filter(
        Bot.bot_id == bot_id,
        Bot.owner_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )
    
    bot.enabled = not bot.enabled
    db.commit()
    
    return {
        "message": f"机器人已{'启用' if bot.enabled else '禁用'}",
        "enabled": bot.enabled
    }


@app.post("/api/bots/{bot_id}/start")
def start_bot(
    bot_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """启动机器人（启用并尝试连接）"""
    bot = db.query(Bot).filter(
        Bot.bot_id == bot_id,
        Bot.owner_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )
    
    bot.enabled = True
    db.commit()
    
    # 通知 Worker 启动连接（通过数据库状态变更，Worker 会自动同步）
    return {
        "message": "机器人已启动",
        "bot_id": bot_id,
        "enabled": True
    }


@app.post("/api/bots/{bot_id}/stop")
def stop_bot(
    bot_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """停止机器人（禁用并断开连接）"""
    bot = db.query(Bot).filter(
        Bot.bot_id == bot_id,
        Bot.owner_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )
    
    bot.enabled = False
    db.commit()
    
    return {
        "message": "机器人已停止",
        "bot_id": bot_id,
        "enabled": False
    }


@app.post("/api/bots/{bot_id}/send-test")
def send_test_message(
    bot_id: str,
    data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    发送测试消息到机器人
    用户需要在企业微信中给机器人发消息，机器人会回复测试消息
    """
    bot = db.query(Bot).filter(
        Bot.bot_id == bot_id,
        Bot.owner_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )
    
    if not bot.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人已禁用，请先启用"
        )
    
    message = data.get("message", "这是一条测试消息")
    
    # 尝试发送测试消息
    # 注意：需要先有 chatid 才能发送，所以这里只是记录测试请求
    # 实际测试流程：用户先发消息给机器人，获取 chatid，然后机器人回复
    
    return {
        "message": "测试请求已发送",
        "instruction": "请在企业微信中给机器人发送任意消息，机器人将回复测试内容",
        "bot_id": bot_id,
        "test_message": message
    }


# ==================== Dify HTTP 回调 ====================

@app.post("/notify")
@app.get("/notify")
def notify_callback(
    request: Request,
    token: str = Query(..., description="机器人 token"),
    # 支持 form-data 方式传变量
    text: Optional[str] = Form(None, description="消息内容"),
    query: Optional[str] = Form(None, description="查询内容"),
    input: Optional[str] = Form(None, description="输入内容"),
    message: Optional[str] = Form(None, description="消息"),
    # 支持 query string 方式
    text_q: Optional[str] = Query(None, alias="text", description="消息内容(query)"),
    query_q: Optional[str] = Query(None, alias="query", description="查询内容(query)"),
    db: Session = Depends(get_db)
):
    """
    Dify HTTP 节点回调接口
    
    支持多种传参方式：
    1. Form-data: text=xxx&query=xxx
    2. Query string: ?text=xxx&query=xxx
    3. JSON body: {"text": "xxx"}
    
    变量名可以是: text, query, input, message 中的任意一个
    """
    # 查找机器人
    bot = db.query(Bot).filter(Bot.token == token).first()
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    if not bot.enabled:
        raise HTTPException(status_code=403, detail="机器人已禁用")
    
    # 获取消息内容（按优先级）
    content = text or query or input or message or text_q or query_q
    
    # 如果没有从 form/query 获取到，尝试从 body 读取
    if not content:
        try:
            body = asyncio.run(request.body())
            if body:
                try:
                    json_data = json.loads(body)
                    content = json_data.get('text') or json_data.get('query') or json_data.get('input') or json_data.get('message')
                except:
                    content = body.decode('utf-8')
        except:
            pass
    
    if not content:
        content = "收到消息"
    
    # 记录 Dify -> 企微 的消息
    message_record = Message(
        bot_id=bot.bot_id,
        direction="dify_to_wecom",
        content=content,
        sender_name="Dify",
        sender_id="dify",
        msg_type="text",
        status="pending"
    )
    db.add(message_record)
    db.commit()
    
    # 发送到企微机器人
    wecom_result = False
    if bot.default_chatid:
        wecom_result = send_text_message(
            bot.wecom_bot_id,
            bot.wecom_secret,
            bot.default_chatid,
            content
        )
    
    # 更新消息状态
    message_record.status = "success" if wecom_result else "failed"
    if not wecom_result:
        message_record.error_msg = "发送到企微失败"
    db.commit()
    
    return {
        "status": "ok",
        "bot_id": bot.bot_id,
        "wecom_sent": wecom_result,
        "message": f"收到: {content[:100]}..." if len(content) > 100 else f"收到: {content}"
    }


# ==================== 消息记录 API ====================

@app.get("/api/bots/{bot_id}/messages")
def get_bot_messages(
    bot_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取机器人的消息记录"""
    # 检查机器人是否存在且属于当前用户
    bot = db.query(Bot).filter(
        Bot.bot_id == bot_id,
        Bot.owner_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    # 查询消息记录
    query = db.query(Message).filter(Message.bot_id == bot_id)
    total = query.count()
    messages = query.order_by(Message.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "messages": messages
    }


@app.get("/api/bots/{bot_id}/stats")
def get_bot_stats(
    bot_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取机器人今日统计"""
    from datetime import datetime, timedelta
    
    # 检查机器人是否存在且属于当前用户
    bot = db.query(Bot).filter(
        Bot.bot_id == bot_id,
        Bot.owner_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    
    # 获取今日开始时间
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 今日消息统计
    today_messages = db.query(Message).filter(
        Message.bot_id == bot_id,
        Message.created_at >= today_start
    ).count()
    
    # 今日成功消息
    today_success = db.query(Message).filter(
        Message.bot_id == bot_id,
        Message.created_at >= today_start,
        Message.status == "success"
    ).count()
    
    # 今日失败消息
    today_failed = db.query(Message).filter(
        Message.bot_id == bot_id,
        Message.created_at >= today_start,
        Message.status == "failed"
    ).count()
    
    return {
        "today_total": today_messages,
        "today_success": today_success,
        "today_failed": today_failed
    }


@app.put("/api/user/avatar")
def update_user_avatar(
    avatar_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新用户头像"""
    avatar_url = avatar_data.get("avatar")
    if not avatar_url:
        raise HTTPException(status_code=400, detail="头像URL不能为空")
    
    current_user.avatar = avatar_url
    db.commit()
    
    return {"success": True, "avatar": avatar_url}


@app.get("/api/user/stats")
def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的整体统计数据"""
    from datetime import datetime, timedelta
    
    # 获取用户的所有机器人ID
    user_bots = db.query(Bot).filter(Bot.owner_id == current_user.id).all()
    bot_ids = [bot.bot_id for bot in user_bots]
    
    if not bot_ids:
        return {
            "wecom": 0,
            "bridge": 0,
            "dify": 0,
            "totalMessages": 0,
            "successRate": 0,
            "activeBots": 0
        }
    
    # 获取今日开始时间
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 统计今日消息
    today_messages = db.query(Message).filter(
        Message.bot_id.in_(bot_ids),
        Message.created_at >= today_start
    ).count()
    
    # 统计今日成功消息
    today_success = db.query(Message).filter(
        Message.bot_id.in_(bot_ids),
        Message.created_at >= today_start,
        Message.status == "success"
    ).count()
    
    # 计算成功率
    success_rate = round((today_success / today_messages * 100), 1) if today_messages > 0 else 0
    
    # 统计活跃机器人（今日有消息的）
    active_bots = db.query(Message.bot_id).filter(
        Message.bot_id.in_(bot_ids),
        Message.created_at >= today_start
    ).distinct().count()
    
    # 分别统计 WeCom->Bridge 和 Bridge->Dify 的消息
    wecom_messages = db.query(Message).filter(
        Message.bot_id.in_(bot_ids),
        Message.direction == "wecom_to_dify",
        Message.created_at >= today_start
    ).count()
    
    dify_messages = db.query(Message).filter(
        Message.bot_id.in_(bot_ids),
        Message.direction == "dify_to_wecom",
        Message.created_at >= today_start
    ).count()
    
    return {
        "wecom": wecom_messages,
        "bridge": today_messages,
        "dify": dify_messages,
        "totalMessages": today_messages,
        "successRate": success_rate,
        "activeBots": active_bots
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8899)
