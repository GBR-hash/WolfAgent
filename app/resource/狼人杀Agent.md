
狼人杀Agent系统 - 设计决策与架构汇总
文档目的：为Agent助手提供完整的设计决策、架构要点和技术规范，用于生成代码实现。此文档包含所有关键设计决策，不含具体代码实现。
1. 项目核心目标
构建一个混合人机协作的狼人杀游戏Agent系统，满足以下核心需求：
✅ 支持真人玩家介入：在关键决策点（狼人讨论、女巫用药、预言家查验、人类发言/投票）暂停AI流程，等待人类输入
✅ 双重分析机制：
战术分析（投票前）：整合场上信息，输出投票策略
战略分析（投票后）：复盘本轮得失，更新长期记忆
✅ 角色隔离：狼人私密讨论空间，其他角色不可见
✅ 完整游戏流程：支持夜晚行动→白天发言→投票→分析→下一轮的完整循环
✅ 可视化工作流：提供清晰的架构图和状态流转
2. 系统架构设计
2.1 核心架构图















































2.2 关键设计原则
表格
原则	说明	实现要点
人类介入点 (HITL)	在关键决策点暂停AI流程	使用 __interrupt__ 节点，状态中包含 require_human_intervention 标志
状态隔离	保护私密信息	狼人讨论状态仅对狼人可见，公共信息池对所有玩家可见
双重分析	战术+战略分析分离	投票前分析（pre_vote_analysis）和投票后分析（post_vote_analysis）作为独立节点
可扩展性	支持新角色	角色特定状态（wolf_coven, witch, seer）独立设计
错误处理	健壮的游戏流程	状态中包含 error_log，游戏结束检查节点
3. 核心状态设计
3.1 状态结构总览
python

编辑



GameState = {
    # 全局状态
    "game_id": str,               # 唯一游戏ID
    "game_round": int,            # 当前轮次（从1开始）
    "current_phase": Literal["night", "day_speech", "vote", "analysis", "game_over"],
    "timestamp": datetime,        # 最后更新时间
    
    # 玩家管理
    "players": List[Player],      # 所有玩家信息
    "alive_players": List[int],   # 存活玩家ID列表
    
    # 阶段控制
    "night_step": int,            # 夜晚阶段步骤（0:wolf, 1:witch, 2:seer）
    "current_speaker_index": int, # 当前发言玩家索引
    "current_voter_index": int,   # 当前投票玩家索引
    
    # 角色特定状态
    "wolf_coven": WolfCovenState, # 狼人阵营状态
    "witch": WitchState,         # 女巫状态
    "seer": SeerState,           # 预言家状态
    
    # 投票管理
    "vote_state": VoteState,      # 投票状态
    
    # 分析状态
    "analysis": AnalysisState,    # 分析结果存储
    
    # 人类介入
    "require_human_intervention": bool,    # 是否需要人类介入
    "human_input_request": Optional[str], # 人类输入请求描述
    "human_input_result": Optional[Any],   # 人类输入结果
    
    # 日志
    "game_log": List[str],        # 游戏事件日志
    "error_log": List[str]        # 错误日志
}
3.2 关键子状态定义
Player: 包含 player_id, name, role, is_human, is_alive, private_memory, public_statements
WolfCovenState: 包含 target, strategy, consensus, discussion_history
WitchState: 包含 has_heal, has_poison, heal_target, poison_target, used_heal, used_poison
SeerState: 包含 check_target, check_result, suspicions
VoteState: 包含 votes_cast, current_voter, voting_complete
AnalysisState: 包含 pre_vote_analysis, post_vote_analysis, strategic_insights, updated_beliefs
4. 核心工作流节点
4.1 节点列表与职责
表格
节点名称	职责	人类介入点
night_router	路由夜晚阶段子步骤	❌
wolf_phase	狼人讨论和决策	✅（人类狼人）
witch_phase	女巫用药决策	✅（人类女巫）
seer_phase	预言家查验	✅（人类预言家）
day_announcement	公布夜晚结果	❌
speech_router	路由发言顺序	❌
human_speech	人类玩家发言	✅
ai_speech	AI玩家发言	❌
pre_vote_analysis	投票前战术分析	❌
vote_router	路由投票顺序	❌
human_vote	人类玩家投票	✅
ai_vote	AI玩家投票	❌
vote_resolution	投票结果统计	❌
post_vote_analysis	投票后战略分析	❌
game_over_check	检查游戏结束条件	❌
human_intervention_handler	处理人类输入	✅（所有介入点）
4.2 关键路由逻辑
夜晚路由：根据 night_step 决定下一步（狼人→女巫→预言家→白天）
发言路由：根据 current_speaker_index 和玩家是否为人类决定路由
投票路由：根据 current_voter_index 和玩家是否为人类决定路由
游戏结束路由：检查胜利条件（狼人数量≥村民数量，或所有狼人出局）
5. 人类介入机制 (HITL)
5.1 介入点设计
表格
介入点	触发条件	输入类型	处理方式
狼人行动	人类玩家是狼人	目标玩家ID	更新 wolf_coven.target
女巫用药	人类玩家是女巫	布尔值+目标ID	更新 witch 状态
预言家查验	人类玩家是预言家	目标玩家ID	更新 seer.check_target
人类发言	轮到人类玩家发言	文本字符串	添加到 public_statements
人类投票	轮到人类玩家投票	目标玩家ID或-1（弃票）	更新 vote_state.votes_cast
5.2 技术实现要点
状态标志：require_human_intervention 控制流程暂停
请求描述：human_input_request 提供清晰的输入指引
结果处理：human_intervention_handler 节点统一处理所有人类输入
超时机制：设置5分钟超时，超时后自动继续流程
6. 文件结构规划
文本

编辑



werewolf-agent/
├── app/
│   ├── state.py           # 状态定义（TypedDict）
│   ├── nodes.py           # 所有节点函数实现
│   ├── routers.py         # 路由函数
│   └── workflow.py        # 工作流构建
├── agents/
│   ├── wolf_agent.py      # 狼人Agent逻辑
│   ├── seer_agent.py      # 预言家Agent逻辑
│   ├── witch_agent.py     # 女巫Agent逻辑
│   └── villager_agent.py  # 村民Agent逻辑
├── utils/
│   ├── game_logic.py      # 游戏规则逻辑
│   ├── human_input.py     # 人类输入处理
│   └── visualization.py   # 可视化工具
├── config/
│   └── settings.py        # 配置文件
├── main.py                # FastAPI入口
├── requirements.txt       # 依赖管理
└── README.md              # 项目文档
7. 技术栈要求
7.1 核心依赖
LangGraph: 工作流管理（langgraph）
LangChain: Agent和LLM集成（langchain-core, langchain-openai）
FastAPI: Web服务（fastapi, uvicorn）
WebSocket: 实时人类介入（websockets）
状态管理: 内存检查点（langgraph.checkpoint.memory）
7.2 开发工具
依赖管理: uv（替代pip）
代码质量: ruff, mypy
测试: pytest
文档: mkdocs
8. 关键性能与安全要求
8.1 性能要求
响应时间：AI决策节点 < 10秒，人类介入无时间限制
并发支持：至少支持5个并发游戏会话
状态大小：单个游戏状态 < 1MB
8.2 安全要求
输入验证：所有人类输入必须验证格式和范围
会话隔离：不同游戏会话状态完全隔离
超时保护：人类介入5分钟超时自动继续
错误恢复：任何节点失败后能恢复到上一个稳定状态
9. 验收标准
9.1 功能验收
支持5人狼人杀完整流程（1狼2神2民）
人类玩家可以在5个介入点正确参与
双重分析机制产生有效的战术和战略洞察
狼人私密讨论对非狼人玩家不可见
游戏结束条件正确判断
9.2 非功能验收
工作流可视化清晰展示所有节点和路由
错误日志记录所有异常情况
状态序列化/反序列化无数据丢失
单元测试覆盖核心逻辑（>80%）