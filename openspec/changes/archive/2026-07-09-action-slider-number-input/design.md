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

### 单位标签重叠修复

验收发现数字输入框内容与右侧浮动单位标签重叠：

```
修复前:
┌────────── w-28 ──────────┐
│ ┌──────────────────┐     │
│ │ 8px   "12345"  8px│     │
│ └──────────────────┘     │
│                  条  ← 重叠
└──────────────────────────┘

修复后:
┌────────── w-28 ──────────┐
│ ┌──────────────────┐     │
│ │ 8px   "12345"  36px│    │
│ └──────────────────┘     │
│                  条  ← 避开
└──────────────────────────┘
```

**做法**：输入框右侧 padding 从 `px-2`（8px）加大到 `pl-2 pr-9`（36px），为右侧浮动单位标签留出安全空间。

### 默认 0 无法删除

数字输入框初始值为 0，用户无法删除。输入 "123" 时显示 "0123"：

```
┌────────┐  用户按 Backspace → ┌────────┐
│   0    │                     │        │  ← 立即弹回 "0"
└────────┘                     └────────┘
     ↓ 用户输入 123
┌────────┐
│ 0123   │  ← 显示怪，虽然数值 123 是对的
└────────┘
```

**做法**：输入框 `value` 改为 `actionAmount || ''`。当 actionAmount=0 时显示空字符串，用户可直接输入。

**影响范围分析**：
- `CompanyPage.tsx:895` — 唯一受影响处。`value={actionAmount}` → `value={actionAmount || ''}`
- `TradeForm.tsx` 的两个 `<input type="number">` — 使用 `useState('')` 初始为空，无此问题
- `actionAmount` state 类型不变（仍是 number），所有 `actionAmount` 的派生计算不受影响

## 改动位置

改一个文件：

| 文件 | 行号 | 改动 |
|------|------|------|
| `jjs-web/src/pages/CompanyPage.tsx` | ~869-889 | 替换滑块区域为 `slider + input[type=number]` 组合 |
| `jjs-web/src/pages/CompanyPage.tsx` | ~905 | 输入框 `px-2` → `pl-2 pr-9`，避免与单位标签重叠 |
| `jjs-web/src/pages/CompanyPage.tsx` | ~895 | 输入框 `value={actionAmount}` → `value={actionAmount \|\| ''}`，解决默认 0 无法删除问题 |

## 不变部分

- `actionAmount` state 的类型和初始值不变（仍是 `useState(0)`）
- `maxAmount`、`cost` 的计算逻辑不变
- 提交按钮的 `canSubmit` 逻辑不变
- 底部成本/收入显示不变
- 各项行动类型的详情描述文字不变
- `TradeForm.tsx` 的两个输入框不受影响（已用字符串状态）
