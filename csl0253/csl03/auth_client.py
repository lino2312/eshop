"""
认证客户端模块 - 与 ginAuth 服务器通信
用于软件授权验证和统计信息上报
支持 NTP 时间同步功能
"""
import requests
import time
import hashlib
import hmac
import uuid
import platform
import json
import logging
import os
import socket
import struct

# 配置 - 请根据实际情况修改
AUTH_SERVER_URL = "http://hk_phone.auth.tiantianda.com/api"  # ginAuth 服务器地址
APP_KEY = "80673fecfd04d9428e4bb850a7a1bc6db3f91b1508220e431180eeeaf7b3a0eb"  # 在此处填入从 ginAuth 管理后台获取的 AppKey

# NTP 服务器列表（用于时间同步）
NTP_SERVERS = [
    "pool.ntp.org",
    "time.windows.com",
    "time.google.com",
    "time.cloudflare.com",
    "cn.pool.ntp.org"  # 中国区 NTP 服务器
]

# 尝试从外部配置文件加载配置
_config_loaded = False
if not _config_loaded:
    try:
        import auth_config
        AUTH_SERVER_URL = getattr(auth_config, "AUTH_SERVER_URL", AUTH_SERVER_URL)
        APP_KEY = getattr(auth_config, "APP_KEY", APP_KEY)
        _config_loaded = True
    except ImportError:
        pass


class NTPClient:
    """NTP 时间同步客户端"""

    # NTP 协议常量
    NTP_PACKET_SIZE = 48
    NTP_DELTA = 2208988800  # 1970-01-01 到 1900-01-01 的秒数

    # HTTP 时间获取服务器列表（备选方案）
    HTTP_TIME_SOURCES = [
        "http://worldtimeapi.org/api/timezone/Asia/Shanghai",
        "http://worldtimeapi.org/api/ip",
        "https://www.google.com",
        "https://www.baidu.com",
    ]

    @staticmethod
    def get_ntp_time(host, timeout=3):
        """
        从 NTP 服务器获取时间

        Args:
            host (str): NTP 服务器地址
            timeout (int): 超时时间（秒）

        Returns:
            float: NTP 服务器的时间戳，失败返回 None
        """
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.settimeout(timeout)

            # 构造 NTP 请求包
            data = b'\x1b' + 47 * b'\x00'  # LI=0, VN=3, Mode=3 (Client)
            client.sendto(data, (host, 123))

            # 接收响应
            data, _ = client.recvfrom(NTP_PACKET_SIZE)
            client.close()

            if len(data) < NTP_PACKET_SIZE:
                return None

            # 解析 NTP 响应（传输时间戳在字节 40-47）
            ntp_timestamp = struct.unpack("!I", data[40:44])[0]
            return ntp_timestamp - NTP_DELTA

        except Exception as e:
            return None

    @staticmethod
    def get_http_time(url, timeout=5):
        """
        从 HTTP 响应头获取时间（备选方案）

        Args:
            url (str): HTTP 时间源 URL
            timeout (int): 超时时间（秒）

        Returns:
            float: 服务器时间戳，失败返回 None
        """
        try:
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
                    from datetime import datetime
                    return datetime.fromisoformat(data['datetime']).timestamp()
            except:
                pass

            return None

        except Exception as e:
            return None

    @classmethod
    def sync_time(cls):
        """
        同步系统时间到 NTP 服务器或 HTTP 时间源

        Returns:
            tuple: (是否成功, 时间差秒数, 使用消息)
        """
        logger = logging.getLogger("NTPClient")

        local_time = time.time()

        # 方法 1: 尝试 NTP 服务器
        logger.debug("正在尝试从 NTP 服务器同步时间...")
        for ntp_server in NTP_SERVERS:
            ntp_time = cls.get_ntp_time(ntp_server)
            if ntp_time is None:
                logger.debug(f"NTP 服务器 {ntp_server} 响应失败，尝试下一个...")
                continue

            time_diff = ntp_time - local_time
            result = cls._sync_to_time(ntp_time, time_diff, f"NTP 服务器 {ntp_server}")
            return result[0], result[1], result[2]

        logger.debug("所有 NTP 服务器均无法连接，尝试 HTTP 时间源...")

        # 方法 2: 尝试 HTTP 时间源（备选方案）
        logger.debug("正在尝试从 HTTP 时间源同步时间...")
        for http_url in cls.HTTP_TIME_SOURCES:
            http_time = cls.get_http_time(http_url)
            if http_time is None:
                logger.debug(f"HTTP 时间源 {http_url} 响应失败，尝试下一个...")
                continue

            time_diff = http_time - local_time
            result = cls._sync_to_time(http_time, time_diff, f"HTTP 时间源 {http_url}")
            return result[0], result[1], result[2]

        logger.debug("所有时间源均无法连接")

        return False, 0, "无法连接时间服务器，请手动同步时间"

    @classmethod
    def _sync_to_time(cls, target_time, time_diff, source_name):
        """
        同步系统时间到目标时间

        Returns:
            tuple: (是否成功, 时间差秒数, 使用消息)
        """
        logger = logging.getLogger("NTPClient")
        local_time = time.time()

        # 时间差超过 5 分钟提示警告
        if abs(time_diff) > 300:
            logger.debug(f"检测到时间差异: {time_diff:.2f} 秒 (约 {abs(time_diff)/60:.1f} 分钟)")
            logger.debug(f"本地时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(local_time))}")
            logger.debug(f"网络时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(target_time))}")

            # 尝试设置系统时间（需要管理员权限）
            try:
                if platform.system() == "Windows":
                    import ctypes
                    import datetime

                    # Windows 设置系统时间
                    win_time = datetime.datetime.fromtimestamp(target_time)
                    ctypes.windll.kernel32.SetSystemTime(
                        win_time.year, win_time.month, win_time.weekday(),
                        win_time.day, win_time.hour, win_time.minute,
                        win_time.second, int((win_time.microsecond / 1000000))
                    )
                    logger.debug(f"已成功将系统时间同步到 {source_name}")
                    return True, 0, f"时间已同步 (使用 {source_name})"

                elif platform.system() == "Linux":
                    import subprocess
                    # Linux 设置系统时间
                    ntp_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(target_time))
                    subprocess.run(["date", "-s", ntp_date], check=True)
                    logger.debug(f"已成功将系统时间同步到 {source_name}")
                    return True, 0, f"时间已同步 (使用 {source_name})"
                else:
                    logger.debug(f"当前系统 ({platform.system()}) 不支持自动同步时间")
                    return False, time_diff, f"时间差异 {time_diff:.2f} 秒，请手动同步时间"

            except Exception as sync_error:
                logger.debug(f"自动同步系统时间失败: {sync_error}")
                return False, time_diff, f"时间差异 {time_diff:.2f} 秒，自动同步失败"

        return True, time_diff, f"时间正常 (差异 {time_diff:.2f} 秒)"


class AuthClient:
    """认证客户端"""

    def __init__(self, server_url=AUTH_SERVER_URL, app_key=APP_KEY):
        self.server_url = server_url
        self.app_key = app_key
        self.logger = logging.getLogger("AuthClient")
        self.device_info = self._get_device_info()
        self.time_offset = 0  # 与服务器的时间偏移

    def _get_device_info(self):
        """获取设备信息"""
        return f"{platform.system()} {platform.release()} - {platform.machine()}"

    def sync_time(self):
        """同步时间（调用 NTPClient）"""
        return NTPClient.sync_time()

    def verify(self, auto_sync_time=True):
        """
        验证软件授权（使用增强版 v2 接口）

        Args:
            auto_sync_time (bool): 是否在时间差异时尝试自动同步时间

        Returns:
            bool: 授权是否通过
            str: 错误消息（如果失败）
        """
        if not self.app_key:
            self.logger.debug("AppKey 未配置")
            return False, "AppKey 未配置，请联系管理员"

        # 首先尝试 NTP 时间同步
        if auto_sync_time:
            sync_success, time_diff, sync_msg = self.sync_time()
            if not sync_success:
                self.logger.debug(f"{sync_msg}")

        try:
            # 使用调整后的时间戳
            timestamp = int(time.time())
            nonce = str(uuid.uuid4())

            self.logger.debug(f"当前时间戳: {timestamp}")
            self.logger.debug(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")

            # 生成签名
            message = f"{self.app_key}{timestamp}{nonce}{self.device_info}"
            signature = hmac.new(
                self.app_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            headers = {
                "Content-Type": "application/json",
                "X-Timestamp": str(timestamp),
                "X-Nonce": nonce,
                "X-Signature": signature
            }

            payload = {
                "app_key": self.app_key,
                "device_info": self.device_info,
                "timestamp": timestamp,
                "nonce": nonce
            }

            self.logger.debug("正在验证授权...")
            response = requests.post(
                f"{self.server_url}/v2/verify",
                json=payload,
                headers=headers,
                timeout=10
            )

            self.logger.debug(f"响应状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0 and result.get("data", {}).get("allowed"):
                    self.logger.debug("授权验证成功")
                    return True, None
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code", 0)
                    self.logger.debug(f"授权验证失败 (错误码: {error_code}): {error_msg}")

                    return False, error_msg
            else:
                self.logger.debug(f"授权请求失败，状态码: {response.status_code}")
                try:
                    result = response.json()
                    error_msg = result.get("message", "服务器请求失败")
                except:
                    error_msg = f"服务器请求失败 (HTTP {response.status_code})"
                return False, error_msg

        except requests.exceptions.Timeout:
            self.logger.debug("授权请求超时")
            return False, "授权服务器响应超时，请检查网络连接或联系管理员"
        except requests.exceptions.ConnectionError:
            self.logger.debug("无法连接到授权服务器")
            return False, "无法连接到授权服务器，请联系管理员"
        except Exception as e:
            self.logger.debug(f"授权验证异常: {e}")
            return False, f"授权验证异常: {str(e)}"

    def report_stats(self, event_type, event_data=None):
        """
        上报统计信息

        Args:
            event_type (str): 事件类型（如：order_success, startup, shutdown等）
            event_data (str): 事件数据（可选）

        Returns:
            bool: 上报是否成功
        """
        if not self.app_key:
            self.logger.warning("AppKey 未配置，跳过统计上报")
            return False

        try:
            payload = {
                "app_key": self.app_key,
                "event_type": event_type,
                "event_data": event_data or ""
            }

            self.logger.info(f"上报统计信息: {event_type}")
            response = requests.post(
                f"{self.server_url}/stats",
                json=payload,
                timeout=5
            )

            if response.status_code == 200:
                self.logger.info(f"✅ 统计信息上报成功: {event_type}")
                return True
            else:
                self.logger.warning(f"⚠️ 统计信息上报失败，状态码: {response.status_code}")
                return False

        except Exception as e:
            self.logger.warning(f"⚠️ 统计信息上报异常: {e}")
            return False


# 全局认证客户端实例
_auth_client = None


def get_auth_client():
    """获取全局认证客户端实例"""
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthClient()
    return _auth_client


def verify_auth():
    """
    快捷函数：验证授权
    如果验证失败，打印错误消息并建议联系管理员

    Returns:
        bool: 授权是否通过
    """
    client = get_auth_client()
    success, error_msg = client.verify()

    if not success:
        pass

    return success


def report_order_success(product_info=None):
    """
    快捷函数：上报订购成功统计信息

    Args:
        product_info (dict): 商品信息（可选）

    Returns:
        bool: 上报是否成功
    """
    client = get_auth_client()
    event_data = json.dumps(product_info) if product_info else None
    return client.report_stats("order_success", event_data)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 测试 NTP 时间同步
    print("测试 NTP 时间同步...")
    NTPClient.sync_time()

    print("\n" + "="*60)

    # 测试授权验证
    print("\n测试授权验证...")
    result = verify_auth()
    print(f"验证结果: {result}")

    # 测试统计上报
    if result:
        print("\n测试统计上报...")
        report_order_success({"product": "test", "amount": 1})
