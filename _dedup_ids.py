# -*- coding: utf-8 -*-
"""Remove duplicate pf-* IDs from old portfolio panel remnants."""
import re
path = r'D:\hl\炒股\frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all pf-total occurrences and determine which are in the floating panel
# The floating panel one is the one we want to keep
# Find the floating panel section
ftp_pos = content.find('id="floating-trade-panel"')

# Find all lines with id="pf-total"
lines = content.split('\n')
new_lines = []
in_old_portfolio = False
changes = 0

for i, line in enumerate(lines):
    # Check if this is an old portfolio panel (not the floating panel one)
    if 'portfolio-panel' in line and 'floating' not in content[max(0, i-20):i+len(line)]:
        # Skip lines until we're past the old portfolio panel
        in_old_portfolio = True
        changes += 1
        print(f'Skipping old portfolio panel line {i}: {line.strip()[:60]}')
        continue

    if in_old_portfolio:
        # Skip lines until we hit a </div> that closes the panel
        if line.strip() == '</div>':
            in_old_portfolio = False
            print(f'Stopped skipping at line {i}')
            continue
        changes += 1
        print(f'Skipping line {i}: {line.strip()[:60]}')
        continue

    new_lines.append(line)

if changes:
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines('\n'.join(new_lines))
    print(f'Removed {changes} lines of old portfolio panel')
else:
    print('No old portfolio panel found')

# Count remaining pf-total
count = content.count('id="pf-total"')
print(f'pf-total count before: {count}')

with open(path, 'r', encoding='utf-8') as f:
    after_content = f.read()
count_after = after_content.count('id="pf-total"')
print(f'pf-total count after: {count_after}')
