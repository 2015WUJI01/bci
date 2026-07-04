## ADDED Requirements

### Requirement: Company Quarterly Settlement

系统 SHALL 执行公司季度结算，分为两个阶段：预报（pre-generate）和最终结算（finalize）。

结算顺序：
1. `finalizeQuarter(currentQ)` — 结算刚结束的季度，利润加入公司现金
2. `GlobalQuarter.Add(1)` — 推进全局季度号
3. `processAllBuildQueues(newQ)` — 处理到期的建造订单
4. `WalkProsperity()` — 更新各行业景气度
5. `preGenerateQuarter(newQ)` — 异步生成新季度预报

#### Scenario: Finalize updates company cash

- **WHEN** 季度最终结算执行时
- **THEN** `Company.Cash` SHALL 增加 `CompanyQuarterly.Profit`，`Company.LastSettledQuarter` SHALL 更新为当前季度号

#### Scenario: Pre-generate does not touch cash

- **WHEN** 预报阶段生成 CompanyQuarterly 记录时
- **THEN** `Company.Cash` SHALL 保持不变，预报记录的 `Quarter` 等于 `GlobalQuarter`

#### Scenario: Skip already settled company

- **WHEN** `Company.LastSettledQuarter >= quarter` 时
- **THEN** `settleCompanyBaseline` SHALL 直接返回 nil，不重复结算

### Requirement: Manufacturing Cost Model

制造业公司季度利润计算 SHALL 使用以下成本拆分模型：

```
BaseMaintenance  = CapCount × BaseMaintenanceRate
OperationalCost  = activeLines × OperationalCostRate
LaborCost        = employees × LaborRate
WarehouseCost    = inventory × 0.5
TotalCost        = LaborCost + BaseMaintenance + OperationalCost + WarehouseCost
Profit           = Revenue - TotalCost
```

#### Scenario: Manufacturing settlement with full capacity

- **WHEN** 员工产出 < 产线产能上限时
- **THEN** `ProdQty = employees × 2000`，`activeLines = ceil(employees × 2000 / 10000)`

#### Scenario: Manufacturing settlement capped by capacity

- **WHEN** 员工产出 ≥ 产线产能上限时
- **THEN** `ProdQty = capCount × 10000`，所有产线为 active

#### Scenario: Demand cap by inventory and production

- **WHEN** 需求 > (ProdQty + prevInventory) × 2.0 时
- **THEN** `Demand` SHALL 被截断为 `(ProdQty + prevInventory) × 2.0`

### Requirement: Mining Settlement

矿业公司 SHALL 使用以下特殊结算逻辑：

```
产量 = min(员工产出, 储量上限)
销量 = min(产量 + 库存, 需求)
储量 = max(0, CapCount - 产量)
```

储量每季递减，每季开采量不超过储量的 20%。

#### Scenario: Mining ore depletion

- **WHEN** 矿业公司持续开采
- **THEN** `CapCount`（矿物储量）SHALL 逐季递减，开采量 ≤ CapCount × 0.2

#### Scenario: Mining exploration expands reserves

- **WHEN** 矿业公司提交扩产（探矿）操作时
- **THEN** 新增储量 SHALL 由 `ProspectOreReserves(rng)` 在提交时随机确定

### Requirement: Order Book Matching

交易引擎 SHALL 执行限价单和市价单撮合，遵循价格优先、时间优先规则。

撮合流程：
1. 买单冻结资金（`FreezeCash`）
2. 查询对手单（限价单：价格约束；市价单：全部对手单）
3. 按价格 ASC + SeqNum ASC 排序
4. 逐笔撮合，更新持仓和资金
5. 未成交部分保留为 open/partial 状态

#### Scenario: Limit buy matches opposing sells

- **WHEN** 买单价格 ≥ 卖单价格时
- **THEN** 按卖单价格成交，买方支付 `tradeAmount + commission`，卖方收入 `tradeAmount - commission - stampTax`

#### Scenario: Market buy sweeps all opposing orders

- **WHEN** 市价买单提交时
- **THEN** SHALL 扫描所有对手卖单，按价格 ASC 顺序撮合

#### Scenario: Insufficient cash cancels market order

- **WHEN** 市价买单剩余未成交部分无法冻结足够资金时
- **THEN** 未成交部分 SHALL 被标记为 `cancelled`

### Requirement: Fund Freezing Consistency

所有资金和持仓变更 MUST 在同一数据库事务中成对执行。

不变量：`PlayerState.FrozenCash` 恒等于该玩家所有 open/partial 买单的 `FrozenAmount` 之和。

| 操作 | FrozenCash | Order.FrozenAmount |
|------|------------|-------------------|
| 买单调入 | +estimated | = estimatedCost |
| 买入成交 | -cost | -= cost |
| 买单填满剩余 | -remainder | = 0 |
| 撤单 | -全部 | = 0 |

#### Scenario: Buy order freeze and unfreeze

- **WHEN** 买单提交时冻结 ¥1000
- **THEN** 成交 ¥600 后 SHALL 解冻剩余 ¥400

#### Scenario: Cancel unfreezes all

- **WHEN** 撤销一个 partially filled 的买单时
- **THEN** `FrozenAmount` SHALL 归零，对应现金 SHALL 解冻

### Requirement: Fee Calculation

交易手续费 SHALL 按以下规则计算：

| 费用 | 方向 | 费率 |
|------|------|------|
| 佣金 | 买入 | max(成交额 × 0.025%, ¥5) |
| 佣金 | 卖出 | max(成交额 × 0.025%, ¥5) |
| 印花税 | 卖出 | 成交额 × 0.1% |

金额单位：元（分到元四舍五入）。

#### Scenario: Minimum commission enforcement

- **WHEN** 成交额 × 0.025% < ¥5 时
- **THEN** 佣金 SHALL 为 ¥5

#### Scenario: Stamp tax only on sell

- **WHEN** 买入交易执行时
- **THEN** 不收取印花税

### Requirement: Broker Inventory Release

证券机构（BROKER 系统账号）SHALL 每 5 tick 扫描一次，将 IPO 增发的流通股逐步释放到市场。

释放规则：
1. 查询有库存的股票
2. 取最优买单
3. 价格门禁：`buyPrice ≥ max(bestBid, currentPrice) × 0.9`
4. 满足条件时按买价卖出

#### Scenario: Broker releases at market price

- **WHEN** 最优买单价格 ≥ 参考价的 90% 时
- **THEN** BROKER SHALL 按买价将库存卖给买单持有者

#### Scenario: Broker skips when price too low

- **WHEN** 最优买单价格 < 参考价的 90% 时
- **THEN** BROKER SHALL 跳过该股票，等待价格回升

### Requirement: AI Trader Cigarette Butt Valuation

AI 交易者 SHALL 使用统一的烟蒂估值模型计算预期股价：

```
liquidationValue = (Cash + CapCount × CapAssetValue) × 0.75 / TotalShares × Prosperity
earningValue = annualEPS × 行业PE × Prosperity
expectedPrice = max(liquidationValue, earningValue, 1) × random(0.85, 1.15)
```

#### Scenario: Profitable company valuation

- **WHEN** 公司连续盈利且 EPS > 0 时
- **THEN** `expectedPrice` SHALL 取 `earningValue`（通常高于清算价值）

#### Scenario: Loss-making company valuation

- **WHEN** 公司亏损（EPS ≤ 0）时
- **THEN** `expectedPrice` SHALL 取 `liquidationValue`（清算价值兜底）

### Requirement: AI Trader Sliding Probability

AI 交易者 SHALL 使用滑动概率决定买卖方向：

| ratio (当前价/预期价) | 买入概率 |
|:---:|:---:|
| ≤ 0.5 | 90% |
| 0.5 ~ 1.0 | 线性 90% → 50% |
| 1.0 ~ 2.0 | 线性 50% → 10% |
| ≥ 2.0 | 10% |

每个 tick 有 50% 概率跳过不做决策。

#### Scenario: Undervalued stock triggers buy

- **WHEN** ratio ≤ 0.5 时
- **THEN** 买入概率 SHALL 为 90%

#### Scenario: Overvalued stock triggers sell

- **WHEN** ratio ≥ 2.0 时
- **THEN** 买入概率 SHALL 为 10%（即卖出概率 90%）

### Requirement: AI Trader Lifecycle

AI 交易者 SHALL 遵循以下生命周期：
- 初始化：零持仓起步，随机初始资金 ¥5,000~¥500,000
- 交易：每 2-8 tick 执行一次决策
- 耗尽退出：Cash < ¥100 且持仓为零时退出
- 系统补充：每 100 tick 检查，耗尽者重新分配随机资金 + 参数

#### Scenario: Bot exhaustion and respawn

- **WHEN** AI 交易者现金 < ¥100 且无持仓时
- **THEN** 该交易者 SHALL 退出市场，系统在下一次 100 tick 检查时补充新交易者

### Requirement: Prosperity Random Walk

行业景气度 SHALL 使用随机游走 + 回归机制更新：

```
randomStep = (rand() × 2 - 1) × ProsperityMaxStep
regressionStep = -(prosperity - 1.0) / halfRange × ProsperityRegression
newProsperity = clamp(oldProsperity + randomStep + regressionStep, Min, Max)
```

每季度有 `CorrectionProb` 概率触发修正脉冲，覆盖正常步长。

景气度影响：营收乘数 = prosperity（繁荣 >1.0，衰退 <1.0）。

#### Scenario: Prosperity regression toward 1.0

- **WHEN** 景气度偏离 1.0 较远时
- **THEN** `regressionStep` SHALL 向 1.0 方向施加回归力

#### Scenario: Prosperity correction pulse

- **WHEN** 随机数 < CorrectionProb 时
- **THEN** SHALL 执行修正脉冲：`pulse = -deviation × CorrectionPulse`

### Requirement: WebSocket Price Update Broadcast

系统 SHALL 每 2 秒通过 WebSocket 广播全量行情更新：

消息类型 `price_update` 包含：
- 所有股票的 `currentPrice`、`change`、`changePercent`
- 每支股票的三周期 K 线 OHLC（15t/60t/150t）

#### Scenario: Price update includes candles

- **WHEN** WebSocket 广播 price_update 时
- **THEN** 每支股票 SHALL 包含 `candles` 字段，含 `15t`、`60t`、`150t` 三个周期的 OHLC

### Requirement: WebSocket Portfolio Update on Trade

成交时 SHALL 向买卖双方单播 `portfolio_update` 消息：

内容包含：`cash`、`frozenCash`、`holdings[]`（含 symbol、qty、costPrice、currentPrice、marketValue、pnl）。

#### Scenario: Both buyer and seller receive update

- **WHEN** 一笔交易撮合完成时
- **THEN** 买方和卖方 SHALL 各自收到一条 `portfolio_update` 消息

### Requirement: IPO Process

公司 IPO SHALL 满足以下条件：
- 运营季度 ≥ 12 季
- 连续盈利 ≥ 4 季
- 现金 ≥ ¥1,000,000
- 近 4 季营收合计 ≥ ¥5,000,000

发行价公式：`max(1, NAV + EPS × 行业PE × 景气度) × 0.95`，四舍五入到分。

#### Scenario: IPO creates stock and broker inventory

- **WHEN** 公司成功发起 IPO 时
- **THEN** SHALL 创建 Stock 记录 + BrokerInventory（TotalQty = 增发股数）

### Requirement: Bankruptcy Liquidation

公司破产清算 SHALL 在连续两季度现金 < 0 后触发：

清算流程：
1. 撤销全部挂单并解冻
2. 全员解散
3. 库存+产能 50% 折价出售
4. 剩余现金按持股分配
5. 退市销股，删除建造队列，清 BrokerInventory

#### Scenario: Liquidation distributes cash by shareholding

- **WHEN** 公司破产清算时
- **THEN** 剩余现金 SHALL 按持股比例分配给股东（IPO 后按 holdings 表，IPO 前按 CEOShares）

### Requirement: Bankruptcy Trigger

破产清算按钮 SHALL 在连续两季度 CompanyQuarterly 结算后 cash < 0 时出现。

#### Scenario: Bankruptcy button appears after two negative quarters

- **WHEN** 公司连续两个季度结算后 CompanyQuarterly.Cash < 0 时
- **THEN** 前端 SHALL 显示「破产清算」按钮
