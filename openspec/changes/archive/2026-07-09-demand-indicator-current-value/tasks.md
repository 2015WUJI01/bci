## 1. 后端 — 暴露当前需求量

- [x] 1.1 companyStateResponse 新增 `Demand int64` 字段
- [x] 1.2 State() handler 中赋值 `Demand: company.Demand`

## 2. 前端类型 — CompanyState 接口

- [x] 2.1 CompanyState 接口新增 `demand: number` 字段

## 3. 前端 — MetricCard 类型放宽

- [x] 3.1 MetricCard 的 `value` prop 类型从 `string` 改为 `React.ReactNode`

## 4. 前端 — 需求量指标卡更新

- [x] 4.1 主值数据源从 `confirmedQ.sales_qty` 改为 `company.demand`，拼接景气偏离
- [x] 4.2 景气偏离部分用 `<span>` 包覆，单独应用 `text-accent-red/green` 颜色，demand 数字使用默认色
- [x] 4.3 移除 MetricCard 的 `colorClass` 属性（颜色已由内联 span 控制）
- [x] 4.4 有 `company.last_quarterly` 时，添加悬浮提示 `上季需求量 {confirmedQ.demand}件/季`
- [x] 4.5 无上季结算时退化为仅显示景气偏离百分比（维持现有行为）

## 5. 验证

- [x] 5.1 `pnpm typecheck` 通过
- [x] 5.2 `go build ./...` 通过（ESLint 配置缺失系已有问题，不影响）
- [ ] 5.3 手动检查页面渲染：当前需求值正确、颜色仅作用于景气偏离、悬浮提示正确
