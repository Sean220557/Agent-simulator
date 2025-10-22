# Multi-Agent Social Simulation Platform

This project is a **multi-agent simulation framework** powered by LLMs (e.g., DeepSeek-Chat).  
It enables researchers to design **social experiments in silico**, where agents with realistic personas interact within shared environments.  
Inspired by controversial experiments such as *The Third Wave*, this platform provides a **safe and ethical alternative** for studying collective behavior, authority, conformity, and social dynamics.

---

## 📑 目录

- [快速开始](#-快速开始)
- [环境配置详细步骤](#-环境配置详细步骤)
- [创建实验](#-创建实验)
- [运行模拟](#-运行模拟)
- [API接口使用](#-api接口使用)
- [核心功能](#-核心功能)
- [CLI命令行工具](#-cli命令行工具)
- [数据分析](#-数据分析)
- [常见问题](#-常见问题)

---

## 🚀 快速开始

**推荐方式：使用Web UI界面**

### 步骤一：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤二：配置API密钥

在项目根目录创建 `.env` 文件：

```bash
OPENAI_API_KEY=your_deepseek_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com
```

**获取 DeepSeek API Key:**
1. 访问 https://platform.deepseek.com/
2. 注册/登录账号
3. 在"API Keys"页面创建新密钥
4. 复制密钥粘贴到 `.env` 文件

### 步骤三：启动Web服务器

**Windows用户：**
```bash
start_ui.bat
```
或双击 `start_ui.bat` 文件

**Linux/Mac用户：**
```bash
chmod +x start_ui.sh
./start_ui.sh
```

### 步骤四：打开浏览器

启动成功后访问：
- 🌐 **Web界面**: http://localhost:8000/ui
- 📚 **API文档**: http://localhost:8000/docs

---

## ⚙️ 环境配置详细步骤

### 1. 系统要求

- **Python版本**: 3.10 或更高
- **操作系统**: Windows / Linux / macOS
- **内存**: 建议 4GB 以上
- **网络**: 需要访问外网（调用LLM API）

### 2. Python环境安装

**Windows:**
```bash
# 下载并安装 Python 3.10+
# 从 https://www.python.org/downloads/ 下载安装包

# 验证安装
python --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
python3.10 --version
```

**macOS:**
```bash
# 使用 Homebrew
brew install python@3.10
python3.10 --version
```

### 3. 创建虚拟环境

```bash
# 进入项目目录
cd agentsociety_backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# 验证虚拟环境已激活（命令行前会显示 (venv)）
```

### 4. 安装项目依赖

```bash
pip install -r requirements.txt
```

依赖包列表：
- `openai>=1.42.0` - OpenAI兼容的API客户端
- `python-dotenv>=1.0.1` - 环境变量管理
- `tenacity>=9.0.0` - API重试机制
- `pydantic>=2.8.2` - 数据验证
- `numpy>=1.24.0` - 数值计算
- `fastapi>=0.100.0` - Web API框架
- `uvicorn>=0.23.0` - ASGI服务器

### 5. 配置环境变量

在项目根目录创建 `.env` 文件（可以从 `env.example` 复制）：

```bash
# 复制示例文件
cp env.example .env

# 编辑 .env 文件
nano .env  # 或使用其他编辑器
```

`.env` 文件内容：

```bash
# 使用 DeepSeek API（推荐，性价比高）
OPENAI_API_KEY=sk-your-deepseek-api-key
OPENAI_BASE_URL=https://api.deepseek.com

# 或使用 OpenAI（成本较高）
# OPENAI_API_KEY=sk-your-openai-api-key
# OPENAI_BASE_URL=https://api.openai.com/v1

# 或使用本地LLM（如Ollama）
# OPENAI_API_KEY=ollama
# OPENAI_BASE_URL=http://localhost:11434/v1

# 可选：自定义系统提示词
# SYSTEM_PROMPT=You are a helpful assistant.
```

### 6. 验证配置

```bash
# 测试API连接
python src/app.py "你好，世界"

# 如果配置正确，应该能看到LLM的响应
```

### 7. 启动服务器

```bash
# 使用启动脚本（推荐）
# Windows:
start_ui.bat

# Linux/Mac:
./start_ui.sh

# 或手动启动
python -m src.api_server
```

服务器启动成功会显示：
```
================================
AgentSociety Web UI Server
================================
访问 http://localhost:8000/ui 使用Web界面
访问 http://localhost:8000/docs 查看API文档
================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🧪 创建实验

### 方法一：通过Web UI创建（推荐）

1. **访问Web界面**: http://localhost:8000/ui

2. **填写实验信息**:
   - **实验名称**: 例如"办公室社交实验"
   - **环境描述**: 详细描述场景，例如：
     ```
     一个现代科技公司的办公室，包含开放工位、会议室、休息区和食堂。
     有程序员、设计师、产品经理等不同角色的员工。
     公司正在进行新产品开发，团队需要频繁协作。
     ```
   - **智能体数量**: 10-30（建议从少开始）
   - **关系影响力**: 0.8（默认值，范围0-1）

3. **（可选）高级配置**:
   ```json
   {
     "occupations": ["programmer", "designer", "product_manager", "tester"],
     "relation_density": 0.08,
     "age_range": [25, 40]
   }
   ```

4. **点击"创建实验"按钮**

5. **等待创建完成**（通常需要30-90秒）
   - 系统会自动生成环境描述
   - 创建符合环境的多样化智能体
   - 建立社会关系网络
   - 初始化日志系统

6. **查看创建结果**:
   - 实验会出现在右侧列表中
   - 点击实验名称查看详情

### 方法二：通过命令行创建

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 创建实验
python src/exp_cli.py create \
  --name "办公室社交实验" \
  --env-hint "一个现代科技公司的办公室环境" \
  --count 15 \
  --relation-influence 0.8

# 带约束条件的创建
python src/exp_cli.py create \
  --name "医院急诊室" \
  --env-hint "繁忙的医院急诊室，包含接待区、候诊区、诊室" \
  --count 20 \
  --constraints-json '{"occupations": ["doctor", "nurse", "patient"], "relation_density": 0.05}'
```

### 方法三：通过API创建

```bash
curl -X POST http://localhost:8000/api/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "校园咖啡馆",
    "env_hint": "一个大学校园内的咖啡馆，有学生、教师、咖啡师",
    "count": 15,
    "relation_influence": 0.8
  }'
```

### 实验目录结构

创建成功后，会在 `experiments/` 目录下生成实验文件夹：

```
experiments/
  └── 办公室社交实验/
      ├── meta.json          # 实验元信息
      ├── env.json           # 环境描述
      ├── agents.json        # 所有智能体信息
      ├── relations.json     # 社会关系网络
      ├── constraints.json   # 约束条件
      └── logs/              # 日志目录
          └── agents/        # 各智能体的日志文件
              ├── JohnDoe.jsonl
              ├── JaneSmith.jsonl
              └── ...
```

### 实验配置示例

**示例1：校园社交实验**
```json
{
  "name": "大学校园社交网络",
  "env_hint": "一所现代大学校园，包含教室、图书馆、食堂、宿舍和运动场。学生来自不同年级和专业。",
  "count": 20,
  "relation_influence": 0.75
}
```

**示例2：紧急情况模拟**
```json
{
  "name": "办公楼火警疏散",
  "env_hint": "一栋10层办公大楼发生火警警报，有员工、访客、保安。规则：1) 必须按疏散指示行动 2) 不使用电梯 3) 优先帮助需要协助的人",
  "count": 30,
  "relation_influence": 0.5,
  "constraints_json": "{\"occupations\": [\"employee\", \"visitor\", \"security_guard\"], \"relation_density\": 0.05}"
}
```

**示例3：第三浪潮实验**
```json
{
  "name": "第三浪潮复现实验",
  "env_hint": "1960年代美国高中历史课堂，进行关于纪律、团体归属感和权威的社会实验。包含教室、走廊、食堂。规则：1) 遵守课堂纪律 2) 鼓励团队协作 3) 强调集体荣誉",
  "count": 25,
  "relation_influence": 0.9
}
```

---

## ▶️ 运行模拟

### 方法一：通过Web UI运行（推荐）

1. **打开实验详情页**: 在实验列表中点击实验名称

2. **切换到"运行模拟"标签**

3. **配置模拟参数**:
   - **Temperature** (0.0-2.0): 控制随机性，默认0.7
     - 0.0-0.3: 行为稳定、可预测
     - 0.4-0.7: 平衡的创造性
     - 0.8-2.0: 高度随机、创造性
   - **Max Tokens**: 每次生成的最大长度，默认700
   - **Tick间隔**: 时间步间隔（秒），默认10秒
   - **最大Ticks**: 限制运行次数（留空则持续运行）

4. **点击"启动模拟"按钮**

5. **监控运行状态**:
   - 显示当前Tick数
   - 显示运行状态（运行中/已停止）
   - 每5秒自动刷新

6. **查看实时日志**:
   - 切换到"日志"标签
   - 点击"刷新日志"查看最新活动

7. **停止模拟**:
   - 点击"停止模拟"按钮
   - 或等待达到最大Ticks自动停止

### 方法二：通过命令行运行

```bash
# 运行实验（交互式模式）
python src/app_loop.py \
  --exp-dir experiments/办公室社交实验 \
  --interval 60 \
  --max-ticks 10

# 后台运行
nohup python src/app_loop.py \
  --exp-dir experiments/办公室社交实验 \
  --interval 60 > simulation.log 2>&1 &
```

### 方法三：通过API运行

**启动模拟：**
```bash
curl -X POST http://localhost:8000/api/experiments/{实验slug}/start \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 0.7,
    "max_tokens": 700,
    "interval": 10,
    "max_ticks": 20
  }'
```

**查询状态：**
```bash
curl http://localhost:8000/api/experiments/{实验slug}/status
```

**停止模拟：**
```bash
curl -X POST http://localhost:8000/api/experiments/{实验slug}/stop
```

### 日志格式说明

每个智能体的日志保存在 `logs/agents/{AgentName}.jsonl` 文件中，格式为JSONL（每行一个JSON对象）：

```json
{
  "type": "tick",
  "tick": 5,
  "agent_id": "agent_001",
  "agent_name": "John Doe",
  "location": "Meeting Room",
  "action": "Participating in team meeting",
  "speech": "I think we should prioritize the API redesign",
  "thoughts": "Considering the project timeline and team capacity",
  "state": {
    "mood": "focused",
    "energy": 0.8
  },
  "memory": ["Discussed API redesign with team"],
  "emotion": {
    "valence": 0.6,
    "arousal": 0.7,
    "dominance": 0.5
  }
}
```

---

## 📡 API接口使用

### 基础信息

- **服务地址**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **内容类型**: `application/json`

### 完整API列表

#### 1. 获取API信息

```bash
GET /
```

**响应示例：**
```json
{
  "name": "AgentSociety API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

#### 2. 获取所有实验

```bash
GET /api/experiments
```

**响应示例：**
```json
[
  {
    "name": "办公室社交实验",
    "slug": "办公室社交实验",
    "path": "experiments/办公室社交实验",
    "created_at": "2024-01-15T10:30:00",
    "agent_count": 15,
    "has_logs": true
  },
  {
    "name": "校园咖啡馆",
    "slug": "校园咖啡馆",
    "path": "experiments/校园咖啡馆",
    "created_at": "2024-01-14T08:20:00",
    "agent_count": 20,
    "has_logs": false
  }
]
```

---

#### 3. 创建新实验

```bash
POST /api/experiments
Content-Type: application/json
```

**请求体：**
```json
{
  "name": "实验名称",
  "env_hint": "环境描述文本",
  "count": 15,
  "relation_influence": 0.8,
  "constraints_json": "{\"occupations\": [\"programmer\", \"designer\"]}"
}
```

**参数说明：**
- `name` (必需): 实验名称
- `env_hint` (必需): 环境描述，会由LLM扩展为完整环境
- `count` (必需): 智能体数量
- `relation_influence` (可选): 关系影响力，范围0-1，默认0.8
- `constraints_json` (可选): JSON字符串格式的约束条件

**响应示例：**
```json
{
  "success": true,
  "message": "实验创建成功",
  "experiment_path": "experiments/实验名称"
}
```

**cURL示例：**
```bash
curl -X POST http://localhost:8000/api/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试实验",
    "env_hint": "一个小型咖啡馆",
    "count": 10,
    "relation_influence": 0.8
  }'
```

**Python示例：**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/experiments",
    json={
        "name": "测试实验",
        "env_hint": "一个小型咖啡馆",
        "count": 10,
        "relation_influence": 0.8
    }
)
print(response.json())
```

---

#### 4. 获取实验详情

```bash
GET /api/experiments/{exp_slug}
```

**响应示例：**
```json
{
  "meta": {
    "name": "办公室社交实验",
    "slug": "办公室社交实验",
    "relation_influence": 0.8,
    "count": 15
  },
  "environment": {
    "title": "现代科技公司办公室",
    "prompt": "一个开放式办公空间，包含工位区、会议室、休息区和食堂...",
    "rules": [
      "工作时间为9:00-18:00",
      "会议室需要提前预约",
      "休息区禁止大声喧哗"
    ]
  },
  "agents": [
    {
      "id": "agent_001",
      "name": "John Doe",
      "description": "30岁男性，高级软件工程师...",
      "initial_state": {
        "location": "工位区",
        "mood": "focused"
      },
      "relations": {
        "agent_002": {
          "type": "coworker",
          "strength": 0.7
        }
      }
    }
  ],
  "relations": {
    "agent_001": {
      "agent_002": {
        "type": "coworker",
        "strength": 0.7
      }
    }
  },
  "simulation_running": false
}
```

---

#### 5. 获取实验日志

```bash
GET /api/experiments/{exp_slug}/logs?agent_name={agent_name}&limit={limit}
```

**参数说明：**
- `agent_name` (可选): 指定智能体名称，不提供则返回所有智能体的最新日志
- `limit` (可选): 限制返回数量，默认100

**响应示例（所有智能体）：**
```json
{
  "logs": [
    {
      "agent_file": "JohnDoe.jsonl",
      "type": "tick",
      "tick": 10,
      "agent_name": "John Doe",
      "location": "Meeting Room",
      "action": "Discussing project timeline",
      "speech": "We need to finalize the API design by Friday"
    }
  ]
}
```

**响应示例（单个智能体）：**
```json
{
  "logs": [
    {
      "type": "tick",
      "tick": 1,
      "agent_name": "John Doe",
      "location": "工位区",
      "action": "Coding",
      "speech": "",
      "thoughts": "Need to fix this bug before lunch"
    },
    {
      "type": "tick",
      "tick": 2,
      "agent_name": "John Doe",
      "location": "休息区",
      "action": "Taking a break",
      "speech": "This coffee is great!",
      "thoughts": "Good time to relax"
    }
  ]
}
```

**cURL示例：**
```bash
# 获取所有智能体的最新日志
curl http://localhost:8000/api/experiments/办公室社交实验/logs

# 获取特定智能体的日志
curl "http://localhost:8000/api/experiments/办公室社交实验/logs?agent_name=JohnDoe&limit=50"
```

---

#### 6. 启动模拟

```bash
POST /api/experiments/{exp_slug}/start
Content-Type: application/json
```

**请求体：**
```json
{
  "temperature": 0.7,
  "max_tokens": 700,
  "interval": 10.0,
  "max_ticks": 20
}
```

**参数说明：**
- `temperature` (可选): LLM温度参数，范围0.0-2.0，默认0.7
- `max_tokens` (可选): 每次生成的最大token数，默认700
- `interval` (可选): 每个tick的间隔秒数，默认10.0
- `max_ticks` (可选): 最大tick数，不设置则持续运行

**响应示例：**
```json
{
  "success": true,
  "message": "模拟已启动"
}
```

**cURL示例：**
```bash
curl -X POST http://localhost:8000/api/experiments/办公室社交实验/start \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 0.7,
    "interval": 10,
    "max_ticks": 50
  }'
```

---

#### 7. 停止模拟

```bash
POST /api/experiments/{exp_slug}/stop
```

**响应示例：**
```json
{
  "success": true,
  "message": "正在停止模拟..."
}
```

**cURL示例：**
```bash
curl -X POST http://localhost:8000/api/experiments/办公室社交实验/stop
```

---

#### 8. 查询模拟状态

```bash
GET /api/experiments/{exp_slug}/status
```

**响应示例（运行中）：**
```json
{
  "running": true,
  "current_tick": 15,
  "message": "运行中"
}
```

**响应示例（未运行）：**
```json
{
  "running": false,
  "current_tick": 0,
  "message": "模拟未运行"
}
```

---

#### 9. 删除实验

```bash
DELETE /api/experiments/{exp_slug}
```

**响应示例：**
```json
{
  "success": true,
  "message": "实验已删除"
}
```

**cURL示例：**
```bash
curl -X DELETE http://localhost:8000/api/experiments/测试实验
```

---

### 完整工作流示例

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. 创建实验
print("创建实验...")
create_response = requests.post(
    f"{BASE_URL}/api/experiments",
    json={
        "name": "API测试实验",
        "env_hint": "一个小型咖啡馆，有顾客和咖啡师",
        "count": 10,
        "relation_influence": 0.8
    }
)
print(create_response.json())
exp_slug = "API测试实验"

# 2. 查看实验详情
print("\n查看实验详情...")
detail_response = requests.get(f"{BASE_URL}/api/experiments/{exp_slug}")
experiment = detail_response.json()
print(f"智能体数量: {len(experiment['agents'])}")

# 3. 启动模拟
print("\n启动模拟...")
start_response = requests.post(
    f"{BASE_URL}/api/experiments/{exp_slug}/start",
    json={
        "temperature": 0.7,
        "interval": 5,
        "max_ticks": 10
    }
)
print(start_response.json())

# 4. 监控状态
print("\n监控模拟状态...")
for i in range(5):
    time.sleep(10)
    status_response = requests.get(f"{BASE_URL}/api/experiments/{exp_slug}/status")
    status = status_response.json()
    print(f"Tick {status['current_tick']}: {status['message']}")
    
    if not status['running']:
        break

# 5. 查看日志
print("\n查看日志...")
logs_response = requests.get(f"{BASE_URL}/api/experiments/{exp_slug}/logs")
logs = logs_response.json()['logs']
print(f"共有 {len(logs)} 条最新日志")

# 6. 停止模拟（如果还在运行）
print("\n停止模拟...")
stop_response = requests.post(f"{BASE_URL}/api/experiments/{exp_slug}/stop")
print(stop_response.json())
```

---

### 错误处理

所有API错误都返回标准格式：

```json
{
  "detail": "错误描述信息"
}
```

常见HTTP状态码：
- `200` - 成功
- `400` - 请求参数错误
- `404` - 资源不存在
- `500` - 服务器内部错误

---

## ✨ 核心功能

### 1. 实验管理
- 创建独立的实验目录，包含环境规格、智能体、关系和日志
- 每个实验有自己的 `agents.json`, `env.json`, `relations.json` 和日志文件

### 2. 智能体生成
- 真实的英文姓名（名+姓）
- 包含性别、年龄、职业、教育、收入、描述、初始记忆和状态
- 支持基于LLM的生成，确保多样性
- 人口统计和职业分布可通过约束条件引导

### 3. 环境建模
- 从简单的 `--env-hint` 扩展为详细的 `env.json`：
  - 标题
  - 详细描述
  - 明确规则
- 示例: "1960年代美国高中教室" → 生成教室、食堂、体育馆等

### 4. 关系图谱
- 每个实验包含**社会关系网络** (`relations.json`)
- 关系类型（家人、同事、邻居、熟人）影响互动概率和信任度
- 强度因子 (`0-1`) 控制互动频率和可靠性

### 5. 模拟循环
- 基于tick的模拟，可配置间隔
- 每个tick智能体更新行动、对话、状态、思考和记忆
- 同地点的群体相遇模拟，受关系的**硬约束**
- 日志按智能体和集体事件分别保存

### 6. 日志与分析
- `logs/agents/<agent>.jsonl` → 每个智能体的逐步日志
- `logs/events/encounters.jsonl` → 每个tick的所有群体事件
- JSONL格式便于后续**定量分析**和**可视化**

---

## 💻 CLI命令行工具

### 实验管理CLI

```bash
# 创建实验
python src/exp_cli.py create \
  --name "实验名称" \
  --env-hint "环境描述" \
  --count 20 \
  --relation-influence 0.8 \
  --constraints-json '{"occupations": ["teacher", "student"]}'

# 从JSON文件读取约束
python src/exp_cli.py create \
  --name "复杂实验" \
  --env-hint "复杂环境" \
  --count 30 \
  --constraints-json constraints.json
```

### 智能体CLI

```bash
# 查看智能体信息
python src/agents_cli.py list --exp-dir experiments/实验名称

# 生成新智能体
python src/agents_cli.py generate \
  --count 10 \
  --env-hint "咖啡馆环境"
```

### 关系管理CLI

```bash
# 查看关系网络
python src/relations_cli.py show \
  --exp-dir experiments/实验名称

# 分析关系密度
python src/relations_cli.py analyze \
  --exp-dir experiments/实验名称
```

---

## 📊 数据分析

### 日志文件位置

```
experiments/
  └── {实验名称}/
      └── logs/
          ├── agents/          # 各智能体日志
          │   ├── JohnDoe.jsonl
          │   ├── JaneSmith.jsonl
          │   └── ...
          └── events/          # 事件日志
              └── encounters.jsonl
```

### Python分析示例

```python
import json
from collections import Counter
from pathlib import Path

# 读取单个智能体的日志
def load_agent_logs(agent_name, exp_dir):
    log_file = Path(exp_dir) / "logs" / "agents" / f"{agent_name}.jsonl"
    logs = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))
    return logs

# 分析行为模式
logs = load_agent_logs("JohnDoe", "experiments/办公室社交实验")

# 统计行为类型
actions = [log.get('action', '') for log in logs if 'action' in log]
action_counts = Counter(actions)
print("行为频率：", action_counts.most_common(10))

# 分析对话内容
speeches = [log.get('speech', '') for log in logs if log.get('speech')]
print(f"总对话次数: {len(speeches)}")

# 分析位置变化
locations = [log.get('location', '') for log in logs if 'location' in log]
location_changes = Counter(locations)
print("位置分布：", location_changes)

# 情绪分析
emotions = [log.get('emotion', {}) for log in logs if 'emotion' in log]
if emotions:
    avg_valence = sum(e.get('valence', 0) for e in emotions) / len(emotions)
    print(f"平均愉悦度: {avg_valence:.2f}")
```

### 可视化示例

```python
import matplotlib.pyplot as plt
import json

# 绘制智能体活动时间线
def plot_agent_timeline(agent_name, exp_dir):
    logs = load_agent_logs(agent_name, exp_dir)
    ticks = [log['tick'] for log in logs if 'tick' in log]
    locations = [log.get('location', 'Unknown') for log in logs]
    
    plt.figure(figsize=(12, 6))
    plt.scatter(ticks, locations, alpha=0.6)
    plt.xlabel('Tick')
    plt.ylabel('Location')
    plt.title(f'{agent_name} Activity Timeline')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# 绘制关系网络
import networkx as nx

def plot_relation_network(exp_dir):
    relations_file = Path(exp_dir) / "relations.json"
    with open(relations_file, 'r', encoding='utf-8') as f:
        relations = json.load(f)
    
    G = nx.Graph()
    for source, targets in relations.items():
        for target, rel_info in targets.items():
            G.add_edge(source, target, 
                      weight=rel_info['strength'],
                      type=rel_info['type'])
    
    plt.figure(figsize=(15, 15))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=500, font_size=8, font_weight='bold')
    plt.title('Social Relation Network')
    plt.show()
```

---

## ❓ 常见问题

### Q1: 提示"No module named 'src'"错误？

**A**: 确保从项目根目录运行，或使用 `-m` 参数：
```bash
cd agentsociety_backend
python -m src.api_server
```

### Q2: API调用失败，显示认证错误？

**A**: 检查以下几点：
1. `.env` 文件是否存在于项目根目录
2. `OPENAI_API_KEY` 是否正确配置
3. API密钥是否有效且有足够额度
4. 网络连接是否正常

### Q3: 创建实验很慢？

**A**: 这是正常的，创建过程需要多次调用LLM：
- 生成环境描述（1次）
- 生成约束条件（1次）
- 生成每个智能体（N次）
通常需要30-90秒，智能体越多耗时越长。

### Q4: 模拟运行很慢？

**A**: 每个tick都需要为每个智能体调用LLM。优化建议：
1. 增加tick间隔时间（如60秒）
2. 减少智能体数量（10-15个最佳）
3. 使用更快的LLM模型
4. 降低 `max_tokens` 参数

### Q5: 端口8000被占用？

**A**: 修改端口号：
```python
# 编辑 src/api_server.py 最后一行
uvicorn.run(app, host="0.0.0.0", port=8080)  # 改为其他端口
```

### Q6: 如何使用本地LLM（如Ollama）？

**A**: 修改 `.env` 文件：
```bash
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
```
确保Ollama已启动并加载了模型。

### Q7: 如何导出实验数据？

**A**: 所有数据都以JSON/JSONL格式保存在 `experiments/` 目录：
```bash
# 压缩整个实验目录
tar -czf experiment_backup.tar.gz experiments/实验名称/

# 或使用Python读取
import json
with open('experiments/实验名称/agents.json', 'r') as f:
    agents = json.load(f)
```

### Q8: 可以同时运行多个实验吗？

**A**: 可以！每个实验的模拟是独立的后台任务。但注意：
- 同时运行多个会增加API调用量
- 可能影响性能和响应速度

### Q9: 服务器崩溃后数据会丢失吗？

**A**: 不会。所有数据实时写入磁盘：
- 实验配置保存在JSON文件中
- 日志实时追加到JSONL文件
- 重启服务器后可继续使用已有实验

### Q10: 如何调试LLM生成的内容？

**A**: 查看日志输出：
```bash
# 启动时显示详细日志
python -m src.api_server --log-level DEBUG

# 或查看控制台输出
```

---

## 📦 手动安装（命令行使用）

```bash
# 克隆仓库
git clone <this-repo>
cd agentsociety_backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
# 编辑 .env 文件，填入你的API密钥
```

---

## 📚 更多资源

### 相关文档

- [快速开始指南](QUICK_START.md) - 3步快速上手
- [Web UI使用指南](WEB_UI_GUIDE.md) - Web界面详细教程
- [API文档](http://localhost:8000/docs) - 交互式API文档（需启动服务器）

### 项目特点

- 🎨 **易用**: Web界面 + CLI + API 三种使用方式
- 🚀 **强大**: 基于先进LLM的智能体系统
- 🔬 **科研**: 适合社会学、心理学实验研究
- 📊 **可分析**: JSONL格式日志，方便数据分析
- 🔌 **灵活**: 支持DeepSeek、OpenAI、本地LLM等多种后端

### 应用场景

1. **社会学研究**: 研究群体行为、社会网络、从众效应
2. **心理学实验**: 模拟经典心理学实验（如斯坦福监狱实验、第三浪潮）
3. **行为分析**: 分析特定环境下的人类行为模式
4. **教育培训**: 教学演示、互动式学习材料
5. **游戏开发**: NPC行为设计、剧情生成
6. **政策模拟**: 评估政策对群体行为的影响

### 示例项目

查看 `experiments/` 目录下的示例实验：
- **第三浪潮实验**: 重现1960年代的经典社会实验
- **城市地铁-晚高峰**: 模拟公共交通场景下的人群行为
- **ThirdWaveExperiment**: 英文版第三浪潮实验

### 技术栈

- **后端**: Python 3.10+, FastAPI, Uvicorn
- **AI**: OpenAI API (兼容DeepSeek、本地LLM)
- **数据**: JSON/JSONL, Pydantic
- **前端**: HTML/CSS/JavaScript (Web UI)

### 性能优化建议

1. **智能体数量**: 10-20个最佳，30+会显著增加延迟
2. **Tick间隔**: 建议10-60秒，根据LLM响应速度调整
3. **并发控制**: 避免同时运行过多实验
4. **缓存策略**: 可以实现LLM响应缓存（自行开发）
5. **批处理**: 将相似请求批处理可减少API调用

### 安全与隐私

- ✅ 所有数据保存在本地
- ✅ API密钥仅用于LLM调用，不会上传
- ✅ 实验数据完全私有
- ⚠️ 注意保护`.env`文件，不要提交到版本控制
- ⚠️ 生产环境建议使用HTTPS

### 致谢

本项目受以下研究和项目启发：
- **The Third Wave** by Ron Jones - 经典社会心理学实验
- **Generative Agents** by Stanford - AI智能体社会模拟
- **LangChain** - LLM应用开发框架

---

## 🤝 贡献

欢迎贡献代码、报告问题、提出建议！

### 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发指南

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 代码格式化
black src/

# 类型检查
mypy src/
```

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **讨论**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: your-email@example.com

---

## ⭐ Star History

如果这个项目对你有帮助，欢迎给个 Star ⭐！

---

## 📝 更新日志

### v1.0.0 (2024-01)
- ✨ 完整的Web UI界面
- ✨ RESTful API接口
- ✨ 智能体生成与关系网络
- ✨ 情绪模型与互动系统
- ✨ 详细的日志系统
- 📚 完整的文档

### 未来计划
- [ ] 支持更多LLM后端（Claude、Gemini等）
- [ ] 可视化关系网络图
- [ ] 实时监控仪表板
- [ ] 实验模板库
- [ ] 数据分析工具集
- [ ] 多语言支持

---

**感谢使用 AgentSociety! 🎉**

开始你的社会模拟实验之旅：
```bash
# Windows
start_ui.bat

# Linux/Mac
./start_ui.sh
```

然后访问: http://localhost:8000/ui
