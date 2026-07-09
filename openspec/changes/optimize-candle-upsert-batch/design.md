## Context

`TradingTicker.onTick()` 每 2 秒触发一次，其中 `aggregateAllCandles` 对每个活跃股票执行 3 次 (15t/60t/150t) `store.UpsertCandle`。每个 `UpsertCandle` 执行 `First`（读）+ `Create`/`Save`（写），即 2 次独立 DB 往返。对于 N 个活跃股票，每 tick 产生 6N 次查询（约 300 次/tick），占 Hot Path 查询量 60% 以上。

`UpsertCandle` 的语义：若 candle 已存在则更新 high/low/close/volume，否则创建新 candle。交易引擎（`matching.go`）在成交时也调用 `UpsertCandle` 记录成交量，但该路径频率低（每笔成交），且需要在已有事务中执行，故保留不改。

**前置变更**：GORM 依赖已从 v1.30.0 升级至 v1.31.2（`gorm.io/gorm`）、MySQL driver 从 v1.5.7 升级至 v1.6.0（`gorm.io/driver/mysql`）、底层 driver 从 v1.8.1 升级至 v1.10.0（`github.com/go-sql-driver/mysql`）。构建验证已通过。

## Goals / Non-Goals

**Goals:**
- 将 tick 路径的 candle upsert 从 6N 次独立 DB 往返降至 2 次（1 upsert + 1 select）
- 保持与原有 `UpsertCandle` 完全一致的 OHLC 语义（high 取最大值、low 取最小值并处理 0、close=最新价格、volume 累加）
- 保持函数签名兼容：`aggregateAllCandles` 返回类型不变

**Non-Goals:**
- 不改动交易引擎中的 `UpsertCandleWithTx`（成交量记录路径）
- 不改动 WebSocket 广播逻辑
- 不改动 candle 数据模型或索引
- 不优化 AI 交易者或季度结算的查询模式（后续 change 处理）

## Decisions

### 决策 1：使用 `INSERT ... ON DUPLICATE KEY UPDATE` 原生 SQL

**选择**：构建多行 INSERT ... ON DUPLICATE KEY UPDATE 语句，一次性完成所有 candle 的 upsert。

**替代方案**：
- GORM `Clauses(clause.OnConflict{...}).Create(&candles)` — 不支持 UPDAT 中的条件逻辑（GREATEST/LEAST），会错误地将 low 覆盖为当前价格
- 两阶段（SELECT 全部 → 内存合并 → 分别 INSERT/UPDATE）— 查询次数更多，无优势

**理由**：原生 SQL 能用 `GREATEST(high, VALUES(high))` 和 `IF(low=0, VALUES(low), LEAST(low, VALUES(low)))` 精确表达 OHLC 条件语义，且仅需 1 次查询完成全部 upsert。

唯一索引为 `(stock_id, period, open_time)`，ON DUPLICATE KEY UPDATE 在此约束上触发。

### 决策 2：upsert 后 SELECT 回最新的 candle

`INSERT ... ON DUPLICATE KEY UPDATE` 不返回完整行数据（MySQL 返回 affected rows 但非 full row），而 `aggregateAllCandles` 需要返回完整的 `map[uint]map[string]domain.Candle` 用于 WebSocket 广播。

**选择**：upsert 之后执行一次批量 SELECT：
```sql
SELECT * FROM candles WHERE (stock_id, period, open_time) IN ((1,'15t','...'), (1,'60t','...'), ...)
```

GORM 可直接用 `db.Where("(stock_id, period, open_time) IN ?", tuples).Find(&candles)`。

### 决策 3：新增 `CandleTick` 输入类型和 `BulkUpsertCandles` 函数

在 `store/candle.go` 新增：
```go
type CandleTick struct {
    StockID  uint
    Period   string
    OpenTime time.Time
    Price    int64
}

func BulkUpsertCandles(ticks []CandleTick) (map[uint]map[string]domain.Candle, error)
```

调用方 `aggregateAllCandles` 将所有 stock × period 组合收集到一个 `[]CandleTick` 切片中，一次调用完成全部 upsert。

### 决策 4：保留 `UpsertCandle` / `UpsertCandleWithTx`

不改动这两个现有函数，确保交易引擎（`matching.go`）等调用方不受影响。

## Risks / Trade-offs

### R1: 唯一索引完整性 ✅ 已确认

`ON DUPLICATE KEY UPDATE` 依赖 `uq_candle` 索引触发冲突检测。已验证 `domain/models.go:153-155`：
```go
StockID  uint      `gorm:"uniqueIndex:uq_candle;not null"`
Period   string    `gorm:"type:varchar(10);uniqueIndex:uq_candle;not null"`
OpenTime time.Time `gorm:"uniqueIndex:uq_candle;not null"`
```
`AutoMigrate` 中已注册 `&domain.Candle{}`（`store/db.go:45`）→ 索引一定会存在。**无风险。**

### R2: `open` 字段不应被 UPDATE 覆盖 ⚠️ 需代码审查验证

`open` 是 candle 第一个价格，创建后不可变。原生 SQL 必须在 `ON DUPLICATE KEY UPDATE` 子句中**排除** `open`：

```sql
-- ✅ 正确：open 不在 UPDATE 子句中
INSERT INTO candles (...) VALUES (...)
ON DUPLICATE KEY UPDATE
  high = GREATEST(high, VALUES(high)),
  low = IF(low = 0, VALUES(low), LEAST(low, VALUES(low))),
  close = VALUES(close),
  volume = volume + VALUES(volume);

-- ❌ 错误：如果误把 open 也放入 UPDATE
ON DUPLICATE KEY UPDATE
  open = VALUES(open),  -- 会把 candle 的 open 改成当前价格
  ...
```

**缓解**：实现时确保 SQL 模板中 UPDATE 部分只包含 high/low/close/volume 四个字段，写入 tests.md 中校验。

### R3: GORM v1.30.0 复合 IN 查询兼容性 ⚠️ 需验证

upsert 后的 SELECT 需要复合条件 `WHERE (stock_id, period, open_time) IN (...)`：

```go
tuples := make([][]interface{}, 0, len(ticks))
for _, t := range ticks {
    tuples = append(tuples, []interface{}{t.StockID, t.Period, t.OpenTime})
}
db.Where("(stock_id, period, open_time) IN ?", tuples).Find(&candles)
```

GORM v1.30.0 理论支持复合 IN（`go.mod` 确认版本），但项目现有 7 处 IN 查询均为单列（如 `store/stock.go:11`、`store/order.go:73`），无先例。

**缓解**：若编译或运行时发现不支持，降级为拼接 OR 条件：
```go
db.Where(
    "(stock_id = ? AND period = ? AND open_time = ?)" + strings.Repeat(" OR (stock_id = ? AND period = ? AND open_time = ?)", len(ticks)-1),
    flattenArgs...,
).Find(&candles)
```
此降级方案查询次数仍为 1 次，性能等同。

### R4: 单点故障 vs 优雅降级 ⚠️ 行为变更

**当前行为**（循环调用 `UpsertCandle`）：某个 stock 的 candle upsert 失败时，`slog.Error` 记录日志并 `continue`，其余 candle 继续处理。一条失败不影响其他。

**批量行为**（单条 SQL）：SQL 构造错误或执行失败时，**整个 tick 所有 candle 更新全部丢失**。

**评估**：`UpsertCandle` 当前失败的唯一现实场景是 DB 连接中断——此时所有调用都会失败，循环跳过并无实际收益。且 candle 更新仅为辅助数据（WebSocket 前端 K 线展示），短期内丢失一个 candle 点对玩家无感知。**实际风险低。**

### R5: 原生 SQL 与 GORM 模型耦合的维护风险

若将来 `Candle` 模型增加或重命名字段（如新增 `adjusted_close`），需同步修改 `BulkUpsertCandles` 中的两处 SQL 字符串（INSERT 子句 + SELECT 子句）。

**缓解**：`BulkUpsertCandles` 与 `Candle` 模型位于同一 package（`store`），方便发现和维护。在函数注释中注明 SQL 依赖的字段列表。

### R6: `time.Time` 参数在原生 SQL 中的精度 ⚠️ 需验证

`openTime` 的类型为 `time.Time`，GORM 的 MySQL driver 会序列化为 `2006-01-02 15:04:05.999` (datetime(3))。`candleOpenTime()` 返回的值通过 Unix 秒级截断产生（`time.Unix(unix-(unix%periodSecs), 0)`），纳秒部分为零，无精度不一致问题。

但 GORM `db.Exec(sql, args...)` 中 `time.Time` 的绑定依赖 driver，需确认 MySQL driver 正确将 `time.Time` 序列化为 datetime(3) 字面量。

**缓解**：GORM v1.30.0 + `gorm.io/driver/mysql` 已熟练掌握此场景。若测试发现异常，可改为写入前显式格式化为 `time.Format("2006-01-02 15:04:05.000")` 字符串。

### R7: `max_allowed_packet` 限制 ✅ 安全边界已确认

150 行 × ~100 bytes = ~15KB << 4MB（MySQL 默认 `max_allowed_packet`）。即使 stocks 扩展到 500 个（1500 行 ≈ 150KB），仍在安全范围内。**无风险。**

### R8: 并发 tick 执行 ✅ 非新引入问题

若 tick 函数执行时间超过 2 秒间隔，`time.NewTicker` 会丢弃中间的 tick（channel 容量为 1），不会并发执行同一个 tick。当前 `aggregateAllCandles` 中 `UpsertCandle` 使用 `store.DB`（非事务），与批量 upsert 的隔离级别一致。**无新引入风险。**

### R9: 交易引擎 `UpsertCandleWithTx` 不受影响 ✅ 已确认

`matching.go` 在成交事务中调用 `UpsertCandleWithTx(tx, ...)` 记录成交量（包含非零 qty）。本次只新增 `BulkUpsertCandles` 用于 tick 路径（qty=0），不改动 `UpsertCandleWithTx`。两个路径互不干扰。**无风险。**

### 总体评估

| 风险 | 等级 | 状态 |
|------|------|------|
| R1 唯一索引完整性 | 🟢 低 | ✅ 已确认安全 |
| R2 `open` 字段误覆盖 | 🟡 中 | ⚠️ 需代码审查 |
| R3 GORM 复合 IN 兼容性 | 🟡 中 | ⚠️ 需验证，有降级方案 |
| R4 单点故障 vs 优雅降级 | 🟢 低 | ✅ 实际影响微小 |
| R5 原生 SQL 维护成本 | 🟢 低 | ✅ 同 package 内 |
| R6 `time.Time` 序列化精度 | 🟡 低 | ⚠️ 需验证，有降级方案 |
| R7 `max_allowed_packet` 限制 | 🟢 低 | ✅ 远低于阈值 |
| R8 并发 tick 执行 | 🟢 低 | ✅ 非新引入问题 |
| R9 交易引擎不受影响 | 🟢 低 | ✅ 路径隔离 |

需要关注的 3 个黄色风险均有明确的验证步骤或降级方案，不影响推进。
