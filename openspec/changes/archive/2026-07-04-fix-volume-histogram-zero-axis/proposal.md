## Why

在持仓/行情页面的 K 线图中，成交量柱状图的 0 轴不可见——柱子看起来是"悬空"的，无法判断成交量基线。

根本原因：`KlineChart.tsx` 中成交量 `HistogramSeries` 的 `priceScale.scaleMargins.bottom` 被设为 `0`，导致 0 基线和对应的 Y 轴标签被图表底部裁掉。

虽然 `HistogramSeries` 的 autoScale 默认包含 0，但由于 `bottom = 0`，0 轴紧贴图表底边不可见。这不是功能设计，是配置 bug。

## What Changes

- **修改** `jjs-web/src/components/KlineChart.tsx` 的第 78-80 行
  - `scaleMargins.bottom` 从 `0` 改为 `0.03`
  - 增加底部边距，让 0 基线和 Y 轴标签可见

## Capabilities

### Fixed Capabilities

- `kline-chart`: K 线图成交量柱状图——0 基线现在可见，柱子从 0 轴起始

## Impact

- **代码**：仅修改 `KlineChart.tsx` 中 `volumeSeries.priceScale().applyOptions()` 的 `scaleMargins.bottom` 值
- **无影响**：不改变任何业务逻辑、API 行为、数据格式
- **无副作用**：边距微调不影响图表核心渲染；柱状图的相对高度比例保持不变
