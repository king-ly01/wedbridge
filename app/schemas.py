"""Pydantic 模型"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ==================== 用户相关 ====================

class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    avatar: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """用户更新信息"""
    avatar: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== 机器人相关 ====================

class BotBase(BaseModel):
    bot_id: str
    description: Optional[str] = None
    enabled: bool = True


class BotCreate(BotBase):
    # 企业微信配置
    wecom_bot_id: str
    wecom_secret: str
    
    # Dify 配置
    dify_api_base: str = "http://127.0.0.1/v1"
    dify_api_key: str
    dify_workflow_id: Optional[str] = None
    input_variable: str = "input"
    output_variable: str = "text"
    timeout: int = 60
    
    # 其他配置
    default_chatid: Optional[str] = None
    welcome_message: str = "你好！有什么可以帮你的吗？"
    thinking_message: str = "⏳ 思考中..."


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    wecom_bot_id: Optional[str] = None
    wecom_secret: Optional[str] = None
    dify_api_base: Optional[str] = None
    dify_api_key: Optional[str] = None
    dify_workflow_id: Optional[str] = None
    default_chatid: Optional[str] = None
    welcome_message: Optional[str] = None
    thinking_message: Optional[str] = None


class BotResponse(BotBase):
    id: int
    wecom_bot_id: str
    dify_api_base: str
    dify_workflow_id: Optional[str]
    default_chatid: Optional[str]
    welcome_message: str
    thinking_message: str
    token: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    last_started_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BotDetail(BotResponse):
    wecom_secret: str
    dify_api_key: str


# ==================== 消息记录相关 ====================

class MessageResponse(BaseModel):
    id: int
    bot_id: str
    direction: str  # wecom_to_dify 或 dify_to_wecom
    content: str
    sender_name: Optional[str]
    sender_id: Optional[str]
    msg_type: str
    status: str
    error_msg: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    total: int
    messages: list[MessageResponse]


# ==================== 系统相关 ====================

class HealthCheck(BaseModel):
    status: str
    version: str = "1.2.0"
    services: dict
