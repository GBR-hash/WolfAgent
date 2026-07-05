import sys, json, urllib.request, time
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost:8000'

# Create game as werewolf
def api(path, data=None, method='GET'):
    url = BASE + path
    if data is None:
        req = urllib.request.Request(url, method=method)
    else:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method=method)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

# Create game
g = api('/game/new', {'role': 'werewolf', 'play_style': 'balanced'}, 'POST')
gid = g['game_id']
print(f'Game: {gid}')

# Wait for interrupt
time.sleep(2)
dbg = api(f'/game/{gid}/debug')
it = dbg.get('interrupt', {}) or {}
print(f'Interrupt: {it.get("type", "none")}')

if it.get('type') == 'werewolf_discuss':
    # Kill player 1
    api(f'/game/{gid}/action', {'action': '1'}, 'POST')
    print('Killed player 1')
    time.sleep(5)

# Check for next interrupts
dbg2 = api(f'/game/{gid}/debug')
it2 = dbg2.get('interrupt', {}) or {}
st2 = dbg2.get('state', {})

print(f'Status: {dbg2.get("status")}')
print(f'Phase: {st2.get("phase")}')
print(f'Round: {st2.get("game_round")}')
print(f'Interrupt: {it2.get("type", "none")}')
print(f'_last_words: {json.dumps(st2.get("_last_words"), ensure_ascii=False)}')
print(f'kill_target: {st2.get("werewolf_kill_target")}')
print(f'heal_target: {st2.get("witch_heal_target")}')

# If speech interrupt, submit speech
if it2.get('type') == 'speech':
    api(f'/game/{gid}/action', {'action': 'test speech'}, 'POST')
    time.sleep(2)
    dbg3 = api(f'/game/{gid}/debug')
    st3 = dbg3.get('state', {})
    print(f'After speech - _last_words: {json.dumps(st3.get("_last_words"), ensure_ascii=False)}')

# Continue submitting actions until we see _last_words or finish
for round_num in range(3):
    time.sleep(2)
    dbg = api(f'/game/{gid}/debug')
    it = dbg.get('interrupt', {}) or {}
    st = dbg.get('state', {})
    lw = st.get('_last_words')
    print(f'  Check {round_num}: status={dbg.get("status")}, interrupt={it.get("type","none")}, _last_words={json.dumps(lw, ensure_ascii=False) if lw else "None"}')
    if lw:
        print(f'FOUND LAST WORDS: {lw}')
        break
    
    # Try to auto-advance
    if dbg.get('status') == 'waiting':
        it_type = it.get('type', '')
        if it_type in ('speech', 'vote', 'werewolf_discuss', 'witch_decision', 'seer_check', 'last_words', 'vote_result'):
            action = 'ok'
            if it_type == 'vote':
                action = str(it.get('valid_targets', [1])[0] if it.get('valid_targets') else '0')
            elif it_type == 'werewolf_discuss':
                action = str(it.get('valid_targets', [1])[0] if it.get('valid_targets') else '0')
            elif it_type == 'speech':
                action = 'test speech content'
            api(f'/game/{gid}/action', {'action': action}, 'POST')
            print(f'  Submitted: {it_type} -> {action}')

# Final check
dbg_final = api(f'/game/{gid}/debug')
st_final = dbg_final.get('state', {})
print(f'\nFinal _last_words: {json.dumps(st_final.get("_last_words"), ensure_ascii=False)}')
print(f'Final eliminated_roles: {st_final.get("eliminated_roles")}')
print(f'Final _night_killed_ids: {st_final.get("_night_killed_ids")}')
