package bots

import (
	"sync"

	"jjs-server/internal/domain"
)

type BotMetrics struct {
	mu              sync.Mutex
	TotalSignals    int64
	TotalOrders     int64
	BuyOrders       int64
	SellOrders      int64
	StopLossExits   int64
	ActiveTraders   int
	DepletedTraders int
}

func (m *BotMetrics) Snapshot() map[string]interface{} {
	m.mu.Lock()
	defer m.mu.Unlock()
	return map[string]interface{}{
		"total_signals":    m.TotalSignals,
		"total_orders":     m.TotalOrders,
		"buy_orders":       m.BuyOrders,
		"sell_orders":      m.SellOrders,
		"stop_loss_exits":  m.StopLossExits,
		"active_traders":   m.ActiveTraders,
		"depleted_traders": m.DepletedTraders,
	}
}

func (m *BotMetrics) RecordSignal()       { m.mu.Lock(); m.TotalSignals++; m.mu.Unlock() }
func (m *BotMetrics) RecordOrder(side string) {
	m.mu.Lock()
	m.TotalOrders++
	if side == "buy" {
		m.BuyOrders++
	} else {
		m.SellOrders++
	}
	m.mu.Unlock()
}
func (m *BotMetrics) RecordStopLoss() { m.mu.Lock(); m.StopLossExits++; m.mu.Unlock() }
func (m *BotMetrics) SetTraders(active, depleted int) {
	m.mu.Lock()
	m.ActiveTraders = active
	m.DepletedTraders = depleted
	m.mu.Unlock()
}

type StockRef struct {
	ID           uint
	CurrentPrice int64
}

type TraderStats struct {
	ID            string  `json:"id"`
	Cash          int64   `json:"cash"`
	FrozenCash    int64   `json:"frozen_cash"`
	HoldingValue  int64   `json:"holding_value"`
	RiskTolerance float64 `json:"risk_tolerance"`
}

func GatherTraderStats(traders []*AiTrader, stocksByID map[uint]*domain.Stock) []TraderStats {
	psCache := sync.Map{}
	stats := make([]TraderStats, 0, len(traders))

	for _, t := range traders {
		psV, _ := psCache.LoadOrStore(t.ID, mustGetPs(t.ID))
		ps, _ := psV.(*domain.PlayerState)
		if ps == nil {
			continue
		}
		holdings, _ := mustGetHoldings(t.ID)
		holdingValue := int64(0)
		for _, h := range holdings {
			if s, ok := stocksByID[h.StockID]; ok {
				holdingValue += s.CurrentPrice * h.Qty
			}
		}
		stats = append(stats, TraderStats{
			ID:            t.ID,
			Cash:          ps.Cash,
			FrozenCash:    ps.FrozenCash,
			HoldingValue:  holdingValue,
			RiskTolerance: t.RiskTolerance,
		})
	}
	return stats
}
