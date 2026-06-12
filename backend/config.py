import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./stock_game.db")

STARTING_CASH = 10_000.0
PRICE_TICK_INTERVAL = 1.5  # seconds
LEADERBOARD_INTERVAL = 7.5  # seconds
DB_FLUSH_INTERVAL = 30  # seconds
PRICE_MIN = 0.0001  # 无上限，仅防止归零
PRICE_MAX = 1_000_000.0
SHARES_OUTSTANDING = 500_000_000
MAX_POSITION_PER_PLAYER = int(SHARES_OUTSTANDING * 0.05)  # 单人最大持仓 = 5% 流通股 = 2500万股
MAX_ORDER_QTY = int(SHARES_OUTSTANDING * 0.01)  # 单笔最大委托 = 1% 流通股 = 500万股
INITIAL_PRICE = 100.0

# Transaction fees (like real Chinese stock market)
STAMP_TAX_RATE = 0.001  # 印花税 0.1% (sell only)
COMMISSION_RATE = 0.00025  # 佣金 0.025% (both buy and sell)
MIN_COMMISSION = 5.0  # 最低佣金 5元

SHORT_SELL_FEE_RATE = 0.000003  # 融券费率 0.0003%/tick group（按融券持仓市值收取）
MARGIN_INTEREST_RATE = 0.000003  # 融资利率 0.0003%/tick group（约 0.864%/天，合理范围）
MARGIN_MIN_ASSETS = 1_000_000  # 融资融券最低资产门槛

STOCKS_TEMPLATE = []
