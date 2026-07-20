# WolfAgent - 智能 AI Agent 平台

基于 LangGraph + FastAPI 构建的多功能 AI Agent，集成语音合成、游戏互动、文档处理、知识库问答等能力。

## 功能模块

| 模块 | 路径 | 说明 |
|------|------|------|
| 语音合成 | `/speak` | 阿里云 NLS 文本转语音，流式返回 WAV |
| 游戏助手 | `/game/` | 基于 LangGraph 的回合制互动游戏 |
| 身份认证 | `/auth/` | JWT 用户注册/登录 |
| 对战记录 | `/records` | 游戏历史记录查询 |
| 对话 API | `/api/` | LangGraph Agent 流式对话（SSE） |

## 技术栈

- **框架**: FastAPI + Uvicorn
- **AI 引擎**: LangChain + LangGraph + DeepSeek
- **语音**: 阿里云 NLS（自然语言语音合成）
- **数据库**: MySQL（Checkpointer 持久化）
- **认证**: bcrypt + PyJWT
- **前端**: Vite + Vue（独立静态部署）

## 系统架构

```
浏览器 ──→ wolfgo.top:443 ──→ Nginx ──→ 127.0.0.1:18000 ──(autossh)──→ 树莓派:8000
```

WolfAgent 部署在树莓派上，通过 autossh 反向隧道暴露到云服务器，Nginx 做 SSL 终结和路由。

## 部署方式

### systemd 服务

服务文件：`~/.config/systemd/user/wolfagent.service`

```ini
[Unit]
Description=WolfAgent (FastAPI on port 8000)
After=autossh-tunnel.service
Requires=autossh-tunnel.service

[Service]
Type=simple
WorkingDirectory=/mnt/nvme/workspace/WolfAgent
ExecStart=/mnt/nvme/workspace/.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

### 管理命令

```bash
systemctl --user status wolfagent       # 查看状态
systemctl --user restart wolfagent      # 重启
sudo journalctl _SYSTEMD_USER_UNIT=wolfagent.service -f  # 实时日志
```

## 环境变量

在项目根目录创建 `.env` 文件：

```env
# 阿里云 NLS 语音合成
NLS_AK_ID=your_aliyun_access_key
NLS_AK_SECRET=your_aliyun_secret

# JWT
JWT_SECRET=your_jwt_secret

# MySQL
DB_HOST=localhost
DB_PORT=13306
DB_USER=root
DB_PASSWORD=1234
DB_NAME=lc-db

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_key
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 前端页面 |
| POST | `/auth/login` | 用户登录 |
| POST | `/auth/register` | 用户注册 |
| GET | `/speak?text=xxx` | 语音合成（流式 WAV） |
| GET | `/records` | 游戏记录列表 |
| POST | `/api/chat` | Agent 对话（SSE） |
| GET | `/game/` | 游戏前端 |

## 线上访问

**https://wolfgo.top/wolf/**

## 本地开发

```bash
cd WolfAgent
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
