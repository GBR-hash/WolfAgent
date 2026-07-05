import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("app/graph.py", "r", encoding="utf-8") as f:
    content = f.read()

# === Build the three replacement nodes ===

common_setup = '''def _night_common(state):
    """Shared setup for all night phase nodes."""
    if state.get('game_over', False) or state.get('phase') == 'game_over':
        return None
    round_num = state.get('game_round', 0) + 1
    players = state['players']
    human_id = state.get('human_player_id', 7)
    human_player = players[str(human_id)]
    human_role = human_player['role'] if human_player['is_alive'] else None
    alive = _players_alive(state)
    night_lines = list(state.get('_night_lines', []))
    return {
        'round_num': round_num, 'players': players,
        'human_id': human_id, 'human_role': human_role,
        'alive': alive, 'night_lines': night_lines,
    }
'''

node_werewolf = '''
def node_night_werewolf(state: GameState) -> dict:
    """Step 1: Werewolf kill decision (LLM or human)."""
    ctx = _night_common(state)
    if ctx is None:
        return {'phase': 'game_over', 'game_over': True,
                'speeches_history': state.get('speeches_history', {}),
                'votes_history': state.get('votes_history', {})}

    round_num = ctx['round_num']
    players = ctx['players']
    human_id = ctx['human_id']
    human_role = ctx['human_role']
    alive = ctx['alive']
    night_lines = ctx['night_lines']

    glog = [_log_entry(state, 'round_start', f'--- Round {round_num} 夜晚开始 ---', round=round_num)]

    result = {
        'game_round': round_num, 'votes': {}, 'speeches': [],
        'speech_cursor': 0, 'vote_cursor': 0,
        'eliminated_tonight': [], 'game_log': glog,
        'werewolf_kill_target': None,
        'witch_has_heal': state.get('witch_has_heal', True),
        'witch_has_poison': state.get('witch_has_poison', True),
        'witch_heal_target': None, 'witch_poison_target': None,
        'seer_check_target': None, 'seer_check_result': None,
        'god_announcement': '', '_night_lines': night_lines,
        'speeches_history': state.get('speeches_history', {}),
        'votes_history': state.get('votes_history', {}),
        'phase': 'night',
    }

    werewolf_ids = [int(pid) for pid, p in players.items()
                    if p['role'] == 'werewolf' and p['is_alive']]

    if not werewolf_ids:
        result['_night_lines'] = night_lines
        log.info('night_werewolf: 无存活狼人，跳过')
        return result

    valid_targets = [pid for pid in alive if pid not in werewolf_ids]
    log.info('=== NODE: night_werewolf (round %d) ===', round_num)
    log.info('Step 1: 狼人讨论与杀人 (werewolves=%s, human_role=%s)', werewolf_ids, human_role)

    if human_role == 'werewolf' and human_id in werewolf_ids:
        other_wolf = [w for w in werewolf_ids if w != human_id]
        secret_chat = list(state.get('_werewolf_secret_chat', []))

        if not secret_chat:
            for pw in other_wolf:
                try:
                    advice = _wolf_partner_suggestion(pw, state)
                    if advice:
                        secret_chat.append({'from': pw, 'content': advice})
                except Exception:
                    log.warning('狼人队友%d策略生成失败', pw)

        state['_night_lines'] = night_lines
        state['_werewolf_secret_chat'] = secret_chat

        while True:
            human_choice = interrupt({
                'type': 'werewolf_discuss', 'human_role': 'werewolf',
                'partner': other_wolf, 'valid_targets': valid_targets,
                'secret_chat': secret_chat,
                'prompt': f'狼人秘密讨论。队友:{other_wolf}。可杀:{valid_targets}。输入消息讨论，或直接输入数字杀人。',
                'game_round': round_num,
            })

            hc = human_choice.strip() if isinstance(human_choice, str) else ''

            if hc.startswith('chat:'):
                msg = hc[5:].strip()
                if msg:
                    secret_chat.append({'from': human_id, 'content': msg})
                    for pw in other_wolf:
                        try:
                            reply = _wolf_partner_suggestion(pw, state, secret_chat)
                            if reply:
                                secret_chat.append({'from': pw, 'content': reply})
                        except Exception:
                            log.warning('狼人队友%d回复失败', pw)
                    state['_night_lines'] = night_lines
                    state['_werewolf_secret_chat'] = secret_chat
                    interrupt({
                        'type': 'werewolf_discuss', 'human_role': 'werewolf',
                        'partner': other_wolf, 'valid_targets': valid_targets,
                        'secret_chat': secret_chat,
                        'prompt': f'狼人秘密讨论。队友:{other_wolf}。可杀:{valid_targets}。输入消息讨论，或直接输入数字杀人。',
                        'game_round': round_num,
                    })
                    return {}
                else:
                    secret_chat.append({'from': 'system', 'content': '无法识别，请输入数字选目标或 chat:消息 讨论'})
                    state['_night_lines'] = night_lines
                    state['_werewolf_secret_chat'] = secret_chat
                    interrupt({
                        'type': 'werewolf_discuss', 'human_role': 'werewolf',
                        'partner': other_wolf, 'valid_targets': valid_targets,
                        'secret_chat': secret_chat,
                        'prompt': f'狼人秘密讨论。队友:{other_wolf}。可杀:{valid_targets}。输入消息讨论，或直接输入数字杀人。',
                        'game_round': round_num,
                    })
                    return {}

            try:
                kt = int(hc)
                if kt in valid_targets and kt > 0:
                    result['werewolf_kill_target'] = kt
                    secret_chat.append({'from': human_id, 'content': f'[决定击杀: 玩家{kt}]'})
                    night_lines.append(f'狼人击杀: 玩家{kt}')
                    result.setdefault('game_log', []).append(
                        _log_entry(state, 'wolf_kill', f'狼人(真人)选择击杀玩家{kt}', target=kt, round=round_num))
                    log.info('狼人(真人)击杀: 玩家%d', kt)
                    break
            except ValueError:
                secret_chat.append({'from': 'system', 'content': '无法识别，请输入数字选目标或 chat:消息 讨论'})
                state['_night_lines'] = night_lines
                state['_werewolf_secret_chat'] = secret_chat
                interrupt({
                    'type': 'werewolf_discuss', 'human_role': 'werewolf',
                    'partner': other_wolf, 'valid_targets': valid_targets,
                    'secret_chat': secret_chat,
                    'prompt': f'狼人秘密讨论。队友:{other_wolf}。可杀:{valid_targets}。输入消息讨论，或直接输入数字杀人。',
                    'game_round': round_num,
                })
                return {}

        result['_werewolf_secret_chat'] = secret_chat
        result['_night_lines'] = night_lines
    else:
        try:
            secret_history = state.get('_werewolf_secret_chat', None)
            wolf_result = werewolf_discussion_and_kill(state, secret_chat_history=secret_history if secret_history else None)
            result.update(wolf_result)
            kt = wolf_result.get('werewolf_kill_target')
            if kt is not None and kt > 0:
                night_lines.append(f'狼人击杀: 玩家{kt}')
                result.setdefault('game_log', []).append(
                    _log_entry(state, 'wolf_kill', f'狼人(LLM)选择击杀玩家{kt}', target=kt, round=round_num))
                log.info('狼人(LLM)击杀: 玩家%d', kt)
        except Exception:
            log.error('狼人讨论失败:\n%s', traceback.format_exc())
            raise

    result['_night_lines'] = night_lines
    result.setdefault('game_log', [])
    return result
'''

node_witch = '''
def node_night_witch(state: GameState) -> dict:
    """Step 2: Witch decision (LLM or human)."""
    ctx = _night_common(state)
    if ctx is None:
        return {'phase': 'game_over', 'game_over': True}

    round_num = ctx['round_num']
    players = ctx['players']
    human_id = ctx['human_id']
    human_role = ctx['human_role']
    alive = ctx['alive']
    night_lines = list(state.get('_night_lines', []))

    kill_target = state.get('werewolf_kill_target')
    has_heal = state.get('witch_has_heal', True)
    has_poison = state.get('witch_has_poison', True)

    result = {
        'witch_has_heal': has_heal, 'witch_has_poison': has_poison,
        'witch_heal_target': None, 'witch_poison_target': None,
        '_night_lines': night_lines, 'phase': 'night',
    }

    witch_id = None
    for pid, p in players.items():
        if p['role'] == 'witch' and p['is_alive']:
            witch_id = int(pid)
            break

    log.info('=== NODE: night_witch (round %d) ===', round_num)

    if witch_id is None or (not has_heal and not has_poison):
        log.info('night_witch: 无女巫或无药，跳过')
        return result

    log.info('Step 2: 女巫决策 (witch=%d, has_heal=%s, has_poison=%s)', witch_id, has_heal, has_poison)

    if human_role == 'witch':
        valid_poison = [pid for pid in alive if pid != human_id]
        state['_night_lines'] = night_lines

        human_choice = interrupt({
            'type': 'witch_decision', 'human_role': 'witch',
            'killed_target': kill_target, 'has_heal': has_heal, 'has_poison': has_poison,
            'valid_poison_targets': valid_poison,
            'prompt': f'女巫决策。被狼人击杀: 玩家{kill_target}。解药:{"可用" if has_heal else "无"}。毒药:{"可用" if has_poison else "无"}。回复 save/poison N/skip',
            'game_round': round_num,
        })

        hc = human_choice.strip().lower() if isinstance(human_choice, str) else ''
        if hc.startswith('save') and has_heal:
            result['witch_heal_target'] = kill_target
            result['witch_has_heal'] = False
            night_lines.append(f'女巫救活: 玩家{kill_target}')
            result.setdefault('game_log', []).append(
                _log_entry(state, 'witch_save', f'女巫(真人)救活玩家{kill_target}', round=round_num))
            log.info('女巫(真人)救活: 玩家%d', kill_target)
        elif hc.startswith('poison') and has_poison:
            parts = hc.split()
            if len(parts) > 1:
                try:
                    pt = int(parts[1])
                    if pt in valid_poison and pt > 0:
                        result['witch_poison_target'] = pt
                        result['witch_has_poison'] = False
                        night_lines.append(f'女巫毒杀: 玩家{pt}')
                        result.setdefault('game_log', []).append(
                            _log_entry(state, 'witch_poison', f'女巫(真人)毒杀玩家{pt}', target=pt, round=round_num))
                        log.info('女巫(真人)毒杀: 玩家%d', pt)
                except ValueError:
                    pass
    else:
        try:
            witch_result = witch_decision(state)
            for k in ('witch_heal_target', 'witch_poison_target', 'witch_has_heal', 'witch_has_poison'):
                if k in witch_result:
                    result[k] = witch_result[k]
            ht = witch_result.get('witch_heal_target')
            pt = witch_result.get('witch_poison_target')
            if ht is not None and ht > 0:
                night_lines.append(f'女巫救活: 玩家{ht}')
                result.setdefault('game_log', []).append(
                    _log_entry(state, 'witch_save', f'女巫(LLM)救活玩家{ht}', round=round_num))
                log.info('女巫(LLM)救活: 玩家%d', ht)
            if pt is not None and pt > 0:
                night_lines.append(f'女巫毒杀: 玩家{pt}')
                result.setdefault('game_log', []).append(
                    _log_entry(state, 'witch_poison', f'女巫(LLM)毒杀玩家{pt}', target=pt, round=round_num))
                log.info('女巫(LLM)毒杀: 玩家%d', pt)
        except Exception:
            log.error('女巫决策失败:\n%s', traceback.format_exc())
            raise

    result['_night_lines'] = night_lines
    if 'game_log' not in result:
        result['game_log'] = []
    return result
'''

node_seer = '''
def node_night_seer(state: GameState) -> dict:
    """Step 3: Seer check (LLM or human). After completion, builds night_summary and transitions to day."""
    ctx = _night_common(state)
    if ctx is None:
        return {'phase': 'game_over', 'game_over': True}

    round_num = ctx['round_num']
    players = ctx['players']
    human_id = ctx['human_id']
    human_role = ctx['human_role']
    alive = ctx['alive']
    night_lines = list(state.get('_night_lines', []))

    result = {
        'seer_check_target': None, 'seer_check_result': None,
        '_night_lines': night_lines, 'phase': 'night',
    }

    seer_id = None
    for pid, p in players.items():
        if p['role'] == 'seer' and p['is_alive']:
            seer_id = int(pid)
            break

    log.info('=== NODE: night_seer (round %d) ===', round_num)

    if seer_id is None:
        log.info('night_seer: 无存活预言家，跳过')
        night_summary = '; '.join(night_lines) if night_lines else '平安夜，无事发生'
        result['night_summary'] = night_summary
        result['phase'] = 'day_announcement'
        result['_night_lines'] = []
        return result

    # Check if seer already completed (after seer_result interrupt)
    already_checked = state.get('_seer_checked', False)

    log.info('Step 3: 预言家查验')

    if human_role == 'seer':
        if not already_checked:
            valid_targets = [pid for pid in alive if pid != human_id]
            state['_night_lines'] = night_lines

            human_choice = interrupt({
                'type': 'seer_check', 'human_role': 'seer',
                'valid_targets': valid_targets,
                'prompt': f'预言家查验。可选: {valid_targets}。回复玩家编号。',
                'game_round': round_num,
            })

            try:
                ct = int(human_choice)
                if ct in valid_targets:
                    result['seer_check_target'] = ct
                    r = '狼人' if players[str(ct)]['role'] == 'werewolf' else '好人'
                    result['seer_check_result'] = r
                    night_lines.append(f'预言家查验: 玩家{ct} -> {r}')
                    result.setdefault('game_log', []).append(
                        _log_entry(state, 'seer_check', f'预言家(真人)查验玩家{ct}: {r}', round=round_num))
                    log.info('预言家(真人)查验玩家%d: %s', ct, r)

                    # Mark checked so next call knows to skip
                    state['_seer_checked'] = True
                    state['_night_lines'] = night_lines

                    interrupt({
                        'type': 'seer_result',
                        'checked_player': ct,
                        'check_result': r,
                        'prompt': f'查验结果：玩家{ct}是{r}',
                        'game_round': round_num,
                    })
                    return {}
            except (ValueError, TypeError):
                pass

        # Either already checked or after seer_result confirmed
        # Restore result from state
        ct = state.get('seer_check_target') if already_checked else result.get('seer_check_target')
        cr = state.get('seer_check_result') if already_checked else result.get('seer_check_result')
        if ct:
            result['seer_check_target'] = ct
        if cr:
            result['seer_check_result'] = cr
    else:
        try:
            seer_result = seer_check_action(state)
            for k in ('seer_check_target', 'seer_check_result'):
                if k in seer_result:
                    result[k] = seer_result[k]
            ct = seer_result.get('seer_check_target')
            cr = seer_result.get('seer_check_result')
            if ct is not None and ct > 0:
                night_lines.append(f'预言家查验: 玩家{ct} -> {cr}')
                result.setdefault('game_log', []).append(
                    _log_entry(state, 'seer_check', f'预言家(LLM)查验玩家{ct}: {cr}', round=round_num))
                log.info('预言家(LLM)查验玩家%d: %s', ct, cr)
        except Exception:
            log.error('预言家查验失败:\n%s', traceback.format_exc())
            raise

    night_summary = '; '.join(night_lines) if night_lines else '平安夜，无事发生'
    result['night_summary'] = night_summary
    result['phase'] = 'day_announcement'
    result['_night_lines'] = []
    result['_seer_checked'] = False  # Reset for next round

    log.info('night_seer 完成 -> day_announcement, night_summary=%s', night_summary)
    return result
'''

# === Now replace node_night_phase with the three new functions ===
# Find the bounds
old_start = content.find('def node_night_phase')
old_end = content.find('\n\n# ==================== 3. day_announcement')

if old_start >= 0 and old_end > old_start:
    replacement = common_setup + node_werewolf + node_witch + node_seer + '\n\n'
    content = content[:old_start] + replacement + content[old_end:]
    print("Replaced node_night_phase with 3 split nodes")
else:
    print("ERROR: Could not find node_night_phase boundaries")

# Update build_graph to use new nodes
old_build = """    workflow.add_node('night_phase', node_night_phase)
    workflow.add_node('day_announcement', node_day_announcement)"""

new_build = """    workflow.add_node('night_werewolf', node_night_werewolf)
    workflow.add_node('night_witch', node_night_witch)
    workflow.add_node('night_seer', node_night_seer)
    workflow.add_node('day_announcement', node_day_announcement)"""

if old_build in content:
    content = content.replace(old_build, new_build)
    print("Updated build_graph nodes")
else:
    print("ERROR: build_graph nodes pattern not found")

# Update edges
old_edge1 = "workflow.add_edge('init_game', 'night_phase')"
new_edge1 = "workflow.add_edge('init_game', 'night_werewolf')"
if old_edge1 in content:
    content = content.replace(old_edge1, new_edge1)
    print("Updated init_game edge")

old_edge2 = "workflow.add_edge('night_phase', 'day_announcement')"
new_edge2 = """workflow.add_edge('night_werewolf', 'night_witch')
    workflow.add_edge('night_witch', 'night_seer')
    workflow.add_edge('night_seer', 'day_announcement')"""
if old_edge2 in content:
    content = content.replace(old_edge2, new_edge2)
    print("Updated night phase edges")

# Update route_after_vote (night_phase -> night_werewolf)
old_edge3 = "'night_phase': 'night_phase'"
new_edge3 = "'night_werewolf': 'night_werewolf'"
if old_edge3 in content:
    content = content.replace(old_edge3, new_edge3)
    print("Updated route_after_vote")

# Update route_after_eliminate
old_edge4 = "'night_phase': 'night_phase'"
# Already replaced above if pattern matches
# Let me check specifically in route_after_eliminate
if "'night_phase': 'night_phase'" in content:
    content = content.replace("'night_phase': 'night_phase'", "'night_werewolf': 'night_werewolf'")
    print("Updated remaining night_phase references")

with open("app/graph.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done")
