## 交易记录应用（本地运行）

- 后端: FastAPI + SQLite（本地文件）
- 前端: 简单移动端友好网页，可在同一 Wi‑Fi 下用手机访问

### 运行步骤

1. 安装依赖

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

2. 启动服务（默认监听 0.0.0.0，手机可访问）

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. 在电脑打开: `http://localhost:8000`
   在手机（同一 Wi‑Fi）打开: `http://<你电脑的局域网IP>:8000`

### 功能

- 记录现货买卖（币种、方向、数量、价格、时间、备注、手续费）
- 自动计算每个币种的移动加权成本、持仓数量、持仓成本、已实现盈亏
- 记录合约机器人（已关闭）的币种与利润
- 查看汇总与按币种查询

### 数据存储

- 本地 `sqlite` 数据库文件：`data/trades.db`
- 纯本地运行，不上传到网络

### 备份

- 直接备份 `data/` 目录即可

### 注意

- 本工具为记账与复盘用途，不连接交易所 API。

---

## 公开访问（不在同一局域网也能手机连）

有两种推荐方式：

### 方式 A：Cloudflare Tunnel（保留本地 SQLite）

无需云服务器，将本地 `http://localhost:8000` 暴露到公网，并用你的域名/子域名访问。

1. 安装 cloudflared（Windows）

```powershell
winget install Cloudflare.cloudflared
```

2. 登录并授权你的域名（按提示在浏览器确认）

```powershell
cloudflared tunnel login
```

3. 运行临时隧道（短期测试）

```powershell
cloudflared tunnel --url http://localhost:8000
```

命令会输出一个公网可访问的 URL（如 https://xxx.trycloudflare.com），手机即可直接访问。

4. 永久隧道（可选）：在 Cloudflare Zero Trust 面板创建 Tunnel，关联你的域名子域，并将流量指向 `http://localhost:8000`。

注意：使用隧道时，数据仍保存在你的本地机器 `data/trades.db`，请保证电脑在线即可访问。

### 方式 B：部署到 Render（云端数据库 Postgres）

1. 注册并登录 Render
2. 连接本仓库，选择根目录部署（或用 Render Blueprint）
3. Render 会按 `render.yaml` 创建一个免费 Web 服务和一个免费 Postgres 数据库
4. 启动后，Render 自动将 `DATABASE_URL` 注入环境；应用会使用云端 Postgres
5. 打开 Render 提供的 `onrender.com` 域名，用手机随时访问

如果你已有自己的云服务器，也可用 Docker 运行：

```bash
docker build -t trade-notes .
docker run -d -p 8000:8000 -e DATABASE_URL="postgresql://user:pass@host:5432/db" trade-notes
```
