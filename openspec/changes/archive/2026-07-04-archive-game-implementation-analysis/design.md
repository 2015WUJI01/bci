## Context

大猫投资项目的文档体系分为三层：

| 层级 | 文档 | 用途 |
|------|------|------|
| 意图层 | `docs/GAME_DESIGN.md`, `docs/COMPANY_V2_DESIGN.md` | 描述"要做什么" |
| 架构层 | `docs/ARCHITECTURE.md`, `docs/REFACTORING_ROADMAP.md` | 描述"怎么做"和"进度" |
| **实现层** | **本 spec（openspec）** | 描述"实际做了什么"+ 可测试场景 |

本次归档覆盖的核心系统位于 `jjs-server/internal/engine/` 和 `jjs-server/internal/bots/`。

## Goals / Non-Goals

**Goals:**
- 将游戏核心系统的行为规范化为可测试的场景
- 为 P8 测试阶段提供直接可用的测试用例来源
- 新贡献者可通过 spec 快速理解系统行为，无需逐文件阅读代码
- 代码变更时可通过 spec 快速判断影响范围

**Non-Goals:**
- 不修改任何现有代码（纯文档）
- 不覆盖前端实现（前端在 P7 阶段独立处理）
- 不覆盖 API 路由和请求格式（属于接口规范，不是行为规范）
- 不覆盖配置常量（`config.go` 中的值可能随调参变化）

## Decisions

### Decision 1: 使用 openspec 格式而非 Markdown 文档

**选择**：使用 openspec 的 spec-driven schema 创建结构化规范。

**替代方案**：
- 纯 Markdown 文档（如 `docs/GAME_IMPLEMENTATION.md`）
- 直接在代码中写注释

**理由**：
- openspec 强制要求每个 requirement 配备 scenario，保证可测试性
- 与项目已有的 openspec 基础设施一致（已有 archive change）
- 结构化格式便于工具解析和 diff

### Decision 2: 合并为单一 capability（game-core-systems）

**选择**：将所有核心系统合并为一个 capability `game-core-systems`。

**替代方案**：
- 拆分为多个 capability（`company-operations`、`trading-engine`、`ai-traders` 等）

**理由**：
- 这些系统高度耦合（公司结算影响股价 → 影响 AI 决策 → 影响交易撮合）
- 拆分后需要大量交叉引用，反而增加维护成本
- 项目规模适中，单一 spec 文件不会超过 300 行

### Decision 3: 以代码实现为真值，而非设计文档

**选择**：spec 描述的是代码的**实际行为**，可能与设计文档有差异。

**替代方案**：以设计文档为真值，描述"应有行为"。

**理由**：
- 设计文档可能过时（代码已迭代但文档未更新）
- spec 的价值在于可测试——测试必须基于实际代码行为
- 如有差异，可在 spec 中标注"与设计文档不一致"

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| spec 随代码演进过时 | P8 测试阶段会验证 spec 场景，发现不一致时同步更新 |
| 单一 capability 文件过大 | 当前约 250 行，可接受；如超过 500 行再拆分 |
| 与设计文档重复 | 设计文档侧重"为什么"，spec 侧重"是什么"，互补而非替代 |

## 关键系统数据流

```
公司季度结算
  ├── 产能计算 (manufacturing.go / mining.go)
  ├── 成本拆分 (Labor + BaseMaint + OpCost + Warehouse)
  ├── 利润计算 → CompanyQuarterly.Profit
  └── 现金更新 → Company.Cash

股价公式
  ├── NAV = (Cash + CapCount × CapAssetValue) / TotalShares
  ├── EPS = avg(近4季Profit) / TotalShares
  └── Price = max(1, NAV + EPS × PE × Prosperity)

AI 交易者
  ├── 烟蒂估值 = max(清算价值, 盈利估值) × 个体扰动
  ├── 滑动概率 = f(当前价/预期价)
  └── 限价下单 → 订单簿撮合

交易撮合
  ├── 价格优先 → 时间优先
  ├── 冻结/解冻资金（同一事务）
  └── 证券机构库存释放（每5tick）
```

## 与现有文档的关系

| 文档 | 定位 | 与本 spec 的关系 |
|------|------|------------------|
| `docs/GAME_DESIGN.md` | 游戏策划案 | 本 spec 是其"实现验证" |
| `docs/ARCHITECTURE.md` | 架构文档 | 本 spec 是其"行为补充" |
| `docs/AI_TRADER_DESIGN.md` | AI 设计 v2 | 本 spec 描述其实际行为 |
| `docs/REFACTORING_ROADMAP.md` | 重写路线图 | 本 spec 是 P8 测试的前置输入 |
