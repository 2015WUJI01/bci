# Tasks — 景气度随机游走改进

## Task 1: IndustryConfig 新增 ProsperityStdDev 并更新参数

**文件**: `jjs-server/internal/engine/industry.go`

- [x] 1.1 `IndustryConfig` 结构体新增字段 `ProsperityStdDev float64`
- [x] 1.2 更新各行业 `ProsperityMax` 为非对称值（`1 / ProsperityMin`）
- [x] 1.3 各行业新增 `ProsperityStdDev`（MaxStep 的一半，见设计表）
- [ ] 1.4 验证：`go build ./...` 通过 (需要 Go 环境)

## Task 2: 重写 WalkProsperity 算法

**文件**: `jjs-server/internal/engine/prosperity.go`

- [x] 2.1 新增 `calcDeviation()` 辅助函数
- [x] 2.2 重写 `WalkProsperity()`：正态分布步长 + 非对称回归 + 保留脉冲
- [x] 2.3 保留 `clamp()` 辅助函数
- [ ] 2.4 验证：`go build ./...` 通过 (需要 Go 环境)

## Task 3: 心智检查 — 确认所有调用方不受影响

**文件**: 以下文件中搜索 `WalkProsperity` 或 `Prosperity` 的使用

- [x] 3.1 `engine/ticker.go` — 每季度调用 `WalkProsperity()`，仅传参不变
- [x] 3.2 `engine/manufacturing.go` / `engine/mining.go` — 仅读取已存的 prosperity，不受算法变更影响
- [x] 3.3 `bots/scheduler.go` / `bots/helpers.go` — 读取 prosperity，不受影响
- [x] 3.4 `handler/company.go` / `handler/action.go` / `handler/ipo.go` / `handler/leaderboard.go` — 读取 prosperity，不受影响
