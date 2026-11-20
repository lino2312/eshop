# CSL 抢购系统 - Go 版本

集中式库存监控 + 分布式终端抢购架构，性能优化的 CSL 网站抢购系统。

## 架构设计

```
┌─────────────────┐
│  监控服务器      │ ← 单点轮询库存 API (500ms/次)
│  (Go HTTP)      │
└────────┬────────┘
         │ WebSocket 广播
         ↓
┌────────────┬────────────┬────────────┐
│  客户端1    │  客户端2    │  客户端3    │
│ (已登录)    │ (已登录)    │ (已登录)    │
└────────────┴────────────┴────────────┘
收到通知 → 立即用 Cookie 加购 (<100ms)
```

## 优势

- **零延迟响应**: WebSocket 长连接，收到通知 < 10ms
- **浏览器预热**: 提前完成登录和 Cloudflare 验证
- **单点监控**: 避免多账号并发被限流
- **纯 HTTP 抢购**: Cookie 预热后无需浏览器，直接 API 加购

## 快速开始

### 1. 配置账号

编辑 `config/config.yaml`:

```yaml
accounts:
  - username: "your-email@example.com"
    password: "your-password"
  - username: "another@example.com"
    password: "another-password"
```

### 2. 配置商品

```yaml
product:
  name: "iPhone 17 Pro Max"
  color: "927"      # 927=银色, 31033=宇宙橙色, 31034=深墨蓝色
  storage: "1026"   # 1025=256GB, 1026=512GB, 1027=1TB
```

### 3. 运行

```bash
chmod +x run.sh
./run.sh
```

选择启动模式：
- **选项 1**: 仅启动监控服务器
- **选项 2**: 仅启动客户端（需服务器已运行）
- **选项 3**: 自动启动服务器 + 所有配置的客户端

## 手动运行

**启动监控服务器**:
```bash
./bin/server
```

**启动客户端** (每个账号一个进程):
```bash
./bin/client
```

## 编译

需要 Go 1.21+:

```bash
# 编译服务器
go build -o bin/server ./server

# 编译客户端
go build -o bin/client ./client
```

## 配置说明

### 服务器配置

```yaml
server:
  port: 8080
  check_interval_ms: 500  # 库存检查间隔
```

### 客户端配置

```yaml
client:
  server_url: "ws://localhost:8080/ws"
  headless: false          # 登录时是否使用无头浏览器
  purchase_quantity: 2     # 购买数量
```

## 工作流程

1. **客户端启动**: 使用 chromedp 登录 CSL 网站，提取 Cookie
2. **待命状态**: 关闭浏览器，通过 WebSocket 连接监控服务器
3. **服务器监控**: 每 500ms 轮询一次库存 API
4. **有货通知**: 服务器检测到库存，广播给所有客户端
5. **极速抢购**: 客户端收到通知，用 Cookie 直接调用加购 API
6. **自动结算**: 加购成功后跳转到支付页面

## 性能对比

| 实现方式 | 响应时间 | 优势 |
|---------|---------|------|
| Python + DrissionPage | 3-5秒 | 浏览器全流程，操作慢 |
| Go + chromedp (登录) + HTTP (抢购) | <100ms | Cookie 预热，纯 HTTP 加购 |

## 注意事项

- 配置文件 `config/config.yaml` 不会打包到二进制中，可随时修改
- 每个账号启动一个客户端进程
- 确保网络稳定，避免 WebSocket 断连
- 监控服务器建议部署在网络条件好的环境

## 目录结构

```
csl-rush-system/
├── server/          # 监控服务器
├── client/          # 终端客户端
├── protocol/        # 通信协议
├── config/          # 配置文件和加载器
├── bin/             # 编译输出
├── run.sh           # 启动脚本
└── README.md
```

## License

MIT
