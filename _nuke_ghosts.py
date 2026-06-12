# -*- coding: utf-8 -*-
"""Remove ALL content between game-grid close and floating-trade-panel."""
path = r'D:\hl\炒股\frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the first floating-trade-panel (marker for the real one)
real_ftp = content.find('id="floating-trade-panel"')
print(f'FTP at {real_ftp}')

# Find the game-grid closing </div>
# Look backwards from FTP for the pattern:
# game-page's </div> is right before the FTP section
# Actually let's find the structure: game-page starts at a known position
# Find "Main Trading Page"
main_page = content.find('Main Trading Page')
print(f'Main page at {main_page}')

# Find where game-page div closes (</div> at the end of the page)
# The structure is:
# <div id="game-page">
#   ... grid ...
# </div>  <- closes game-page
# <!-- floating panel... -->
# <div id="floating-trade-panel">
#   ...
# </div>
# <div id="toast">

# Find the </div> that closes game-page
# Look for the pattern: a </div> that is preceded by game-grid closing
# Let me find all </div> lines between the grid end and the FTP
grid_start = content.find('class="game-grid"')
print(f'Grid class marker at {grid_start}')

# Scan backwards from FTP to find the </div> at game-page level
# Look for </div> that's just before the FTP
pre_ftp = content[max(0,real_ftp-500):real_ftp]
print(f'Content before FTP (last 200 chars):')
print(pre_ftp[-200:].encode('ascii', 'replace').decode('ascii'))

# Find the last </div> before FTP that closes game-page
# The pattern should be:
# </div> (game-grid)
# </div> (game-page)
# blank lines
# <!-- FTP comment
# <div id="floating-trade-panel">

close_markers = []
idx = 0
while True:
    idx = content.find('</div>', idx)
    if idx < 0 or idx > real_ftp:
        break
    close_markers.append(idx)
    idx += 6

print(f'\nAll </div> before FTP:')
for pos in close_markers[-10:]:
    context = content[max(0,pos-30):pos+30].replace('\n', '\\n').encode('ascii', 'replace').decode('ascii')
    print(f'  {pos}: {context}')

# The game-page close should be the last </div> before the FTP
if close_markers:
    game_page_close = close_markers[-1]
    print(f'\nGame-page close at {game_page_close}')
    print(f'After game-page close:')
    print(content[game_page_close:game_page_close+200].encode('ascii', 'replace').decode('ascii'))
    print(f'\nBefore game-page close:')
    print(content[max(0,game_page_close-100):game_page_close].encode('ascii', 'replace').decode('ascii'))

# Strategy: remove EVERYTHING between game_page_close and real_ftp
# (the ghosts are in this region)
# Then place our clean FTP HTML right after game_page_close

# But first we need to confirm what we're removing
if close_markers:
    gp_close = close_markers[-1]
    between = content[gp_close:real_ftp]
    print(f'\n=== Content to remove ({len(between)} chars) ===')
    print(between.encode('ascii', 'replace').decode('ascii')[:500])
    print('...(truncated)...')

# Ok this approach is too fragile. Let me just do it the right way:
# Find ALL ftp-section divs outside the real FTP and remove them
# plus their content (until the matching </div>)

# Find the real FTP structure boundaries
# Use a simpler method: look for the FTP ID and count divs
ftp_start = real_ftp
depth = 0
ftp_end = ftp_start
for i in range(ftp_start, len(content)):
    if content[i:i+5] == '<div ' and not content[i+5] in 'iae':  # very rough div detection
        pass
    # just find the last </div> that closes ftp
    if content[i:i+6] == '</div>':
        depth -= 1
        if depth < 0:
            ftp_end = i + 6
            break

# OK let's just do dumb removal. Find the FTP section visually.
# Real FTP starts at "id=\"floating-trade-panel\""
# FTP ENDS at the last </div> of that block
# We can find it by counting: <div id="floating-trade-panel"> +1, then each child +1, each </div> -1

# Actually let's use a more robust counting method
inner = content[ftp_start:]
div_count = 0
ftp_end = 0
for i, ch in enumerate(inner):
    if inner[i:i+5] == '<div ' and inner[i+5] != ' ' and inner[i+5] != 'i':
        continue
    if inner[i:i+4] == '<div':
        div_count += 1
    elif inner[i:i+6] == '</div>':
        div_count -= 1
        if div_count == 0:
            ftp_end = ftp_start + i + 6
            break

print(f'\nReal FTP: {ftp_start} to {ftp_end}')
print(f'Content length: {len(content)}')

# Extract only the real FTP section
real_ftp_html = content[ftp_start:ftp_end]

# Count pf-total in the real FTP
print(f'pf-total in real FTP: {real_ftp_html.count("id=\\"pf-total\\"")}')

# Build new file:
# 1. Content before game-page close
# 2. Our clean floating panel
# 3. Content after FTP end

if close_markers:
    gp_close = close_markers[-1]
    # Check if gp_close is actually the game-page closing div
    # It should be just a </div> on its own line
    before_part = content[:gp_close].rstrip() + '\n\n'
    after_part = content[ftp_end:]

    # Verify after_part starts with toast or blank lines
    print(f'\nAfter FTP end:')
    print(after_part[:200].encode('ascii', 'replace').decode('ascii'))

    new_content = before_part + '\n' + real_ftp_html + '\n\n' + after_part

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f'\nWritten {len(new_content)} chars')

    # Count pf-total
    import re
    count = len(re.findall(r'id="pf-total"', new_content))
    print(f'pf-total count: {count}')
    if count == 1:
        print('ALL CLEAN!')
    else:
        print('Still has duplicates')
        for m in re.finditer(r'id="pf-total"', new_content):
            print(f'  at {m.start()}')
