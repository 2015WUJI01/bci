# Tasks — 行动滑块增加数字输入框

## 前置条件

- [x] 已理解 `CompanyPage.tsx` 的行动弹窗结构
- [x] 已确认 `actionAmount` 为 `number` 类型，与 `Number()` 转换兼容

---

## Task 1: 替换滑块为滑块+输入框组合 ✅

**文件**: `jjs-web/src/pages/CompanyPage.tsx` (~line 869-889)

- [x] 将 `<span>` 数值显示替换为 `<input type="number">`
- [x] 输入框与滑块共享 `actionAmount` state，`onChange` 双向同步
- [x] 输入框添加 `onBlur` 将值 clamp 到 [0, maxAmount]
- [x] 输入框隐藏浏览器默认上下箭头
- [x] 单位标签（岗位/¥/条/人等）浮在输入框右侧
- [x] 分红场景保留 `toFixed(2)` 精度

**涉及的行 (旧版)**:
```
869-889 行: 数值显示 + range slider
```
**替换后**: slider (`flex-1`) + 数字输入框 (`w-28 shrink-0`)

---

## Task 2: 验证 ⏳

- [ ] `pnpm typecheck` 通过
- [ ] `pnpm lint` 通过
- [ ] 手动测试所有 7 种行动类型：
  - [ ] expand: 输入数值 ≥ 0，确认成本计算正确
  - [ ] hire: 输入招募人数，同步显示预期实招人数
  - [ ] layoff: 输入裁员人数，同步显示预计产能
  - [ ] sell_assets: 输入出售数量，同步显示收入
  - [ ] marketing: 输入投入金额，同步显示需求提升
  - [ ] inject_capital: 输入注资金额，clamp 到个人现金上限
  - [ ] dividend: 输入每股分红（0.01 步进），确认 `toFixed(2)` 精度
- [ ] 验证失焦时数值自动 clamp 到合法范围
- [ ] 验证单位标签正确显示（¥/岗位/人/条/单位）
- [ ] 验证分红场景输入 0.01、0.1、1.23 等值均正确保留两位小数

---

## Task 3: 修复输入框与单位标签重叠

- [x] 3.1 确认问题：右对齐数字文本与 `absolute right-2` 单位标签重叠
- [x] 3.2 输入框 `px-2` → `pl-2 pr-9`，右侧留出 36px 避开标签
- [ ] 3.3 验证所有行动类型单位标签（条/人/岗/¥/%/股/元/次/单位）均不与数字重叠（需手动验证）
