## ADDED Requirements

### Requirement: 经营指标展示景气度季度变化

`GET /api/company/state` SHALL 返回当前季度景气值（`prosperity`）和上一季度景气值（`prev_prosperity`）。

经营指标面板 SHALL 展示景气度季度变化百分比：
- 变化率 = (prosperity - prev_prosperity) / prev_prosperity × 100%
- 保留 2 位小数，末尾省略 0（如 3.50% → 3.5%，0.00% → 0%）
- 正数绿色（`text-accent-green`），负数红色（`text-accent-red`）
- 上期值不存在时显示 `—`

#### Scenario: 公司页加载后看到景气度变化

- **WHEN** 玩家打开公司页，`GET /api/company/state` 返回 `prosperity: 1.05, prev_prosperity: 1.02`
- **THEN** 经营指标显示第 6 项 `景气度 +2.9%`（绿色），悬停提示 "上期 1.02 → 本期 1.05"

#### Scenario: 景气度下降

- **WHEN** `prosperity: 0.95, prev_prosperity: 1.00`
- **THEN** 显示 `景气度 -5%`（红色），悬停提示 "上期 1.00 → 本期 0.95"

#### Scenario: 上期数据不存在

- **WHEN** 公司刚成立，数据库中只有当期景气值，`prev_prosperity` 为 0 或不存在
- **THEN** 显示 `景气度 —`（灰色），无悬停提示

#### Scenario: 百分比格式符合规范

- **WHEN** 变化率为 0.035 → `+3.5%`（不是 +3.50%）
- **WHEN** 变化率为 0.0003 → `+0.03%`（保留 2 位小数）
- **WHEN** 变化率为 0 → `0%`（不加正负号）
