package handler

import (
	"encoding/json"
	"log/slog"
	"math"
	"math/rand"
	"net/http"

	"gorm.io/datatypes"

	"jjs-server/internal/domain"
	"jjs-server/internal/engine"
	"jjs-server/internal/middleware"
	"jjs-server/internal/store"
)

type actionRequest struct {
	Actions []actionItem `json:"actions"`
}

type actionItem struct {
	Type   string `json:"type"`
	Amount int    `json:"amount"`
}

type actionResponse struct {
	Cash      int64              `json:"cash"`
	Employees int                `json:"employees"`
	CapCount  int                `json:"cap_count"`
	Actions   []domain.ActionLog `json:"actions"`
}

type dividendCalcInfo struct {
	perShareFen int64             // 每股分红(分)
	totalYuan   int64             // 总分红金额(元)
	shares      int64             // 总分配股数
	isPreIpo    bool              // IPO前仅向CEO分红
	holdings    []domain.Holding  // IPO后所有持仓者
}

var validActionTypes = map[string]bool{
	"expand":         true,
	"hire":           true,
	"layoff":         true,
	"sell_assets":    true,
	"marketing":      true,
	"inject_capital": true,
	"dividend":       true,
}

const assetSellDiscount = 0.75

func actionHireRNG(companyID uint, quarter int) *rand.Rand {
	seed := int64(companyID)*1_000_000 + int64(quarter)*100 + 99
	return rand.New(rand.NewSource(seed))
}

func (h *CompanyHandler) SubmitActions(w http.ResponseWriter, r *http.Request) {
	userID, ok := middleware.GetUserID(r)
	if !ok {
		WriteJSON(w, http.StatusUnauthorized, map[string]string{"error": "未登录"})
		return
	}

	var req actionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "请求格式错误"})
		return
	}

	if len(req.Actions) == 0 || len(req.Actions) > 3 {
		WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "每季度最多执行 3 次操作"})
		return
	}

	c, err := store.GetActiveCompanyByCEOID(userID)
	if err != nil {
		WriteJSON(w, http.StatusNotFound, map[string]string{"error": "未找到活跃公司"})
		return
	}

	currentQ := int(engine.GlobalQuarter.Load())
	if currentQ == 0 {
		WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "游戏尚未开始"})
		return
	}

	existingCount := countExistingActions(c.ID, currentQ)
	if existingCount+len(req.Actions) > 3 {
		WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "本季度操作次数已用完"})
		return
	}

	cfg := engine.Industries[c.Industry]

	dividendCalcs := make([]*dividendCalcInfo, len(req.Actions))

	var totalCost int64
	for i, a := range req.Actions {
		if !validActionTypes[a.Type] {
			WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "无效的操作类型: " + a.Type})
			return
		}
		if a.Amount <= 0 {
			WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "操作数量必须大于 0"})
			return
		}
		if a.Type == "layoff" && a.Amount > c.Employees {
			WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "裁员人数超过现有员工"})
			return
		}
		if a.Type == "sell_assets" && a.Amount > c.CapCount {
			WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "出售数量超过现有资产"})
			return
		}
		if a.Type == "marketing" && cfg.MarketingScale <= 0 {
			WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "该行业暂不支持营销"})
			return
		}

		if a.Type == "dividend" {
			dividendPerShare := int64(a.Amount) // 分/股
			var distShares int64
			var isPreIpo bool
			var holdings []domain.Holding
			if c.IpoQuarter == 0 {
				distShares = c.CEOShares
				isPreIpo = true
			} else {
				s, err := store.GetStockByCompanyID(c.ID)
				if err != nil {
					WriteJSON(w, http.StatusNotFound, map[string]string{"error": "公司尚未上市"})
					return
				}
				holdings, err = store.GetHoldingsByStockID(s.ID)
				if err != nil {
					WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "查询持仓失败"})
					return
				}
				for _, h := range holdings {
					distShares += h.Qty
				}
				isPreIpo = false
			}
			if distShares <= 0 {
				WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "无可分配股份"})
				return
			}
			totalYuan := dividendPerShare * distShares / 100
			if totalYuan <= 0 {
				WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "每股分红过低"})
				return
			}
			dividendCalcs[i] = &dividendCalcInfo{
				perShareFen: dividendPerShare,
				totalYuan:   totalYuan,
				shares:      distShares,
				isPreIpo:    isPreIpo,
				holdings:    holdings,
			}
		}

		switch a.Type {
		case "expand":
			totalCost += int64(math.Round(float64(a.Amount) * cfg.CapBuildCost))
		case "hire":
			totalCost += int64(math.Round(float64(a.Amount) * cfg.HireCost))
		case "layoff":
			totalCost += int64(math.Round(float64(a.Amount) * cfg.LaborRate * 3))
		case "sell_assets":
			// asset sale gives cash, not costs it
		case "marketing":
			totalCost += int64(a.Amount)
		case "dividend":
			totalCost += dividendCalcs[i].totalYuan
		}
	}

	if totalCost > 0 {
		if c.Cash < totalCost {
			WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "公司现金不足"})
			return
		}
		c.Cash -= totalCost
	}

	var actionLogs []domain.ActionLog

	existingPendingCount := 0
	if c.Industry == "mining" {
		existingOrders, err := store.GetPendingBuildOrders(c.ID)
		if err == nil {
			existingPendingCount = len(existingOrders)
		}
	}
	exploreIdx := existingPendingCount

	for i, a := range req.Actions {
		switch a.Type {
		case "expand":
			var capAmount int
			if c.Industry == "mining" {
				for i := 0; i < a.Amount; i++ {
					rng := engine.MiningRNG(c.ID, currentQ, "prospect", exploreIdx)
					capAmount += int(engine.ProspectOreReserves(rng))
					exploreIdx++
				}
			} else {
				capAmount = a.Amount
			}

			readyQuarter := currentQ + cfg.CapBuildQuarters
			order := &domain.CapBuildOrder{
				CompanyID:    c.ID,
				ReadyQuarter: readyQuarter,
				Amount:       capAmount,
				Completed:    cfg.CapBuildQuarters == 0,
			}
			if err := store.CreateCapBuildOrder(order); err != nil {
				WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "创建建造订单失败"})
				return
			}

			if cfg.CapBuildQuarters == 0 {
				c.CapCount += capAmount
			}
			actionLogs = append(actionLogs, domain.ActionLog{
				Type:         "expand",
				Amount:       a.Amount,
				Cost:         int64(float64(a.Amount) * cfg.CapBuildCost),
				ReadyQuarter: readyQuarter,
			})
			slog.Info("expand order created", "company", c.ID, "amount", a.Amount, "capAmount", capAmount, "readyQ", readyQuarter)

		case "hire":
			reqAmount := a.Amount
			rng := actionHireRNG(c.ID, currentQ)
			ratio := 0.3 + rng.Float64()*0.7
			actualHired := int(math.Round(float64(reqAmount) * ratio))
			if actualHired < 1 {
				actualHired = 1
			}
			c.Employees += actualHired
			actionLogs = append(actionLogs, domain.ActionLog{
				Type:   "hire",
				Amount: reqAmount,
				Actual: actualHired,
				Cost:   int64(float64(reqAmount) * cfg.HireCost),
			})
			slog.Info("hire completed", "company", c.ID, "requested", reqAmount, "hired", actualHired)

		case "layoff":
			c.Employees -= a.Amount
			actionLogs = append(actionLogs, domain.ActionLog{
				Type:   "layoff",
				Amount: a.Amount,
				Cost:   int64(float64(a.Amount) * cfg.LaborRate * 3),
			})
			slog.Info("layoff completed", "company", c.ID, "laidOff", a.Amount)

		case "sell_assets":
			sellCash := int64(math.Round(float64(a.Amount) * cfg.CapAssetValue * assetSellDiscount))
			c.CapCount -= a.Amount
			c.Cash += sellCash
			actionLogs = append(actionLogs, domain.ActionLog{
				Type:   "sell_assets",
				Amount: a.Amount,
				Cost:   int64(-sellCash),
			})
			slog.Info("assets sold", "company", c.ID, "amount", a.Amount, "cashReceived", sellCash)

		case "marketing":
			amount := float64(a.Amount)
			var demandBoost float64
			if c.Industry == "mining" {
				rng := engine.MiningRNG(c.ID, currentQ, "marketing", 0)
				demandBoost = cfg.MarketingScale * math.Pow(amount, cfg.MarketingExponent) * (0.85 + rng.Float64()*0.30)
			} else {
				rng := engine.ManufacturingRNG(c.ID, currentQ, "marketing")
				demandBoost = cfg.MarketingScale * math.Pow(amount, cfg.MarketingExponent) * (0.85 + rng.Float64()*0.30)
			}
			c.Demand += int64(math.Round(demandBoost))
			actionLogs = append(actionLogs, domain.ActionLog{
				Type:   "marketing",
				Amount: a.Amount,
				Actual: int(demandBoost),
				Cost:   int64(a.Amount),
			})
			slog.Info("marketing completed", "company", c.ID, "investment", a.Amount, "demandBoost", demandBoost)

		case "inject_capital":
			cashAmount := int64(a.Amount)
			if err := store.DeductCash(userID, cashAmount, "公司注资"); err != nil {
				WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "个人现金不足"})
				return
			}
			c.Cash += cashAmount
			actionLogs = append(actionLogs, domain.ActionLog{
				Type:   "inject_capital",
				Amount: a.Amount,
				Cost:   int64(-cashAmount),
			})
			slog.Info("capital injected", "company", c.ID, "amount", cashAmount)

		case "dividend":
			calc := dividendCalcs[i]
			if calc == nil {
				WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "分红计算数据丢失"})
				return
			}
			if calc.isPreIpo {
				if err := store.AddCash(store.DB, userID, calc.perShareFen*calc.shares/100); err != nil {
					WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "CEO资金入账失败"})
					return
				}
				slog.Info("dividend distributed (pre-IPO)", "company", c.ID, "perShareFen", calc.perShareFen, "shares", calc.shares, "companyTotalShares", c.TotalShares, "total", calc.totalYuan)
			} else {
				for _, h := range calc.holdings {
					amount := calc.perShareFen * h.Qty / 100
					if amount <= 0 {
						continue
					}
					if err := store.AddCash(store.DB, h.PlayerID, amount); err != nil {
						slog.Error("dividend add cash failed", "player", h.PlayerID, "error", err)
						continue
					}
				}
				slog.Info("dividend distributed (post-IPO)", "company", c.ID, "perShareFen", calc.perShareFen, "holders", len(calc.holdings), "distShares", calc.shares, "companyTotalShares", c.TotalShares, "total", calc.totalYuan)
			}
			actionLogs = append(actionLogs, domain.ActionLog{
				Type:   "dividend",
				Amount: a.Amount,
				Actual: int(calc.shares),
				Cost:   calc.totalYuan,
			})
		}
	}

	if err := store.UpdateCompany(c); err != nil {
		WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "更新公司状态失败"})
		return
	}

	prosperity, err := store.LatestProsperity(c.Industry)
	if err != nil {
		prosperity = 1.0
	}

	var existingActions datatypes.JSON
	var quarterly domain.CompanyQuarterly
	var existingQ domain.CompanyQuarterly

	err = store.DB.Where("company_id = ? AND quarter = ?", c.ID, currentQ).First(&existingQ).Error
	if err == nil {
		existingActions = existingQ.Actions
		quarterly = existingQ
	}

	switch c.Industry {
	case "manufacturing":
		result := engine.SettleManufacturing(
			c.ID, c.Employees, c.CapCount, c.Inventory, c.Demand,
			prosperity, currentQ,
			cfg.BaseMaintenanceRate, cfg.OperationalCostRate,
		)

		beginningCash := c.Cash
		newCash := beginningCash + result.Profit

		merged, mergeErr := engine.MergeActionLogs(existingActions, actionLogs)
		if mergeErr != nil {
			WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "合并操作记录失败"})
			return
		}

		quarterly.CompanyID = c.ID
		quarterly.Quarter = currentQ
		quarterly.Revenue = result.Revenue
		quarterly.Profit = result.Profit
		quarterly.BeginningCash = beginningCash
		quarterly.Cash = newCash
		quarterly.LaborCost = result.LaborCost
		quarterly.BaseMaintenance = result.BaseMaintenance
		quarterly.OperationalCost = result.OperationalCost
		quarterly.WarehouseCost = result.WarehouseCost
		quarterly.TotalCost = result.LaborCost + result.BaseMaintenance + result.OperationalCost + result.WarehouseCost
		quarterly.SalesQty = result.SalesQty
		quarterly.ProdQty = result.ProdQty
		quarterly.Employees = c.Employees
		quarterly.TotalShares = c.TotalShares
		quarterly.CEOShares = c.CEOShares
		quarterly.InvestorShares = c.InvestorShares
		quarterly.PublicFloat = c.PublicFloat
		quarterly.CapCount = c.CapCount
		quarterly.Inventory = result.Inventory
		quarterly.Demand = result.Demand
		quarterly.Actions = datatypes.JSON(merged)

		if quarterly.ID != 0 {
			if err := store.DB.Save(&quarterly).Error; err != nil {
				WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "更新季度报表失败"})
				return
			}
		} else {
			if err := store.DB.Create(&quarterly).Error; err != nil {
				WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "创建季度报表失败"})
				return
			}
		}

	case "mining":
		result := engine.SellMining(
			c.ID, c.Employees, c.CapCount, c.Inventory, c.Demand,
			prosperity, currentQ,
			cfg.BaseMaintenanceRate, cfg.OperationalCostRate,
		)

		beginningCash := c.Cash
		newCash := beginningCash + result.Profit

		merged, mergeErr := engine.MergeActionLogs(existingActions, actionLogs)
		if mergeErr != nil {
			WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "合并操作记录失败"})
			return
		}

		quarterly.CompanyID = c.ID
		quarterly.Quarter = currentQ
		quarterly.Revenue = result.Revenue
		quarterly.Profit = result.Profit
		quarterly.BeginningCash = beginningCash
		quarterly.Cash = newCash
		quarterly.LaborCost = result.LaborCost
		quarterly.BaseMaintenance = result.BaseMaintenance
		quarterly.OperationalCost = result.OperationalCost
		quarterly.WarehouseCost = result.WarehouseCost
		quarterly.TotalCost = result.LaborCost + result.BaseMaintenance + result.OperationalCost + result.WarehouseCost
		quarterly.SalesQty = result.SalesQty
		quarterly.ProdQty = result.ProdQty
		quarterly.Employees = c.Employees
		quarterly.TotalShares = c.TotalShares
		quarterly.CEOShares = c.CEOShares
		quarterly.InvestorShares = c.InvestorShares
		quarterly.PublicFloat = c.PublicFloat
		quarterly.CapCount = result.OreRemaining
		quarterly.Inventory = result.Inventory
		quarterly.Demand = result.Demand
		quarterly.Actions = datatypes.JSON(merged)

		if quarterly.ID != 0 {
			if err := store.DB.Save(&quarterly).Error; err != nil {
				WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "更新季度报表失败"})
				return
			}
		} else {
			if err := store.DB.Create(&quarterly).Error; err != nil {
				WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "创建季度报表失败"})
				return
			}
		}

	default:
		merged, mergeErr := engine.MergeActionLogs(existingActions, actionLogs)
		if mergeErr != nil {
			WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "合并操作记录失败"})
			return
		}

		quarterly.CompanyID = c.ID
		quarterly.Quarter = currentQ
		quarterly.BeginningCash = c.Cash
		quarterly.Cash = c.Cash
		quarterly.Employees = c.Employees
		quarterly.TotalShares = c.TotalShares
		quarterly.CEOShares = c.CEOShares
		quarterly.InvestorShares = c.InvestorShares
		quarterly.PublicFloat = c.PublicFloat
		quarterly.CapCount = c.CapCount
		quarterly.Inventory = c.Inventory
		quarterly.Demand = c.Demand
		quarterly.Actions = datatypes.JSON(merged)

		if quarterly.ID != 0 {
			if err := store.DB.Save(&quarterly).Error; err != nil {
				WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "更新季度报表失败"})
				return
			}
		} else {
			if err := store.DB.Create(&quarterly).Error; err != nil {
				WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "创建季度报表失败"})
				return
			}
		}
	}

	WriteJSON(w, http.StatusOK, actionResponse{
		Cash:      c.Cash,
		Employees: c.Employees,
		CapCount:  c.CapCount,
		Actions:   actionLogs,
	})
}

func countExistingActions(companyID uint, quarter int) int {
	var qr domain.CompanyQuarterly
	if err := store.DB.Where("company_id = ? AND quarter = ?", companyID, quarter).First(&qr).Error; err != nil {
		return 0
	}
	if len(qr.Actions) == 0 {
		return 0
	}
	var actions []domain.ActionLog
	if err := json.Unmarshal(qr.Actions, &actions); err != nil {
		return 0
	}
	return len(actions)
}
