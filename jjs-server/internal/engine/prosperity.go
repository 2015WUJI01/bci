package engine

import (
	"fmt"
	"log/slog"
	"math"
	"math/rand"

	"jjs-server/internal/store"
)

func WalkProsperity(oldProsperity float64, cfg IndustryConfig) float64 {
	halfRange := (cfg.ProsperityMax - cfg.ProsperityMin) / 2

	// deviation from center (1.0), normalized to [-1, +1]
	deviation := (oldProsperity - 1.0) / halfRange

	// regression strength proportional to how far from center
	regressionShare := math.Abs(deviation) * cfg.ProsperityRegression
	randomShare := 1.0 - regressionShare

	// random walk: random(-maxStep, +maxStep) * randomShare
	randomStep := (rand.Float64()*2 - 1) * cfg.ProsperityMaxStep * randomShare

	// regression pull towards 1.0: -deviation * maxStep * regressionShare
	regressionStep := -deviation * cfg.ProsperityMaxStep * regressionShare

	change := randomStep + regressionStep

	// clamp change to [-maxStep, +maxStep]
	if change > cfg.ProsperityMaxStep {
		change = cfg.ProsperityMaxStep
	} else if change < -cfg.ProsperityMaxStep {
		change = -cfg.ProsperityMaxStep
	}

	newProsperity := oldProsperity + change

	// clamp final value to [min, max]
	if newProsperity > cfg.ProsperityMax {
		newProsperity = cfg.ProsperityMax
	} else if newProsperity < cfg.ProsperityMin {
		newProsperity = cfg.ProsperityMin
	}

	return newProsperity
}

func RestoreOrSeedGlobalQuarter() error {
	maxQ, err := store.MaxProsperityQuarter()
	if err != nil {
		return fmt.Errorf("get max prosperity quarter: %w", err)
	}

	if maxQ == 0 {
		for id := range Industries {
			if err := store.SaveProsperity(id, 1, 1.0); err != nil {
				return fmt.Errorf("save initial prosperity for %s: %w", id, err)
			}
		}
		GlobalQuarter.Store(1)
		slog.Info("seeded initial prosperity", "quarter", 1)
	} else {
		GlobalQuarter.Store(int64(maxQ))
		slog.Info("restored global quarter from DB", "quarter", maxQ)
	}

	return nil
}
