# AgentSociety Backend

多智能体社会模拟后端，支持 DeepSeek / Gemini。

## 快速开始

1) 配置环境变量（根目录创建 .env，可从 env.example 复制）：

```bash
cp env.example .env
```

`.env` 关键项（与代码一致）：

```bash
# 选择后端：deepseek 或 gemini
LLM_PROVIDER=deepseek

# DeepSeek
DEEPSEEK_API_KEY=你的APIKey
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Gemini（如使用）
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=你的APIKey
# GEMINI_MODEL=gemini-2.5-flash
```

2) 启动（脚本会自动创建 venv、用清华镜像安装依赖并运行）：

```bash
# Windows
start_ui.bat

# Linux / macOS
chmod +x start_ui.sh
./start_ui.sh
```

访问：
- Web UI: http://localhost:8000/ui
- API Docs: http://localhost:8000/docs

## 手动安装（可选）

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -U pip setuptools wheel \
  -i https://pypi.tuna.tsinghua.edu.cn/simple \
  --trusted-host pypi.tuna.tsinghua.edu.cn
pip install -r requirements.txt \
  -i https://pypi.tuna.tsinghua.edu.cn/simple \
  --trusted-host pypi.tuna.tsinghua.edu.cn
python -m src.api_server
```

## 常用目录

```
experiments/
  └── {实验名称}/
      ├── meta.json
      ├── env.json
      ├── agents.json
      ├── relations.json
      ├── constraints.json
      └── logs/
```

## 说明
- 脚本默认使用清华镜像安装依赖；需更换可自行改脚本镜像地址。
- 若使用 Gemini，请在 `.env` 切换 `LLM_PROVIDER` 并填写对应 Key。
