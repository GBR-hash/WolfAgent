# -*- coding: utf-8 -*-
"""WolfAgent Streamlit Frontend - Debug Panel"""
import streamlit as st
import requests, time, json
import sys
sys.stdout.reconfigure(encoding='utf-8')

API_BASE = 'http://localhost:8000'

st.set_page_config(page_title='WolfAgent', page_icon='🐺', layout='wide', initial_sidebar_state='expanded')

st.markdown("""
<style>
.phase-night{background:#1a1a2e;color:#e0e0ff;padding:10px 20px;border-radius:8px;margin:8px 0}
.phase-day{background:#2d1a00;color:#ffe0b0;padding:10px 20px;border-radius:8px;margin:8px 0}
.phase-speech{background:#1a2d1a;color:#b0ffb0;padding:10px 20px;border-radius:8px;margin:8px 0}
.phase-over{background:#1a2e1a;color:#b0ffb0;padding:10px 20px;border-radius:8px;margin:8px 0}
.announcement{background:#2a2a3e;color:#ffd700;padding:12px 18px;border-radius:8px;margin:8px 0;font-size:15px;font-weight:bold}
.round-header{background:#2a3050;padding:8px 16px;border-radius:6px;margin:12px 0 6px;font-size:16px;font-weight:bold;color:#b0c0ff}
.speech-item{padding:6px 12px;margin:2px 0;border-radius:4px;background:#252535;border-left:3px solid #4a90d9;font-size:13px}
.speech-human{border-left:3px solid #ff6b6b!important;background:#352525!important}
.vote-item{display:inline-block;padding:3px 10px;margin:2px;background:#353545;border-radius:4px;font-size:12px}
.vote-human{border:1px solid #ff6b6b!important}
.alive{color:#4caf50}.dead{color:#f44336;text-decoration:line-through}
.human-input{border:2px solid #ff6b6b;border-radius:8px;padding:15px;margin:15px 0;background:#352525}
.spinner-box{padding:20px;text-align:center;color:#888;font-size:14px}
</style>
""", unsafe_allow_html=True)

for k in ['game_id','auto_refresh','last_state','human_info','all_rounds_data']:
    if k not in st.session_state:
        st.session_state[k] = None if k != 'auto_refresh' else True
        if k == 'all_rounds_data':
            st.session_state[k] = []

def api_new_game(role='random'):
    try: r=requests.post(f'{API_BASE}/game/new',json={'role':role},timeout=60); return r.json() if r.status_code==200 else None
    except: return None
def api_get_debug(gid):
    try: r=requests.get(f'{API_BASE}/game/{gid}/debug',timeout=8); return r.json() if r.status_code==200 else None
    except: return None
def api_submit(gid,act):
    try: return requests.post(f'{API_BASE}/game/{gid}/action',json={'action':act},timeout=120).status_code==200
    except: return False

def remoji(r): return {'werewolf':'🐺','witch':'🧪','seer':'🔮','villager':'👤'}.get(r,'?')
def rcn(r): return {'werewolf':'狼人','witch':'女巫','seer':'预言家','villager':'村民'}.get(r,r)

with st.sidebar:
    st.title('🐺 WolfAgent')
    st.caption('选择身份开始游戏：')
    role_choice = st.selectbox(
        '身份',
        ['random', 'werewolf', 'witch', 'seer', 'villager'],
        format_func=lambda x: {'random':'🎲 随机','werewolf':'🐺 狼人','witch':'🧪 女巫','seer':'🔮 预言家','villager':'👤 村民'}.get(x, x),
        key='role_select'
    )
    if st.button('🔄 新游戏', use_container_width=True):
        r = api_new_game(role=st.session_state.role_select)
        if r:
            st.session_state.game_id = r['game_id']
            st.session_state.human_info = {'role':r['human_role'],'pid':7}
            st.session_state.last_state = None
            st.session_state.all_rounds_data = []
            st.rerun()
        else:
            st.error('后端未连接 (localhost:8000)')

    st.session_state.auto_refresh = st.toggle('🔧 自动刷新', value=st.session_state.auto_refresh)
    st.divider()

    if st.session_state.game_id and st.session_state.human_info:
        hr = st.session_state.human_info['role']
        st.info(f'{remoji(hr)} 你是 **{rcn(hr)}** (玩家7)')

    if st.session_state.game_id and st.session_state.last_state:
        state = st.session_state.last_state.get('state',{})
        players = state.get('players',{})
        if players:
            st.subheader('玩家状态')
            for k in sorted(players.keys(),key=int):
                p=players[k]; al=p['is_alive']; r=p.get('role','?')
                icon = '✅' if al else '💀'
                c = 'alive' if al else 'dead'
                star = ' ⭐真人' if p.get('is_human') else ''
                st.markdown(f'{icon} <span class="{c}">玩家{k}: {remoji(r)}{rcn(r)}{star}</span>', unsafe_allow_html=True)

    if st.session_state.auto_refresh and st.session_state.game_id:
        gs = st.session_state.last_state
        stat = gs.get('status','running') if gs else 'running'
        delay = 2.0 if stat == 'running' else 1.5
        time.sleep(delay)
        st.rerun()

# ==== Main ====
st.title('🐺 狼人杀 AI · 调试面板')
if not st.session_state.game_id:
    st.info('点击侧边栏 **新游戏** 开始')
    st.stop()

gs = api_get_debug(st.session_state.game_id)
if gs is None:
    st.warning('连接中...')
    time.sleep(1)
    st.rerun()

st.session_state.last_state = gs
state = gs.get('state',{})
status = gs.get('status','unknown')
is_waiting = gs.get('is_waiting',False)
interrupt = gs.get('interrupt') or {}
phase = state.get('phase','init')
rn = state.get('game_round',0)

# Phase banner
phase_label = {
    'init': ('初始化',''),
    'night': ('夜晚阶段','phase-night'),
    'day_announcement': ('白天·公告','phase-day'),
    'day_speeches': ('白天·发言','phase-speech'),
    'day_vote': ('白天·投票','phase-day'),
    'game_over': ('游戏结束','phase-over'),
}
lbl, cls = phase_label.get(phase, (phase,''))
st.markdown(f'<div class="{cls}"><h3>{lbl} | 第 {rn} 轮</h3></div>', unsafe_allow_html=True)

status_msg = {
    'waiting': '等待你输入...',
    'running': 'AI 思考中...',
    'finished': '已结束',
    'error': '错误',
}
st.caption(status_msg.get(status, status))

# God announcement
ann = state.get('god_announcement','')
if ann:
    st.markdown(f'<div class="announcement">📢 {ann}</div>', unsafe_allow_html=True)

# ==== Human Input ====
if is_waiting and interrupt:
    it = interrupt.get('type','')
    st.markdown('<div class="human-input">', unsafe_allow_html=True)

    if it == 'speech':
        st.subheader('轮到你发言：')
        st.info(f"身份: {interrupt.get('human_role','')}")
        with st.expander('之前发言', expanded=True):
            st.text(interrupt.get('previous_speeches',''))
        elim_info = interrupt.get('eliminated_info','')
        if elim_info:
            st.caption(f'已淘汰: {elim_info}')
        act = st.text_area('发言:', key='sp', height=80)
        if st.button('提交发言', type='primary', use_container_width=True):
            if act.strip():
                with st.spinner('...'):
                    api_submit(st.session_state.game_id, act)
                st.rerun()

    elif it == 'vote':
        st.subheader('请投票')
        valid = interrupt.get('valid_targets',[])
        with st.expander('全部发言', expanded=True):
            st.text(interrupt.get('speeches_summary',''))
        elim_info = interrupt.get('eliminated_info','')
        if elim_info:
            st.caption(f'已淘汰: {elim_info}')
        cols = st.columns(min(len(valid)+1,5))
        for i,t in enumerate(valid):
            with cols[i%5]:
                if st.button(f'玩家{t}', key=f'v_{t}', use_container_width=True):
                    api_submit(st.session_state.game_id, str(t))
                    st.rerun()
        with cols[min(len(valid),4)]:
            if st.button('弃权', key='va', use_container_width=True):
                api_submit(st.session_state.game_id, '弃权')
                st.rerun()

    elif it == 'werewolf_discuss':
        st.subheader('🐺 秘密频道 - 与队友讨论')
        secret_chat = interrupt.get('secret_chat', [])
        valid = interrupt.get('valid_targets', [])
        partner = interrupt.get('partner', [])
        st.info(f"队友: 玩家{partner}")

        # Show chat history
        if secret_chat:
            with st.container(height=250):
                for msg in secret_chat:
                    sender = msg.get('from', '?')
                    content = msg.get('content', '')
                    if sender == 7:
                        st.markdown(f'<div style="background:#1a3a1a;padding:6px 10px;border-radius:6px;margin:3px 0"><strong>你:</strong> {content}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="background:#2a2a3a;padding:6px 10px;border-radius:6px;margin:3px 0"><strong>队友{sender}号:</strong> {content}</div>', unsafe_allow_html=True)
        else:
            st.caption('等待队友发言...')

        # Chat input
        col1, col2 = st.columns([4, 1])
        with col1:
            import time as _time
            chat_key = f'wolf_chat_{int(_time.time()*1000)}'
            chat_msg = st.text_input('秘密消息', key=chat_key, placeholder='输入消息讨论，或直接输入数字杀人')
        with col2:
            send_key = f'wolf_send_{int(_time.time()*1000)}'
            if st.button('发送', use_container_width=True, key=send_key):
                if chat_msg.strip():
                    # If starts with chat: or doesn't look like a number, prepend chat:
                    msg = chat_msg.strip()
                    if not msg.startswith('chat:') and not msg.isdigit():
                        msg = 'chat: ' + msg
                    api_submit(st.session_state.game_id, msg)
                    st.rerun()

        st.divider()
        st.caption('选择击杀目标（或输入数字发送）：')
        cols = st.columns(min(len(valid), 5))
        for i, t in enumerate(valid):
            with cols[i % 5]:
                if st.button(f'杀{t}', key=f'k_{t}', use_container_width=True):
                    api_submit(st.session_state.game_id, str(t))
                    st.rerun()



    elif it == 'witch_decision':
        st.subheader('🧪 女巫决策')
        killed = interrupt.get('killed_target', '?')
        has_heal = interrupt.get('has_heal', False)
        has_poison = interrupt.get('has_poison', False)
        valid_poison = interrupt.get('valid_poison_targets', [])

        st.info(f'🐺 狼人今晚击杀了 **玩家{killed}**')
        st.caption(f'解药: {"✅ 可用" if has_heal else "❌ 已用"} | 毒药: {"✅ 可用" if has_poison else "❌ 已用"}')

        col1, col2, col3 = st.columns(3)
        with col1:
            if has_heal:
                if st.button(f'💚 救活玩家{killed}', key='witch_save', use_container_width=True, type='primary'):
                    api_submit(st.session_state.game_id, 'save')
                    st.rerun()
            else:
                st.button('💚 解药已用', key='witch_save_gone', disabled=True, use_container_width=True)

        with col2:
            if has_poison and valid_poison:
                poison_choice = st.selectbox('毒杀目标', valid_poison, key='witch_poison_select',
                                             format_func=lambda x: f'玩家{x}')
                if st.button(f'☠️ 毒杀玩家{poison_choice}', key='witch_poison_btn', use_container_width=True):
                    api_submit(st.session_state.game_id, f'poison {poison_choice}')
                    st.rerun()
            elif has_poison:
                st.button('☠️ 无可毒目标', key='witch_poison_none', disabled=True, use_container_width=True)
            else:
                st.button('☠️ 毒药已用', key='witch_poison_gone', disabled=True, use_container_width=True)

        with col3:
            if st.button('⏭️ 跳过（不操作）', key='witch_skip', use_container_width=True):
                api_submit(st.session_state.game_id, 'skip')
                st.rerun()

    elif it == 'seer_check':
        st.subheader('预言家查验')
        valid = interrupt.get('valid_targets',[])
        cols = st.columns(min(len(valid),5))
        for i,t in enumerate(valid):
            with cols[i%5]:
                if st.button(f'查{t}', key=f'c_{t}', use_container_width=True):
                    api_submit(st.session_state.game_id, str(t))
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ==== AI Thinking Indicator ====
if not is_waiting and status == 'running' and phase in ('night','day_announcement','day_speeches','day_vote'):
    with st.container():
        st.markdown('<div class="spinner-box">', unsafe_allow_html=True)
        with st.spinner(f'{lbl} - AI 正在计算...'):
            if phase == 'night':
                st.caption('可能需要等待 30-60 秒（狼人讨论+女巫+预言家）')
        st.markdown('</div>', unsafe_allow_html=True)

# ==== Current Round Speeches ====
speeches = state.get('speeches',[])
if speeches:
    st.subheader(f'本轮发言 ({len(speeches)}条)')
    for i, sp in enumerate(speeches):
        pid = sp.get('player_id','?')
        content = sp.get('content','')
        cls = 'speech-item speech-human' if pid == 7 else 'speech-item'
        st.markdown(f'<div class="{cls}"><strong>#{i+1} 玩家{pid}</strong>: {content}</div>', unsafe_allow_html=True)

# ==== Current Round Votes ====
votes = state.get('votes',{})
if votes and not is_waiting:
    st.subheader(f'本轮投票 ({len(votes)}票)')
    tally = {}
    voter_list = []
    for voter, target in votes.items():
        t = int(target) if target else -1
        label = '弃权' if t == -1 else f'→ 玩家{t}'
        if t != -1:
            tally[t] = tally.get(t,0) + 1
        voter_list.append((voter, label))
    for v, lb in voter_list:
        cls = 'vote-item vote-human' if v == '7' else 'vote-item'
        st.markdown(f'<span class="{cls}">玩家{v} {lb}</span>', unsafe_allow_html=True)
    if tally:
        st.markdown('**票数统计:** ' + ' | '.join(f'玩家{k}:{v}票' for k,v in sorted(tally.items(), key=lambda x:-x[1])))

# ==== Complete Round Timeline ====
game_log = state.get('game_log',[])
if game_log:
    st.subheader('完整时间线')
    rounds = {}
    for entry in game_log:
        r = entry.get('round', 0)
        if r not in rounds:
            rounds[r] = []
        rounds[r].append(entry)
    for rn_num in sorted(rounds.keys()):
        entries = rounds[rn_num]
        with st.expander(f'第 {rn_num} 轮', expanded=(rn_num == max(rounds.keys()))):
            for e in entries:
                etype = e.get('type','')
                msg = e.get('message','')
                color_map = {
                    'wolf_kill':'#ff6666','witch_save':'#66ff66','witch_poison':'#ff4466',
                    'seer_check':'#6699ff','death_night':'#ff6666','peace_night':'#88aa88',
                    'elimination':'#ffaa00','game_over':'#ffdd44','speech':'#88ccff',
                    'vote':'#aaaacc','round_start':'#888','day_start':'#888','speech_end':'#888',
                    'vote_start':'#888','tie':'#aaaacc','speech_error':'#ff4444','vote_error':'#ff4444',
                }
                c = color_map.get(etype,'#ccc')
                st.markdown(f'<span style="color:{c}">• {msg}</span>', unsafe_allow_html=True)

# ==== Game Over ====
if status == 'finished' or state.get('game_over'):
    winner = state.get('winner','')
    wcn = {'werewolf':'🐺 狼人','villager':'👤 好人'}.get(winner, winner)
    st.balloons()
    st.success(f'## {wcn}阵营获胜！')

    players_final = state.get('players',{})
    eliminated_roles = state.get('eliminated_roles',{})
    st.subheader('身份揭秘')
    for k in sorted(players_final.keys(),key=int):
        p=players_final[k]; r=p['role']; al=p['is_alive']
        icon = '✅' if al else '💀'
        star = ' ⭐真人' if p.get('is_human') else ''
        st.markdown(f'{icon} 玩家{k}: {remoji(r)} **{rcn(r)}**{star}')

    game_log_final = state.get('game_log',[])
    if game_log_final:
        st.subheader(f'游戏统计（共 {rn} 轮）')

        # Full speeches per round
        with st.expander('全部发言记录（按轮次）', expanded=True):
            speeches_by_round = {}
            for e in game_log_final:
                if e.get('type') == 'speech':
                    r = e.get('round', 0)
                    if r not in speeches_by_round:
                        speeches_by_round[r] = []
                    speeches_by_round[r].append(e)
            if speeches_by_round:
                for r_num in sorted(speeches_by_round.keys()):
                    sp_list = speeches_by_round[r_num]
                    with st.expander(f'第 {r_num} 轮 ({len(sp_list)}条发言)', expanded=(r_num == max(speeches_by_round.keys()))):
                        for sp in sp_list:
                            pid = sp.get('player_id', '?')
                            content = sp.get('message', '')
                            cls = 'speech-item speech-human' if pid == 7 else 'speech-item'
                            st.markdown(f'<div class="{cls}"><strong>玩家{pid}</strong>: {content}</div>', unsafe_allow_html=True)
            else:
                st.caption('（发言记录为空）')

        # Full votes per round
        with st.expander('全部投票记录（按轮次）', expanded=True):
            votes_by_round = {}
            for e in game_log_final:
                if e.get('type') == 'vote':
                    r = e.get('round', 0)
                    if r not in votes_by_round:
                        votes_by_round[r] = []
                    votes_by_round[r].append(e)
            if votes_by_round:
                for r_num in sorted(votes_by_round.keys()):
                    tally = {}
                    voter_list = []
                    for v_e in votes_by_round[r_num]:
                        voter = str(v_e.get('player_id', '?'))
                        target = v_e.get('target', -1)
                        if target is None: target = -1
                        lbl = '弃权' if target == -1 else f'→ 玩家{target}'
                        if target != -1: tally[target] = tally.get(target, 0) + 1
                        voter_list.append((voter, lbl))
                    st.markdown(f'**第 {r_num} 轮** ({len(votes_by_round[r_num])}票):')
                    for v, lb in voter_list:
                        st.markdown(f'<span class="vote-item">玩家{v} {lb}</span>', unsafe_allow_html=True)
                    if tally:
                        st.markdown('票数: ' + ' | '.join(f'玩家{k}:{v}票' for k,v in sorted(tally.items(), key=lambda x:-x[1])))
            else:
                st.caption('（投票记录为空）')

# ==== Night Actions ====
with st.expander('最近夜晚行动', expanded=False):
    na = [
        ('狼人目标', state.get('werewolf_kill_target')),
        ('女巫救', state.get('witch_heal_target')),
        ('女巫毒', state.get('witch_poison_target')),
        ('预言家查验', state.get('seer_check_target')),
    ]
    shown = False
    for icon, v in na:
        if v is not None:
            shown = True
            extra = ''
            if '查验' in icon:
                extra = ': %s' % state.get('seer_check_result','?')
            st.markdown('%s: **玩家%d**%s' % (icon, v, extra))
    if not shown:
        st.caption('无行动记录')

# ==== Debug ====
with st.expander('Raw State', expanded=False):
    st.json(state)
    it_val = interrupt or {}
    st.caption(f'status={status}, waiting={is_waiting}, itype={it_val.get("type","none")}, s_cur={state.get("speech_cursor","?")}, v_cur={state.get("vote_cursor","?")}')

st.divider()
st.caption('WolfAgent · LangGraph + DeepSeek')