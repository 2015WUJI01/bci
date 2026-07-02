package store

import (
	"gorm.io/gorm"

	"jjs-server/internal/domain"
)

func GetOrCreateHolding(db *gorm.DB, playerID string, stockID uint) (*domain.Holding, error) {
	var h domain.Holding
	err := db.Where("player_id = ? AND stock_id = ?", playerID, stockID).First(&h).Error
	if err == nil {
		return &h, nil
	}
	if err != gorm.ErrRecordNotFound {
		return nil, err
	}
	h = domain.Holding{PlayerID: playerID, StockID: stockID}
	if err := db.Create(&h).Error; err != nil {
		return nil, err
	}
	return &h, nil
}

func GetHolding(db *gorm.DB, playerID string, stockID uint) (*domain.Holding, error) {
	var h domain.Holding
	err := db.Where("player_id = ? AND stock_id = ?", playerID, stockID).First(&h).Error
	if err != nil {
		return nil, err
	}
	return &h, nil
}

func GetHoldingsByPlayer(playerID string) ([]domain.Holding, error) {
	var holdings []domain.Holding
	err := DB.Where("player_id = ? AND qty > 0", playerID).Find(&holdings).Error
	return holdings, err
}

func SaveHolding(db *gorm.DB, h *domain.Holding) error {
	return db.Save(h).Error
}

func UpdateHoldingQty(db *gorm.DB, playerID string, stockID uint, delta int64, avgCost int64) error {
	h, err := GetHolding(db, playerID, stockID)
	if err != nil {
		return err
	}
	if delta > 0 {
		totalCost := h.AvgCost*int64(h.Qty) + avgCost*delta
		h.Qty += delta
		if h.Qty > 0 {
			h.AvgCost = totalCost / h.Qty
		}
	} else {
		h.Qty += delta
	}
	return db.Save(h).Error
}

func FreezeHoldingQty(db *gorm.DB, holdingID uint, qty int64) error {
	return db.Model(&domain.Holding{}).Where("id = ?", holdingID).
		Update("frozen_qty", gorm.Expr("frozen_qty + ?", qty)).Error
}

func UnfreezeHoldingQty(db *gorm.DB, holdingID uint, qty int64) error {
	return db.Model(&domain.Holding{}).Where("id = ?", holdingID).
		Update("frozen_qty", gorm.Expr("GREATEST(frozen_qty - ?, 0)", qty)).Error
}

func DeductHoldingQty(db *gorm.DB, holdingID uint, qty int64) error {
	return db.Model(&domain.Holding{}).Where("id = ? AND frozen_qty >= ?", holdingID, qty).
		Updates(map[string]interface{}{
			"qty":        gorm.Expr("qty - ?", qty),
			"frozen_qty": gorm.Expr("frozen_qty - ?", qty),
		}).Error
}

func DeductHoldingQtyByPlayerStock(db *gorm.DB, playerID string, stockID uint, qty int64) error {
	return db.Model(&domain.Holding{}).Where("player_id = ? AND stock_id = ? AND frozen_qty >= ?", playerID, stockID, qty).
		Updates(map[string]interface{}{
			"qty":        gorm.Expr("qty - ?", qty),
			"frozen_qty": gorm.Expr("frozen_qty - ?", qty),
		}).Error
}

func GetHoldingsByStockID(stockID uint) ([]domain.Holding, error) {
	var holdings []domain.Holding
	err := DB.Where("stock_id = ? AND qty > 0", stockID).Find(&holdings).Error
	return holdings, err
}

func ZeroOutHoldings(tx *gorm.DB, stockID uint) error {
	return tx.Model(&domain.Holding{}).Where("stock_id = ?", stockID).
		Updates(map[string]interface{}{
			"qty":        0,
			"frozen_qty": 0,
		}).Error
}
