package handler

import (
	"math"
	"net/http"
	"sort"

	"jjs-server/internal/domain"
	"jjs-server/internal/engine"
	"jjs-server/internal/store"
)

type LeaderboardHandler struct{}

type playerLeaderboardEntry struct {
	Rank          int    `json:"rank"`
	PlayerID      string `json:"player_id"`
	Nickname      string `json:"nickname"`
	TotalAssets   int64  `json:"total_assets"`
	Cash          int64  `json:"cash"`
	FrozenCash    int64  `json:"frozen_cash"`
	HoldingsValue int64  `json:"holdings_value"`
}

type playerLeaderboardResponse struct {
	Players []playerLeaderboardEntry `json:"players"`
}

func (h *LeaderboardHandler) Players(w http.ResponseWriter, r *http.Request) {
	players, err := store.GetHumanPlayerStates()
	if err != nil {
		WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "获取玩家数据失败"})
		return
	}

	playerIDs := make([]string, len(players))
	for i, p := range players {
		playerIDs[i] = p.PlayerID
	}

	holdingsMap, err := store.GetHoldingsByPlayerIDs(playerIDs)
	if err != nil {
		holdingsMap = make(map[string][]domain.Holding)
	}

	stocks, err := store.ListStocks()
	stockPriceMap := make(map[uint]int64, len(stocks))
	if err == nil {
		for _, s := range stocks {
			if s.Status == "active" {
				stockPriceMap[s.ID] = s.CurrentPrice
			}
		}
	}

	entries := make([]playerLeaderboardEntry, 0, len(players))
	for _, p := range players {
		holdingsValueFen := int64(0)
		if hList, ok := holdingsMap[p.PlayerID]; ok {
			for _, h := range hList {
				if price, ok := stockPriceMap[h.StockID]; ok {
					holdingsValueFen += price * h.Qty
				}
			}
		}
		holdingsValue := holdingsValueFen / 100
		totalAssets := p.Cash + p.FrozenCash + holdingsValue - p.MarginDebt

		entries = append(entries, playerLeaderboardEntry{
			PlayerID:      p.PlayerID,
			Nickname:      p.Nickname,
			TotalAssets:   totalAssets,
			Cash:          p.Cash,
			FrozenCash:    p.FrozenCash,
			HoldingsValue: holdingsValue,
		})
	}

	sort.Slice(entries, func(i, j int) bool {
		return entries[i].TotalAssets > entries[j].TotalAssets
	})

	for i := range entries {
		entries[i].Rank = i + 1
	}

	WriteJSON(w, http.StatusOK, playerLeaderboardResponse{Players: entries})
}

type companyLeaderboardEntry struct {
	Rank       int     `json:"rank"`
	Symbol     string  `json:"symbol"`
	Name       string  `json:"name"`
	Industry   string  `json:"industry"`
	Valuation  float64 `json:"valuation"`
	Listed     bool    `json:"listed"`
	StockPrice float64 `json:"stock_price"`
}

type companyLeaderboardResponse struct {
	Companies []companyLeaderboardEntry `json:"companies"`
}

type stockBrief struct {
	CurrentPrice int64
	Status       string
}

func (h *LeaderboardHandler) Companies(w http.ResponseWriter, r *http.Request) {
	companies, err := store.GetActiveCompanies()
	if err != nil {
		WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "获取公司列表失败"})
		return
	}

	if len(companies) == 0 {
		WriteJSON(w, http.StatusOK, companyLeaderboardResponse{Companies: []companyLeaderboardEntry{}})
		return
	}

	companyIDs := make([]uint, len(companies))
	for i, c := range companies {
		companyIDs[i] = c.ID
	}

	quarterliesMap, err := store.GetQuarterliesByCompanyIDs(companyIDs, 4)
	if err != nil {
		quarterliesMap = make(map[uint][]domain.CompanyQuarterly)
	}

	stocks, _ := store.ListStocks()
	stockByCompany := make(map[uint]stockBrief, len(stocks))
	for i := range stocks {
		stockByCompany[stocks[i].CompanyID] = stockBrief{
			CurrentPrice: stocks[i].CurrentPrice,
			Status:       stocks[i].Status,
		}
	}

	entries := make([]companyLeaderboardEntry, 0, len(companies))
	for _, c := range companies {
		var valuation float64
		var listed bool
		var stockPrice float64

		stockInfo, hasStock := stockByCompany[c.ID]
		if hasStock && stockInfo.Status == "active" && c.IpoQuarter > 0 {
			listed = true
			marketCapFen := stockInfo.CurrentPrice * c.TotalShares
			valuation = float64(marketCapFen) / 100
			stockPrice = float64(stockInfo.CurrentPrice) / 100
		} else {
			listed = false
			cfg, ok := engine.Industries[c.Industry]
			if !ok {
				continue
			}

			totalAssets := float64(c.Cash) + float64(c.CapCount)*cfg.CapAssetValue
			nav := totalAssets / float64(c.TotalShares)

			var avgProfit float64
			if qs, ok := quarterliesMap[c.ID]; ok && len(qs) > 0 {
				for _, q := range qs {
					avgProfit += float64(q.Profit)
				}
				avgProfit /= float64(len(qs))
			}
			eps := avgProfit / float64(c.TotalShares)

			prosperity := 1.0
			if p, err := store.LatestProsperity(c.Industry); err == nil {
				prosperity = p
			}

			theoreticalPrice := math.Max(1, nav+eps*cfg.PE*prosperity)
			valuation = theoreticalPrice * float64(c.TotalShares)
		}

		entries = append(entries, companyLeaderboardEntry{
			Symbol:     c.Symbol,
			Name:       c.Name,
			Industry:   c.Industry,
			Valuation:  valuation,
			Listed:     listed,
			StockPrice: stockPrice,
		})
	}

	sort.Slice(entries, func(i, j int) bool {
		return entries[i].Valuation > entries[j].Valuation
	})

	for i := range entries {
		entries[i].Rank = i + 1
	}

	WriteJSON(w, http.StatusOK, companyLeaderboardResponse{Companies: entries})
}
