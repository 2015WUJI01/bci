## 1. 创建 fix 分支

- [x] 1.1 从 `master` 创建 `fix/volume-histogram-zero-axis` 分支

## 2. 修改 KlineChart.tsx 中 volume priceScale 的 scaleMargins

- [x] 2.1 打开 `jjs-web/src/components/KlineChart.tsx`
- [x] 2.2 将 `volumeSeries.priceScale().applyOptions()` 中 `bottom` 从 `0` 改为 `0.03`
  - 原代码：`scaleMargins: { top: 0.2, bottom: 0 }`
  - 新代码：`scaleMargins: { top: 0.2, bottom: 0.03 }`

## 3. 验证

- [x] 3.1 运行 `pnpm typecheck` 确保类型无误
- [ ] 3.2 运行 `pnpm lint` 确保 lint 通过（当前环境缺少 eslint 配置，与改动无关）
- [ ] 3.3 本地启动 `pnpm dev` 查看图表底部是否显示 0 基线
