package store

import (
	"gorm.io/gorm"

	"jjs-server/internal/domain"
)

func ListStocks() ([]domain.Stock, error) {
	var stocks []domain.Stock
	err := DB.Find(&stocks).Error
	return stocks, err
}

func GetStockByID(stockID uint) (*domain.Stock, error) {
	var s domain.Stock
	if err := DB.First(&s, stockID).Error; err != nil {
		return nil, err
	}
	return &s, nil
}

func GetStockBySymbol(symbol string) (*domain.Stock, error) {
	var s domain.Stock
	if err := DB.Where("symbol = ?", symbol).First(&s).Error; err != nil {
		return nil, err
	}
	return &s, nil
}

func UpdateStockFromTrade(tx *gorm.DB, stockID uint, price int64, qty int64, turnover int64) error {
	updates := map[string]interface{}{
		"current_price": price,
		"volume":        gorm.Expr("volume + ?", qty),
		"turnover":      gorm.Expr("turnover + ?", turnover),
		"high":          gorm.Expr("GREATEST(high, ?)", price),
		"low":           gorm.Expr("CASE WHEN low = 0 THEN ? ELSE LEAST(low, ?) END", price, price),
		"open":          gorm.Expr("CASE WHEN open = 0 THEN ? ELSE open END", price),
	}
	return tx.Model(&domain.Stock{}).Where("id = ?", stockID).Updates(updates).Error
}

type OrderBookLevel struct {
	Price  int64
	Volume int64
}

func SnapshotOrderBook(tx *gorm.DB, stockID uint) error {
	var bidLevels []OrderBookLevel
	tx.Raw(`
		SELECT price, SUM(qty - filled_qty) as volume
		FROM orders
		WHERE stock_id = ? AND side = 'buy' AND type = 'limit' AND status IN ('open','partial')
		GROUP BY price ORDER BY price DESC LIMIT 5
	`, stockID).Scan(&bidLevels)

	var askLevels []OrderBookLevel
	tx.Raw(`
		SELECT price, SUM(qty - filled_qty) as volume
		FROM orders
		WHERE stock_id = ? AND side = 'sell' AND type = 'limit' AND status IN ('open','partial')
		GROUP BY price ORDER BY price ASC LIMIT 5
	`, stockID).Scan(&askLevels)

	updates := map[string]interface{}{
		"bid_price_1": int64(0), "bid_vol_1": int64(0),
		"bid_price_2": int64(0), "bid_vol_2": int64(0),
		"bid_price_3": int64(0), "bid_vol_3": int64(0),
		"bid_price_4": int64(0), "bid_vol_4": int64(0),
		"bid_price_5": int64(0), "bid_vol_5": int64(0),
		"ask_price_1": int64(0), "ask_vol_1": int64(0),
		"ask_price_2": int64(0), "ask_vol_2": int64(0),
		"ask_price_3": int64(0), "ask_vol_3": int64(0),
		"ask_price_4": int64(0), "ask_vol_4": int64(0),
		"ask_price_5": int64(0), "ask_vol_5": int64(0),
	}

	bidFields := []struct {
		price, vol string
	}{
		{"bid_price_1", "bid_vol_1"},
		{"bid_price_2", "bid_vol_2"},
		{"bid_price_3", "bid_vol_3"},
		{"bid_price_4", "bid_vol_4"},
		{"bid_price_5", "bid_vol_5"},
	}
	for i, l := range bidLevels {
		if i >= 5 {
			break
		}
		updates[bidFields[i].price] = l.Price
		updates[bidFields[i].vol] = l.Volume
	}

	askFields := []struct {
		price, vol string
	}{
		{"ask_price_1", "ask_vol_1"},
		{"ask_price_2", "ask_vol_2"},
		{"ask_price_3", "ask_vol_3"},
		{"ask_price_4", "ask_vol_4"},
		{"ask_price_5", "ask_vol_5"},
	}
	for i, l := range askLevels {
		if i >= 5 {
			break
		}
		updates[askFields[i].price] = l.Price
		updates[askFields[i].vol] = l.Volume
	}

	return tx.Model(&domain.Stock{}).Where("id = ?", stockID).Updates(updates).Error
}
