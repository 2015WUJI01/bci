import sqlite3
conn = sqlite3.connect('stock_game.db')
cur = conn.cursor()
print('=== 市场价格 ===')
for row in cur.execute("SELECT player_id, cash, frozen_cash FROM player_state WHERE player_id LIKE '_market_%'"):
    print(f'  {row[0]}: price={row[1]}, volume={row[2]}')
print('=== 真实玩家 ===')
for row in cur.execute("SELECT player_id, cash, frozen_cash FROM player_state WHERE player_id NOT LIKE '_market_%' AND player_id NOT LIKE 'ai_%'"):
    print(f'  {row[0]}: cash={row[1]}, frozen={row[2]}')
print('=== 持仓 ===')
for row in cur.execute('SELECT player_id, symbol, qty, avg_cost, frozen_qty FROM holdings'):
    print(f'  {row[0]}: {row[1]} {row[2]}股 @ {row[3]} 冻结{row[4]}')
print('=== 最近20笔交易 ===')
for row in cur.execute('SELECT player_id, trade_type, symbol, quantity, price FROM transactions ORDER BY id DESC LIMIT 20'):
    print(f'  {row[0]} {row[1]} {row[2]} {row[3]}股 @ {row[4]}')
print('=== 交易统计 ===')
ai_count = cur.execute("SELECT COUNT(*) FROM transactions WHERE player_id LIKE 'ai_%'").fetchone()[0]
real_count = cur.execute("SELECT COUNT(*) FROM transactions WHERE player_id NOT LIKE 'ai_%' AND player_id NOT LIKE '_market_%'").fetchone()[0]
print(f'  AI交易: {ai_count}')
print(f'  玩家交易: {real_count}')
conn.close()
