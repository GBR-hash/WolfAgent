target = r"D:\pycharm projects\WolfAgent\app\graph.py"
with open(target, "r", encoding="utf-8") as f:
    content = f.read()

# Search for any code that sets _night_killed_ids to empty
import re
for m in re.finditer(r'_night_killed_ids', content):
    pos = m.start()
    line_start = content.rfind('\n', 0, pos) + 1
    line_end = content.find('\n', pos)
    line_num = content[:pos].count('\n') + 1
    line = content[line_start:line_end]
    print(f"L{line_num}: {line.strip()}")
