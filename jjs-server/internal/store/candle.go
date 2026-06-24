package store

import (
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

func UpsertCandle(stockID uint, period string, openTime time.Time, price int64, qty int64) error {
	return UpsertCandleWithTx(DB, stockID, period, openTime, price, qty)
}

func UpsertCandleWithTx(db *gorm.DB, stockID uint, period string, openTime time.Time, price int64, qty int64) error {
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
		return db.Create(&candle).Error
	}

	if price > candle.High {
		candle.High = price
	}
	if price < candle.Low || candle.Low == 0 {
		candle.Low = price
	}
	candle.Close = price
	candle.Volume += qty
	return db.Save(&candle).Error
}

func GetCandles(stockID uint, period string, limit int) ([]domain.Candle, error) {
	var candles []domain.Candle
	err := DB.Where("stock_id = ? AND period = ?", stockID, period).
		Order("open_time DESC").
		Limit(limit).
		Find(&candles).Error
	return candles, err
}
