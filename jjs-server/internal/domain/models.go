package domain

import (
	"time"

	"gorm.io/gorm"
)

type User struct {
	ID           string    `gorm:"type:varchar(12);primaryKey"`
	Username     string    `gorm:"type:varchar(50);uniqueIndex;not null"`
	Nickname     string    `gorm:"type:varchar(20);not null;default:''"`
	PasswordHash string    `gorm:"type:varchar(128);not null;default:''"`
	IsAdmin      bool      `gorm:"not null;default:false"`
	CreatedAt    time.Time `gorm:"autoCreateTime"`
	UpdatedAt    time.Time `gorm:"autoUpdateTime"`
}

type Transaction struct {
	ID        uint      `gorm:"primaryKey;autoIncrement"`
	PlayerID  string    `gorm:"type:varchar(12);index:idx_transactions_player;not null"`
	Symbol    string    `gorm:"type:varchar(10);not null"`
	TradeType string    `gorm:"type:varchar(10);not null;check:trade_type IN ('buy','sell','short_sell','cover')"`
	Quantity  int64     `gorm:"not null"`
	Price     float64   `gorm:"not null"`
	Total     float64   `gorm:"not null"`
	CreatedAt time.Time `gorm:"autoCreateTime"`
}

type PlayerState struct {
	PlayerID   string  `gorm:"type:varchar(12);primaryKey"`
	Nickname   string  `gorm:"type:varchar(50);not null;default:''"`
	Cash       float64 `gorm:"not null;default:0"`
	FrozenCash float64 `gorm:"not null;default:0"`
	MarginDebt float64 `gorm:"not null;default:0"`
}

type Holding struct {
	ID           uint    `gorm:"primaryKey;autoIncrement"`
	PlayerID     string  `gorm:"type:varchar(12);index:idx_holdings_player;not null;uniqueIndex:uq_player_symbol"`
	Symbol       string  `gorm:"type:varchar(10);not null;uniqueIndex:uq_player_symbol"`
	Qty          int64   `gorm:"not null;default:0"`
	AvgCost      float64 `gorm:"not null;default:0"`
	FrozenQty    int64   `gorm:"not null;default:0"`
	ShortQty     int64   `gorm:"not null;default:0"`
	ShortAvgCost float64 `gorm:"not null;default:0"`
}

type Company struct {
	gorm.Model
	PlayerID string `gorm:"type:varchar(12);uniqueIndex;not null"`
	Name     string `gorm:"type:varchar(50);not null"`
	Symbol   string `gorm:"type:varchar(10);unique;not null"`
	Industry string `gorm:"type:varchar(20);not null;index:idx_company_industry"`

	Cash             float64 `gorm:"not null;default:100000"`
	TotalAssets      float64 `gorm:"not null;default:100000"`
	Revenue          float64 `gorm:"not null;default:0"`
	Profit           float64 `gorm:"not null;default:0"`
	Employees        int     `gorm:"not null;default:10"`
	Quarter          int     `gorm:"not null;default:1"`
	SharePrice       float64 `gorm:"not null;default:10"`
	SharesOutstanding int64  `gorm:"not null;default:10000000"`

	TechPoints      float64 `gorm:"not null;default:0"`
	CurrentStrategy string  `gorm:"type:varchar(20);not null;default:'balanced'"`
	AllocPcts       string  `gorm:"type:varchar(200);not null;default:'{\"reserve\":25,\"sales\":25,\"dividend\":25,\"research\":25}'"`

	// --- v2 fields (P2 启用) ---

	AP    int `gorm:"not null;default:3"`
	APCap int `gorm:"not null;default:3"`

	BoardSatisfaction  float64 `gorm:"not null;default:50"`
	KpiType            string  `gorm:"type:varchar(20);default:''"`
	KpiTarget          float64 `gorm:"not null;default:0"`
	ProtectionQuarters int     `gorm:"not null;default:8"`

	TechLevel       int    `gorm:"not null;default:0"`
	ActionCooldowns string `gorm:"type:text"`
	MergerCount     int    `gorm:"not null;default:0"`
	SharesIssued    bool   `gorm:"not null;default:false"`

	IndustryCycle string `gorm:"type:varchar(10);not null;default:'normal'"`
}

type CompanyQuarterly struct {
	ID           uint      `gorm:"primaryKey;autoIncrement"`
	CompanyID    uint      `gorm:"index;not null"`
	Quarter      int       `gorm:"not null"`
	Period       string    `gorm:"type:varchar(20);not null"`
	Revenue      float64   `gorm:"not null;default:0"`
	Profit       float64   `gorm:"not null;default:0"`
	Assets       float64   `gorm:"not null;default:0"`
	Cash         float64   `gorm:"not null;default:0"`
	Employees    int       `gorm:"not null;default:0"`
	SharePrice   float64   `gorm:"not null;default:0"`
	SalaryCost   float64   `gorm:"not null;default:0"`
	RdSpend      float64   `gorm:"not null;default:0"`
	FixedCost    float64   `gorm:"not null;default:0"`
	DividendPaid float64   `gorm:"not null;default:0"`
	IndustryCycle string  `gorm:"type:varchar(10);not null;default:'normal'"`
	PrevRevenue  float64   `gorm:"not null;default:0"`
	PrevProfit   float64   `gorm:"not null;default:0"`
	CycleMult    float64   `gorm:"not null;default:1"`
	BaseRevenue  float64   `gorm:"not null;default:0"`
	InterestIncome float64 `gorm:"not null;default:0"`
	MarketCondition float64 `gorm:"not null;default:0"`
	CreatedAt    time.Time `gorm:"autoCreateTime"`
}

type AssetLog struct {
	ID        uint      `gorm:"primaryKey;autoIncrement"`
	PlayerID  string    `gorm:"type:varchar(12);index;not null"`
	Type      string    `gorm:"type:varchar(20);not null"`
	Amount    float64   `gorm:"not null"`
	Balance   float64   `gorm:"not null"`
	Note      string    `gorm:"type:varchar(200);default:''"`
	CreatedAt time.Time `gorm:"autoCreateTime"`
}

func (Company) TableName() string         { return "companies" }
func (CompanyQuarterly) TableName() string { return "company_quarterly" }
func (PlayerState) TableName() string      { return "player_state" }
func (Holding) TableName() string          { return "holdings" }
func (Transaction) TableName() string      { return "transactions" }
func (AssetLog) TableName() string         { return "asset_logs" }
