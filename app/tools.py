# Game tools for Werewolf Agent - LLM function calling tools
from langchain_core.tools import tool
from typing import Optional


@tool
def kill_player(player_id: int) -> str:
    '''
    狼人使用：选择今晚要杀死的玩家。
    player_id: 要杀死的玩家编号（1-7）
    '''
    return f"已选择杀死玩家{player_id}。等待最终确认。"


@tool
def save_player(player_id: int) -> str:
    '''
    女巫使用：使用解药救活一名被狼人杀死的玩家。
    player_id: 要救活的玩家编号（1-7）
    注意：解药只能使用一次！
    '''
    return f"使用了解药，将救活玩家{player_id}。"


@tool
def poison_player(player_id: int) -> str:
    '''
    女巫使用：使用毒药毒杀一名玩家。
    player_id: 要毒杀的玩家编号（1-7）
    注意：毒药只能使用一次！
    '''
    return f"使用了毒药，将毒杀玩家{player_id}。"


@tool
def check_player(player_id: int) -> str:
    '''
    预言家使用：查验一名玩家的身份。
    player_id: 要查验的玩家编号（1-7）
    返回该玩家是"好人"还是"狼人"。
    '''
    return f"正在查验玩家{player_id}的身份..."


WEREWOLF_TOOLS = [kill_player]
WITCH_TOOLS = [save_player, poison_player]
SEER_TOOLS = [check_player]

# Tool name mapping for parsing
TOOL_BY_NAME = {
    "kill_player": kill_player,
    "save_player": save_player,
    "poison_player": poison_player,
    "check_player": check_player,
}
