## Why

移动端经营行动弹窗有两个影响体验的问题：一是 iOS 输入框聚焦时页面自动缩放，二是7个行动按钮在单列布局下高度过长，小屏手机一屏装不下。两者都集中在经营行动弹窗，需要一并解决。

## What Changes

### 1. 全局移动端缩放锁定

在 `index.html` 的 viewport meta 中加入 `maximum-scale=1.0, user-scalable=no`，同时在 `index.css` 中添加 `html { touch-action: manipulation }`。三者组合彻底阻止移动端任何形式的缩放（双指缩放、双击缩放、输入框聚焦自动缩放）。

**涉及文件**:
- `jjs-web/index.html` — viewport meta 一行改动
- `jjs-web/src/index.css` — 新增一条 touch-action 规则

### 2. 经营行动按钮改为响应式双列网格

将经营行动弹窗第一级（7个行动按钮的选择视图）从当前纵向单列列表改为响应式 Grid 布局：
- 手机竖屏 (default)：2 列
- 平板 / PC 小窗 (≥768px)：3 列
- PC 大屏 (≥1024px)：4 列

第 7 项"个人注资"在奇数列时使用 `col-span` 独占一行，与其他 6 项在语义和视觉上区分。

弹窗宽度同步响应式：`max-w-sm` → `max-w-lg (md)` → `max-w-xl (lg)`。

**涉及文件**:
- `jjs-web/src/pages/CompanyPage.tsx` — 按钮容器从 `space-y-3` 改为 `grid`，每项从 `w-full p-4` 改为响应式 grid item

### 3. 视觉微调

按钮内边距从 `p-4` 压缩到 `p-3`，图标从 `text-lg` 缩到 `text-base`，描述文字从 `text-xs` 缩到 `text-[11px]`，适配更紧凑的网格布局。

## Capabilities

### New Capabilities

无。两个改动均为现有功能的配置优化和 UI 重构，不引入新能力。

### Modified Capabilities

无。现有 `openspec/specs/` 为空，且按钮布局改动不影响功能需求。

## Impact

| 影响范围 | 说明 |
|---------|------|
| `jjs-web/index.html` | viewport meta 属性修改 |
| `jjs-web/src/index.css` | 新增全局 `touch-action` |
| `jjs-web/src/pages/CompanyPage.tsx` | 行动按钮选择视图的布局和样式重写 |
| 可访问性 | `user-scalable=no` 禁止用户缩放页面，但游戏场景不需要此能力 |
| 已有 change `action-slider-number-input` | 该 change 改的是第二级详情页（数量调整），本 change 改的是第一级（按钮选择），互不冲突 |
