package bots

import (
	"log/slog"
	"math"
	"math/rand"
	"sync"
	"time"

	"gorm.io/gorm"

	"jjs-server/internal/config"
	"jjs-server/internal/domain"
	"jjs-server/internal/engine"
	"jjs-server/internal/store"
)

type Scheduler struct {
	traders    []*AiTrader
	mu         sync.Mutex
	metrics    *BotMetrics
	tickCount  int64
	PlaceOrder func(order *domain.Order) error
}

func NewScheduler(traders []*AiTrader) *Scheduler {
	return &Scheduler{
		traders: traders,
		metrics: &BotMetrics{},
	}
}

func (s *Scheduler) ScheduleTick(db *gorm.DB, stocks []domain.Stock) {
	start := time.Now()
	s.tickCount++

	s.mu.Lock()
	var ready []*AiTrader
	for _, t := range s.traders {
		if t.CoolDownLeft > 0 {
			t.CoolDownLeft--
		}
		if t.CoolDownLeft == 0 {
			ready = append(ready, t)
		}
	}
	s.mu.Unlock()

	if len(ready) == 0 {
		return
	}

	companies, err := store.GetActiveCompanies()
	if err != nil {
		return
	}
	companyByID := make(map[uint]*domain.Company, len(companies))
	companyIDs := make([]uint, 0, len(companies))
	for i := range companies {
		companyByID[companies[i].ID] = &companies[i]
		companyIDs = append(companyIDs, companies[i].ID)
	}

	prosperityCache := make(map[string]float64)
	var prospMu sync.Mutex

	quarterlies, _ := store.GetQuarterliesByCompanyIDs(companyIDs, 8)

	stockByID := make(map[uint]*domain.Stock, len(stocks))
	activeStocks := make([]*domain.Stock, 0, len(stocks))
	for i := range stocks {
		if stocks[i].CurrentPrice > 0 {
			stockByID[stocks[i].ID] = &stocks[i]
			activeStocks = append(activeStocks, &stocks[i])
		}
	}

	if len(activeStocks) == 0 {
		return
	}

	readyIDs := make([]string, len(ready))
	for i, t := range ready {
		readyIDs[i] = t.ID
	}

	playerStates, _ := store.GetPlayerStatesByIDs(readyIDs)
	allHoldings, _ := store.GetHoldingsByPlayerIDs(readyIDs)
	allOpenOrders, _ := store.GetOpenOrdersByPlayerIDs(readyIDs)

	depleted := 0
	for _, trader := range ready {
		openOrders := allOpenOrders[trader.ID]
		for _, o := range openOrders {
			st, ok := stockByID[o.StockID]
			if !ok || st.CurrentPrice <= 0 {
				engine.CancelOrder(db, o.ID, trader.ID)
				continue
			}
			if time.Since(o.CreatedAt) > config.AiTraderCancelMaxAge {
				engine.CancelOrder(db, o.ID, trader.ID)
				continue
			}
			if o.Side == "buy" {
				gap := float64(st.CurrentPrice-o.Price) / float64(st.CurrentPrice)
				if gap > config.AiTraderCancelDevThreshold {
					engine.CancelOrder(db, o.ID, trader.ID)
				}
			} else {
				gap := float64(o.Price-st.CurrentPrice) / float64(st.CurrentPrice)
				if gap > config.AiTraderCancelDevThreshold {
					engine.CancelOrder(db, o.ID, trader.ID)
				}
			}
		}

		if rand.Float64() < config.AiTraderSkipProbability {
			trader.CoolDownLeft = trader.CooldownTicks
			continue
		}

		sampled := sampleStocks(activeStocks)
		if sampled == nil {
			continue
		}

		ps, ok := playerStates[trader.ID]
		if !ok {
			continue
		}
		holdings := allHoldings[trader.ID]
		holdingMap := make(map[uint]*domain.Holding, len(holdings))
		for i := range holdings {
			holdingMap[holdings[i].StockID] = &holdings[i]
		}

		for _, stock := range sampled {
			if stock.CurrentPrice <= 0 {
				continue
			}

			if h, ok := holdingMap[stock.ID]; ok {
				stopOrderFunc := func(order *domain.Order) error {
					_, err := engine.ExecuteOrderWithStock(db, order, stock)
					return err
				}
				if CheckStopLoss(stopOrderFunc, trader, stock, h) {
					s.metrics.RecordStopLoss()
					continue
				}
			}

			company, ok := companyByID[stock.CompanyID]
			if !ok {
				continue
			}

			indCfg, ok := engine.Industries[company.Industry]
			if !ok {
				continue
			}

			prospMu.Lock()
			prosperity, exists := prosperityCache[company.Industry]
			if !exists {
				p, err := store.LatestProsperity(company.Industry)
				if err == nil {
					prosperity = p
				} else {
					prosperity = 1.0
				}
				prosperityCache[company.Industry] = prosperity
			}
			prospMu.Unlock()

			stockQuarterlies := quarterlies[company.ID]

			expectedPrice := float64(expectedPriceCents(company, stockQuarterlies, &indCfg, prosperity))
			ratio := float64(stock.CurrentPrice) / expectedPrice
			buyProb := buyProbability(ratio)

			s.metrics.RecordSignal()

			var order *domain.Order
			if rand.Float64() < buyProb {
				order = buildBuyOrderV2(trader, stock, ps, expectedPrice)
			} else {
				order = buildSellOrderV2(trader, stock, expectedPrice, holdingMap)
			}

			if order == nil {
				continue
			}

			if _, err := engine.ExecuteOrderWithStock(db, order, stock); err != nil {
				slog.Debug("bot order failed", "bot", trader.ID, "stock", stock.Symbol, "error", err)
				continue
			}
			s.metrics.RecordOrder(order.Side)
		}

		trader.CoolDownLeft = trader.CooldownTicks

		holdingValue := int64(0)
		for _, h := range holdings {
			if s, ok := stockByID[h.StockID]; ok {
				holdingValue += s.CurrentPrice * h.Qty
			}
		}
		if ps.Cash < config.AiTraderExitCash && holdingValue == 0 {
			depleted++
		}
	}

	s.metrics.SetTraders(len(s.traders), depleted)

	if s.tickCount%config.AiTraderResupplyInterval == 0 {
		CheckAndReplenish(db, s.traders)
	}

	elapsed := time.Since(start).Microseconds()
	if elapsed > 1_000_000 {
		slog.Warn("AI tick slow", "us", elapsed)
	}
}

func sampleStocks(stocks []*domain.Stock) []*domain.Stock {
	if len(stocks) == 0 {
		return nil
	}
	n := int(math.Ceil(float64(len(stocks)) * config.AiTraderSampleRatio))
	if n > 20 {
		n = 20
	}
	minStocks := config.AiTraderMinStocks
	if len(stocks) < 15 && minStocks > len(stocks) {
		minStocks = len(stocks)
	}
	if n < minStocks {
		n = minStocks
	}
	if n > len(stocks) {
		n = len(stocks)
	}

	perm := rand.Perm(len(stocks))
	result := make([]*domain.Stock, n)
	for i := 0; i < n; i++ {
		result[i] = stocks[perm[i]]
	}
	return result
}

func (s *Scheduler) Metrics() *BotMetrics {
	return s.metrics
}

func (s *Scheduler) GatherTraderStats(stocksByID map[uint]*StockRef) []TraderStats {
	s.mu.Lock()
	defer s.mu.Unlock()

	domainStocks := make(map[uint]*domain.Stock, len(stocksByID))
	for id, ref := range stocksByID {
		domainStocks[id] = &domain.Stock{ID: ref.ID, CurrentPrice: ref.CurrentPrice}
	}
	return GatherTraderStats(s.traders, domainStocks)
}
