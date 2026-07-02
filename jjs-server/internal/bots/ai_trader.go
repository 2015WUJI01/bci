package bots

import (
	"fmt"
	"math"
	"math/rand"
	"time"

	"jjs-server/internal/config"
	"jjs-server/internal/domain"
	"jjs-server/internal/engine"
	"jjs-server/internal/store"
)

type AiTrader struct {
	ID            string
	CooldownTicks int
	RiskTolerance float64
	CoolDownLeft  int
	SpawnedAt     time.Time
}

func InitTraders() []*AiTrader {
	traders := make([]*AiTrader, 0, config.AiTraderCount)
	for i := 0; i < config.AiTraderCount; i++ {
		id := fmt.Sprintf("bot_%04d", i+1)
		trader := &AiTrader{
			ID:            id,
			CooldownTicks: randomIntRange(config.AiTraderCooldownMin, config.AiTraderCooldownMax),
			RiskTolerance: randomTolerance(),
			CoolDownLeft:  0,
			SpawnedAt:     time.Now(),
		}
		traders = append(traders, trader)

		cash := randomRange(config.AiTraderInitCashMin, config.AiTraderInitCashMax)
		store.GetOrCreatePlayerState(id, id)

		orders, err := store.GetOpenOrdersByPlayer(id)
		if err == nil {
			for _, o := range orders {
				engine.CancelOrderTx(store.DB, o.ID, id)
			}
		}

		store.DB.Model(&domain.PlayerState{}).Where("player_id = ?", id).
			Updates(map[string]interface{}{"cash": cash, "frozen_cash": 0})
	}
	return traders
}

func newTraderParams() (int, float64) {
	return randomIntRange(config.AiTraderCooldownMin, config.AiTraderCooldownMax), randomTolerance()
}

func randomRange(min, max int64) int64 {
	if max <= min {
		return min
	}
	return min + rand.Int63n(max-min+1)
}

func randomIntRange(min, max int) int {
	if max <= min {
		return min
	}
	return min + rand.Intn(max-min+1)
}

func randomFloatRange(min, max float64) float64 {
	return min + rand.Float64()*(max-min)
}

func randomTolerance() float64 {
	return config.AiTraderRiskToleranceMin + rand.Float64()*(config.AiTraderRiskToleranceMax-config.AiTraderRiskToleranceMin)
}

func clamp(v, lo, hi float64) float64 {
	return math.Max(lo, math.Min(hi, v))
}
