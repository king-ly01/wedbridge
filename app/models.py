"""数据库模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    avatar = Column(Text)  # 头像 URL 或 base64 数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    bots = relationship("Bot", back_populates="owner", cascade="all, delete-orphan")


class Bot(Base):
    """机器人配置表"""
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(String(50), unique=True, index=True, nullable=False)  # 用户定义的机器人ID
    name = Column(String(100), nullable=True)
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    
    # 企业微信配置
    wecom_bot_id = Column(String(100), nullable=False)
    wecom_secret = Column(String(255), nullable=False)
    
    # Dify 配置
    dify_api_base = Column(String(255), default="http://127.0.0.1/v1")
    dify_api_key = Column(String(255), nullable=False)
    dify_workflow_id = Column(String(100))
    input_variable = Column(String(50), default="input")
    output_variable = Column(String(50), default="text")
    timeout = Column(Integer, default=60)
    
    # 其他配置
    default_chatid = Column(String(100))
    welcome_message = Column(String(500), default="你好！有什么可以帮你的吗？")
    thinking_message = Column(String(100), default="⏳ 思考中...")
    token = Column(String(100), unique=True, nullable=False)  # 用于 HTTP 回调验证
    
    # 元数据
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_started_at = Column(DateTime, nullable=True)  # 上次启动时间
    
    # 关系
    owner = relationship("User", back_populates="bots")
    messages = relationship("Message", back_populates="bot", cascade="all, delete-orphan", order_by="desc(Message.created_at)")


class Message(Base):
    """消息记录表"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(String(50), ForeignKey("bots.bot_id"), nullable=False, index=True)
    
    # 消息方向: wecom_to_dify (企微->Dify) 或 dify_to_wecom (Dify->企微)
    direction = Column(String(20), nullable=False)
    
    # 消息内容
    content = Column(Text, nullable=False)
    
    # 发送者信息
    sender_name = Column(String(100))  # 用户姓名或机器人名称
    sender_id = Column(String(100))    # 用户ID或机器人ID
    
    # 消息类型
    msg_type = Column(String(50), default="text")  # text, markdown, image 等
    
    # 状态
    status = Column(String(20), default="success")  # success, failed, pending
    error_msg = Column(Text)  # 错误信息
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    bot = relationship("Bot", back_populates="messages")
