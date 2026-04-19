#!/bin/bash
# WEDBRIDGE 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/docker"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║  ██╗    ██╗███████╗██████╗ ██████╗ ██████╗ ██╗██████╗ ███████╗ ║"
    echo "║  ██║    ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗██╔════╝ ║"
    echo "║  ██║ █╗ ██║█████╗  ██║  ██║██████╔╝██████╔╝██║██║  ██║█████╗   ║"
    echo "║  ██║███╗██║██╔══╝  ██║  ██║██╔══██╗██╔══██╗██║██║  ██║██╔══╝   ║"
    echo "║  ╚███╔███╔╝███████╗██████╔╝██████╔╝██║  ██║██║██████╔╝███████╗ ║"
    echo "║   ╚══╝╚══╝ ╚══════╝╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝ ╚══════╝ ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo "         企业微信 + Dify 智能桥接平台"
    echo ""
}

show_help() {
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  web       启动 Web 模式（完整服务）"
    echo "  cli       进入 CLI 命令行模式"
    echo "  api       仅启动 API 服务"
    echo "  worker    仅启动 Worker 服务"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  logs      查看日志"
    echo "  status    查看服务状态"
    echo "  build     重新构建镜像"
    echo "  clean     清理数据（危险！）"
    echo ""
    echo "示例:"
    echo "  $0 web     # 启动完整服务"
    echo "  $0 cli     # 进入命令行交互模式"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker 未安装${NC}"
        exit 1
    fi
    if ! command -v docker compose &> /dev/null; then
        echo -e "${RED}错误: Docker Compose 未安装${NC}"
        exit 1
    fi
}

start_web() {
    echo -e "${GREEN}🚀 启动 Web 模式...${NC}"
    
    # 检查 .env 文件
    if [ ! -f .env ]; then
        echo -e "${YELLOW}⚠️  .env 文件不存在，从模板创建...${NC}"
        cp .env.example .env
    fi
    
    # 拉取最新镜像
    echo "📥 拉取镜像..."
    docker compose pull
    
    # 启动服务
    docker compose up -d
    
    echo ""
    echo -e "${GREEN}✅ 服务已启动！${NC}"
    echo ""
    echo "访问地址:"
    echo "  Web 界面:    http://localhost"
    echo "  API 文档:    http://localhost/docs"
    echo "  健康检查:    http://localhost/health"
    echo ""
    echo "默认账户:"
    echo "  用户名: admin"
    echo "  密码:   admin"
    echo ""
    echo "查看日志: $0 logs"
}

start_cli() {
    echo -e "${YELLOW}🖥️  进入 CLI 模式...${NC}"
    
    # 确保数据库已启动
    docker compose up -d db redis
    
    # 等待数据库就绪
    echo "等待数据库就绪..."
    sleep 3
    
    # 进入 CLI 交互
    docker compose exec api python cli.py "$@"
}

start_api() {
    echo -e "${GREEN}🚀 启动 API 服务...${NC}"
    docker compose up -d db redis
    sleep 2
    docker compose run --rm init
    docker compose up -d api
    echo -e "${GREEN}✅ API 服务已启动: http://localhost:8898${NC}"
}

start_worker() {
    echo -e "${GREEN}🚀 启动 Worker 服务...${NC}"
    docker compose up -d worker
    echo -e "${GREEN}✅ Worker 服务已启动${NC}"
}

stop_all() {
    echo -e "${YELLOW}🛑 停止所有服务...${NC}"
    docker compose down
    echo -e "${GREEN}✅ 所有服务已停止${NC}"
}

restart_all() {
    echo -e "${YELLOW}🔄 重启所有服务...${NC}"
    docker compose restart
    echo -e "${GREEN}✅ 服务已重启${NC}"
}

show_logs() {
    docker compose logs -f
}

show_status() {
    docker compose ps
}

build_images() {
    echo -e "${YELLOW}🔨 重新构建镜像...${NC}"
    docker compose build --no-cache
    echo -e "${GREEN}✅ 镜像构建完成${NC}"
}

clean_data() {
    echo -e "${RED}⚠️  警告: 这将删除所有数据！${NC}"
    read -p "确定要继续吗? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        docker compose down -v
        echo -e "${GREEN}✅ 数据已清理${NC}"
    else
        echo "已取消"
    fi
}

# 主逻辑
print_banner

case "${1:-}" in
    web)
        check_docker
        start_web
        ;;
    cli)
        check_docker
        shift
        start_cli "$@"
        ;;
    api)
        check_docker
        start_api
        ;;
    worker)
        check_docker
        start_worker
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    build)
        build_images
        ;;
    clean)
        clean_data
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac
