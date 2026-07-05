# Player interaction logic for Werewolf Agent
# Each LLM player maintains independent memory and uses LLM for all decisions

from typing import Any
from collections import Counter
import re, time, logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from app.config import get_llm
from app.tools import (
    WEREWOLF_TOOLS, WITCH_TOOLS, SEER_TOOLS, kill_player, save_player, poison_player, check_player,
)
from app.prompts import (
    GAME_RULES_COMMON,
    WEREWOLF_SYSTEM_PROMPT, WEREWOLF_SECRET_CHAT_PROMPT,
    WITCH_SYSTEM_PROMPT, SEER_SYSTEM_PROMPT, VILLAGER_SYSTEM_PROMPT,
    WEREWOLF_STRATEGY, SEER_STRATEGY, WITCH_STRATEGY, VILLAGER_STRATEGY,
)

plog = logging.getLogger('wolfagent.players')


def _get_role_name(role: str) -> str:
    names = {
        "werewolf": "狼人",
        "villager": "村民",
        "seer": "预言家",
        "witch": "女巫",
    }
    return names.get(role, role)


def _get_player_memory(state: dict, player_id: int) -> list[dict]:
    """Get the message memory for a specific player."""
    memories = state.get("player_memories", {})
    pid = str(player_id)
    if pid not in memories:
        memories[pid] = []
    return memories[pid]


def _add_to_memory(state: dict, player_id: int, messages: list[dict]):
    """Add messages to a player's memory."""
    if "player_memories" not in state:
        state["player_memories"] = {}
    pid = str(player_id)
    if pid not in state["player_memories"]:
        state["player_memories"][pid] = []
    state["player_memories"][pid].extend(messages)


def _build_role_prompt(player: dict, state: dict, extra_context: str = "", is_public_speech: bool = False, is_secret_chat: bool = False) -> str:
    """Build the system prompt for a player based on their role and game state."""
    role = player["role"]
    player_id = player["player_id"]
    alive_ids = state.get("alive_player_ids", [])
    alive_str = ", ".join(str(p) for p in alive_ids)
    play_style = state.get("play_style", "balanced")

    eliminated_roles = state.get("eliminated_roles", {})
    night_killed = set(state.get("_night_killed_ids", []))
    eliminated_roles = {k: v for k, v in eliminated_roles.items() if int(k) not in night_killed}
    role_parts = [f"玩家{k}({_get_role_name(v)})" for k, v in eliminated_roles.items()]
    night_parts = [f"玩家{pid}(身份未知)" for pid in night_killed]
    eliminated_info = ", ".join(role_parts + night_parts) if (role_parts or night_parts) else "无"
    import logging; logging.getLogger("wolfagent").warning("TRACE build_role_prompt player=%s role=%s night_killed=%s eliminated_roles=%s eliminated_info=%s", player_id, role, night_killed, eliminated_roles, eliminated_info)

    if role == "werewolf":
        other_wolf_id = None
        for pkey, pdata in state["players"].items():
            if int(pkey) != player_id and pdata["role"] == "werewolf":
                other_wolf_id = pkey
                break
        if is_secret_chat:
            prompt = WEREWOLF_SECRET_CHAT_PROMPT.format(
                player_id=player_id,
                alive_players=alive_str,
                eliminated_info=eliminated_info,
                extra_context=extra_context,
                GAME_RULES_COMMON=GAME_RULES_COMMON,
            )
        else:
            prompt = WEREWOLF_SYSTEM_PROMPT.format(
                wolf_partner_id=other_wolf_id,
                alive_players=alive_str,
                eliminated_info=eliminated_info,
                extra_context=extra_context + f'\n\n重要提醒：你是玩家{player_id}号，编号是{player_id}。发言时请用"我是{player_id}号玩家"来标识自己。',
                strategy_section=WEREWOLF_STRATEGY.get(play_style, WEREWOLF_STRATEGY["balanced"]),
            GAME_RULES_COMMON=GAME_RULES_COMMON,
            )
    elif role == "witch":
        heal_status = "可用" if state.get("witch_has_heal", True) else "已用"
        poison_status = "可用" if state.get("witch_has_poison", True) else "已用"
        killed = state.get("werewolf_kill_target")
        killed_str = f"玩家{killed}" if killed is not None else "无人"
        # Build action history for prompt injection
        if state.get("_witch_action_history"):
            action_hist = state["_witch_action_history"]
            action_lines = []
            for r in sorted(action_hist.keys()):
                entry = action_hist[r]
                parts = []
                if entry.get("heal"):
                    parts.append(f"救活玩家{entry["heal"]}")
                if entry.get("poison"):
                    parts.append(f"毒杀玩家{entry["poison"]}")
                action_lines.append(f"第{r}晚：{",".join(parts)}")
            witch_action_context = "\n你的用药历史：\n" + "\n".join(action_lines)
        else:
            witch_action_context = ""
        prompt = WITCH_SYSTEM_PROMPT.format(
            alive_players=alive_str,
            heal_status=heal_status,
            poison_status=poison_status,
            killed_player=killed_str,
            eliminated_info=eliminated_info,
            extra_context=extra_context + witch_action_context + f'\n\n重要提醒：你是玩家{player_id}号，编号是{player_id}。发言时请用"我是{player_id}号玩家"来标识自己。',
            strategy_section=WITCH_STRATEGY.get(play_style, WITCH_STRATEGY["balanced"]),
            GAME_RULES_COMMON=GAME_RULES_COMMON,
        )
    elif role == "seer":
        # Build check history for prompt injection
        if state.get("_seer_check_history"):
            check_hist = state["_seer_check_history"]
            check_lines = []
            for r in sorted(check_hist.keys()):
                entry = check_hist[r]
                tgt = entry["target"]
                res = entry["result"]
                check_lines.append(f"第{r}晚：查验玩家{tgt} → {res}")
            seer_check_context = "\n你的查验历史：\n" + "\n".join(check_lines)
        else:
            seer_check_context = ""
        prompt = SEER_SYSTEM_PROMPT.format(
            alive_players=alive_str,
            eliminated_info=eliminated_info,
            extra_context=extra_context + seer_check_context + f'\n\n重要提醒：你是玩家{player_id}号，编号是{player_id}。发言时请用"我是{player_id}号玩家"来标识自己。',
            strategy_section=SEER_STRATEGY.get(play_style, SEER_STRATEGY["balanced"]),
            GAME_RULES_COMMON=GAME_RULES_COMMON,
        )
    else:  # villager
        prompt = VILLAGER_SYSTEM_PROMPT.format(
            alive_players=alive_str,
            eliminated_info=eliminated_info,
            extra_context=extra_context + f'\n\n重要提醒：你是玩家{player_id}号，编号是{player_id}。发言时请用"我是{player_id}号玩家"来标识自己。',
            strategy_section=VILLAGER_STRATEGY.get(play_style, VILLAGER_STRATEGY["balanced"]),
            GAME_RULES_COMMON=GAME_RULES_COMMON,
        )
    return prompt


INFO_PRIORITY_SYSTEM = """
【线索优先级体系 —— 始终按此权重判断】
优先级1（铁证，直接锁定）：淘汰玩家身份暴露后与存活玩家声称冲突 → 必为狼人
优先级2（强证据）：预言家查验结果 → "X号是狼人"直接采信
优先级3（中等证据）：投票模式（票型）→ 谁保护了谁、谁冲票了谁
优先级4（弱证据）：发言矛盾、语气可疑、行为反常
优先级5（参考）：直觉、感觉、"此人不像好人"

重要：高优先级证据可以直接覆盖低优先级判断。
例如：即使某玩家发言"像个好人"，如果他被预言家验出是狼人，就必须投他。
"""


def _call_llm_with_tools(
    system_prompt: str,
    user_prompt: str,
    tools: list,
    temperature: float = 0.7,
) -> dict[str, Any]:
    """Call LLM with tools bound. Returns dict with "content" and "tool_calls" keys."""
    llm = get_llm(temperature=temperature)
    llm_with_tools = llm.bind_tools(tools)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm_with_tools.invoke(messages)

    result: dict[str, Any] = {"content": response.content or ""}
    if hasattr(response, "tool_calls") and response.tool_calls:
        result["tool_calls"] = response.tool_calls
    return result


def _call_llm_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    history: list[dict] | None = None,
) -> str:
    """Call LLM for text generation. Returns text content."""
    llm = get_llm(temperature=temperature)
    messages = [SystemMessage(content=system_prompt)]

    if history:
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "assistant" or role == "ai":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))

    messages.append(HumanMessage(content=user_prompt))
    response = llm.invoke(messages)
    return response.content or ""


# ========== Night Phase Functions ==========

def werewolf_discussion_and_kill(state: dict, secret_chat_history: list = None) -> dict:
    """Werewolves secretly discuss and decide who to kill.
    If secret_chat_history is provided, includes it in the LLM context."""
    players = state["players"]
    werewolf_ids = [int(pid) for pid, pdata in players.items()
                    if pdata["role"] == "werewolf" and pdata["is_alive"]]

    if len(werewolf_ids) == 0:
        return {"werewolf_kill_target": None}

    alive_ids = state.get("alive_player_ids", [])
    valid_targets = list(alive_ids)  # allow self-kill and teammate kill
    valid_targets_str = ", ".join(str(t) for t in valid_targets)

    wolf_decisions = {}

        # Determine play_style hints (same for all wolves)
    ps = state.get("play_style", "balanced")
    if ps == "aggressive":
        wolf_hint = "激进伪装：优先跳假身份混淆视听，大胆指认好人"
        seer_hint = "激进查验：第2轮必须报查验结果，对跳硬刚"
        witch_hint = "激进用药：有毒就跳，直接施压"
        villager_hint = "激进挡刀：必要时跳假身份吸引火力"
    else:  # balanced
        wolf_hint = "适度伪装：可选跳假预言家/女巫混淆视听"
        seer_hint = "适度查验：第2轮起公布结果但不必急于跳"
        witch_hint = "适度用药：有信息就表明身份"
        villager_hint = "适度挡刀：局势紧张时考虑挡刀"

    role_hints = f"""- 狼人: {wolf_hint}
- 预言家: {seer_hint}
- 女巫: {witch_hint}
- 村民: {villager_hint}"""


    # 1st round: discussion + tool call
    for wolf_id in werewolf_ids:
        player = players[str(wolf_id)]
        # Include secret chat history if available
        chat_ctx = ""
        if secret_chat_history:
            lines = []
            for msg in secret_chat_history:
                sender = msg.get("from", "?")
                c = msg.get("content", "")
                lines.append(f"[{sender}?]: {c[:200]}")
            if lines:
                chat_ctx = f"【秘密讨论记录】\n" + "\n".join(lines) + "\n【讨论结束】\n\n"

        extra = f"""\n{chat_ctx}【角色策略】
{role_hints}

【历史讨论】
{_format_chat(state.get("werewolf_chat", []))}

【击杀决策】
请使用 kill_player 工具选择今晚的击杀目标。

⚠️ 击杀优先级（从高到低）：
1. 已明牌的神职玩家（有人跳了预言家/女巫且被相信 → 立刻刀！）
2. 指挥投票方向的活跃玩家（可能是隐藏神职或高配村民）
3. 发言犀利的分析型玩家（威胁最大）
4. 其他存活玩家

可杀目标：{valid_targets_str}"""
        prompt = _build_role_prompt(player, state, extra)
        llm_prompt = f"请使用 kill_player 工具选择击杀目标。优先刀明牌神职！可杀目标：{valid_targets_str}。"

        result = _call_llm_with_tools(prompt, llm_prompt, WEREWOLF_TOOLS, temperature=0.8)
        response_text = result.get("content", "")

        tool_calls = result.get("tool_calls", [])
        decided_target = None
        for tc in tool_calls:
            if tc.get("name") == "kill_player":
                args = tc.get("args", {})
                decided_target = args.get("player_id")
                break

        wolf_decisions[wolf_id] = {
            "target": decided_target,
            "message": response_text,
        }

    targets = [d["target"] for d in wolf_decisions.values()]
    targets = [t for t in targets if t is not None]

    if len(set(targets)) == 1 and targets:
        final_target = targets[0]
    elif targets:
        # No consensus: 2nd round discussion
        new_chat = []
        for wolf_id, dec in wolf_decisions.items():
            msg = dec.get("message", "")
            if msg:
                new_chat.append({"player_id": wolf_id, "content": msg, "target": dec.get("target")})
                _add_to_memory(state, wolf_id, [{"role": "assistant", "content": msg}])

        for wolf_id in werewolf_ids:
            player = players[str(wolf_id)]
            decisions_summary = []
            for wid, dec in wolf_decisions.items():
                decisions_summary.append(f"玩家{wid}的选择: 目标{dec.get('target')}, 发言: {dec.get('message','')[:100]}")
            decisions_str = "\\n".join(decisions_summary)

            extra2 = f'''\n第一轮讨论结果：
{decisions_str}

请根据队友的选择，再次使用 kill_player 工具做出最终决定。
可杀目标：{valid_targets_str}'''
            prompt2 = _build_role_prompt(player, state, extra2)
            llm_prompt2 = f"第一轮你的队友选择了目标，请做出最终决定。使用 kill_player 工具。可杀目标：{valid_targets_str}。"

            result2 = _call_llm_with_tools(prompt2, llm_prompt2, WEREWOLF_TOOLS, temperature=0.5)
            tool_calls2 = result2.get("tool_calls", [])
            for tc in tool_calls2:
                if tc.get("name") == "kill_player":
                    args = tc.get("args", {})
                    wolf_decisions[wolf_id]["target"] = args.get("player_id")
                    break

        targets2 = [d["target"] for d in wolf_decisions.values()]
        targets2 = [t for t in targets2 if t is not None]
        if len(set(targets2)) == 1 and targets2:
            final_target = targets2[0]
        elif targets2:
            final_target = targets2[0]
        else:
            final_target = valid_targets[0] if valid_targets else None
    else:
        final_target = valid_targets[0] if valid_targets else None

    chat_entries = []
    for wolf_id, dec in wolf_decisions.items():
        chat_entries.append({
            "player_id": wolf_id,
            "content": dec.get("message", ""),
            "target": dec.get("target"),
        })
        _add_to_memory(state, wolf_id, [{"role": "assistant", "content": dec.get("message", "")}])

    return {
        "werewolf_kill_target": final_target,
        "werewolf_chat": chat_entries,
    }


def witch_decision(state: dict) -> dict:
    """Witch decides whether to save or poison."""
    players = state["players"]
    witch_id = None
    for pid, pdata in players.items():
        if pdata["role"] == "witch" and pdata["is_alive"]:
            witch_id = int(pid)
            break

    if witch_id is None:
        return {}

    player = players[str(witch_id)]
    alive_ids = state.get("alive_player_ids", [])
    killed_target = state.get("werewolf_kill_target")
    has_heal = state.get("witch_has_heal", True)
    has_poison = state.get("witch_has_poison", True)

    available_tools = []
    if has_heal and killed_target is not None:
        available_tools.append(save_player)
    if has_poison:
        available_tools.append(poison_player)

    extra = f'''
今晚狼人杀死的是玩家{killed_target}。
你可以使用的工具：{"save_player 和 poison_player" if len(available_tools) == 2 else "poison_player" if has_poison and not has_heal else "save_player" if has_heal else "无"}
请做出你的决定。记住：作为女巫，你有责任在关键时刻使用毒药帮助好人阵营！'''
    prompt = _build_role_prompt(player, state, extra)

    heal_target: int | None = None
    poison_target: int | None = None
    new_has_heal = has_heal
    new_has_poison = has_poison

    if available_tools:
        valid_targets = [pid for pid in alive_ids if pid != witch_id]
        valid_targets_str = ", ".join(str(t) for t in valid_targets)
        llm_prompt = f"请做出决定。可用的工具在函数列表中。可毒杀的目标：{valid_targets_str}（不能毒自己）。被杀死的是玩家{killed_target}。"

        result = _call_llm_with_tools(prompt, llm_prompt, available_tools, temperature=0.7)
        tool_calls = result.get("tool_calls", [])

        for tc in tool_calls:
            if tc.get("name") == "save_player":
                args = tc.get("args", {})
                heal_target = args.get("player_id")
                if heal_target is not None:
                    new_has_heal = False
            elif tc.get("name") == "poison_player":
                args = tc.get("args", {})
                pt = args.get("player_id")
                if pt is not None and pt in valid_targets:
                    poison_target = pt
                    new_has_poison = False

        _add_to_memory(state, witch_id, [{"role": "assistant", "content": result.get("content", "")}])

    return {
        "witch_heal_target": heal_target,
        "witch_poison_target": poison_target,
        "witch_has_heal": new_has_heal,
        "witch_has_poison": new_has_poison,
    }


def seer_check_action(state: dict) -> dict:
    """Seer chooses a player to check."""
    players = state["players"]
    seer_id = None
    for pid, pdata in players.items():
        if pdata["role"] == "seer" and pdata["is_alive"]:
            seer_id = int(pid)
            break

    if seer_id is None:
        return {}

    player = players[str(seer_id)]
    alive_ids = state.get("alive_player_ids", [])
    valid_targets = [pid for pid in alive_ids if pid != seer_id]
    valid_targets_str = ", ".join(str(t) for t in valid_targets)

    extra = f'''请使用 check_player 工具查验一名玩家的身份。
可以查验的目标：{valid_targets_str}'''
    prompt = _build_role_prompt(player, state, extra)
    llm_prompt = f"请使用 check_player 工具查验一名玩家的身份。可以查验的目标：{valid_targets_str}。"

    result = _call_llm_with_tools(prompt, llm_prompt, SEER_TOOLS, temperature=0.5)
    tool_calls = result.get("tool_calls", [])
    check_target = None
    for tc in tool_calls:
        if tc.get("name") == "check_player":
            args = tc.get("args", {})
            check_target = args.get("player_id")
            break

    check_result = None
    if check_target is not None:
        target_player = players.get(str(check_target))
        if target_player:
            actual_role = target_player["role"]
            check_result = "狼人" if actual_role == "werewolf" else "好人"
            _add_to_memory(state, seer_id, [
                {"role": "system", "content": f"查验结果：玩家{check_target}是{check_result}"}
            ])

    return {
        "seer_check_target": check_target,
        "seer_check_result": check_result,
    }


def _generate_last_words(player_id: int, state: dict) -> str:
    """Generate last words for a player killed on night 1.
    Role-specific prompt: seers know check results, witches know action history, wolves know teammates."""
    player = state["players"].get(str(player_id))
    if not player:
        return ""
    
    role = player["role"]
    round_num = state.get("game_round", 1)
    
    # Build role-specific context
    role_context = ""
    if role == "seer":
        check_hist = state.get("_seer_check_history", {})
        if check_hist:
            check_lines = []
            for r, entry in sorted(check_hist.items()):
                check_lines.append(f"你查验了玩家{entry['target']}，结果是{entry['result']}")
            role_context = "你的查验信息：" + "；".join(check_lines) + "。你可以选择透露或隐瞒这些信息。"
        else:
            role_context = "你还没有查验过任何玩家。"
    elif role == "witch":
        has_heal = state.get("witch_has_heal", True)
        has_poison = state.get("witch_has_poison", True)
        heal_status = "可用" if has_heal else "已用"
        poison_status = "可用" if has_poison else "已用"
        role_context = f"你的解药状态：{heal_status}，毒药状态：{poison_status}。你可以选择透露或隐瞒。"
    elif role == "werewolf":
        partner_id = None
        for pk, pv in state["players"].items():
            if int(pk) != player_id and pv["role"] == "werewolf":
                partner_id = pk
                break
        role_context = f"你的狼队友是玩家{partner_id}号。你可以假装神职带节奏，也可以低调装好人。记住你是狼人，你的狼队友还活着。"
    else:
        role_context = "你是普通村民，可以根据自己的判断发表遗言。"
    
    prompt = f"""你是狼人杀游戏的玩家{player_id}号，你的身份是{_get_role_name(role)}。
你在第1晚被淘汰了（你不知道自己是怎么被淘汰的），现在是你的遗言机会。

{role_context}

请发表你的遗言，严格控制在50字以内。

重要提示：目前是第一晚，尚未进行过任何白天公开发言，请不要以"某人发言划水"、"某人行为奇怪"、"某人偏狼"等理由指认其他玩家——这些判断还没有任何依据。你唯一能做的：决定是否暴露自己的真实身份，或选择沉默。

你可以：
- 选择暴露自己的真实身份，或假装成其他身份带节奏
- 不要超过50字！简短有力"""

    try:
        llm = get_llm(temperature=0.7)
        response = llm.invoke([HumanMessage(content=prompt)])
        last_words = response.content or "我没什么要说的。"
        # Truncate to ~50 Chinese characters
        if len(last_words) > 80:
            last_words = last_words[:80]
        return last_words.strip()
    except Exception:
        return "我没什么要说的。"

# ========== Day Phase Functions ==========


def _wolf_partner_suggestion(wolf_id: int, state: dict, chat_history=None) -> str:
    """Generate a strategy suggestion/reply from an LLM werewolf teammate.
    If chat_history is provided, this is a reply in an ongoing conversation."""
    player = state["players"].get(str(wolf_id))
    if not player:
        return ""

    alive_ids = state.get("alive_player_ids", [])
    werewolf_ids = [int(pid) for pid, p in state["players"].items()
                    if p["role"] == "werewolf" and p["is_alive"]]
    valid_targets = list(alive_ids)  # allow self-kill and teammate kill
    valid_targets_str = ", ".join(str(t) for t in valid_targets)

    eliminated_roles = state.get("eliminated_roles", {})
    night_killed = set(state.get("_night_killed_ids", []))
    eliminated_roles = {k: v for k, v in eliminated_roles.items() if int(k) not in night_killed}
    role_parts = [f"玩家{k}({_get_role_name(v)})" for k, v in eliminated_roles.items()]
    night_parts = [f"玩家{pid}(身份未知)" for pid in night_killed]
    elim_info = ", ".join(role_parts + night_parts) if (role_parts or night_parts) else "无"


    # Build day public context (speeches + votes) so wolf knows what happened
    day_context = ""
    speeches = state.get("speeches", [])
    votes = state.get("votes", {})
    if speeches:
        sp_lines = []
        for sp in speeches:
            sp_id = sp.get("player_id", "?")
            sp_content = sp.get("content", "")[:200]
            sp_lines.append(f"  玩家{sp_id}: {sp_content}")
        day_context += "白天公开发言：\n" + "\n".join(sp_lines) + "\n"
    if votes:
        vt_lines = []
        for v_id, tgt in votes.items():
            tgt_str = f"玩家{tgt}" if tgt and int(tgt) > 0 else "弃权"
            vt_lines.append(f"  玩家{v_id} → {tgt_str}")
        day_context += "白天投票：\n" + "\n".join(vt_lines) + "\n"
        # Tally
        from collections import Counter
        tally = Counter(int(t) for t in votes.values() if t and int(t) > 0)
        if tally:
            tl_lines = [f"  玩家{pid}:{cnt}票" for pid, cnt in tally.most_common()]
            day_context += "票数统计: " + ", ".join(tl_lines) + "\n"
    if not day_context:
        day_context = "（第一晚尚无白天信息）\n"
    # Build chat history context if multi-turn
    # IMPORTANT: When chat_history is provided, DON'T include it in extra (text form).
    # Instead, pass it as structured messages via history_for_llm.
    # This prevents the LLM from seeing the same conversation twice.
    chat_context = ""
    if chat_history:
        # Only use structured history, not text in extra
        chat_context = "（参考下方对话历史继续回复，不要重复之前说过的话）\n"
    else:
        chat_context = ""

    if chat_history:
        # Filter chat_history to only current round (avoid cross-night confusion)
        current_round = state.get("game_round", 0) + 1
        chat_history = [m for m in chat_history if m.get("round") == current_round]
        if not chat_history:
            chat_history = None

    if chat_history:
        # Build kill history from state
        kill_hist = state.get('_werewolf_kill_history', {})
        kill_lines = []
        for r in sorted(kill_hist.keys()):
            kill_lines.append(f"  第{r}晚：击杀玩家{kill_hist[r]}")
        kill_hist_str = "\n".join(kill_lines) if kill_lines else "  （尚无击杀记录）"

        extra = f"""【当前是第{state.get("game_round", 0) + 1}晚】你的真人队友7号正在等你讨论今晚杀谁。

前几晚你们的击杀记录：
{kill_hist_str}

存活玩家: {", ".join(str(p) for p in alive_ids)}
可杀目标: {valid_targets_str}
已淘汰的玩家: {elim_info}

{day_context}
{chat_context}
规则提醒：
1. 直接说出想法，不要用"我是X号玩家"这种公开演讲腔
2. 简短、像真实队友聊天一样
3. 你不是第一次发言！参考下面的对话历史继续聊，不要从头开始
4. 如果队友已经说了想杀谁，你就回应他的选择，不要重新提议
5. ⚠️ 已淘汰的玩家绝对不能再杀！可杀目标只包含存活玩家！
5. ⚠️ 已淘汰的玩家绝对不能杀！可杀目标只包含存活玩家！"""
    else:
        # Build kill history
        kill_hist = state.get('_werewolf_kill_history', {})
        kill_lines = []
        for r in sorted(kill_hist.keys()):
            kill_lines.append(f"  第{r}晚：击杀玩家{kill_hist[r]}")
        kill_hist_str = "\n".join(kill_lines) if kill_lines else "  （尚无击杀记录）"

        extra = f"""【当前是第{state.get("game_round", 0) + 1}晚】你的真人队友7号正在等你讨论今晚杀谁。

前几晚你们的击杀记录：
{kill_hist_str}

存活玩家: {", ".join(str(p) for p in alive_ids)}
可杀目标: {valid_targets_str}
已淘汰的玩家: {elim_info}

{day_context}
请就今晚杀谁给出你的策略建议。
规则提醒：
1. 直接说出想法，不要用"我是X号玩家"这种公开演讲腔
2. 简短、像真实队友聊天一样
3. 绝对不要长篇大论分析局势，这是秘密讨论不是公开发言！
4. 只讨论杀谁和策略，不要扯其他内容
5. ⚠️ 已淘汰的玩家绝对不能再杀！可杀目标只包含存活玩家！
5. ⚠️ 已淘汰的玩家绝对不能杀！可杀目标只包含存活玩家！"""

    prompt = _build_role_prompt(player, state, extra, is_secret_chat=True)
    if chat_history:
        llm_prompt = "继续。"
    else:
        llm_prompt = "请就今晚杀谁给出你的策略建议。简短直接，像队友聊天，不要用公开演讲腔。"
    # Build messages with proper role alternation (user/assistant/user/...)
    # Standard chat APIs require first non-system message to be user.
    # The old history_for_llm approach violated this, causing DeepSeek to
    # drop messages and the teammate to "forget" the conversation.
    if chat_history:
        llm = get_llm(temperature=0.8)
        messages = [SystemMessage(content=prompt)]
        first_is_assistant = chat_history and chat_history[0].get("from") != 7
        if first_is_assistant:
            # Synthetic user message to match the initial suggestion prompt
            messages.append(HumanMessage(content="请就今晚杀谁给出你的策略建议。"))
        for msg in chat_history:
            role = "assistant" if msg.get("from") != 7 else "user"
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))
        response = llm.invoke(messages)
        suggestion = response.content or ""
    else:
        suggestion = _call_llm_text(prompt, llm_prompt, temperature=0.8)
    _add_to_memory(state, wolf_id, [{"role": "assistant", "content": suggestion}])
    return suggestion or ""

def _wolf_strategy_summary(wolf_id: int, state: dict, kill_target: int, round_num: int, chat_history=None) -> str:
    """Generate a brief strategy summary for a werewolf's private memory.
    This is stored in player_memories so the wolf recalls the night's decision during day phases."""
    try:
        player = state['players'].get(str(wolf_id))
        if not player:
            return ''
        # Build a concise system message
        teammate_ids = [int(pid) for pid, p in state['players'].items()
                        if p['role'] == 'werewolf' and p['is_alive'] and int(pid) != wolf_id]
        teammate_str = f"队友玩家{teammate_ids[0]}" if teammate_ids else "队友已阵亡"
        summary = f"第{round_num}晚秘密讨论：{teammate_str}，决定击杀玩家{kill_target}。"
        return summary
    except Exception:
        return ''

def _format_chat(chat_list: list[dict]) -> str:
    """Format chat list into readable string."""
    if not chat_list:
        return "（暂无讨论）"
    lines = []
    for msg in chat_list:
        pid = msg.get("player_id", "?")
        content = msg.get("content", "")
        lines.append(f"玩家{pid}: {content[:200]}")
    return "\\n".join(lines)


def generate_speech(player_id: int, state: dict) -> str:
    """Generate speech for an LLM player during the speech phase.
    Loads the player's full memory history for context."""
    player = state["players"].get(str(player_id))
    if not player:
        return ""

    role = player["role"]
    speeches = state.get("speeches", [])
    round_num = state.get("game_round", 1)
    eliminated_roles = state.get("eliminated_roles", {})
    night_killed = set(state.get("_night_killed_ids", []))
    eliminated_roles = {k: v for k, v in eliminated_roles.items() if int(k) not in night_killed}
    speeches_lines = []
    for sp in speeches:
        sp_id = sp.get("player_id", "?")
        sp_content = sp.get("content", "")[:300]
        speeches_lines.append(f"玩家{sp_id}: {sp_content}")
    speeches_summary = "\n---\n".join(speeches_lines) if speeches_lines else "（你是第一位发言者）"

    # Build eliminated info
    elim_parts = []
    role_parts = [f"玩家{k}({_get_role_name(v)})" for k, v in eliminated_roles.items()]
    night_parts = [f"玩家{pid}(身份未知)" for pid in night_killed]
    elim_info_str = ", ".join(role_parts + night_parts) if (role_parts or night_parts) else "无"
    elim_str = ", ".join(elim_parts) if elim_parts else "无"
    night_result = state.get("god_announcement", "（上一晚没有玩家被淘汰）")

    # Build previous round vote history for context
    vote_history_text = ""
    if round_num > 1:
        prev_round = round_num - 1
        vh = state.get('votes_history', {})
        prev_votes = vh.get(prev_round, {})
        if prev_votes:
            vote_lines = []
            for v_id, tgt in prev_votes.items():
                tgt_str = f"玩家{tgt}" if tgt and int(tgt) > 0 else "弃权"
                vote_lines.append(f"玩家{v_id}→{tgt_str}")
            from collections import Counter
            tally = Counter(int(t) for t in prev_votes.values() if t and int(t) > 0)
            tally_lines = [f"玩家{pid}:{cnt}?" for pid, cnt in tally.most_common()]
            vote_history_text = "投票：" + "; ".join(vote_lines) + " 票数：" + ", ".join(tally_lines)
            if tally:
                max_cnt = tally.most_common(1)[0][1]
                top = [pid for pid, cnt in tally.items() if cnt == max_cnt]
                if len(top) == 1:
                    vote_history_text += f" 淘汰：玩家{top[0]}号"
                else:
                    vote_history_text += " 平票，无人淘汰"

    # Build mode-dependent role hints based on play_style
    ps = state.get("play_style", "balanced")
    if ps == "aggressive":
        wolf_hint = "第1轮起主动跳假身份/和队友配合制造混乱"
        seer_hint = "第1轮暗示有信息，第2轮公布所有查验结果并硬刚对跳者"
        witch_hint = "用药立刻公开，有毒就威胁毒人，主动指挥投票"
        villager_hint = "频繁挡刀假装神职，带头分析投票模式，带动全场节奏"
    elif ps == "conservative":
        wolf_hint = "全程伪装村民，不跳任何身份，低调随大流"
        seer_hint = "只在查到狼人时才跳身份，其他时间以村民身份发言"
        witch_hint = "永不暴露身份，只做村民式逻辑分析"
        villager_hint = "纯逻辑分析找狼人，不挡刀不伪装"
    else:  # balanced
        wolf_hint = "第2轮起考虑跳假预言家/女巫混淆视听"
        seer_hint = "第2轮起公布查验结果，有人对跳用查验链揭穿"
        witch_hint = "有用药信息就跳出来说明，局势不明时主动引导"
        villager_hint = "积极分析发言和投票，必要时跳假身份挡刀"
    
    role_hints = f"""- 狼人策略：{wolf_hint}
- 预言家策略：{seer_hint}
- 女巫策略：{witch_hint}
- 村民策略：{villager_hint}"""
    # 本轮角色策略提示（根据play_style生成）
    secret_chat_reminder = ""
    # 狼人读取夜间秘密讨论，在白天发言时记住策略
    if role == "werewolf":
        sc = state.get("_werewolf_secret_chat", [])
        if sc:
            current_round_msgs = [m for m in sc if m.get("round") == round_num]
            if current_round_msgs:
                sc_lines = []
                for m in current_round_msgs:
                    sender = m.get("from", "?")
                    c = m.get("content", "")
                    if isinstance(sender, int):
                        sc_lines.append(f"玩家{sender}号: {c[:150]}")
                    else:
                        sc_lines.append(f"[{sender}]: {c[:150]}")
                secret_chat_reminder = "\n【重要】本轮夜间你与队友秘密讨论记录：\n" + "\n".join(sc_lines) + "\n请在白天发言中配合执行你们讨论的策略！"

    

    extra = f'''
你是第{len(speeches) + 1}位发言者。
本轮之前的发言：
{speeches_summary}

昨晚的结果：{night_result}

上轮投票详情：
{vote_history_text}

{secret_chat_reminder}
当前是第{round_num}轮。
已经被淘汰的玩家（含身份）：{elim_info_str}

请发表你的观点。严格限制：发言不得超过300字，必须简洁明了！超长发言无效。记住：
- 发言严格控制在300字以内，简洁有力，禁止长篇大论
- 如果玩家已被淘汰，不要对他们发言
- 基于已知信息做合理推理
- 如果你是狼人：可选策略——低调装村民，或适时跳假预言家/女巫混淆视听
- 如果你是预言家：有查验结果就公布，不必死等查到狼人才跳
- 如果你是女巫：有用药信息就果断表明身份，不要只暗示
- 如果你是村民：大多数时候诚实分析，必要时挡刀（假装神职吸引狼人攻击）
- 一定要明确投票建议：建议投票给谁
- 再次强调：发言请严格控制在300字以内！超长无效'''
    prompt = _build_role_prompt(player, state, extra)

    # Load full player memory as history
    history = _get_player_memory(state, player_id)

    # Position-specific strategy hint to avoid homogenization
    speech_pos = len(speeches) + 1
    total_alive = len(state.get("alive_player_ids", []))
    if speech_pos <= 2:
        pos_hint = "你是最早发言的，可以自由发挥，不需要回应别人"
    elif speech_pos >= total_alive - 1:
        pos_hint = "你是最后发言的，需要总结前面所有人的观点，给出明确的投票建议"
    else:
        pos_hint = "你在中间发言，可以点评前面的观点，引出新的分析方向"


    # Random opener to avoid identical phrasing
    import random as _random
    openers = [
        f"玩家{player_id}号",
        f"我是{player_id}号",
        f"轮到我了，我是{player_id}号玩家",
    ]
    opener = _random.choice(openers)

    # Random style hint to diversify speech patterns
    style_hints = [
        "简洁有力，直接说重点",
        "用分析的语气表达，不要只总结别人的话",
        "自信表达你的判断，不要模棱两可",
    ]
    style_hint = _random.choice(style_hints)
    llm_prompt = f'''你是玩家{player_id}号。

第{round_num}轮发言框架：
{pos_hint}

【已淘汰玩家】{elim_info_str}

你必须按以下结构组织发言，每个部分都要覆盖：

1.【身份判断】如果淘汰玩家的身份已暴露，首先就此发表看法。
例如："玩家4号被淘汰后身份是预言家，这说明之前也跳预言家的
玩家1号必定是狼人，我今天建议全票出1号。"

2.【查验/用药信息】（你是神职时）公布你的查验结果或用药情况。

3.【票型回顾】（第2轮起）分析上一轮的投票模式。谁投了谁？

4.【发言分析】分析最可疑的1-2名玩家的发言。
指出具体矛盾，不要笼统地说"有人可疑"。

5.【投票建议】明确说"我建议今天投票给X号"，并给出理由。
必须给出一个具体的投票建议！

发言规则：
- 严格控制在300字以内，超过会被截断
- 禁止说"我是X号玩家，身份是..."——除神职跳身份外，不要在发言开头报编号
- 如果你发现了身份冲突（铁狼），必须大声说出来，不要藏着！
- 今晚的结果：{night_result}
- 上轮投票详情：{vote_history_text}
- 你必须以"{opener}"开头，{style_hint}。说自己的观点，不要总结别人的观点。不要重复上面已经说过的内容。'''

    speech = _call_llm_text(prompt, llm_prompt, temperature=0.9, history=history)
    _add_to_memory(state, player_id, [{"role": "assistant", "content": speech}])
    return speech or "（发言生成失败）"



def generate_vote(player_id: int, state: dict):
    """Generate a voting decision for an LLM player."""
    player = state["players"].get(str(player_id))
    if not player:
        return None

    role = player["role"]
    speeches = state.get("speeches", [])
    round_num = state.get("game_round", 1)
    eliminated_roles = state.get("eliminated_roles", {})
    night_killed = set(state.get("_night_killed_ids", []))
    eliminated_roles = {k: v for k, v in eliminated_roles.items() if int(k) not in night_killed}
    alive_ids = state.get("alive_player_ids", [])
    valid_targets = [int(x) for x in alive_ids if int(x) != player_id]
    valid_targets_str = ", ".join(str(t) for t in valid_targets)
    speeches_summary = "\n".join([f"玩家{s.get("player_id","?")}: {s.get("content","")[:150]}" for s in speeches]) if speeches else "（暂无发言）"
    elim_parts = []
    role_parts = [f"玩家{k}({_get_role_name(v)})" for k, v in eliminated_roles.items()]
    night_parts = [f"玩家{pid}(身份未知)" for pid in night_killed]
    elim_info_str = ", ".join(role_parts + night_parts) if (role_parts or night_parts) else "无"
    extra = f'''
当前是第{round_num}轮投票阶段。
刚刚所有玩家的发言：
{speeches_summary}

你可以投票的玩家（存活）：{valid_targets_str}
你必须投票，不要弃权！

已被淘汰的玩家（含身份）：{elim_info_str}

请做出投票决定。记住：

⚠️ 最重要的推理规则（优先级最高）：
如果淘汰玩家的身份已暴露，立刻检查是否有人之前声称过相同身份！
身份冲突 = 铁狼！例如：淘汰的4号是预言家，而1号也曾跳预言家 → 1号必为狼人！
这比任何发言分析都更可靠！

投票原则：
- 如果有身份冲突（铁狼证据）→ 必须投那个人，不需犹豫
- 如果有预言家查验"X号是狼人"→ 优先投X号
- 如果有明确狼人信息 → 果断投票
- 如果没有以上证据 → 投最可疑的玩家
- 绝对不要弃权！弃权等于帮狼人获胜！'''
    prompt = _build_role_prompt(player, state, extra)
    history = _get_player_memory(state, player_id)

    llm_prompt = f'''请按以下优先级顺序做出投票决定（高优先级证据可直接决定投票，无需走后续步骤）：

第1步（最高优先级 —— 身份冲突检查）：
已被淘汰的玩家身份是否已经暴露？
存活玩家中是否有人之前声称过与被淘汰者相同的身份？
→ 例如：淘汰的玩家4号是预言家，而玩家1号之前也自称预言家
→ 那么玩家1号100%是狼人！直接投票给他！不需要继续分析！
→ 身份冲突 = 铁狼，这是最硬的证据。

第2步（预言家查验结果）：
预言家是否公布了"X号是狼人"的查验结果？
→ 如果有，直接采信，投票给X号。

第3步（票型分析）：
上一轮谁投了谁？被淘汰者的投票对象是谁？
如果某玩家总是在保护另一个玩家（从不投他），他们可能是狼队友。

第4步（发言矛盾分析）：
同一玩家在不同轮次的发言是否有重大矛盾？
例如：上一轮怀疑A，这一轮突然转而攻击B，且没有合理解释。

第5步（兜底）：
如果以上步骤都无法确定，投你最怀疑的存活玩家。
可投票的玩家：{valid_targets_str}。你必须投票给其中一个！
回复一个数字。禁止回复"弃权"——弃权等于帮狼人获胜！'''

    vote_response = _call_llm_text(prompt, llm_prompt, temperature=0.4, history=history)

    if vote_response and "弃权" in vote_response:
        _add_to_memory(state, player_id, [{"role": "assistant", "content": "弃权"}])
        return None
    import re
    numbers = re.findall(r'\d+', vote_response or "")
    target = None
    if numbers:
        target = int(numbers[0])
        if target not in valid_targets:
            target = None
    if target is None and valid_targets:
        import random as _rand
        target = _rand.choice(valid_targets)
    if target is None:
        return None

    # Generate 50-word voting summary using LLM
    try:
        role_parts = [f"玩家{k}({_get_role_name(v)})" for k, v in eliminated_roles.items()]
        night_parts = [f"玩家{pid}(身份未知)" for pid in night_killed]
        elim_info = ", ".join(role_parts + night_parts) if (role_parts or night_parts) else "无"
        # Build vote result context
        all_votes = state.get('votes', {})
        vote_lines = []
        for v_id, tgt in all_votes.items():
            tgt_str = f'玩家{tgt}' if tgt and tgt > 0 else '弃权'
            vote_lines.append(f'玩家{v_id}→{tgt_str}')
        vote_summary_str = '; '.join(vote_lines) if vote_lines else '无投票记录'

        # Count votes
        from collections import Counter
        tally = Counter(t for t in all_votes.values() if t and t > 0)
        tally_lines = [f'玩家{pid}:{cnt}票' for pid, cnt in tally.most_common()]
        tally_str = ', '.join(tally_lines) if tally_lines else '平票'

        # Find eliminated
        eliminated_vote = None
        if tally:
            max_cnt = tally.most_common(1)[0][1]
            top = [pid for pid, cnt in tally.items() if cnt == max_cnt]
            if len(top) == 1:
                eliminated_vote = top[0]

        elim_vote_str = f'玩家{eliminated_vote}被投票淘汰' if eliminated_vote else '无人被淘汰（平票）'

        summary_prompt = f'本轮投票结果：{vote_summary_str}。票数：{tally_str}。结果：{elim_vote_str}。你投了玩家{target}。请用50字左右总结你的推理链。格式：第{round_num}轮投票总结：我怀疑[谁]，所以投了玩家{target}，因为[原因]。结合投票结果可以补充：我的判断是否正确。'
        llm_s = get_llm(temperature=0.3)
        summary_response = llm_s.invoke([HumanMessage(content=summary_prompt)])
        summary = summary_response.content or f'第{round_num}轮投票总结：投票给玩家{target}。'
        _add_to_memory(state, player_id, [{'role': 'system', 'content': summary}])
    except Exception:
        _add_to_memory(state, player_id, [{'role': 'system', 'content': f'第{round_num}轮投票总结：投票给玩家{target}。'}])

    _add_to_memory(state, player_id, [{'role': 'assistant', 'content': f'投票给玩家{target}'}])
    return target
