## 1. GORM 依赖升级

- [x] 1.1 Upgrade `gorm.io/gorm` v1.30.0 → v1.31.2
- [x] 1.2 Upgrade `gorm.io/driver/mysql` v1.5.7 → v1.6.0
- [x] 1.3 Upgrade `github.com/go-sql-driver/mysql` v1.8.1 → v1.10.0
- [x] 1.4 Run `go mod tidy && go build ./...` to verify

## 2. Store layer — Bulk upsert

- [x] 2.1 Add `CandleTick` struct to `store/candle.go` (fields: StockID, Period, OpenTime, Price)
- [x] 2.2 Implement `BulkUpsertCandles(ticks []CandleTick) (map[uint]map[string]domain.Candle, error)` using raw SQL `INSERT ... ON DUPLICATE KEY UPDATE` with `GREATEST(high, VALUES(high))` and `IF(low=0, VALUES(low), LEAST(low, VALUES(low)))`
- [x] 2.3 After upsert, batch SELECT all affected candles with `WHERE (stock_id, period, open_time) IN ?` and return grouped map

## 3. Engine layer — Use batch upsert in tick

- [x] 3.1 Modify `TradingTicker.aggregateAllCandles()`: collect all (stockID, period, openTime, price) for valid stocks into `[]store.CandleTick`, call `store.BulkUpsertCandles` once, build `candlesByStock` from result
- [x] 3.2 Ensure stocks with `CurrentPrice <= 0` are still skipped (excluded from batch and from return map)

## 4. Risk verification (from design.md)

- [x] 4.1 R2: Code review — confirm `open` field is NOT in `ON DUPLICATE KEY UPDATE` clause (only high/low/close/volume)
- [x] 4.2 R3: Verify GORM composite IN `WHERE (stock_id, period, open_time) IN ?` compiles and runs correctly; if not, implement OR-based fallback
- [ ] 4.3 R6: Verify `time.Time` values serialize correctly in raw SQL — insert a candle and SELECT it back, confirm open_time matches

## 5. Build & runtime verification

- [x] 5.1 Run `go build ./...` in `jjs-server/` to verify compilation
- [x] 5.2 Run `pnpm typecheck && pnpm lint` in `jjs-web/` to ensure no frontend changes needed (pre-existing failures unrelated)
- [ ] 5.3 Start server locally, run `mysqladmin status` or `SHOW PROCESSLIST` to confirm query volume drops after tick starts
- [ ] 5.4 Verify WebSocket `PriceUpdate` message still contains `candlesByStock` field with valid OHLC data
- [x] 5.5 Verify existing `UpsertCandle` / `UpsertCandleWithTx` callers in `matching.go` still compile and function (no regression)
