"""Check order book state on server - no f-string dict issues."""
import paramiko, json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file('C:/Users/Admin/Downloads/LIU.pem')
ssh.connect('120.79.28.144', 22, 'root', pkey=key, timeout=10)

# Write script to file on server, then run it
script = """
import sys
sys.path.insert(0, '/root/stock-game')
from backend.game_engine import get_global_state
s = get_global_state()
pending = [o for o in s.pending_orders.values() if o['status'] == 'pending']
print('Pending orders count:', len(pending))
for o in pending[:8]:
    print(' ', o['type'], o['symbol'], '@', o['price'], 'qty', o['quantity'], 'filled', o['filled'], 'pid', o['player_id'][:10])
price = s.stocks.get('DM', {}).get('price', 0)
print('DM price:', price)
# Check inst and hot players
for p in ['inst_1', 'inst_2', 'inst_3', 'hot_1', 'hot_2']:
    pl = s.players.get(p, {})
    h = s.holdings.get(p, {}).get('DM', {})
    if pl:
        print(f'{p}: cash={pl.get(\"cash\",0):.0f} holdings={h.get(\"qty\",0)} frozen={h.get(\"frozen_qty\",0)}')
"""

# Upload script
sftp = ssh.open_sftp()
with sftp.open('/tmp/check_orders.py', 'w') as f:
    f.write(script)
sftp.close()

# Run it
stdin, stdout, stderr = ssh.exec_command(
    'cd /root/stock-game && source venv/bin/activate && python3 /tmp/check_orders.py'
)
print(stdout.read().decode().strip())
err = stderr.read().decode().strip()
if err:
    print('ERR:', err[:300])

ssh.close()
