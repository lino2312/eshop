#!/bin/bash
# 编译 CSL 抢购系统

set -e

cd "$(dirname "$0")"

echo "开始编译 CSL 抢购系统..."
echo ""

# 创建输出目录
mkdir -p bin

# 检查 Go 环境
if ! command -v go &> /dev/null; then
    echo "❌ 错误: 未找到 Go 环境"
    echo "请先安装 Go 1.21+: https://go.dev/dl/"
    exit 1
fi

echo "Go 版本: $(go version)"
echo ""

# 下载依赖
echo "正在下载依赖..."
go mod download
echo ""

# 编译服务器
echo "编译监控服务器..."
go build -o bin/server -ldflags="-s -w" ./server
echo "✅ 服务器编译完成: bin/server"

# 编译客户端
echo "编译终端客户端..."
go build -o bin/client -ldflags="-s -w" ./client
echo "✅ 客户端编译完成: bin/client"

echo ""
echo "========================================="
echo "  编译完成！"
echo "========================================="
echo ""
echo "下一步:"
echo "1. 编辑配置文件: config/config.yaml"
echo "2. 运行系统: ./run.sh"
echo ""
