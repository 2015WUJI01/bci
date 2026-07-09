## Why

当前"需求量"指标显示的是上季实际销量（`last_quarterly.sales_qty`），而非理论需求量（`companies.demand`）。玩家做了营销推广后，`demand` 已实时增加，但指标仍显示上季旧值，无法反映当前真实需求状态。需要将数据源切换到当前 `demand`，让玩家感知营销效果实时体现在需求量上。

## What Changes

- **后端**：`GET /api/company/state` 响应中新增 `demand` 字段（`companies.demand` 实时值）
- **前端**：经营指标第 6 项"需求量"主值改为当前 `demand` + 景气度偏离，颜色仅应用于景气偏离部分
- 悬浮提示展示上季需求量作为对比（`last_quarterly.demand`）
- 无上季结算时退化为仅显示景气偏离（维持现有行为）

## Capabilities

### New Capabilities
- `demand-indicator`: 在经营指标面板展示当前需求量（实时 demand + 景气偏离），着色仅作用于景气偏离

### Modified Capabilities
- `prosperity-indicator` (从上一 Change): 需求量数据源从上季销量改为当前 demand；颜色范围缩小到仅景气偏离部分；新增悬浮提示

## Impact

- `jjs-server/internal/handler/company.go` — companyStateResponse 新增 `demand` 字段，State() handler 填充
- `jjs-web/src/pages/CompanyPage.tsx` — 需求量 MetricCard 数据源、颜色范围、悬浮提示逻辑
- `jjs-web/src/types/index.ts` — CompanyState 接口新增 `demand` 字段
