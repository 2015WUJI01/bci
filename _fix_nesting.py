# -*- coding: utf-8 -*-
"""Fix holdings nesting within panel-center and remove extra div."""
path = r'D:\hl\炒股\frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find key lines
holdings_line = None
close_panel_center = None
extra_close = None

for i, line in enumerate(lines):
    if 'Holdings below chart' in line:
        holdings_line = i
    if close_panel_center is None and holdings_line and i > holdings_line and line.strip() == '</div>' and lines[i-1].strip() == '</div>':
        extra_close = i
        break

# Also find the panel-center's closing </div> (line 104)
# panel-center is: <div class="panel-center">
# Its closing is at line 104:       </div>
close_pc = None
for i in range(holdings_line-5, holdings_line):
    if lines[i].strip() == '</div>' and lines[i-1].strip() == '</div>':
        close_pc = i
        break

if holdings_line:
    print(f'Holdings at line {holdings_line}')
    print(f'Panel-center closing at line {close_pc}')
    print(f'Extra close at line {extra_close}')

    # Move holdings inside panel-center
    # Extract holdings div (lines 106-114)
    holdings_div = lines[holdings_line:extra_close]  # includes the extra </div>

    # Remove the holdings from current position and the extra </div>
    new_lines = lines[:close_pc] + holdings_div + lines[extra_close+1:]

    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f'Written {len(new_lines)} lines')
else:
    print('Holdings not found!')
