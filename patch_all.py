"""一次性修补 game_engine.py — 所有 5 个功能 + 待处理修复。
使用行级操作避免缩进不匹配问题。"""
import re

with open('backend/game_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def replace_text(old_text, new_text):
    """Replace exact text in the lines array. Returns True if found."""
    global lines
    content = ''.join(lines)
    if old_text not in content:
        return False
    content = content.replace(old_text, new_text, 1)
    lines = content.splitlines(keepends=True)
    return True

# ============================================================
# 1. __init__ — 添加 retail_data 和 zhuang_data
# ============================================================
content = ''.join(lines)
old = '        self.quant_data: dict[str, dict] = {}'
new = '        self.quant_data: dict[str, dict] = {}\n        self.retail_data: dict[str, dict] = {}\n        self.zhuang_data: dict = {}'
assert old in content, "Patch 1"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# 2. init_global_market — 添加散户+庄家初始化
# ============================================================
content = ''.join(lines)
old = """    # Restore saved state from DB
    await load_market_state()
    await load_all_player_states()"""
new = """    # Initialize 100 Retail Investors (散户)
    retail_strategies = ["retail_fomo", "retail_panic", "retail_random"]
    for i in range(100):
        pid = f"retail_{i:03d}"
        strategy = retail_strategies[i % 3]
        cash = round(random.uniform(2000, 10000), 2)
        init_shares = random.randint(0, 500)
        state.players[pid] = {"nickname": f"散户{i+1}", "cash": cash, "frozen_cash": 0, "margin_debt": 0.0}
        state.holdings.setdefault(pid, {})
        state.holdings[pid]["DM"] = {"qty": init_shares, "avg_cost": 5.0, "frozen_qty": 0, "short_qty": 0, "short_avg_cost": 0.0}
        state.retail_data[pid] = {
            "strategy": strategy,
            "cooldown": random.randint(50, 200),
            "last_tick": random.randint(0, 50),
            "position_limit": int(MAX_POSITION_PER_PLAYER * 0.02),
            "risk": random.uniform(0.3, 0.8),
            "last_decision": "hold",
        }

    # Initialize 庄家 (Market Maker)
    zj_id = "zhuangjia"
    state.players[zj_id] = {"nickname": "庄家", "cash": 500_000_000, "frozen_cash": 0, "margin_debt": 0.0}
    state.holdings.setdefault(zj_id, {})
    init_zj_shares = int(SHARES_OUTSTANDING * 0.10)
    state.holdings[zj_id]["DM"] = {"qty": init_zj_shares, "avg_cost": 5.0, "frozen_qty": 0, "short_qty": 0, "short_avg_cost": 0.0}
    state.zhuang_data = {
        "phase": "accumulate",
        "phase_ticks": 0,
        "target_price": 0,
        "position_limit": int(SHARES_OUTSTANDING * 0.30),
    }

    # Restore saved state from DB
    await load_market_state()
    await load_all_player_states()"""
assert old in content, "Patch 2"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# 3. 启动散户+庄家循环
# ============================================================
content = ''.join(lines)
old = """    asyncio.create_task(npc_trading_loop())
    asyncio.create_task(quant_trading_loop())"""
new = """    asyncio.create_task(npc_trading_loop())
    asyncio.create_task(quant_trading_loop())
    asyncio.create_task(retail_trading_loop())
    asyncio.create_task(zhuangjia_trading_loop())"""
assert old in content, "Patch 3"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# 4. _compute_signal — 添加散户策略
# ============================================================
content = ''.join(lines)
old = """    elif strategy == "news":
        # 检查最近两条新闻
        if len(news_feed) >= 2:
            last_news = news_feed[0]
            impact = last_news.get("impact", "")
            if impact == "利好":
                return 0.9  # 积极追买
            elif impact == "利空":
                return -0.9 if holding["qty"] > 0 else 0  # 清仓
        # 无新闻时小额定投式买入
        if holding["qty"] == 0 and player["cash"] > 10000:
            return 0.2
        return 0

    return 0"""
new = """    elif strategy == "news":
        # 检查最近两条新闻
        if len(news_feed) >= 2:
            last_news = news_feed[0]
            impact = last_news.get("impact", "")
            if impact == "利好":
                return 0.9  # 积极追买
            elif impact == "利空":
                return -0.9 if holding["qty"] > 0 else 0  # 清仓
        # 无新闻时小额定投式买入
        if holding["qty"] == 0 and player["cash"] > 10000:
            return 0.2
        return 0

    elif strategy == "retail_fomo":
        # 散户追涨杀跌：看最近3个tick的价格变化
        if len(history) < 4:
            return 0
        changes = [(history[i] - history[i-1]) / history[i-1] for i in range(-3, 0)]
        cons_up = all(c > 0 for c in changes)
        cons_down = all(c < 0 for c in changes)
        if cons_up:
            return 0.6
        if cons_down:
            return -0.7
        return random.uniform(-0.1, 0.1)

    elif strategy == "retail_panic":
        if len(history) < 10:
            return 0
        change_10 = (price - history[-10]) / history[-10]
        if change_10 < -0.05:
            return -0.9
        if change_10 > 0.10:
            return 0.8
        return random.uniform(-0.2, 0.2)

    elif strategy == "retail_random":
        r = random.random()
        if r < 0.20:
            return random.uniform(0.3, 0.6)
        elif r < 0.40:
            if holding["qty"] > 0:
                return random.uniform(-0.5, -0.2)
            return 0
        return 0

    return 0"""
assert old in content, "Patch 4"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# 5. 在 npc_trading_loop 后添加 _retail_make_decision + retail_trading_loop
# ============================================================
content = ''.join(lines)
old = """# ---------------------------------------------------------------------------
# Quant Fund trading (量化基金) — 大额交易制造波动
# ---------------------------------------------------------------------------"""
new = """async def _retail_make_decision(pid: str, rd: dict, state):
    stock = state.stocks.get("DM")
    if not stock:
        return
    price = stock["price"]
    player = state.players.get(pid)
    if not player:
        return
    holding = state.holdings.setdefault(pid, {}).setdefault("DM", {"qty": 0, "avg_cost": 0.0, "frozen_qty": 0, "short_qty": 0, "short_avg_cost": 0.0})
    available_cash = player["cash"] - player.get("frozen_cash", 0)
    available_qty = holding["qty"] - holding.get("frozen_qty", 0)

    signal = _compute_signal(rd["strategy"], price, state.price_history, holding, player, state.news_feed)
    signal += random.uniform(-0.2, 0.2)
    signal = max(-1, min(1, signal))

    if signal > 0.25 and available_cash > 200 and holding["qty"] < rd["position_limit"]:
        invest_pct = min(signal * rd["risk"], 0.8)
        budget = int(available_cash * invest_pct)
        qty = min(int(budget / price), rd["position_limit"] - holding["qty"])
        qty = max(0, min(qty, random.randint(100, 1000)))
        if qty >= 100:
            await execute_trade(pid, {
                "stock_symbol": "DM", "quantity": qty, "trade_type": "buy",
            })
    elif signal < -0.25 and available_qty > 0:
        sell_pct = min(abs(signal), 1.0)
        qty = int(available_qty * sell_pct)
        qty = max(0, min(qty, random.randint(100, 2000)))
        if qty >= 100:
            await execute_trade(pid, {
                "stock_symbol": "DM", "quantity": qty, "trade_type": "sell",
            })


async def retail_trading_loop():
    state = get_global_state()
    tick_count = 0
    while True:
        await asyncio.sleep(PRICE_TICK_INTERVAL)
        tick_count += 1
        retail_ids = list(state.retail_data.keys())
        if not retail_ids:
            continue
        sample_size = min(len(retail_ids), random.randint(10, 20))
        active = random.sample(retail_ids, sample_size)
        for pid in active:
            rd = state.retail_data.get(pid)
            if not rd:
                continue
            if tick_count - rd["last_tick"] < rd["cooldown"]:
                continue
            rd["last_tick"] = tick_count
            try:
                await _retail_make_decision(pid, rd, state)
            except Exception as e:
                logger.error(f"Retail {pid} error: {e}")


# ---------------------------------------------------------------------------
# Quant Fund trading (量化基金) — 大额交易制造波动
# ---------------------------------------------------------------------------"""
assert old in content, "Patch 5"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# 6. 庄家交易逻辑 — 在 _quant_make_decision 之后插入
# ============================================================
content = ''.join(lines)
old = """# ---------------------------------------------------------------------------
# Trade execution — 订单簿撮合引擎
# ---------------------------------------------------------------------------"""
new = """# ---------------------------------------------------------------------------
# 庄家操盘：4 阶段周期（吸筹->拉升->洗盘->出货）
# ---------------------------------------------------------------------------
async def _zhuangjia_make_decision(state):
    stock = state.stocks.get("DM")
    if not stock:
        return
    price = stock["price"]
    player = state.players.get("zhuangjia")
    if not player:
        return
    zd = state.zhuang_data
    if not zd:
        return
    holding = state.holdings.setdefault("zhuangjia", {}).setdefault("DM", {"qty": 0, "avg_cost": 0.0, "frozen_qty": 0, "short_qty": 0, "short_avg_cost": 0.0})

    ma20 = _ma(state.price_history, 20) or price
    phase = zd.get("phase", "accumulate")
    zd["phase_ticks"] = zd.get("phase_ticks", 0) + 1
    available_cash = player["cash"] - player.get("frozen_cash", 0)
    available_qty = holding["qty"] - holding.get("frozen_qty", 0)

    if phase == "accumulate" and (price > ma20 * 1.03 or zd["phase_ticks"] > 250):
        zd["phase"] = "pump"
        zd["phase_ticks"] = 0
        logger.info("庄家进入拉升阶段")
    elif phase == "pump" and (price > zd.get("target_price", price) or zd["phase_ticks"] > 80):
        zd["phase"] = "shakeout"
        zd["phase_ticks"] = 0
        logger.info("庄家进入洗盘阶段")
    elif phase == "shakeout" and (price < ma20 * 0.97 or zd["phase_ticks"] > 50):
        zd["phase"] = "distribute"
        zd["phase_ticks"] = 0
        logger.info("庄家进入出货阶段")
    elif phase == "distribute" and (holding["qty"] < 50000 or zd["phase_ticks"] > 200):
        zd["phase"] = "accumulate"
        zd["phase_ticks"] = 0
        logger.info("庄家重新进入吸筹阶段")

    phase = zd["phase"]
    if phase == "accumulate":
        if available_cash > 500000 and holding["qty"] < zd["position_limit"]:
            limit_price = round(price * random.uniform(0.95, 0.99), 4)
            qty = min(int(available_cash * 0.08 / price), 80000)
            if qty >= 5000:
                await place_limit_order("zhuangjia", {
                    "stock_symbol": "DM", "quantity": qty,
                    "order_type": "buy", "price": limit_price,
                })
    elif phase == "pump":
        if available_cash > 500000:
            qty = min(int(available_cash * 0.12 / price), 100000)
            if qty >= 5000:
                await execute_trade("zhuangjia", {
                    "stock_symbol": "DM", "quantity": qty, "trade_type": "buy",
                })
        if not zd.get("target_price"):
            zd["target_price"] = round(price * 1.15, 2)
    elif phase == "shakeout":
        if available_qty > 50000:
            qty = min(int(available_qty * 0.12), 50000)
            if qty >= 5000:
                await execute_trade("zhuangjia", {
                    "stock_symbol": "DM", "quantity": qty, "trade_type": "sell",
                })
    elif phase == "distribute":
        if available_qty > 50000:
            limit_price = round(price * random.uniform(1.0, 1.05), 4)
            qty = min(int(available_qty * 0.15), 150000)
            if qty >= 5000:
                await place_limit_order("zhuangjia", {
                    "stock_symbol": "DM", "quantity": qty,
                    "order_type": "sell", "price": limit_price,
                })


async def zhuangjia_trading_loop():
    state = get_global_state()
    tick_count = 0
    while True:
        await asyncio.sleep(PRICE_TICK_INTERVAL)
        tick_count += 1
        if tick_count % random.randint(2, 4) != 0:
            continue
        try:
            await _zhuangjia_make_decision(state)
        except Exception as e:
            logger.error(f"庄家 error: {e}")


# ---------------------------------------------------------------------------
# Trade execution — 订单簿撮合引擎
# ---------------------------------------------------------------------------"""
assert old in content, "Patch 6"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# 7. EPS/NAV 动态漂移
# ============================================================
content = ''.join(lines)
old = """        # --- AI 证监会检查 every 60 ticks ---
        if tick_count % 60 == 0:
            try:
                await sec_regulator_check()
            except Exception as e:
                logger.error(f"SEC regulator error: {e}")"""
new = """        # --- AI 证监会检查 every 60 ticks ---
        if tick_count % 60 == 0:
            try:
                await sec_regulator_check()
            except Exception as e:
                logger.error(f"SEC regulator error: {e}")

        # --- EPS/NAV 动态漂移 every 60 ticks ---
        if tick_count % 60 == 0:
            for sym_eps, sd_eps in state.stocks.items():
                sd_eps["eps"] = round(sd_eps["eps"] * random.uniform(0.98, 1.02), 4)
                sd_eps["nav"] = round(sd_eps["nav"] * random.uniform(0.99, 1.01), 4)"""
assert old in content, "Patch 7"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# 8. Timeshare 添加 avg_price
# ============================================================
content = ''.join(lines)
old = """            state.timeshare.append({
                "time": now_ms,
                "price": sd["price"],
            })"""
new = """            if not hasattr(state, '_vwap_value'):
                state._vwap_value = 0.0
                state._vwap_vol = 0
            if sd.get("volume", 0) > state._vwap_vol:
                vol_delta = sd["volume"] - state._vwap_vol
                state._vwap_value += sd["price"] * vol_delta
                state._vwap_vol = sd["volume"]
            avg_p = round(state._vwap_value / state._vwap_vol, 4) if state._vwap_vol > 0 else sd["price"]

            state.timeshare.append({
                "time": now_ms,
                "price": sd["price"],
                "avg_price": avg_p,
            })"""
assert old in content, "Patch 8"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# 9. execute_trade tape 添加 side 字段
# ============================================================
content = ''.join(lines)
old = """    # Add to trade tape
    state.trade_tape.insert(0, {
        "time": datetime.utcnow().strftime("%H:%M:%S"),
        "price": price,
        "quantity": qty,
        "type": trade_type,
    })"""
new = """    # Add to trade tape
    side = "active_buy" if trade_type in ("buy", "cover") else "active_sell"
    state.trade_tape.insert(0, {
        "time": datetime.utcnow().strftime("%H:%M:%S"),
        "price": price,
        "quantity": qty,
        "type": trade_type,
        "side": side,
    })"""
assert old in content, "Patch 9"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# 10. _sweep_sell_orders tape 添加 side
# ============================================================
content = ''.join(lines)
old = """        fills.append({"price": fill_price, "qty": fill_qty, "cost": fill_cost, "commission": buyer_comm})

        # 记录成交到 tape
        stock["buy_volume"] = stock.get("buy_volume", 0) + fill_qty"""
new = """        fills.append({"price": fill_price, "qty": fill_qty, "cost": fill_cost, "commission": buyer_comm})

        # 记录成交到 tape
        state.trade_tape.insert(0, {
            "time": datetime.utcnow().strftime("%H:%M:%S"),
            "price": fill_price,
            "quantity": fill_qty,
            "type": "buy",
            "side": "active_buy",
        })
        if len(state.trade_tape) > 100:
            state.trade_tape = state.trade_tape[:100]
        stock["buy_volume"] = stock.get("buy_volume", 0) + fill_qty"""
assert old in content, "Patch 10"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# 11. _sweep_buy_orders tape 添加 side
# ============================================================
content = ''.join(lines)
old = """        fills.append({"price": fill_price, "qty": fill_qty, "value": fill_value})

    filled = qty - remaining"""
new = """        fills.append({"price": fill_price, "qty": fill_qty, "value": fill_value})

        # 记录成交到 tape
        state.trade_tape.insert(0, {
            "time": datetime.utcnow().strftime("%H:%M:%S"),
            "price": fill_price,
            "quantity": fill_qty,
            "type": "sell",
            "side": "active_sell",
        })
        if len(state.trade_tape) > 100:
            state.trade_tape = state.trade_tape[:100]

    filled = qty - remaining"""
assert old in content, "Patch 11"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# 12. _execute_limit_order — 改为走订单簿 (行级操作避免缩进问题)
# ============================================================
# 找到该函数及其内部的 if/elif/else 块
content = ''.join(lines)
tmp_lines = content.splitlines(keepends=True)

func_start = None
for i, line in enumerate(tmp_lines):
    if 'async def _execute_limit_order(order: dict, quantity: int, price: float):' in line:
        func_start = i
        break
assert func_start is not None, "Patch 12: cannot find _execute_limit_order"

# Find buy branch
buy_start = None
for i in range(func_start, len(tmp_lines)):
    stripped = tmp_lines[i].lstrip()
    if stripped.startswith('if trade_type == "buy":'):
        buy_start = i
        break
assert buy_start is not None, "Patch 12: cannot find buy branch"

# Find where the if/elif/else block ends (back to function body indent level)
func_indent = len(tmp_lines[buy_start]) - len(tmp_lines[buy_start].lstrip())
block_end = None
for i in range(buy_start + 1, len(tmp_lines)):
    if not tmp_lines[i].strip():
        continue
    indent = len(tmp_lines[i]) - len(tmp_lines[i].lstrip())
    if indent <= func_indent:
        block_end = i
        break
assert block_end is not None, "Patch 12: cannot find block end"

print(f"  _execute_limit_order: line {func_start+1}, buy_start {buy_start+1}, block_end {block_end+1}")

new_block_lines = [
    '    if trade_type == "buy":\n',
    '        # 持仓上限检查\n',
    '        current_qty = holding.get("qty", 0)\n',
    '        if current_qty + qty_to_execute > MAX_POSITION_PER_PLAYER and not player_id.startswith(("ai_", "q_", "nat_", "zhuangjia", "retail_")):\n',
    '            return\n',
    '        # 走订单簿扫单\n',
    '        total_needed = round(price * qty_to_execute, 2)\n',
    '        available_cash = player["cash"] - player.get("frozen_cash", 0)\n',
    '        margin_debt = player.get("margin_debt", 0.0)\n',
    '        max_cash_for_buy = available_cash\n',
    '        if total_needed + commission > available_cash:\n',
    '            _, ratio = calc_player_assets(player_id)\n',
    '            if ratio is not None and ratio >= 300 and not player_id.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "zhuangjia", "retail_")):\n',
    '                max_cash_for_buy = available_cash * 2.0\n',
    '            else:\n',
    '                max_qty_by_cash = int((available_cash - commission) / price) if price > 0 else 0\n',
    '                qty_to_execute = min(qty_to_execute, max_qty_by_cash)\n',
    '                if qty_to_execute <= 0:\n',
    '                    return\n',
    '                total_needed = round(price * qty_to_execute, 2)\n',
    '        result = await _sweep_sell_orders(state, player_id, symbol, qty_to_execute, max_cash_for_buy)\n',
    '        if result:\n',
    '            fill_qty = result["filled_qty"]\n',
    '            fill_avg_price = result["avg_price"]\n',
    '            fill_total_cost = result["total_cost"]\n',
    '            fill_commission = result["commission"]\n',
    '            order["filled"] += fill_qty\n',
    '            if order["filled"] >= order["quantity"]:\n',
    '                order["status"] = "filled"\n',
    '            new_qty = holding["qty"] + fill_qty\n',
    '            holding["avg_cost"] = round(\n',
    '                (holding["avg_cost"] * holding["qty"] + fill_total_cost) / new_qty, 2\n',
    '            ) if new_qty > 0 else 0\n',
    '            holding["qty"] = new_qty\n',
    '            reserved_total = order.get("_reserved", total_needed)\n',
    '            fill_ratio = fill_qty / order["quantity"] if order["quantity"] > 0 else 0\n',
    '            unfreeze = round(reserved_total * fill_ratio, 2)\n',
    '            player["frozen_cash"] = max(0, player.get("frozen_cash", 0) - unfreeze)\n',
    '            stock["volume"] = stock.get("volume", 0) + fill_qty\n',
    '            mark_dirty(player_id)\n',
    '            impact = round(fill_avg_price * (fill_qty / SHARES_OUTSTANDING) * 50, 6)\n',
    '            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] + impact)), 4)\n',
    '        else:\n',
    '            if available_cash <= 0:\n',
    '                return\n',
    '            max_qty_cash = int(available_cash / price) if price > 0 else 0\n',
    '            qty_to_execute = min(qty_to_execute, max_qty_cash)\n',
    '            if qty_to_execute <= 0:\n',
    '                return\n',
    '            total_cost = round(price * qty_to_execute, 2)\n',
    '            commission = round(max(total_cost * COMMISSION_RATE, MIN_COMMISSION), 2)\n',
    '            new_qty = holding["qty"] + qty_to_execute\n',
    '            holding["avg_cost"] = round(\n',
    '                (holding["avg_cost"] * holding["qty"] + price * qty_to_execute) / new_qty, 2\n',
    '            ) if new_qty > 0 else 0\n',
    '            holding["qty"] = new_qty\n',
    '            player["cash"] = round(player["cash"] - total_cost - commission, 2)\n',
    '            mark_dirty(player_id)\n',
    '            impact = round(price * (qty_to_execute / SHARES_OUTSTANDING) * 100, 6)\n',
    '            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] + impact)), 4)\n',
    '            order["filled"] += qty_to_execute\n',
    '            if order["filled"] >= order["quantity"]:\n',
    '                order["status"] = "filled"\n',
    '            fill_commission = commission\n',
    '            fill_qty = qty_to_execute\n',
    '            fill_avg_price = price\n',
    '            fill_total_cost = total_cost\n',
    '\n',
    '    elif trade_type == "sell":\n',
    '        available_long = holding["qty"] - holding.get("frozen_qty", 0)\n',
    '        sell_from_long = min(qty_to_execute, max(0, available_long))\n',
    '        if sell_from_long <= 0:\n',
    '            return\n',
    '        qty_to_execute = sell_from_long\n',
    '        result = await _sweep_buy_orders(state, player_id, symbol, qty_to_execute)\n',
    '        if result:\n',
    '            fill_qty = result["filled_qty"]\n',
    '            fill_avg_price = result["avg_price"]\n',
    '            fill_total_proceeds = result["total_proceeds"]\n',
    '            fill_commission = result["commission"]\n',
    '            fill_stamp = result["stamp_tax"]\n',
    '            fill_fee = fill_commission + fill_stamp\n',
    '            order["filled"] += fill_qty\n',
    '            if order["filled"] >= order["quantity"]:\n',
    '                order["status"] = "filled"\n',
    '            holding["frozen_qty"] = max(0, holding.get("frozen_qty", 0) - fill_qty)\n',
    '            holding["qty"] -= fill_qty\n',
    '            if holding["qty"] == 0:\n',
    '                holding["avg_cost"] = 0.0\n',
    '            mark_dirty(player_id)\n',
    '            impact = round(fill_avg_price * (fill_qty / SHARES_OUTSTANDING) * 50, 6)\n',
    '            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] - impact)), 4)\n',
    '            commission = fill_commission\n',
    '            stamp_tax = fill_stamp\n',
    '            fill_fee = fill_fee\n',
    '        else:\n',
    '            total_cost = round(price * qty_to_execute, 2)\n',
    '            holding["frozen_qty"] = max(0, holding.get("frozen_qty", 0) - qty_to_execute)\n',
    '            commission = round(max(total_cost * COMMISSION_RATE, MIN_COMMISSION), 2)\n',
    '            stamp_tax = round(total_cost * STAMP_TAX_RATE, 2)\n',
    '            total_fee = commission + stamp_tax\n',
    '            net = round(total_cost - total_fee, 2)\n',
    '            margin_debt = player.get("margin_debt", 0)\n',
    '            if margin_debt > 0:\n',
    '                repay = min(net, margin_debt)\n',
    '                player["margin_debt"] = round(margin_debt - repay, 2)\n',
    '                player["cash"] = round(player["cash"] + net - repay, 2)\n',
    '            else:\n',
    '                player["cash"] = round(player["cash"] + net, 2)\n',
    '            holding["qty"] -= qty_to_execute\n',
    '            if holding["qty"] == 0:\n',
    '                holding["avg_cost"] = 0.0\n',
    '            mark_dirty(player_id)\n',
    '            impact = round(price * (qty_to_execute / SHARES_OUTSTANDING) * 100, 6)\n',
    '            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] - impact)), 4)\n',
    '            order["filled"] += qty_to_execute\n',
    '            if order["filled"] >= order["quantity"]:\n',
    '                order["status"] = "filled"\n',
    '            fill_qty = qty_to_execute\n',
    '            fill_avg_price = price\n',
    '            fill_total_cost = total_cost\n',
    '            fill_commission = commission\n',
    '            fill_fee = total_fee\n',
    '            fill_stamp = stamp_tax\n',
    '    else:\n',
    '        return\n',
    '\n',
    '    stock["volume"] += qty_to_execute\n',
]

# Replace lines
tmp_lines = tmp_lines[:buy_start] + new_block_lines + tmp_lines[block_end:]
lines = tmp_lines

print("Patch 12: OK")

# ============================================================
# 13. 系统玩家过滤添加 zhuangjia + retail_
# ============================================================
content = ''.join(lines)

# 13a. save_player_state
old = 'if pid.startswith("ai_") or pid.startswith("npc_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_"):'
new = 'if pid.startswith("ai_") or pid.startswith("npc_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_") or pid == "zhuangjia":'
assert old in content, "Patch 13d"
content = content.replace(old, new, 1)

old = 'if pid.startswith("ai_") or pid.startswith("npc_") or pid.startswith("_market_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_"):'
new = 'if pid.startswith("ai_") or pid.startswith("npc_") or pid.startswith("_market_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_") or pid == "zhuangjia":'
assert old in content, "Patch 13e"
content = content.replace(old, new, 1)

old = 'if pid.startswith("retail_") or pid.startswith("ai_") or pid.startswith("_market_") or pid.startswith("npc_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_"):'
new = 'if pid.startswith("retail_") or pid.startswith("ai_") or pid.startswith("_market_") or pid.startswith("npc_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_") or pid == "zhuangjia":'
assert old in content, "Patch 13g"
content = content.replace(old, new, 1)

old = 'not player_id.startswith("ai_") and not player_id.startswith("npc_") and not player_id.startswith("q_") and not player_id.startswith("nat_"):'
new = 'not player_id.startswith("ai_") and not player_id.startswith("npc_") and not player_id.startswith("q_") and not player_id.startswith("nat_") and player_id != "zhuangjia" and not player_id.startswith("retail_"):'
assert old in content, "Patch 13f"
content = content.replace(old, new, 1)

idx = content.find("async def save_player_state")
assert idx > 0, "Patch 13a"
old = 'or player_id.startswith("nat_"):'
new = 'or pid.startswith("nat_") or pid.startswith("zhuangjia"):'
sub = content.find(old, idx)
assert sub > 0, "Patch 13a2"
content = content[:sub] + content[sub:].replace(old, new, 1)

old = 'pid.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "_market_"))'
new = 'pid.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "zhuangjia", "_market_"))'
idx = content.find("async def load_all_player_states")
assert idx > 0, "Patch 13b"
sub = content.find(old, idx)
assert sub > 0, "Patch 13b2"
content = content[:sub] + content[sub:].replace(old, new, 1)

old = 'if pid.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "_market_")):'
new = 'if pid.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "zhuangjia", "_market_")):'
idx = content.find("重要：服务器重启后清空冻结字段，因为挂单（pending_orders）是内存中的，重启后已丢失")
assert idx > 0, "Patch 13c"
sub = content.find(old, idx)
assert sub > 0, "Patch 13c2"
content = content[:sub] + content[sub:].replace(old, new, 1)

old = 'not player_id.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_"))'
new = 'not player_id.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "zhuangjia", "retail_"))'
count = content.count(old)
assert count > 0, f"Patch 13h: found {count}"
content = content.replace(old, new)

idx = content.find("async def check_forced_liquidation")
assert idx > 0, "Patch 13i"
old = 'if pid.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "_market_")):'
sub = content.find(old, idx)
assert sub > 0, "Patch 13i2"
new = 'if pid.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "zhuangjia", "_market_")):'
content = content[:sub] + content[sub:].replace(old, new, 1)

lines = content.splitlines(keepends=True)

# ============================================================
# 14. 大单冲击 EPS/NAV
# ============================================================
content = ''.join(lines)
old = """    # Send trade_executed to player
    await manager.send_to(GLOBAL_ROOM_ID, player_id, {"""
new = """    # 大单冲击：成交 > 流通股 0.1% 时影响 EPS/NAV
    if fill_qty >= SHARES_OUTSTANDING * 0.001:
        eps_impact = random.uniform(-0.005, 0.01)
        nav_impact = random.uniform(-0.008, 0.005)
        if trade_type in ("buy", "cover"):
            stock["eps"] = round(stock["eps"] * (1 + eps_impact), 4)
        else:
            stock["eps"] = round(stock["eps"] * (1 - eps_impact * 0.5), 4)
        stock["nav"] = round(stock["nav"] * (1 + nav_impact), 4)

    # Send trade_executed to player
    await manager.send_to(GLOBAL_ROOM_ID, player_id, {"""
assert old in content, "Patch 14"
content = content.replace(old, new, 1)
lines = content.splitlines(keepends=True)

# ============================================================
# Write final file
# ============================================================
with open('backend/game_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"OK: game_engine.py patched successfully! Final size: {len(lines)} lines")
