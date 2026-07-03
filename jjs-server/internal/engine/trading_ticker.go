package engine

import (
	"log/slog"
	"time"

	"gorm.io/gorm"

	"jjs-server/internal/config"
	"jjs-server/internal/domain"
	"jjs-server/internal/store"
	"jjs-server/internal/ws"
)

type BotRunner interface {
	ScheduleTick(db *gorm.DB, stocks []domain.Stock)
}

type TradingTicker struct {
	stopCh    chan struct{}
	tickCount int64
	hub       *ws.Hub
	botRunner BotRunner
}

func NewTradingTicker() *TradingTicker {
	return &TradingTicker{}
}

func (t *TradingTicker) SetHub(h *ws.Hub) {
	t.hub = h
}

func (t *TradingTicker) SetBotRunner(b BotRunner) {
	t.botRunner = b
}

func (t *TradingTicker) Start() {
	t.stopCh = make(chan struct{})
	go t.run()
	slog.Info("trading ticker started", "interval", config.PriceTickInterval)
}

func (t *TradingTicker) Stop() {
	close(t.stopCh)
	slog.Info("trading ticker stopped")
}

func (t *TradingTicker) run() {
	ticker := time.NewTicker(config.PriceTickInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			t.onTick()
		case <-t.stopCh:
			return
		}
	}
}

func (t *TradingTicker) onTick() {
	t.tickCount++

	if t.tickCount%config.BrokerScanTicks == 0 {
		go ReleaseBrokerInventory(store.DB)
	}

	stocks, err := store.ListStocks()
	if err != nil {
		return
	}

	candlesByStock := t.aggregateAllCandles(stocks)

	if t.botRunner != nil {
		t.botRunner.ScheduleTick(store.DB, stocks)
	}

	if t.hub != nil {
		t.broadcastPriceUpdate(stocks, candlesByStock)
		t.broadcastOrderBooks(stocks)
	}
}

func (t *TradingTicker) broadcastPriceUpdate(stocks []domain.Stock, candlesByStock map[uint]map[string]domain.Candle) {
	companies, err := store.GetActiveCompanies()
	if err != nil {
		return
	}

	companyMap := make(map[string]*domain.Company, len(companies))
	for i := range companies {
		companyMap[companies[i].Symbol] = &companies[i]
	}

	msg := ws.BuildPriceUpdate(stocks, companyMap, t.tickCount, candlesByStock)
	t.hub.Broadcast(msg)
}

func (t *TradingTicker) aggregateAllCandles(stocks []domain.Stock) map[uint]map[string]domain.Candle {
	candlesByStock := make(map[uint]map[string]domain.Candle, len(stocks))

	for _, s := range stocks {
		if s.CurrentPrice <= 0 {
			continue
		}
		periodCandles := make(map[string]domain.Candle, 3)
		for _, period := range []struct {
			name    string
			seconds int64
		}{
			{"15t", 30},
			{"60t", 120},
			{"150t", 300},
		} {
			openTime := candleOpenTime(time.Now(), period.seconds)
			candle, err := store.UpsertCandle(s.ID, period.name, openTime, s.CurrentPrice, 0)
			if err != nil {
				slog.Error("candle upsert failed", "stockID", s.ID, "period", period.name, "error", err)
				continue
			}
			periodCandles[period.name] = candle
		}
		candlesByStock[s.ID] = periodCandles
	}
	return candlesByStock
}

func candleOpenTime(t time.Time, periodSecs int64) time.Time {
	unix := t.Unix()
	return time.Unix(unix-(unix%periodSecs), 0).UTC()
}

func (t *TradingTicker) broadcastOrderBooks(stocks []domain.Stock) {
	stockIDs := make([]uint, 0, len(stocks))
	for _, s := range stocks {
		stockIDs = append(stockIDs, s.ID)
	}

	allBooks, err := store.GetAllOrderBooks(stockIDs)
	if err != nil {
		return
	}

	books := make(map[string]struct {
		Bids []store.OrderBookLevel
		Asks []store.OrderBookLevel
	}, len(stocks))
	for _, s := range stocks {
		if ob, ok := allBooks[s.ID]; ok {
			books[s.Symbol] = struct {
				Bids []store.OrderBookLevel
				Asks []store.OrderBookLevel
			}{ob.Bids, ob.Asks}
		}
	}
	if len(books) == 0 {
		return
	}
	msg := ws.BuildOrderBookSnapshot(books)
	t.hub.Broadcast(msg)
}
