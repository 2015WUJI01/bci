## Context

上一 Change（`prosperity-indicator-display`）实现了经营指标第 6 项"需求量"——显示上季实际销量 + 景气偏离百分比。然而该指标的数据源是 `last_quarterly.sales_qty`（历史值），玩家做了营销推广（增加 `companies.demand`）后，指标不反映当前需求状态。需要在同一张卡片上展示实时需求值（`demand`）与景气偏离的叠加效果，让玩家直观理解需求变化原因。

当前 `companies.demand` 已存在于数据库并随营销操作实时更新，但后端未暴露给前端。

## Goals / Non-Goals

**Goals:**
- `GET /api/company/state` 暴露 `companies.demand` 实时值
- 需求量主值改为当前 `demand` + 景气偏离百分比
- 颜色仅应用于景气偏离部分（demand 数字本身使用默认色）
- 悬浮提示展示上季需求量作为历史对比
- 无上季结算时退化为仅显示景气偏离（维持现有行为）

**Non-Goals:**
- 不修改营销操作逻辑
- 不新增 API 端点
- 不改动其他指标卡片
- 不涉及「销量」指标的数据源修改

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| 数据源 | `companies.demand`（实时）而非 `last_quarterly.sales_qty`（历史） | 营销效果已写入 demand，实时反映需求状态 |
| 颜色范围 | 仅 `formatProsperityDeviation` 返回值着色，demand 数字不变色 | 基准需求本身不包含涨跌含义，涨跌是景气偏离引起的 |
| 着色方式 | 使用内联 `<span>` + `text-accent-red/green`，不通过 MetricCard `colorClass` | `colorClass` 作用于整个值区域，无法只给部分文字着色 |
| 悬浮提示 | 显示 `上季需求量 X,XXX件` | 与主值（当前需求）形成历史对比，不重复当前值 |
| MetricCard | `value` 类型 `string` → `React.ReactNode` | 需要传入 JSX 以实现局部着色，string 类型太严格 |
| 无上季数据 | 退化为仅显示景气偏离百分比 | 新公司刚成立时 last_quarterly 为空，此时无历史可对比 |

## Risks / Trade-offs

- **类型变更**：`MetricCard` 的 `value` 从 `string` 改为 `React.ReactNode`，需确保所有调用处兼容（字符串是合法的 ReactNode，无破坏性）
- **当前 demand 可能已被上限截断**：营销后 demand 会增加，但结算时会被 `demandCap` 限制，结算后 `companies.demand` 存的是截断后的值。但这正是真实需求量，符合展示意图
- **上季无 demand**：目前的 `last_quarterly` 不一定有 `demand` 字段（旧季度记录），no data 时 hint 不显示即可
