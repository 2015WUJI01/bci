## 1. 后端 — 暴露景气值

- [x] 1.1 companyStateResponse 新增 prosperity / prev_prosperity 字段
- [x] 1.2 拼装 response 时查询并填充两个字段

## 2. 前端类型 — CompanyState 接口

- [x] 2.1 prosperity / prev_prosperity 字段加入 CompanyState 接口

## 3. 前端 — 格式化工具函数

- [x] 3.1 实现 formatProsperityDeviation 函数（`(prosperity-1)×100%`，保留 2 位小数，末尾去 0）

## 4. 前端 — 需求量指标卡

- [x] 4.1 在库存卡片后添加景气度 MetricCard（原实现，待修正）
- [x] 4.2 修正为"需求量"——改标签、值含销量+景气偏离、红涨绿跌、删悬停、无数据时回退
