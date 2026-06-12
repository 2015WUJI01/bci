"""
后台交易工具 —— 通过 SSH 命令行操作管理员账号进行买卖。

用法:
  # 拉升：买入10万股
  python3 backend/admin_trade.py buy 100000

  # 砸盘：卖出5万股
  python3 backend/admin_trade.py sell 50000

  # 拉升到目标价 ¥6.0
  python3 backend/admin_trade.py target-buy 6.0

  # 查询当前状态
  python3 backend/admin_trade.py status

这个脚本直接调用 game_engine 的函数，不需要 WebSocket 连接。
"""
import asyncio
import sys
import os

# 确保能找到 backend 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.game_engine import (
    get_global_state, execute_trade, place_limit_order,
    broadcast_leaderboard,
)
from backend.database import async_session
from backend.models import User
from sqlalchemy import select


ADMIN_EMAIL = "admin@stock.game"
ADMIN_CASH_TARGET = 500_000_000


async def get_admin_id() -> str | None:
    """从数据库获取后台管理员玩家ID。"""
    async with async_session() as session:
        r = await session.execute(
            select(User.id).where(User.username == ADMIN_EMAIL)
        )
        return r.scalar_one_or_none()


async def ensure_admin_state(pid: str):
    """确保管理员已在游戏内存中，且现金足够。"""
    state = get_global_state()
    if pid not in state.players:
        state.players[pid] = {
            "nickname": "操盘手",
            "cash": ADMIN_CASH_TARGET,
            "frozen_cash": 0,
            "margin_debt": 0.0,
            "is_admin": True,
        }
    elif state.players[pid]["cash"] < ADMIN_CASH_TARGET:
        state.players[pid]["cash"] = ADMIN_CASH_TARGET
    if not state.players[pid].get("is_admin"):
        state.players[pid]["is_admin"] = True


async def cmd_status():
    """查询当前股价 + 管理员资金。"""
    state = get_global_state()
    stock = state.stocks.get("DM")
    price = stock["price"] if stock else 0
    admin_id = await get_admin_id()
    if admin_id:
        p = state.players.get(admin_id)
        cash = p["cash"] if p else 0
        frozen = p.get("frozen_cash", 0) if p else 0
        available = cash - frozen
    else:
        cash = available = 0
    print(f"当前股价: ¥{price:.4f}")
    print(f"管理员现金: ¥{cash:.2f} (可用: ¥{available:.2f})")
    print(f"管理员ID: {admin_id}")


async def cmd_buy(qty: int):
    """市价买入指定股数。"""
    pid = await get_admin_id()
    if not pid:
        print("错误: 找不到管理员账号")
        return
    await ensure_admin_state(pid)
    state = get_global_state()
    stock = state.stocks.get("DM")
    if not stock:
        print("错误: 没有行情数据")
        return
    price = stock["price"]
    print(f"市价买入 {qty} 股 @ ¥{price:.4f}，预计花费 ¥{price * qty:.2f}")
    await execute_trade(pid, {
        "stock_symbol": "DM",
        "quantity": qty,
        "trade_type": "buy",
    })
    await broadcast_leaderboard()
    # 刷新状态
    state = get_global_state()
    p = state.players.get(pid)
    if p:
        print(f"执行后现金: ¥{p['cash']:.2f}")
    print("委托已发送")


async def cmd_sell(qty: int):
    """市价卖出指定股数。"""
    pid = await get_admin_id()
    if not pid:
        print("错误: 找不到管理员账号")
        return
    await ensure_admin_state(pid)
    print(f"市价卖出 {qty} 股")
    await execute_trade(pid, {
        "stock_symbol": "DM",
        "quantity": qty,
        "trade_type": "sell",
    })
    await broadcast_leaderboard()
    state = get_global_state()
    p = state.players.get(pid)
    if p:
        print(f"执行后现金: ¥{p['cash']:.2f}")
    print("委托已发送")


async def cmd_target_buy(target_price: float):
    """分批限价买入，拉升到目标价。"""
    pid = await get_admin_id()
    if not pid:
        print("错误: 找不到管理员账号")
        return
    await ensure_admin_state(pid)
    state = get_global_state()
    stock = state.stocks.get("DM")
    if not stock:
        print("错误: 没有行情数据")
        return
    cur_price = stock["price"]
    if target_price <= cur_price:
        print(f"目标价 {target_price} 必须高于当前价 {cur_price:.4f}")
        return
    p = state.players.get(pid)
    cash = p["cash"] - p.get("frozen_cash", 0)
    steps = min(5, int((target_price - cur_price) / (cur_price * 0.01)) + 1)
    cash_per_step = min(cash * 0.2, 20_000_000)
    print(f"目标价 ¥{target_price}, 当前 ¥{cur_price:.4f}, {steps} 档拉升")
    for i in range(steps):
        step_price = round(cur_price * (1 + 0.01 * (i + 1)), 4)
        step_qty = int(cash_per_step / step_price / 1000) * 1000
        if step_qty < 1000:
            continue
        print(f"  档{i+1}: 限价买入 {step_qty} 股 @ ¥{step_price}")
        await place_limit_order(pid, {
            "stock_symbol": "DM",
            "quantity": step_qty,
            "order_type": "buy",
            "price": step_price,
        })
    await broadcast_leaderboard()
    print("拉升委托已全部提交")


async def cmd_target_sell(target_price: float):
    """分批限价卖出，把价格砸到目标价。"""
    pid = await get_admin_id()
    if not pid:
        print("错误: 找不到管理员账号")
        return
    await ensure_admin_state(pid)
    state = get_global_state()
    stock = state.stocks.get("DM")
    if not stock:
        print("错误: 没有行情数据")
        return
    cur_price = stock["price"]
    if target_price >= cur_price:
        print(f"目标价 {target_price} 必须低于当前价 {cur_price:.4f}")
        return
    # 检查持仓
    holding = state.holdings.get(pid, {}).get("DM", {"qty": 0})
    if holding["qty"] <= 0:
        print("没有持仓可卖")
        return
    steps = min(5, int((cur_price - target_price) / (cur_price * 0.01)) + 1)
    qty_per_step = int(holding["qty"] / steps / 1000) * 1000
    print(f"目标价 ¥{target_price}, 当前 ¥{cur_price:.4f}, {steps} 档砸盘")
    for i in range(steps):
        step_price = round(cur_price * (1 - 0.01 * (i + 1)), 4)
        if qty_per_step >= 1000:
            print(f"  档{i+1}: 限价卖出 {qty_per_step} 股 @ ¥{step_price}")
            await place_limit_order(pid, {
                "stock_symbol": "DM",
                "quantity": qty_per_step,
                "order_type": "sell",
                "price": step_price,
            })
    await broadcast_leaderboard()
    print("砸盘委托已全部提交")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "status":
        asyncio.run(cmd_status())
    elif cmd == "buy" and len(sys.argv) >= 3:
        asyncio.run(cmd_buy(int(sys.argv[2])))
    elif cmd == "sell" and len(sys.argv) >= 3:
        asyncio.run(cmd_sell(int(sys.argv[2])))
    elif cmd == "target-buy" and len(sys.argv) >= 3:
        asyncio.run(cmd_target_buy(float(sys.argv[2])))
    elif cmd == "target-sell" and len(sys.argv) >= 3:
        asyncio.run(cmd_target_sell(float(sys.argv[2])))
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
