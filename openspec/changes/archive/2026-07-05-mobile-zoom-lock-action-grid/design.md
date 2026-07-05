## Context

经营行动弹窗当前存在两个移动端体验问题：

1. **iOS 自动缩放** — `index.html` 中 viewport meta 未限制缩放，iOS Safari 在聚焦 `<input type="number">`（font-size < 16px）时会自动放大视口。弹窗中数量输入框使用 `text-xs`（12px），必然触发此行为。
2. **按钮布局过长** — 7 个行动按钮使用纵向单列 `space-y-3` 布局，每项 `p-4` 约 76px 高，总高度约 632px。iPhone SE 视口可用高度约 500px，一屏装不下。

已有 change `action-slider-number-input` 改动了同一弹窗的第二级页面（行动详情/数量调整），本 change 改第一级（按钮选择）和全局缩放配置，两者独立不冲突。

## Goals / Non-Goals

**Goals:**
- 彻底阻止移动端所有形式的页面缩放（双指、双击、输入框聚焦自动缩放）
- 经营行动按钮在手机竖屏下完整可见，无需滚动
- 大屏设备充分利用屏幕宽度，不局促
- 保持触屏友好，点击区域不小于 44×44px

**Non-Goals:**
- 不改动第二级详情页（数量调整页）的布局 — 那是 `action-slider-number-input` 的范围
- 不改动行动类型、数量、逻辑或 API — 纯 UI 改动
- 不提取可复用组件 — 如果后续再用 Grid 布局再重构

## Decisions

### D1: Viewport + touch-action 双重锁定

选择三者组合而非只修输入框 font-size：

| 方案 | 覆盖范围 | 可靠性 |
|------|---------|--------|
| 仅修输入框 font-size | 只修了触发条件，没禁止缩放能力 | iOS 版本行为不一致 |
| 仅 maximum-scale=1.0 | 拦截程序缩放，不拦双击 | 某些 iOS 版本双击仍会短暂缩放 |
| **三者组合（选定）** | 无死角 | 任何 iOS 版本均不触发 |

**备选方案**: 只改输入框 font-size 到 16px（不锁 viewport）。否决原因：只治标不治本。

### D2: Grid 布局 + 响应式列数

选择 `display: grid` 而非 `display: flex` + `flex-wrap`。Grid 能精确控制每行列数，`space-y-3` 替换为 `gap-2`。

列数断点映射：

| 断点 | 列数 | 弹窗宽度 | 每格宽度 |
|------|------|---------|---------|
| default (< 640px) | 2 | max-w-sm (384px) | ≈ 168px |
| md (≥ 768px) | 3 | max-w-lg (512px) | ≈ 155px |
| lg (≥ 1024px) | 4 | max-w-xl (576px) | ≈ 130px |

### D3: 奇数项处理 — "个人注资"独占行

第 7 项"个人注资"在 2 列和 4 列布局中会单独落在最后一行。选择用 `col-span-2` / `col-span-3` / `col-span-2` 让它独占一行，视觉上与其他 6 项区分。

**备选方案**: 所有格等宽，最后一行左对齐。否决原因：奇数项左对齐会留白，视觉上不对称。

### D4: 内边距压缩

按钮 `p-4` → `p-3`，图标 `text-lg` → `text-base`，描述文字 `text-xs` → `text-[11px]`。单格高度从 ~76px 降至 ~66px，4 行总高从 ~376px 降至 ~288px。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| `user-scalable=no` 违反 WCAG 可访问性要求，对视障用户不友好 | 游戏场景非公共服务，用户群体不需要页面缩放能力 |
| `touch-action: manipulation` 会影响自定义手势库 | 项目中未使用任何手势库 |
| 描述文字从 `text-xs` 缩到 `text-[11px]`，可读性下降 | 仅第一级选择视图缩，第二级详情页保持 `text-xs` |
| 与已有 change `action-slider-number-input` 改同一文件 | 改不同代码区域（第一级 vs 第二级），合并不冲突 |

## Open Questions

无。
