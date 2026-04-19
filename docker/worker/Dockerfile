# Worker Service
FROM python:3.11-slim

WORKDIR /app

# apt 换国内源 + 安装依赖
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# pip 换国内源 + 安装 Python 依赖（分层缓存）
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制 worker 目录下的所有代码
COPY worker/ .

EXPOSE 8897 8898

CMD ["python", "main_v2.py"]
