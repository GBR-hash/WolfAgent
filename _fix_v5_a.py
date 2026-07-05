# -*- coding: utf-8 -*-
PATH = r"D:\pycharm projects\WolfAgent\app\players.py"
with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace('\r\n', '\n')

# === Fix 0: _call_llm_text string guard ===
content = content.replace(
    "    if history:\n        for msg in history:\n            role = msg.get(\u0022role\u0022, \u0022user\u0022)\n            content = msg.get(\u0022content\u0022, \u0022\u0022)",
    "    if history:\n        for msg in history:\n            if isinstance(msg, str):\n                messages.append(HumanMessage(content=msg))\n                continue\n            role = msg.get(\u0022role\u0022, \u0022user\u0022)\n            content = msg.get(\u0022content\u0022, \u0022\u0022)"
)
print("Fix 0 OK")

# === Fix 1: elim_str -> elim_info_str ===
content = content.replace("{elim_str}", "{elim_info_str}")
print("Fix 1 OK")

# === Fix 2: _detect_identity_leak ===
func_def = '\n\n'
func_def += "def _detect_identity_leak(speech: str) -> bool:\n"
func_def += "    \"\"\"Check if werewolf speech contains identity-revealing meta-commentary.\"\"\"\n"
func_def += "    banned_patterns = [\n"
func_def += '        "\u6211\u662f\u72fc\u4eba", "\u4f5c\u4e3a\u72fc\u4eba",\n'
func_def += '        "\u6211\u4eec\u72fc\u4eba", "\u6211\u662f\u72fc", "\u8eab\u4e3a\u72fc\u4eba",\n'
func_def += '        "\u6211\u7684\u961f\u53cb", "\u72fc\u961f\u53cb", "\u6211\u7684\u540c\u4f34",\n'
func_def += '        "\u5e2e\u961f\u53cb", "\u914d\u5408\u961f\u53cb", "\u63a9\u62a4\u961f\u53cb",\n'
func_def += '        "\u548c\u961f\u53cb", "\u66ff\u961f\u53cb",\n'
func_def += '        "\u6211\u5fc5\u987b\u4f2a\u88c5", "\u6211\u9700\u8981\u4f2a\u88c5",\n'
func_def += '        "\u6211\u8981\u4f2a\u88c5\u6210", "\u6211\u4f1a\u5047\u88c5",\n'
func_def += '        "\u6211\u4e0d\u80fd\u516c\u5f00\u8bf4", "\u4e0d\u80fd\u8bf4\u51fa\u6765",\n'
func_def += '        "\u4e0d\u80fd\u5728\u516c\u5f00\u573a\u5408",\n'
func_def += '        "\u8fd9\u662f\u5185\u90e8\u4fe1\u606f", "\u6211\u79c1\u4e0b\u77e5\u9053",\n'
func_def += '        "\u6211\u6697\u4e2d",\n'
func_def += '        "\u6536\u5230\u6307\u4ee4", "\u6309\u7167\u6307\u4ee4",\n'
func_def += '        "\uff08\u6211\u662f\u72fc", "\uff08\u4f5c\u4e3a\u72fc",\n'
func_def += '        "\uff08\u867d\u7136\u6211\u662f\u72fc",\n'
func_def += "    ]\n"
func_def += "    for pattern in banned_patterns:\n"
func_def += "        if pattern in speech:\n"
func_def += "            return True\n"
func_def += '    if re.search(r"\uff08[^\uff09]{0,30}\u72fc\u4eba[^\uff09]{0,30}\uff09", speech):\n'
func_def += "        return True\n"
func_def += "    return False\n"

gen_pos = content.find("def generate_speech(")
content = content[:gen_pos] + func_def + "\n" + content[gen_pos:]
print("Fix 2 OK")

# === Fix 3: leak check in generate_speech ===
old_block = '    speech = _call_llm_text(prompt, llm_prompt, temperature=0.9, history=history)\n    _add_to_memory(state, player_id, [{"role": "assistant", "content": speech}])\n    return speech or "????"'

rw = (
    "\\n\\n\u3010\u7cfb\u7edf\u68c0\u6d4b\u5230\u4f60\u7684\u53d1\u8a00\u4e2d\u5305\u542b\u4e86\u66b4\u9732\u72fc\u4eba\u8eab\u4efd\u7684\u5143\u8bdd\u6216\u5185\u5fc3\u72ec\u767d\uff01\u3011"
    "\u8bf7\u5b8c\u5168\u91cd\u65b0\u751f\u6210\u53d1\u8a00\u3002\u8bb0\u4f4f\uff1a\u4f60\u751f\u6210\u7684\u6240\u6709\u6587\u5b57\u90fd\u4f1a\u88ab\u5176\u4ed6\u73a9\u5bb6\u770b\u5230\uff01"
    "\u7981\u6b62\u7528\u62ec\u53f7\u5199\u5185\u5fc3\u72ec\u767d\uff01\u7981\u6b62\u6697\u793a\u4f60\u6709\u9690\u85cf\u8eab\u4efd\uff01"
    "\u4f60\u7684\u53d1\u8a00\u5fc5\u987b\u50cf\u4e00\u4e2a\u771f\u6b63\u7684\u666e\u901a\u6751\u6c11\uff0c\u4e0d\u8981\u6709\u4e00\u4e1d\u7834\u7efd\uff01"
)
fw = (
    "\\n\\n\u3010\u4e25\u91cd\u8b66\u544a\uff01\u4f60\u4e0a\u4e00\u6b21\u53d1\u8a00\u53c8\u66b4\u9732\u4e86\u8eab\u4efd\uff01\u8fd9\u662f\u6700\u540e\u673a\u4f1a\uff01\u3011"
    "\u7981\u6b62\u5728\u53d1\u8a00\u4e2d\u51fa\u73b0\u72fc\u4eba\u4e8c\u5b57\uff01\u7981\u6b62\u62ec\u53f7\u5185\u5bb9\uff01\u7981\u6b62\u8bf4\u6211\u5047\u88c5\u3001\u6211\u4f2a\u88c5\uff01"
    "\u5c31\u5f53\u81ea\u5df1\u771f\u7684\u662f\u4e2a\u666e\u901a\u6751\u6c11\uff0c\u5b8c\u5168\u5fd8\u8bb0\u81ea\u5df1\u662f\u72fc\u4eba\u8fd9\u4ef6\u4e8b\uff0c\u76f4\u63a5\u8bf4\u51fa\u6751\u6c11\u4f1a\u8bf4\u7684\u8bdd\uff01"
)

new_block = f'    speech = _call_llm_text(prompt, llm_prompt, temperature=0.9, history=history)\n\n    # Identity leak check for werewolf players\n    if role == "werewolf" and _detect_identity_leak(speech):\n        plog.warning("Player %d (werewolf) speech leaked identity, regenerating", player_id)\n        retry_prompt = prompt + ("{rw}")\n        speech = _call_llm_text(retry_prompt, llm_prompt, temperature=0.7, history=history)\n        if _detect_identity_leak(speech):\n            plog.warning("Player %d (werewolf) speech still leaking, final retry", player_id)\n            final_prompt = prompt + ("{fw}")\n            speech = _call_llm_text(final_prompt, llm_prompt, temperature=0.5, history=history)\n\n    _add_to_memory(state, player_id, {{"role": "assistant", "content": speech}})\n    return speech or "????"'

content = content.replace(old_block, new_block)
print("Fix 3 OK")

# === Fix 4: witch info ===
gen_start = content.find("def generate_speech(")
gen_end = content.find("\ndef generate_vote", gen_start)
target = "    prompt = _build_role_prompt(player, state, extra)"
target_pos = content.find(target, gen_start, gen_end)

if target_pos > 0:
    witch_code = (
        '    # Add witch-specific night info to speech context\n'
        '    if role == "witch":\n'
        '        kill_target = state.get("werewolf_kill_target")\n'
        '        heal_target = state.get("witch_heal_target")\n'
        '        poison_target = state.get("witch_poison_target")\n'
        '        has_heal = state.get("witch_has_heal", True)\n'
        '        has_poison = state.get("witch_has_poison", True)\n'
        '        \n'
        '        witch_lines = []\n'
        '        witch_lines.append("\\n\\n\u3010\u4f60\u662f\u5973\u5deb\uff0c\u62e5\u6709\u7279\u6b8a\u4fe1\u606f\u3011")\n'
        '        if kill_target is not None:\n'
        '            witch_lines.append(f"\u6628\u665a\u72fc\u4eba\u7684\u523a\u6740\u76ee\u6807\uff1a\u73a9\u5bb6{kill_target}")\n'
        '        if heal_target is not None:\n'
        '            witch_lines.append(f"\u4f60\u4f7f\u7528\u89e3\u836f\u6551\u6d3b\u4e86\u73a9\u5bb6{heal_target}")\n'
        '        if poison_target is not None:\n'
        '            witch_lines.append(f"\u4f60\u4f7f\u7528\u6bd2\u836f\u6bd2\u6740\u4e86\u73a9\u5bb6{poison_target}")\n'
        '        if heal_target is None and poison_target is None:\n'
        '            witch_lines.append("\u4f60\u6ca1\u6709\u4f7f\u7528\u4efb\u4f55\u836f\u54c1")\n'
        '        h = "\u5df2\u7528" if not has_heal else "\u53ef\u7528"\n'
        '        p = "\u5df2\u7528" if not has_poison else "\u53ef\u7528"\n'
        '        witch_lines.append(f"\u89e3\u836f\u72b6\u6001\uff1a{h} | \u6bd2\u836f\u72b6\u6001\uff1a{p}")\n'
        '        witch_lines.append("\\n\u53d1\u8a00\u65f6\u4f60\u5fc5\u987b\u516c\u5f00\u8bf4\u660e\uff1a")\n'
        '        witch_lines.append("1. \u6628\u665a\u72fc\u4eba\u7684\u523a\u6740\u76ee\u6807\u662f\u8c01")\n'
        '        witch_lines.append("2. \u4f60\u662f\u5426\u4f7f\u7528\u4e86\u89e3\u836f/\u6bd2\u836f\uff0c\u7528\u4e86\u5c31\u660e\u786e\u8bf4\u51fa\u7528\u5728\u8c01\u8eab\u4e0a")\n'
        '        witch_lines.append("3. \u5982\u679c\u4f60\u6551\u4e86\u4eba\uff0c\u8bf4\u51fa\u6551\u4e86\u8c01\uff1b\u5982\u679c\u6bd2\u4e86\u4eba\uff0c\u8bf4\u51fa\u6bd2\u4e86\u8c01")\n'
        '        witch_lines.append("4. \u5982\u679c\u4f60\u4ec0\u4e48\u90fd\u6ca1\u505a\uff0c\u8bf4\u660e\u4e3a\u4ec0\u4e48\u4e0d\u7528\u836f")\n'
        '        \n'
        '        extra += "".join(witch_lines)\n'
    )
    content = content[:target_pos] + witch_code + '\n' + content[target_pos:]
    print("Fix 4 OK")
else:
    print("Fix 4 FAIL")

print("Fixes 0-4 complete, now fixing wolf secret chat...")