## Context

经营行动弹窗有 7 种行动类型（expand/hire/layoff/sell_assets/marketing/inject_capital/dividend），共享同一个 `actionAmount` state，初始值 `0`。每次选行动都从 0 开始。玩家每季度重复类似操作，需要手动拖动滑块或输入数值，体验繁琐。

已有 `action-slider-number-input` change 已实现 slider + number input 组合和默认 0 移除，本 change 在此基础上增加"记忆上次提交值"功能。

## Goals / Non-Goals

**Goals:**
- 按行动类型记住最后提交的数值，下次选同类型时作为默认值
- 跨页面刷新保留（localStorage 持久化）
- 记忆值超过当前上限时自动 clamp 到上限

**Non-Goals:**
- 不记忆未提交的调整值（仅提交时更新缓存）
- 不做后端持久化
- 不改变现有 UI 布局和交互流程

## Decisions

### D1: 存储方式 — localStorage

选择 localStorage 而非 useState/useRef 纯内存方案：

| 方案 | 生命周期 | 跨刷新 |
|------|---------|--------|
| useState/useRef | 当前会话 | ✗ |
| **localStorage（选定）** | 持久化 | ✓ |

理由：经营决策的节奏是"每季度一次"，玩家可能隔几天回来玩。useState 刷新就丢，价值有限。localStorage 写入成本极低（~200 bytes），无性能担忧。

### D2: 记忆时机 — 提交成功后

在 `handleSubmitAction` 中，API 返回成功后更新缓存。选择器内调整但不提交 → 不记忆。理由：
- 只有真正执行了的行动才值得记住
- 用户可能乱拖然后又关掉，不应污染记忆值

### D3: 读取策略 — 选行动时 clamp

选行动时：`Math.min(lastAmount ?? 0, maxAmount)`
- `lastAmount` 不存在 → 0（首次使用）
- `lastAmount` 超过当前上限（如现金减少、裁员人数超员工数）→ 自动 clamp 到 `maxAmount`

### D4: 数据结构 — Record<string, number>

```typescript
type LastActionValues = {
  expand?: number
  hire?: number
  layoff?: number
  sell_assets?: number
  marketing?: number
  inject_capital?: number
  dividend?: number
}
```

存入 JSON：`localStorage.setItem('bci_last_action_values', JSON.stringify(record))`

## Risks / Trade-offs

| 风险 | 缓解 |
|------|------|
| localStorage 被用户清空或浏览器不支持 | try/catch 包裹读取，降级为默认 0 |
| 分红场景 `toFixed(2)` 精度与存储精度不一致 | 存储时保留原始 number，分红精度在显示层处理 |
| 公司破产重建后，旧记忆值可能不适用 | clamp 到 maxAmount 兜底，不会越界 |
