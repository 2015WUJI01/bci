package engine

import (
	"log/slog"
	"time"

	"jjs-server/internal/config"
	"jjs-server/internal/domain"
	"jjs-server/internal/store"
)

type TradingTicker struct {
	stopCh    chan struct{}
	tickCount int64
}

func NewTradingTicker() *TradingTicker {
	return &TradingTicker{}
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

	t.updateAllStockPrices()
	t.aggregateAllCandles()
}

func (t *TradingTicker) updateAllStockPrices() {
	stocks, err := store.ListStocks()
	if err != nil {
		return
	}

	for _, s := range stocks {
		if s.PrevClose <= 0 {
			continue
		}
		change := s.CurrentPrice - s.PrevClose
		changePct := float64(0)
		if s.PrevClose > 0 {
			changePct = float64(change) / float64(s.PrevClose) * 100
		}
		if change == s.Change && changePct == s.ChangePercent {
			continue
		}
		store.DB.Model(&domain.Stock{}).Where("id = ?", s.ID).Updates(map[string]interface{}{
			"change":         change,
			"change_percent": changePct,
		})
	}
}

func (t *TradingTicker) aggregateAllCandles() {
	stocks, err := store.ListStocks()
	if err != nil {
		return
	}

	for _, s := range stocks {
		if s.CurrentPrice <= 0 {
			continue
		}
		for _, period := range []struct {
			name    string
			seconds int64
		}{
			{"40t", 80},
			{"150t", 300},
			{"600t", 1200},
		} {
			openTime := candleOpenTime(time.Now(), period.seconds)
			if err := store.UpsertCandle(s.ID, period.name, openTime, s.CurrentPrice, 0); err != nil {
				slog.Error("candle upsert failed", "stockID", s.ID, "period", period.name, "error", err)
			}
		}
	}
}

func candleOpenTime(t time.Time, periodSecs int64) time.Time {
	unix := t.Unix()
	return time.Unix(unix-(unix%periodSecs), 0).UTC()
}
