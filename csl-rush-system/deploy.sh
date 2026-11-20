#!/bin/bash
# 一键部署脚本

set -e

cd "$(dirname "$0")"

echo "========================================="
echo "  CSL 抢购系统 - 一键部署"
echo "========================================="
echo ""

# 1. 检查 Go 环境
if ! command -v go &> /dev/null; then
    echo "❌ 未找到 Go 环境"
    echo "正在安装 Go..."
    if command -v brew &> /dev/null; then
        brew install go
    else
        echo "请手动安装 Go: https://go.dev/dl/"
        exit 1
    fi
fi

echo "✅ Go 版本: $(go version)"
echo ""

# 2. 复制配置文件示例
if [ ! -f "config/config.yaml" ]; then
    echo "正在创建配置文件..."
    cp config/config.yaml.example config/config.yaml
    echo "⚠️  请编辑 config/config.yaml 填写账号信息"
    echo ""
    read -p "按回车键继续编辑配置文件..."
    ${EDITOR:-nano} config/config.yaml
fi

# 3. 编译
echo "正在编译..."
./build.sh

echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo "启动命令: ./run.sh"
echo ""
