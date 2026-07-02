package store

import (
	"gorm.io/gorm"

	"jjs-server/internal/domain"
)

func ListActiveBrokerInventories() ([]domain.BrokerInventory, error) {
	var inventories []domain.BrokerInventory
	err := DB.Where("total_qty > 0").Find(&inventories).Error
	return inventories, err
}

func GetBrokerInventory(stockID uint) (*domain.BrokerInventory, error) {
	var bi domain.BrokerInventory
	if err := DB.Where("stock_id = ?", stockID).First(&bi).Error; err != nil {
		return nil, err
	}
	return &bi, nil
}

func DeductBrokerInventory(tx *gorm.DB, stockID uint, qty int64) error {
	return tx.Model(&domain.BrokerInventory{}).Where("stock_id = ? AND total_qty >= ?", stockID, qty).
		Update("total_qty", gorm.Expr("total_qty - ?", qty)).Error
}
