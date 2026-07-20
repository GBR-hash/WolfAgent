# Game State Models for Werewolf Agent
from typing import TypedDict, Optional, Literal, Annotated, Any
from langgraph.graph.message import add_messages
import operator

RoleType = Literal["werewolf", "witch", "seer", "villager"]
PhaseType = Literal["init", "night", "day", "game_over"]

class PlayerData(TypedDict):
    player_id: int
    role: str          # "werewolf", "witch", "seer", "villager"
    is_human: bool
    is_alive: bool

class GameState(TypedDict, total=False):
    # Player management
    players: dict[str, dict]       # str(player_id) -> PlayerData
    alive_player_ids: list[int]
    human_player_id: int           # always 7
    human_role: Optional[str]        # pre-assigned role for human (None = random)
    play_style: str                # 'aggressive', 'balanced', 'conservative'
    game_round: int                # starts at 1

    # Phase control
    phase: str                     # "init", "night", "day_announcement", "day_speeches", "day_vote", "day_eliminate", "game_over"

    # Night action state
    _night_step: int               # 0=werewolf, 1=witch, 2=seer, 3=done (anti-replay guard)
    werewolf_kill_target: Optional[int]
    witch_has_heal: bool
    witch_has_poison: bool
    witch_heal_target: Optional[int]
    witch_poison_target: Optional[int]
    seer_check_target: Optional[int]
    seer_check_result: Optional[str]

    # Werewolf secret chat (only werewolves see this)
    werewolf_chat: Annotated[list[dict], operator.add]
    _werewolf_secret_chat: list[dict]  # human+LLM werewolf multi-turn secret discussion

    # ===== NEW: Role-specific action histories =====
    _werewolf_kill_history: dict[int, int]    # round_num -> killed_player_id (private, not in game_log)
    _witch_action_history: dict[int, dict]    # round_num -> {action: "heal"/"poison", target: pid}
    _seer_check_history: dict[int, dict]      # round_num -> {target: pid, result: "好人"/"狼人"}

    # Day phase state
    speech_order: list[int]
    speech_cursor: int
    speeches: list[dict]

    # Voting state
    vote_order: list[int]
    vote_cursor: int
    votes: dict[str, int]

    # Elimination tracking
    eliminated_tonight: list[int]
    eliminated_all: list[int]
    eliminated_roles: dict[int, str]
    _last_words: Optional[dict]   # night 1 last words: {player_id, content}
    _night_killed_ids: list[int]  # player IDs killed on night 1 (role hidden until game end); night 2+ kills go to eliminated_roles

    # ===== NEW: Per-round history for game review =====
    speeches_history: dict[int, list[dict]]   # round_num -> list of {player_id, content}
    votes_history: dict[int, dict[str, int]]  # round_num -> {voter_id: target}

    # ===== NEW: Vote tally for day_eliminate phase =====
    _vote_tally: dict          # {votes: {voter->target}, counts: {target->count}, eliminated: int|null}
    _eliminated_today: Optional[int]

    # God's announcement
    god_announcement: str

    # Game result
    game_over: bool
    winner: Optional[str]

    # Human interaction
    interrupt_type: str
    interrupt_prompt: str
    human_input: str

    # Per-player LLM memories
    player_memories: dict[str, list[dict]]

    # Night summary for round summary building
    night_summary: str

    # Error tracking
    game_log: Annotated[list[dict], operator.add]
    error_log: Annotated[list[str], operator.add]
