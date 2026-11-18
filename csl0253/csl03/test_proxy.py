#!/usr/bin/env python3
"""
代理IP测试脚本
测试代理是否可用，以及响应速度

代理格式: IP:端口:用户名:密码

支持两种测试方式:
1. requests 库测试（纯HTTP请求）
2. DrissionPage 测试（真实浏览器）
"""

import requests
import time
import os
from DrissionPage import Chromium, ChromiumOptions

# 模拟真实浏览器的请求头
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}


def test_proxy(proxy_ip, proxy_port, proxy_user, proxy_pass, test_url="https://httpbin.org/ip", headers=None):
    """
    测试代理是否可用

    Args:
        proxy_ip: 代理IP地址
        proxy_port: 代理端口
        proxy_user: 代理用户名
        proxy_pass: 代理密码
        test_url: 测试目标URL（默认使用 httpbin.org/ip 返回请求来源IP）

    Returns:
        dict: 测试结果，包含 success, elapsed, error, response_ip 等
    """
    # 构建代理字典
    proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_ip}:{proxy_port}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }

    print(f"测试代理: {proxy_ip}:{proxy_port}")
    print(f"用户名: {proxy_user}")
    print(f"测试目标: {test_url}")
    print("-" * 50)

    result = {
        "success": False,
        "elapsed": None,
        "error": None,
        "response_ip": None,
        "proxy_ip": proxy_ip
    }

    # 合并默认请求头和自定义请求头
    request_headers = DEFAULT_HEADERS.copy()
    if headers:
        request_headers.update(headers)

    try:
        start_time = time.time()
        
        # 发送请求（设置超时时间为10秒，添加请求头）
        response = requests.get(
            test_url,
            proxies=proxies,
            headers=request_headers,
            timeout=10,
            verify=False  # 忽略SSL证书验证
        )
        
        elapsed = time.time() - start_time
        result["elapsed"] = elapsed

        if response.status_code == 200:
            result["success"] = True
            
            # 解析返回的IP信息
            try:
                data = response.json()
                result["response_ip"] = data.get("origin", "未知")
            except:
                result["response_ip"] = response.text[:100]

            print(f"✅ 代理可用！")
            print(f"响应时间: {elapsed:.2f} 秒")
            print(f"返回的IP: {result['response_ip']}")
            print(f"状态码: {response.status_code}")
        else:
            result["error"] = f"HTTP状态码: {response.status_code}"
            print(f"❌ 请求失败，状态码: {response.status_code}")

    except requests.exceptions.ProxyError as e:
        result["error"] = "代理连接失败"
        print(f"❌ 代理连接失败: {e}")
    
    except requests.exceptions.ConnectTimeout as e:
        result["error"] = "连接超时"
        print(f"❌ 连接超时: {e}")
    
    except requests.exceptions.ReadTimeout as e:
        result["error"] = "读取超时"
        print(f"❌ 读取超时: {e}")
    
    except requests.exceptions.SSLError as e:
        result["error"] = "SSL错误"
        print(f"❌ SSL错误: {e}")
    
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ 其他错误: {e}")

    return result


def test_multiple_urls(proxy_ip, proxy_port, proxy_user, proxy_pass):
    """
    使用多个URL测试代理

    Args:
        proxy_ip: 代理IP地址
        proxy_port: 代理端口
        proxy_user: 代理用户名
        proxy_pass: 代理密码
    """
    test_urls = [
        "https://httpbin.org/ip",           # 返回请求来源IP
        "https://www.google.com",           # 测试Google访问
        "https://eshop.hkcsl.com/zh_HK/",   # 测试CSL网站访问
    ]

    print("=" * 50)
    print("多URL测试")
    print("=" * 50)

    results = []
    for url in test_urls:
        print(f"\n测试URL: {url}")
        result = test_proxy(proxy_ip, proxy_port, proxy_user, proxy_pass, url)
        results.append(result)
        print()

    # 汇总结果
    print("=" * 50)
    print("测试汇总")
    print("=" * 50)
    success_count = sum(1 for r in results if r["success"])
    print(f"成功: {success_count}/{len(results)}")
    
    for i, r in enumerate(results):
        status = "✅" if r["success"] else "❌"
        elapsed = f"{r['elapsed']:.2f}s" if r["elapsed"] else "N/A"
        print(f"{status} URL{i+1}: {elapsed} - {r['error'] or '成功'}")


def create_proxy_auth_extension(proxy_user, proxy_pass):
    """
    创建 Chrome 扩展来自动处理代理认证

    Args:
        proxy_user: 代理用户名
        proxy_pass: 代理密码

    Returns:
        str: 扩展目录路径
    """
    import os
    import tempfile
    import shutil
    
    # 创建临时扩展目录
    extension_dir = os.path.join(tempfile.gettempdir(), 'proxy_auth_extension')
    
    # 如果目录已存在，先删除
    if os.path.exists(extension_dir):
        shutil.rmtree(extension_dir, ignore_errors=True)
    
    os.makedirs(extension_dir, exist_ok=True)
    
    # 创建 manifest.json (Manifest V2，对代理认证支持更好)
    manifest_content = '''{
  "version": "1.0.0",
  "manifest_version": 2,
  "name": "Proxy Auto Auth",
  "permissions": [
    "webRequest",
    "webRequestBlocking",
    "<all_urls>"
  ],
  "background": {
    "scripts": ["background.js"],
    "persistent": true
  }
}'''
    
    with open(os.path.join(extension_dir, 'manifest.json'), 'w') as f:
        f.write(manifest_content)
    
    # 创建 background.js（填入用户名密码）
    # 使用 asyncBlocking 方式，并检查 isProxy 属性
    background_content = (
        "// 代理认证凭据\n"
        "const PROXY_USER = '" + proxy_user + "';\n"
        "const PROXY_PASS = '" + proxy_pass + "';\n"
        "\n"
        "// 监听代理认证请求并自动填写\n"
        "chrome.webRequest.onAuthRequired.addListener(\n"
        "  function(details, callback) {\n"
        "    console.log('=== Auth Required ===');\n"
        "    console.log('URL:', details.url);\n"
        "    console.log('IsProxy:', details.isProxy);\n"
        "    console.log('Realm:', details.realm);\n"
        "    console.log('Challenger:', details.challenger);\n"
        "\n"
        "    // 如果是代理认证请求，自动填写凭据\n"
        "    if (details.isProxy === true) {\n"
        "      console.log('This is a proxy auth request, providing credentials...');\n"
        "      callback({\n"
        "        authCredentials: {\n"
        "          username: PROXY_USER,\n"
        "          password: PROXY_PASS\n"
        "        }\n"
        "      });\n"
        "    } else {\n"
        "      // 不是代理认证，继续正常流程\n"
        "      callback({ cancel: false });\n"
        "    }\n"
        "  },\n"
        "  { urls: ['<all_urls>'] },\n"
        "  ['asyncBlocking']\n"
        ");\n"
        "\n"
        "// 同时监听所有请求，确保扩展正在工作\n"
        "chrome.webRequest.onBeforeRequest.addListener(\n"
        "  function(details) {\n"
        "    console.log('Request to:', details.url);\n"
        "  },\n"
        "  { urls: ['<all_urls>'] }\n"
        ");\n"
        "\n"
        "console.log('=== Proxy Auto Auth Extension Loaded ===');\n"
        "console.log('Username:', PROXY_USER);\n"
        "console.log('Extension ready, monitoring all requests');\n"
    )
    
    with open(os.path.join(extension_dir, 'background.js'), 'w') as f:
        f.write(background_content)
    
    # 打印生成的 background.js 内容，确认用户名密码是否正确
    print(f"生成的 background.js 内容:")
    print("-" * 30)
    print(background_content)
    print("-" * 30)
    
    print(f"✅ 创建代理认证扩展: {extension_dir}")
    return extension_dir


def test_proxy_with_drissionpage(proxy_ip, proxy_port, proxy_user, proxy_pass, test_url="https://eshop.hkcsl.com/zh_HK/"):
    """
    使用 DrissionPage 真实浏览器测试代理
    通过本地转发代理，将用户名密码嵌入代码，无需手动输入

    原理：
    1. 启动一个本地 HTTP 代理（如 127.0.0.1:8888），不需要认证
    2. 本地代理自动将请求转发到远程代理（带用户名密码认证）
    3. 浏览器连接本地代理，不会弹出认证窗口

    Args:
        proxy_ip: 远程代理IP地址
        proxy_port: 远程代理端口
        proxy_user: 远程代理用户名
        proxy_pass: 远程代理密码
        test_url: 测试目标URL

    Returns:
        dict: 测试结果
    """
    print("=" * 50)
    print("DrissionPage 浏览器测试（本地转发代理，无需弹窗）")
    print("=" * 50)
    print(f"远程代理: {proxy_ip}:{proxy_port}")
    print(f"用户名: {proxy_user}")
    print(f"密码: {proxy_pass}")
    print(f"测试目标: {test_url}")
    print("-" * 50)

    result = {
        "success": False,
        "elapsed": None,
        "error": None,
        "page_title": None,
        "page_url": None,
        "page_content_length": None
    }

    browser = None
    
    try:
        # ====== 第1步：启动本地转发代理 ======
        import random
        import threading
        import base64
        from http.server import HTTPServer, BaseHTTPRequestHandler
        from socketserver import ThreadingMixIn
        import http.client
        import ssl
        
        local_port = random.randint(10000, 19999)
        
        # 构建 Proxy-Authorization 头
        auth_str = f"{proxy_user}:{proxy_pass}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()
        proxy_auth_header = f"Basic {auth_b64}"
        
        class LocalProxyHandler(BaseHTTPRequestHandler):
            """本地代理处理器，转发请求到远程代理"""
            
            def do_CONNECT(self):
                """处理 HTTPS 隧道请求（CONNECT 方法）"""
                try:
                    # 连接远程代理
                    remote_conn = http.client.HTTPSConnection(
                        proxy_ip, int(proxy_port), timeout=30
                    )
                    # 发送 CONNECT 请求到远程代理（带认证）
                    remote_conn.set_tunnel(
                        self.path,
                        headers={"Proxy-Authorization": proxy_auth_header}
                    )
                    # 实际上需要用 socket 方式处理 CONNECT
                    # 改用 socket 直接连接
                    remote_sock = self._connect_remote()
                    if remote_sock:
                        self.send_response(200, "Connection Established")
                        self.end_headers()
                        # 双向转发数据
                        self._tunnel(self.connection, remote_sock)
                except Exception as e:
                    self.send_error(502, str(e))
            
            def _connect_remote(self):
                """连接远程代理并建立隧道"""
                import socket
                try:
                    remote_sock = socket.create_connection((proxy_ip, int(proxy_port)), timeout=30)
                    # 发送 CONNECT 请求
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
                        print(f"远程代理拒绝连接: {response}")
                        return None
                except Exception as e:
                    print(f"连接远程代理失败: {e}")
                    return None
            
            def _tunnel(self, client_sock, remote_sock):
                """双向转发数据"""
                import select
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
                    
                    # 构建转发请求头
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
                print(f"  [代理] {args[0]}")
        
        class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
            """多线程 HTTP 服务器"""
            daemon_threads = True
        
        # 启动本地代理服务器
        server = ThreadedHTTPServer(('127.0.0.1', local_port), LocalProxyHandler)
        proxy_thread = threading.Thread(target=server.serve_forever, daemon=True)
        proxy_thread.start()
        
        print(f"✅ 本地转发代理已启动: 127.0.0.1:{local_port}")
        time.sleep(1)
        
        # ====== 第2步：启动浏览器，连接本地代理 ======
        # 参考 rush_buy.py 的浏览器配置，能通过 Cloudflare 验证
        co = ChromiumOptions()
        co.set_load_mode('none')     # 网页连接成功即停止加载，加快速度
        co.incognito(True)           # 隐身模式
        co.no_imgs(False)            # 不禁用图片
        co.headless(False)           # 非无头模式
        
        # 设置代理为本地代理（不需要认证，认证由本地代理处理）
        co.set_proxy(f"127.0.0.1:{local_port}")
        
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
        
        # 各种性能优化参数（参考 rush_buy.py）
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
        
        print(f"正在启动浏览器（代理: 127.0.0.1:{local_port}）...")
        print("✅ 无需手动输入用户名密码，本地代理会自动处理认证")
        
        browser = Chromium(co)
        tab = browser.latest_tab
        
        # ====== 第3步：访问测试网址 ======
        print(f"正在访问: {test_url}")
        
        start_time = time.time()
        tab.get(test_url, timeout=30)
        elapsed = time.time() - start_time
        result["elapsed"] = elapsed
        
        # 等待页面加载
        print("等待页面加载...")
        time.sleep(5)
        
        # 获取页面信息
        result["page_title"] = tab.title
        result["page_url"] = tab.url
        
        # 检查页面内容长度
        page_html = tab.html
        result["page_content_length"] = len(page_html)
        
        print(f"\n页面信息:")
        print(f"  响应时间: {elapsed:.2f} 秒")
        print(f"  页面标题: {tab.title}")
        print(f"  当前URL: {tab.url}")
        print(f"  页面内容长度: {len(page_html)} 字符")
        
        # 检查是否有 Cloudflare 验证
        page_html_lower = page_html.lower()
        if "cloudflare" in page_html_lower or "just a moment" in tab.title.lower():
            print("\n⚠️ 检测到 Cloudflare 验证页面，等待10秒...")
            time.sleep(10)
            
            # 如果仍然没有通过，刷新一次
            if "just a moment" in tab.title.lower():
                print("Cloudflare 验证未通过，刷新页面...")
                tab.refresh()
                time.sleep(10)
            
            result["page_title"] = tab.title
            result["page_url"] = tab.url
            page_html = tab.html
            
            if "just a moment" not in tab.title.lower():
                print(f"✅ Cloudflare 验证已通过！")
                print(f"页面标题: {tab.title}")
            else:
                print("⚠️ Cloudflare 验证仍未通过，可能需要手动点击验证框")
        
        # 判断是否成功（页面内容长度大于1000字符视为成功）
        if len(page_html) > 1000:
            result["success"] = True
            print("\n✅ 测试成功！页面加载正常")
            
            # 通过验证后，打开登录页面
            LOGIN_URL = "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Login-Show"
            print(f"\n正在打开登录页面: {LOGIN_URL}")
            tab.get(LOGIN_URL, timeout=30)
            time.sleep(3)
            print(f"页面标题: {tab.title}")
            print(f"当前URL: {tab.url}")
        else:
            print(f"\n⚠️ 页面内容较少（{len(page_html)} 字符）")
            print("请在浏览器窗口中检查页面是否正常显示")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if browser:
            print("\n浏览器窗口保持打开，可以手动检查...")
            print("关闭浏览器窗口结束程序")
    
    return result


def main():
    """主函数"""
    # 代理信息（从用户输入解析）
    proxy_str = "124.155.250.87:443:LUuteRCHxpEV:6RCyiJubJJ"
    
    # 解析代理字符串
    parts = proxy_str.split(":")
    if len(parts) != 4:
        print("代理格式错误，应为: IP:端口:用户名:密码")
        return
    
    proxy_ip = parts[0]
    proxy_port = parts[1]
    proxy_user = parts[2]
    proxy_pass = parts[3]

    print("请选择测试方式:")
    print("1. requests 测试（纯HTTP请求）")
    print("2. DrissionPage 测试（真实浏览器）")
    print("3. 两种方式都测试")
    choice = input("请输入 (1-3，默认3): ").strip() or "3"

    if choice == "1":
        # requests 测试
        print("=" * 50)
        print("requests 测试")
        print("=" * 50)
        test_proxy(proxy_ip, proxy_port, proxy_user, proxy_pass)
        print("\n")
        test_multiple_urls(proxy_ip, proxy_port, proxy_user, proxy_pass)
    
    elif choice == "2":
        # DrissionPage 测试
        test_proxy_with_drissionpage(proxy_ip, proxy_port, proxy_user, proxy_pass)
    
    elif choice == "3":
        # 两种方式都测试
        print("=" * 50)
        print("requests 测试")
        print("=" * 50)
        test_proxy(proxy_ip, proxy_port, proxy_user, proxy_pass)
        print("\n")
        test_multiple_urls(proxy_ip, proxy_port, proxy_user, proxy_pass)
        
        print("\n")
        test_proxy_with_drissionpage(proxy_ip, proxy_port, proxy_user, proxy_pass)
    
    else:
        print("无效选择")


if __name__ == "__main__":
    main()