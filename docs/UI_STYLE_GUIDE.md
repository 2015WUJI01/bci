# 大猫投资 - UI 与风格设计文档（jjs-web）

> 本文档适用于 **jjs-web**（React 18 + TypeScript + Vite + Tailwind CSS + Zustand + TanStack Query/Router），旧版 Vanilla JS 前端已废弃。

---

## 1. 设计理念

- **专业交易终端风格** —— 暗色主题，信息密度高
- **中国股市配色** —— 红涨/绿跌（与西方相反）
- **移动优先** —— 底部 Dock 导航，三档响应式断点
- **Utility-First** —— 优先使用 Tailwind utility class，尽量不写自定义 CSS

---

## 2. 设计令牌（Tailwind 自定义主题）

定义于 `tailwind.config.ts`。

### 2.1 背景色系

| Token | 色值 | 用途 |
|-------|------|------|
| `bg-primary` | `#0a0e17` | 最深底色 |
| `bg-secondary` | `#111827` | 次要背景（登录页卡片） |
| `bg-card` | `#1a2332` | 面板/卡片/Dock 背景 |
| `bg-card-hover` | `#1e2a3d` | 卡片悬停（较少直接使用） |
| `bg-input` | `#0f1729` | 输入框/统计框背景 |
| `bg-hover` | `rgba(59,130,246,0.1)` | 行悬停高亮 |

### 2.2 文本色系

| Token | 色值 | 用途 |
|-------|------|------|
| `text-primary` | `#e8edf5` | 正文/主标题 |
| `text-secondary` | `#94a3b8` | 副标题/辅助文字 |
| `text-muted` | `#64748b` | 占位符/弱化标签 |

### 2.3 语义色彩

| Token | 色值 | 用途 |
|-------|------|------|
| `accent-blue` | `#3b82f6` | 主品牌色/选中态/链接 |
| `accent-red` | `#ef4444` | 错误/危险/警告 |
| `accent-green` | `#10b981` | 成功/已连接 |
| `accent-gold` | `#f59e0b` | 品牌标题/现金高亮 |
| `accent-purple` | `#8b5cf6` | 预留 |
| `accent-cyan` | `#06b6d4` | 预留 |

### 2.4 交易语义色

| Token | 色值 | 场景 |
|-------|------|------|
| `buy` | `#ef4444`（红） | 买入按钮 |
| `sell` | `#10b981`（绿） | 卖出按钮 |
| `up` | `#ef4444`（红） | 上涨/正值 |
| `down` | `#10b981`（绿） | 下跌/负值 |

> ⚠️ 中国股市配色：**红色 = 涨/买**，**绿色 = 跌/卖**（与 Western 惯例相反）。

### 2.5 边框与阴影

| Token | 值 | 用途 |
|-------|-----|------|
| `border` | `#1e293b` | 默认分割线/边框 |
| `border-light` | `#334155` | 面板悬停边框 |
| `shadow` | `0 8px 32px rgba(0,0,0,0.5)` | 大阴影（模态框） |
| `shadow-sm` | `0 2px 8px rgba(0,0,0,0.3)` | 小阴影（卡片） |
| `shadow-glow` | `0 0 20px rgba(59,130,246,0.15)` | 蓝色荧光 |

### 2.6 圆角

| Token | 值 |
|-------|-----|
| `rounded` | `10px` |
| `rounded-sm` | `6px` |
| `rounded-lg` | `14px` |

### 2.7 渐变

| Token | 值 |
|-------|-----|
| `bg-gradient-header` | `linear-gradient(135deg, #1a2332, #0f1729)` |
| `bg-gradient-gold` | `linear-gradient(135deg, #f59e0b, #d97706)` |
| `bg-gradient-blue` | `linear-gradient(135deg, #3b82f6, #2563eb)` |
| `bg-gradient-green` | `linear-gradient(135deg, #10b981, #059669)` |

---

## 3. 排版

### 3.1 字体

```ts
// tailwind.config.ts
fontFamily: {
  sans: ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
  mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
}
```

- 优先系统原生字体，中文优化（苹方/微软雅黑）
- 金融数值使用 `font-mono` + `tabular-nums` 保证对齐

### 3.2 常用字阶

| 场景 | 大小 | 字重 |
|------|------|------|
| 股价/资产大数 | `text-lg` ~ `text-2xl` | 700 |
| 面板标题 | `text-sm` | 600~700 |
| 表格数据 | `text-xs` | 400~600 |
| 辅助文字 | `text-[11px]` | 400 |
| 微小标签 | `text-[10px]` | 400 |

---

## 4. 布局结构

### 4.1 页面路由

| 路径 | 组件 | 需登录 |
|------|------|--------|
| `/login` | `AuthPage` | 否 |
| `/game/market` | `MarketPage` | 是 |
| `/game/portfolio` | `PortfolioPage` | 是 |
| `/game/company` | `CompanyPage` | 是 |
| `/game/company/quarterly` | `QuarterlyPage` | 是 |
| `/game/leaderboard` | `LeaderboardPage` | 是 |

### 4.2 GameLayout（主布局）

```
┌─────────────────────────────────────┐
│  Header（sticky）                    │
│  [大猫投资] [标语] [季度] [倒计时]     │
│  [连接状态] [在线] [昵称▼] [现金]     │
├─────────────────────────────────────┤
│  <Outlet />（flex-1, overflow-y-auto）│
│                                     │
├─────────────────────────────────────┤
│  Dock（sticky bottom, 4 Tab）        │
│  📈市场 📊持仓 🏢公司 🏆排行         │
└─────────────────────────────────────┘
```

- Header 响应式三档：`sm` 隐藏标语，`md` 隐藏延迟/在线人数
- Dock 4 个 Tab，激活态 `[&.active]:text-accent-blue [&.active]:border-t-2 [&.active]:border-accent-blue`
- 路由守卫通过 `beforeLoad` 检查 `authStore.isAuthenticated`

---

## 5. 组件约定

### 5.1 文件组织

```
src/
  api/           # 数据层（查询 hooks、WS 客户端）
  components/    # 共享组件（Dock, Header, Panel, Toast, TradeForm, KlineChart）
  pages/         # 路由页面组件
  stores/        # Zustand stores（authStore, gameStore）
  types/         # TypeScript 定义
```

### 5.2 命名规则

- 组件文件：PascalCase，named export
- 工具文件：camelCase
- 别名：`@/` → `src/`
- 内部辅助组件：定义在同文件中，函数名首字母大写

### 5.3 Panel 组件

通用卡片容器，含标题栏、可选右侧操作区、可选标题前缀。

```tsx
<Panel title="标题" headerAction={<button>...</button>}>
  {/* 内容 */}
</Panel>
```

渲染结构：`bg-bg-card rounded border border-border shadow-sm`，标题栏渐变底纹。

### 5.4 按钮体系

定义在 `index.css` `@layer components`：

| Class | 用途 |
|-------|------|
| `btn` | 基础按钮 |
| `btn-primary` | 蓝色主要操作 |
| `btn-secondary` | 灰色次要操作 |
| `btn-buy` | 买入（红色） |
| `btn-sell` | 卖出（绿色） |
| `btn-danger` | 危险操作 |
| `btn-sm` / `btn-xs` | 尺寸变体 |
| `btn-full` | 通栏按钮 |

### 5.5 价格颜色

```tsx
className={`font-mono ${change >= 0 ? 'text-up' : 'text-down'}`}
```

### 5.6 Tab 切换模式

活动项用 `bg-accent-blue text-white`，非活动项用 `text-text-muted hover:text-text-primary`。

### 5.7 表格

- 表头 `sticky top-0 bg-bg-card`
- 行边框 `border-b border-border/40`，悬停 `hover:bg-white/[0.03]`
- 字号 `text-xs`

### 5.8 弹窗

```tsx
<div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
  <div className="bg-bg-card border border-border rounded-lg shadow-xl p-4 max-w-md w-full mx-3">
    {/* 内容 */}
  </div>
</div>
```

---

## 6. 表单元素

### 6.1 全局输入框样式

定义于 `index.css` `@layer components`：

```css
input[type="email"],
input[type="password"],
input[type="text"],
select {
  @apply w-full px-3.5 py-2.5 bg-bg-input border border-border rounded-sm
         text-text-primary text-[15px] outline-none;
}
```

### 6.2 ⚠️ 特异性约定：不用 `input[type="number"]` 设置全局 padding

> **不要**在 `@layer components` 中用 `input[type="number"]` 选择器设置 padding。

原因：`input[type="number"]` 选择器特异性 (0,1,1) 高于 Tailwind utility class (0,1,0)，会导致 `pr-9` 等 padding utility 被覆盖失效（详见 `fix/number-input-padding-specificity` 分支）。

对于需要自定义 padding 的数字输入框，在行内通过 utility class 完整声明样式，并手动隐藏 spinner：

```tsx
<input
  type="number"
  className="w-full pl-2 pr-9 py-1.5 text-xs text-right bg-bg-input border border-border rounded
             focus:outline-none focus:border-accent-blue
             [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none
             [&::-webkit-outer-spin-button]:appearance-none"
/>
```

---

## 7. 动画系统

| 类名 | 类型 | 用途 |
|------|------|------|
| `animate-flash-up` | 背景色脉冲消失 | 价格上涨闪烁 |
| `animate-flash-down` | 背景色脉冲消失 | 价格下跌闪烁 |
| `animate-tick-pulse` | 透明度交替 | 倒计时 ≤5s 紧迫态 |
| `animate-ftp-in` | 淡入+上移 | 面板打开 |

---

## 8. 响应式设计

### 8.1 断点

使用 Tailwind 默认断点（无自定义）：

| 断点 | 最小宽度 | 主要变化 |
|------|----------|----------|
| 默认 | 0（mobile first） | 单列，窄边距 |
| `sm` | 640px | Header 显示标语 |
| `md` | 768px | Header 显示延迟/在线人数 |
| `lg` | 1024px | 市场页面双列布局 |

### 8.2 Header 响应式行为

- `< sm`：只显示品牌名 + 昵称 + 现金
- `sm`：显示标语
- `md`：显示连接延迟 + 在线人数
- 退出按钮在昵称下拉菜单中

---

## 9. 其他约定

### 9.1 无图标库

直接使用 Emoji 字符代替图标库：📈 📊 🏢 🏆 💻 🏦 🏭 ⛏️ 等。

### 9.2 语言

全界面简体中文。

### 9.3 暗色主题唯一

无亮色主题，无切换计划。

### 9.4 价格单位

股票价格后端以 `分`（cents）存储，前端除以 100 展示，使用 `¥` 前缀 + `toLocaleString()`。

### 9.5 滚动条

自定义 4px 细滚动条，颜色 `#1e293b`。`.scrollbar-hide` 类可完全隐藏。

### 9.6 状态管理分层

| 层级 | 工具 | 用途 |
|------|------|------|
| 全局 UI/游戏状态 | Zustand store | auth, ws, 实时行情 |
| 服务端数据 | TanStack Query | REST 查询缓存 |
| 临时 UI 状态 | `useState` | 表单输入、弹窗开关 |
| Toast | Context | 全局通知 |
