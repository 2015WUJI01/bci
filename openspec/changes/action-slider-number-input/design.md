# 设计 — 行动滑块增加数字输入框

## 目标

经营行动弹窗中，用户既能通过滑块快速拉取大致数值，也能通过输入框精确键入目标值。

## 方案

### 当前状态（修改前）

```
┌─────────────────────────────────────┐
│  招募岗位数                   123 岗位 │
│  ═══════════════●═══════════════════  │
│  ¥3,000/岗                   已到上限 │
└─────────────────────────────────────┘
```

### 修改后状态

```
┌─────────────────────────────────────┐
│  招募岗位数                           │
│  ═══════════●══════════ [ 123 岗位 ] │
│  ¥3,000/岗                   已到上限 │
└─────────────────────────────────────┘
```

### 布局结构

```
<div class="flex items-center gap-3">
  <input type="range" class="flex-1" />      ← 滑块占剩余宽度
  <div class="relative shrink-0 w-28">       ← 输入框固定宽度
    <input type="number" />                   ← 数字输入
    <span>单位</span>                          ← 单位标签（浮在右侧）
  </div>
</div>
```

### 数据流

```
滑块 onChange ──→ Number(e.target.value) ──→ setActionAmount
                                                      ↑
输入框 onChange ──→ Number(e.target.value) ────────────┘
输入框 onBlur ────→ clamp [0, maxAmount] ─────────────┘ (失焦纠正)
```

两个输入控件共享同一个 `actionAmount` state，始终双向同步。

### 输入框行为

- **type="number"**，但隐藏浏览器默认的上下箭头（`appearance:textfield` + `::-webkit-inner-spin-button: none`）
- **step** 与滑块保持一致：分红 `0.01`，其余 `1`
- **失焦 clamp**：小于 0 → 0，大于 maxAmount → maxAmount
- **空值处理**：输入为空时视为 0（`e.target.value === '' ? 0 : Number(...)`）
- **分红精度**：分红场景下 `value={actionAmount.toFixed(2)}`，onChange 时 `Math.round(v * 100) / 100` 保留两位小数

### 样式

| 元素 | 样式 |
|------|------|
| 滑块 | `flex-1 accent-accent-blue`（与原来一致） |
| 输入框容器 | `relative shrink-0 w-28` |
| 输入框 | `w-full px-2 py-1.5 text-xs text-right bg-bg-input border border-border rounded` |
| 输入框聚焦 | `focus:outline-none focus:border-accent-blue` |
| 单位标签 | `absolute right-2 top-1/2 -translate-y-1/2 text-[11px] text-text-muted pointer-events-none` |

## 改动位置

只改一个文件：

| 文件 | 行号 | 改动 |
|------|------|------|
| `jjs-web/src/pages/CompanyPage.tsx` | ~869-889 | 替换滑块区域为 `slider + input[type=number]` 组合 |

## 不变部分

- `actionAmount` state 的类型和初始值不变
- `maxAmount`、`cost` 的计算逻辑不变
- 提交按钮的 `canSubmit` 逻辑不变
- 底部成本/收入显示不变
- 各项行动类型的详情描述文字不变
