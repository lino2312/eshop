#!/usr/bin/env python3
"""
多线程网站抢购助手
使用DrissionPage实现多账号并发抢购
"""
from csl_test.set import iphone_17_pro_max, iphone_17, iphone_17_pro
from csl_test.check_stock import get_check_stock
from csl_test.check_stock_selenium import check_stock_with_selenium2
import time
import threading
import random
from DrissionPage import Chromium, ChromiumOptions
from DrissionPage.errors import ElementNotFoundError, WaitTimeoutError
from DrissionPage.common import Keys
import logging
from datetime import datetime
import os
import platform
import subprocess
import socket
import base64
import select
import http.client
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from auth_client import verify_auth, report_order_success
from base.add_cart import base_add_cart
from send_email import send_email
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rush_buy.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

TARGET_URL = ""
LOGIN_URL = "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Login-Show"
CHECKOUT_URL = "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Checkout-Begin?stage=payment"
CART_URL = "https://eshop.hkcsl.com/zh_HK/cart"
CHECK_INTERVAL = 0
VERBOSE_STOCK_LOG = False
FAST_ACTION_DELAY = 0.05
FAST_POST_CLICK_DELAY = 0.1
FAST_CART_DELAY = 0.15
FAST_SCROLL_DELAY = 0.05
FAST_SELECT_OPEN_DELAY = 0.2
FAST_SELECT_APPLY_DELAY = 0.1
FAST_RETRY_DELAY = 0.1
CSL_SCAVENGE_INTERVAL = 0.5
PRO_COLOR_TO_MEMORY_DELAY = 1.0
PROMAX_COLOR_TO_MEMORY_DELAY = 1.0
is_in_coding = False                     # 是否在测试模式下

IPHONE_17_PRO_AND_PROMAX_COLOR_OPTIONS = {
    "1": {"name": "銀色", "value": "927"},
    "2": {"name": "宇宙橙色", "value": "31033"},
    "3": {"name": "深墨藍色", "value": "31034"}
}
IPHONE_17_COLOR_OPTIONS = {
    "1": {"name": "黑色", "value": "25"},
    "2": {"name": "白色", "value": "962"},
    "3": {"name": "藍色", "value": "16827"},
    "4": {"name": "薰衣草紫色", "value": "15121"},
    "5": {"name": "鼠尾草綠色", "value": "31032"}
}
IPHONE_18_PRO_COLOR_OPTIONS = {
    "1": {"name": "黑色", "value": "25"},
    "2": {"name": "銀色", "value": "927"},
    "3": {"name": "布根地紅色", "value": "33609"},
    "4": {"name": "冰川色", "value": "33610"}
}

IPHONE_18_PRO_MAX_COLOR_OPTIONS = {
    "1": {"name": "黑色", "value": "25"},
    "2": {"name": "銀色", "value": "927"},
    "3": {"name": "布根地紅色", "value": "33609"},
    "4": {"name": "冰川色", "value": "33610"}
}

STORAGE_OPTIONS = {
    "1": {"name": "256GB", "value": "1025"},
    "2": {"name": "512GB", "value": "1026"},
    "3": {"name": "1TB", "value": "1027"},
    "4": {"name": "2TB", "value": "4697"}
}

goods_options = {
    "1": {"name": "iphone_17_pro_max", "url": "https://eshop.hkcsl.com/zh_HK/apple/iPhone/IP17_promaxscol.html"},
    "2": {"name": "iphone_17_pro", "url": "https://eshop.hkcsl.com/zh_HK/apple/iPhone/IP17_proscol.html"},
    "3": {"name": "iphone_17", "url": "https://eshop.hkcsl.com/zh_HK/apple/IP17scol.html"},
    "4": {"name": "iphone_17_promax_and_airpods_pro_3", "url": "https://eshop.hkcsl.com/zh_HK/apple/iPhone/P3_IP17_promaxscol.html"},
    "5": {"name": "iphone_17_pro_and_airpods_pro_3", "url": "https://eshop.hkcsl.com/zh_HK/apple/iPhone/P3_IP17_proscol.html"},
    "6": {"name": "iphone_18_pro_max", "url": "https://eshop.hkcsl.com/zh_HK/apple/iPhone/IP18_promaxscol.html"},
    "7": {"name": "iphone_18_pro", "url": "https://eshop.hkcsl.com/zh_HK/apple/iPhone/IP18_proscol.html"}
}

class PortManager:
    def __init__(self):
        self.used_ports = set()
        self.lock = threading.Lock()
    
    def get_available_port(self, start_port=9222, end_port=9999):
        """获取可用的调试端口"""
        with self.lock:
            attempts = 0
            max_attempts = 100
            
            while attempts < max_attempts:
                port = random.randint(start_port, end_port)
                if port not in self.used_ports and self.is_port_available(port):
                    self.used_ports.add(port)
                    return port
                attempts += 1
            
            port = start_port
            while port <= end_port:
                if port not in self.used_ports and self.is_port_available(port):
                    self.used_ports.add(port)
                    return port
                port += 1
            
            raise Exception("无法找到可用端口")
    
    def is_port_available(self, port):
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result != 0
        except:
            return False
    
    def release_port(self, port):
        """释放端口"""
        with self.lock:
            self.used_ports.discard(port)

port_manager = PortManager()


def play_success_sound(sound_file='y1871.wav', repeat=3):
    """
    播放成功音效
    sound_file: 音效文件路径
    repeat: 重复播放次数
    """
    def play_in_thread():
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sound_path = os.path.join(script_dir, sound_file)

            if not os.path.exists(sound_path):
                logging.warning(f"音效文件不存在: {sound_path}")
                return

            logging.info(f"🔊 开始播放成功音效，循环 {repeat} 次")

            system = platform.system()

            for i in range(repeat):
                logging.info(f"🔊 播放第 {i+1}/{repeat} 遍")

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

            logging.info("🔊 音效播放完成")

        except Exception as e:
            logging.error(f"播放音效失败: {e}")

    sound_thread = threading.Thread(target=play_in_thread, daemon=True)
    sound_thread.start()


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
            """简化日志输出，不输出代理转发日志避免刷屏"""
            pass

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


class RushBuyBot:
    """抢购机器人类"""

    def __init__(self, username, password, thread_id, target_color=None, target_storage=None, scavenge_mode=False, goods_choice="1", proxy_str=""):
        self.username = username
        self.password = password
        self.thread_id = thread_id
        self.target_color = target_color
        self.target_storage = target_storage
        self.scavenge_mode = scavenge_mode
        self.proxy_str = proxy_str
        self.browser = None
        self.tab = None
        self.logger = logging.getLogger(f"Thread-{thread_id}")
        self.debugging_port = None
        self.user_data_dir = None
        self.is_pro_model = False
        self.goods_choice = goods_choice
        self.new_tab = None

    def cleanup_chrome_processes(self):
        """清理残留的 Chrome 进程"""
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
            self.logger.debug(f"清理 Chrome 进程时出错（可忽略）: {e}")

    def init_driver(self):
        """初始化浏览器驱动 - 使用 DrissionPage"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                
                self.logger.info(f"🚀 使用 DrissionPage 初始化浏览器... (尝试 {attempt + 1}/{max_retries})")
                
                if attempt > 0:
                    self.cleanup_chrome_processes()
                
                co = ChromiumOptions()
                # 'normal'：阻塞进程，等待所有资源下载完成（默认）
                # 'eager'：DOM 就绪即停止加载
                # 'none'：网页连接成功即停止加载
                co.set_load_mode('none')
                co.incognito(True)
                co.no_imgs(False)
                co.headless(False)

                # ---- 代理配置 ----
                # 如果有代理配置，启动本地转发代理，浏览器连接本地代理（无需弹窗认证）
                if self.proxy_str:
                    parts = self.proxy_str.split(":")
                    if len(parts) >= 4:
                        proxy_ip = parts[0]
                        proxy_port = parts[1]
                        proxy_user = parts[2]
                        proxy_pass = ":".join(parts[3:])  # 密码可能包含冒号
                        local_port = start_local_proxy(proxy_ip, proxy_port, proxy_user, proxy_pass)
                        co.set_proxy(f"127.0.0.1:{local_port}")
                        self.logger.info(f"已启用代理: {proxy_ip}:{proxy_port} (本地转发: 127.0.0.1:{local_port})")
                    else:
                        self.logger.warning(f"代理格式错误，应为 IP:端口:用户名:密码，忽略代理设置")

                prefs = {
                    "profile.default_content_setting_values.notifications": 2,
                    "profile.default_content_setting_values.geolocation": 2
                }
                co.set_pref("profile.default_content_setting_values", prefs)
                
                self.user_data_dir = os.path.join(base_dir, f"./chrome_profile_{self.thread_id}_{random.randint(1000, 9999)}")
                os.makedirs(self.user_data_dir, exist_ok=True)
                
                co.set_user_data_path(self.user_data_dir)
                
                # co.set_argument("--no-sandbox")
                co.set_argument("--disable-dev-shm-usage")
                # co.set_argument("--disable-blink-features=AutomationControlled")
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
                # co.set_argument("--disable-setuid-sandbox")
                
                offset = (self.thread_id - 1) % 10 * 50
                co.set_argument(f"--window-position={offset},{offset}")
                
                self.debugging_port = port_manager.get_available_port()
                co.set_local_port(self.debugging_port)
                
                self.browser = Chromium(co)
                self.tab = self.browser.latest_tab
                
                self.tab.set.window.size(1200, 900)
                
                self.logger.info(f"✅ DrissionPage 初始化成功 - 账号: {self.username}, 调试端口: {self.debugging_port}")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ 浏览器初始化失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if self.debugging_port:
                    port_manager.release_port(self.debugging_port)
                if self.user_data_dir and os.path.exists(self.user_data_dir):
                    import shutil
                    shutil.rmtree(self.user_data_dir, ignore_errors=True)
                
                if attempt < max_retries - 1:
                    self.logger.info(f"等待 2 秒后重试...")
                    time.sleep(2)
                else:
                    self.logger.error(f"❌ 已达到最大重试次数，浏览器初始化失败")
                    return False
        
        return False

    def cleanup(self):
        """清理资源"""
        if self.debugging_port:
            port_manager.release_port(self.debugging_port)
        if self.user_data_dir and os.path.exists(self.user_data_dir):
            import shutil
            shutil.rmtree(self.user_data_dir, ignore_errors=True)

    def wait_for_verification(self, max_attempts=20, check_interval=3):
        """持续检测并处理Cloudflare验证页面，直到成功进入站点"""
        try:
            self.logger.info("🔍 开始循环检测 Cloudflare 验证页面...")

            for attempt in range(max_attempts):
                self.logger.info(f"第 {attempt + 1}/{max_attempts} 次检测验证页面...")
                time.sleep(check_interval)

                page_source = self.tab.html.lower()
                page_title = self.tab.title.lower()
                
                # if 'cloudflare' not in page_source and 'checking' not in page_title and
                if  'just a moment' not in page_title and '请稍候' not in page_title:
                    try:
                        body_text = self.tab('tag:body').text
                        if body_text and len(body_text) > 50:
                            self.logger.info("✅ 已成功进入站点，无需验证或验证已完成！")
                            return True
                    except:
                        pass

                # iframe_selectors = [
                #     "iframe[src*='cloudflare']",
                #     "iframe[title*='cloudflare']",
                #     "iframe[id*='cf']",
                #     "iframe[title='Widget containing a Cloudflare security challenge']",
                #     "iframe[src*='challenges.cloudflare.com']"
                # ]

                # iframe_found = False
                # for selector in iframe_selectors: 
                #     try:
                #         iframes = self.tab.eles(selector)
                #         if iframes:
                #             iframe = iframes[0]
                #             self.logger.info(f"🎯 找到 Cloudflare iframe: {selector}")
                #             iframe_found = True

                #             self.tab.get_frame(iframe)
                #             self.logger.info("✓ 已切换到 Cloudflare iframe")

                #             checkbox_selectors = [
                #                 "input[type='checkbox']",
                #                 "label.ctp-checkbox-label",
                #                 ".cb-lb",
                #                 ".mark",
                #                 "#challenge-stage input",
                #                 "[role='checkbox']"
                #             ]

                #             clicked = False
                #             for cb_selector in checkbox_selectors:
                #                 try:
                #                     checkbox = self.tab.ele(cb_selector, timeout=2)
                #                     if checkbox:
                #                         checkbox.click()
                #                         self.logger.info(f"✅ 已点击 Cloudflare 验证框！(选择器: {cb_selector})")
                #                         clicked = True
                #                         time.sleep(2)
                #                         break
                #                 except:
                #                     continue

                #             if not clicked:
                #                 self.logger.warning("⚠️ 未能点击验证框，尝试其他方法...")

                #             self.tab.back()

                #             self.logger.info("⏳ 等待 Cloudflare 验证处理中...")
                #             time.sleep(3)
                #             break
                #     except Exception as e:
                #         continue

                # if not iframe_found:
                    # try:
                    #     if 'cloudflare' in page_source or 'checking your browser' in page_source or 'just a moment' in page_source or '请稍候' in page_source:
                    #         self.logger.info("⏳ 检测到 Cloudflare 验证页面（非 iframe 形式），等待自动通过...")
                    #         time.sleep(3)
                    #         continue
                    #     else:
                    #         self.logger.info("✅ 未检测到验证页面，已进入正常页面")
                    #         return True
                    # except:
                    #     pass

            self.logger.info(f"完成 {max_attempts} 次验证检测")
            return True

        except Exception as e:
            self.logger.warning(f"验证处理异常: {e}")
            return True

    def safe_click_checkbox(self):
        """安全地点击checkbox，确保真正生效"""
        try:
            self.logger.info("开始安全点击checkbox...")
            
            try:
                checkbox_input = self.tab.ele("tag:input@@class=custom-control-input@@type=checkbox", timeout=5)
                
                if checkbox_input:
                    self.tab.run_js("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", checkbox_input)
                    time.sleep(1)
                    
                    self.tab.run_js("""
                        arguments[0].checked = true;
                        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                        arguments[0].dispatchEvent(new Event('click', { bubbles: true }));
                    """, checkbox_input)
                    time.sleep(0.5)
                    
                    # if checkbox_input.attr('checked'):
                    #     self.logger.info(f"✅ checkbox已勾选")
                    return True
                        
            except Exception as e:
                self.logger.warning(f"方法1失败: {e}")

            try:
                label = self.tab.ele("label=custom-control-label", timeout=3)
                
                if label:
                    self.tab.run_js("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", label)
                    time.sleep(1)
                    
                    label.click()
                    time.sleep(0.5)
                    
                    try:
                        checkbox_input = self.tab.ele("input.custom-control-input[type='checkbox']", timeout=2)
                        if checkbox_input and checkbox_input.attr('checked'):
                            self.logger.info("✅ 方法2成功：通过点击label勾选了checkbox")
                        return True
                    except:
                        pass
                        
            except Exception as e:
                self.logger.warning(f"方法2失败: {e}")

            try:
                checkboxes = self.tab.eles("input[type='checkbox'].custom-control-input")
                if checkboxes:
                    for idx, cb in enumerate(checkboxes):
                        try:
                            self.tab.run_js("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", cb)
                            time.sleep(0.5)
                            
                            cb.click()
                            time.sleep(0.5)
                            
                            if cb.attr('checked'):
                                self.logger.info(f"✅ 方法3成功：已勾选第 {idx+1} 个checkbox")
                            return True
                        except:
                            continue
            except Exception as e:
                self.logger.warning(f"方法3失败: {e}")

            self.logger.error("❌ 所有方法都未能成功勾选checkbox")
            return False
            
        except Exception as e:
            self.logger.error(f"安全点击checkbox过程出现异常: {e}")
            return False

    def login(self):
        """执行登录流程 - 使用指定的登录页面"""
        while True:
            try:
                self.logger.info("开始登录流程...")

                self.tab.get(LOGIN_URL)
                self.wait_for_verification()
                time.sleep(1)
                try:
                    # cookies按钮 class="affirm btn cookie-btn"，文案"明白!"
                    # 先等弹窗真正显示(#consent-tracking 出现 show 类)，避免命中未显示的按钮导致点击失败
                    modal = self.tab.ele("css:#consent-tracking.show", timeout=8)
                    cookies_btn = None
                    if modal:
                        cookies_btn = modal.ele("css:button.cookie-btn", timeout=2) \
                            or modal.ele("css:button[data-dismiss='modal']", timeout=1)
                    if not cookies_btn:
                        # 兜底：按按钮文案"明白!"包含匹配
                        cookies_btn = self.tab.ele("tag:button@@text():明白", timeout=2)
                    if cookies_btn:
                        try:
                            cookies_btn.click()
                        except Exception:
                            # 常规点击被遮挡时退回 JS 点击
                            cookies_btn.click(by_js=True)
                        self.logger.info("已点击cookies弹窗关闭按钮")
                        time.sleep(1)
                        if self.tab.ele("css:#consent-tracking.show", timeout=1):
                            self.tab.run_js("var b=document.querySelector('#consent-tracking button.cookie-btn');b&&b.click();")
                            self.logger.info("cookies弹窗仍在，已用JS再次点击关闭")
                    else:
                        self.logger.info("未找到cookies弹窗关闭按钮。")
                except Exception as e:
                    self.logger.warning(f"关闭cookies弹窗异常: {e}")

                self.logger.info("查找邮箱登录切换按钮...")
                try:
                    # email_login_btn = self.tab.ele("tag:button@@class=login-email-btn", timeout=10)
                    email_login_btn = self.tab.ele("xpath://*[@id='maincontent']/div/div/div[1]/div/div[1]/div/form/button", timeout=10)
                    if email_login_btn:
                        email_login_btn.click()
                        self.logger.info("已点击邮箱登录切换按钮")
                    else:
                        self.logger.info("未找到邮箱登录切换按钮。")
                except:
                    self.logger.warning("未找到邮箱登录切换按钮，可能已经在邮箱登录页面")

                self.logger.info("等待邮箱输入框出现...")
                email_input = None
                max_wait = 60  # 最多等待60秒
                for wait_attempt in range(max_wait):
                    try:
                        email_input = self.tab.ele("tag:input@@type=email", timeout=1)
                        if email_input:
                            break
                    except:
                        pass
                    time.sleep(1)
                    if wait_attempt > 0 and wait_attempt % 10 == 0:
                        self.logger.info(f"等待邮箱输入框中... 已等待{wait_attempt}秒")

                if email_input:
                    email_input.clear()
                    email_input.input(self.username)
                    self.logger.info(f"已输入邮箱: {self.username}")
                else:
                    self.logger.error(f"等待邮箱输入框超时（{max_wait}秒）")
                    return False
                time.sleep(1)
                self.logger.info("输入密码...")
                try:
                    password_input = self.tab.ele("tag:input@@type=password", timeout=10)
                    if password_input:
                        password_input.clear()
                        password_input.input(self.password)
                        self.logger.info("已输入密码")
                except:
                    self.logger.error("未找到密码输入框")
                    return False
                time.sleep(1)
                self.logger.info("点击 checkbox...")
                if not self.safe_click_checkbox():
                    self.logger.warning("⚠️ checkbox点击失败，但继续尝试登录")

                time.sleep(1)

                self.logger.info("点击登录按钮...")
                try:
                    login_submit_btn = self.tab.ele("tag:button@@class=btn btn-block btn-primary js-action", timeout=10)
                    if login_submit_btn:
                        login_submit_btn.click()
                        self.logger.info("已点击登录提交按钮")
                except:
                    self.logger.error("未找到登录提交按钮")
                    return False
                
                time.sleep(5)
                self.wait_for_verification(max_attempts=3, check_interval=2)
                
                current_url = self.tab.url
                if "Login-Show" not in current_url:
                    self.logger.info("登录成功！")
                    return True
                else:
                    self.logger.error("登录失败")
                    return False

            except Exception as e:
                self.logger.error(f"登录失败: {e},即将重新尝试")
                return False

    def _ensure_live_tab(self):
        """确保 self.tab 指向一个存活的标签页，失效则从浏览器现有标签页中恢复"""
        def _is_alive(tab):
            if tab is None:
                return False
            try:
                _ = tab.url
                return True
            except Exception:
                return False

        # 优先复用当前 tab
        if _is_alive(self.tab):
            return self.tab
        # 其次复用手动操作的新 tab（同一浏览器，登录态共享）
        if _is_alive(self.new_tab):
            self.logger.info("原标签页已断开，切换到手动操作的新标签页继续")
            self.tab = self.new_tab
            return self.tab
        # 再从浏览器现存标签页中找一个存活的
        try:
            for tab_id in self.browser.tab_ids:
                cand = self.browser.get_tab(tab_id)
                if _is_alive(cand):
                    self.logger.info(f"原标签页已断开，复用浏览器现有标签页: {tab_id}")
                    self.tab = cand
                    return self.tab
        except Exception:
            pass
        # 都失效则新建标签页
        self.logger.info("无可用标签页，新建标签页继续")
        self.tab = self.browser.new_tab()
        return self.tab

    def navigate_to_product(self):
        """导航到商品页面"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self._ensure_live_tab()
                self.logger.info("导航到商品页面...")
                self.tab.get(TARGET_URL)
                self.tab.wait.ele_displayed("xpath=//*[@id='pdpContainer']/div[10]/div[1]/div/div/div[1]/div[1]")
                self.tab.stop_loading()  # 主动停止加载
                # time.sleep(1)
                # self.wait_for_verification(max_attempts=5, check_interval=2)
                self.detect_model_mode()
                return True
            except Exception as e:
                self.logger.warning(f"导航失败({attempt + 1}/{max_attempts}): {str(e).strip()}，2秒后重试...")
                time.sleep(2)
        self.logger.error("导航到商品页面失败，已达最大重试次数")
        return False

    def refresh_page_and_wait(self):
        """刷新页面并等待加载完成"""
        try:
            self.tab.refresh()
            time.sleep(1)

            self.logger.info("页面刷新完成")
            return True
        except Exception as e:
            self.logger.error(f"刷新页面失败: {e}")
            return False

    def safe_find_element(self, selector, timeout=10, retries=3):
        """安全地查找元素"""
        for attempt in range(retries):
            try:
                element = self.tab.ele(selector, timeout=timeout)
                return element
            except Exception as e:
                self.logger.warning(f"查找元素失败 (尝试 {attempt + 1}/{retries}): {selector}")
                if attempt < retries - 1:
                    time.sleep(0.5)
                    continue
        return None

    def detect_model_mode(self):
        """检测当前页面是 Pro 还是 Pro Max"""
        url_lower = (self.tab.url or TARGET_URL).lower()

        has_custom_select = False
        has_native_select = False
        try:
            has_custom_select = len(self.tab.eles(".select-items")) >= 2
        except Exception:
            pass
        try:
            has_native_select = bool(self.tab.eles("select.select-color"))
        except Exception:
            pass

        if has_custom_select and not has_native_select:
            self.is_pro_model = False
        elif has_native_select and not has_custom_select:
            self.is_pro_model = True
        else:
            is_promax_url = any(token in url_lower for token in ("promax", "pro_max", "pro-max", "pro max"))
            is_pro_url = ("proscol" in url_lower or "/ip17_pro" in url_lower or "ip17_pro" in url_lower)
            if is_promax_url:
                self.is_pro_model = False
            elif is_pro_url:
                self.is_pro_model = True
            else:
                self.is_pro_model = False

        if self.is_pro_model:
            self.logger.info("检测到Pro型号页面，将使用Pro专用解析方式")
        else:
            self.logger.info("检测到Pro Max型号页面，将使用Pro Max解析方式")

    def is_option_available(self, option):
        """判断 select option 是否可用"""
        text = (option.text or "").strip()
        text_lower = text.lower()
        if any(keyword in text for keyword in ("售罄", "無貨", "缺貨")):
            return False
        if "sold out" in text_lower or "out of stock" in text_lower:
            return False

        class_attr = (option.attr("class") or "").lower()
        if any(token in class_attr for token in ("disabled", "out-of-stock", "soldout", "sold-out", "unselectable")):
            return False

        disabled_attr = option.attr("disabled")
        aria_disabled = option.attr("aria-disabled")
        if disabled_attr is not None or (aria_disabled and aria_disabled.lower() == "true"):
            return False

        data_selectable = option.attr("data-selectable")
        if data_selectable and data_selectable.lower() in ("false", "0", "no"):
            return False

        data_available = option.attr("data-available")
        if data_available and data_available.lower() in ("false", "0", "no"):
            return False

        data_stock = option.attr("data-stock") or option.attr("data-qty")
        if data_stock and data_stock.isdigit() and int(data_stock) <= 0:
            return False

        return True

    def _log_verbose(self, message):
        if VERBOSE_STOCK_LOG:
            self.logger.info(message)

    def _get_select_options_data(self, selectors):
        """通过 JS 一次性读取 select options"""
        if isinstance(selectors, str):
            selectors = [selectors]

        for selector in selectors:
            try:
                data = self.tab.run_js(
                    f"""
                    const select = document.querySelector('{selector}');
                    if (!select) return null;
                    return Array.from(select.options).map(o => ({{
                        text: (o.text || '').trim(),
                        dataId: o.getAttribute('data-id') || '',
                        dataAttrValue: o.getAttribute('data-attr-value') || '',
                        className: o.className || '',
                        disabled: !!o.disabled,
                        ariaDisabled: o.getAttribute('aria-disabled') || '',
                        dataSelectable: o.getAttribute('data-selectable') || '',
                        dataAvailable: o.getAttribute('data-available') || '',
                        dataStock: o.getAttribute('data-stock') || '',
                        dataQty: o.getAttribute('data-qty') || ''
                    }}));
                    """
                )
                if data is not None:
                    return data, selector
            except Exception:
                continue

        return None, None

    def _get_custom_options_data(self, list_index):
        """通过 JS 读取自定义下拉的选项"""
        try:
            return self.tab.run_js(
                f"""
                const lists = document.querySelectorAll('.select-items');
                if (lists.length <= {list_index}) return null;
                const items = lists[{list_index}].querySelectorAll(':scope > div');
                const results = [];
                for (let i = 1; i < items.length; i++) {{
                    const v = items[i].querySelector('.value');
                    if (!v) continue;
                    results.push({{
                        text: (v.textContent || '').trim(),
                        dataAttrValue: v.getAttribute('data-attr-value') || ''
                    }});
                }}
                return results;
                """
            )
        except Exception:
            return None

    def _find_select_element(self, select_index):
        """查找原生 select 元素"""
        if select_index == 0:
            selectors = [
                "select.select-color",
                "select[data-attr='select-color']",
                "select.js-select-variant[data-index='0']"
            ]
        else:
            selectors = [
                "select.select-storage",
                "select[data-attr='select-storage']",
                "select.select-internal_storage_rom",
                "select[data-attr='select-internal_storage_rom']",
                "select.js-select-variant[data-index='1']"
            ]

        for selector in selectors:
            try:
                select_element = self.tab.ele(selector, timeout=2)
                if select_element:
                    return select_element, selector
            except Exception:
                continue

        try:
            all_selects = self.tab.eles("select.custom-select.form-control")
            if len(all_selects) > select_index:
                return all_selects[select_index], "select.custom-select.form-control"
        except Exception:
            pass

        return None, None

    def _option_matches_target(self, option, target_value):
        """判断 option 是否匹配目标值"""
        if not option:
            return False
        data_id = option.attr("data-id")
        data_attr_value = option.attr("data-attr-value")
        return data_id == target_value or data_attr_value == target_value

    def _option_data_matches_target(self, option_data, target_value):
        """判断 option data 是否匹配目标值"""
        if not option_data:
            return False
        return option_data.get("dataId") == target_value or option_data.get("dataAttrValue") == target_value

    def _is_option_available_from_data(self, option_data):
        """判断通过 JS 读取的 option 是否可用"""
        text = (option_data.get("text") or "").strip()
        text_lower = text.lower()
        if any(keyword in text for keyword in ("售罄", "無貨", "缺貨")):
            return False
        if "sold out" in text_lower or "out of stock" in text_lower:
            return False

        class_attr = (option_data.get("className") or "").lower()
        if any(token in class_attr for token in ("disabled", "out-of-stock", "soldout", "sold-out", "unselectable")):
            return False

        disabled_attr = option_data.get("disabled")
        aria_disabled = option_data.get("ariaDisabled")
        if disabled_attr or (aria_disabled and str(aria_disabled).lower() == "true"):
            return False

        data_selectable = option_data.get("dataSelectable")
        if data_selectable and str(data_selectable).lower() in ("false", "0", "no"):
            return False

        data_available = option_data.get("dataAvailable")
        if data_available and str(data_available).lower() in ("false", "0", "no"):
            return False

        data_stock = option_data.get("dataStock") or option_data.get("dataQty")
        if data_stock and str(data_stock).isdigit() and int(data_stock) <= 0:
            return False

        return True

    def check_stock_with_retry(self):
        """检查库存（单次检查，外层控制刷新与间隔）"""
        memory_available = False

        try:
            self.logger.info("🔧 强制选择目标颜色以检查内存库存...")
            if not self.select_specific_option(0, self.target_color, "颜色", ignore_stock=True):
                self.logger.warning("选择颜色失败，等待下一轮...")
                return False

            if self.is_pro_model:
                time.sleep(PRO_COLOR_TO_MEMORY_DELAY)
            else:
                time.sleep(PROMAX_COLOR_TO_MEMORY_DELAY)

            try:
                storage_selectors = [
                    "select.select-storage",
                    "select[data-attr='select-storage']",
                    "select.select-internal_storage_rom",
                    "select[data-attr='select-internal_storage_rom']",
                    "select.js-select-variant[data-index='1']",
                    "select.custom-select.form-control:nth-of-type(2)"
                ]

                storage_options_data, used_selector = self._get_select_options_data(storage_selectors)
                if storage_options_data is not None:
                    if used_selector:
                        self._log_verbose(f"🔧 找到内存select元素: {used_selector}")
                    self.logger.info("🔧 【原生select】从 select 元素读取内存选项")
                    self._log_verbose(f"🔍 【调试】从 select 中找到 {len(storage_options_data)} 个内存选项")

                    for idx, option_data in enumerate(storage_options_data):
                        option_text = (option_data.get("text") or "").strip()
                        data_id = option_data.get("dataId") or ""
                        data_attr_value = option_data.get("dataAttrValue") or ""

                        if not data_id and not data_attr_value:
                            continue

                        self._log_verbose(
                            f"🔍 【内存选项{idx}】data-id: '{data_id}' | data-attr-value: '{data_attr_value}' | 文本: '{option_text}'"
                        )

                        if self._option_data_matches_target(option_data, self.target_storage):
                            if self._is_option_available_from_data(option_data):
                                memory_available = True
                                self.logger.info(f"✅ 【内存匹配】目标内存 {option_text} 有货！")
                            else:
                                self.logger.info(f"❌ 【内存匹配】目标内存 {option_text} 已售罄或不可选，本轮无货")
                            break
                else:
                    storage_select, _ = self._find_select_element(1)

                    if storage_select:
                        storage_options = storage_select.eles("tag:option")

                        self._log_verbose(f"🔍 【调试】从 select 中找到 {len(storage_options)} 个内存选项")

                        for idx, option in enumerate(storage_options):
                            try:
                                option_text = option.text.strip()
                                data_id = option.attr("data-id") or ""
                                data_attr_value = option.attr("data-attr-value") or ""

                                if not data_id and not data_attr_value:
                                    continue

                                self._log_verbose(
                                    f"🔍 【内存选项{idx}】data-id: '{data_id}' | data-attr-value: '{data_attr_value}' | 文本: '{option_text}'"
                                )

                                if self._option_matches_target(option, self.target_storage):
                                    if self.is_option_available(option):
                                        memory_available = True
                                        self.logger.info(f"✅ 【内存匹配】目标内存 {option_text} 有货！")
                                    else:
                                        self.logger.info(f"❌ 【内存匹配】目标内存 {option_text} 已售罄或不可选，本轮无货")
                                    break
                            except Exception as e:
                                self.logger.warning(f"解析内存 option 时出错: {e}")
                                continue
                    else:
                        self.logger.info("🔧 【自定义下拉】从 select-items div 读取内存选项")
                        memory_options_data = self._get_custom_options_data(1)
                        if memory_options_data is not None:
                            self._log_verbose(f"🔍 【调试】找到 {len(memory_options_data)} 个内存选项")
                            for idx, option_data in enumerate(memory_options_data):
                                option_text = (option_data.get("text") or "").strip()
                                data_attr_value = option_data.get("dataAttrValue")

                                self._log_verbose(
                                    f"🔍 【内存选项{idx+1}】文本: '{option_text}' | data-attr-value: '{data_attr_value}'"
                                )

                                if data_attr_value == self.target_storage:
                                    if "售罄" not in option_text:
                                        memory_available = True
                                        self.logger.info(f"✅ 【内存匹配】目标内存 {option_text} 有货！")
                                    else:
                                        self.logger.info(f"❌ 【内存匹配】目标内存 {option_text} 已售罄，本轮无货")
                                    break
                        else:
                            memory_items = None
                            for attempt in range(3):
                                try:
                                    select_items_divs = self.tab.eles(".select-items")
                                    if len(select_items_divs) >= 2:
                                        memory_items = select_items_divs[1]
                                        break
                                    else:
                                        time.sleep(0.5)
                                except Exception:
                                    time.sleep(0.5)
                                    continue

                            if not memory_items:
                                self.logger.warning("无法找到内存选项，等待下一轮...")
                                return False

                            memory_option_divs = memory_items.eles("tag:div")[1:]

                            self._log_verbose(f"🔍 【调试】找到 {len(memory_option_divs)} 个内存选项")

                            for idx, option_div in enumerate(memory_option_divs):
                                try:
                                    value_span = option_div.ele(".value")
                                    option_text = value_span.text.strip()
                                    data_attr_value = value_span.attr("data-attr-value")

                                    self._log_verbose(
                                        f"🔍 【内存选项{idx+1}】文本: '{option_text}' | data-attr-value: '{data_attr_value}'"
                                    )

                                    if data_attr_value == self.target_storage:
                                        if "售罄" not in option_text:
                                            memory_available = True
                                            self.logger.info(f"✅ 【内存匹配】目标内存 {option_text} 有货！")
                                        else:
                                            self.logger.info(f"❌ 【内存匹配】目标内存 {option_text} 已售罄，本轮无货")
                                        break
                                except Exception as e:
                                    self.logger.warning(f"解析内存选项时出错: {e}")
                                    continue
            except Exception as e:
                self.logger.error(f"读取内存选项失败: {e}")
                return False

            if memory_available:
                if not self.select_specific_option(1, self.target_storage, "内存"):
                    self.logger.warning("内存选项不可选，等待下一轮...")
                    return False
                self.logger.info("✅ 目标商品有货！准备抢购！")
                return True

            self.logger.info("本轮无货，继续监控...")
            return False

        except Exception as e:
            self.logger.warning(f"检查库存异常: {e}，等待下一轮...")
            return False

    def check_stock(self):
        """检查指定颜色和内存是否有货（单次检查）"""
        return self.check_stock_with_retry()

    def is_checkout_payment_page(self):
        """判断当前是否已进入 CSL 支付阶段页面"""
        try:
            current_url = self.tab.url or ""
            if "Checkout-Begin?stage=payment" in current_url:
                return True
            return bool(self.tab.eles("#place-order"))
        except Exception:
            return False

    def enter_checkout_payment_page(self):
        """捡漏模式：每 0.5 秒重复进入支付页，直到确认已跳转成功"""
        attempt = 0

        while True:
            attempt += 1
            try:
                self.tab.get(CHECKOUT_URL)
                time.sleep(1)

                if self.is_checkout_payment_page():
                    self.logger.info("✅ 已进入支付页面，开始点击提交按钮")
                    return True

                self.logger.info(
                    f"捡漏模式第 {attempt} 轮：尚未进入支付页面，{CSL_SCAVENGE_INTERVAL} 秒后重试"
                )
            except Exception as e:
                self.logger.warning(f"捡漏模式第 {attempt} 轮进入支付页面失败: {e}")

            time.sleep(CSL_SCAVENGE_INTERVAL)

    def select_specific_option(self, select_index, target_value, option_name, ignore_stock=False):
        """
        选择指定的选项
        select_index: 0 表示颜色，1 表示内存
        target_value: 目标选项的data-attr-value或 data-id
        option_name: 选项名称（用于日志）
        ignore_stock: True 时忽略售罄标记，强制选择
        """
        try:
            select_element, used_selector = self._find_select_element(select_index)
            if select_element:
                mode_label = "Pro模式" if self.is_pro_model else "原生select"
                if used_selector:
                    self._log_verbose(f"🔧 找到{option_name}select元素: {used_selector}")
                self.logger.info(f"🔧 【{mode_label}】使用 select 元素选择{option_name}")
                try:
                    options = select_element.eles("tag:option")
                    target_option = None
                    option_text = ""
                    for option in options:
                        if self._option_matches_target(option, target_value):
                            target_option = option
                            option_text = option.text.strip()
                            self.logger.info(f"找到目标{option_name}: {option_text}")

                            if not self.is_option_available(option):
                                if ignore_stock:
                                    self.logger.warning(
                                        f"⚠️ 目标{option_name} {option_text} 标记售罄，仍强制选择以刷新库存"
                                    )
                                else:
                                    self.logger.error(f"❌ 目标{option_name} {option_text} 已售罄或不可选！")
                                    return False
                            break

                    if target_option:
                        self.tab.run_js("""
                            arguments[0].selected = true;
                            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                        """, target_option)
                        self.logger.info(f"✅ 已选择目标{option_name}")
                        time.sleep(FAST_ACTION_DELAY)
                        return True
                    else:
                        self.logger.warning(f"⚠️ 未在 select 中找到目标{option_name}（value={target_value}），尝试自定义下拉")

                except Exception as e:
                    self.logger.error(f"select 模式选择{option_name}失败: {e}")
                    import traceback
                    self.logger.error(traceback.format_exc())

            for attempt in range(3):
                try:
                    select_selected_divs = self.tab.eles(".select-selected")

                    if len(select_selected_divs) <= select_index:
                        self.logger.error(f"未找到第 {select_index + 1} 个选择器")
                        if attempt < 2:
                            time.sleep(FAST_RETRY_DELAY)
                            continue
                        return False

                    select_button = select_selected_divs[select_index]

                    self.tab.run_js("""
                        arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                    """, select_button)
                    time.sleep(FAST_SCROLL_DELAY)

                    try:
                        select_button.click()
                        self.logger.info(f"已点击第 {select_index + 1} 个下拉选择器")
                    except Exception as e:
                        self.logger.warning(f"点击失败: {e}")

                    time.sleep(FAST_SELECT_OPEN_DELAY)

                    select_items_divs = self.tab.eles(".select-items")

                    if len(select_items_divs) <= select_index:
                        self.logger.error(f"未找到第 {select_index + 1} 个下拉列表")
                        if attempt < 2:
                            time.sleep(FAST_RETRY_DELAY)
                            continue
                        return False

                    items_div = select_items_divs[select_index]

                    time.sleep(FAST_SELECT_OPEN_DELAY)

                    option_divs = items_div.eles("tag:div")[1:]

                    target_option = None
                    for option_div in option_divs:
                        try:
                            value_span = option_div.ele(".value")
                            option_text = value_span.text.strip()
                            data_attr_value = value_span.attr("data-attr-value")

                            is_match = False
                            if self.is_pro_model:
                                name_map = {}
                                if select_index == 0:
                                    name_map = {
                                        "927": "銀色",
                                        "31033": "宇宙橙色",
                                        "31034": "深墨藍色"
                                    }
                                else:
                                    name_map = {
                                        "1025": "256GB",
                                        "1026": "512GB",
                                        "1027": "1TB",
                                        "4697": "2TB"
                                    }

                                if target_value in name_map:
                                    target_name = name_map[target_value]
                                    if target_name in option_text:
                                        is_match = True
                                        self.logger.info(f"🔧 【Pro模式选择】通过名称匹配: {target_name}")

                                if not is_match:
                                    is_match = (data_attr_value == target_value)
                            else:
                                is_match = (data_attr_value == target_value)

                            if is_match:
                                if "售罄" in option_text:
                                    if ignore_stock:
                                        self.logger.warning(f"⚠️ 目标{option_name} {option_text} 标记售罄，仍强制选择以刷新库存")
                                    else:
                                        self.logger.error(f"❌ 目标{option_name} {option_text} 已售罄！")
                                        return False
                                target_option = option_div
                                self.logger.info(f"找到目标{option_name}: {option_text}")
                                break
                        except Exception as e:
                            continue

                    if not target_option:
                        self.logger.error(f"❌ 未找到目标{option_name}（value={target_value}）")
                        if attempt < 2:
                            time.sleep(FAST_RETRY_DELAY)
                            continue
                        return False

                    try:
                        target_option.click()
                        self.logger.info(f"✅ 已选择目标{option_name}")
                    except Exception as e:
                        self.logger.warning(f"点击选项失败: {e}")

                    time.sleep(FAST_SELECT_APPLY_DELAY)

                    return True

                except Exception as e:
                    self.logger.error(f"选择{option_name}时出错 (尝试 {attempt + 1}/3): {e}")
                    if attempt < 2:
                        time.sleep(FAST_RETRY_DELAY)
                        continue
                    else:
                        return False

        except Exception as e:
            self.logger.error(f"选择{option_name}时发生严重错误: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def add_cart_ok(self):
        """如果添加购物车成功就返回True否则返回False"""
        self.logger.info("开始检测是否添加购物车成功")
        try:
            minicart_quantity = self.tab.ele("span.minicart-quantity", timeout=5)
            if minicart_quantity:
                quantity_text = minicart_quantity.text.strip()
                if quantity_text.isdigit() and int(quantity_text) > 0:
                    self.logger.info(f"✅ 购物车已添加 {quantity_text} 件商品")
                    return True
            self.logger.warning("⚠️ 购物车商品数量异常或为空")
            return False
        except Exception as e:
            self.logger.error(f"检测购物车商品数量失败: {e}")
            return False

    def add_to_cart_and_checkout(self):
        """选择指定颜色和容量，然后加入购物车并跳转到结算页面"""
        try:
            self.logger.info("步骤5: 点击加入购物车...")
            base_add_cart_res = base_add_cart(self.tab, self.goods_choice, self.target_color, self.target_storage)
            if 200 != base_add_cart_res:
                self.logger.error(f"❌ 加入购物车失败: {base_add_cart_res}")
                if base_add_cart_res == 429:
                    self.logger.warning("⚠️ 加入购物车失败，可能是因为请求频率过高,开始休息20分钟后重试")
                    time.sleep(1200)
                return False
            self.logger.info("✅ 成功加入购物车...")
            
            self.logger.info("步骤6: 跳转到结账页面...")
            try:
                self.tab.get(CHECKOUT_URL)
                self.logger.info(f"✅ 已跳转到结账页面: {CHECKOUT_URL}")
                time.sleep(FAST_POST_CLICK_DELAY)

                if self.complete_checkout():
                    self.logger.info("🎉 抢购成功！已进入支付页面！")
                    return True
                else:
                    self.logger.warning("⚠️ 结账流程未完成，但已加入购物车")
                    return True

            except Exception as e:
                self.logger.error(f"❌ 跳转到结账页面失败: {e}")
                try:
                    self.tab.get("https://eshop.hkcsl.com/zh_HK/cart")
                    self.logger.info("✅ 已跳转到购物车页面（备用方案）")
                    return True
                except:
                    return False

        except Exception as e:
            self.logger.error(f"❌ 加入购物车/结算失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def complete_checkout(self):
        """完成结账流程"""
        try:
            wait_timeout = 3 if self.scavenge_mode else 15

            self.logger.info(f"当前页面 URL: {self.tab.url}")

            self.logger.info("结账步骤1: 选择支付方式....")
            visa_payment = self.tab.ele("xpath://*[@id='checkout-main']/div[1]/div[1]/form/div/div[3]/div[2]/div[1]")
            if visa_payment:
                visa_payment.click()
                self.logger.info("✅ 已选择 Visa支付方式")
            else:
                self.logger.error("❌ 未找到 Visa支付方式元素")
                return False
            # try:
            #     payment_selectors = [
            #         ".card-payment-id",
            #         "div.payment-methods-item.card-payment-id",
            #         "div.payment-methods-item.card-payment-id.selected",
            #         "input#CARD",
            #         "input[value='CARD']",
            #         "label[for='CARD']"
            #     ]
                
            #     payment_method = None
            #     for selector in payment_selectors:
            #         try:
            #             payment_method = self.tab.ele(selector, timeout=5)
            #             if payment_method:
            #                 self.logger.info(f"找到支付方式元素: {selector}")
            #                 break
            #         except:
            #             continue
                
            #     if payment_method is None:
            #         self.logger.warning("未找到支付方式元素，检查页面是否正确...")
            #         self.logger.info(f"页面标题: {self.tab.title}")
            #         self.logger.info(f"页面url: {self.tab.url}")
            #         return False
                
            #     self.tab.run_js("arguments[0].scrollIntoView({block: 'center'});", payment_method)
            #     time.sleep(FAST_ACTION_DELAY)

            #     parent_div = payment_method.parent()
            #     class_attr = parent_div.attr("class") or ""
                
            #     if "selected" in class_attr:
            #         self.logger.info("✅ 支付方式已选中，跳过点击")
            #     else:
            #         payment_method.click()
            #         self.logger.info("✅ 已选择支付方式，等待页面更新...")
            #         time.sleep(FAST_POST_CLICK_DELAY)
                    
            # except Exception as e:
            #     self.logger.error(f"❌ 选择支付方式失败: {e}")
            #     return False
            # time.sleep(1)2222
            self.tab.wait.ele_displayed("tag:div@@class=veil")
            self.tab.wait.ele_deleted("tag:div@@class=veil")

            self.logger.info("结账步骤2: 勾选条款确认...")
            ok_checkbox = self.tab.ele("xpath://*[@id='checkout-main']/div[1]/div[2]/div[1]/div[2]/div[2]/form/div[1]/div[1]/label/div/p")
            if ok_checkbox:
                ok_checkbox.click()
                self.logger.info("✅ 已勾选条款确认")
            else:
                self.logger.error("❌ 未找到条款确认元素")
                return False
            time.sleep(0.1)
            # try:
            #     agree_terms_checkbox = self.tab.ele("#agreeterms", timeout=wait_timeout)

            #     self.tab.run_js("arguments[0].scrollIntoView({block: 'center'});", agree_terms_checkbox)
            #     time.sleep(FAST_ACTION_DELAY)

            #     if not agree_terms_checkbox.attr('checked'):
            #         agree_terms_checkbox.click()
            #         self.logger.info("✅ 已勾选条款确认")
            #     else:
            #         self.logger.info("✅ 条款确认已经勾选")

            #     time.sleep(FAST_ACTION_DELAY)
            # except Exception as e:
            #     self.logger.warning(f"⚠️ 勾选条款确认失败: {e}")

            self.logger.info("结账步骤3: 点击提交订单按钮...")
            submit_button = self.tab.ele("xpath://*[@id='place-order']")
            if submit_button:
                submit_button.click()
                self.logger.info("✅ 已点击提交订单按钮！进入支付页面...")
            else:
                self.logger.error("❌ 未找到提交订单按钮元素")
                return False
            # try:
            #     place_order_button = self.tab.ele("#place-order", timeout=wait_timeout)

            #     if place_order_button:
            #         place_order_button.click()
            #         self.logger.info("✅ 已点击提交订单按钮！进入支付页面...")
            #         time.sleep(FAST_POST_CLICK_DELAY)
            #         return True
            #     else:
            #         self.logger.warning("⚠️ 提交订单按钮不可点击")
            #         return False

            # except Exception as e:
            #     self.logger.error(f"❌ 点击提交订单按钮失败: {e}")
            #     return False

        except Exception as e:
            self.logger.error(f"❌ 完成结账流程失败: {e}")
            return False

    def run_scavenge_mode(self):
        """CSL 捡漏模式：跳过库存检查，直接反复进入支付页并提交订单"""
        self.logger.info(
            f"已开启 CSL 捡漏模式：跳过库存检查，每 {CSL_SCAVENGE_INTERVAL} 秒轮询支付页面"
        )

        while True:
            self.enter_checkout_payment_page()

            if self.complete_checkout():
                self.logger.info("🎉 捡漏成功！请手动完成后续支付流程。")
                ok_content = {"mode": "scavenge", "goods": goods_options.get(self.goods_choice, {}).get("name", "unknown")}
                report_order_success(ok_content)
                play_success_sound('y1871.wav', repeat=3)
                # ok_content转换为字符串
                ok_content_str = json.dumps(ok_content, ensure_ascii=False, indent=2)
                # 发送订购成功邮件通知
                send_email("抢购成功通知", ok_content_str)
                self.logger.info("浏览器将保持打开状态，按 Ctrl+C 终止程序...")
                while True:
                    time.sleep(1)

            self.logger.warning(
                f"⚠️ 本轮提交失败，{CSL_SCAVENGE_INTERVAL} 秒后重新进入支付页面继续尝试..."
            )
            time.sleep(CSL_SCAVENGE_INTERVAL)
            
    def is_cart_page(self):
        """判断当前是否已进入 CSL 购物车页面"""
        try:
            current_url = self.tab.url or ""
            if "cart" in current_url:
                return True
            return False
        except Exception:
            return False
            
    def enter_cart_page(self):
        """捡漏模式：每 0.5 秒重复进入购物车页面，直到确认已跳转成功"""
        attempt = 0

        while True:
            attempt += 1
            try:
                self.tab.get(CART_URL)

                if self.is_cart_page():
                    self.logger.info("✅ 已进入购物车页面，开始点击提交按钮")
                    return True

                self.logger.info(
                    f"捡漏模式第 {attempt} 轮：尚未进入购物车页面，{CSL_SCAVENGE_INTERVAL} 秒后重试"
                )
            except Exception as e:
                self.logger.warning(f"捡漏模式第 {attempt} 轮进入购物车页面失败: {e}")

            time.sleep(CSL_SCAVENGE_INTERVAL)
            
    def run_scavenge_mode2(self):
        """CSL 捡漏模式：跳过库存检查，直接反复进入购物车页面并提交订单"""
        self.logger.info(
            f"已开启 CSL 捡漏模式：跳过库存检查，每 {CSL_SCAVENGE_INTERVAL} 秒轮询购物车页面"
        )

        while True:
            self.enter_cart_page()
            if "售罄" in self.tab.html:
                self.logger.info("商品已售罄，无法购买")
                continue
            else:
                self.run_scavenge_mode()
            time.sleep(CSL_SCAVENGE_INTERVAL)
    
    def add_cart_use_js(self):
        #<button class="add-to-cart btn btn-primary btn-block" data-gtmdata="{&quot;id&quot;:&quot;IP17scol&quot;,&quot;name&quot;:&quot;Apple iPhone 17 512GB 薰衣草紫色&quot;,&quot;category&quot;:&quot;🍎Apple&quot;,&quot;categoryID&quot;:&quot;apple&quot;,&quot;price&quot;:&quot;8249.00&quot;}" data-gtmga4data="{&quot;item_id&quot;:&quot;IP17scol&quot;,&quot;item_name&quot;:&quot;iPhone 17&quot;,&quot;item_brand&quot;:&quot;APPLE&quot;,&quot;item_variant&quot;:&quot;4030211scol&quot;,&quot;affiliation&quot;:&quot;hkt-hk&quot;,&quot;item_category&quot;:&quot;🍎Apple&quot;,&quot;item_category2&quot;:&quot;&quot;,&quot;item_category3&quot;:&quot;&quot;,&quot;item_category4&quot;:&quot;&quot;,&quot;item_category5&quot;:&quot;&quot;,&quot;discount&quot;:&quot;350&quot;,&quot;price&quot;:&quot;8249.00&quot;,&quot;currency&quot;:&quot;HKD&quot;,&quot;location_id&quot;:&quot;productvariation&quot;}" data-pid="IP17scol" data-error-message="message.error.insufficient">
        #     <span class="icon icon-add-to-cart"></span>
        #     添加至購物車
        # </button>
        try:
            add_cart_button = self.tab.ele("tag:button@@class=add-to-cart btn btn-primary btn-block")
            if add_cart_button:
                self.logger.info("✅ 找到加入购物车按钮")
                self.tab.run_js("arguments[0].click();", add_cart_button)
                self.logger.info("✅ 已使用JS点击加入购物车按钮")
                return True
            else:
                self.logger.error("❌ 未找到加入购物车按钮")
                return False
        except Exception as e:
            self.logger.error(f"❌ 使用JS点击加入购物车按钮失败: {e}")
            return False
    def _get_checkbox_checked(self, checkbox_ele):
        """读取勾选框是否选中：以 input 的 DOM checked 属性为准（与红/黑字体颜色无关）"""
        # 优先 JS 读取实时 checked 属性，最可靠
        try:
            cb_id = checkbox_ele.attr('id')
            if cb_id:
                val = self.tab.run_js(f"return document.getElementById('{cb_id}').checked;")
                if val is not None:
                    return bool(val)
        except Exception:
            pass
        # 兜底：DrissionPage states
        try:
            return bool(checkbox_ele.states.is_checked)
        except Exception:
            try:
                return bool(checkbox_ele.states.is_selected)
            except Exception:
                return False

    def _ensure_agreement_checked(self, label_selectors, name):
        """确保协议勾选框处于选中状态：
        - 已选中：不动，直接返回（重复点击label会取消选中）
        - 未选中：点击label勾选，无效则JS点击input，最终校验checked"""
        label = None
        for sel in label_selectors:
            label = self.tab.ele(sel, timeout=3)
            if label:
                break
        if not label:
            self.logger.error(f"❌ 未找到{name}")
            return False
        # 通过 label 的 for 属性定位对应 checkbox
        checkbox = None
        for_id = label.attr('for')
        if for_id:
            checkbox = self.tab.ele(f"css:input#{for_id}", timeout=3)
        # 已选中则保持不动
        if checkbox is not None and self._get_checkbox_checked(checkbox):
            self.logger.info(f"✅ {name}已选中，保持不动")
            return True
        # 未选中 → 点击 label 勾选
        try:
            label.click()
        except Exception:
            label.click(by_js=True)
        time.sleep(0.5)
        if checkbox is not None and self._get_checkbox_checked(checkbox):
            self.logger.info(f"✅ {name}已选中")
            return True
        # label 点击无效 → JS 直接点击 input 本身
        if checkbox is not None:
            try:
                cb_id = checkbox.attr('id')
                if cb_id:
                    self.tab.run_js(f"var c=document.getElementById('{cb_id}');if(c&&!c.checked)c.click();")
                    time.sleep(0.5)
                    if self._get_checkbox_checked(checkbox):
                        self.logger.info(f"✅ {name}已选中(JS点击)")
                        return True
            except Exception:
                pass
            self.logger.error(f"❌ {name}未能选中")
            return False
        # 找不到 checkbox 时无法校验，点击 label 后乐观返回
        self.logger.warning(f"⚠️ {name}未定位到勾选框，已点击label，未校验状态")
        return True

    def add_to_cart_via_api(self, quantity=2):
        """
        有货后通过站内 AJAX 接口直接加购物车（跳过页面选择颜色/内存/勾选协议，省 3-5 秒）。
        流程：GET Product-Variation(颜色+内存) 拿 variant pid → POST Cart-AddProduct。
        返回: "ok" 成功 / "fail" 失败 / "cf_blocked" 被Cloudflare拦截
        """
        try:
            from csl_test import check_stock_selenium as css
            from urllib.parse import urlparse, parse_qs
            base_url = css.LAST_VARIATION_URL
            if not base_url:
                self.logger.warning("⚠️ 监控尚未捕获到 variation 请求URL，无法使用API加购")
                return "fail"
            qs = parse_qs(urlparse(base_url).query)
            master_pid = (qs.get("pid") or [None])[0]
            if not master_pid:
                self.logger.warning("⚠️ 无法从监控URL解析pid")
                return "fail"
            # 在监控捕获的颜色查询URL基础上追加内存参数，得到具体 variant（如 4030211scol）
            var_url = f"{base_url}&dwvar_{master_pid}_internal_storage_rom={self.target_storage}"
            add_url = "/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Cart-AddProduct"
            js = """
return (async (varUrl, addUrl, qty) => {
  try {
    const r1 = await fetch(varUrl, {headers: {'X-Requested-With': 'XMLHttpRequest'}});
    if (r1.status !== 200) return {step: 'variation', status: r1.status};
    const d1 = await r1.json();
    const pid = d1.product && d1.product.id;
    const available = d1.product && d1.product.available;
    if (!pid) return {step: 'variation', status: 200, error: 'no pid in response'};
    if (available === false) return {step: 'variation', status: 200, pid: pid, available: false};
    const r2 = await fetch(addUrl, {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest'},
      body: 'pid=' + encodeURIComponent(pid) + '&quantity=' + qty + '&options=[]',
      credentials: 'same-origin'
    });
    const txt = await r2.text();
    let j = null;
    try { j = JSON.parse(txt); } catch (e) {}
    if (r2.status !== 200 || !j) {
      return {step: 'add', status: r2.status, pid: pid, head: txt.slice(0, 150)};
    }
    // 明确失败
    if (j.error) return {step: 'add', status: 200, pid: pid, jsonError: JSON.stringify(j).slice(0, 200)};
    // 明确成功
    if (j.success === true || 'quantityTotal' in j || 'cart' in j) {
      return {step: 'add', status: 200, pid: pid, confirmed: true};
    }
    // 响应结构不明确：拉取购物车页面确认 variant 是否在其中
    const rc = await fetch('/zh_HK/cart', {credentials: 'same-origin'});
    const cartHtml = await rc.text();
    return {step: 'add', status: 200, pid: pid, confirmed: cartHtml.includes(pid)};
  } catch (e) {
    return {step: 'exception', error: String(e)};
  }
})(arguments[0], arguments[1], arguments[2])
"""
            result = self.tab.run_js(js, var_url, add_url, quantity)
            self.logger.info(f"API加购响应: {json.dumps(result, ensure_ascii=False)[:300]}")
            if not isinstance(result, dict):
                return "fail"
            status = result.get("status")
            head = result.get("head") or ""
            if status == 429 or "<!DOCTYPE" in head or "Just a moment" in head:
                return "cf_blocked"
            if result.get("step") == "add" and status == 200:
                if result.get("confirmed"):
                    self.logger.info(f"✅ API加购成功: variant={result.get('pid')}, 数量={quantity}")
                    return "ok"
                if result.get("jsonError"):
                    self.logger.warning(f"⚠️ API加购返回错误: {result['jsonError']}")
                else:
                    self.logger.warning("⚠️ API加购后购物车未确认到商品")
                return "fail"
            self.logger.warning(f"⚠️ API加购未成功: step={result.get('step')}, status={status}")
            return "fail"
        except Exception as e:
            self.logger.warning(f"⚠️ API加购异常: {e}")
            return "fail"

    def _submit_order_on_checkout_tab(self):
        """在预结账 tab 上点击提交订单按钮"""
        self.logger.info("结账步骤3: 点击提交订单按钮......")
        if self.new_tab is None:
            self.logger.error("❌ new_tab 为空，无法提交订单")
            return False
        submit_button = self.new_tab.ele('xpath://*[@id="place-order"]', timeout=5)
        if submit_button:
            submit_button.click()
            self.logger.info("✅ 已点击提交订单按钮！进入支付页面...")
            return True
        self.logger.error("❌ 未找到提交订单按钮元素")
        return False

    def add_to_cart_and_checkout_drissionpage(self):
        """使用 DrissionPage 直接在页面上加入购物车并提交订单"""
        # 快速通道：API 直接加购，成功后立即提交订单
        api_result = self.add_to_cart_via_api(quantity=2)
        if api_result == "ok":
            return self._submit_order_on_checkout_tab()
        elif api_result == "cf_blocked":
            self.logger.warning("⚠️ API加购被Cloudflare拦截，刷新页面后回退到页面操作")
            try:
                self.tab.refresh()
                time.sleep(3)
            except Exception:
                pass
        else:
            self.logger.warning("⚠️ API加购失败，回退到页面操作")
        # ---- 以下为原页面操作兜底流程 ----
        color_option = self.tab.ele(f"tag:option@@data-id={self.target_color}")
        if color_option:
            self.logger.info(f"✅ 找到目标颜色: {self.target_color}")
            color_option.click()
        else:
            self.logger.error(f"❌ 未找到目标颜色 ID: {self.target_color}")
            return False
        time.sleep(1)
        rom_option = self.tab.ele(f"tag:option@@data-id={self.target_storage}")
        if rom_option:
            self.logger.info(f"✅ 找到目标内存: {self.target_storage}")
            rom_option.click()
            self.logger.info("✅ 已点击目标内存")
        else:
            self.logger.error(f"❌ 未找到目标内存 ID: {self.target_storage}")
            return False
        # 两个协议勾选框：只在未选中时点击勾选，已选中保持不动（重复点击会取消选中）
        # 选中状态以 input 的 checked 属性为准，与字体颜色（未选中提交时变红）无关
        if not self._ensure_agreement_checked(
                ["css:label[for^='detail_terms_']", "tag:label@@text():本人聲明及確認購買"],
                "自用声明协议"):
            return False
        if not self._ensure_agreement_checked(
                ["css:label.js-tnc-expand[for^='tnc_edd_']", "tag:label@@text():本人了解這是預購產品"],
                "预购产品送货日期协议"):
            return False
        # # 点击增加库存按钮
        # add_count_option = self.tab.ele("t:span@@class=icon-plus")
        # if add_count_option:
        #     self.logger.info("✅ 找到增加订购数量按钮")
        #     add_count_option.click()
        #     self.logger.info("✅ 已点击增加订购数量按钮")
        # else:
        #     self.logger.error("❌ 未找到增加订购数量按钮")
        #     return False
        # if is_in_coding:
        #     input("请手动完成后续支付流程，完成后按任意键继续...")
        # 手工输入订购数量
        count_option = self.tab.ele("tag:input@@type=number@@inputmode=numeric")
        if count_option:
            self.logger.info("✅ 找到订购数量输入框")
            # count_option.input(Keys.RIGHT)
            count_option.clear()
            count_option.input("2")
            self.logger.info(f"✅ 已输入订购数量: {2}")
        else:
            self.logger.error("❌ 未找到订购数量输入框")
            return False
        # if is_in_coding:
        #     input("请手动完成后续支付流程，完成后按任意键继续...")
        # # 点击加入购物车按钮
        add_cart_option = self.tab.ele("tag:button@@class=add-to-cart btn btn-primary btn-block", timeout=0.5)
        if add_cart_option:
            self.logger.info("✅ 找到加入购物车按钮1")
            self.tab.listen.start('on/demandware.store/Sites-hkt-hk-Site/zh_HK/Cart-AddProduct')
            # add_cart_option.click()
            add_cart_option.scroll.to_see()
            add_cart_option.click()
            self.logger.info("✅ 已点击加入购物车按钮")
        else:
            self.logger.error("❌ 未找到加入购物车按钮")
            return False

        # # 使用js点击加入购物车按钮
        # if not self.add_cart_use_js():
        #     return False
        
        if is_in_coding:
            input("请手动完成后续支付流程，完成后按任意键继续...")
        # time.sleep(6)
        # # 判断是否添加购物车成功
        for packet in self.tab.listen.steps():
            status = packet.response.status
            print(status)
            if status == 200:
                self.logger.info("✅ 加入购物车成功")
                break
                # return True
            else:
                self.logger.error(f"❌ 加入购物车失败, 状态码: {status}")
                return False
        
        # while True:
        #     goods_count = self.tab.ele("xpath://*[@id='navigation']/div[4]/div[1]/div/div/div[2]/div[2]/div/div[3]/div/div[1]/a/span[2]")
        #     if goods_count:
        #         goods_count_text = goods_count.text.strip()
        #         print(goods_count_text)
        #         print(type(goods_count_text))
        #         self.logger.info(f"✅ 购物车商品数量: {goods_count_text}")
        #         if int(goods_count_text) >= 1:
        #             self.logger.info("✅ 加入购物车成功")
        #             break
        #     else:
        #         self.logger.error("❌ 未找到购物车商品数量, 重试...")
        #     time.sleep(1)
        # self.logger.info("步骤6: 跳转到结账页面...")
        return self._submit_order_on_checkout_tab()
        # try:
        #     self.tab.get(CHECKOUT_URL)
        #     self.tab.wait.ele_displayed("xpath://*[@id='checkout-main']/div[1]/div[1]/form/div/div[3]/div[2]/div[1]")
        #     # self.tab.wait.eles_loaded(["xpath://*[@id='checkout-main']/div[1]/div[1]/form/div/div[3]/div[2]/div[1]", "xpath://*[@id='maincontent']/div[1]/div[1]/h1"], any_one=True)
        #     self.tab.stop_loading()  # 主动停止加载
        #     self.logger.info(f"✅ 已跳转到结账页面: {CHECKOUT_URL}")
        #     # input("请手动完成后续支付流程，完成后按任意键继续...")
        #     # time.sleep(FAST_POST_CLICK_DELAY)

        #     if self.complete_checkout():
        #         self.logger.info("🎉 抢购成功！已进入支付页面！")
        #         return True
        #     else:
        #         self.logger.warning("⚠️ 结账流程未完成，但已加入购物车")
        #         return True

        # except Exception as e:
        #     self.logger.error(f"❌ 跳转到结账页面失败: {e}")
        #     # input("请手动完成后续支付流程，完成后按任意键继续...")
        #     try:
        #         self.tab.get("https://eshop.hkcsl.com/zh_HK/cart")
        #         self.logger.info("✅ 已跳转到购物车页面（备用方案）")
        #         return True
        #     except:
        #         return False
        return False
    def new_tab_and_add_little_goods_to_pay(self):
        goods_url = "https://eshop.hkcsl.com/zh_HK/HONOR/2474761scol.html"
        new_tab = self.browser.new_tab(goods_url)
        add_cart_button = new_tab.ele("xpath://*[@id='pdpContainer']/div[15]/div[2]/div/div/div[1]/button")
        if add_cart_button:
            add_cart_button.click()
            self.logger.info("✅ 已点击加入购物车按钮")
        else:
            self.logger.error("❌ 未找到加入购物车按钮")
            return False
        time.sleep(2)
        new_tab.get("https://eshop.hkcsl.com/zh_HK/cart")
        jz_button = new_tab.ele("xpath://*[@id='maincontent']/div[3]/div/div[2]/div[1]/div[2]/div/div[1]/a")
        if jz_button:
            jz_button.click()
            self.logger.info("✅ 已点击结账按钮")
        else:
            self.logger.error("❌ 未找到结账按钮")
            return False
        time.sleep(10)
        # 等待结账页进入支付阶段（支付按钮是后加载的，固定 sleep 可能不够）
        xyk_button = None
        for _ in range(30):
            # 优先用稳定的 id/class 选择器，旧的层级 xpath 作为兜底
            xyk_button = new_tab.ele("css:input#CARD", timeout=1) \
                or new_tab.ele("css:.payment-methods-item.card-payment-id", timeout=1) \
                or new_tab.ele("xpath://*[@id='checkout-main']/div[1]/div[1]/form/div/div[3]/div[2]/div[1]", timeout=1)
            if xyk_button:
                break
            # 还未到支付阶段则刷新等待
            if "stage=payment" not in (new_tab.url or ""):
                self.logger.info(f"等待支付页面加载中... 当前: {new_tab.url}")
            time.sleep(1)
        if xyk_button:
            xyk_button.click()
            self.logger.info("✅ 已点击信用卡支付方式按钮...")
        else:
            self.logger.error(f"❌ 未找到信用卡支付方式按钮元素，当前URL: {new_tab.url}")
            return False
        time.sleep(5)
        xy_button = new_tab.ele("xpath://*[@id='agreeterms']")
        if xy_button:
            xy_button.click()
            self.logger.info("✅ 已点击同意条款按钮...")
        else:
            self.logger.error("❌ 未找到同意条款按钮元素")
            return False
        time.sleep(2)
        return new_tab
    def run(self):
        """运行抢购流程"""
        last_refresh_time = 0
        try:
            if not self.init_driver():
                return

            # 如果使用代理，先访问CSL首页通过Cloudflare验证
            if self.proxy_str:
                self.logger.info("使用代理模式，先访问CSL首页通过Cloudflare验证...")
                self.tab.get("https://eshop.hkcsl.com/zh_HK/")
                time.sleep(5)
                # 检查是否需要通过Cloudflare
                if "just a moment" in self.tab.title.lower() or "請稍候" in self.tab.title.lower():
                    self.logger.info("等待Cloudflare验证通过...")
                    time.sleep(10)
                    # 如果仍未通过，刷新一次
                    if "just a moment" in self.tab.title.lower() or "請稍候" in self.tab.title.lower():
                        self.logger.info("刷新页面重试...")
                        self.tab.refresh()
                        time.sleep(10)
                self.logger.info(f"Cloudflare验证完成，页面标题: {self.tab.title}")

            while True:
                if self.login():
                    break
                else:
                    self.logger.error("登录失败，重试...")
                    time.sleep(2)
            # 登录页刚跳转完，等待稳定
            time.sleep(2)
            self.new_tab = self.new_tab_and_add_little_goods_to_pay()
            if not self.new_tab:
                self.logger.error("❌ 准备支付流程失败（new_tab 为空），终止运行")
                return

            # input("请手动打开新的tab，并在新tab中打开商品页面，添加到购物车，并完成选择支付方式，完成后按任意键继续...")
            # self.new_tab = self.browser.latest_tab
            print(self.new_tab.url)
            if self.scavenge_mode:
                self.run_scavenge_mode2()
                return

            if not self.navigate_to_product():
                self.logger.error("无法导航到商品页面，终止运行")
                return

            interval_label = "无间隔" if CHECK_INTERVAL <= 0 else f"{CHECK_INTERVAL}秒"
            self.logger.info(f"开始监控库存，检查间隔: {interval_label}...")
            
            
            goods = {"name": goods_options[self.goods_choice]["name"], "color": self.target_color, "rom": self.target_storage}
            check_num = 0
            while True:
                try:
                    if "zh_HK/home" in self.tab.url:
                        self.tab.get(TARGET_URL)
                        time.sleep(2)
                        continue
                    check_num += 1
                    if check_num % 10 == 0:
                        print(f"🔍 第{check_num}次开始检查库存: {goods['name']}, 颜色: {goods['color']}, 内存: {goods['rom']}")
                    # if get_check_stock(goods):
                    # time.sleep(1)
                    if check_stock_with_selenium2(self.tab, goods):
                        self.logger.info("🎉 有货了，开始加入购物车。")
                        # if self.add_to_cart_and_checkout():
                        if self.add_to_cart_and_checkout_drissionpage():
                            self.logger.info("🎉 抢购成功！请手动完成后续支付流程。")
                            try:
                                is_payment_page = False
                                for _ in range(10):
                                    if "https://onepayment.pccw.com/ecom/web/v2/pay?p=" in self.new_tab.url:
                                        is_payment_page = True
                                        break
                                    time.sleep(1)
                        
                                if is_payment_page:
                                    self.logger.info("支付页面加载完成")
                                    play_success_sound('y1871.wav', repeat=3)
                                    self.logger.info(f"当前url: {self.new_tab.url}")
                                    
                                    # 从支付页抓取总金额: <label for="amount" ...>30055.00</label>
                                    amount = "未知"
                                    try:
                                        # 页面有两个 for='amount' 的label（灰色"交易金額"标题 + 白色数值），
                                        # 金额数值的label带 text-white class，用它精确定位
                                        amount_label = self.new_tab.ele("css:label.text-white[for='amount']", timeout=5)
                                        if amount_label:
                                            amount = amount_label.text.strip()
                                    except Exception as amount_e:
                                        self.logger.warning(f"获取总金额失败: {str(amount_e).strip()}")
                                    ok_content = {
                                        "账户名": self.username,
                                        "密码": self.password,
                                        "商品类型": goods["name"],
                                        "颜色": goods["color"],
                                        "rom型号": goods["rom"],
                                        "总金额": amount,
                                    }
                                    report_order_success(ok_content)
                                    self.logger.info("开始发送通知邮件")
                                    ok_content_str = json.dumps(ok_content, ensure_ascii=False, indent=2)
                                    print(ok_content_str)
                                    # 发送订购成功邮件通知
                                    send_email(to_email='k2049@qq.com', subject="抢购成功通知", content=ok_content_str)
                                    send_email(to_email='leontang2010@gmail.com', subject="抢购成功通知", content=ok_content_str)
                                    
                                    self.logger.info("通知邮件发送完成")
                            except Exception as e:
                                self.logger.error(f"❌ 检测支付页面状态时发生异常: {e}")
                                self.logger.error(traceback.format_exc())
                        

                            self.logger.info("浏览器将保持打开状态，按 Ctrl+C 终止程序...")
                            while True:
                                time.sleep(60)
                        else:
                            self.logger.error("抢购失败，继续监控...")
                            self.tab.refresh()
                            time.sleep(FAST_RETRY_DELAY)
                    else:
                        time.sleep(1)
                        if check_num % 10 == 0:
                            self.logger.info(f"第{check_num}次当前库存不足08，继续监控...")
                        if time.time() - last_refresh_time > 8 * 60:
                            self.tab.refresh()
                            last_refresh_time = time.time()
                            self.logger.info("刷新页面")
                    if CHECK_INTERVAL > 0:
                        time.sleep(CHECK_INTERVAL)
                    else:
                        time.sleep(0)
                except Exception as loop_e:
                    err_msg = str(loop_e).strip()
                    self.logger.warning(f"监控循环出现异常(忽略继续): {err_msg}")
                    # 标签页连接断开时尝试恢复到存活标签页
                    if "disconnected" in err_msg or "refreshed" in err_msg:
                        try:
                            self._ensure_live_tab()
                        except Exception:
                            pass
                    time.sleep(2)

        except KeyboardInterrupt:
            self.logger.info("用户中断程序")
        except Exception as e:
            self.logger.error(f"运行异常: {e}", exc_info=True)
        finally:
            if self.browser:
                self.logger.info("保持浏览器打开，请手动关闭...")
            self.cleanup()


def load_accounts(filename='account.txt'):
    """从文件加载账号信息"""
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


def main():
    """主函数"""
    global TARGET_URL
    global is_in_coding

    if not verify_auth():
        input("初始化不成功，按任意键退出...")
        return

    interval_label = "0秒(无间隔)" if CHECK_INTERVAL <= 0 else f"{CHECK_INTERVAL}秒"
    print(f"""
    ╔═══════════════════════════════════════╗
    ║     多线程网站抢购助手 v2.0          ║
    ║     使用 DrissionPage 驱动           ║
    ║                                       ║
    ║  目标: 香港CSL手机抢购                ║
    ║  检查间隔: {interval_label:<23}║
    ╚═══════════════════════════════════════╝
    """)
    print("是否在测试模式：")
    print("1. 不是")
    print("2. 是")
    is_in_coding = (input("请输入 (1-2，默认1): ").strip() == "2")

    print("请选择运行模式:")
    print("1. 正常抢购模式")
    print("2. CSL捡漏模式（跳过库存检查，直接轮询支付页提交订单）")
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
        print("请选择要抢购的商品：")
        for key, value in goods_options.items():
            print(f"{key}. {value['name']}")
        goods_choice = input("请输入数字选择商品 (1-7): ").strip()
        if goods_choice not in goods_options:
            print("错误：无效的商品选择")
            return
        TARGET_URL = goods_options[goods_choice]["url"]
        color_options = IPHONE_17_COLOR_OPTIONS if goods_choice == "3" else IPHONE_17_PRO_AND_PROMAX_COLOR_OPTIONS
        if goods_choice == "6":
            color_options = IPHONE_18_PRO_MAX_COLOR_OPTIONS
        elif goods_choice == "7":
            color_options = IPHONE_18_PRO_COLOR_OPTIONS

        print("\n请选择要抢购的颜色:")
        for key, value in color_options.items():
            print(f"  {key}. {value['name']}")

        color_choice = input("请输入数字选择颜色 (1-3): ").strip()
        if color_choice not in color_options:
            print("错误：无效的颜色选择")
            return

        selected_color = color_options[color_choice]
        print(f"✓ 已选择颜色: {selected_color['name']}")

        print("\n请选择要抢购的内存空间:")
        for key, value in STORAGE_OPTIONS.items():
            print(f"  {key}. {value['name']}")

        storage_choice = input("请输入数字选择内存 (1-4): ").strip()
        if storage_choice not in STORAGE_OPTIONS:
            print("错误：无效的内存选择")
            return

        selected_storage = STORAGE_OPTIONS[storage_choice]
        print(f"✓ 已选择内存: {selected_storage['name']}")

    # ---- 是否使用代理IP ----
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
            print(f"✓ 已启用代理: {loaded_proxy.split(':')[0]}:{loaded_proxy.split(':')[1]}")
        else:
            print("✓ 已选择直连模式")
    else:
        print("\n未检测到代理配置（proxy.txt 为空或不存在），将使用直连模式")

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

    accounts = load_accounts('account.txt')
    if not accounts:
        print("错误：未能加载任何账号，请检查 account.txt 文件")
        return

    print(f"\n已加载 {len(accounts)} 个账号，准备启动...\n")

    threads = []
    bots = []

    for i, (username, password) in enumerate(accounts, 1):
        bot = RushBuyBot(
            username,
            password,
            i,
            selected_color['value'] if selected_color else None,
            selected_storage['value'] if selected_storage else None,
            scavenge_mode=scavenge_mode,
            goods_choice=goods_choice,
            proxy_str=proxy_str
        )
        bots.append(bot)
        thread = threading.Thread(
            target=bot.run,
            name=f"Bot-{i}-{username}"
        )
        threads.append(thread)

    print(f"正在启动 {len(threads)} 个抢购线程...\n")
    for thread in threads:
        thread.start()
        time.sleep(2)

    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        print("浏览器窗口将保持打开状态，请手动关闭")


if __name__ == "__main__":
    main()