#!/usr/bin/env python3
"""
手动设置系统时间工具
用于解决系统时间错误导致授权验证失败的问题
"""
import sys
import os
import time
import logging
import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

# HTTP 时间源列表
HTTP_TIME_SOURCES = [
    "http://worldtimeapi.org/api/timezone/Asia/Shanghai",
    "http://worldtimeapi.org/api/ip",
    "https://www.google.com",
    "https://www.baidu.com",
]


def get_http_time(url, timeout=5):
    """从 HTTP 响应头获取时间"""
    try:
        import requests
        response = requests.get(url, timeout=timeout, verify=False)
        response.raise_for_status()

        # 优先从响应头获取时间
        if 'Date' in response.headers:
            from email.utils import parsedate_to_datetime
            date = parsedate_to_datetime(response.headers['Date'])
            return date.timestamp()

        # 如果是 JSON API，尝试解析时间字段
        try:
            data = response.json()
            if 'unixtime' in data:
                return data['unixtime']
            if 'datetime' in data:
                return datetime.datetime.fromisoformat(data['datetime']).timestamp()
        except:
            pass

        return None

    except Exception as e:
        logging.warning(f"HTTP 时间源 {url} 响应失败: {e}")
        return None


def set_windows_time(unix_time):
    """设置 Windows 系统时间（需要管理员权限）"""
    try:
        import ctypes

        win_time = datetime.datetime.fromtimestamp(unix_time)

        # Windows 设置系统时间
        ctypes.windll.kernel32.SetSystemTime(
            win_time.year, win_time.month, win_time.weekday(),
            win_time.day, win_time.hour, win_time.minute,
            win_time.second, int((win_time.microsecond / 1000000))
        )
        return True
    except Exception as e:
        logging.error(f"设置 Windows 时间失败: {e}")
        return False


def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════╗
    ║       手动设置系统时间工具 v1.1          ║
    ╚═══════════════════════════════════════╝
    """)

    current_time = time.time()
    print(f"\n当前系统时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}")
    print(f"当前时间戳: {int(current_time)}")

    print("\n检测到严重的时间问题!")
    print("系统时间显示为未来时间，这将导致授权验证失败。")
    print("\n正在尝试从网络获取正确时间...\n")

    # 尝试从 HTTP 获取时间
    http_time = None
    used_source = None

    for http_url in HTTP_TIME_SOURCES:
        http_time = get_http_time(http_url)
        if http_time:
            used_source = http_url
            break

    if http_time is None:
        print("❌ 无法从网络获取时间\n")
        print("请手动设置系统时间:")
        print("\nWindows 用户:")
        print("  1. 右键点击系统托盘的时间")
        print("  2. 选择 \"调整日期/时间\"")
        print("  3. 点击 \"立即更新\" 按钮")
        print("  4. 等待同步完成\n")
        print("  或以管理员身份运行 CMD:")
        print("  w32tm /resync\n")
        return

    # 显示时间对比
    print(f"\n✅ 从网络获取到时间:")
    print(f"   来源: {used_source}")
    print(f"   网络时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(http_time))}")
    print(f"   本地时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    time_diff = (http_time - current_time) / 60
    print(f"   时间差异: {time_diff:.1f} 分钟\n")

    # 检查是否需要同步
    if abs(time_diff) < 1:
        print("✅ 系统时间已正确！")
        print("\n现在可以运行 rush_buy.py 了\n")
        return

    print(f"⚠️ 检测到时间差异 {time_diff:.1f} 分钟，正在尝试同步...\n")

    # Windows 自动设置
    if sys.platform == "win32":
        print("正在设置 Windows 系统时间...")

        if set_windows_time(http_time):
            # 验证设置结果
            time.sleep(1)
            new_time = time.time()
            new_diff = abs(new_time - http_time)

            if new_diff < 5:
                print("✅ 系统时间已成功更新!")
                print(f"   新时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(new_time))}")
                print("\n✅ 时间同步成功! 现在可以运行 rush_buy.py\n")
                return
            else:
                print(f"⚠️ 时间设置后仍有差异: {new_diff:.1f} 秒")
        else:
            print("\n❌ 自动设置系统时间失败")
            print("原因: 可能需要管理员权限")

    # 手动设置指引
    print("\n" + "="*60)
    print("请手动设置正确的系统时间:")
    print("="*60)
    print(f"\n目标时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(http_time))}")
    print("\nWindows 用户:")
    print("  1. 右键点击系统托盘的时间")
    print("  2. 选择 \"调整日期/时间\"")
    print("  3. 手动设置或点击 \"立即更新\"")
    print("\n  或以管理员身份运行 CMD:")
    print("  w32tm /resync\n")
    print("Linux 用户:")
    print("  sudo date -s \"$(date -d @{})\"".format(int(http_time)))
    print("  或")
    print("  sudo ntpdate pool.ntp.org\n")
    print("="*60)
    print("\n设置完成后，重新运行此程序验证:")
    print("python set_time.py")
    print("\n验证通过后运行:")
    print("python rush_buy.py\n")


if __name__ == "__main__":
    main()
