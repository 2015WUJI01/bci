# -*- coding: utf-8 -*-
"""Remove duplicate FTP ghost copies, keep only the real one."""
path = r'D:\hl\炒股\frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the real FTP (has id="floating-trade-panel")
real_ftp = content.find('id="floating-trade-panel"')

# Find the ftp-body start and end (the 2nd nested section structure)
# The ghost copies are <div class="ftp-section"> blocks that got duplicated
# Find ghost copy #1 (at pos ~8115)
# Find ghost copy #2 (at pos ~10597)

# Strategy: find all ftp-section divs that are NOT inside the real FTP
# and REMOVE them along with their content

# Find the boundary of the real FTP
real_ftp_start = real_ftp
# Count nesting to find end
depth = 0
real_ftp_end = real_ftp_start
for i in range(real_ftp_start, len(content)):
    if content[i:i+6] == '<div ' and 'class=' in content[i:i+100]:
        depth += 1
    elif content[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            real_ftp_end = i + 6
            break

print(f'Real FTP: {real_ftp_start} to {real_ftp_end}')

# Now find all ftp-section occurrences
import re
section_count = 0
for m in re.finditer(r'<div class="ftp-section"', content):
    pos = m.start()
    in_real = real_ftp_start <= pos < real_ftp_end
    print(f'ftp-section at {pos}: {"IN-REAL" if in_real else "GHOST"}')
    section_count += 1

# Find all ftp-orders-header occurrences
for m in re.finditer(r'ftp-orders-header', content):
    pos = m.start()
    in_real = real_ftp_start <= pos < real_ftp_end
    print(f'ftp-orders-header at {pos}: {"IN-REAL" if in_real else "GHOST"}')

# Find the ghost sections and remove them
# A ghost section is ftp-section or ftp-orders-section that is OUTSIDE the real FTP
# Remove them by finding their containing div and removing it

# Strategy: find all content from the first non-ftp content to the end of the ghosts
# Look for the pattern: everything between game-grid closing and the real FTP

# Find close of game-page
game_page_close = content.find('</div>', content.find('</div>', content.find('panel-right')))
# Actually let's find </div> that closes game-page (after game-grid)
# Find game-grid close
gg_start = content.find('class="game-grid"')
gg_close = None
depth = 0
for i in range(gg_start, len(content)):
    if content[i:i+6] == '<div ':
        depth += 1
    elif content[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            gg_close = i + 6
            break

print(f'\ngame-grid from {gg_start} to {gg_close}')

# Content before real FTP
between = content[gg_close:real_ftp_start]
print(f'\nContent between game-grid and real FTP ({len(between)} chars):')
print(between[:200].encode('ascii', 'replace').decode('ascii'))
print('...')
print(between[-200:].encode('ascii', 'replace').decode('ascii'))

# Find ghost divs in the "between" section
ghost_start = between.find('ftp-section')
if ghost_start > 0:
    ghost_start_abs = gg_close + ghost_start
    print(f'\nGhost starts at {ghost_start_abs}')

    # Find the end of all ghost content
    # Look for anything that could be a repeated FTP body
    # Search for patterns

    # Remove from gg_close to real_ftp_start (all ghost content)
    new_content = content[:gg_close] + '\n' + content[real_ftp_start:]
    print(f'\nRemoved {real_ftp_start - gg_close} chars of ghost content')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    # Verify
    with open(path, 'r', encoding='utf-8') as f:
        verified = f.read()
    count = verified.count('id="pf-total"')
    print(f'pf-total count after cleanup: {count}')
else:
    print('No ghost content found between game-grid and FTP')
