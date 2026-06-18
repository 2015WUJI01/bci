# 大猫投资 (Big Cat Investment)

股票模拟交易游戏，支持实时撮合、做空与杠杆交易。

## 项目结构

| 目录 | 说明 |
| --- | --- |
| `jjs-server/` | Go 后端 (chi + GORM + MySQL + JWT)，当前活跃开发 |
| `jjs-web/` | React 前端 (TypeScript + Vite + Tailwind + TanStack Router)，当前活跃开发 |
| `backend/` | 遗留 Python 后端 (FastAPI + SQLite)，仅供参考，不再维护 |
| `frontend/` | 遗留前端 (vanilla JS)，仅供参考，不再维护 |
| `docs/` | 设计文档与重构路线图 |

## 技术栈

**后端**：Go 1.24, chi v5, GORM, MySQL, JWT (HS256), bcrypt

**前端**：React 18, TypeScript, Vite 6, Tailwind CSS 3, Zustand, TanStack Query, TanStack Router

## 本地启动

### 前置依赖

- Go 1.24+
- Node.js 18+，pnpm (`npm i -g pnpm`)
- MySQL 数据库

### 1. 后端 (jjs-server)

```bash
cd jjs-server

# 安装依赖
go mod tidy

# 编译
go build -o bin/jjs-server cmd/server/main.go

# 启动（需要 config.json）
./bin/jjs-server
```

### 后端配置

服务启动时会按以下顺序读取配置，**配置文件的值会覆盖环境变量**：

1. **默认值**（硬编码在代码中）：
   - MySQL DSN: `root:root@tcp(127.0.0.1:3306)/jjs?...`
   - JWT Secret: `jjs-dev-secret-change-in-production`
   - Port: `8080`

2. **环境变量**（可选的覆盖方式）：
   ```bash
   export MYSQL_DSN="user:pass@tcp(127.0.0.1:3306)/jjs?charset=utf8mb4&parseTime=True&loc=Local"
   export JWT_SECRET="your-secret"
   export PORT="8080"
   ```

3. **配置文件**（推荐，覆盖环境变量）：
   在 `jjs-server/` 目录下创建 `config.json`（gitignore 已忽略），格式如下：
   ```json
   {
     "mysql_dsn": "user:pass@tcp(127.0.0.1:3306)/jjs?charset=utf8mb4&parseTime=True&loc=Local",
     "jwt_secret": "your-secret",
     "port": "8080"
   }
   ```
   如需指定其他配置文件路径，可设置环境变量 `CONFIG_FILE`：

   ```bash
   CONFIG_FILE=./bin/config.json ./bin/jjs-server
   ```

若使用 MySQL 默认 `root:root@tcp(127.0.0.1:3306)/jjs...`，则无需任何配置即可启动 —— 只要本地 MySQL 的 root 密码是 `root` 且已创建 `jjs` 库。

### 2. 前端 (jjs-web)

```bash
cd jjs-web

# 安装依赖（必须使用 pnpm）
pnpm install

# 启动开发服务器（监听 :5173，自动代理 /api → :8080）
pnpm dev
```

访问 http://localhost:5173，登录后即可使用。

### 完整启动流程

1. 启动 MySQL，确保目标数据库已创建
2. 在 `jjs-server/` 下执行 `go build -o bin/jjs-server cmd/server/main.go && ./bin/jjs-server`
3. 在 `jjs-web/` 下执行 `pnpm dev`
4. 打开 http://localhost:5173

## 开发命令

```bash
# 后端
go run ./cmd/server                    # 直接运行（无需先编译）

# 前端
pnpm dev                               # 开发服务器
pnpm build                             # 生产构建 → dist/
pnpm typecheck                         # TypeScript 类型检查
pnpm lint                              # ESLint 检查
```

前端代码检查顺序：先 `pnpm typecheck`，再 `pnpm lint`，两者通过才算完成。

## 关键约定

- 包管理器：`jjs-web` 仅使用 **pnpm**
- 颜色体系：中国红涨（红涨绿跌），与西方习惯相反
- 密码长度：最低 3 位（刻意放宽，非 bug）
- 目前无测试、无 CI、无 pre-commit hook
