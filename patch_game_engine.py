"""一次性修补 game_engine.py 实现所有 5 个功能的后端改动。"""
import re

with open('backend/game_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# 1. GlobalMarketState.__init__ — 添加 retail_data 和 zhuang_data
# ============================================================
old = '        self.quant_data: dict[str, dict] = {}'
new = '        self.quant_data: dict[str, dict] = {}\n        self.retail_data: dict[str, dict] = {}\n        self.zhuang_data: dict = {}'
assert old in content, "Patch 1: cant find quant_data init"
content = content.replace(old, new, 1)

# ============================================================
# 2. init_global_market — 添加散户初始化和庄家初始化
# ============================================================
# 在国家队初始化之后、恢复存档之前 插入散户+庄家
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

assert old in content, "Patch 2: cant find restore saved state"
content = content.replace(old, new, 1)

# ============================================================
# 3. init_global_market — 启动散户和庄家循环
# ============================================================
old = """    asyncio.create_task(npc_trading_loop())
    asyncio.create_task(quant_trading_loop())"""
new = """    asyncio.create_task(npc_trading_loop())
    asyncio.create_task(quant_trading_loop())
    asyncio.create_task(retail_trading_loop())
    asyncio.create_task(zhuangjia_trading_loop())"""
assert old in content, "Patch 3: cant find create_task section"
content = content.replace(old, new, 1)

# ============================================================
# 4. _compute_signal — 添加 3 个散户策略
# ============================================================
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
        cons_up = all(c > 0 for c in changes)  # 连涨3 tick
        cons_down = all(c < 0 for c in changes)  # 连跌3 tick
        if cons_up:
            return 0.6  # 追涨
        if cons_down:
            return -0.7  # 杀跌
        return random.uniform(-0.1, 0.1)

    elif strategy == "retail_panic":
        # 散户恐慌/贪婪：跌幅>5%恐慌卖出，涨幅>10%贪婪追入
        if len(history) < 10:
            return 0
        change_10 = (price - history[-10]) / history[-10]
        if change_10 < -0.05:
            return -0.9  # 恐慌清仓
        if change_10 > 0.10:
            return 0.8  # 贪婪追涨
        # 小幅震荡时随机
        return random.uniform(-0.2, 0.2)

    elif strategy == "retail_random":
        # 散户随机交易，但有跟风效应（受最近成交方向影响）
        r = random.random()
        if r < 0.20:
            return random.uniform(0.3, 0.6)
        elif r < 0.40:
            if holding["qty"] > 0:
                return random.uniform(-0.5, -0.2)
            return 0
        return 0

    return 0"""

assert old in content, "Patch 4: cant find _compute_signal news section"
content = content.replace(old, new, 1)

# ============================================================
# 5. 在 npc_trading_loop 之后添加 _retail_make_decision 和 retail_trading_loop
# ============================================================
old = """# ---------------------------------------------------------------------------
# Quant Fund trading (量化基金) — 大额交易制造波动
# ---------------------------------------------------------------------------"""

new = """async def _retail_make_decision(pid: str, rd: dict, state):
    \"\"\"单个散户的交易决策。\"\"\"
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
        # 散户买入
        invest_pct = min(signal * rd["risk"], 0.8)
        budget = int(available_cash * invest_pct)
        qty = min(int(budget / price), rd["position_limit"] - holding["qty"])
        qty = max(0, min(qty, random.randint(100, 1000)))
        if qty >= 100:
            await execute_trade(pid, {
                "stock_symbol": "DM", "quantity": qty, "trade_type": "buy",
            })

    elif signal < -0.25 and available_qty > 0:
        # 散户卖出
        sell_pct = min(abs(signal), 1.0)
        qty = int(available_qty * sell_pct)
        qty = max(0, min(qty, random.randint(100, 2000)))
        if qty >= 100:
            await execute_trade(pid, {
                "stock_symbol": "DM", "quantity": qty, "trade_type": "sell",
            })


async def retail_trading_loop():
    \"\"\"散户交易循环：每 tick 随机唤醒 10~20 个散户。\"\"\"
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

assert old in content, "Patch 5: cant find quant fund section header"
content = content.replace(old, new, 1)

# ============================================================
# 6. 庄家交易逻辑: 在 _quant_make_decision 之后、execute_trade 之前插入
# ============================================================
old = """# ---------------------------------------------------------------------------
# Trade execution — 订单簿撮合引擎
# ---------------------------------------------------------------------------"""

new = """# ---------------------------------------------------------------------------
# 庄家操盘：4 阶段周期（吸筹→拉升→洗盘→出货）
# ---------------------------------------------------------------------------
async def _zhuangjia_make_decision(state):
    \"\"\"庄家操盘决策。\"\"\"
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

    # ---- Phase transitions ----
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
        # 吸筹：价格低迷时挂低价限价单
        if available_cash > 500000 and holding["qty"] < zd["position_limit"]:
            limit_price = round(price * random.uniform(0.95, 0.99), 4)
            qty = min(int(available_cash * 0.08 / price), 80000)
            if qty >= 5000:
                await place_limit_order("zhuangjia", {
                    "stock_symbol": "DM", "quantity": qty,
                    "order_type": "buy", "price": limit_price,
                })

    elif phase == "pump":
        # 拉升：市价买入推高价格
        if available_cash > 500000:
            qty = min(int(available_cash * 0.12 / price), 100000)
            if qty >= 5000:
                await execute_trade("zhuangjia", {
                    "stock_symbol": "DM", "quantity": qty, "trade_type": "buy",
                })
        if not zd.get("target_price"):
            zd["target_price"] = round(price * 1.15, 2)

    elif phase == "shakeout":
        # 洗盘：小量卖出打压价格
        if available_qty > 50000:
            qty = min(int(available_qty * 0.12), 50000)
            if qty >= 5000:
                await execute_trade("zhuangjia", {
                    "stock_symbol": "DM", "quantity": qty, "trade_type": "sell",
                })

    elif phase == "distribute":
        # 出货：大量挂卖单
        if available_qty > 50000:
            limit_price = round(price * random.uniform(1.0, 1.05), 4)
            qty = min(int(available_qty * 0.15), 150000)
            if qty >= 5000:
                await place_limit_order("zhuangjia", {
                    "stock_symbol": "DM", "quantity": qty,
                    "order_type": "sell", "price": limit_price,
                })


async def zhuangjia_trading_loop():
    \"\"\"庄家交易循环：每 2~4 tick 运行一次。\"\"\"
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

assert old in content, "Patch 6: cant find trade execution section header"
content = content.replace(old, new, 1)

# ============================================================
# 7. price_tick_loop — EPS/NAV 动态漂移（tick_count % 60 == 0 块内）
# ============================================================
# tick_count % 60 已经有 SEC 检查，在 SEC 之后添加 EPS/NAV 漂移
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

assert old in content, "Patch 7: cant find SEC regulator check"
content = content.replace(old, new, 1)

# ============================================================
# 8. price_tick_loop — timeshare 添加 avg_price（VWAP）
# ============================================================
# VWAP = 累计成交金额 / 累计成交量
# 在股票初始化时添加 total_value 和 total_vol 追踪
# 找到 timeshare.append 调用并修改
old = """            state.timeshare.append({
                "time": now_ms,
                "price": sd["price"],
            })"""

new = """            # Track VWAP for average price line
            if not hasattr(state, '_vwap_value'):
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

assert old in content, "Patch 8: cant find timeshare.append"
content = content.replace(old, new, 1)

# ============================================================
# 9. execute_trade — tape 添加 side 字段
# ============================================================
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

assert old in content, "Patch 9: cant find execute_trade tape insert"
content = content.replace(old, new, 1)

# ============================================================
# 10. _sweep_sell_orders — tape 添加 side 字段
# ============================================================
# 找到 tape 记录
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

assert old in content, "Patch 10: cant find sweep_sell tape"
content = content.replace(old, new, 1)

# ============================================================
# 11. _sweep_buy_orders — tape 添加 side 字段
# ============================================================
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

assert old in content, "Patch 11: cant find sweep_buy tape area"
content = content.replace(old, new, 1)

# ============================================================
# 12. _execute_limit_order — 改为走订单簿 (rewrite buy/sell branches)
# ============================================================
# 找到 _execute_limit_order 函数的整体内容并替换
# 当前实现使用 impact formula，改为 sweep order book
old_func = """        if trade_type == "buy":
        # 持仓上限检查
        current_qty = holding.get("qty", 0)
        if current_qty + qty_to_execute > MAX_POSITION_PER_PLAYER and not player_id.startswith("ai_") and not player_id.startswith("q_") and not player_id.startswith("nat_"):
            return
        total_needed = round(price * qty_to_execute, 2)
        total_required = round(total_needed + commission, 2)
        available_cash = player["cash"] - player.get("frozen_cash", 0)
        margin_debt = player.get("margin_debt", 0.0)
        # 担保比例检查
        _, ratio = calc_player_assets(player_id)
        needs_margin = total_required > available_cash
        # 融资融券准入门槛
        if needs_margin and not player_id.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_")):
            gross = player["cash"]
            for sym_g, h_g in state.holdings.get(player_id, {}).items():
                sp_g = state.stocks.get(sym_g, {})
                gross += h_g["qty"] * sp_g.get("price", 0)
            if gross < MARGIN_MIN_ASSETS:
                return
        if needs_margin and ratio is not None and ratio < 300 and not player_id.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_")):
            return
        buying_power = round(available_cash * 2.0, 2)
        if total_required > buying_power:
            return
        # Split between cash and margin
        cash_used = min(available_cash, total_required)
        margin_used = round(total_required - cash_used, 2)
        player["cash"] = round(player["cash"] - cash_used, 2)
        if margin_used > 0:
            player["margin_debt"] = round(margin_debt + margin_used, 2)
        # Unfreeze cash
        reserved_total = order.get("_reserved", total_required)
        fill_ratio = qty_to_execute / order["quantity"]
        unfreeze = round(reserved_total * fill_ratio, 2)
        player["frozen_cash"] = max(0, player.get("frozen_cash", 0) - unfreeze)
        # Update holdings
        new_qty = holding["qty"] + qty_to_execute
        holding["avg_cost"] = round(
            (holding["avg_cost"] * holding["qty"] + price * qty_to_execute) / new_qty, 2
        ) if new_qty > 0 else 0
        holding["qty"] = new_qty
        # Price impact: buying pushes price up
        impact = round(price * (qty_to_execute / SHARES_OUTSTANDING) * 100, 6)
        stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] + impact)), 4)
        mark_dirty(player_id)
    elif trade_type == "sell":
        available_long = holding["qty"] - holding.get("frozen_qty", 0)
        sell_from_long = min(qty_to_execute, max(0, available_long))
        if sell_from_long <= 0:
            return  # nothing to sell
        qty_to_execute = sell_from_long  # actual fill
        total_cost = round(price * qty_to_execute, 2)
        # Unfreeze holdings
        holding["frozen_qty"] = max(0, holding.get("frozen_qty", 0) - sell_from_long)
        # Sell from long
        long_cost = round(price * qty_to_execute, 2)
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
        holding["qty"] -= qty_to_execute
        if holding["qty"] == 0:
            holding["avg_cost"] = 0.0
        # Recalculate commission/stamp for response
        commission = round(max(total_cost * COMMISSION_RATE, MIN_COMMISSION), 2)
        stamp_tax = round(total_cost * STAMP_TAX_RATE, 2)
        total_fee = commission + stamp_tax
        # Price impact: selling pushes price down
        impact = round(price * (qty_to_execute / SHARES_OUTSTANDING) * 100, 6)
        stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] - impact)), 4)
        mark_dirty(player_id)
    else:
        return"""

new_func = """        if trade_type == "buy":
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
                # 钱不够又没融资额度
                # 只能买能买得起的数量
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
            # Update limit order tracking
            order["filled"] += fill_qty
            if order["filled"] >= order["quantity"]:
                order["status"] = "filled"
            # Update buy-side holding from sweep (reverse of sell holding decrease)
            # _sweep_sell_orders already handles: seller cash, seller frozen stocks, buyer cash deduction
            # But buyer's holdings need to be updated - sweep does NOT update buyer's holdings!
            new_qty = holding["qty"] + fill_qty
            holding["avg_cost"] = round(
                (holding["avg_cost"] * holding["qty"] + fill_total_cost) / new_qty, 2
            ) if new_qty > 0 else 0
            holding["qty"] = new_qty
            # Unfreeze the reserved cash for the filled portion
            reserved_total = order.get("_reserved", total_needed)
            fill_ratio = fill_qty / order["quantity"] if order["quantity"] > 0 else 0
            unfreeze = round(reserved_total * fill_ratio, 2)
            player["frozen_cash"] = max(0, player.get("frozen_cash", 0) - unfreeze)
            # Buy commission already deducted inside _sweep_sell_orders
            stock["volume"] = stock.get("volume", 0) + fill_qty
            mark_dirty(player_id)
            # Price impact from last fill price
            impact = round(fill_avg_price * (fill_qty / SHARES_OUTSTANDING) * 50, 6)
            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] + impact)), 4)
        else:
            # No sell orders to sweep, try impact formula as fallback
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
            # Still update order
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
        # 走订单簿扫单
        result = await _sweep_buy_orders(state, player_id, symbol, qty_to_execute)
        if result:
            fill_qty = result["filled_qty"]
            fill_avg_price = result["avg_price"]
            fill_total_proceeds = result["total_proceeds"]
            fill_commission = result["commission"]
            fill_stamp = result["stamp_tax"]
            fill_fee = fill_commission + fill_stamp
            # Update limit order tracking
            order["filled"] += fill_qty
            if order["filled"] >= order["quantity"]:
                order["status"] = "filled"
            # Unfreeze holdings
            holding["frozen_qty"] = max(0, holding.get("frozen_qty", 0) - fill_qty)
            holding["qty"] -= fill_qty
            if holding["qty"] == 0:
                holding["avg_cost"] = 0.0
            # Cash already handled by _sweep_buy_orders
            mark_dirty(player_id)
            impact = round(fill_avg_price * (fill_qty / SHARES_OUTSTANDING) * 50, 6)
            stock["price"] = round(max(PRICE_MIN, min(PRICE_MAX, stock["price"] - impact)), 4)
            commission = fill_commission
            stamp_tax = fill_stamp
            total_fee = fill_fee
        else:
            # No buy orders to sweep, impact fallback
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
            # Update order
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
        return"""

assert old_func in content, f"Patch 12: cant find _execute_limit_order buy/sell section. Found at index {content.find('if trade_type == \"buy\":')}"
content = content.replace(old_func, new_func, 1)

# ============================================================
# 13. 所有系统玩家过滤添加 zhuangjia
# ============================================================

# 13a. save_player_state filter
old = "or pid.startswith(\"nat_\"):"
new = 'or pid.startswith("nat_") or pid.startswith("zhuangjia"):'
# Only replace in save_player_state (the first occurrence after that function definition)
idx = content.find("async def save_player_state")
assert idx > 0, "Patch 13a: cant find save_player_state"
sub_idx = content.find(old, idx)
assert sub_idx > 0, "Patch 13a: cant find nat_ filter in save_player_state"
content = content[:sub_idx] + content[sub_idx:].replace(old, new, 1)

# 13b. load_all_player_states filter (inst_ startswith tuple)
old = 'pid.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "_market_"))'
new = 'pid.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "zhuangjia", "_market_"))'
idx = content.find("async def load_all_player_states")
assert idx > 0, "Patch 13b: cant find load_all_player_states"
sub_idx = content.find(old, idx)
assert sub_idx > 0, "Patch 13b: cant find filter in load_all_player_states"
content = content[:sub_idx] + content[sub_idx:].replace(old, new, 1)

# 13c. Another load_all_player_states filter (the inst_ tuple at line ~212)
old = 'if pid.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "_market_")):'
new = 'if pid.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "zhuangjia", "_market_")):'
# Make sure we get the right one (in the frozen_cash reset block)
idx2 = content.find("frozen_cash 是内存中的，重启后已丢失")
assert idx2 > 0, "Patch 13c: cant find frozen_cash comment"
sub_idx2 = content.find(old, idx2)
assert sub_idx2 > 0, "Patch 13c: cant find second load filter"
content = content[:sub_idx2] + content[sub_idx2:].replace(old, new, 1)

# 13d. price_tick_loop asset_history filter
old = 'if pid.startswith("ai_") or pid.startswith("npc_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_"):'
new = 'if pid.startswith("ai_") or pid.startswith("npc_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_") or pid == "zhuangjia":'
assert old in content, "Patch 13d: cant find asset_history filter"
content = content.replace(old, new, 1)

# 13e. price_tick_loop day_start_assets filter
old = 'if pid.startswith("ai_") or pid.startswith("npc_") or pid.startswith("_market_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_"):'
new = 'if pid.startswith("ai_") or pid.startswith("npc_") or pid.startswith("_market_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_") or pid == "zhuangjia":'
assert old in content, "Patch 13e: cant find day_start_assets filter"
content = content.replace(old, new, 1)

# 13f. execute_trade MAX_ORDER_QTY filter
old = 'not player_id.startswith("ai_") and not player_id.startswith("npc_") and not player_id.startswith("q_") and not player_id.startswith("nat_"):'
new = 'not player_id.startswith("ai_") and not player_id.startswith("npc_") and not player_id.startswith("q_") and not player_id.startswith("nat_") and player_id != "zhuangjia" and not player_id.startswith("retail_"):'
assert old in content, "Patch 13f: cant find MAX_ORDER_QTY filter"
content = content.replace(old, new, 1)

# 13g. leaderboard filter - already has retail_, just add zhuangjia
old = 'if pid.startswith("retail_") or pid.startswith("ai_") or pid.startswith("_market_") or pid.startswith("npc_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_"):'
new = 'if pid.startswith("retail_") or pid.startswith("ai_") or pid.startswith("_market_") or pid.startswith("npc_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_") or pid == "zhuangjia":'
assert old in content, "Patch 13g: cant find leaderboard filter"
content = content.replace(old, new, 1)

# 13h. _execute_limit_order margin check filter (nat_ tuple)
old = 'not player_id.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_"))'
new = 'not player_id.startswith(("ai_", "npc_", "inst_", "hot_", "q_", "nat_", "zhuangjia", "retail_"))'
# Replace all remaining occurrences of this pattern
count = content.count(old)
assert count > 0, f"Patch 13h: cant find margin filter (found {count})"
content = content.replace(old, new)

# 13i. Forced liquidation filter - add zhuangjia and retail_
old = 'if pid.startswith("ai_") or pid.startswith("npc_") or pid.startswith("_market_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_"):'
# This pattern appears in multiple places - find the one in check_forced_liquidation
idx = content.find("async def check_forced_liquidation")
assert idx > 0, "Patch 13i: cant find forced_liquidation"
sub_idx = content.find(old, idx)
assert sub_idx > 0, "Patch 13i: cant find forced_liquidation filter"
content = content[:sub_idx] + content[sub_idx:].replace(old, 'if pid.startswith("ai_") or pid.startswith("npc_") or pid.startswith("_market_") or pid.startswith("inst_") or pid.startswith("hot_") or pid.startswith("q_") or pid.startswith("nat_") or pid == "zhuangjia" or pid.startswith("retail_"):', 1)

# ============================================================
# 14. 大单成交冲击 EPS/NAV
# ============================================================
# 在 execute_trade 中如果有大单，影响 EPS/NAV
# 在交易完成的 portfolio_update 发送之前添加
old = """    # Send trade_executed to player
    await manager.send_to(GLOBAL_ROOM_ID, player_id, {"""

new = """    # 大单冲击：成交 > 流通股 0.1% 时影响 EPS/NAV
    if fill_qty >= SHARES_OUTSTANDING * 0.001:
        eps_impact = random.uniform(-0.005, 0.01)  # 买入利好，卖出利空
        nav_impact = random.uniform(-0.008, 0.005)
        if trade_type in ("buy", "cover"):
            stock["eps"] = round(stock["eps"] * (1 + eps_impact), 4)
        else:
            stock["eps"] = round(stock["eps"] * (1 - eps_impact * 0.5), 4)
        stock["nav"] = round(stock["nav"] * (1 + nav_impact), 4)

    # Send trade_executed to player
    await manager.send_to(GLOBAL_ROOM_ID, player_id, {"""

assert old in content, "Patch 14: cant find trade_executed send section"
content = content.replace(old, new, 1)

# Write the result
with open('backend/game_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("OK: game_engine.py patched successfully!")
print(f"File size: {len(content)} chars")
