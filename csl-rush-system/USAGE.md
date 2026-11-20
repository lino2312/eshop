# CSL 抢购系统使用指南

## 快速开始（3 步）

### 1. 一键部署
```bash
cd csl-rush-system
./deploy.sh
```

这会自动：
- 检查/安装 Go 环境
- 复制配置文件模板
- 打开编辑器让你填写账号
- 编译服务器和客户端

### 2. 编辑配置文件

打开 `config/config.yaml`，修改以下内容：

```yaml
# 必改：账号信息
accounts:
  - username: "your-email@example.com"    # 改成真实账号
    password: "your-password"              # 改成真实密码

# 必改：商品信息
product:
  color: "927"      # 颜色代码（见下方对照表）
  storage: "1026"   # 内存代码（见下方对照表）
```

**颜色代码对照表**：
- `927` = 银色
- `31033` = 宇宙橙色
- `31034` = 深墨蓝色

**内存代码对照表**：
- `1025` = 256GB
- `1026` = 512GB
- `1027` = 1TB
- `4697` = 2TB

### 3. 启动系统
```bash
./run.sh
```

选择 **选项 3**（全部启动），系统会：
1. 启动监控服务器（开始轮询库存）
2. 为每个账号启动一个客户端
3. 客户端自动登录（会看到浏览器窗口）
4. 登录完成后待命，等待库存通知

## 工作流程

```
[监控服务器] 每 0.5 秒检查库存
        ↓
    发现有货！
        ↓
   WebSocket 广播
        ↓
[所有客户端] 同时收到通知（<10ms）
        ↓
  用 Cookie 直接调用加购 API
        ↓
    自动跳转支付页面
```

## 高级用法

### 分离运行（推荐用于多机器）

**机器 A（服务器）**：
```bash
./bin/server
# 监听 0.0.0.0:8080
```

**机器 B、C、D（客户端）**：
```bash
# 修改 config/config.yaml 中的 server_url
client:
  server_url: "ws://机器A的IP:8080/ws"

# 启动客户端
./bin/client -account 0  # 使用第 1 个账号
./bin/client -account 1  # 使用第 2 个账号
```

### 配置文件参数说明

```yaml
server:
  port: 8080                # WebSocket 服务端口
  check_interval_ms: 500    # 库存检查间隔（毫秒）

client:
  server_url: "ws://localhost:8080/ws"
  headless: false           # true=无头浏览器（看不到窗口）
  purchase_quantity: 2      # 购买数量
```

### 无头模式（服务器部署）

如果在无界面服务器上运行，修改 `config/config.yaml`：

```yaml
client:
  headless: true
```

需要安装 Xvfb（虚拟显示）：
```bash
# Ubuntu/Debian
sudo apt-get install xvfb

# 启动客户端
xvfb-run ./bin/client
```

## 日志查看

**服务器日志**：
```
Monitor server started on :8080
Monitoring: iPhone 17 Pro Max (Color: 927, Storage: 1026)
Stock available! iPhone 17 Pro Max 927 1026  # 发现库存
```

**客户端日志**：
```
Starting login with chromedp...
Login successful for account@example.com, cookies extracted
Connected to monitor server
Client ready, waiting for stock alerts...
Stock alert received! Starting purchase...      # 收到通知
Successfully added to cart: IP17scol            # 加购成功
Successfully navigated to checkout page         # 进入支付页
```

## 常见问题

### Q: 客户端一直卡在登录页面？
A: 手动完成 Cloudflare 验证，程序会继续。或者检查账号密码是否正确。

### Q: 提示 "WebSocket connection failed"？
A: 确认监控服务器已启动，且 `server_url` 配置正确。

### Q: 加购失败提示 "status 429"？
A: 被 CSL 限流，等待几分钟后重试。检查 `check_interval_ms` 是否太小（建议 ≥500）。

### Q: 如何添加更多账号？
A: 编辑 `config/config.yaml`，在 `accounts` 下添加：
```yaml
accounts:
  - username: "account1@example.com"
    password: "password1"
  - username: "account2@example.com"  # 新账号
    password: "password2"
```

重新运行 `./run.sh` 选择选项 3。

### Q: 如何更换抢购商品？
A: 修改 `config/config.yaml` 中的 `product` 部分，重启监控服务器。

## 性能对比

| 方案 | 响应时间 | 说明 |
|------|---------|------|
| Python 原版 | 3-5 秒 | 浏览器全流程操作 |
| Go 混合模式 | <100ms | Cookie 预热 + HTTP 加购 |
| 纯 HTTP（无验证）| 20-50ms | 仅适用于无反爬网站 |

## 卸载

```bash
cd csl-rush-system
rm -rf bin/
# 保留 config/config.yaml（你的账号配置）
```

## 技术支持

项目地址：`/Volumes/My Passport/eshop/csl-rush-system`

查看详细架构说明：`README.md`
