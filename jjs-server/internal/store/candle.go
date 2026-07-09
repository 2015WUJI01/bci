package store

import (
	"fmt"
	"strings"
	"time"

	"gorm.io/gorm"

	"jjs-server/internal/domain"
)

type PeriodStockStats struct {
	StockID    uint
	PeriodOpen int64
	PeriodHigh int64
	PeriodLow  int64
	PeriodVol  int64
}

// CandleTick 是批量 candle 更新的单条输入，描述某个股票在某个时间窗口内的当前价格。
// 调用方收集所有需要更新的 stock×period 组合，一次传入 BulkUpsertCandles。
type CandleTick struct {
	StockID  uint      // 股票 ID
	Period   string    // K 线周期："15t" / "60t" / "150t"
	OpenTime time.Time // 当前 candle 窗口的起始时间（按周期秒数向下取整）
	Price    int64     // 当前最新价格（分）
}

func GetPeriodStatsForAllStocks(period string) (map[uint]PeriodStockStats, error) {
	var results []PeriodStockStats
	err := DB.Raw(`
		SELECT
			c.stock_id,
			c.open AS period_open,
			c.high AS period_high,
			c.low AS period_low,
			c.volume AS period_vol
		FROM candles c
		INNER JOIN (
			SELECT stock_id, MAX(open_time) AS max_time
			FROM candles
			WHERE period = ?
			GROUP BY stock_id
		) m ON c.stock_id = m.stock_id AND c.open_time = m.max_time
		WHERE c.period = ?
	`, period, period).Scan(&results).Error

	if err != nil {
		return nil, err
	}

	stats := make(map[uint]PeriodStockStats, len(results))
	for _, r := range results {
		stats[r.StockID] = r
	}
	return stats, nil
}

func UpsertCandle(stockID uint, period string, openTime time.Time, price int64, qty int64) (domain.Candle, error) {
	return UpsertCandleWithTx(DB, stockID, period, openTime, price, qty)
}

func UpsertCandleWithTx(db *gorm.DB, stockID uint, period string, openTime time.Time, price int64, qty int64) (domain.Candle, error) {
	var candle domain.Candle
	err := db.Where("stock_id = ? AND period = ? AND open_time = ?", stockID, period, openTime).First(&candle).Error
	if err != nil {
		candle = domain.Candle{
			StockID:  stockID,
			Period:   period,
			OpenTime: openTime,
			Open:     price,
			High:     price,
			Low:      price,
			Close:    price,
			Volume:   qty,
		}
		return candle, db.Create(&candle).Error
	}

	if price > candle.High {
		candle.High = price
	}
	if price < candle.Low || candle.Low == 0 {
		candle.Low = price
	}
	candle.Close = price
	candle.Volume += qty
	return candle, db.Save(&candle).Error
}

// BulkUpsertCandles 批量更新所有股票的 K 线数据，用一次 INSERT ... ON DUPLICATE KEY UPDATE
// 替换原有的逐股票逐周期 UpsertCandle 循环调用，将 N×3×2 次独立 DB 往返压缩为 2 次查询。
//
// 行为等价于对每个 CandleTick 依次调用 UpsertCandle(StockID, Period, OpenTime, Price, 0)，
// 即：新 candle 则创建（open/high/low/close 均为 Price），已存在则更新 high（取较大值）、
// low（取较小值，原 low 为 0 时直接写入 Price）、close=Price，volume 不变（qty=0）。
//
// 原理：
//   - 通过唯一索引 uq_candle(stock_id, period, open_time) 触发 ON DUPLICATE KEY UPDATE，
//     用 GREATEST/LEAST/IF 函数在 SQL 层面完成 OHLC 条件更新，避免逐个 upsert 的往返开销。
//   - upsert 完成后批量 SELECT 回全部受影响的 candle，构建 stockID → period → Candle 的
//     二级 map 供 WebSocket 广播使用。
//
// 使用方式：
//
//	ticks := make([]CandleTick, 0, len(stocks)*3)
//	for _, s := range stocks {
//	    for _, p := range periods {
//	        ticks = append(ticks, CandleTick{StockID: s.ID, Period: p.Name, OpenTime: t, Price: s.CurrentPrice})
//	    }
//	}
//	candlesByStock, err := BulkUpsertCandles(ticks)
func BulkUpsertCandles(ticks []CandleTick) (map[uint]map[string]domain.Candle, error) {
	if len(ticks) == 0 {
		return make(map[uint]map[string]domain.Candle), nil
	}

	// 构建多行 INSERT 语句，每行 8 个占位符：stock_id, period, open_time, open, high, low, close, volume
	valuePlaceholders := make([]string, 0, len(ticks))
	upsertArgs := make([]interface{}, 0, len(ticks)*8)
	for _, t := range ticks {
		valuePlaceholders = append(valuePlaceholders, "(?, ?, ?, ?, ?, ?, ?, ?)")
		// open/high/low/close 初始均为当前价格；volume 传 0 因为 tick 聚合只记录价格不含成交量
		upsertArgs = append(upsertArgs, t.StockID, t.Period, t.OpenTime,
			t.Price, t.Price, t.Price, t.Price, int64(0))
	}

	// ON DUPLICATE KEY UPDATE 中仅更新 high/low/close/volume，open 保持不变（candle 首价不可变）
	sql := fmt.Sprintf(`
		INSERT INTO candles (stock_id, period, open_time, open, high, low, close, volume)
		VALUES %s
		ON DUPLICATE KEY UPDATE
			high = GREATEST(high, VALUES(high)),
			low = IF(low = 0, VALUES(low), LEAST(low, VALUES(low))),
			close = VALUES(close),
			volume = volume + VALUES(volume)
	`, strings.Join(valuePlaceholders, ", "))

	if err := DB.Exec(sql, upsertArgs...).Error; err != nil {
		return nil, err
	}

	// ON DUPLICATE KEY UPDATE 不返回行数据，需额外 SELECT 取回最新 candle。
	// 用 OR 条件拼接代替复合 IN 以避免 GORM 版本兼容性问题。
	whereClauses := make([]string, 0, len(ticks))
	selectArgs := make([]interface{}, 0, len(ticks)*3)
	for _, t := range ticks {
		whereClauses = append(whereClauses, "(stock_id = ? AND period = ? AND open_time = ?)")
		selectArgs = append(selectArgs, t.StockID, t.Period, t.OpenTime)
	}

	var candles []domain.Candle
	if err := DB.Where(strings.Join(whereClauses, " OR "), selectArgs...).Find(&candles).Error; err != nil {
		return nil, err
	}

	// 构建 stockID → period → Candle 的二级 map，与 aggregateAllCandles 的返回格式一致
	result := make(map[uint]map[string]domain.Candle)
	for _, c := range candles {
		if _, ok := result[c.StockID]; !ok {
			result[c.StockID] = make(map[string]domain.Candle)
		}
		result[c.StockID][c.Period] = c
	}
	return result, nil
}

func GetCandles(stockID uint, period string, limit int) ([]domain.Candle, error) {
	var candles []domain.Candle
	err := DB.Where("stock_id = ? AND period = ?", stockID, period).
		Order("open_time DESC").
		Limit(limit).
		Find(&candles).Error
	return candles, err
}

func GetRecentClosePrices(stockID uint, limit int) ([]int64, error) {
	var prices []int64
	err := DB.Model(&domain.Candle{}).
		Where("stock_id = ? AND period = ?", stockID, "15t").
		Order("open_time DESC").
		Limit(limit).
		Pluck("close", &prices).Error
	return prices, err
}

func GetRecentVolumes(stockID uint, limit int) ([]int64, error) {
	var volumes []int64
	err := DB.Model(&domain.Candle{}).
		Where("stock_id = ? AND period = ?", stockID, "15t").
		Order("open_time DESC").
		Limit(limit).
		Pluck("volume", &volumes).Error
	return volumes, err
}

func GetRecentClosePricesAll(limit int) (map[uint][]int64, error) {
	rows, err := DB.Raw(`
		SELECT stock_id, close FROM (
			SELECT stock_id, close,
				ROW_NUMBER() OVER (PARTITION BY stock_id ORDER BY open_time DESC) as rn
			FROM candles WHERE period = '15t'
		) t WHERE rn <= ?
	`, limit).Rows()
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := make(map[uint][]int64)
	for rows.Next() {
		var stockID uint
		var price int64
		if err := rows.Scan(&stockID, &price); err != nil {
			return nil, err
		}
		result[stockID] = append(result[stockID], price)
	}
	return result, nil
}

func GetRecentVolumesAll(limit int) (map[uint][]int64, error) {
	rows, err := DB.Raw(`
		SELECT stock_id, volume FROM (
			SELECT stock_id, volume,
				ROW_NUMBER() OVER (PARTITION BY stock_id ORDER BY open_time DESC) as rn
			FROM candles WHERE period = '15t'
		) t WHERE rn <= ?
	`, limit).Rows()
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := make(map[uint][]int64)
	for rows.Next() {
		var stockID uint
		var volume int64
		if err := rows.Scan(&stockID, &volume); err != nil {
			return nil, err
		}
		result[stockID] = append(result[stockID], volume)
	}
	return result, nil
}
