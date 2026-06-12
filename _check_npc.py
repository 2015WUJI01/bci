"""快速检查NPC运行状态"""
import sqlite3
conn = sqlite3.connect('stock_game.db')
cur = conn.cursor()

ai_count = cur.execute("SELECT COUNT(*) FROM transactions WHERE player_id LIKE 'ai_%'").fetchone()[0]
npc_count = cur.execute("SELECT COUNT(*) FROM transactions WHERE player_id LIKE 'npc_%'").fetchone()[0]
player_count = cur.execute("SELECT COUNT(*) FROM transactions WHERE player_id NOT LIKE 'ai_%' AND player_id NOT LIKE 'npc_%' AND player_id NOT LIKE '_market_%'").fetchone()[0]

print(f"AI交易: {ai_count}")
print(f"NPC交易: {npc_count}")
print(f"玩家交易: {player_count}")
print(f"总计: {ai_count + npc_count + player_count}")

print("\n=== 最近NPC交易 ===")
for row in cur.execute("SELECT player_id, trade_type, quantity, price FROM transactions WHERE player_id LIKE 'npc_%' ORDER BY id DESC LIMIT 10"):
    print(f"  {row[0]} {row[1]} {row[2]}股 @ {row[3]:.4f}")

print("\n=== NPC持仓统计 ===")
for row in cur.execute("SELECT player_id, qty, avg_cost FROM holdings WHERE player_id LIKE 'npc_%' AND qty > 0 ORDER BY qty DESC LIMIT 10"):
    print(f"  {row[0]}: {row[1]}股 @ {row[2]:.2f}")

npc_with_shares = cur.execute("SELECT COUNT(*) FROM holdings WHERE player_id LIKE 'npc_%' AND qty > 0").fetchone()[0]
npc_total = cur.execute("SELECT COUNT(DISTINCT player_id) FROM (SELECT player_id FROM holdings WHERE player_id LIKE 'npc_%' UNION SELECT player_id FROM player_state WHERE player_id LIKE 'npc_%')").fetchone()[0]
print(f"\n有持仓的NPC: {npc_with_shares} / 总计NPC: {npc_total}")

conn.close()
