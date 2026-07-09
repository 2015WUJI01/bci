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

// aggregateAllCandles 收集所有活跃股票 × 3 个周期（15t/60t/150t）的当前价格，
// 通过 BulkUpsertCandles 一次批量 upsert 全部 candle 数据，替代原有的逐股票逐周期
// UpsertCandle 循环调用。将 N×3×2 次 DB 往返压缩为 2 次（1 upsert + 1 select）。
//
// 返回 stockID → period → Candle 的二级 map，供 WebSocket PriceUpdate 广播使用。
func (t *TradingTicker) aggregateAllCandles(stocks []domain.Stock) map[uint]map[string]domain.Candle {
	periods := []struct {
		name    string
		seconds int64
	}{
		{"15t", 30},
		{"60t", 120},
		{"150t", 300},
	}

	now := time.Now()
	openTimes := make([]time.Time, len(periods))
	for i, p := range periods {
		openTimes[i] = candleOpenTime(now, p.seconds)
	}

	// 收集全部 stock×period 组合，一次调用批量写入
	ticks := make([]store.CandleTick, 0, len(stocks)*len(periods))
	for _, s := range stocks {
		if s.CurrentPrice <= 0 {
			continue
		}
		for i, p := range periods {
			ticks = append(ticks, store.CandleTick{
				StockID:  s.ID,
				Period:   p.name,
				OpenTime: openTimes[i],
				Price:    s.CurrentPrice,
			})
		}
	}

	candlesByStock, err := store.BulkUpsertCandles(ticks)
	if err != nil {
		slog.Error("bulk candle upsert failed", "error", err)
		return make(map[uint]map[string]domain.Candle)
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
