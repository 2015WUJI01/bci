# 设计 — 景气度随机游走改进

## 目标

用正态分布步长 + 非对称边界重写景气度游走算法，解决均匀分布缺乏周期感、对称边界比例不平衡的问题。

---

## 算法设计

### 1. 非对称边界计算

```
对每个行业：
  ProsperityMin      (不变，沿用当前值)
  ProsperityMax = 1 / ProsperityMin   (非对称，比例等价)
```

各行业新边界：

| 行业 | 当前 Min | 当前 Max | 新 Max (≈ 1/Min) |
|------|----------|----------|-------------------|
| tech | 0.85 | 1.15 | **1.1765** |
| finance | 0.90 | 1.10 | **1.1111** |
| manufacturing | 0.90 | 1.10 | **1.1111** |
| mining | 0.85 | 1.15 | **1.1765** |
| consumer | 0.94 | 1.06 | **1.0638** |
| healthcare | 0.94 | 1.06 | **1.0638** |

### 2. 偏差归一化（非对称）

对称边界时 `halfRange = (max - min) / 2` 就可把偏离度归到 [-1, +1]。非对称后需要分段归一化：

```go
func calcDeviation(p, min, max float64) float64 {
    if p >= 1.0 {
        return (p - 1.0) / (max - 1.0)  // → [0, +1]
    }
    return (p - 1.0) / (1.0 - min)      // → [-1, 0)
}
```

### 3. 正态分布步长

用 Go `math/rand.NormFloat64()` 生成标准正态分布 N(0,1) 的随机数，乘以 `ProsperityStdDev` 得到实际步长：

```go
rawStep := rand.NormFloat64() * cfg.ProsperityStdDev
```

效果对比：

| 步长范围 | 均匀分布 | 正态分布 (σ=0.025) |
|----------|----------|-------------------|
| ±0.01 以内 | 20% 的季度 | **~68% 的季度**（小波动） |
| ±0.02~0.05 | 80% 的季度 | **~27% 的季度**（中等波动） |
| ±0.05 以上 | 无 | **~5% 的季度**（大波动） |

正态分布自动产生"大部分小波动、偶尔大波动"的效果，无需额外的修正脉冲逻辑。

### 4. 新 `WalkProsperity()` 完整算法

```go
func WalkProsperity(oldProsperity float64, cfg IndustryConfig) float64 {
    // 1. 正态分布随机步长
    rawStep := rand.NormFloat64() * cfg.ProsperityStdDev

    // 2. 向心回归（非对称归一化）
    dev := calcDeviation(oldProsperity, cfg.ProsperityMin, cfg.ProsperityMax)
    regressionStep := -dev * cfg.ProsperityRegression

    // 3. 修正脉冲（小概率，仅极端偏离时触发）
    if rand.Float64() < cfg.CorrectionProb {
        pulse := -dev * cfg.CorrectionPulse
        // 脉冲替换当季步长（包括回归）
        return clamp(oldProsperity+pulse, cfg.ProsperityMin, cfg.ProsperityMax)
    }

    // 4. 步长 = 随机 + 回归，再 clamp 到 ±MaxStep 防止极端单季变化
    change := clamp(rawStep+regressionStep, -cfg.ProsperityMaxStep, cfg.ProsperityMaxStep)

    return clamp(oldProsperity+change, cfg.ProsperityMin, cfg.ProsperityMax)
}
```

注：虽然正态分布理论上无限尾，但实际游戏中每季度仅 6 个行业各一次采样，数十年游戏内也极难出现 ±4σ 以上的值。`ProsperityMaxStep` 的 clamp 作为安全网保留。

### 5. 参数变更

`IndustryConfig` 字段变更：

| 字段 | 变化 | 说明 |
|------|------|------|
| `ProsperityMaxStep` | 保留 | 作为单季变化硬上限安全网 |
| `ProsperityStdDev` | **新增** | 正态分布标准差，控制日常波动幅度 |
| `ProsperityMax` | 改为 `1/Min` | 非对称边界 |
| `ProsperityMin` | 不变 | — |

各行业新参数值：

| 行业 | Min | Max | StdDev | MaxStep(不变) | Regression | CorrProb | CorrPulse |
|------|-----|-----|--------|---------------|------------|----------|-----------|
| manufacturing | 0.90 | 1.1111 | 0.020 | 0.04 | 0.02 | 0.04 | 0.05 |
| mining | 0.85 | 1.1765 | 0.025 | 0.05 | 0.03 | 0.05 | 0.06 |
| tech | 0.85 | 1.1765 | 0.025 | 0.05 | 0.03 | 0.05 | 0.06 |
| finance | 0.90 | 1.1111 | 0.020 | 0.04 | 0.02 | 0.04 | 0.05 |
| consumer | 0.94 | 1.0638 | 0.015 | 0.03 | 0.01 | 0.03 | 0.03 |
| healthcare | 0.94 | 1.0638 | 0.015 | 0.03 | 0.01 | 0.03 | 0.03 |

StdDev 取 MaxStep 的一半，使 ±2σ ≈ MaxStep 的幅度，兼顾正态分布特性与现有波动幅度。

---

## 改动位置

| 文件 | 改动 |
|------|------|
| `jjs-server/internal/engine/industry.go` | `IndustryConfig` 新增 `ProsperityStdDev float64`；更新各行业 `ProsperityMax`、新增 `ProsperityStdDev` |
| `jjs-server/internal/engine/prosperity.go` | 重写 `WalkProsperity()`，新增 `calcDeviation()`；`WalkProsperity` 单元测试覆盖可手动运行 |

---

## 不变部分

- `IndustryProsperity` 模型、表结构、store 层不变
- `PriceElasticity` 传导公式不变
- 制造业/矿业/AI交易者/IPO/领袖板使用景气度的方式不变
- `RestoreOrSeedGlobalQuarter()` 不变
