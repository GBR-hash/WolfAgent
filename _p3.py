import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("app/prompts.py", "r", encoding="utf-8") as f:
    content = f.read()

# Game rules block to append before {strategy_section} in all prompts
game_rules = """

【游戏规则速查】
- 7人局：2狼人、1女巫(1瓶解药+1瓶毒药，各仅1次)、1预言家(每晚验1人)、3村民
- 流程：夜晚→白天发言→投票淘汰→循环
- 第1晚被狼人杀害的玩家有遗言(50字)，其余夜晚和投票淘汰均无遗言
- 女巫同晚不能既用解药又用毒药
"""

# Villager-specific extra rules (villagers need to know about witch abilities)
villager_extra = """
- 女巫拥有1瓶解药(可救人)和1瓶毒药(可杀人)，各仅能使用1次
"""

# Replace pattern: {strategy_section} -> {game_rules}\n{strategy_section}
# For villager, also add extra rules
old = "{strategy_section}"
new = "{" + "game_rules" + "}" + game_rules + "\n{" + "strategy_section" + "}"
# Oops, this will replace ALL occurrences. Let me do it more carefully.

# Actually, the format uses .format() with named placeholders. I need to add
# game_rules as a placeholder in the template strings, not in the .format() call.
# The templates are like: "... {strategy_section}"""
# I need: "... {game_rules}\n{strategy_section}"""
# And then update .format() calls to include game_rules=...

# This is getting complex. Let me take a different approach:
# Just insert the rules text directly before {strategy_section} in each prompt template,
# without making it a format parameter.

# Find all occurrences of '{strategy_section}"""' (end of each prompt)
rules_text = "\n" + game_rules.strip() + "\n"
old_end = "{strategy_section}" + chr(34) + chr(34) + chr(34)
new_end = rules_text + "{" + "strategy_section" + "}" + chr(34) + chr(34) + chr(34)

count = content.count(old_end)
print(f"Template endings found: {count}")
content = content.replace(old_end, new_end)

# Now for villager, add extra rules before the game_rules
# Find VILLAGER_SYSTEM_PROMPT and add villager-specific rules
villager_marker = "3村民"
villager_rules = "3村民" + villager_extra
# Only replace the first occurrence in VILLAGER_SYSTEM_PROMPT context
# Find the VILLAGER section
v_start = content.find("VILLAGER_SYSTEM_PROMPT")
if v_start > 0:
    # Find "3村民" within the VILLAGER prompt
    v_end_search = content.find("3村民", v_start)
    if v_end_search > 0:
        content = content[:v_end_search] + villager_rules + content[v_end_search + 3:]

with open("app/prompts.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
print("prompts.py: game rules added")