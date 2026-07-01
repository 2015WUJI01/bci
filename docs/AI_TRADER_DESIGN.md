# AI 交易者系统设计 v2（烟蒂简化版）

> 将 12 因子 × 7 策略的复杂模型替换为「预期股价 + 滑动概率」的简洁模型。
> 核心理念：**烟蒂投资**——取 max(持续经营估值, 破产清算估值) 作为预期价，自动适配盈利/亏损公司。

---

## 一、设计原则

- **单一模型**。所有 100 个 AI 交易者使用完全相同的决策框架，差异仅在于随机参数（预期偏差、风险容忍度、冷却时间）。
- **烟蒂估值**。`expectedPrice = max(liquidationValue, earningValue)`，不分盈利轨/亏损轨，自然切换。
- **滑动概率**。买卖概率随 (当前价 / 预期价) 线性滑动，无需信号阈值。
- **限价单流动性**。全部限价单，不对称报价范围制造自然价差。
- **自循环生命周期**。AI 资金耗尽后退出，系统自动补充新生 AI，维持市场参与者数量稳定。

---

## 二、核心数据结构

### 2.1 AiTrader

```go
type AiTrader struct {
    ID             string    // "bot_0001" ~ "bot_0100"
    CooldownTicks  int       // 两次操作间隔 tick 数 (2-8)
    RiskTolerance  float64   // 0.15~0.6, 影响仓位激进程度
    CoolDownLeft   int       // 剩余冷却 tick
    SpawnedAt      time.Time
}
```

AI 交易者的现金和持仓复用现有 PlayerState + Holding 表。

### 2.2 无 Strategy 类型

所有 trader 使用同一估值模型，个体差异来自：
- 预期股价 ±10% 随机扰动（每个 AI 每支股票每 tick 独立计算）
- RiskTolerance 随机 (0.15~0.60)
- CooldownTicks 随机 (2~8)

---

## 三、预期股价计算

### 3.1 公式

```go
// 破产清算价值（烟蒂）
liquidationValue = (Cash + CapCount × CapAssetValue) × LiquidationRatio / TotalShares × Prosperity

// 持续经营价值
annualEPS = sum(近4季Profit) / TotalShares   // 年化 EPS
earningValue = annualEPS × 行业PE × Prosperity

// 取高者（min floor = 1 cent）
expectedPrice = max(liquidationValue, earningValue, 1)
```

所有值统一为**分（cents）**，与 CurrentPrice 同单位。

### 3.2 自动适配逻辑

| 公司状态 | earningValue | liquidationValue | 最终 |
|----------|:-----------:|:----------------:|:----:|
| 高利润 | 很高 | 较低 | earningValue |
| 微利 | 略低 | 略低 | 略高者 |
| 亏损 (EPS≤0) | ≤0 | >0 | liquidationValue |

无需人为划分盈利/亏损轨道。

### 3.3 个体扰动

```go
expectedPrice = expectedPrice × random(0.85, 1.15)
```

每个 AI 对同一支股票的预期略有不同，自然形成对手盘。

---

## 四、决策模型

### 4.1 每 Tick 执行流

```
对每个到期 trader:
  1. 50% 概率 → 什么都不做, 跳过本 tick
  2. 采样股票 (20%, 上限20, 下限3)
  3. 对每支采样股票:
     a. 止损检查 (保留现有逻辑)
     b. 计算 expectedPrice = 烟蒂公式 × random(0.85, 1.15)
     c. ratio = CurrentPrice / expectedPrice
     d. buyProb = slide(ratio)  // 滑动概率
     e. rand < buyProb → 买入, else → 卖出
     f. 计算限价单报价范围
     g. 计算仓位规模
     h. 提交订单
  4. CoolDownLeft = CooldownTicks
```

### 4.2 滑动概率

```
buyProb:
  ratio ≤ 0.5   → 0.90
  ratio ∈ (0.5, 1.0] → 线性 0.9→0.5
  ratio ∈ [1.0, 2.0) → 线性 0.5→0.1
  ratio ≥ 2.0   → 0.10

sellProb = 1 - buyProb  (决定操作后必然买卖其一)
```

| ratio | 含义 | buyProb | 倾向 |
|:-----:|------|:------:|------|
| 0.5 | 股价仅为预期的一半 | 90% | 强烈买入 |
| 1.0 | 股价等于预期 | 50% | 均衡 |
| 2.0 | 股价是预期的两倍 | 10% | 强烈卖出 |

### 4.3 报价范围

```
price < expected  → 报价 ∈ [price × 0.9,  price × 1.2]
price ≥ expected  → 报价 ∈ [price × 0.8,  price × 1.1]
```

不对称设计：低估时愿意支付溢价（上限 120%），高估时只愿出折扣价（上限 110%）。

买单和卖单使用相同范围——范围不因买卖方向变化。

### 4.4 仓位规模

```go
// 买入
availableCash = Cash - FrozenCash
maxSpend = availableCash × RiskTolerance
qty = maxSpend / price, clamp 100 ~ MaxOrderQty

// 卖出
availableQty = Holding.Qty - FrozenQty
maxSell = availableQty × RiskTolerance
qty = clamp(maxSell, 100, MaxOrderQty)
```

简化：不再乘以 |signal| 系数，直接用 RiskTolerance。

---

## 五、撤单策略（保留）

与 v1 一致：

```
对每个挂单:
  ├─ 股票不存在或价格归零 → 撤
  ├─ 挂单存活 > 120s → 撤
  ├─ 买单: (现价 - 挂单价) / 现价 > 5% → 撤
  ├─ 卖单: (挂单价 - 现价) / 现价 > 5% → 撤
  └─ 上述均不满足 → 保留
```

---

## 六、止损闸门（保留）

与 v1 一致：

```
if holding != nil && holding.Qty > 0:
    gainPct = (currentPrice - avgCost) / avgCost
    threshold = -(0.25 + RiskTolerance × 0.60)
    if gainPct < threshold → 市价全平持仓, 跳过该股票
```

---

## 七、生命周期（保留）

- **初始化**：零持仓起步，随机初始资金 ¥5,000~¥500,000（分）
- **耗尽条件**：Cash < ¥100 且持仓为零
- **补给**：每 100 tick 检查，耗尽者重新分配随机资金 + 随机参数
- **恢复**：重启时从 DB 恢复 bot 财务状态，随机分配新参数

---

## 八、关键常量

| 参数 | 值 | 说明 |
|------|-----|------|
| 交易者总数 | 100 | 固定目标数量 |
| 初始资金范围 | ¥5,000 ~ ¥500,000 | 按分存储 |
| CoolDown 范围 | 2 ~ 8 tick | 4s ~ 16s 间隔 |
| RiskTolerance | 0.15 ~ 0.60 | 仓位激进程度 |
| 跳过概率 | 50% | 每 tick 50% 什么都不做 |
| 采股比例 | 20% | 上限 20 支，下限 3 支 |
| 烟蒂清算比 | 75% | LiquidationRatio |
| 预期扰动范围 | ±10% | 每 AI 每股票随机扰动 |
| 撤单偏差阈值 | 5% | 挂单价偏离市价 > 5% 时撤单 |
| 撤单最大年龄 | 120s | 挂单硬超时 |
| 止损基准偏移 | 0.25 | threshold = -(0.25 + RT×0.60) |
| 退出现金阈值 | ¥100 (10,000分) | 现金 + 持仓为零时重置 |
| 补给检查间隔 | 100 tick | ~200s |

---

## 九、与 v1 的区别

| 项目 | v1 (旧) | v2 (新) |
|------|---------|---------|
| 因子体系 | 12 因子 (6理性+5行为+1噪声) | 无因子，烟蒂估值 |
| 策略类型 | 7 种策略 × 各自权重 | 统一模型 |
| 市场情绪 | EMA 情绪指数传导 15% | 移除 |
| 市价单 | |signal|>0.5 市价单 | 全部限价单 |
| 下单触发 | |signal|>0.2 | 买卖方向必然选一 |
| 信号值 | 连续 [-1,1] | 二元 (买/卖) |
| 跳过概率 | 无显式跳过 | 50% tick 级别跳过 |
| 报价 | 信号驱动宽幅 (±30%) | 预期价方向驱动 |
| 冷却 | 5-30 tick | 2-8 tick |

---

## 十、目录结构

```
jjs-server/internal/bots/
├── ai_trader.go     # AiTrader struct + 初始化函数
├── scheduler.go     # ScheduleTick: 新决策流
├── helpers.go       # 预期股价计算 + 滑动概率 + 报价范围 + 订单构建
├── lifecycle.go     # 初始化 + 枯竭重置 + 新生补充
├── stoploss.go      # 止损闸门 (不变)
└── metrics.go       # BotMetrics + TraderStats
```

已删除：`factors.go`, `sentiment.go`
