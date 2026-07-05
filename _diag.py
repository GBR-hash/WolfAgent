with open(r"D:\pycharm projects\WolfAgent\main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add diagnostic log in _build_snapshot
old_snap_end = """            speeches_history=st.get("speeches_history", {}),
            votes_history=st.get("votes_history", {}),
        )"""
new_snap_end = """            speeches_history=st.get("speeches_history", {}),
            votes_history=st.get("votes_history", {}),
        )
        sh_keys = st.get("speeches_history", {}).keys() if st.get("speeches_history") else []
        vh_keys = st.get("votes_history", {}).keys() if st.get("votes_history") else []
        if sh_keys:
            log.debug("[%s] snapshot: speeches_history rounds=%s, votes_history rounds=%s",
                     self.game_id, list(sh_keys), list(vh_keys))"""
content = content.replace(old_snap_end, new_snap_end)

# Add diagnostic log in _sync_state game_over branch
old_game_over = """            session.status = "finished"
            session._push_state()
            log.info("[%s] game over, winner=%s", session.game_id, st.get("winner"))"""
new_game_over = """            session.status = "finished"
            session._push_state()
            sh = st.get("speeches_history", {})
            vh = st.get("votes_history", {})
            log.info("[%s] game over, winner=%s, speeches_history=%s rounds, votes_history=%s rounds",
                     session.game_id, st.get("winner"),
                     len(sh) if sh else 0, len(vh) if vh else 0)"""
content = content.replace(old_game_over, new_game_over)

with open(r"D:\pycharm projects\WolfAgent\main.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Added diagnostic logs")
