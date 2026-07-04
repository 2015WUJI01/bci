## Why

大猫投资（Big Cat Investment）项目经历了从 Python+FastAPI+SQLite+vanillaJS 到 Go+chi+GORM+MySQL+React+TypeScript 的完整重写。新代码中分散着复杂的业务逻辑（公司运营、交易撮合、AI 交易者、行业景气度、WebSocket 推送），但缺少一份**统一的、可机读的实现规范**来描述这些核心系统的行为。

当前问题：
- `docs/` 下的设计文档是**意图文档**（描述"要做什么"），不是**实现规范**（描述"实际做了什么"）
- 新贡献者需要阅读 `jjs-server/internal/engine/` 下 10+ 个文件才能理解一个完整流程
- 代码变更时无法快速判断影响范围（一个公式改动会影响哪些下游系统？）
- 没有可测试的场景定义，无法验证行为是否符合预期

现在创建这份归档，是因为 P4（AI 交易者）已完成、P5（业务系统）即将启动，是固化核心系统行为的最佳时机。

## What Changes

- **新建** `openspec/specs/game-core-systems/spec.md`：完整描述游戏核心系统的行为规范，包含：
  - 公司运营系统（季度结算、成本模型、建造队列、破产清算）
  - 交易引擎（订单簿撮合、资金冻结、手续费、证券机构库存释放）
  - AI 交易者系统（烟蒂估值、滑动概率、生命周期）
  - 行业景气度系统（随机游走 + 回归）
  - WebSocket 实时推送（消息类型、触发时机）
- **归档** 本次分析的完整内容到 openspec change 历史中

## Capabilities

### New Capabilities

- `game-core-systems`: 游戏核心系统行为规范——覆盖公司运营、交易撮合、AI 交易者、行业景气度、WebSocket 推送的完整行为定义和可测试场景

### Modified Capabilities

（无现有 spec 被修改，openspec/specs/ 当前为空）

## Impact

- **代码**：`jjs-server/internal/engine/`、`jjs-server/internal/bots/`、`jjs-server/internal/ws/` 中的核心逻辑被文档化
- **文档**：与 `docs/REFACTORING_ROADMAP.md`、`docs/ARCHITECTURE.md`、`docs/GAME_DESIGN.md` 形成互补——设计文档描述意图，spec 描述实际行为
- **测试**：spec 中的场景可直接转化为 P8 阶段的集成测试用例
- **无破坏性变更**：纯文档新增，不修改任何代码
