## Why

经营行动弹窗每次打开，7 种行动的数值都从 0 开始。玩家每季度重复类似操作（扩 5 条产线、招 20 人、营销 10 万），每次从 0 拖动或输入很繁琐。需要记住每种行动上一次提交的值，作为默认值。

## What Changes

### 1. 按行动类型记忆上次提交值

使用 `localStorage` 存储每种行动类型最后提交的数值。选行动时读取记忆值作为默认（clamp 到当前上限）。仅提交成功时更新缓存。

**涉及文件**:
- `jjs-web/src/pages/CompanyPage.tsx` — 新增 localStorage 读写逻辑，修改选行动和提交回调

### 2. 越界保护

读取记忆值时用 `Math.min(saved, maxAmount)` 确保不超出当前上限（如现金减少、员工数变化）。

## Capabilities

### New Capabilities

无。纯 UX 优化，不引入新能力。

### Modified Capabilities

无。

## Impact

| 影响范围 | 说明 |
|---------|------|
| `jjs-web/src/pages/CompanyPage.tsx` | 新增 `~15` 行，删除 `~7` 行，改 `7` 个按钮的 onClick |
| localStorage | 新增 key `bci_last_action_values`，约 200 bytes |
