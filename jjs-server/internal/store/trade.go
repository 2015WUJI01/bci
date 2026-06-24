package store

import (
	"jjs-server/internal/domain"
)

func CreateTrade(trade *domain.Trade) error {
	return DB.Create(trade).Error
}

func GetTradesByStock(stockID uint, limit int) ([]domain.Trade, error) {
	var trades []domain.Trade
	err := DB.Where("stock_id = ?", stockID).
		Order("id DESC").
		Limit(limit).
		Find(&trades).Error
	return trades, err
}
