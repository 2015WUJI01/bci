# Add margin trading (融资) support to game_engine.py
f = open('backend/game_engine.py', 'r', encoding='utf-8')
content = f.read()
f.close()

# 1. BUY: Add margin support
old_buy = '''        # Pre-check total cash needed
        cover_cost = round(price * cover_qty, 2)
        buy_cost = round(price * buy_qty, 2)
        total_needed = round(cover_cost + buy_cost, 2)
        commission_total = round(max(total_needed * COMMISSION_RATE, MIN_COMMISSION), 2)
        total_required = round(total_needed + commission_total, 2)
        available_cash = player["cash"] - player.get("frozen_cash", 0)
        if available_cash < total_required:
            await manager.send_to(GLOBAL_ROOM_ID, player_id, {
                "type": "trade_rejected",
                "data": {
                    "reason": f"现金不足（含佣金 ¥{commission_total:.2f}），需要 ¥{total_required:,.2f}，可用 ¥{available_cash:,.2f}",
                    "stock_symbol": symbol,
                    "requested_qty": qty,
                },
            })
            return

        # Step 1: Cover short position (buy to close)
        if cover_qty > 0:
            player["cash"] = round(player["cash"] - cover_cost, 2)
            holding["short_qty"] = short_qty - cover_qty
            if holding["short_qty"] <= 0:
                holding["short_qty"] = 0
                holding["short_avg_cost"] = 0.0
            stock["buy_volume"] = stock.get("buy_volume", 0) + cover_qty
            impact = round(price * (cover_qty / SHARES_OUTSTANDING) * 0.5, 4)
            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] + impact)), 2)

        # Step 2: Build long position (remaining qty)
        if buy_qty > 0:
            player["cash"] = round(player["cash"] - round(buy_cost + commission_total, 2), 2)
            new_qty = holding["qty"] + buy_qty
            holding["avg_cost"] = round(
                (holding["avg_cost"] * holding["qty"] + price * buy_qty) / new_qty, 2
            ) if new_qty > 0 else 0
            holding["qty"] = new_qty
            stock["buy_volume"] = stock.get("buy_volume", 0) + buy_qty
            impact = round(price * (buy_qty / SHARES_OUTSTANDING) * 0.5, 4)
            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] + impact)), 2)

        stock["volume"] += qty'''

new_buy = '''        cover_cost = round(price * cover_qty, 2)
        buy_cost = round(price * buy_qty, 2)
        total_needed = round(cover_cost + buy_cost, 2)
        commission_total = round(max(total_needed * COMMISSION_RATE, MIN_COMMISSION), 2)
        total_required = round(total_needed + commission_total, 2)
        available_cash = player["cash"] - player.get("frozen_cash", 0)
        margin_debt = player.get("margin_debt", 0.0)
        # 融资 (margin buy): up to 2x leverage
        buying_power = round(available_cash * 2.0, 2)
        if total_required > buying_power:
            await manager.send_to(GLOBAL_ROOM_ID, player_id, {
                "type": "trade_rejected",
                "data": {
                    "reason": f"购买力不足（含融资），需要 ¥{total_required:,.2f}，购买力 ¥{buying_power:,.2f}",
                    "stock_symbol": symbol,
                    "requested_qty": qty,
                },
            })
            return
        # Use cash first, then margin for remainder
        cash_used = min(available_cash, total_required)
        margin_used = round(total_required - cash_used, 2)
        player["cash"] = round(player["cash"] - cash_used, 2)
        if margin_used > 0:
            player["margin_debt"] = round(margin_debt + margin_used, 2)

        # Step 1: Cover short position (buy to close)
        if cover_qty > 0:
            player["cash"] = round(player["cash"] - cover_cost, 2)
            holding["short_qty"] = short_qty - cover_qty
            if holding["short_qty"] <= 0:
                holding["short_qty"] = 0
                holding["short_avg_cost"] = 0.0
            stock["buy_volume"] = stock.get("buy_volume", 0) + cover_qty
            impact = round(price * (cover_qty / SHARES_OUTSTANDING) * 0.5, 4)
            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] + impact)), 2)

        # Step 2: Build long position (remaining qty)
        if buy_qty > 0:
            player["cash"] = round(player["cash"] - round(buy_cost + commission_total, 2), 2)
            new_qty = holding["qty"] + buy_qty
            holding["avg_cost"] = round(
                (holding["avg_cost"] * holding["qty"] + price * buy_qty) / new_qty, 2
            ) if new_qty > 0 else 0
            holding["qty"] = new_qty
            stock["buy_volume"] = stock.get("buy_volume", 0) + buy_qty
            impact = round(price * (buy_qty / SHARES_OUTSTANDING) * 0.5, 4)
            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] + impact)), 2)

        stock["volume"] += qty'''

if old_buy in content:
    content = content.replace(old_buy, new_buy)
    print('OK: buy section updated for margin')
else:
    print('FAIL: buy section not found')

# 2. SELL: Repay margin debt first
old_sell = '''        # Part 1: Sell from long position
        if sell_long_qty > 0:
            long_cost = round(price * sell_long_qty, 2)
            long_commission = round(max(long_cost * COMMISSION_RATE, MIN_COMMISSION), 2)
            long_stamp = round(long_cost * STAMP_TAX_RATE, 2)
            long_fee = long_commission + long_stamp
            net_long = round(long_cost - long_fee, 2)
            player["cash"] = round(player["cash"] + net_long, 2)
            holding["qty"] -= sell_long_qty'''

new_sell = '''        # Part 1: Sell from long position
        if sell_long_qty > 0:
            long_cost = round(price * sell_long_qty, 2)
            long_commission = round(max(long_cost * COMMISSION_RATE, MIN_COMMISSION), 2)
            long_stamp = round(long_cost * STAMP_TAX_RATE, 2)
            long_fee = long_commission + long_stamp
            net_long = round(long_cost - long_fee, 2)
            margin_debt = player.get("margin_debt", 0)
            if margin_debt > 0:
                repay = min(net_long, margin_debt)
                player["margin_debt"] = round(margin_debt - repay, 2)
                player["cash"] = round(player["cash"] + net_long - repay, 2)
            else:
                player["cash"] = round(player["cash"] + net_long, 2)
            holding["qty"] -= sell_long_qty'''

if old_sell in content:
    content = content.replace(old_sell, new_sell)
    print('OK: sell section updated for margin')
else:
    print('FAIL: sell section not found')

# 3. total_assets calculation: include margin_debt
content = content.replace(
    'total_assets += mv - short_liability  # long adds value, short subtracts',
    'total_assets += mv - short_liability  # long adds value, short subtracts\ntotal_assets -= player.get("margin_debt", 0)  # margin debt subtracts'
)

# Also check the second occurrence
content = content.replace(
    'total_assets += mv - short_liability',
    'total_assets += mv - short_liability\ntotal_assets -= player.get("margin_debt", 0)  # margin debt'
)

print('OK: total_assets updated for margin')

# 4. Leaderboard: include margin_debt
old_leaderboard = '''            total += h["qty"] * cur_price  # long position
            short_qty = h.get("short_qty", 0)
            if short_qty > 0:
                total -= short_qty * cur_price  # short liability'''

new_leaderboard = '''            total += h["qty"] * cur_price  # long position
            short_qty = h.get("short_qty", 0)
            if short_qty > 0:
                total -= short_qty * cur_price  # short liability
        total -= pdata.get("margin_debt", 0)  # margin debt'''

if old_leaderboard in content:
    content = content.replace(old_leaderboard, new_leaderboard)
    print('OK: leaderboard updated')
else:
    print('FAIL: leaderboard not found')

# 5. Asset history: include margin_debt
old_asset_hist = '''                    total += h["qty"] * cur_price  # long position
                    short_qty = h.get("short_qty", 0)
                    if short_qty > 0:
                        total -= short_qty * cur_price  # short liability'''

new_asset_hist = '''                    total += h["qty"] * cur_price  # long position
                    short_qty = h.get("short_qty", 0)
                    if short_qty > 0:
                        total -= short_qty * cur_price  # short liability
                total -= pdata.get("margin_debt", 0)  # margin debt'''

if old_asset_hist in content:
    content = content.replace(old_asset_hist, new_asset_hist)
    print('OK: asset history updated')
else:
    print('FAIL: asset history not found')

# 6. portfolio_update: include margin_debt
content = content.replace(
    '"frozen_cash": player.get("frozen_cash", 0),\n        },\n    })',
    '"frozen_cash": player.get("frozen_cash", 0),\n            "margin_debt": player.get("margin_debt", 0),\n        },\n    })'
)
print('OK: portfolio_update has margin_debt')

# 7. Same for second portfolio_update
content = content.replace(
    '"frozen_cash": player.get("frozen_cash", 0), "holdings": holdings_list,',
    '"frozen_cash": player.get("frozen_cash", 0), "margin_debt": player.get("margin_debt", 0), "holdings": holdings_list,'
)
print('OK: second portfolio update has margin_debt')

# 8. Add margin interest in price_tick_loop (every 10 ticks)
# Find the section after asset history recording
old_interest = '''            if len(state.asset_history[pid]) > 500:
                    state.asset_history[pid] = state.asset_history[pid][-500:]

        # --- Track price history for retail AI trend detection ---'''

new_interest = '''            if len(state.asset_history[pid]) > 500:
                    state.asset_history[pid] = state.asset_history[pid][-500:]

        # --- Margin interest ---
        if tick_count % 20 == 0:
            for pid_m, pdata_m in list(state.players.items()):
                md = pdata_m.get("margin_debt", 0)
                if md > 0:
                    interest = round(md * 0.0003, 2)  # 0.03% per tick group (~20 ticks = 30s)
                    pdata_m["margin_debt"] = round(md + interest, 2)

        # --- Track price history for retail AI trend detection ---'''

if old_interest in content:
    content = content.replace(old_interest, new_interest)
    print('OK: margin interest added')
else:
    print('FAIL: margin interest not found')

# 9. Limit order buy: use margin
old_limit_buy = '''        total_needed = round(price * qty_to_execute, 2)
        commission_total = round(max(total_needed * COMMISSION_RATE, MIN_COMMISSION), 2)
        total_required = round(total_needed + commission_total, 2)
        if player["cash"] < total_required:
            return
        # Unfreeze cash'''

new_limit_buy = '''        total_needed = round(price * qty_to_execute, 2)
        commission_total = round(max(total_needed * COMMISSION_RATE, MIN_COMMISSION), 2)
        total_required = round(total_needed + commission_total, 2)
        available_cash = player["cash"] - player.get("frozen_cash", 0)
        margin_debt = player.get("margin_debt", 0.0)
        buying_power = round(available_cash * 2.0, 2)
        if total_required > buying_power:
            return
        # Split between cash and margin
        cash_used = min(available_cash, total_required)
        margin_used = round(total_required - cash_used, 2)
        player["cash"] = round(player["cash"] - cash_used, 2)
        if margin_used > 0:
            player["margin_debt"] = round(margin_debt + margin_used, 2)
        # Unfreeze cash'''

if old_limit_buy in content:
    content = content.replace(old_limit_buy, new_limit_buy)
    print('OK: limit order buy section updated')
else:
    print('FAIL: limit order buy section not found')

f = open('backend/game_engine.py', 'w', encoding='utf-8')
f.write(content)
f.close()
print('All done')
