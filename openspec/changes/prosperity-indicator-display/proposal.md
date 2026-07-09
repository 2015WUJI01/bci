## Why

当前游戏只提示当月销量，但销量受景气度（Prosperity）驱动而浮动，玩家看不到景气度的具体变化，无法理解销量波动的原因。需要在经营指标中展示景气度季度变化百分比，让玩家感知行业需求趋势。

## What Changes

- **后端**：`GET /api/company/state` 响应中增加 `prosperity`（当期景气值）和 `prev_prosperity`（上期景气值）两个字段
- **前端**：经营指标（当前 5 项）增加第 6 项——需求量 = 上季实际销量 + 景气度偏离（相对于基准 1.0），红涨绿跌（与 A 股一致）
- 无已结算季度时，回退为仅显示景气度偏离百分比
- 所有显示保留 2 位小数，末尾省略 0（如 23.40% → 23.4%）
- 仅影响已启用的行业（制造、矿业）

## Capabilities

### New Capabilities
- `prosperity-indicator`: 在经营指标面板中展示需求量（上季销量+景气度偏离）

### Modified Capabilities

<!-- 无现有 spec 变更 -->

## Impact

- `jjs-server/internal/handler/company.go` — companyStateResponse 新增字段，填充数据
- `jjs-web/src/pages/CompanyPage.tsx` — 经营指标区域新增 MetricCard
