# -*- coding: utf-8 -*-
# Read the file and replace the left column with the floating panel structure
path = r'D:\hl\炒股\frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the boundaries of the left column and the start of the center column
left_start = None
left_end = None
center_start = None
right_start = None

for i, line in enumerate(lines):
    if 'panel-stock-left' in line:
        left_start = i
    if left_start is not None and left_end is None and '</div>' in line and i > left_start + 5:
        # Check if this closes the panel-stock-left div
        # We want the closing </div> that matches panel-stock-left
        pass

# Simpler approach: find exact line numbers
for i, line in enumerate(lines):
    if '<!-- Left: Account + Holdings + Trading -->' in line:
        left_start = i
    if left_start is not None and '<!-- Center:' in line:
        left_end = i - 1  # line before center starts
        center_start = i

print(f'Left column: lines {left_start} to {left_end}')
print(f'Center starts at: {center_start}')
print(f'Total lines: {len(lines)}')

# Verify the left_end correctly closes the panel-stock-left div
if left_end:
    # Show what's being replaced
    print(f'\nFirst line to remove ({left_start}): {repr(lines[left_start].rstrip())}')
    print(f'Last line to remove ({left_end}): {repr(lines[left_end].rstrip())}')

# Now build the new content
# Keep lines 0 to left_start-1, insert new center+holdings, then keep from center_start
new_lines = lines[:left_start]

# Add our new center column header + holdings
new_lines.append('        <!-- Center: K-line Chart + Holdings inline -->\n')
# Keep the panel-center div and everything in it, but need to rewrite the center
# Actually, let's just skip the old left column and keep the center as-is

# Find the end of the right column to add the floating panel HTML after
right_section_end = None
toast_start = None
for i, line in enumerate(lines):
    if '<div id="toast" class="toast hidden">' in line:
        toast_start = i
        break

# Build new content: remove left column (left_start to left_end inclusive)
new_lines = lines[:left_start]
# Add everything from center_start onward
new_lines.extend(lines[center_start:])

# Write back
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'\nWritten {len(new_lines)} lines (removed lines {left_start}-{left_end})')
