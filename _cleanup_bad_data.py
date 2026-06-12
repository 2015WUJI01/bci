"""清理被刷数据的玩家和AI异常状态"""
import sqlite3
import sys

conn = sqlite3.connect('stock_game.db')
cur = conn.cursor()

# 1. 清理刷数据的玩家 63fbf8e78e98
bad_id = '63fbf8e78e98'
cur.execute("DELETE FROM holdings WHERE player_id = ?", (bad_id,))
cur.execute("DELETE FROM player_state WHERE player_id = ?", (bad_id,))
cur.execute("DELETE FROM transactions WHERE player_id = ?", (bad_id,))
print(f"Deleted player {bad_id} (89万亿现金 + 100万亿股)")

# 2. 重置市场状态（价格和成交量）
cur.execute("DELETE FROM player_state WHERE player_id = '_market_DM'")
print("Reset market state (_market_DM)")

# 3. 清除AI交易记录（太多，保留但可以清理）
cur.execute("DELETE FROM transactions WHERE player_id LIKE 'ai_%'")
print("Cleared AI transaction records")

conn.commit()
conn.close()
print("Done!")
