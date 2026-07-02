package engine

import (
	"math"

	"gorm.io/gorm"

	"jjs-server/internal/domain"
	"jjs-server/internal/store"
)

type LiquidationResult struct {
	FireSale    int64 `json:"fire_sale"`
	PerShare    int64 `json:"per_share"`
	Distributed int64 `json:"distributed"`
	Holders     int   `json:"holders"`
}

func CanLiquidate(companyID uint, currentQuarter int) bool {
	var qs []domain.CompanyQuarterly
	store.DB.Where("company_id = ? AND quarter < ?", companyID, currentQuarter).
		Order("quarter DESC").Limit(2).Find(&qs)
	if len(qs) < 2 {
		return false
	}
	return qs[0].Cash < 0 && qs[1].Cash < 0
}

func cancelAllOrdersForStock(tx *gorm.DB, stockID uint) error {
	var orders []domain.Order
	if err := tx.Where("stock_id = ? AND status IN ('open','partial')", stockID).Find(&orders).Error; err != nil {
		return err
	}

	for _, order := range orders {
		if order.Side == "buy" && order.FrozenAmount > 0 {
			if err := store.UnfreezeCash(tx, order.PlayerID, order.FrozenAmount); err != nil {
				return err
			}
		}
		if order.Side == "sell" {
			unfilledQty := order.Qty - order.FilledQty
			if unfilledQty > 0 {
				holding, err := store.GetHolding(tx, order.PlayerID, order.StockID)
				if err != nil {
					return err
				}
				if err := store.UnfreezeHoldingQty(tx, holding.ID, unfilledQty); err != nil {
					return err
				}
			}
		}
		order.Status = "cancelled"
		order.FrozenAmount = 0
		if err := tx.Save(&order).Error; err != nil {
			return err
		}
	}
	return nil
}

func LiquidateCompany(db *gorm.DB, company *domain.Company) (*LiquidationResult, error) {
	tx := db.Begin()

	cfg := Industries[company.Industry]

	var stock *domain.Stock
	if company.IpoQuarter > 0 {
		s, err := store.GetStockByCompanyID(company.ID)
		if err == nil {
			stock = s
		}
	}

	if stock != nil {
		if err := cancelAllOrdersForStock(tx, stock.ID); err != nil {
			tx.Rollback()
			return nil, err
		}
		if err := tx.Model(stock).Update("status", "delisted").Error; err != nil {
			tx.Rollback()
			return nil, err
		}
	}

	company.Employees = 0

	var fireSaleInventory int64
	var fireSaleCapacity int64

	if company.Inventory > 0 {
		var unitPrice float64
		switch company.Industry {
		case "manufacturing":
			unitPrice = mfgUnitPrice
		case "mining":
			unitPrice = miningUnitPrice
		}
		if unitPrice > 0 {
			fireSaleInventory = int64(math.Round(float64(company.Inventory) * unitPrice * 0.5))
			company.Cash += fireSaleInventory
		}
	}
	if company.CapCount > 0 && cfg.CapAssetValue > 0 {
		fireSaleCapacity = int64(math.Round(float64(company.CapCount) * cfg.CapAssetValue * 0.5))
		company.Cash += fireSaleCapacity
	}
	company.Inventory = 0
	company.CapCount = 0

	result := &LiquidationResult{
		FireSale: fireSaleInventory + fireSaleCapacity,
	}

	if stock != nil && company.Cash > 0 && company.TotalShares > 0 {
		perShare := company.Cash / company.TotalShares
		result.PerShare = perShare

		var holdings []domain.Holding
		if err := tx.Where("stock_id = ? AND qty > 0", stock.ID).Find(&holdings).Error; err != nil {
			tx.Rollback()
			return nil, err
		}

		for _, h := range holdings {
			cashAmount := perShare * h.Qty
			if cashAmount > 0 {
				if err := store.AddCash(tx, h.PlayerID, cashAmount); err != nil {
					tx.Rollback()
					return nil, err
				}
				result.Distributed += cashAmount
			}
		}
		result.Holders = len(holdings)
	}

	if stock == nil && company.Cash > 0 && company.TotalShares > 0 {
		ceoCash := company.Cash * company.CEOShares / company.TotalShares
		if ceoCash > 0 {
			if err := store.AddCash(tx, company.CEOID, ceoCash); err != nil {
				tx.Rollback()
				return nil, err
			}
			result.PerShare = company.Cash / company.TotalShares
			result.Distributed = ceoCash
			result.Holders = 1
		}
	}

	if stock != nil {
		if err := store.ZeroOutHoldings(tx, stock.ID); err != nil {
			tx.Rollback()
			return nil, err
		}
	}

	if stock != nil {
		if err := store.DeleteBrokerInventoryByStockID(tx, stock.ID); err != nil {
			tx.Rollback()
			return nil, err
		}
	}
	if err := store.DeleteBuildOrdersByCompanyID(tx, company.ID); err != nil {
		tx.Rollback()
		return nil, err
	}

	company.Status = "liquidated"
	if err := tx.Save(company).Error; err != nil {
		tx.Rollback()
		return nil, err
	}

	if err := tx.Commit().Error; err != nil {
		return nil, err
	}

	return result, nil
}
