## Context

`jjs-web/src/components/KlineChart.tsx` 使用 TradingView `lightweight-charts` 库渲染 K 线图和成交量柱状图。

当前代码在 `HistogramSeries` 创建后，通过 `priceScale().applyOptions()` 设置了 `scaleMargins: { top: 0.2, bottom: 0 }`，其中 `bottom: 0` 导致 0 基线不可见。

## Goals / Non-Goals

**Goals:**
- 成交量柱状图的 0 基线可见
- Y 轴标签显示 0 值
- 最小侵入性修改

**Non-Goals:**
- 不改变成交量柱的渲染颜色、宽度、样式
- 不调整 K 线图的 price scale（`top: 0.2` 保持不动）
- 不改变图表的高度、布局、交互行为

## Decisions

### Decision 1: `bottom: 0.03` 而非更大的值

**选择**：设置 `scaleMargins.bottom = 0.03`

**替代方案**：
- `bottom: 0.05`：边距过大，压缩柱状图显示区域
- `bottom: 0.01`：可能仍不够，0 轴标签仍被裁

**理由**：
- `0.03` 约等于图表高度的 3%，对 400px 高度的 chart 约 12px
- 足够容纳 0 轴标签，不会过度压缩柱状图面积
- 与 `top: 0.2`（约 80px）相比比例合理

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| 底部标签仍被裁 | 若 `0.03` 不足可微调至 `0.04` |
| 柱状图面积缩小 3% | 视觉影响极小，柱状图相对高度比例不变 |
