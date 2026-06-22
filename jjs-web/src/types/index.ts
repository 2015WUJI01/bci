export interface StockInfo {
  symbol: string
  name: string
  price: number          // 股价 (分, 显示时 ÷100)
  change: number
  changePercent: number
  open: number           // 分
  high: number           // 分
  low: number            // 分
  volume: number
  pe: number
  marketCap: number
  sharesOutstanding: number
  eps: number
  tick: number
}

export interface OrderBookLevel {
  price: number  // 分
  qty: number
}

export interface OrderBook {
  symbol: string
  bids: OrderBookLevel[]
  asks: OrderBookLevel[]
  spread: number
}

export interface TradeRecord {
  time: string
  symbol: string
  price: number     // 分
  qty: number
  direction: 'buy' | 'sell'
}

export interface KlineBar {
  time: string
  open: number      // 分
  high: number      // 分
  low: number       // 分
  close: number     // 分
  volume: number
}

export interface Holding {
  symbol: string
  name: string
  qty: number
  costPrice: number     // 持仓均价 (円, 整数)
  currentPrice: number  // 当前价 (分, 显示时 ÷100)
  marketValue: number
  pnl: number
  pnlPercent: number
}

export interface PortfolioState {
  cash: number
  frozenCash: number
  availableCash: number
  holdings: Holding[]
  totalAssets: number
  totalPnl: number
  totalPnlPercent: number
}

export interface PlayerInfo {
  id: string
  email: string
  nickname: string
  type: 'admin' | 'player' | 'npc'
}

export interface PlayerBasicInfo {
  player_id: string
  nickname: string
  email: string
  cash: number
  frozen_cash: number
  margin_debt: number
  global_quarter: number
}

export interface NewsItem {
  id: string
  time: string
  title: string
  content: string
  sentiment: 'bullish' | 'bearish' | 'neutral'
  symbol?: string
}

export interface LeaderboardEntry {
  rank: number
  nickname: string
  totalAssets: number
  pnl: number
  isMe: boolean
}

export interface PendingOrder {
  id: string
  symbol: string
  type: 'buy' | 'sell'
  orderType: 'market' | 'limit'
  price: number | null  // 分 (限价单)
  qty: number
  filledQty: number
  status: 'pending' | 'partial' | 'filled' | 'cancelled'
  createdAt: string
}

export interface CompanyState {
  id: number
  symbol: string
  name: string
  industry: Industry
  ceo_id: string
  created_quarter: number
  cash: number
  employees: number
  status: string
  total_shares: number
  ceo_shares: number
  own_ratio: number
  cap_count: number
  inventory: number
  capacity_ceiling: number
  actual_output: number
  revenue: number
  profit: number
  last_quarterly: QuarterlyReport | null
  pending_builds: number
}

export type Industry = 'tech' | 'finance' | 'manufacturing' | 'mining' | 'consumer' | 'healthcare'

export interface IndustryInfo {
  id: Industry
  name: string
  icon: string
  description: string
  basePE: number
  revenuePerEmployee: number
  startingEmployees: number
  startingCash: number
  sharesOutstanding: number
}

export interface QuarterlyResponse {
  items: QuarterlyReport[]
  hasMore: boolean
}

export interface QuarterlyReport {
  ID: number
  CompanyID: number
  quarter: number
  revenue: number
  profit: number
  beginning_cash: number
  cash: number
  labor_cost: number
  base_maintenance: number
  operational_cost: number
  warehouse_cost: number
  total_cost: number
  sales_qty: number
  prod_qty: number
  employees: number
  total_shares: number
  ceo_shares: number
  cap_count: number
  inventory: number
  CreatedAt: string
}

export interface RandomEvent {
  id: string
  title: string
  description: string
  impact: string
  type: 'positive' | 'negative' | 'neutral'
}

export interface MarginAccount {
  totalAssets: number
  totalDebt: number
  marginRatio: number
  status: 'safe' | 'normal' | 'warning' | 'danger'
  shortPositions: ShortPosition[]
  borrowLimit: number
  usedBorrow: number
}

export interface ShortPosition {
  symbol: string
  qty: number
  costPrice: number     // 持仓均价 (円, 整数)
  currentPrice: number  // 当前价 (分, 显示时 ÷100)
  marketValue: number
  pnl: number
  pnlPercent: number
}

export interface WsMessage {
  type: WsMessageType
  data: unknown
}

export type WsMessageType =
  | 'join'
  | 'price_update'
  | 'portfolio_update'
  | 'orderbook'
  | 'trade_tape'
  | 'news'
  | 'quarterly_report'
  | 'company_update'
  | 'leaderboard_update'
  | 'event_notification'
  | 'order_update'
  | 'error'

export type KlinePeriod = '1m' | '5m' | '15m' | '30m' | '60m' | '1d'
