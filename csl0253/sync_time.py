#!/usr/bin/env python3
"""
时间同步工具
用于解决授权验证时的时间不同步问题
"""
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_client import NTPClient
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════╗
    ║         时间同步工具 v1.0              ║
    ╚═══════════════════════════════════════╝
    """)

    print("\n当前系统时间:", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    print("时间戳:", int(time.time()))
    print("\n正在从 NTP 服务器同步时间...\n")

    success, time_diff, message = NTPClient.sync_time()

    print("\n" + "="*60)
    if success:
        print("✅", message)
        print("当前系统时间:", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
        print("时间戳:", int(time.time()))
    else:
        print("⚠️", message)
        print("\n提示: 如果无法自动同步，请手动执行以下命令:")
        print("\nWindows:")
        print("  w32tm /resync")
        print("\nLinux:")
        print("  sudo ntpdate pool.ntp.org")
        print("  或")
        print("  sudo systemctl restart systemd-timesyncd")

    print("="*60 + "\n")


if __name__ == "__main__":
    main()
