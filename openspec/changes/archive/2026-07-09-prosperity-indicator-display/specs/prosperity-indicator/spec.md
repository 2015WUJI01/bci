## ADDED Requirements

### Requirement: 经营指标展示需求量（上季销量 + 景气度偏离）

`GET /api/company/state` SHALL 返回当前季度景气值（`prosperity`）和上一季度景气值（`prev_prosperity`）。

经营指标面板 SHALL 增加第 6 项"需求量"：
- 有上季结算时：`{sales_qty}件/季（{景气偏离}）`
- 无上季结算时：仅显示景气偏离
- 景气偏离 = `(prosperity - 1.0) × 100%`，保留 2 位小数，末尾省略 0（如 23.40% → 23.4%）
- 景气 > 1 涨红（`text-accent-red`），景气 < 1 跌绿（`text-accent-green`）
- 不展示悬停提示
- 颜色与 A 股保持一致（红涨绿跌）

#### Scenario: 有上季结算时显示完整信息

- **WHEN** `company.last_quarterly` 存在，`sales_qty=200000`，`prosperity=1.01`
- **THEN** 显示 `需求量    200,000件/季（+1.01%）`，颜色红色

#### Scenario: 景气低于基准

- **WHEN** `prosperity=0.91`，`sales_qty=150000`
- **THEN** 显示 `需求量    150,000件/季（-9%）`，颜色绿色

#### Scenario: 无上季结算数据

- **WHEN** `company.last_quarterly` 为 null
- **THEN** 显示 `需求量    +23.45%`（仅景气偏离），颜色按景气偏离正负决定

#### Scenario: 百分比格式

- **WHEN** 景气偏离为 0.035 → 显示 `+3.5%`（不是 +3.50%）
- **WHEN** 景气偏离为 0.0003 → 显示 `+0.03%`
- **WHEN** 景气偏离为 0 → 显示 `0%`（无正负号，无颜色）
