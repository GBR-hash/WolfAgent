import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open(r'D:\pycharm projects\WolfAgent\app\players.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find openers list
idx = c.find('openers = [')
if idx >= 0:
    end = c.find(']', idx) + 1
    print('openers:')
    print(c[idx:end])
    print()

# Find style_hints list
idx = c.find('style_hints = [')
if idx >= 0:
    end = c.find(']', idx) + 1
    print('style_hints:')
    print(c[idx:end])