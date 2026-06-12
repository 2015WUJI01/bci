# Remove short selling (做空) but keep margin buy (融资)
f = open('backend/game_engine.py', 'r', encoding='utf-8')
content = f.read()
f.close()

# 1. execute_trade buy: remove short covering, keep margin
old_buy = '''        cover_cost = round(price * cover_qty, 2)
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

new_buy = '''        total_needed = round(price * qty, 2)
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

        # Execute buy
        player["cash"] = round(player["cash"] - total_required, 2)
        player["cash"] = round(player["cash"] + cash_used, 2)  # undo double-charge
        new_qty = holding["qty"] + qty
        holding["avg_cost"] = round(
            (holding["avg_cost"] * holding["qty"] + price * qty) / new_qty, 2
        ) if new_qty > 0 else 0
        holding["qty"] = new_qty
        stock["volume"] += qty
        stock["buy_volume"] = stock.get("buy_volume", 0) + qty
        impact = round(price * (qty / SHARES_OUTSTANDING) * 0.5, 4)
        stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] + impact)), 2)'''

# Fix: the buy section is more complex, let me just rewrite it simply
# Actually, let me re-read the current state to write a cleaner replacement

f2 = open('backend/game_engine.py', 'r', encoding='utf-8')
content2 = f2.read()
f2.close()

# Find the buy section start
idx = content2.find('        # Pre-check total cash needed')
if idx >= 0:
    print('found old buy style, replace it')
else:
    idx = content2.find('        cover_cost = round(price * cover_qty, 2)')
    if idx >= 0:
        print('found current buy style with cover')
    else:
        idx = content2.find("        total_needed = round(price * qty, 2)")
        if idx >= 0:
            print('found target new style')

# Find the sell section
idx2 = content2.find('        # Part 1: Sell from long position')
idx3 = content2.find('        # Part 2: Open short position (sell what you don\'t have)')
if idx3 >= 0:
    print(f'found short sell at {idx3}')
else:
    idx3 = content2.find('            # Open new short position for excess')
    if idx3 >= 0:
        print(f'found limit order short at {idx3}')
    else:
        print('no short sell found')

# Find the end of sell section
idx4 = content2.find("    else:")
idx5 = content2.find("        await manager.send_to(GLOBAL_ROOM_ID, player_id, {")
if idx5 > idx2:
    sell_section = content2[idx2:idx5]
    print(f'sell section from {idx2} to {idx5}')

# Check holdings_list for short fields
if 'short_qty' in content2:
    print('short_qty found in holdings list')
if 'short_pnl' in content2:
    print('short_pnl found in holdings list')
