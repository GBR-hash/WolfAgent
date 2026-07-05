import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("app/graph.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add import of _generate_last_words
old_import = "from app.players import (\n    werewolf_discussion_and_kill, witch_decision, seer_check_action,\n    generate_speech, generate_vote,"
new_import = "from app.players import (\n    werewolf_discussion_and_kill, witch_decision, seer_check_action,\n    generate_speech, generate_vote, _generate_last_words,"
content = content.replace(old_import, new_import)

# 2. Add node_night_last_words function before node_day_announcement
# Insert before "# ==================== 3. day_announcement ===================="
marker = "# ==================== 3. day_announcement ===================="
last_words_node = '''def node_night_last_words(state: GameState) -> dict:
    """Night 1 only: werewolf-killed player gets last words. Runs after seer, before day announcement."""
    round_num = state.get("game_round", 1)
    
    # Only round 1, only werewolf kill (not witch poison)
    if round_num != 1:
        return {"phase": "day_announcement", "game_round": round_num}
    
    kill_target = state.get("werewolf_kill_target")
    heal_target = state.get("witch_heal_target")
    
    # No kill or kill was healed: skip last words
    if kill_target is None or kill_target <= 0 or heal_target == kill_target:
        return {"phase": "day_announcement", "game_round": round_num}
    
    players = state["players"]
    human_id = state.get("human_player_id", 7)
    killed_pid = kill_target
    
    log.info("=== NODE: night_last_words (round %d, killed=%d) ===", round_num, killed_pid)
    
    last_words = ""
    if killed_pid == human_id:
        # Human player killed: interrupt for last words input
        human_choice = interrupt({
            "type": "last_words",
            "killed_player": human_id,
            "prompt": "\u4f60\u5728\u7b2c1\u665a\u88ab\u72fc\u4eba\u6740\u5bb3\u4e86\uff01\u8fd9\u662f\u4f60\u7684\u9057\u8a00\u673a\u4f1a\uff0c50\u5b57\u4ee5\u5185\u3002\u4f60\u53ef\u4ee5\u9009\u62e9\u66b4\u9732\u6216\u9690\u7792\u8eab\u4efd\u3002",
            "game_round": round_num,
        })
        last_words = human_choice.strip() if isinstance(human_choice, str) else ""
    else:
        # LLM player killed: generate last words
        try:
            last_words = _generate_last_words(killed_pid, state)
        except Exception:
            log.error("\u9057\u8a00\u751f\u6210\u5931\u8d25:\n%s", traceback.format_exc())
            last_words = ""
    
    # Truncate if too long
    if len(last_words) > 80:
        last_words = last_words[:80]
    
    # Store last words in state and game log
    glog = []
    if last_words:
        glog.append(_log_entry(state, "last_words", f"\u7b2c1\u665a\u9057\u8a00(\u73a9\u5bb6{killed_pid}): {last_words}", round=1, player_id=killed_pid))
        
        # Write to all alive player memories
        player_memories = state.get("player_memories", {})
        import copy
        alive = _players_alive(state)
        mem_entry = f"\u7b2c1\u665a\u9057\u8a00(\u73a9\u5bb6{killed_pid}): {last_words}"
        for pid in alive:
            pid_str = str(pid)
            if pid_str not in player_memories:
                player_memories[pid_str] = []
            player_memories[pid_str].append({"role": "system", "content": mem_entry})
        
        updated_mem = {}
        for k, v in player_memories.items():
            updated_mem[k] = list(v)
        
        return {
            "phase": "day_announcement",
            "game_round": round_num,
            "game_log": glog,
            "player_memories": updated_mem,
        }
    
    return {"phase": "day_announcement", "game_round": round_num}

'''

content = content.replace(marker, last_words_node + "\n" + marker)

# 3. Register node and fix edges
# Add node registration after night_seer
old_register = "    workflow.add_node('night_seer', node_night_seer)\n\n    workflow.add_node('day_announcement', node_day_announcement)"
new_register = "    workflow.add_node('night_seer', node_night_seer)\n    workflow.add_node('night_last_words', node_night_last_words)\n\n    workflow.add_node('day_announcement', node_day_announcement)"
content = content.replace(old_register, new_register)

# Change edge: night_seer -> day_announcement to night_seer -> night_last_words -> day_announcement
old_edge = "    workflow.add_edge('night_seer', 'day_announcement')"
new_edge = "    workflow.add_edge('night_seer', 'night_last_words')\n    workflow.add_edge('night_last_words', 'day_announcement')"
content = content.replace(old_edge, new_edge)

with open("app/graph.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
print("graph.py: node_night_last_words added + edges updated")