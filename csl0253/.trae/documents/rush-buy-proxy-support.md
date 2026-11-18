# rush_buy.py 代理IP支持改造计划

## Context
用户需要 rush_buy.py 通过代理IP访问CSL网站完成购买。test_proxy.py 中已验证本地转发代理方案可行（无弹窗、通过Cloudflare），需要将此方案集成到 rush_buy.py 中。

代理配置从文件读取（用户选择）。

## 修改文件
- `/Users/Admin/Desktop/projects/client/leon/csl0253/csl03/rush_buy.py`（主要改造）
- `/Users/Admin/Desktop/projects/client/leon/csl0253/csl03/proxy.txt`（新建，代理配置文件）

## 改造步骤

### 步骤1：新建 proxy.txt 代理配置文件
格式：`IP:端口:用户名:密码`，一行一个代理。为空则不使用代理。
```
124.155.250.87:443:LUuteRCHxpEV:6RCyiJubJJ
```

### 步骤2：新增 load_proxy() 函数（约第290行，init_browser之前）
参考 `load_accounts()` 的模式，从 proxy.txt 读取代理配置：
- 格式: `IP:端口:用户名:密码`
- 返回 `(proxy_ip, proxy_port, proxy_user, proxy_pass)` 或 None

### 步骤3：新增 start_local_proxy() 函数（紧接 load_proxy 之后）
从 test_proxy.py 提取本地转发代理核心代码：
- `LocalProxyHandler` 类（处理 CONNECT 隧道 + HTTP 转发 + Proxy-Authorization 认证头）
- `ThreadedHTTPServer` 多线程服务器
- 启动后台 daemon 线程运行代理
- 返回本地代理端口号

### 步骤4：修改 init_browser() 函数
- 新增可选参数 `proxy_str=""`
- 如果 proxy_str 非空，解析并启动本地代理，设置 `co.set_proxy(f"127.0.0.1:{local_port}")`
- 如果 proxy_str 为空，不设置代理（保持原有行为）

### 步骤5：修改 run() 函数
- 新增可选参数 `proxy_str=""`
- 传递给 `init_browser(proxy_str)`
- 在 `init_browser()` 成功后、`login()` 之前，先访问 CSL 首页通过 Cloudflare 验证，再跳转登录页

### 步骤6：修改 main() 函数
- 步骤6（加载账号）之后，新增加载代理配置：调用 `load_proxy('proxy.txt')`
- 步骤7（启动抢购）中，将 proxy_str 传入 `run()`
- 确认配置汇总中显示代理信息

### 步骤7：新增 import
在文件顶部添加：`import base64, threading, socket, select, http.client`
- `from http.server import HTTPServer, BaseHTTPRequestHandler`
- `from socketserver import ThreadingMixIn`

## 验证方式
1. 运行 `python rush_buy.py`
2. proxy.txt 中有代理配置时，确认配置汇总显示代理信息
3. 浏览器通过代理访问CSL，通过Cloudflare，打开登录页
4. proxy.txt 为空时，保持原有行为（直连）
