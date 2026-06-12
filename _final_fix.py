# -*- coding: utf-8 -*-
"""Clean rewrite of the game-grid section and surrounding structure."""
path = r'D:\hl\炒股\frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact boundaries
grid_start = content.find('<!-- Main Grid -->')
right_start = content.find('<!-- Right: Order Book + Tape + Tabbed -->')

# Also find the floating panel section and toast
ftp_start = content.find('<!-- =========')
toast_start = content.find('<div id="toast"')

if grid_start < 0 or right_start < 0:
    print(f'ERROR: grid_start={grid_start}, right_start={right_start}')
    exit(1)

print(f'grid_start={grid_start}, right_start={right_start}')
print(f'ftp_start={ftp_start}, toast_start={toast_start}')

# Build the new game-grid section
new_game_grid = """    <!-- Main Grid (center + right, left column = floating panel) -->
    <div class="game-grid">
      <!-- Center: K-line Chart (main content) -->
      <div class="panel-center">
        <div class="panel kline-panel" style="flex:1;">
          <div class="panel-header">K线图</div>
          <div class="kline-container">
            <canvas id="kline-canvas" width="400" height="360"></canvas>
            <div class="kline-axis-x" id="kline-time">--:--</div>
            <div class="indicator-selector">
              <button class="indicator-btn active" data-indicator="MACD" onclick="setIndicator('MACD')">MACD</button>
              <button class="indicator-btn" data-indicator="KDJ" onclick="setIndicator('KDJ')">KDJ</button>
              <button class="indicator-btn" data-indicator="RSI" onclick="setIndicator('RSI')">RSI</button>
              <button class="indicator-btn" data-indicator="BOLL" onclick="setIndicator('BOLL')">BOLL</button>
            </div>
            <div class="kline-period-selector">
              <button class="kline-period-btn active" data-period="chart" onclick="switchKlinePeriod('chart')">分时</button>
              <button class="kline-period-btn" data-period="kline-4t" onclick="switchKlinePeriod('kline-4t')">K线</button>
              <button class="kline-period-btn" data-period="kline-1t" onclick="switchKlinePeriod('kline-1t')">Tick</button>
              <button class="kline-period-btn" data-period="kline-20t" onclick="switchKlinePeriod('kline-20t')">1分</button>
              <button class="kline-period-btn" data-period="kline-1d" onclick="switchKlinePeriod('kline-1d')">日K</button>
              <button class="kline-period-btn" data-period="kline-1w" onclick="switchKlinePeriod('kline-1w')">周K</button>
              <button class="kline-period-btn" data-period="kline-1m" onclick="switchKlinePeriod('kline-1m')">月K</button>
            </div>
          </div>
        </div>
        <!-- Holdings below chart -->
        <div class="panel">
          <div class="panel-header">持仓明细</div>
          <div class="holdings-table" id="holdings-table">
            <div class="holding-row holding-header">
              <span>股票</span><span>数量</span><span>均价</span><span>现价</span><span>市值</span><span>盈亏</span><span>收益率</span>
            </div>
          </div>
        </div>
      </div>
"""

# Replace everything from grid_start to right_start with our new grid
# Find the end of the grid: look for the closing </div> after the right section
# The structure is: game-grid div → [panel-center, panel-right] → </div>
# Find the second </div> after right_start that doesn't have matching content

# Better approach: find from grid_start to the closing </div> at game-grid level
# Look for the pattern: after right section content, there will be a </div> closing game-grid
# followed by </div> closing game-page

# Find where the current grid section ends - it should be:
# ...right content...
#     </div>     <- closes panel-right
#   </div>       <- closes game-grid
# </div>         <- closes game-page

# Find the first </div> after the point where right content ends
# We need to find the </div> that closes game-grid

# Let's find "<!-- Right:" and then count nesting to find the game-grid closing
# Actually let's be simpler: find the first two </div> after right_start that are alone on their line

# Find the portion of content from right_start
# We need to replace from grid_start to the end of game-grid
# The pattern is: there should be 3 closing divs after right section content:
#   </div> (panel-right)
# </div> (game-grid)
# then either game-page or something else

# Let's scan from right_start for the closing structure
section_after_right = content[right_start:]
lines = section_after_right.split('\n')
closing_divs_found = 0
grid_end_offset = 0

for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == '</div>':
        closing_divs_found += 1
        # The 2nd </div> closes game-grid (1st closes panel-right)
        if closing_divs_found == 2:
            # Include this line
            grid_end_offset = sum(len(l) + 1 for l in lines[:i+1]) - 1
            break

grid_end = right_start + grid_end_offset
print(f'grid_end={grid_end}')

# Now replace from grid_start to grid_end
before_grid = content[:grid_start]
after_grid = content[grid_end:]

new_content = before_grid + new_game_grid + after_grid

# Remove all duplicate floating panels (there might be remnants)
while 'Floating Trading Panel (draggable)' in new_content:
    start = new_content.find('<!-- =========')
    end = new_content.find('</div>', new_content.find('floating-trade-panel'))
    next_close = new_content.find('</div>', end + 6)
    if next_close > 0:
        end_of_section = next_close + 6
    else:
        end_of_section = end + 6
    new_content = new_content[:start] + new_content[end_of_section:]
    print(f'Removed one floating panel, length={len(new_content)}')

# Add new floating panel before toast
toast_pos = new_content.find('<div id="toast"')
if toast_pos > 0:
    ftp_html = """  <!-- ============================================================
       Floating Trading Panel (draggable)
       ============================================================ -->
  <div id="floating-trade-panel" class="ftp">
    <div class="ftp-header" id="ftp-header">
      <span class="ftp-title">💼 交易面板</span>
      <div class="ftp-actions">
        <button class="ftp-btn" onclick="minimizeFtp()" title="最小化">─</button>
        <button class="ftp-btn" onclick="closeFtp()" title="关闭">✕</button>
      </div>
    </div>
    <div class="ftp-body" id="ftp-body">
      <!-- Portfolio compact -->
      <div class="ftp-section">
        <div class="ftp-portfolio">
          <div class="ftp-pf-row">
            <span class="ftp-pf-label">总资产</span>
            <span class="ftp-pf-value" id="pf-total">¥100,000.00</span>
            <span class="ftp-pf-pnl" id="pf-pnl">¥0.00 (0.00%)</span>
          </div>
          <div class="ftp-pf-sub">
            <span>可用 <b id="pf-cash">¥100,000.00</b></span>
            <span>市值 <b id="pf-stock-value">¥0.00</b></span>
            <span>当日 <b id="pf-day-pnl">¥0.00</b></span>
          </div>
        </div>
      </div>
      <!-- Trading form -->
      <div class="ftp-section">
        <div class="ftp-order-type">
          <button class="ftp-type-btn active" data-type="market" onclick="switchOrderType('market')">市价</button>
          <button class="ftp-type-btn" data-type="limit" onclick="switchOrderType('limit')">限价</button>
        </div>
        <div class="ftp-trade-row hidden" id="ftp-limit-row">
          <span class="ftp-trade-label">价格</span>
          <input type="number" id="trade-limit-price" min="0.01" step="0.01" placeholder="限价" autocomplete="off">
        </div>
        <div class="ftp-trade-row">
          <span class="ftp-trade-label">数量</span>
          <input type="number" id="trade-qty" min="1" value="100" step="100">
        </div>
        <div class="ftp-estimate" id="trade-estimate">预估: ¥0.00</div>
        <div class="ftp-trade-btns">
          <button class="btn btn-buy btn-sm" id="btn-buy" onclick="handleTrade('buy')">买入</button>
          <button class="btn btn-sell btn-sm" id="btn-sell" onclick="handleTrade('sell')">卖出</button>
        </div>
        <div id="trade-msg" class="trade-msg" style="font-size:11px;min-height:16px;"></div>
      </div>
      <!-- Pending orders -->
      <div class="ftp-section ftp-orders-section">
        <div class="ftp-orders-header">
          <span>我的委托</span>
          <button class="btn btn-xs btn-secondary" onclick="loadMyOrders()" style="font-size:10px;padding:1px 5px;">刷新</button>
        </div>
        <div class="ftp-orders" id="pending-orders-content">
          <div class="pending-orders-empty">暂无委托</div>
        </div>
      </div>
    </div>
  </div>

"""
    new_content = new_content[:toast_pos] + ftp_html + new_content[toast_pos:]
    print(f'Added floating panel before toast')

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'Final file length: {len(new_content)} chars')

# Verify
for item in ['pf-total', 'pf-cash', 'pf-stock-value', 'pf-day-pnl', 'pf-pnl']:
    count = new_content.count(f'id="{item}"')
    if count != 1:
        print(f'WARNING: id="{item}" appears {count} times!')
    else:
        print(f'OK: id="{item}" appears once')
