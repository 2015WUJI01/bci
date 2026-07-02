package engine

import (
	"log/slog"
	"time"

	"gorm.io/gorm"

	"jjs-server/internal/config"
	"jjs-server/internal/domain"
	"jjs-server/internal/store"
)

func ReleaseBrokerInventory(db *gorm.DB) {
	inventories, err := store.ListActiveBrokerInventories()
	if err != nil {
		slog.Error("broker: list inventories failed", "error", err)
		return
	}

	if len(inventories) == 0 {
		return
	}

	stockIDs := make([]uint, len(inventories))
	stockIDToInventory := make(map[uint]*domain.BrokerInventory, len(inventories))
	for i := range inventories {
		stockIDs[i] = inventories[i].StockID
		stockIDToInventory[inventories[i].StockID] = &inventories[i]
	}

	stocks, err := store.GetStocksByIDs(stockIDs)
	if err != nil {
		slog.Error("broker: list stocks failed", "error", err)
		return
	}

	slog.Info("broker: scanning", "stocks", len(stocks))
	_ = ensureBrokerPlayerState(db)

	for _, stock := range stocks {
		bi := stockIDToInventory[stock.ID]

		buy, err := store.GetBestOpenBuyOrder(stock.ID)
		if err != nil || buy == nil {
			continue
		}

		bestBid, _ := store.GetBestBid(stock.ID)
		refPrice := stock.CurrentPrice
		if bestBid > refPrice {
			refPrice = bestBid
		}
		if buy.Price < refPrice*9/10 {
			slog.Info("broker: price below threshold", "stockID", stock.ID, "orderID", buy.ID, "orderPrice", buy.Price, "refPrice", refPrice)
			continue
		}

		unfilled := buy.Qty - buy.FilledQty
		fillQty := unfilled
		if fillQty > bi.TotalQty {
			fillQty = bi.TotalQty
		}
		if fillQty <= 0 {
			continue
		}

		slog.Info("broker: matching order", "stockID", stock.ID, "orderID", buy.ID, "orderPrice", buy.Price, "fillQty", fillQty)

		err = func() error {
			tx := db.Begin()

			// 锁订单行防止并发修改
			var lockedBuy domain.Order
			if err := tx.Set("gorm:query_option", "FOR UPDATE").First(&lockedBuy, buy.ID).Error; err != nil {
				tx.Rollback()
				return err
			}
			if lockedBuy.Status != "open" && lockedBuy.Status != "partial" {
				tx.Rollback()
				return nil
			}

			// 基于锁定的实际状态重新计算
			lockedUnfilled := lockedBuy.Qty - lockedBuy.FilledQty
			lockedFillQty := lockedUnfilled
			if lockedFillQty > bi.TotalQty {
				lockedFillQty = bi.TotalQty
			}
			if lockedFillQty <= 0 {
				tx.Rollback()
				return nil
			}

			tradePrice := lockedBuy.Price
			fillAmountYuan := centsToYuan(tradePrice * lockedFillQty)
			buyCommission := calcCommission(fillAmountYuan)

			trade := domain.Trade{
				StockID:     stock.ID,
				BuyerID:     lockedBuy.PlayerID,
				SellerID:    config.SystemBrokerID,
				BuyOrderID:  lockedBuy.ID,
				SellOrderID: 0,
				Price:       tradePrice,
				Qty:         lockedFillQty,
				TotalAmount: tradePrice * lockedFillQty,
				TradeTime:   time.Now(),
			}
			if err := tx.Create(&trade).Error; err != nil {
				tx.Rollback()
				return err
			}

			buyerHolding, err := store.GetOrCreateHolding(tx, lockedBuy.PlayerID, stock.ID)
			if err != nil {
				tx.Rollback()
				return err
			}
			totalCost := int64(buyerHolding.Qty)*buyerHolding.AvgCost + tradePrice*int64(lockedFillQty)
			buyerHolding.Qty += lockedFillQty
			if buyerHolding.Qty > 0 {
				buyerHolding.AvgCost = totalCost / buyerHolding.Qty
			}
			if err := tx.Save(buyerHolding).Error; err != nil {
				tx.Rollback()
				return err
			}

			buyCost := fillAmountYuan + buyCommission
			if buyCost > lockedBuy.FrozenAmount {
				buyCost = lockedBuy.FrozenAmount
			}
			if err := store.DeductFrozenCash(tx, lockedBuy.PlayerID, buyCost); err != nil {
				tx.Rollback()
				return err
			}
			if err := store.UpdateOrderFrozenAmount(tx, lockedBuy.ID, lockedBuy.FrozenAmount-buyCost); err != nil {
				tx.Rollback()
				return err
			}

			newFilledQty := lockedBuy.FilledQty + lockedFillQty
			newStatus := "partial"
			if newFilledQty >= lockedBuy.Qty {
				newStatus = "filled"
			}

			if err := store.DeductBrokerInventory(tx, stock.ID, lockedFillQty); err != nil {
				tx.Rollback()
				return err
			}

			if err := tx.Model(&domain.Order{}).Where("id = ?", lockedBuy.ID).Updates(map[string]interface{}{
				"filled_qty": newFilledQty,
				"status":     newStatus,
			}).Error; err != nil {
				tx.Rollback()
				return err
			}

			if err := store.AddCash(tx, config.SystemBrokerID, fillAmountYuan); err != nil {
				tx.Rollback()
				return err
			}

			if err := store.UpdateStockFromTrade(tx, stock.ID, tradePrice); err != nil {
				tx.Rollback()
				return err
			}
			updateCandlesForTrade(tx, stock.ID, time.Now(), tradePrice, lockedFillQty)

			if err := tx.Commit().Error; err != nil {
				return err
			}

			bi.TotalQty -= lockedFillQty
			slog.Info("broker: trade committed", "stockID", stock.ID, "orderID", lockedBuy.ID, "price", tradePrice, "qty", lockedFillQty)

			if OnTradeExecuted != nil {
				OnTradeExecuted(lockedBuy.PlayerID, "")
			}
			if OnTradeRecorded != nil {
				OnTradeRecorded(stock.Symbol, tradePrice, lockedFillQty)
			}
			return nil
		}()

		if err != nil {
			slog.Error("broker: release failed", "stockID", stock.ID, "buyOrderID", buy.ID, "error", err)
		}
	}
}

func ensureBrokerPlayerState(db *gorm.DB) error {
	var count int64
	if err := db.Model(&domain.PlayerState{}).Where("player_id = ?", config.SystemBrokerID).Count(&count).Error; err != nil {
		return err
	}
	if count == 0 {
		return db.Create(&domain.PlayerState{
			PlayerID:   config.SystemBrokerID,
			Nickname:   "证券机构",
			Cash:       0,
			FrozenCash: 0,
		}).Error
	}
	return nil
}
