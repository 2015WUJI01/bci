const gameState = {
  playerId: null,
  nickname: null,
  stocks: [],       // single stock DM
  cash: 100000,
  holdings: [],     // [{symbol, name, quantity, avg_cost, current_price, market_value, pnl}]
  totalAssets: 100000,
  totalPnl: 0,
  pnlPercent: 0,
  leaderboard: [],
  orderBook: {},
  klinePeriod: 'chart',
  candleData: { '1t': {}, '4t': {}, '20t': {} },
  // NEW FIELDS:
  dailyStats: {},   // {open, high, low, prev_close, volume}
  timeshare: [],    // [{time, price}]
  tape: [],         // [{time, price, quantity, type}]
  newsList: [],     // [{time, title, content, impact}]

  // 扩展指标
  turnoverRate: 0,
  amplitude: 0,
  buyVolume: 0,
  sellVolume: 0,
  pe: 0,
  pb: 0,
  weiBi: 0,
  weiCha: 0,
  bidVolume: 0,
  askVolume: 0,
  trades: [],       // 历史成交
  equityCurve: [],  // 收益率曲线
  f10Data: null,    // F10公司资料
  frozenCash: 0,    // 冻结资金
  marginDebt: 0,    // 融资负债
  dayStartAssets: null,  // 当日初始总资产（计算当日盈亏用）
  financialReports: [],  // 财务报告
};
