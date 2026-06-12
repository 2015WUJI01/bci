"""专门修补 _execute_limit_order 函数 — 改为走订单簿"""
with open('backend/game_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the _execute_limit_order function start
func_start = None
for i, line in enumerate(lines):
    if 'async def _execute_limit_order(order: dict, quantity: int, price: float):' in line:
        func_start = i
        break

assert func_start is not None, "Cannot find _execute_limit_order function"

# Find the function body: the first line of the buy branch
buy_start = None
for i in range(func_start, len(lines)):
    stripped = lines[i].lstrip()
    if stripped.startswith('if trade_type == "buy":'):
        buy_start = i
        break

assert buy_start is not None, "Cannot find buy branch start"

# Find the line after the buy/sell/else block (back to function body level)
# This is the line after `    else:\n        return\n` that has same indent as `if trade_type`
func_body_indent = len(lines[buy_start]) - len(lines[buy_start].lstrip())  # 4 spaces likely

# Find the end of the if/elif/else block
block_end = None
for i in range(buy_start + 1, len(lines)):
    if not lines[i].strip():  # skip empty lines
        continue
    indent = len(lines[i]) - len(lines[i].lstrip())
    if indent <= func_body_indent:
        block_end = i
        break

assert block_end is not None, "Cannot find block end"

print(f"Found _execute_limit_order at line {func_start+1}")
print(f"Buy branch at line {buy_start+1}")
print(f"Block ends at line {block_end+1}")

# Build replacement code
new_code = """    if trade_type == "buy":
        # 持仓上限检查
        current_qty = holding.get("qty", 0)
        if current_qty + qty_to_execute > MAX_POSITION_PER_PLAYER and not player_id.startswith(("ai_", "q_", "nat_", "zhuangjia", "retail_")):
            return
        # 走订单簿扫单
        total_needed = round(price * qty_to_execute, 2)
        available_cash = player["cash"] - player.get("frozen_cash", 0)
        margin_debt = player.get("margin_debt", 0.0)
        max_cash_for_buy = available_cash
        # 检查是否需要融资
        if total_needed + commission > available_cash:
            _, ratio = calc_player_assets(player_id)
            if ratio is not None and ratio >= 300 and not player_id.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "zhuangjia", "retail_")):
                max_cash_for_buy = available_cash * 2.0
            else:
                max_qty_by_cash = int((available_cash - commission) / price) if price > 0 else 0
                qty_to_execute = min(qty_to_execute, max_qty_by_cash)
                if qty_to_execute <= 0:
                    return
                total_needed = round(price * qty_to_execute, 2)
        result = await _sweep_sell_orders(state, player_id, symbol, qty_to_execute, max_cash_for_buy)
        if result:
            fill_qty = result["filled_qty"]
            fill_avg_price = result["avg_price"]
            fill_total_cost = result["total_cost"]
            fill_commission = result["commission"]
            order["filled"] += fill_qty
            if order["filled"] >= order["quantity"]:
                order["status"] = "filled"
            new_qty = holding["qty"] + fill_qty
            holding["avg_cost"] = round(
                (holding["avg_cost"] * holding["qty"] + fill_total_cost) / new_qty, 2
            ) if new_qty > 0 else 0
            holding["qty"] = new_qty
            reserved_total = order.get("_reserved", total_needed)
            fill_ratio = fill_qty / order["quantity"] if order["quantity"] > 0 else 0
            unfreeze = round(reserved_total * fill_ratio, 2)
            player["frozen_cash"] = max(0, player.get("frozen_cash", 0) - unfreeze)
            stock["volume"] = stock.get("volume", 0) + fill_qty
            mark_dirty(player_id)
            impact = round(fill_avg_price * (fill_qty / SHARES_OUTSTANDING) * 50, 6)
            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] + impact)), 4)
        else:
            if available_cash <= 0:
                return
            max_qty_cash = int(available_cash / price) if price > 0 else 0
            qty_to_execute = min(qty_to_execute, max_qty_cash)
            if qty_to_execute <= 0:
                return
            total_cost = round(price * qty_to_execute, 2)
            commission = round(max(total_cost * COMMISSION_RATE, MIN_COMMISSION), 2)
            new_qty = holding["qty"] + qty_to_execute
            holding["avg_cost"] = round(
                (holding["avg_cost"] * holding["qty"] + price * qty_to_execute) / new_qty, 2
            ) if new_qty > 0 else 0
            holding["qty"] = new_qty
            player["cash"] = round(player["cash"] - total_cost - commission, 2)
            mark_dirty(player_id)
            impact = round(price * (qty_to_execute / SHARES_OUTSTANDING) * 100, 6)
            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] + impact)), 4)
            order["filled"] += qty_to_execute
            if order["filled"] >= order["quantity"]:
                order["status"] = "filled"
            fill_commission = commission
            fill_qty = qty_to_execute
            fill_avg_price = price
            fill_total_cost = total_cost

    elif trade_type == "sell":
        available_long = holding["qty"] - holding.get("frozen_qty", 0)
        sell_from_long = min(qty_to_execute, max(0, available_long))
        if sell_from_long <= 0:
            return
        qty_to_execute = sell_from_long
        result = await _sweep_buy_orders(state, player_id, symbol, qty_to_execute)
        if result:
            fill_qty = result["filled_qty"]
            fill_avg_price = result["avg_price"]
            fill_total_proceeds = result["total_proceeds"]
            fill_commission = result["commission"]
            fill_stamp = result["stamp_tax"]
            fill_fee = fill_commission + fill_stamp
            order["filled"] += fill_qty
            if order["filled"] >= order["quantity"]:
                order["status"] = "filled"
            holding["frozen_qty"] = max(0, holding.get("frozen_qty", 0) - fill_qty)
            holding["qty"] -= fill_qty
            if holding["qty"] == 0:
                holding["avg_cost"] = 0.0
            mark_dirty(player_id)
            impact = round(fill_avg_price * (fill_qty / SHARES_OUTSTANDING) * 50, 6)
            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] - impact)), 4)
            commission = fill_commission
            stamp_tax = fill_stamp
            fill_fee = fill_fee
        else:
            total_cost = round(price * qty_to_execute, 2)
            holding["frozen_qty"] = max(0, holding.get("frozen_qty", 0) - qty_to_execute)
            commission = round(max(total_cost * COMMISSION_RATE, MIN_COMMISSION), 2)
            stamp_tax = round(total_cost * STAMP_TAX_RATE, 2)
            total_fee = commission + stamp_tax
            net = round(total_cost - total_fee, 2)
            margin_debt = player.get("margin_debt", 0)
            if margin_debt > 0:
                repay = min(net, margin_debt)
                player["margin_debt"] = round(margin_debt - repay, 2)
                player["cash"] = round(player["cash"] + net - repay, 2)
            else:
                player["cash"] = round(player["cash"] + net, 2)
            holding["qty"] -= qty_to_execute
            if holding["qty"] == 0:
                holding["avg_cost"] = 0.0
            mark_dirty(player_id)
            impact = round(price * (qty_to_execute / SHARES_OUTSTANDING) * 100, 6)
            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] - impact)), 4)
            order["filled"] += qty_to_execute
            if order["filled"] >= order["quantity"]:
                order["status"] = "filled"
            fill_qty = qty_to_execute
            fill_avg_price = price
            fill_total_cost = total_cost
            fill_commission = commission
            fill_fee = total_fee
            fill_stamp = stamp_tax
    else:
        return

    stock["volume"] += qty_to_execute""".splitlines(keepends=True)

# Replace lines from buy_start to block_end
new_lines = lines[:buy_start] + new_code + lines[block_end:]

with open('backend/game_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"OK: Replaced lines {buy_start+1} to {block_end+1}")
