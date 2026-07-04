# 设计 — 撤单无响应修复

## 修复一：前端错误反馈 + 加载态

### 目标

用户点击撤单后，无论成功失败，都能看到明确的视觉反馈。

### 方案

```
撤单按钮        handleCancel          API              用户
  │                │                   │                │
  ├─ 点击 ────────▶│                   │                │
  │  (disabled)    │                   │                │
  │                ├─ DELETE ──────────▶│                │
  │                │                   │                │
  │                │◀─ 200/400/500 ────┤                │
  │                │                   │                │
  │  [成功]        │── invalidate ─────▶                │
  │  订单消失      │                   │                │
  │                │                   │                │
  │  [失败]        │── toast ─────────▶ 显示错误原因     │
  │  按钮恢复      │                   │                │
```

### 具体改动

1. **按钮添加 loading 态**：点击后立即 disabled，文字改为"撤单中..."
2. **`handleCancel` 加错误 toast**：catch 块从空实现改为显示后端错误信息
3. **添加 `toast` 工具函数**：轻量通知组件（如果不存在的话）

### 错误信息展示策略

后端返回形如 `{"error": "订单无法撤销"}` 的错误体，前端 `api.client.ts:30` 已经将其转为 `Error` 对象。只需在 catch 块中将其展示给用户即可。

```
handleCancel 修改后：
  try {
    await api.delete(...)
    invalidateQueries()
  } catch (err) {
    toast(err.message)  ← 展示具体的后端错误原因
  }
```

## 修复二：后端事务一致性

### 目标

`CancelOrderTx` 内部的所有操作在同一个事务中完成。

### 方案

将 `store.GetOrderByIDAndPlayer` 改造为接受 `*gorm.DB` 参数：

```go
// 新增
func GetOrderByIDAndPlayerTx(db *gorm.DB, orderID uint, playerID string) (*domain.Order, error) {
    var o domain.Order
    if err := db.Where("id = ? AND player_id = ?", orderID, playerID).First(&o).Error; err != nil {
        return nil, err
    }
    return &o, nil
}

// 已有（不改）—— 供其他调用方使用
func GetOrderByIDAndPlayer(orderID uint, playerID string) (*domain.Order, error) {
    return GetOrderByIDAndPlayerTx(DB, orderID, playerID)
}
```

然后 `CancelOrderTx` 改为使用 `GetOrderByIDAndPlayerTx(tx, ...)`：

```go
func CancelOrderTx(tx *gorm.DB, orderID uint, playerID string) error {
    order, err := store.GetOrderByIDAndPlayerTx(tx, orderID, playerID)  // ← 用 tx 而非 DB
    ...
}
```

这样读和写在同一个事务 session 内，事务的 REPEATABLE READ 隔离级别保证读取到一致快照。

## 修复三：DELETE+body 代理兼容（可选）

如果验证是 Vite proxy 丢弃 DELETE body，可将该路由改为 `POST`：

后端路由 `/api/trade/order` 同时支持两种方法：
- `POST` — 下订单（已有）
- `DELETE` — 撤单（保留，向下兼容）
- **新增** `POST /api/trade/cancel` — 撤单的替代入口，body 同上

前端改用 `POST` 到 `/api/trade/cancel`，避免 DELETE+body 的代理问题。

## 不变部分

- 后端撤单业务逻辑 (`CancelOrderTx` 的金额解冻逻辑) 不变
- 前端 `portfolioKeys` 的 query key 结构不变
- WebSocket 推送逻辑不变
