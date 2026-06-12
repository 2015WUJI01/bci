import paramiko, json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file('C:/Users/Admin/Downloads/LIU.pem')
ssh.connect('120.79.28.144', 22, 'root', pkey=key, timeout=10)

# Check market state
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:8000/api/market')
data = json.loads(stdout.read().decode())
print(f"Price: {data['price']}, Volume: {data['volume']}")
print(f"Shares: {data.get('shares_outstanding')}")

# Check pending orders via a Python script on the server
script = """
import sys
sys.path.insert(0, '/root/stock-game')
from backend.game_engine import get_global_state
state = get_global_state()
# Check pending orders count
pending = [o for o in state.pending_orders.values() if o['status'] == 'pending']
print(f'Pending orders: {len(pending)}')
# Show some orders
for o in list(pending)[:5]:
    print(f'  {o[\"type\"]} {o[\"symbol\"]} @ {o[\"price\"]} qty={o[\"quantity\"]} filled={o[\"filled\"]} player={o[\"player_id\"][:10]}')
# Check if AI bots are running
print(f'AI buy cash: {state.players.get(\"ai_buy\", {}).get(\"cash\", 0)}')
print(f'AI sell cash: {state.players.get(\"ai_sell\", {}).get(\"cash\", 0)}')
ai_sell_holding = state.holdings.get('ai_sell', {}).get('DM', {})
print(f'AI sell DM qty: {ai_sell_holding.get(\"qty\", 0)}')
print(f'DM price: {state.stocks.get(\"DM\", {}).get(\"price\", 0)}')
"""
stdin, stdout, stderr = ssh.exec_command(f'cd /root/stock-game && source venv/bin/activate && python3 -c {json.dumps(script)}')
print(stdout.read().decode().strip())
err = stderr.read().decode().strip()
if err: print(f'ERR: {err[:500]}')

ssh.close()
