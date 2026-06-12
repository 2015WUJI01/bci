# -*- coding: utf-8 -*-
import os

path = r'D:\hl\炒股\frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replacement 1: Header - add floating panel toggle button
old_header = '''      <div class="header-right">
        <span class="conn-status connected" id="conn-status"><span class="dot"></span><span id="conn-label">已连接</span></span>
        <span class="user-email" id="game-user-email" style="font-size:12px;color:var(--text-muted);"></span>
        <button class="btn btn-sm btn-secondary" onclick="handleLogout()">退出</button>
      </div>'''

new_header = '''      <div class="header-right">
        <button class="btn btn-xs btn-secondary" id="btn-toggle-ftp" onclick="toggleFloatingPanel()" title="交易面板" style="font-size:16px;padding:2px 8px;">💼</button>
        <span class="conn-status connected" id="conn-status"><span class="dot"></span><span id="conn-label">已连接</span></span>
        <span class="user-email" id="game-user-email" style="font-size:12px;color:var(--text-muted);"></span>
        <button class="btn btn-sm btn-secondary" onclick="handleLogout()">退出</button>
      </div>'''

if old_header in content:
    content = content.replace(old_header, new_header)
    print("Header updated")
else:
    print("Header NOT FOUND")

# Replacement 2: Main grid - remove left column, add floating panel after grid
old_grid = '''      <!-- Main Grid -->
      <div class="game-grid">
        <!-- Left: Account + Holdings + Trading -->
        <div class="panel-stock-left">
          <!-- Portfolio Panel -->
          <div class="panel" id="portfolio-panel">
            <div class="panel-header">我的账户</div>
            <div class="pf-body">
              <!-- Total assets hero -->
              <div class="pf-hero">
                <div class="pf-hero-row">
                  <span class="pf-hero-label">总资产</span>
                  <span class="pf-hero-value" id="pf-total">¥100,000.00</span>
                </div>
                <div class="pf-hero-row">
                  <span class="pf-hero-label">当日盈亏</span>
                  <span class="pf-hero-pnl" id="pf-day-pnl">¥0.00 (+0.00%)</span>
                </div>
              </div>
              <!-- Detail grid -->
              <div class="pf-detail-grid">
                <div class="pf-detail-item">
                  <span class="pf-detail-label">可用现金</span>
                  <span class="pf-detail-value" id="pf-cash">¥100,000.00</span>
                </div>
                <div class="pf-detail-item">
                  <span class="pf-detail-label">持仓市值</span>
                  <span class="pf-detail-value" id="pf-stock-value">¥0.00</span>
                </div>
                <div class="pf-detail-item">
                  <span class="pf-detail-label">冻结资金</span>
                  <span class="pf-detail-value" id="pf-frozen-cash">¥0.00</span>
                </div>
                <div class="pf-detail-item">
                  <span class="pf-detail-label">冻结持仓</span>
                  <span class="pf-detail-value" id="pf-frozen-qty">0股</span>
                </div>
              </div>
              <!-- Total P&L footer -->
              <div class="pf-footer">
                <span class="pf-footer-label">总盈亏</span>
                <span class="pf-footer-value" id="pf-pnl">¥0.00 (0.00%)</span>
              </div>
            </div>
          </div>

          <!-- Holdings -->
          <div class="panel" style="flex:1;min-height:0;">
            <div class="panel-header">持仓明细</div>
            <div class="holdings-table" id="holdings-table">
              <div class="holding-row holding-header">
                <span>股票</span><span>数量</span><span>均价</span><span>现价</span><span>市值</span><span>盈亏</span><span>收益率</span>
              </div>
            </div>
          </div>

          <!-- Trading Panel -->
          <div class="panel" id="trading-panel">
            <div class="panel-header">交易</div>
            <div class="trading-form">
              <div class="form-group order-type-group">
                <label>订单类型</label>
                <div class="order-type-toggle">
                  <button class="order-type-btn active" data-type="market" onclick="switchOrderType('market')">市价单</button>
                  <button class="order-type-btn" data-type="limit" onclick="switchOrderType('limit')">限价单</button>
                </div>
              </div>
              <div class="form-group limit-price-group hidden" id="limit-price-group">
                <label>限价价格</label>
                <input type="number" id="trade-limit-price" min="0.01" step="0.01" placeholder="输入限价..." autocomplete="off">
              </div>
              <div class="form-group">
                <label>数量（股）</label>
                <input type="number" id="trade-qty" min="1" value="100" step="100">
              </div>
              <div class="trade-estimate">
                预估金额：<span id="trade-estimate">¥0.00</span>
              </div>
              <div class="trade-buttons">
                <button class="btn btn-buy" id="btn-buy">买入</button>
                <button class="btn btn-sell" id="btn-sell">卖出</button>
              </div>
              <div id="trade-msg" class="trade-msg"></div>
            </div>
          </div>

          <!-- Pending Orders -->
          <div class="panel pending-orders-panel">
            <div class="panel-header">
              <span>我的委托</span>
              <button class="btn btn-xs btn-secondary" onclick="loadMyOrders()" style="font-size:10px;padding:1px 6px;">刷新</button>
            </div>
            <div class="pending-orders-content" id="pending-orders-content">
              <div class="pending-orders-empty">暂无委托</div>
            </div>
          </div>
        </div>'''

new_grid_start = '''      <!-- Main Grid (center + right, left column = floating panel) -->
      <div class="game-grid">
'''

if old_grid in content:
    content = content.replace(old_grid, new_grid_start)
    print("Grid replaced")
else:
    print("Grid NOT FOUND - checking partial matches...")
    # Debug: find partial matches
    for term in ['panel-stock-left', 'portfolio-panel', 'pending-orders-panel']:
        idx = content.find(term)
        if idx >= 0:
            print(f"  Found '{term}' at position {idx}")
            print(f"  Context: {repr(content[idx-20:idx+30])}")

# Replacement 3: Add floating panel HTML before </body>
ftp_html = '''      <!-- ============================================================
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
'''

# Insert floating panel before <div id="toast"
toast_marker = '<div id="toast" class="toast hidden">'
if toast_marker in content:
    content = content.replace(toast_marker, ftp_html + '\n  ' + toast_marker)
    print("Floating panel added")
else:
    print("Toast marker NOT FOUND")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
