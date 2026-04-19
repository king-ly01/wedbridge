# API Service - FastAPI
FROM python:3.11-slim

WORKDIR /app

# apt 换国内源 + 安装系统依赖
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# pip 换国内源 + 安装 Python 依赖（分层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY app/ ./app/
COPY requirements.txt .

# 暴露端口
EXPOSE 8899

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8899"]
