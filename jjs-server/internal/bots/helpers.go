package bots

import (
	"math"
	"math/rand"

	"jjs-server/internal/config"
	"jjs-server/internal/domain"
	"jjs-server/internal/engine"
	"jjs-server/internal/store"
)

func expectedPriceCents(company *domain.Company, quarters []domain.CompanyQuarterly, indCfg *engine.IndustryConfig, prosperity float64) int64 {
	nav := float64(company.Cash) + float64(company.CapCount)*indCfg.CapAssetValue
	liquidationPerShare := nav * config.AiTraderLiquidationRatio / float64(company.TotalShares) * prosperity * 100

	totalProfit := int64(0)
	profitQuarters := 0
	for i := 0; i < len(quarters) && i < 4; i++ {
		totalProfit += quarters[i].Profit
		profitQuarters++
	}
	annualEPS := 0.0
	if profitQuarters > 0 && company.TotalShares > 0 {
		annualEPS = float64(totalProfit) / float64(company.TotalShares)
	}
	earningPerShare := annualEPS * indCfg.PE * prosperity * 100

	raw := math.Max(liquidationPerShare, math.Max(earningPerShare, 1.0))
	jitter := 1.0 + (rand.Float64()*2-1)*config.AiTraderPriceJitter
	return int64(raw * jitter)
}

func buyProbability(ratio float64) float64 {
	if ratio <= 0.5 {
		return 0.9
	}
	if ratio <= 1.0 {
		return 0.9 - (ratio-0.5)/0.5*0.4
	}
	if ratio < 2.0 {
		return 0.5 - (ratio-1.0)/1.0*0.4
	}
	return 0.1
}

func quotePriceFactor(currentPrice int64, expectedPrice float64) (float64, float64) {
	if float64(currentPrice) < expectedPrice {
		return 0.9, 1.2
	}
	return 0.8, 1.1
}

func randomQuotePrice(currentPrice int64, expectedPrice float64) int64 {
	lo, hi := quotePriceFactor(currentPrice, expectedPrice)
	factor := lo + rand.Float64()*(hi-lo)
	price := int64(float64(currentPrice) * factor)
	if price < 1 {
		price = 1
	}
	return price
}

func buildBuyOrderV2(trader *AiTrader, stock *domain.Stock, ps *domain.PlayerState, expectedPrice float64) *domain.Order {
	availableCash := ps.Cash - ps.FrozenCash
	if availableCash <= 0 {
		return nil
	}

	price := randomQuotePrice(stock.CurrentPrice, expectedPrice)

	maxSpend := int64(float64(availableCash) * trader.RiskTolerance)
	qty := maxSpend / price
	if qty < 100 {
		return nil
	}
	if qty > config.MaxOrderQty {
		qty = config.MaxOrderQty
	}

	return &domain.Order{
		StockID:  stock.ID,
		PlayerID: trader.ID,
		Type:     "limit",
		Side:     "buy",
		Price:    price,
		Qty:      qty,
	}
}

func buildSellOrderV2(trader *AiTrader, stock *domain.Stock, expectedPrice float64, holdingMap map[uint]*domain.Holding) *domain.Order {
	holding, ok := holdingMap[stock.ID]
	if !ok || holding == nil || holding.Qty-holding.FrozenQty < 100 {
		return nil
	}

	availableQty := holding.Qty - holding.FrozenQty
	maxSell := int64(float64(availableQty) * trader.RiskTolerance)
	if maxSell < 100 {
		return nil
	}
	if maxSell > config.MaxOrderQty {
		maxSell = config.MaxOrderQty
	}

	price := randomQuotePrice(stock.CurrentPrice, expectedPrice)

	return &domain.Order{
		StockID:  stock.ID,
		PlayerID: trader.ID,
		Type:     "limit",
		Side:     "sell",
		Price:    price,
		Qty:      maxSell,
	}
}

func mustGetPs(playerID string) *domain.PlayerState {
	ps, _ := store.GetPlayerState(playerID)
	return ps
}

func mustGetPlayerState(playerID string) (*domain.PlayerState, error) {
	return store.GetPlayerState(playerID)
}

func mustGetHoldings(playerID string) ([]domain.Holding, error) {
	return store.GetHoldingsByPlayer(playerID)
}
