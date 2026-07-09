package engine

import (
	"fmt"
	"log/slog"
	"math/rand"

	"jjs-server/internal/store"
)

// calcDeviation 将偏离 1.0 的程度归一化到 [-1, +1]。
// 由于边界非对称 (max = 1/min)，上方和下方分别用不同的分母归一化。
func calcDeviation(p, min, max float64) float64 {
	if p >= 1.0 {
		return (p - 1.0) / (max - 1.0) // [0, +1]
	}
	return (p - 1.0) / (1.0 - min) // [-1, 0)
}

func WalkProsperity(oldProsperity float64, cfg IndustryConfig) float64 {
	// 正态分布随机步长：大部分小波动，偶尔大波动
	rawStep := rand.NormFloat64() * cfg.ProsperityStdDev

	// 向心回归（非对称归一化）
	dev := calcDeviation(oldProsperity, cfg.ProsperityMin, cfg.ProsperityMax)
	regressionStep := -dev * cfg.ProsperityRegression

	// 修正脉冲：小概率，极端偏离时向中心猛拉
	if rand.Float64() < cfg.CorrectionProb {
		pulse := -dev * cfg.CorrectionPulse
		return clamp(oldProsperity+pulse, cfg.ProsperityMin, cfg.ProsperityMax)
	}

	// 步长 = 随机 + 回归，clamp 到单季硬上限
	change := clamp(rawStep+regressionStep, -cfg.ProsperityMaxStep, cfg.ProsperityMaxStep)

	return clamp(oldProsperity+change, cfg.ProsperityMin, cfg.ProsperityMax)
}

func clamp(v, lo, hi float64) float64 {
	if v < lo {
		return lo
	} else if v > hi {
		return hi
	}
	return v
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
