# WolfAgent - 狼人杀 AI 游戏

基于 LangGraph 多 Agent 协作的狼人杀游戏，AI 扮演狼人、村民、预言家、女巫等角色，人类玩家加入对战。

## 公网地址

🔗 https://wolfgo.top/wolf/

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python FastAPI + LangGraph + LangChain |
| 前端 | React + TypeScript + Vite + Tailwind CSS |
| 数据库 | MySQL (wolfagent) |
| AI | DeepSeek API |

## 本地部署

### 环境要求

- Python 3.12+
- Node.js 18+
- MySQL 8.0+

### 1. 克隆项目

```bash
git clone https://github.com/GBR-hash/WolfAgent.git
cd WolfAgent
```

### 2. 后端配置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 DeepSeek API Key 和数据库密码
```

### 3. 数据库初始化

```sql
CREATE DATABASE IF NOT EXISTS wolfagent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 前端配置

```bash
cd frontend
npm install
```

### 5. 启动

```bash
# 终端1 - 启动后端 (端口 8000)
python main.py

# 终端2 - 启动前端 (开发模式)
cd frontend && npm run dev
```

访问 http://localhost:5173

## 生产部署

```bash
# 前端构建
cd frontend && npm run build

# 后端使用 systemd 管理
sudo systemctl start wolf-agent
```

## 项目结构

```
WolfAgent/
├── main.py            # FastAPI 入口
├── agents/            # AI Agent 定义
├── app/               # 游戏逻辑
│   ├── graph.py       # LangGraph 工作流
│   ├── players.py     # 玩家管理
│   └── prompts.py     # 提示词
├── frontend/          # React 前端
└── utils/             # 工具函数
```

