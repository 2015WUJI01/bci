# -*- coding: utf-8 -*-
"""Remove the left column (panel-stock-left) and insert floating panel HTML + holdings below chart."""
path = r'D:\hl\炒股\frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find exact line boundaries
left_start = None
left_end = None
center_start = None
for i, line in enumerate(lines):
    if '<!-- Left: Account + Holdings + Trading -->' in line:
        left_start = i
    if left_start is not None and left_end is None and '<!-- Center:' in line:
        left_end = i - 1  # the line before <!-- Center:
        center_start = i

if left_start is None or left_end is None:
    print("ERROR: Could not find boundaries")
    exit(1)

print(f'Removing lines {left_start} to {left_end}')
print(f'  First: {lines[left_start].rstrip()}')
print(f'  Last:  {lines[left_end].rstrip()}')

# New HTML to insert after grid header
# We need to: keep the grid header, remove old left column, keep center + right + end
# The grid div starts at a line before left_start

# Find the grid start
grid_start = None
for i in range(left_start, max(left_start-10, 0), -1):
    if 'class="game-grid"' in lines[i]:
        grid_start = i
        break

print(f'Grid starts at line {grid_start}: {lines[grid_start].rstrip()}')

# Find the end of the entire right section (the closing </div> after all right panels)
# This is the </div> that closes game-grid
# We need to find the matching closing tag
# Strategy: find the </div> after the right section

# Build new file content
new_lines = lines[:left_start]  # up to but not including left_start

# Insert the holdings panel (moving it below the chart in the center column)
# Actually, we need to keep the center column as-is, the holdings will be added there later
# For now, just skip the left column entirely

# Find the end of the right column panel (the closing div of game-grid)
# Look for </div> <-- this closes game-grid, multiple lines after right section
game_grid_end = None
for i in range(center_start, len(lines)):
    stripped = lines[i].strip()
    if stripped == '</div>' and i > center_start:
        # Check if the next few lines contain the closing of game-page or toast
        # This should close game-grid
        game_grid_end = i
        # Verify by checking the next non-blank line after
        for j in range(i+1, min(i+5, len(lines))):
            s = lines[j].strip()
            if s == '<!-- =======' or s.startswith('</div>') and 'toast' in lines[j]:
                break
        break

# Hmm, this is getting complicated. Let me use a different approach.
# Just remove the left column lines and add the floating panel HTML before </body>

# Remove lines from left_start to left_end (inclusive)
new_lines = lines[:left_start]
# Append everything from center_start onward
new_lines.extend(lines[center_start:])

# Now add floating panel HTML before the toast div
toast_idx = None
for i, line in enumerate(new_lines):
    if '<div id="toast"' in line:
        toast_idx = i
        break

if toast_idx is not None:
    ftp_html = [
        '      <!-- ============================================================\n',
        '           Floating Trading Panel (draggable)\n',
        '           ============================================================ -->\n',
        '      <div id="floating-trade-panel" class="ftp">\n',
        '        <div class="ftp-header" id="ftp-header">\n',
        '          <span class="ftp-title">\U0001f4bc 交易面板</span>\n',
        '          <div class="ftp-actions">\n',
        '            <button class="ftp-btn" onclick="minimizeFtp()" title="最小化">─</button>\n',
        '            <button class="ftp-btn" onclick="closeFtp()" title="关闭">✕</button>\n',
        '          </div>\n',
        '        </div>\n',
        '        <div class="ftp-body" id="ftp-body">\n',
        '          <!-- Portfolio compact -->\n',
        '          <div class="ftp-section">\n',
        '            <div class="ftp-portfolio">\n',
        '              <div class="ftp-pf-row">\n',
        '                <span class="ftp-pf-label">总资产</span>\n',
        '                <span class="ftp-pf-value" id="pf-total">¥100,000.00</span>\n',
        '                <span class="ftp-pf-pnl" id="pf-pnl">¥0.00 (0.00%)</span>\n',
        '              </div>\n',
        '              <div class="ftp-pf-sub">\n',
        '                <span>可用 <b id="pf-cash">¥100,000.00</b></span>\n',
        '                <span>市值 <b id="pf-stock-value">¥0.00</b></span>\n',
        '                <span>当日 <b id="pf-day-pnl">¥0.00</b></span>\n',
        '              </div>\n',
        '            </div>\n',
        '          </div>\n',
        '          <!-- Trading form -->\n',
        '          <div class="ftp-section">\n',
        '            <div class="ftp-order-type">\n',
        '              <button class="ftp-type-btn active" data-type="market" onclick="switchOrderType(\'market\')">市价</button>\n',
        '              <button class="ftp-type-btn" data-type="limit" onclick="switchOrderType(\'limit\')">限价</button>\n',
        '            </div>\n',
        '            <div class="ftp-trade-row hidden" id="ftp-limit-row">\n',
        '              <span class="ftp-trade-label">价格</span>\n',
        '              <input type="number" id="trade-limit-price" min="0.01" step="0.01" placeholder="限价" autocomplete="off">\n',
        '            </div>\n',
        '            <div class="ftp-trade-row">\n',
        '              <span class="ftp-trade-label">数量</span>\n',
        '              <input type="number" id="trade-qty" min="1" value="100" step="100">\n',
        '            </div>\n',
        '            <div class="ftp-estimate" id="trade-estimate">预估: ¥0.00</div>\n',
        '            <div class="ftp-trade-btns">\n',
        '              <button class="btn btn-buy btn-sm" id="btn-buy" onclick="handleTrade(\'buy\')">买入</button>\n',
        '              <button class="btn btn-sell btn-sm" id="btn-sell" onclick="handleTrade(\'sell\')">卖出</button>\n',
        '            </div>\n',
        '            <div id="trade-msg" class="trade-msg" style="font-size:11px;min-height:16px;"></div>\n',
        '          </div>\n',
        '          <!-- Pending orders -->\n',
        '          <div class="ftp-section ftp-orders-section">\n',
        '            <div class="ftp-orders-header">\n',
        '              <span>我的委托</span>\n',
        '              <button class="btn btn-xs btn-secondary" onclick="loadMyOrders()" style="font-size:10px;padding:1px 5px;">刷新</button>\n',
        '            </div>\n',
        '            <div class="ftp-orders" id="pending-orders-content">\n',
        '              <div class="pending-orders-empty">暂无委托</div>\n',
        '            </div>\n',
        '          </div>\n',
        '        </div>\n',
        '      </div>\n',
        '\n',
    ]
    # Insert before toast
    new_lines = new_lines[:toast_idx] + ftp_html + new_lines[toast_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'Written {len(new_lines)} lines. Removed left column, added floating panel.')
