# Tasks — 撤单无响应修复

## 前置条件

- [x] 基于最新 `master`/`main` 创建功能分支 `fix/cancel-order-no-response`

---

## Task 1: 后端事务一致性修复 ✅

**文件**: `jjs-server/internal/store/order.go`

- [x] 新增 `GetOrderByIDAndPlayerTx(db *gorm.DB, orderID uint, playerID string) (*domain.Order, error)` 函数
- [x] 将现有 `GetOrderByIDAndPlayer` 改为调用上述新函数，传入全局 `DB`

**文件**: `jjs-server/internal/engine/matching.go`

- [x] `CancelOrderTx` 中调用 `store.GetOrderByIDAndPlayerTx(tx, ...)` 替代 `store.GetOrderByIDAndPlayer`，传入事务 `tx`

---

## Task 2: 前端撤单错误反馈 ✅

**文件**: `jjs-web/src/pages/PortfolioPage.tsx`

- [x] 给撤单按钮加 loading 状态——`handleCancel` 开始执行时 disabled 按钮，文字变为"撤单中..."
- [x] `handleCancel` 的 `catch` 块改为将后端错误信息展示给用户
- [x] 检查是否需要新增 toast 组件；已创建 `jjs-web/src/components/Toast.tsx`

---

## Task 3: DELETE+body 兼容性修复 ✅

- [x] 后端新增路由 `POST /api/trade/cancel`，指向已有 `CancelOrder` handler
- [x] 前端 `handleCancel` 改为 `api.post('/trade/cancel', { order_id: orderId })`
- [ ] ~~待验证：~~ 需在开发环境下用 Network 面板确认后端能正确收到 body

---

## Task 4: 整体验证 ⏳

- [ ] 启动 MySQL + 后端 + 前端
- [ ] 登录游戏，挂一单买入
- [ ] 在持仓页面点击撤单，确认：
  - [ ] 按钮立即变为 disabled + "撤单中..."
  - [ ] 成功后订单从列表消失
  - [ ] 失败（如连续点击第二次）后展示错误提示
- [ ] 挂一个卖单，重复上述验证
- [ ] 验证 AI 交易者撮合场景（挂单后等 AI 部分成交，再撤单）
