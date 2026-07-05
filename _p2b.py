import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("app/graph.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix line 766: the \n in the string got interpreted as real newline
# Current: '            log.error("遗言生成失败:\n%s", traceback.format_exc())'
# This is split across two lines (766-767)
# Fix: merge back into one line with \\n escape
lines[765] = '            log.error("' + chr(36951) + chr(35328) + chr(29983) + chr(25104) + chr(22833) + chr(36133) + ':\\n%s", traceback.format_exc())\n'
# Remove the orphaned line 767
if lines[766].strip() == '%s", traceback.format_exc())':
    del lines[766]

with open("app/graph.py", "w", encoding="utf-8", newline="\n") as f:
    f.writelines(lines)
print("Fixed line 766")