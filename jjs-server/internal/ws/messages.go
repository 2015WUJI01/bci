package ws

import (
	"encoding/json"
	"time"

	"jjs-server/internal/domain"
	"jjs-server/internal/store"
)

type wsEnvelope struct {
	Type string      `json:"type"`
	Data interface{} `json:"data"`
}

type candleSnapshot struct {
	Time   int64 `json:"time"`
	Open   int64 `json:"open"`
	High   int64 `json:"high"`
	Low    int64 `json:"low"`
	Close  int64 `json:"close"`
	Volume int64 `json:"volume"`
}

type stockSnapshot struct {
	Symbol            string                     `json:"symbol"`
	Name              string                     `json:"name"`
	Price             int64                      `json:"price"`
	Change            int64                      `json:"change"`
	ChangePercent     float64                    `json:"changePercent"`
	MarketCap         int64                      `json:"marketCap"`
	SharesOutstanding int64                      `json:"sharesOutstanding"`
	Candles           map[string]candleSnapshot  `json:"candles"`
}

type portfolioHolding struct {
	Symbol       string  `json:"symbol"`
	Name         string  `json:"name"`
	Qty          int64   `json:"qty"`
	CostPrice    int64   `json:"costPrice"`
	CurrentPrice int64   `json:"currentPrice"`
	MarketValue  int64   `json:"marketValue"`
	Pnl          int64   `json:"pnl"`
	PnlPercent   float64 `json:"pnlPercent"`
}

type portfolioData struct {
	Cash       int64             `json:"cash"`
	FrozenCash int64             `json:"frozenCash"`
	Holdings   []portfolioHolding `json:"holdings"`
}

func BuildPriceUpdate(stocks []domain.Stock, companyMap map[string]*domain.Company, tick int64, candlesByStock map[uint]map[string]domain.Candle) []byte {
	data := make(map[string]interface{}, len(stocks)+1)
	for _, s := range stocks {
		name := s.Symbol
		shares := int64(0)
		if c, ok := companyMap[s.Symbol]; ok {
			name = c.Name
			shares = c.TotalShares
		}
		change := int64(0)
		changePct := float64(0)
		if s.PrevClose > 0 {
			change = s.CurrentPrice - s.PrevClose
			changePct = float64(change) / float64(s.PrevClose) * 100
		}

		snapshot := stockSnapshot{
			Symbol:            s.Symbol,
			Name:              name,
			Price:             s.CurrentPrice,
			Change:            change,
			ChangePercent:     changePct,
			MarketCap:         s.CurrentPrice * shares,
			SharesOutstanding: shares,
			Candles:           make(map[string]candleSnapshot),
		}
		if candlesByStock != nil {
			if pc, ok := candlesByStock[s.ID]; ok {
				for period, c := range pc {
					snapshot.Candles[period] = candleSnapshot{
						Time:   c.OpenTime.Unix(),
						Open:   c.Open,
						High:   c.High,
						Low:    c.Low,
						Close:  c.Close,
						Volume: c.Volume,
					}
				}
			}
		}
		data[s.Symbol] = snapshot
	}
	data["tick"] = tick

	msg, _ := json.Marshal(wsEnvelope{Type: "price_update", Data: data})
	return msg
}

func BuildPortfolioUpdate(cash, frozenCash int64, holdings []domain.Holding, stocks map[uint]*domain.Stock, companyMap map[string]*domain.Company) []byte {
	items := make([]portfolioHolding, 0, len(holdings))
	for _, h := range holdings {
		stock, ok := stocks[h.StockID]
		if !ok {
			continue
		}
		name := stock.Symbol
		if c, ok := companyMap[stock.Symbol]; ok {
			name = c.Name
		}
		marketValue := stock.CurrentPrice * h.Qty
		pnl := (stock.CurrentPrice - h.AvgCost) * h.Qty
		pnlPct := float64(0)
		if h.AvgCost > 0 {
			pnlPct = float64(stock.CurrentPrice-h.AvgCost) / float64(h.AvgCost) * 100
		}
		items = append(items, portfolioHolding{
			Symbol:       stock.Symbol,
			Name:         name,
			Qty:          h.Qty,
			CostPrice:    h.AvgCost,
			CurrentPrice: stock.CurrentPrice,
			MarketValue:  marketValue,
			Pnl:          pnl,
			PnlPercent:   pnlPct,
		})
	}
	if items == nil {
		items = []portfolioHolding{}
	}

	msg, _ := json.Marshal(wsEnvelope{
		Type: "portfolio_update",
		Data: portfolioData{
			Cash:       cash,
			FrozenCash: frozenCash,
			Holdings:   items,
		},
	})
	return msg
}

type obLevel struct {
	Price  int64 `json:"price"`
	Volume int64 `json:"volume"`
}

type obPerStock struct {
	Bids []obLevel `json:"bids"`
	Asks []obLevel `json:"asks"`
}

func BuildOrderBookSnapshot(books map[string]struct {
	Bids []store.OrderBookLevel
	Asks []store.OrderBookLevel
}) []byte {
	data := make(map[string]obPerStock, len(books))
	for symbol, book := range books {
		bids := make([]obLevel, len(book.Bids))
		for i, b := range book.Bids {
			bids[i] = obLevel{Price: b.Price, Volume: b.Volume}
		}
		asks := make([]obLevel, len(book.Asks))
		for i, a := range book.Asks {
			asks[i] = obLevel{Price: a.Price, Volume: a.Volume}
		}
		data[symbol] = obPerStock{Bids: bids, Asks: asks}
	}
	msg, _ := json.Marshal(wsEnvelope{Type: "orderbook", Data: data})
	return msg
}

type tradeRecord struct {
	Symbol string `json:"symbol"`
	Price  int64  `json:"price"`
	Qty    int64  `json:"qty"`
	Time   string `json:"time"`
}

func BuildTradeTapeEntry(symbol string, price, qty int64, tradeTime time.Time) []byte {
	msg, _ := json.Marshal(wsEnvelope{
		Type: "trade_tape",
		Data: tradeRecord{
			Symbol: symbol,
			Price:  price,
			Qty:    qty,
			Time:   tradeTime.UTC().Format(time.RFC3339),
		},
	})
	return msg
}
