# -*- coding: utf-8 -*-
"""Fix the HTML structure - holdings should be inside panel-center, fix indentation."""
path = r'D:\hl\炒股\frontend\index.html'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the problem area
for i, line in enumerate(lines):
    if '<!-- Holdings below chart -->' in line:
        print(f'Holdings line {i}: {repr(line)}')
        # Check surrounding lines
        for j in range(i-3, i+10):
            if 0 <= j < len(lines):
                print(f'  {j}: {repr(lines[j].rstrip())}')
        break
