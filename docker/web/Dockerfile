# Web Frontend - Vue 3 + Vite
FROM node:20-alpine

WORKDIR /app

# 安装依赖
RUN npm install -g npm@latest

# 复制 package.json
COPY web/package*.json ./
RUN npm install

# 复制源代码
COPY web/ .

# 暴露端口
EXPOSE 3000

# 开发模式启动
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
