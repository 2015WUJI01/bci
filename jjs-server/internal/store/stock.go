package store

import (
	"gorm.io/gorm"

	"jjs-server/internal/domain"
)

func GetStocksByIDs(ids []uint) ([]domain.Stock, error) {
	var stocks []domain.Stock
	err := DB.Where("id IN ?", ids).Find(&stocks).Error
	return stocks, err
}

func ListStocks() ([]domain.Stock, error) {
	var stocks []domain.Stock
	err := DB.Where("status = ?", "active").Find(&stocks).Error
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

func GetStockByCompanyID(companyID uint) (*domain.Stock, error) {
	var s domain.Stock
	if err := DB.Where("company_id = ?", companyID).First(&s).Error; err != nil {
		return nil, err
	}
	return &s, nil
}

func UpdateStockFromTrade(tx *gorm.DB, stockID uint, price int64) error {
	return tx.Model(&domain.Stock{}).Where("id = ?", stockID).Update("current_price", price).Error
}

type OrderBookLevel struct {
	Price  int64
	Volume int64
}

func GetOrderBook(stockID uint) (bids []OrderBookLevel, asks []OrderBookLevel, err error) {
	err = DB.Raw(`
		SELECT price, SUM(qty - filled_qty) as volume
		FROM orders
		WHERE stock_id = ? AND side = 'buy' AND type = 'limit' AND status IN ('open','partial')
		GROUP BY price ORDER BY price DESC LIMIT 5
	`, stockID).Scan(&bids).Error
	if err != nil {
		return nil, nil, err
	}

	err = DB.Raw(`
		SELECT price, SUM(qty - filled_qty) as volume
		FROM orders
		WHERE stock_id = ? AND side = 'sell' AND type = 'limit' AND status IN ('open','partial')
		GROUP BY price ORDER BY price ASC LIMIT 5
	`, stockID).Scan(&asks).Error
	if err != nil {
		return nil, nil, err
	}

	return bids, asks, nil
}

type StockOrderBook struct {
	StockID uint
	Bids    []OrderBookLevel
	Asks    []OrderBookLevel
}

func GetAllOrderBooks(stockIDs []uint) (map[uint]StockOrderBook, error) {
	if len(stockIDs) == 0 {
		return map[uint]StockOrderBook{}, nil
	}

	type rawRow struct {
		StockID uint  `gorm:"column:stock_id"`
		Price   int64 `gorm:"column:price"`
		Volume  int64 `gorm:"column:volume"`
	}

	var bids []rawRow
	err := DB.Raw(`
		SELECT stock_id, price, volume FROM (
			SELECT stock_id, price, SUM(qty - filled_qty) as volume,
				ROW_NUMBER() OVER (PARTITION BY stock_id ORDER BY price DESC) as rn
			FROM orders
			WHERE stock_id IN ? AND side = 'buy' AND type = 'limit' AND status IN ('open','partial')
			GROUP BY stock_id, price
		) t WHERE rn <= 5
		ORDER BY stock_id, price DESC
	`, stockIDs).Scan(&bids).Error
	if err != nil {
		return nil, err
	}

	var asks []rawRow
	err = DB.Raw(`
		SELECT stock_id, price, volume FROM (
			SELECT stock_id, price, SUM(qty - filled_qty) as volume,
				ROW_NUMBER() OVER (PARTITION BY stock_id ORDER BY price ASC) as rn
			FROM orders
			WHERE stock_id IN ? AND side = 'sell' AND type = 'limit' AND status IN ('open','partial')
			GROUP BY stock_id, price
		) t WHERE rn <= 5
		ORDER BY stock_id, price ASC
	`, stockIDs).Scan(&asks).Error
	if err != nil {
		return nil, err
	}

	result := make(map[uint]StockOrderBook, len(stockIDs))
	for _, b := range bids {
		ob := result[b.StockID]
		ob.StockID = b.StockID
		ob.Bids = append(ob.Bids, OrderBookLevel{Price: b.Price, Volume: b.Volume})
		result[b.StockID] = ob
	}
	for _, a := range asks {
		ob := result[a.StockID]
		ob.StockID = a.StockID
		ob.Asks = append(ob.Asks, OrderBookLevel{Price: a.Price, Volume: a.Volume})
		result[a.StockID] = ob
	}

	return result, nil
}
