package config

import (
	"time"

	"github.com/kelseyhightower/envconfig"
)

type Config struct {
	MySQLDSN     string `envconfig:"MYSQL_DSN" default:"root:root@tcp(127.0.0.1:3306)/jjs?charset=utf8mb4&parseTime=True&loc=Local"`
	JWTSecret    string `envconfig:"JWT_SECRET" default:"jjs-dev-secret-change-in-production"`
	JWTExpire    string `envconfig:"JWT_EXPIRE" default:"168h"`
	Port         string `envconfig:"PORT" default:"8080"`
	FrontendDir  string `envconfig:"FRONTEND_DIR" default:"web"`
}

var AppConfig Config

func Load() error {
	return envconfig.Process("", &AppConfig)
}

// --- 游戏常量（从 config.py 迁移） ---

const (
	StartingCash          = 10_000.0
	PriceTickInterval     = 1500 * time.Millisecond
	LeaderboardInterval   = 7500 * time.Millisecond
	DBFlushInterval       = 30 * time.Second
	PriceMin              = 0.0001
	PriceMax              = 1_000_000.0
	SharesOutstanding     = 500_000_000
	MaxPositionPerPlayer  = SharesOutstanding * 0.05
	MaxOrderQty           = SharesOutstanding * 0.01
	InitialPrice          = 100.0

	StampTaxRate      = 0.001
	CommissionRate    = 0.00025
	MinCommission     = 5.0
	ShortSellFeeRate  = 0.000003
	MarginInterestRate = 0.000003
	MarginMinAssets   = 1_000_000

	MaxNicknameLen = 20
	MinPasswordLen = 3
)
