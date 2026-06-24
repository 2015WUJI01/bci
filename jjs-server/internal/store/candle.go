package store

import (
	"time"

	"gorm.io/gorm"

	"jjs-server/internal/domain"
)

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
