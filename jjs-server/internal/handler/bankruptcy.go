package handler

import (
	"net/http"

	"jjs-server/internal/engine"
	"jjs-server/internal/middleware"
	"jjs-server/internal/store"
)

func (h *CompanyHandler) Liquidate(w http.ResponseWriter, r *http.Request) {
	userID, ok := middleware.GetUserID(r)
	if !ok {
		WriteJSON(w, http.StatusUnauthorized, map[string]string{"error": "未登录"})
		return
	}

	company, err := store.GetActiveCompanyByCEOID(userID)
	if err != nil {
		WriteJSON(w, http.StatusNotFound, map[string]string{"error": "未找到活跃公司"})
		return
	}

	currentQ := int(engine.GlobalQuarter.Load())
	if !engine.CanLiquidate(company.ID, currentQ) {
		WriteJSON(w, http.StatusBadRequest, map[string]string{"error": "不满足破产清算条件（需连续两季度财报现金为负）"})
		return
	}

	result, err := engine.LiquidateCompany(store.DB, company)
	if err != nil {
		WriteJSON(w, http.StatusInternalServerError, map[string]string{"error": "清算执行失败"})
		return
	}

	WriteJSON(w, http.StatusOK, map[string]interface{}{
		"status":  "liquidated",
		"message": "公司已破产清算",
		"result":  result,
	})
}
