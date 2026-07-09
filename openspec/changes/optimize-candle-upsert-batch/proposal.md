## Why

`aggregateAllCandles` in `trading_ticker.go` 每 2 秒对每个活跃股票执行 3 次 `UpsertCandle`（15t/30s、60t/120s、150t/300s 三个周期），每次 `UpsertCandle` 执行 1 次 `First` 查询 + 1 次 `Create`/`Save` 写入。N 个活跃股票 = N × 3 × 2 = 6N 次独立数据库往返。当前约 50 个股票时，每 2 秒产生 300 次查询，占 MySQL 查询总量的 60% 以上。将其改为批量操作可将 300 次查询降至 3~6 次。

## What Changes

- 升级 GORM 全家桶至最新稳定版：`gorm.io/gorm` v1.30.0 → v1.31.2、`gorm.io/driver/mysql` v1.5.7 → v1.6.0、`github.com/go-sql-driver/mysql` v1.8.1 → v1.10.0
- 新增 `store.BulkUpsertCandles` 批量接口：接收多个 stockID + period + price 组合，在单次事务中完成所有 candle 的 upsert
- 修改 `TradingTicker.aggregateAllCandles`：用一次批量调用替代原有的 N × 3 循环调用
- `UpsertCandle` / `UpsertCandleWithTx` 保留向下兼容（交易引擎中 `matching.go` 仍在使用单次调用记录成交量）

## Capabilities

### New Capabilities

- `batch-candle-upsert`: 批量 candle upsert 存储接口，支持在一次数据库往返中更新多个 stock+period 组合的 OHLC 数据

### Modified Capabilities

<!-- None -->

## Impact

- `jjs-server/internal/store/candle.go` — 新增 `BulkUpsertCandles` 函数
- `jjs-server/internal/engine/trading_ticker.go` — 修改 `aggregateAllCandles` 方法
- `jjs-server/go.mod` — GORM 依赖升级（v1.30.0→v1.31.2, driver/mysql v1.5.7→v1.6.0, go-sql-driver v1.8.1→v1.10.0）
- 预计 MySQL QPS 降低 ~150（当前 tick 中 candle 相关部分）
- 无 API 变更，无数据模型变更，无 breaking change
