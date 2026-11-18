#!/usr/bin/env python3
"""
单线程网站抢购助手（简化版）
使用 DrissionPage 实现单账号抢购，方便 ipython 调试

使用方式:
  1. 直接运行: python rush_buy.py
  2. ipython 调试:
     ipython
     In [1]: %run rush_buy.py
     或者逐步执行各个函数
"""

import time
import random
import os
import platform
import subprocess
import logging
import requests
import base64
import threading
import socket
import select
import http.client

from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from DrissionPage import Chromium, ChromiumOptions
from auth_client import verify_auth, report_order_success


# ============================================================
# 日志配置
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rush_buy.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ============================================================
# 常量配置
# ============================================================

# 目标商品页面 URL（运行时由用户选择后赋值）
TARGET_URL = ""

# 登录页面
LOGIN_URL = "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Login-Show"

# 结账页面
CHECKOUT_URL = "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Checkout-Begin?stage=payment"

# 购物车页面
CART_URL = "https://eshop.hkcsl.com/zh_HK/cart"

# 库存检查间隔（秒），0 表示无间隔
CHECK_INTERVAL = 0

# 是否在测试模式下（测试模式下会在关键步骤暂停等待手动操作）
is_in_coding = False

# ---- 各种操作延时（秒） ----
FAST_ACTION_DELAY = 0.05       # 通用操作后等待
FAST_POST_CLICK_DELAY = 0.1    # 点击后等待
FAST_SELECT_OPEN_DELAY = 0.2   # 下拉框打开后等待
FAST_SELECT_APPLY_DELAY = 0.1  # 选择选项后等待
FAST_RETRY_DELAY = 0.1         # 重试间隔
CSL_SCAVENGE_INTERVAL = 0.5    # 捡漏模式轮询间隔
PRO_COLOR_TO_MEMORY_DELAY = 1.0   # Pro 型号选颜色后等内存加载
PROMAX_COLOR_TO_MEMORY_DELAY = 1.0 # ProMax 型号选颜色后等内存加载

# ---- 商品选项配置 ----

# iPhone 17 Pro / Pro Max 颜色选项
IPHONE_17_PRO_AND_PROMAX_COLOR_OPTIONS = {
    "1": {"name": "銀色", "value": "927"},
    "2": {"name": "宇宙橙色", "value": "31033"},
    "3": {"name": "深墨藍色", "value": "31034"}
}

# iPhone 17 颜色选项
IPHONE_17_COLOR_OPTIONS = {
    "1": {"name": "黑色", "value": "25"},
    "2": {"name": "白色", "value": "962"},
    "3": {"name": "藍色", "value": "16827"},
    "4": {"name": "薰衣草紫色", "value": "15121"},
    "5": {"name": "鼠尾草綠色", "value": "31032"}
}

# 存储容量选项
STORAGE_OPTIONS = {
    "1": {"name": "256GB", "value": "1025"},
    "2": {"name": "512GB", "value": "1026"},
    "3": {"name": "1TB", "value": "1027"},
    "4": {"name": "2TB", "value": "4697"}
}

# 商品列表（编号 -> 名称 + URL）
goods_options = {
    "1": {"name": "iphone_17_pro_max", "url": "https://eshop.hkcsl.com/zh_HK/apple/iPhone/IP17_promaxscol.html"},
    "2": {"name": "iphone_17_pro", "url": "https://eshop.hkcsl.com/zh_HK/apple/iPhone/IP17_proscol.html"},
    "3": {"name": "iphone_17", "url": "https://eshop.hkcsl.com/zh_HK/apple/IP17scol.html"},
    "4": {"name": "iphone_17_promax_and_airpods_pro_3", "url": "https://eshop.hkcsl.com/zh_HK/apple/iPhone/P3_IP17_promaxscol.html"},
    "5": {"name": "iphone_17_pro_and_airpods_pro_3", "url": "https://eshop.hkcsl.com/zh_HK/apple/iPhone/P3_IP17_proscol.html"}
}

# ---- 加入购物车请求所需的 headers 和 data ----
_cart_headers = {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://eshop.hkcsl.com',
    'priority': 'u=1, i',
    'referer': 'https://eshop.hkcsl.com/zh_HK/apple/IP17scol.html',
    'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

_cart_data = {
    'pid': '',
    'quantity': '2',
    'options': '[]',
}

# ---- 全局变量（运行时状态） ----
# 浏览器实例和标签页
browser = None
tab = None       # 主标签页（商品页）
new_tab = None   # 新标签页（用于结账等）

# 当前是否为 Pro 型号页面（影响颜色/内存选择方式）
is_pro_model = False


# ============================================================
# 工具函数
# ============================================================

def play_success_sound(sound_file='y1871.wav', repeat=3):
    """
    播放成功音效（同步播放，单线程无需异步）

    Args:
        sound_file: 音效文件名（相对于脚本目录）
        repeat: 重复播放次数
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sound_path = os.path.join(script_dir, sound_file)

        if not os.path.exists(sound_path):
            logging.warning(f"音效文件不存在: {sound_path}")
            return

        logging.info(f"开始播放成功音效，循环 {repeat} 次")
        system = platform.system()

        for i in range(repeat):
            logging.info(f"播放第 {i+1}/{repeat} 遍")
            if system == "Darwin":
                subprocess.run(['afplay', sound_path], check=True)
            elif system == "Windows":
                import winsound
                winsound.PlaySound(sound_path, winsound.SND_FILENAME)
            elif system == "Linux":
                try:
                    subprocess.run(['aplay', sound_path], check=True)
                except FileNotFoundError:
                    try:
                        subprocess.run(['paplay', sound_path], check=True)
                    except FileNotFoundError:
                        logging.warning("Linux 系统未找到音频播放器 (aplay/paplay)")
                        break
            else:
                logging.warning(f"不支持的操作系统: {system}")
                break

        logging.info("音效播放完成")
    except Exception as e:
        logging.error(f"播放音效失败: {e}")


def get_pid(goods_choice, color, storage):
    """
    根据商品编号、颜色值和存储容量值，返回对应的 pid（产品ID）

    Args:
        goods_choice: 商品编号 ("1"=ProMax, "2"=Pro, "3"=17)
        color: 颜色值（如 "927", "25" 等）
        storage: 存储容量值（如 "1025", "1026" 等）

    Returns:
        str: 对应的 pid 字符串
    """
    pid = ''
    if goods_choice == "3":  # iPhone 17
        pid_map = {
            ("25", "1025"): "4030131scol", ("25", "1026"): "4030181scol",
            ("962", "1025"): "4030141scol", ("962", "1026"): "4030191scol",
            ("16827", "1025"): "4030151scol", ("16827", "1026"): "4030201scol",
            ("15121", "1025"): "4030161scol", ("15121", "1026"): "4030211scol",
            ("31032", "1025"): "4030171scol", ("31032", "1026"): "4030221scol",
        }
    elif goods_choice == "2":  # iPhone 17 Pro
        pid_map = {
            ("927", "1025"): "4030351scol", ("927", "1026"): "4030381scol", ("927", "1027"): "4030411scol",
            ("31033", "1025"): "4030361scol", ("31033", "1026"): "4030391scol", ("31033", "1027"): "4030421scol",
            ("31034", "1025"): "4030371scol", ("31034", "1026"): "4030401scol", ("31034", "1027"): "4030431scol",
        }
    elif goods_choice == "1":  # iPhone 17 Pro Max
        pid_map = {
            ("927", "1025"): "4030011scol", ("927", "1026"): "4030041scol",
            ("927", "1027"): "4030071scol", ("927", "4697"): "4030101scol",
            ("31033", "1025"): "4030021scol", ("31033", "1026"): "4030051scol",
            ("31033", "1027"): "4030081scol", ("31033", "4697"): "4030111scol",
            ("31034", "1025"): "4030031scol", ("31034", "1026"): "4030061scol",
            ("31034", "1027"): "4030091scol", ("31034", "4697"): "4030121scol",
        }
    else:
        pid_map = {}

    pid = pid_map.get((color, storage), '')
    if pid == '':
        logging.error(f"未找到对应的 pid: goods_choice={goods_choice}, color={color}, storage={storage}")
    return pid


def add_cart(tab, goods_choice, color, storage):
    """
    使用 DrissionPage Tab 获取 cookies，然后通过 requests 发送加入购物车请求

    Args:
        tab: DrissionPage Tab 实例（用于获取 cookies）
        goods_choice: 商品编号
        color: 颜色值
        storage: 存储容量值

    Returns:
        int: HTTP 状态码（200 表示成功，429 表示请求频率过高）
    """
    # 从浏览器标签页获取 cookies
    cookies_dict = tab.cookies()
    cookies = {cookie['name']: cookie['value'] for cookie in cookies_dict}

    # 获取 pid
    pid = get_pid(goods_choice, color, storage)
    _cart_data['pid'] = pid

    # 发送加入购物车请求
    response = requests.post(
        'https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Cart-AddProduct',
        cookies=cookies,
        headers=_cart_headers,
        data=_cart_data,
    )
    logging.info(f"加购物车状态码: {response.status_code}")
    return response.status_code


def load_accounts(filename='account.txt'):
    """
    从文件加载账号信息

    文件格式: 每行一个账号，用户名和密码用 "——" 分隔
    例如: user@gmail.com——password123

    Args:
        filename: 账号文件路径

    Returns:
        list: [(username, password), ...] 列表
    """
    accounts = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '——' in line:
                    username, password = line.split('——', 1)
                    accounts.append((username.strip(), password.strip()))
        logging.info(f"成功加载 {len(accounts)} 个账号")
        return accounts
    except Exception as e:
        logging.error(f"加载账号文件失败: {e}")
        return []


def load_proxy(filename='proxy.txt'):
    """
    从文件加载代理配置

    文件格式: 每行一个代理，格式为 IP:端口:用户名:密码
    例如: 124.155.250.87:443:LUuteRCHxpEV:6RCyiJubJJ
    空文件则不使用代理

    Args:
        filename: 代理配置文件路径

    Returns:
        str: 代理字符串（原样返回），为空则不使用代理
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    logging.info(f"成功加载代理配置: {line.split(':')[0]}:{line.split(':')[1]}")
                    return line
        logging.info("代理配置文件为空，不使用代理")
        return ""
    except FileNotFoundError:
        logging.info("未找到代理配置文件，不使用代理")
        return ""
    except Exception as e:
        logging.error(f"加载代理配置文件失败: {e}")
        return ""


def start_local_proxy(proxy_ip, proxy_port, proxy_user, proxy_pass):
    """
    启动本地转发代理服务器

    原理：
      1. 在本地启动一个 HTTP 代理（如 127.0.0.1:10000），不需要认证
      2. 本地代理自动将请求转发到远程代理（带 Proxy-Authorization 认证头）
      3. 浏览器连接本地代理，不会弹出认证窗口

    Args:
        proxy_ip: 远程代理IP
        proxy_port: 远程代理端口
        proxy_user: 远程代理用户名
        proxy_pass: 远程代理密码

    Returns:
        int: 本地代理端口号
    """
    # 构建 Proxy-Authorization 认证头
    auth_str = f"{proxy_user}:{proxy_pass}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    proxy_auth_header = f"Basic {auth_b64}"

    class LocalProxyHandler(BaseHTTPRequestHandler):
        """本地代理处理器，转发请求到远程代理"""

        def do_CONNECT(self):
            """处理 HTTPS 隧道请求（CONNECT 方法）"""
            try:
                remote_sock = self._connect_remote()
                if remote_sock:
                    self.send_response(200, "Connection Established")
                    self.end_headers()
                    self._tunnel(self.connection, remote_sock)
            except Exception as e:
                self.send_error(502, str(e))

        def _connect_remote(self):
            """连接远程代理并建立隧道"""
            try:
                remote_sock = socket.create_connection((proxy_ip, int(proxy_port)), timeout=30)
                # 发送带认证的 CONNECT 请求
                connect_req = (
                    f"CONNECT {self.path} HTTP/1.1\r\n"
                    f"Host: {self.path}\r\n"
                    f"Proxy-Authorization: {proxy_auth_header}\r\n"
                    f"\r\n"
                )
                remote_sock.sendall(connect_req.encode())
                # 读取代理响应
                response = remote_sock.recv(4096).decode()
                if "200" in response:
                    return remote_sock
                else:
                    logging.warning(f"远程代理拒绝连接: {response[:100]}")
                    return None
            except Exception as e:
                logging.warning(f"连接远程代理失败: {e}")
                return None

        def _tunnel(self, client_sock, remote_sock):
            """双向转发数据"""
            sockets = [client_sock, remote_sock]
            timeout = 60
            while True:
                readable, _, _ = select.select(sockets, [], [], timeout)
                if not readable:
                    break
                for sock in readable:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            return
                        if sock is client_sock:
                            remote_sock.sendall(data)
                        else:
                            client_sock.sendall(data)
                    except Exception:
                        return

        def do_GET(self):
            """处理 HTTP GET 请求"""
            self._forward_request()

        def do_POST(self):
            """处理 HTTP POST 请求"""
            self._forward_request()

        def _forward_request(self):
            """转发 HTTP 请求到远程代理"""
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else None

                # 构建转发请求头（过滤 host/proxy-connection，注入认证）
                headers = {}
                for key, value in self.headers.items():
                    if key.lower() not in ('host', 'proxy-connection'):
                        headers[key] = value
                headers['Proxy-Authorization'] = proxy_auth_header

                # 连接远程代理
                conn = http.client.HTTPConnection(proxy_ip, int(proxy_port), timeout=30)
                conn.request(self.command, self.path, body=body, headers=headers)
                response = conn.getresponse()

                # 返回响应给客户端
                self.send_response(response.status)
                for key, value in response.getheaders():
                    if key.lower() not in ('transfer-encoding',):
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response.read())
                conn.close()
            except Exception as e:
                self.send_error(502, str(e))

        def log_message(self, format, *args):
            """简化日志输出"""
            pass  # 不输出代理转发日志，避免刷屏

    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        """多线程 HTTP 服务器"""
        daemon_threads = True

    # 选择本地代理端口
    local_port = random.randint(10000, 19999)

    # 启动本地代理服务器（后台 daemon 线程）
    server = ThreadedHTTPServer(('127.0.0.1', local_port), LocalProxyHandler)
    proxy_thread = threading.Thread(target=server.serve_forever, daemon=True)
    proxy_thread.start()

    logging.info(f"本地转发代理已启动: 127.0.0.1:{local_port} -> {proxy_ip}:{proxy_port}")
    return local_port


# ============================================================
# 浏览器初始化
# ============================================================

def init_browser(proxy_str=""):
    """
    初始化浏览器（DrissionPage + Chromium）

    使用隐身模式，关闭图片懒加载，设置各种优化参数。
    全局变量 browser 和 tab 会被赋值。

    Args:
        proxy_str: 代理配置字符串，格式: IP:端口:用户名:密码。为空则不使用代理

    Returns:
        bool: 是否初始化成功
    """
    global browser, tab

    max_retries = 3
    for attempt in range(max_retries):
        try:
            logging.info(f"使用 DrissionPage 初始化浏览器... (尝试 {attempt + 1}/{max_retries})")

            # 如果不是第一次尝试，先清理残留 Chrome 进程
            if attempt > 0:
                _cleanup_chrome_processes()

            # 创建浏览器选项
            co = ChromiumOptions()
            co.set_load_mode('none')   # 网页连接成功即停止加载，加快速度
            co.incognito(True)         # 隐身模式
            co.no_imgs(False)          # 不禁用图片（某些页面需要图片加载）
            co.headless(False)         # 非无头模式，需要看到浏览器

            # ---- 代理配置 ----
            # 如果有代理配置，启动本地转发代理，浏览器连接本地代理（无需弹窗认证）
            if proxy_str:
                parts = proxy_str.split(":")
                if len(parts) >= 4:
                    proxy_ip = parts[0]
                    proxy_port = parts[1]
                    proxy_user = parts[2]
                    proxy_pass = ":".join(parts[3:])  # 密码可能包含冒号
                    local_port = start_local_proxy(proxy_ip, proxy_port, proxy_user, proxy_pass)
                    co.set_proxy(f"127.0.0.1:{local_port}")
                    logging.info(f"已启用代理: {proxy_ip}:{proxy_port} (本地转发: 127.0.0.1:{local_port})")
                else:
                    logging.warning(f"代理格式错误，应为 IP:端口:用户名:密码，忽略代理设置")

            # 禁用通知和定位弹窗
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.geolocation": 2
            }
            co.set_pref("profile.default_content_setting_values", prefs)

            # 设置用户数据目录（每个实例独立）
            base_dir = os.path.dirname(os.path.abspath(__file__))
            user_data_dir = os.path.join(base_dir, f"./chrome_profile_{random.randint(1000, 9999)}")
            os.makedirs(user_data_dir, exist_ok=True)
            co.set_user_data_path(user_data_dir)

            # 各种性能优化参数
            co.set_argument("--disable-dev-shm-usage")
            co.set_argument("--disable-gpu")
            co.set_argument("--disable-extensions")
            co.set_argument("--disable-plugins")
            co.set_argument("--disable-features=VizDisplayCompositor")
            co.set_argument("--disable-background-timer-throttling")
            co.set_argument("--disable-renderer-backgrounding")
            co.set_argument("--disable-backgrounding-occluded-windows")
            co.set_argument("--disable-features=TranslateUI")
            co.set_argument("--disable-ipc-flooding-protection")
            co.set_argument("--no-first-run")
            co.set_argument("--no-default-browser-check")
            co.set_argument("--disable-default-apps")
            co.set_argument("--disable-popup-blocking")
            co.set_argument("--disable-prompt-on-repost")
            co.set_argument("--disable-client-side-phishing-detection")
            co.set_argument("--disable-component-update")
            co.set_argument("--disable-hang-monitor")
            co.set_argument("--disable-sync")
            co.set_argument("--metrics-recording-only")
            co.set_argument("--safebrowsing-disable-auto-update")
            co.set_argument("--password-store=basic")
            co.set_argument("--use-mock-keychain")
            co.set_argument("--disable-accelerated-2d-canvas")
            co.set_argument("--disable-accelerated-video-decode")

            # 随机分配调试端口
            co.set_local_port(random.randint(9222, 9999))

            # 启动浏览器
            browser = Chromium(co)
            tab = browser.latest_tab
            tab.set.window.size(1200, 900)

            logging.info(f"DrissionPage 初始化成功")
            return True

        except Exception as e:
            logging.error(f"浏览器初始化失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logging.info("等待 2 秒后重试...")
                time.sleep(2)
            else:
                logging.error("已达到最大重试次数，浏览器初始化失败")
                return False

    return False


def _cleanup_chrome_processes():
    """清理残留的 Chrome 进程（内部函数）"""
    try:
        if platform.system() == "Windows":
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'],
                         capture_output=True, timeout=5)
            subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe', '/T'],
                         capture_output=True, timeout=5)
        else:
            subprocess.run(['pkill', '-9', 'chrome'], capture_output=True, timeout=5)
            subprocess.run(['pkill', '-9', 'chromedriver'], capture_output=True, timeout=5)
        time.sleep(1)
    except Exception as e:
        logging.debug(f"清理 Chrome 进程时出错（可忽略）: {e}")


# ============================================================
# 登录相关
# ============================================================

def wait_for_verification(max_attempts=10, check_interval=3):
    """
    持续检测 Cloudflare 验证页面，直到成功进入站点

    Args:
        max_attempts: 最大检测次数
        check_interval: 每次检测间隔（秒）

    Returns:
        bool: 是否成功进入站点
    """
    try:
        logging.info("开始循环检测 Cloudflare 验证页面...")

        for attempt in range(max_attempts):
            logging.info(f"第 {attempt + 1}/{max_attempts} 次检测验证页面...")
            time.sleep(check_interval)

            page_title = tab.title.lower()

            # 如果标题中没有 "just a moment" 或 "请稍候"，说明验证已通过
            if 'just a moment' not in page_title and '请稍候' not in page_title:
                try:
                    body_text = tab('tag:body').text
                    if body_text and len(body_text) > 50:
                        logging.info("已成功进入站点，无需验证或验证已完成！")
                        return True
                except:
                    pass

        logging.info(f"完成 {max_attempts} 次验证检测")
        return True

    except Exception as e:
        logging.warning(f"验证处理异常: {e}")
        return True


def safe_click_checkbox():
    """
    安全地点击登录页面的 checkbox（同意条款），确保真正生效

    尝试三种方式:
      1. 通过 JS 设置 checked 属性并触发事件
      2. 通过点击 label 元素
      3. 遍历所有 checkbox 逐个点击

    Returns:
        bool: 是否成功勾选
    """
    try:
        logging.info("开始安全点击checkbox...")

        # 方法1: 通过 JS 设置 checked 并触发 change/click 事件
        try:
            checkbox_input = tab.ele("tag:input@@class=custom-control-input@@type=checkbox", timeout=5)
            if checkbox_input:
                tab.run_js("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", checkbox_input)
                time.sleep(1)
                tab.run_js("""
                    arguments[0].checked = true;
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('click', { bubbles: true }));
                """, checkbox_input)
                time.sleep(0.5)
                return True
        except Exception as e:
            logging.warning(f"方法1失败: {e}")

        # 方法2: 通过点击 label 元素
        try:
            label = tab.ele("label=custom-control-label", timeout=3)
            if label:
                tab.run_js("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", label)
                time.sleep(1)
                label.click()
                time.sleep(0.5)
                try:
                    checkbox_input = tab.ele("input.custom-control-input[type='checkbox']", timeout=2)
                    if checkbox_input and checkbox_input.attr('checked'):
                        logging.info("方法2成功：通过点击label勾选了checkbox")
                    return True
                except:
                    pass
        except Exception as e:
            logging.warning(f"方法2失败: {e}")

        # 方法3: 遍历所有 checkbox 逐个点击
        try:
            checkboxes = tab.eles("input[type='checkbox'].custom-control-input")
            if checkboxes:
                for idx, cb in enumerate(checkboxes):
                    try:
                        tab.run_js("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", cb)
                        time.sleep(0.5)
                        cb.click()
                        time.sleep(0.5)
                        if cb.attr('checked'):
                            logging.info(f"方法3成功：已勾选第 {idx+1} 个checkbox")
                        return True
                    except:
                        continue
        except Exception as e:
            logging.warning(f"方法3失败: {e}")

        logging.error("所有方法都未能成功勾选checkbox")
        return False

    except Exception as e:
        logging.error(f"安全点击checkbox过程出现异常: {e}")
        return False


def login(username, password):
    """
    执行登录流程

    步骤:
      1. 打开登录页面
      2. 等待 Cloudflare 验证
      3. 关闭 cookies 弹窗
      4. 切换到邮箱登录
      5. 输入邮箱和密码
      6. 勾选同意条款 checkbox
      7. 点击登录按钮
      8. 验证是否登录成功

    Args:
        username: 邮箱地址
        password: 密码

    Returns:
        bool: 是否登录成功
    """
    try:
        logging.info("开始登录流程...")

        # 步骤1: 打开登录页面
        tab.get(LOGIN_URL)
        wait_for_verification()
        time.sleep(1)

        # 步骤2: 关闭 cookies 弹窗
        try:
            cookies_btn = tab.ele("xpath://*[@id='consent-tracking']/div/div/div[2]/button", timeout=5)
            if cookies_btn:
                cookies_btn.click()
                logging.info("已关闭cookies弹窗")
            else:
                logging.info("未找到cookies弹窗关闭按钮。")
        except:
            logging.warning("未找到cookies弹窗关闭按钮")

        # 步骤3: 切换到邮箱登录
        try:
            email_login_btn = tab.ele("xpath://*[@id='maincontent']/div/div/div[1]/div/div[1]/div/form/button", timeout=10)
            if email_login_btn:
                email_login_btn.click()
                logging.info("已点击邮箱登录切换按钮")
        except:
            logging.warning("未找到邮箱登录切换按钮，可能已经在邮箱登录页面")

        # 步骤4: 输入邮箱
        try:
            email_input = tab.ele("tag:input@@type=email", timeout=10)
            if email_input:
                email_input.clear()
                email_input.input(username)
                logging.info(f"已输入邮箱: {username}")
        except:
            logging.error("未找到邮箱输入框")
            return False

        # 步骤5: 输入密码
        try:
            password_input = tab.ele("tag:input@@type=password", timeout=10)
            if password_input:
                password_input.clear()
                password_input.input(password)
                logging.info("已输入密码")
        except:
            logging.error("未找到密码输入框")
            return False

        # 步骤6: 勾选 checkbox
        if not safe_click_checkbox():
            logging.warning("checkbox点击失败，但继续尝试登录")

        time.sleep(1)

        # 步骤7: 点击登录按钮
        try:
            login_submit_btn = tab.ele("tag:button@@class=btn btn-block btn-primary js-action", timeout=10)
            if login_submit_btn:
                login_submit_btn.click()
                logging.info("已点击登录提交按钮")
        except:
            logging.error("未找到登录提交按钮")
            return False

        # 步骤8: 等待验证并检查是否登录成功
        time.sleep(5)
        wait_for_verification(max_attempts=3, check_interval=2)

        current_url = tab.url
        if "Login-Show" not in current_url:
            logging.info("登录成功！")
            return True
        else:
            logging.error("登录失败")
            return False

    except Exception as e:
        logging.error(f"登录失败: {e}")
        return False


# ============================================================
# 商品页面操作
# ============================================================

def navigate_to_product(target_url):
    """
    导航到商品页面

    Args:
        target_url: 商品页面 URL

    Returns:
        bool: 是否导航成功
    """
    try:
        logging.info("导航到商品页面...")
        tab.get(target_url)
        tab.wait.ele_displayed("xpath=//*[@id='pdpContainer']/div[10]/div[1]/div/div/div[1]/div[1]")
        tab.stop_loading()  # 主动停止加载，加快速度
        detect_model_mode()
        return True
    except Exception as e:
        logging.error(f"导航失败: {e}")
        return False


def detect_model_mode():
    """
    检测当前页面是 Pro 还是 Pro Max 型号

    通过检测页面上的 select 元素类型来判断:
      - 有原生 select.select-color -> Pro 型号
      - 有自定义 .select-items -> Pro Max 型号

    结果会设置全局变量 is_pro_model
    """
    global is_pro_model

    url_lower = (tab.url or TARGET_URL).lower()

    has_custom_select = False
    has_native_select = False
    try:
        has_custom_select = len(tab.eles(".select-items")) >= 2
    except Exception:
        pass
    try:
        has_native_select = bool(tab.eles("select.select-color"))
    except Exception:
        pass

    if has_custom_select and not has_native_select:
        is_pro_model = False
    elif has_native_select and not has_custom_select:
        is_pro_model = True
    else:
        # 通过 URL 推断
        is_promax_url = any(token in url_lower for token in ("promax", "pro_max", "pro-max", "pro max"))
        is_pro_url = ("proscol" in url_lower or "/ip17_pro" in url_lower or "ip17_pro" in url_lower)
        if is_promax_url:
            is_pro_model = False
        elif is_pro_url:
            is_pro_model = True
        else:
            is_pro_model = False

    if is_pro_model:
        logging.info("检测到Pro型号页面，将使用Pro专用解析方式")
    else:
        logging.info("检测到Pro Max型号页面，将使用Pro Max解析方式")


# ============================================================
# 库存检查
# ============================================================

def check_stock(color_id_str, rom_id_str):
    """
    使用 DrissionPage 在页面上检查库存

    通过 JS 选择颜色选项，然后监听 Product-Variation 接口返回的数据，
    检查目标内存选项是否可选（selectable）。

    Args:
        color_id_str: 目标颜色的 data-id 值
        rom_id_str: 目标内存的 id 值

    Returns:
        bool: 目标商品是否有库存
    """
    try:
        # 查找颜色选项
        color_option = tab.ele(f"tag:option@@data-id={color_id_str}")
        if color_option:
            # 开始监听 Product-Variation 接口
            tab.listen.start('on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation')

            # 通过 JS 选择颜色并触发 change 事件
            js_code = f'''
            (function() {{
                var select = document.querySelector('select.select-color, select[data-attr="select-color"]');
                if (select) {{
                    var options = select.querySelectorAll('option');
                    for (var i = 0; i < options.length; i++) {{
                        var opt = options[i];
                        if (opt.getAttribute('data-id') === '{color_id_str}' || opt.getAttribute('data-attr-value') === '{color_id_str}') {{
                            opt.selected = true;
                            var event = new Event('change', {{ bubbles: true }});
                            select.dispatchEvent(event);
                            return true;
                        }}
                    }}
                }}
                return false;
            }})();
            '''
            tab.run_js(js_code)

            # 等待接口返回数据
            for packet in tab.listen.steps():
                body = packet.response.body
                # 如果遇到 Cloudflare 验证，刷新页面
                if "Just a moment" in body:
                    tab.refresh()
                    return False

                # 从返回数据中解析内存选项
                rom_list = body["product"]["variationAttributes"][1]["values"]
                for rom in rom_list:
                    if rom["id"] == rom_id_str:
                        return rom['selectable']
                break
        else:
            logging.error(f"未找到目标颜色 ID: {color_id_str}，请确认颜色是否正确")
            return False

    except Exception as e:
        logging.error(f"检查库存时出错: {e}")
        tab.refresh()
        return False


# ============================================================
# 加入购物车并结账
# ============================================================

def add_to_cart_and_checkout(goods_choice, target_color, target_storage):
    """
    选择指定颜色和容量，然后加入购物车并跳转到结算页面

    步骤:
      1. 通过 requests 接口加入购物车
      2. 跳转到结账页面
      3. 完成结账流程

    Args:
        goods_choice: 商品编号
        target_color: 目标颜色值
        target_storage: 目标存储容量值

    Returns:
        bool: 是否成功进入支付页面
    """
    try:
        # 步骤1: 加入购物车
        logging.info("步骤1: 点击加入购物车...")
        status_code = add_cart(tab, goods_choice, target_color, target_storage)
        if 200 != status_code:
            logging.error(f"加入购物车失败: {status_code}")
            if status_code == 429:
                logging.warning("加入购物车失败，可能是因为请求频率过高，开始休息20分钟后重试")
                time.sleep(1200)
            return False
        logging.info("成功加入购物车...")

        # 步骤2: 跳转到结账页面
        logging.info("步骤2: 跳转到结账页面...")
        try:
            tab.get(CHECKOUT_URL)
            logging.info(f"已跳转到结账页面: {CHECKOUT_URL}")
            time.sleep(FAST_POST_CLICK_DELAY)

            # 步骤3: 完成结账
            if complete_checkout():
                logging.info("抢购成功！已进入支付页面！")
                return True
            else:
                logging.warning("结账流程未完成，但已加入购物车")
                return True

        except Exception as e:
            logging.error(f"跳转到结账页面失败: {e}")
            try:
                tab.get(CART_URL)
                logging.info("已跳转到购物车页面（备用方案）")
                return True
            except:
                return False

    except Exception as e:
        logging.error(f"加入购物车/结算失败: {e}")
        return False


def add_to_cart_and_checkout_drissionpage(goods_choice, target_color, target_storage):
    """
    使用 DrissionPage 直接在页面上操作加入购物车并提交订单

    步骤:
      1. 选择颜色选项
      2. 选择内存选项
      3. 点击同意协议
      4. 输入订购数量
      5. 点击加入购物车按钮
      6. 监听加入购物车请求结果
      7. 在新标签页点击提交订单

    Args:
        goods_choice: 商品编号
        target_color: 目标颜色值
        target_storage: 目标存储容量值

    Returns:
        bool: 是否成功提交订单
    """
    global new_tab

    # 步骤1: 选择颜色
    color_option = tab.ele(f"tag:option@@data-id={target_color}")
    if color_option:
        logging.info(f"找到目标颜色: {target_color}")
        color_option.click()
    else:
        logging.error(f"未找到目标颜色 ID: {target_color}")
        return False

    time.sleep(1)

    # 步骤2: 选择内存
    rom_option = tab.ele(f"tag:option@@data-id={target_storage}")
    if rom_option:
        logging.info(f"找到目标内存: {target_storage}")
        rom_option.click()
        logging.info("已点击目标内存")
    else:
        logging.error(f"未找到目标内存 ID: {target_storage}")
        return False

    # 步骤3: 点击同意协议
    agree_option = tab.ele(f"tag:p@@text()=本人聲明及確認購買此產品只作自用而非作轉售用途，明白及同意以上安排。")
    if agree_option:
        logging.info("找到同意协议")
        agree_option.click()
        logging.info("已点击同意协议")
    else:
        logging.error("未找到同意协议")
        return False

    # 步骤4: 输入订购数量
    count_option = tab.ele("tag:input@@type=number@@inputmode=numeric")
    if count_option:
        logging.info("找到订购数量输入框")
        count_option.clear()
        count_option.input("2")
        logging.info("已输入订购数量: 2")
    else:
        logging.error("未找到订购数量输入框")
        return False

    # 步骤5: 点击加入购物车按钮
    add_cart_option = tab.ele("tag:button@@class=add-to-cart btn btn-primary btn-block", timeout=0.5)
    if add_cart_option:
        logging.info("找到加入购物车按钮")
        # 开始监听加入购物车的请求
        tab.listen.start('on/demandware.store/Sites-hkt-hk-Site/zh_HK/Cart-AddProduct')
        add_cart_option.scroll.to_see()
        add_cart_option.click()
        logging.info("已点击加入购物车按钮")
    else:
        logging.error("未找到加入购物车按钮")
        return False

    # 测试模式下暂停等待手动操作
    if is_in_coding:
        input("请手动完成后续支付流程，完成后按任意键继续...")

    # 步骤6: 监听加入购物车请求结果
    for packet in tab.listen.steps():
        status = packet.response.status
        logging.info(f"加入购物车请求状态码: {status}")
        if status == 200:
            logging.info("加入购物车成功")
            break
        else:
            logging.error(f"加入购物车失败, 状态码: {status}")
            return False

    # 步骤7: 在新标签页点击提交订单
    logging.info("点击提交订单按钮...")
    submit_button = new_tab.ele("xpath://*[@id='place-order']")
    if submit_button:
        submit_button.click()
        logging.info("已点击提交订单按钮！进入支付页面...")
        time.sleep(3)
        return True
    else:
        logging.error("未找到提交订单按钮元素")
        return False


def complete_checkout():
    """
    完成结账流程

    步骤:
      1. 选择 Visa 支付方式
      2. 等待加载完成
      3. 勾选条款确认
      4. 点击提交订单按钮

    Returns:
        bool: 是否成功提交订单
    """
    try:
        logging.info(f"当前页面 URL: {tab.url}")

        # 步骤1: 选择 Visa 支付方式
        logging.info("结账步骤1: 选择支付方式...")
        visa_payment = tab.ele("xpath://*[@id='checkout-main']/div[1]/div[1]/form/div/div[3]/div[2]/div[1]")
        if visa_payment:
            visa_payment.click()
            logging.info("已选择 Visa支付方式")
        else:
            logging.error("未找到 Visa支付方式元素")
            return False

        # 步骤2: 等待加载遮罩消失
        tab.wait.ele_displayed("tag:div@@class=veil")
        tab.wait.ele_deleted("tag:div@@class=veil")

        # 步骤3: 勾选条款确认
        logging.info("结账步骤2: 勾选条款确认...")
        ok_checkbox = tab.ele("xpath://*[@id='checkout-main']/div[1]/div[2]/div[1]/div[2]/div[2]/form/div[1]/div[1]/label/div/p")
        if ok_checkbox:
            ok_checkbox.click()
            logging.info("已勾选条款确认")
        else:
            logging.error("未找到条款确认元素")
            return False
        time.sleep(0.1)

        # 步骤4: 点击提交订单按钮
        logging.info("结账步骤3: 点击提交订单按钮...")
        submit_button = tab.ele("xpath://*[@id='place-order']")
        if submit_button:
            submit_button.click()
            logging.info("已点击提交订单按钮！进入支付页面...")
        else:
            logging.error("未找到提交订单按钮元素")
            return False

    except Exception as e:
        logging.error(f"完成结账流程失败: {e}")
        return False


# ============================================================
# 捡漏模式
# ============================================================

def enter_checkout_payment_page():
    """
    捡漏模式：反复进入支付页面，直到确认已跳转成功

    Returns:
        bool: 是否成功进入支付页面
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            tab.get(CHECKOUT_URL)
            time.sleep(1)

            # 检查是否已在支付页面
            current_url = tab.url or ""
            if "Checkout-Begin?stage=payment" in current_url or tab.eles("#place-order"):
                logging.info("已进入支付页面，开始点击提交按钮")
                return True

            logging.info(f"捡漏模式第 {attempt} 轮：尚未进入支付页面，{CSL_SCAVENGE_INTERVAL} 秒后重试")
        except Exception as e:
            logging.warning(f"捡漏模式第 {attempt} 轮进入支付页面失败: {e}")

        time.sleep(CSL_SCAVENGE_INTERVAL)


def enter_cart_page():
    """
    捡漏模式：反复进入购物车页面，直到确认已跳转成功

    Returns:
        bool: 是否成功进入购物车页面
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            tab.get(CART_URL)
            current_url = tab.url or ""
            if "cart" in current_url:
                logging.info("已进入购物车页面，开始点击提交按钮")
                return True

            logging.info(f"捡漏模式第 {attempt} 轮：尚未进入购物车页面，{CSL_SCAVENGE_INTERVAL} 秒后重试")
        except Exception as e:
            logging.warning(f"捡漏模式第 {attempt} 轮进入购物车页面失败: {e}")

        time.sleep(CSL_SCAVENGE_INTERVAL)


def run_scavenge_mode(goods_choice):
    """
    CSL 捡漏模式：跳过库存检查，直接反复进入支付页并提交订单

    Args:
        goods_choice: 商品编号（用于上报统计）
    """
    logging.info(f"已开启 CSL 捡漏模式：跳过库存检查，每 {CSL_SCAVENGE_INTERVAL} 秒轮询支付页面")

    while True:
        enter_checkout_payment_page()

        if complete_checkout():
            logging.info("捡漏成功！请手动完成后续支付流程。")
            report_order_success({"mode": "scavenge", "goods": goods_options.get(goods_choice, {}).get("name", "unknown")})
            play_success_sound('y1871.wav', repeat=3)
            logging.info("浏览器将保持打开状态，按 Ctrl+C 终止程序...")
            while True:
                time.sleep(1)

        logging.warning(f"本轮提交失败，{CSL_SCAVENGE_INTERVAL} 秒后重新进入支付页面继续尝试...")
        time.sleep(CSL_SCAVENGE_INTERVAL)


def run_scavenge_mode2(goods_choice):
    """
    CSL 捡漏模式2：先进入购物车页面检查，再进入支付页提交订单

    Args:
        goods_choice: 商品编号（用于上报统计）
    """
    logging.info(f"已开启 CSL 捡漏模式：跳过库存检查，每 {CSL_SCAVENGE_INTERVAL} 秒轮询购物车页面")

    while True:
        enter_cart_page()
        if "售罄" in tab.html:
            logging.info("商品已售罄，无法购买")
            continue
        else:
            run_scavenge_mode(goods_choice)
        time.sleep(CSL_SCAVENGE_INTERVAL)


# ============================================================
# 主流程
# ============================================================

def run(username, password, target_color, target_storage, scavenge_mode, goods_choice, proxy_str=""):
    """
    主抢购流程（单线程顺序执行）

    步骤:
      1. 初始化浏览器（支持代理）
      2. 如果使用代理，先访问CSL首页通过Cloudflare验证
      3. 登录
      4. 创建新标签页并打开商品页面
      5. 如果是捡漏模式，直接进入捡漏流程
      6. 如果是正常模式，循环检查库存，有货则抢购

    Args:
        username: 登录邮箱
        password: 登录密码
        target_color: 目标颜色值
        target_storage: 目标存储容量值
        scavenge_mode: 是否为捡漏模式
        goods_choice: 商品编号
        proxy_str: 代理配置字符串，格式: IP:端口:用户名:密码。为空则不使用代理
    """
    global new_tab

    last_refresh_time = 0

    # ---- 步骤1: 初始化浏览器 ----
    if not init_browser(proxy_str):
        return

    # ---- 步骤2: 如果使用代理，先访问CSL首页通过Cloudflare验证 ----
    if proxy_str:
        logging.info("使用代理模式，先访问CSL首页通过Cloudflare验证...")
        tab.get("https://eshop.hkcsl.com/zh_HK/")
        time.sleep(5)
        # 检查是否需要通过Cloudflare
        if "just a moment" in tab.title.lower() or "請稍候" in tab.title.lower():
            logging.info("等待Cloudflare验证通过...")
            time.sleep(10)
            # 如果仍未通过，刷新一次
            if "just a moment" in tab.title.lower() or "請稍候" in tab.title.lower():
                logging.info("刷新页面重试...")
                tab.refresh()
                time.sleep(10)
        logging.info(f"Cloudflare验证完成，页面标题: {tab.title}")

    # ---- 步骤3: 登录 ----
    while True:
        if login(username, password):
            break
        else:
            logging.error("登录失败，重试...")
            time.sleep(2)

    # ---- 步骤4: 创建新标签页并打开商品页面 ----
    new_tab = browser.new_tab()
    new_tab.get(TARGET_URL)
    input("请手动在新tab中打开商品页面，添加到购物车，并完成选择支付方式，完成后按任意键继续...")

    # ---- 步骤5: 捡漏模式 ----
    if scavenge_mode:
        run_scavenge_mode2(goods_choice)
        return

    # ---- 步骤6: 正常抢购模式 - 导航到商品页面 ----
    if not navigate_to_product(TARGET_URL):
        logging.error("无法导航到商品页面，终止运行")
        return

    interval_label = "无间隔" if CHECK_INTERVAL <= 0 else f"{CHECK_INTERVAL}秒"
    logging.info(f"开始监控库存，检查间隔: {interval_label}...")

    # 商品信息字典
    goods = {
        "name": goods_options[goods_choice]["name"],
        "color": target_color,
        "rom": target_storage
    }

    # ---- 步骤6: 循环检查库存 ----
    check_num = 0
    while True:
        # 如果页面跳转到首页，重新导航
        if "zh_HK/home" in tab.url:
            tab.get(TARGET_URL)
            time.sleep(2)
            continue

        check_num += 1
        if check_num % 10 == 0:
            print(f"第{check_num}次开始检查库存: {goods['name']}, 颜色: {goods['color']}, 内存: {goods['rom']}")

        # 检查库存
        if check_stock(goods["color"], goods["rom"]):
            logging.info("有货了，开始加入购物车。")

            # 尝试加入购物车并结账
            if add_to_cart_and_checkout_drissionpage(goods_choice, target_color, target_storage):
                logging.info("抢购成功！请手动完成后续支付流程。")
                try:
                    # 等待支付页面加载
                    is_payment_page = False
                    for _ in range(10):
                        if "https://onepayment.pccw.com/ecom/web/v2/pay?p=" in new_tab.url:
                            is_payment_page = True
                            break
                        time.sleep(1)

                    if is_payment_page:
                        logging.info("支付页面加载完成")
                        play_success_sound('y1871.wav', repeat=3)
                        logging.info(f"当前url: {new_tab.url}")
                        report_order_success(goods)
                except:
                    pass

                logging.info("浏览器将保持打开状态，按 Ctrl+C 终止程序...")
                while True:
                    time.sleep(60)
            else:
                logging.error("抢购失败，继续监控...")
                tab.refresh()
                time.sleep(FAST_RETRY_DELAY)
        else:
            # 无货，继续监控
            time.sleep(1)
            if check_num % 10 == 0:
                logging.info(f"第{check_num}次当前库存不足，继续监控...")
            # 每8分钟刷新一次页面
            if time.time() - last_refresh_time > 8 * 60:
                tab.refresh()
                last_refresh_time = time.time()
                logging.info("刷新页面")

        # 检查间隔
        if CHECK_INTERVAL > 0:
            time.sleep(CHECK_INTERVAL)


# ============================================================
# 入口函数
# ============================================================

def main():
    """
    主函数 - 用户交互入口

    步骤:
      1. 验证授权
      2. 选择测试模式
      3. 选择运行模式（正常/捡漏）
      4. 选择商品、颜色、内存
      5. 确认配置
      6. 加载账号
      7. 启动抢购（单线程，只取第一个账号）
    """
    global TARGET_URL, is_in_coding

    # ---- 步骤1: 验证授权 ----
    if not verify_auth():
        input("初始化不成功，按任意键退出...")
        return

    interval_label = "0秒(无间隔)" if CHECK_INTERVAL <= 0 else f"{CHECK_INTERVAL}秒"
    print(f"""
    ╔═══════════════════════════════════════╗
    ║     单线程网站抢购助手（简化版）      ║
    ║     使用 DrissionPage 驱动           ║
    ║                                       ║
    ║  目标: 香港CSL手机抢购                ║
    ║  检查间隔: {interval_label:<23}║
    ╚═══════════════════════════════════════╝
    """)

    # ---- 步骤2: 选择测试模式 ----
    print("是否在测试模式：")
    print("1. 不是")
    print("2. 是")
    is_in_coding = (input("请输入 (1-2，默认1): ").strip() == "2")

    # ---- 步骤3: 选择运行模式 ----
    print("请选择运行模式:")
    print("  1. 正常抢购模式")
    print("  2. CSL捡漏模式（跳过库存检查，直接轮询支付页提交订单）")
    mode_choice = input("请输入模式 (1-2，默认1): ").strip() or "1"
    if mode_choice not in ("1", "2"):
        print("错误：无效的模式选择")
        return

    scavenge_mode = (mode_choice == "2")
    selected_color = None
    selected_storage = None
    goods_choice = None

    if scavenge_mode:
        print("\n已选择: CSL捡漏模式")
        print(f"将每 {CSL_SCAVENGE_INTERVAL} 秒重复进入支付页：{CHECKOUT_URL}")
    else:
        # ---- 步骤4: 选择商品、颜色、内存 ----
        print("请选择因要抢购的商品：")
        for key, value in goods_options.items():
            print(f"  {key}. {value['name']}")
        goods_choice = input("请输入数字选择商品 (1-5): ").strip()
        if goods_choice not in goods_options:
            print("错误：无效的商品选择")
            return
        TARGET_URL = goods_options[goods_choice]["url"]

        # 选择颜色
        color_options = IPHONE_17_COLOR_OPTIONS if goods_choice == "3" else IPHONE_17_PRO_AND_PROMAX_COLOR_OPTIONS
        print("\n请选择要抢购的颜色:")
        for key, value in color_options.items():
            print(f"  {key}. {value['name']}")
        color_choice = input("请输入数字选择颜色: ").strip()
        if color_choice not in color_options:
            print("错误：无效的颜色选择")
            return
        selected_color = color_options[color_choice]
        print(f"已选择颜色: {selected_color['name']}")

        # 选择内存
        print("\n请选择要抢购的内存空间:")
        for key, value in STORAGE_OPTIONS.items():
            print(f"  {key}. {value['name']}")
        storage_choice = input("请输入数字选择内存 (1-4): ").strip()
        if storage_choice not in STORAGE_OPTIONS:
            print("错误：无效的内存选择")
            return
        selected_storage = STORAGE_OPTIONS[storage_choice]
        print(f"已选择内存: {selected_storage['name']}")

    # ---- 步骤5: 是否使用代理IP ----
    proxy_str = ""
    loaded_proxy = load_proxy('proxy.txt')
    if loaded_proxy:
        print(f"\n检测到代理配置: {loaded_proxy.split(':')[0]}:{loaded_proxy.split(':')[1]}")
        print("是否使用代理IP？")
        print("  1. 使用代理IP")
        print("  2. 不使用代理IP（直连）")
        proxy_choice = input("请输入 (1-2，默认1): ").strip() or "1"
        if proxy_choice == "1":
            proxy_str = loaded_proxy
            print(f"已启用代理: {loaded_proxy.split(':')[0]}:{loaded_proxy.split(':')[1]}")
        else:
            print("已选择直连模式")
    else:
        print("\n未检测到代理配置（proxy.txt 为空或不存在），将使用直连模式")

    # ---- 步骤6: 确认配置 ----
    proxy_display = f"{proxy_str.split(':')[0]}:{proxy_str.split(':')[1]}" if proxy_str else "不使用代理"

    print("\n" + "="*50)
    print("抢购配置汇总:")
    print(f"  运行模式: {'CSL捡漏模式' if scavenge_mode else '正常抢购模式'}")
    print(f"  代理: {proxy_display}")
    if scavenge_mode:
        print(f"  支付页URL: {CHECKOUT_URL}")
        print(f"  轮询间隔: {CSL_SCAVENGE_INTERVAL}秒")
    else:
        print(f"  商品URL: {TARGET_URL}")
        print(f"  目标颜色: {selected_color['name']}")
        print(f"  目标内存: {selected_storage['name']}")
    print("="*50)

    confirm = input("\n确认开始抢购? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return

    # ---- 步骤7: 加载账号 ----
    accounts = load_accounts('account.txt')
    if not accounts:
        print("错误：未能加载任何账号，请检查 account.txt 文件")
        return

    # ---- 步骤7: 启动抢购（单线程，只取第一个账号） ----
    username, password = accounts[0]
    print(f"\n使用账号: {username}，准备启动...\n")

    try:
        run(
            username=username,
            password=password,
            target_color=selected_color['value'] if selected_color else None,
            target_storage=selected_storage['value'] if selected_storage else None,
            scavenge_mode=scavenge_mode,
            goods_choice=goods_choice,
            proxy_str=proxy_str
        )
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        print("浏览器窗口将保持打开状态，请手动关闭")


if __name__ == "__main__":
    main()
