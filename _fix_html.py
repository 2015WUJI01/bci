# -*- coding: utf-8 -*-
"""Clean up index.html: remove duplicate floating panels, add holdings below chart."""
path = r'D:\hl\炒股\frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove ALL floating panel sections (there are 2 duplicates)
while 'Floating Trading Panel (draggable)' in content:
    start = content.find('<!-- =========')
    end = content.find('</div>', content.find('floating-trade-panel'))
    if start < 0 or end < 0:
        break
    # Find the closing of the ftp div
    ftp_close = content.find('</div>', content.find('floating-trade-panel'))
    # Find the NEXT </div> after ftp_close (closes ftp div)
    next_close = content.find('</div>', ftp_close + 6)
    # Remove from start to after the second </div>
    end_of_section = next_close + 6
    content = content[:start] + content[end_of_section:]
    print(f'Removed one floating panel, remaining length: {len(content)}')

# Now add the holdings panel below the chart
# Find the </div> that closes kline-panel's parent div
# We need to insert holdings between panel-center's kline-panel and the right column
marker = '      <!-- Right: Order Book + Tape + Tabbed -->'
holdings_html = '''          <!-- Holdings below chart -->
          <div class="panel">
            <div class="panel-header">持仓明细</div>
            <div class="holdings-table" id="holdings-table">
              <div class="holding-row holding-header">
                <span>股票</span><span>数量</span><span>均价</span><span>现价</span><span>市值</span><span>盈亏</span><span>收益率</span>
              </div>
            </div>
          </div>
        </div>

      ''' + marker

# Replace the marker with the holdings + marker
content = content.replace(marker, holdings_html)
print(f'Added holdings panel')

# Check for duplicate pf-* IDs - remove old portfolio panel content if any
# (The pf-total etc. IDs are now in the floating panel, any old ones in the left-column should be gone)

# Fix the floating panel placement: it should be BEFORE <div id="toast">
# Remove it from its current position and place it right
toast_marker = '<div id="toast" class="toast hidden">'

# Find the last ftp reference and make sure it's placed properly
# Check if ftp is before toast
ftp_start = content.find('id="floating-trade-panel"')
toast_pos = content.find(toast_marker)

if ftp_start > 0 and toast_pos > 0:
    # Find where the ftp div ends
    ftp_end = content.find('</div>', content.find('</div>', ftp_start) + 6) + 6
    ftp_section = content[ftp_start:ftp_end]

    if ftp_start > toast_pos:
        # Move it before toast
        content = content[:ftp_start] + content[ftp_end:]
        # Recalculate
        toast_pos = content.find(toast_marker)
        content = content[:toast_pos] + '\n' + ftp_section + '\n' + content[toast_pos:]
        print('Moved floating panel before toast')
    else:
        print('Floating panel already before toast')

# Also make sure the indentation of the floating panel is consistent (6 spaces = game-page level)
# Remove old portfolio panel if it still exists (with pf-* classes)
old_pf_block = content.find('id="portfolio-panel"')
if old_pf_block > 0 and old_pf_block < 500:  # near the top of file
    # This is the old portfolio panel that got left behind
    print(f'WARNING: Old portfolio panel still found at position {old_pf_block}')
    # Show context
    print(content[old_pf_block-50:old_pf_block+50])

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Final file length: {len(content)} chars')
print('Done!')
