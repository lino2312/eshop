#!/bin/bash
# CSL 抢购系统启动脚本

set -e

cd "$(dirname "$0")"

echo "========================================="
echo "  CSL 抢购系统 - 启动向导"
echo "========================================="
echo ""

# 检查配置文件
if [ ! -f "config/config.yaml" ]; then
    echo "❌ 错误: 找不到配置文件 config/config.yaml"
    echo "请先复制 config/config.yaml.example 并修改账号信息"
    exit 1
fi

# 选择启动模式
echo "请选择启动模式:"
echo "1. 监控服务器 (运行库存监控)"
echo "2. 终端客户端 (连接服务器并抢购)"
echo "3. 全部启动 (服务器 + 所有客户端)"
echo ""
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "启动监控服务器..."
        ./bin/server
        ;;
    2)
        echo ""
        echo "启动终端客户端..."
        ./bin/client
        ;;
    3)
        echo ""
        echo "启动服务器和客户端..."
        ./bin/server &
        SERVER_PID=$!
        sleep 2

        # 读取账号数量
        ACCOUNT_COUNT=$(grep -c "username:" config/config.yaml || echo "0")
        echo "检测到 $ACCOUNT_COUNT 个账号，启动对应数量的客户端..."

        for i in $(seq 1 $ACCOUNT_COUNT); do
            ./bin/client &
            echo "客户端 $i 已启动"
            sleep 1
        done

        echo ""
        echo "所有进程已启动！按 Ctrl+C 停止所有服务"
        wait $SERVER_PID
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
