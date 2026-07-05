PATH = r"D:\pycharm projects\WolfAgent\app\players.py"

# 1. Compile
compile(open(PATH, encoding='utf-8').read(), 'players.py', 'exec')
print("1. Compile OK")

with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 2. Leak detection present and called
import re
matches = list(re.finditer(r"_detect_identity_leak", content))
print(f"2. _detect_identity_leak occurrences: {len(matches)}")
for m in matches:
    line_start = content.rfind('\n', 0, m.start()) + 1
    line_end = content.find('\n', m.end())
    line = content[line_start:line_end]
    print(f"   {line.strip()[:100]}")

# 3. Witch info present in generate_speech
gen_start = content.find("def generate_speech(")
witch_in_gen = content.find("\u4f60\u662f\u5973\u5deb", gen_start)
print(f"3. Witch info in generate_speech: {witch_in_gen > 0}")

# 4. Test leak detection function
import re as _re
exec_start = content.find("def _detect_identity_leak")
exec_end = content.find("\ndef generate_speech", exec_start)
exec(content[exec_start:exec_end])

leaked = "我是5号玩家。作为狼人，我需要判断。我的狼队友玩家3。"
good = "我是5号玩家。现在局势很有趣。玩家6跳了女巫但发言有矛盾。我建议投票给玩家6。"
print(f"4a. Leaked speech detected: {_detect_identity_leak(leaked)}")
print(f"4b. Good speech clean: {_detect_identity_leak(good)}")

# 5. Encoding check
with open(PATH, "rb") as f:
    raw = f.read()
print(f"5. Multi-byte: {any(b > 0x7f for b in raw)}, Size: {len(raw)}, CRLF: {b'\r\n' in raw}")