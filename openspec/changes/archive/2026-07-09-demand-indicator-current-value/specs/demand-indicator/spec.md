## ADDED Requirements

### Requirement: 后端暴露当前需求量

`GET /api/company/state` SHALL 在响应中返回 `demand` 字段，其值为 `companies` 表中当前公司的 `demand` 字段（已包含营销推广等操作的实时加成）。

#### Scenario: 响应包含当前需求量

- **WHEN** 公司 demand 为 220000
- **THEN** `GET /api/company/state` 返回 `{ ..., "demand": 220000, ... }`

#### Scenario: 营销后需求立即更新

- **WHEN** 玩家提交营销操作成功，`c.Demand` 增加 demandBoost
- **THEN** 下次 `GET /api/company/state` 返回的 `demand` 已包含该加成

### Requirement: 前端存在当前需求量字段

`CompanyState` TypeScript 接口 SHALL 包含 `demand: number` 字段。

### Requirement: MetricCard 支持 ReactNode 值

`MetricCard` 组件的 `value` 属性类型 SHALL 从 `string` 改为 `React.ReactNode`，以支持在值区域中嵌入带样式的 JSX。

#### Scenario: 字符串值仍可正常工作

- **WHEN** 现有调用传入字符串
- **THEN** MetricCard 正常渲染，无类型错误
