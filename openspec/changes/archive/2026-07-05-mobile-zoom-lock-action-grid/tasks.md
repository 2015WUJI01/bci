## 1. 全局缩放锁定

- [x] 1.1 `index.html`: 在 viewport meta 中添加 `maximum-scale=1.0, user-scalable=no`
- [x] 1.2 `index.css`: 在 `@layer base` 中添加 `html { touch-action: manipulation }`

## 2. 经营行动按钮 → 响应式双列网格

- [x] 2.1 `CompanyPage.tsx`: 将按钮容器从 `<div className="p-4 space-y-3">` 改为 `<div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 p-3">`
- [x] 2.2 `CompanyPage.tsx`: 每项按钮从 `w-full p-4` 改为 `p-3`，最后一项 (个人注资) 添加 `col-span-2 md:col-span-3 lg:col-span-2`
- [x] 2.3 `CompanyPage.tsx`: 按钮内部 icon 从 `text-lg` 改为 `text-base`，`mb-1` 改为 `mb-0.5`，描述文字从 `text-xs` 改为 `text-[11px]`
- [x] 2.4 `CompanyPage.tsx`: Modal 宽度从 `max-w-sm` 扩展为 `max-w-sm md:max-w-lg lg:max-w-xl`

## 3. 验证

- [x] 3.1 `pnpm typecheck` 通过
- [ ] 3.2 `pnpm lint` 通过（阻塞：项目中缺少 eslint.config.*，非本次改动导致。已确认 typecheck 通过）
- [ ] 3.3 手动测试：
  - [ ] 手机竖屏下 7 个按钮完整可见，不滚动
  - [ ] 2 列布局对齐正确，"个人注资"独占一行
  - [ ] 缩放锁定后 iOS 输入框聚焦不再放大
  - [ ] PC 浏览器窗口拉宽时列数自动切换 (2→3→4)
