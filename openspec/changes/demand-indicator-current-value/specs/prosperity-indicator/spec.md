## MODIFIED Requirements

### Requirement: 经营指标展示需求量（当前 demand + 景气度偏离）

`GET /api/company/state` SHALL 返回当前季度景气值（`prosperity`）、上一季度景气值（`prev_prosperity`）及当前公司需求量（`demand`）。

经营指标面板 SHALL 展示第 6 项"需求量"：
- 有上季结算时：`{current_demand}件/季（{景气偏离}）`，需求数字使用默认色，景气偏离部分着色
- 无上季结算时：仅显示景气偏离
- 景气偏离 = `(prosperity - 1.0) × 100%`，保留 2 位小数，末尾省略 0（如 23.40% → 23.4%）
- 景气 > 1 景气偏离文字涨红（`text-accent-red`），景气 < 1 跌绿（`text-accent-green`）
- 景气 = 1 不标注颜色
- 有上季结算时 SHALL 展示悬浮提示：`上季需求量 {last_quarterly.demand}件/季`
- 颜色与 A 股保持一致（红涨绿跌）

**CHANGED FROM**: 上季方案使用 `last_quarterly.sales_qty`（上季销量）作为主值，且整个值区域统一着色。现改为使用 `companies.demand`（当前实时需求量）作为主值，颜色仅作用于景气偏离部分，并增加悬浮提示展示上季需求量。

#### Scenario: 有上季结算时显示当前需求量

- **WHEN** `company.demand=220000`，`company.last_quarterly.demand=200000`，`prosperity=1.01`
- **THEN** 显示 `需求量    220,000件/季（+1%）`，景气偏离文字红色，demand 数字默认色
- **THEN** 悬浮显示 `上季需求量 200,000件/季`

#### Scenario: 景气低于基准

- **WHEN** `prosperity=0.91`，`company.demand=180000`
- **THEN** 显示 `需求量    180,000件/季（-9%）`，景气偏离文字绿色

#### Scenario: 无上季结算数据

- **WHEN** `company.last_quarterly` 为 null
- **THEN** 显示 `需求量    +23.45%`（仅景气偏离），颜色按景气偏离正负决定

#### Scenario: 景气偏离为零

- **WHEN** `prosperity=1.0`
- **THEN** 景气偏离显示 `0%`，无正负号，无颜色
