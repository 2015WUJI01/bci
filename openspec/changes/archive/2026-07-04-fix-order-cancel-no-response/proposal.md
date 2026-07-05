# 修复撤单无响应问题

## 问题

用户在持仓页面点击"撤单"按钮时，某些条件下按钮无任何反馈：不报错、不刷新、订单依然挂在那里。

## 根本原因分析

经过全链路代码审查，发现三个问题叠加导致此现象：

### 问题 1：前端 `catch {}` 静默吞错误（Severity: 高）

`jjs-web/src/pages/PortfolioPage.tsx:101-109`：

```typescript
const handleCancel = async (orderId: number) => {
  try {
    await api.delete('/trade/order', { order_id: orderId })
    queryClient.invalidateQueries(...)
  } catch {
    // error is handled by api client  ← 空的 catch，任何后端错误都不会反馈给用户
  }
}
```

后端返回的任何错误（400/500）都会被吞掉，用户看到的视觉效果就是"点了没反应"。

### 问题 2：后端读取和写入不在同一个事务中（Severity: 中）

`jjs-server/internal/engine/matching.go:546-586`：

`CancelOrderTx` 接收事务 `tx` 参数，但内部的 `store.GetOrderByIDAndPlayer` 使用的是**全局 `DB` 连接**而非 `tx`：

```go
func CancelOrderTx(tx *gorm.DB, orderID uint, playerID string) error {
    order, err := store.GetOrderByIDAndPlayer(orderID, playerID) // ← 用了 DB，不是 tx
```

而 `store.GetOrderByIDAndPlayer` 定义在 `store/order.go:21`：

```go
func GetOrderByIDAndPlayer(orderID uint, playerID string) (*domain.Order, error) {
    if err := DB.Where("id = ? AND player_id = ?", orderID, playerID).First(&o).Error; err != nil {
```

这导致订单读取在事务外，而 `tx.Save(order)` 在事务内，读写在两个 session 上。在 AI 交易者撮合引擎并发运行的场景下，可能读到过期状态，导致：
- 读取时状态为 `open` → 判断可撤单
- 保存时状态已被撮合引擎修改 → 数据覆盖或不一致

### 问题 3：按钮缺少加载态（Severity: 低）

点击撤单后按钮无任何视觉反馈（disabled、loading 动画等），用户无法判断操作是否已被触发。

## 范围

### 修复

| 文件 | 修改 |
|------|------|
| `jjs-web/src/pages/PortfolioPage.tsx` | `handleCancel` 添加错误提示 + 按钮加载态 |
| `jjs-server/internal/store/order.go` | `GetOrderByIDAndPlayer` 改为接受 `*gorm.DB` 参数 |
| `jjs-server/internal/engine/matching.go` | `CancelOrderTx` 传入 `tx` 而非全局 `DB` |
| `jjs-web/src/api/client.ts` | (可选) 考虑改用 POST 替代 DELETE+body |

### 不在范围

- 其他页面的错误处理重构
- 撮合引擎的其他竞态条件
- 后端全局 `DB` 模式的其他误用
