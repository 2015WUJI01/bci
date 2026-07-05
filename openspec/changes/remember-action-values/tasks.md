## 1. 新增 localStorage 读写逻辑

- [x] 1.1 定义 `STORAGE_KEY = 'bci_last_action_values'` 常量和 `Record<string, number>` 类型
- [x] 1.2 新增 `useRef<Record<string, number>>({})` 存储记忆值
- [x] 1.3 新增 `useEffect`，初始化时从 localStorage 读取到 ref（try/catch 兜底）

## 2. 修改选行动逻辑

- [x] 2.1 抽取 `handleActionSelect(view: string)` 函数：从 ref 取记忆值，`Math.min(last ?? 0, maxAmount)` 设默认值
- [x] 2.2 7 个按钮的 `onClick` 从行内 `setActionView(...); setActionAmount(0); ...` 改为调用 `handleActionSelect`

## 3. 提交成功后更新缓存

- [x] 3.1 在 `handleSubmitAction` API 成功后（`try` 块内），更新 `ref.current[type] = amount` 并写入 localStorage

## 4. 验证

- [x] 4.1 `pnpm typecheck` 通过
- [ ] 4.2 手动测试：提交一次行动 → 关闭 → 重新选同类型 → 默认显示上次提交值
- [ ] 4.3 验证越界场景：记忆值 > 当前 maxAmount 时自动 clamp
- [ ] 4.4 验证首次使用（无记忆）默认 0
- [ ] 4.5 刷新页面后验证数据仍保留
