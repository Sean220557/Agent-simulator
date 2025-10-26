# 情绪与关系系统全面升级总结

## 🎯 升级概览

本次升级对Agent社会模拟系统的**情绪系统**和**关系系统**进行了全面重构，使其更加科学、丰富和动态。

## 📊 升级内容

### 一、情绪系统升级 (emotion_model.py)

#### 1. 理论基础
基于多个心理学理论构建：
- **PAD情绪模型** (Mehrabian & Russell)：三维情绪空间
- **基本情绪理论** (Ekman)：6种基本情绪
- **Plutchik情绪轮盘**：8种基本情绪及复合形式
- **认知评估理论** (Lazarus)：情绪源于情境评估
- **社会学情绪理论** (Hochschild)：情绪的社会建构

#### 2. 核心特性

**多维情绪支持（19个维度）**
```python
@dataclass
class EmotionProfile:
    # PAD三维模型
    valence: float = 0.0      # 愉悦度: -1.0 到 1.0
    arousal: float = 0.0      # 唤醒度: -1.0 到 1.0
    dominance: float = 0.0    # 支配感: -1.0 到 1.0
    
    # 基本情绪（支持负值）
    joy: float = 0.0          # -0.5 到 1.0
    sadness: float = 0.0      # -0.5 到 1.0
    anger: float = 0.0        # -0.5 到 1.0
    fear: float = 0.0         # -0.5 到 1.0
    surprise: float = 0.0     # -1.0 到 1.0
    disgust: float = 0.0      # -0.5 到 1.0
    
    # 社会情绪
    trust: float = 0.0        # -1.0 到 1.0
    anticipation: float = 0.0 # -0.5 到 1.0
    
    # 复合情绪
    optimism: float = 0.0     # -0.5 到 1.0
    anxiety: float = 0.0      # -0.5 到 1.0
    guilt: float = 0.0        # -0.5 到 1.0
    pride: float = 0.0        # -0.5 到 1.0
    shame: float = 0.0        # -0.5 到 1.0
    envy: float = 0.0         # -0.5 到 1.0
    gratitude: float = 0.0    # -0.5 到 1.0
    hope: float = 0.0         # -0.5 到 1.0
```

**智能情绪生成**
- 基于人格特质的情绪生成
- 上下文敏感的情绪分析
- 情绪演化和衰减机制
- 情绪稳定性计算

**情绪分析工具**
- 情绪相似度计算
- 情绪混合和插值
- 情绪象限分析
- 情绪平衡分析

**可视化支持**
- 情绪热力图数据
- 情绪时间线数据
- 情绪雷达图数据
- 情绪模式分析

#### 3. 新增情绪模板（25+种）

基础情绪：
- neutral, calm, excited, anxious, angry, sad, fearful, surprised, disgusted

社会情绪：
- trusting, suspicious, confident, shy

复合情绪：
- hopeful, guilty, proud, envious, grateful

认知评估情绪：
- threatened, challenged, supported, ignored

### 二、关系系统升级 (directed_relations.py)

#### 1. 核心特性

**有向加权关系图**
```python
@dataclass
class DirectedRelation:
    from_agent: str
    to_agent: str
    intimacy: float = 0.0  # -1.0（极度敌对）到 1.0（极度亲密）
    
    # 关系维度分解
    trust: float = 0.0      # 信任度
    respect: float = 0.0    # 尊重度
    affection: float = 0.0  # 喜爱度
    dependency: float = 0.0 # 依赖度
```

**关系计算公式**
```python
intimacy = trust * 0.35 + respect * 0.25 + affection * 0.30 + dependency * 0.10
```

#### 2. 动态演化机制

**12种互动类型**
| 互动类型 | 效果 |
|---------|------|
| cooperation | 提升信任、尊重、喜爱 |
| conflict | 降低信任、尊重、喜爱 |
| help | 提升喜爱、信任、依赖 |
| betrayal | 严重降低信任和喜爱 |
| praise | 提升尊重和喜爱 |
| criticism | 降低尊重和喜爱 |
| support | 提升信任、喜爱、依赖 |
| rejection | 严重降低喜爱 |
| competition | 提升尊重，轻微降低信任 |
| alliance | 提升信任和依赖 |
| conversation | 轻微提升各维度 |
| ignore | 轻微降低各维度 |

**时间衰减**
```python
# 关系随时间自然衰减
decay_rate = 0.01  # 每天衰减1%
```

#### 3. 标准化处理

支持三种标准化方法：
- **Min-Max归一化**：映射到[-1, 1]
- **Z-score标准化**：基于均值和标准差
- **Softmax归一化**：保持相对大小

#### 4. 分析工具

**关系不对称性**
```python
asymmetry_score = abs(intimacy_A_to_B - intimacy_B_to_A) / 2.0
```

**Agent统计**
- 总关系数
- 正面/负面/中性关系数量
- 平均亲密度和标准差
- 最亲密和最敌对的关系

**社交画像**
- 社交类型：社交达人、友善型、孤立型、冲突型、平衡型、中立型
- 关系健康度：0.0-1.0

### 三、关系管理器 (relation_manager.py)

统一管理情绪和关系的集成系统：

```python
class RelationManager:
    def process_interaction_event(
        self,
        from_agent: str,
        to_agent: str,
        event_type: str,
        from_emotion: EmotionProfile,
        to_emotion: EmotionProfile,
        context: str
    ):
        """处理带情绪的互动事件"""
        # 1. 根据情绪调整影响值
        # 2. 更新有向关系
        # 3. 记录情绪历史
```

**特色功能**
- 情绪影响关系变化的强度
- 情绪历史追踪
- 双向关系摘要
- 社交画像生成
- 关系报告生成

## 🚀 使用示例

### 快速开始

```python
from src.agentsim.relation_manager import RelationManager
from src.agentsim.emotion_model import EmotionGenerator

# 1. 创建管理器
manager = RelationManager()

# 2. 添加agents
manager.directed_graph.add_agent("Alice")
manager.directed_graph.add_agent("Bob")

# 3. 设置初始关系（有向）
manager.directed_graph.set_relation("Alice", "Bob", intimacy=0.5)
manager.directed_graph.set_relation("Bob", "Alice", intimacy=0.7)  # 不对称

# 4. 处理互动事件
alice_emotion = EmotionGenerator.generate_from_template("excited")
bob_emotion = EmotionGenerator.generate_from_template("hopeful")

manager.process_interaction_event(
    "Alice", "Bob", "cooperation",
    alice_emotion, bob_emotion,
    "成功完成项目"
)

# 5. 标准化关系
manager.normalize_all_relations()

# 6. 生成报告
report = manager.generate_relation_report("Alice")
print(report)
```

### 情绪系统示例

```python
from src.agentsim.emotion_model import EmotionProfile, EmotionGenerator, EmotionAnalytics

# 创建复杂情绪
emotion = EmotionProfile(
    valence=0.6,      # 正面
    arousal=0.8,      # 高度兴奋
    joy=0.9,          # 非常快乐
    anxiety=0.3,      # 轻微焦虑
    hope=0.7,         # 充满希望
    context="重要面试前"
)

# 情绪分析
print(emotion.get_mood_description())  # "very joy and hope"
print(emotion.get_emotion_quadrant())  # "excited"
print(emotion.intensity)               # 0.45

# 情绪演化
personality = {"description": "乐观外向的人"}
new_context = "面试成功"
evolved = EmotionGenerator.evolve_emotion(emotion, new_context, personality)

# 生成分析报告
emotions_history = [emotion, evolved]
report = EmotionAnalytics.generate_emotion_report(emotions_history, "Alice")
print(report)
```

## 📈 性能优化

### 数据结构
- 关系图使用嵌套字典：O(1)查询复杂度
- 情绪历史限制长度：最多保留100条记录

### 标准化策略
- 建议每10-20个tick标准化一次
- 超过1000个agents时分批处理

### 时间衰减
- 建议每5-10个tick应用一次
- 可根据模拟时间尺度调整衰减率

## 🔧 集成指南

### 与现有系统集成

```python
# 1. 从AgentPersona初始化
from src.agentsim.models import AgentPersona

agents = [...]  # List[AgentPersona]
manager = RelationManager()
manager.initialize_from_agents(agents)

# 2. 在模拟循环中使用
for tick in range(simulation_steps):
    # 处理互动
    for interaction in tick_interactions:
        manager.process_interaction_event(...)
    
    # 定期标准化
    if tick % 10 == 0:
        manager.normalize_all_relations()
    
    # 应用时间衰减
    if tick % 5 == 0:
        manager.apply_time_decay(current_time)
```

### 数据持久化

```python
# 导出
manager.export_to_json("relations.json")

# 导入
new_manager = RelationManager()
with open("relations.json", 'r') as f:
    data = json.load(f)
new_manager.directed_graph.import_from_dict(data["directed_graph"])
```

## 📚 文档

- **详细使用指南**：`docs/directed_relations_guide.md`
- **API文档**：见各模块的docstring
- **示例代码**：各模块的`__main__`部分

## 🎓 理论支持

### 心理学理论
1. **PAD情绪模型** - Mehrabian & Russell (1974)
2. **基本情绪理论** - Ekman (1992)
3. **Plutchik情绪轮盘** - Plutchik (1980)
4. **认知评估理论** - Lazarus (1991)

### 社会学理论
1. **情绪劳动** - Hochschild (1983)
2. **社会网络理论** - Granovetter (1973)
3. **社会资本理论** - Bourdieu (1986)

## 🔬 测试与验证

所有模块都包含演示函数：

```bash
# 测试情绪系统
python -m src.agentsim.emotion_model

# 测试有向关系图
python -m src.agentsim.directed_relations

# 测试关系管理器
python -m src.agentsim.relation_manager
```

## 📊 数据格式

### 情绪数据格式
```json
{
  "valence": 0.6,
  "arousal": 0.8,
  "dominance": 0.4,
  "joy": 0.9,
  "sadness": 0.0,
  "anger": 0.0,
  "fear": 0.1,
  "surprise": 0.2,
  "disgust": 0.0,
  "trust": 0.7,
  "anticipation": 0.6,
  "optimism": 0.8,
  "anxiety": 0.3,
  "guilt": 0.0,
  "pride": 0.5,
  "shame": 0.0,
  "envy": 0.0,
  "gratitude": 0.4,
  "hope": 0.7,
  "intensity": 0.45,
  "timestamp": 1234567890.123,
  "context": "重要面试前"
}
```

### 关系数据格式
```json
{
  "from_agent": "Alice",
  "to_agent": "Bob",
  "intimacy": 0.65,
  "relation_type": "friend",
  "trust": 0.7,
  "respect": 0.6,
  "affection": 0.8,
  "dependency": 0.3,
  "positive_interactions": 15,
  "negative_interactions": 2,
  "neutral_interactions": 8,
  "last_update_time": 1234567890.123,
  "interaction_count": 25
}
```

## 🎯 应用场景

### 1. 社会模拟
- 社区动态模拟
- 组织行为研究
- 社会网络演化

### 2. 游戏AI
- NPC情绪系统
- 动态关系网络
- 角色互动系统

### 3. 心理学研究
- 情绪传染研究
- 社会影响研究
- 关系动力学研究

### 4. 教育模拟
- 课堂互动模拟
- 团队协作训练
- 冲突解决演练

## 🔮 未来扩展

### 计划中的功能
- [ ] 群体情绪动力学
- [ ] 情绪传染模型
- [ ] 关系网络可视化（图形界面）
- [ ] 机器学习驱动的情绪预测
- [ ] 文化差异的情绪模型

### 性能优化
- [ ] 大规模Agent的并行处理
- [ ] 关系图的稀疏矩阵优化
- [ ] 增量式标准化算法

## 📝 更新日志

### v2.0.0 (2025-10-16)
- ✨ 新增19维情绪模型
- ✨ 新增有向加权关系图
- ✨ 新增关系管理器
- ✨ 支持负值情绪和关系
- ✨ 新增标准化处理
- ✨ 新增情绪分析工具
- ✨ 新增社交画像系统
- 📚 完善文档和示例

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

## 📄 许可

本项目遵循原项目的许可协议。

---

**升级完成！** 🎉

现在您的Agent社会模拟系统拥有了：
- 🧠 科学的多维情绪模型
- 🔗 真实的有向关系网络
- 📊 强大的分析工具
- 🎯 灵活的标准化方案
- 💡 完整的社交画像系统

开始构建更真实的虚拟社会吧！


