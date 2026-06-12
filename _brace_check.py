with open('D:/hl/炒股/frontend/js/ui/game.js', 'r') as f:
    lines = f.readlines()
depth = 0
for i, line in enumerate(lines, 1):
    opens = line.count('{')
    closes = line.count('}')
    old_depth = depth
    depth += opens - closes
    if i > 680:
        print("L%d: [%d->%d] %s" % (i, old_depth, depth, line.rstrip()[:80]))
print("Final depth:", depth)
