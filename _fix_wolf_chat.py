PATH = r"D:\pycharm projects\WolfAgent\app\players.py"
with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('\r\n', '\n')

# Build the day context string to insert
# This goes after elim_info and before the rules, in both branches
day_ctx = '''\n\u767d\u5929\u516c\u5f00\u4fe1\u606f\uff1a
\u53d1\u8a00\u8bb0\u5f55\uff1a
{day_speeches}
\u6295\u7968\u8bb0\u5f55\uff1a
{day_votes}

'''

# Insertion point 1: chat_history branch, after elim_info
# Find: 已淘汰的玩家: {elim_info}\n\n{chat_context}
old1 = '\u5df2\u6dd8\u6c70\u7684\u73a9\u5bb6: {elim_info}\n\n{chat_context}\n\u89c4\u5219\u63d0\u9192\uff1a'
new1 = '\u5df2\u6dd8\u6c70\u7684\u73a9\u5bb6: {elim_info}\n\n' + day_ctx + '{chat_context}\n\u89c4\u5219\u63d0\u9192\uff1a'
content = content.replace(old1, new1)
print("Branch 1 (chat_history):", "OK" if old1 not in content else "failed?")

# Insertion point 2: non-chat_history branch, after elim_info
old2 = '\u5df2\u6dd8\u6c70\u7684\u73a9\u5bb6: {elim_info}\n\n\u8bf7\u5c31\u4eca\u665a\u6740\u8c01\u7ed9\u51fa\u4f60\u7684\u7b56\u7565\u5efa\u8bae\u3002\n\u89c4\u5219\u63d0\u9192\uff1a'
new2 = '\u5df2\u6dd8\u6c70\u7684\u73a9\u5bb6: {elim_info}\n\n' + day_ctx + '\u8bf7\u5c31\u4eca\u665a\u6740\u8c01\u7ed9\u51fa\u4f60\u7684\u7b56\u7565\u5efa\u8bae\u3002\n\u89c4\u5219\u63d0\u9192\uff1a'
content = content.replace(old2, new2)
print("Branch 2 (no chat):", "OK" if old2 not in content else "failed?")

# Now update the function to compute day_speeches and day_votes before the branches
# Find the function start and add the day context computation right before the first branch
# Find: "if chat_history:" which is the first branch decision
# Insert before it: the computation of day_speeches and day_votes

fn_start = content.find("def _wolf_partner_suggestion")
branch_start = content.find("    if chat_history:", fn_start)

# Build the day context computation code
comp_code = '''    # Build day public context for informed decisions
    speeches = state.get("speeches", [])
    votes = state.get("votes", {})
    if speeches:
        day_lines = []
        for sp in speeches:
            day_lines.append(f"\u73a9\u5bb6{sp.get('player_id','?')}\uff1a{sp.get('content','')[:200]}")
        day_speeches = "\n".join(day_lines)
    else:
        day_speeches = "\uff08\u6682\u65e0\u53d1\u8a00\uff09"
    if votes:
        vote_lines = []
        for voter, target in votes.items():
            tgt_str = f"\u73a9\u5bb6{target}" if target and int(target) > 0 else "\u5f03\u6743"
            vote_lines.append(f"\u73a9\u5bb6{voter}\u2192{tgt_str}")
        day_votes = "; ".join(vote_lines)
    else:
        day_votes = "\uff08\u6682\u65e0\u6295\u7968\uff09"
    
'''

# Insert before "    if chat_history:" 
content = content[:branch_start] + comp_code + '\n' + content[branch_start:]

with open(PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

# Verify compile
compile(content, 'players.py', 'exec')
print("Compile OK")
print("All changes applied")