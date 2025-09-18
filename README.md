
# AgentSociety-Style Multi-Agent Backend (Modular, DB)

后端仅版（无前端），基于 FastAPI，具备：
- 场景下添加智能体（性别/语言/背景/特质）
- 回合制步骤生成：(think/speak/move/interact/idle)
- SQLite 持久化：agents / actions / dialogues / logs
- LLM 接口抽象（可替换为 OpenAI/Qwen/DeepSeek 等）

## 运行
```bash
pip install fastapi uvicorn pydantic
uvicorn app.api:app --reload --port 8000
```

## API
- `POST /agents` 添加智能体
- `POST /tick?steps=N` 推进 N 回合
- `GET /logs` 查看日志
- `GET /dialogue` 查看对话
- `GET /actions` 查看动作
- `GET /agents` 查看所有智能体

## 配置
- 默认数据库：`agentsociety.db`（同目录），可通过环境变量 `DB_PATH` 覆盖
- 如需真实 LLM，参考 `app/llm.py` 中的 `OpenAIClient` 示例，实现后在 `app/engine.py` 构造 `Engine(llm=YourClient())`

## 目录结构
```
agentsociety_backend/
  app/
    __init__.py
    api.py        # FastAPI 路由
    engine.py     # 引擎（动作决定 + 落库）
    models.py     # 基本枚举/Agent 数据结构
    llm.py        # LLM 抽象与占位实现
    db.py         # SQLite 连接与初始化
    config.py     # 配置项
  README.md
```

## 注意
- 此版本使用简单的 sqlite3 全局连接（check_same_thread=False）。生产请考虑 SQLAlchemy + 连接池，或每请求单连接。
- 该结构保持了与 AgentSociety 项目相似的“LLM 层可插拔”的理念，方便替换与扩展。
