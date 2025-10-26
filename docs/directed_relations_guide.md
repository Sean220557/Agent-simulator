# 有向加权关系图系统使用指南

## 概述

新的有向加权关系图系统支持：
- ✅ **有向关系**：A对B的关系 ≠ B对A的关系
- ✅ **负值亲密度**：支持敌对关系（-1.0 到 1.0）
- ✅ **动态演化**：关系随事件变化
- ✅ **标准化处理**：归一化每个Agent的关系值
- ✅ **多维度分解**：信任、尊重、喜爱、依赖四个维度

## 核心概念

### 1. 亲密度 (Intimacy)

亲密度范围：**-1.0（极度敌对）到 1.0（极度亲密）**

- `1.0 到 0.7`：非常亲密（挚友、亲人）
- `0.7 到 0.3`：亲密（朋友）
- `0.3 到 -0.3`：中性（普通关系）
- `-0.3 到 -0.7`：敌对（对手）
- `-0.7 到 -1.0`：极度敌对（仇敌）

### 2. 关系维度

亲密度由四个维度组成：

```python
intimacy = trust * 0.35 + respect * 0.25 + affection * 0.30 + dependency * 0.10
```

- **信任 (Trust)**：-1.0 到 1.0，是否信任对方
- **尊重 (Respect)**：-1.0 到 1.0，是否尊重对方
- **喜爱 (Affection)**：-1.0 到 1.0，是否喜欢对方
- **依赖 (Dependency)**：-1.0 到 1.0，是否依赖对方

### 3. 互动类型及其影响

| 互动类型 | 信任影响 | 尊重影响 | 喜爱影响 | 依赖影响 |
|---------|---------|---------|---------|---------|
| cooperation（合作） | +0.8 | +0.6 | +0.4 | +0.2 |
| conflict（冲突） | -0.7 | -0.5 | -0.8 | 0.0 |
| help（帮助） | +0.6 | +0.4 | +0.7 | +0.5 |
| betrayal（背叛） | -1.0 | -0.6 | -0.9 | -0.3 |
| praise（赞美） | +0.3 | +0.7 | +0.5 | 0.0 |
| criticism（批评） | -0.2 | -0.4 | -0.3 | 0.0 |
| support（支持） | +0.5 | +0.4 | +0.6 | +0.3 |
| rejection（拒绝） | -0.4 | -0.3 | -0.8 | -0.2 |
| competition（竞争） | -0.2 | +0.3 | -0.1 | 0.0 |
| alliance（结盟） | +0.7 | +0.5 | +0.3 | +0.6 |

## 使用示例

### 1. 基础使用

```python
from src.agentsim.directed_relations import DirectedRelationGraph

# 创建关系图
graph = DirectedRelationGraph()

# 添加Agents
graph.add_agent("Alice")
graph.add_agent("Bob")

# 设置初始关系（有向）
graph.set_relation("Alice", "Bob", intimacy=0.5, relation_type="friend")
graph.set_relation("Bob", "Alice", intimacy=0.7, relation_type="friend")  # Bob对Alice更亲密

# 添加互动事件
graph.add_interaction("Alice", "Bob", "cooperation", impact=0.8, context="完成项目")

# 查询关系
relation = graph.get_relation("Alice", "Bob")
print(f"Alice对Bob的亲密度: {relation.intimacy:.3f}")
print(f"信任: {relation.trust:.3f}, 尊重: {relation.respect:.3f}")
```

### 2. 双向互动

```python
# 添加双向互动（两个方向可以有不同的影响）
graph.add_bidirectional_interaction(
    "Alice", "Bob", 
    "conflict",
    impact1=-0.6,  # Alice对Bob的影响
    impact2=-0.8,  # Bob对Alice的影响
    context="意见不合"
)
```

### 3. 标准化处理

```python
# 标准化单个Agent的所有关系
graph.normalize_agent_relations("Alice", method="minmax")

# 标准化所有Agent的关系
graph.normalize_all_agents(method="minmax")

# 支持的标准化方法：
# - "minmax": Min-Max归一化到[-1, 1]
# - "zscore": Z-score标准化
# - "softmax": Softmax归一化
```

### 4. 使用关系管理器

```python
from src.agentsim.relation_manager import RelationManager
from src.agentsim.emotion_model import EmotionGenerator

# 创建管理器
manager = RelationManager()

# 添加agents
manager.directed_graph.add_agent("Alice")
manager.directed_graph.add_agent("Bob")

# 处理带情绪的互动事件
alice_emotion = EmotionGenerator.generate_from_template("excited")
bob_emotion = EmotionGenerator.generate_from_template("hopeful")

manager.process_interaction_event(
    from_agent="Alice",
    to_agent="Bob",
    event_type="cooperation",
    from_emotion=alice_emotion,
    to_emotion=bob_emotion,
    context="成功完成项目"
)

# 获取关系摘要
summary = manager.get_mutual_relation_summary("Alice", "Bob")
print(f"不对称度: {summary['asymmetry_score']:.3f}")

# 生成报告
report = manager.generate_relation_report("Alice")
print(report)
```

## 高级功能

### 1. 时间衰减

关系会随时间自然衰减（长时间不互动会导致关系淡化）：

```python
import time

# 应用时间衰减
current_time = time.time()
graph.apply_time_decay(current_time)
```

### 2. 关系不对称性分析

```python
# 计算关系的不对称性
asymmetry = graph.get_asymmetry_score("Alice", "Bob")
print(f"不对称度: {asymmetry:.3f}")
# 0.0 = 完全对称
# 1.0 = 完全不对称
```

### 3. Agent统计信息

```python
stats = graph.get_agent_statistics("Alice")
print(f"总关系数: {stats['total_relations']}")
print(f"正面关系: {stats['positive_relations']}")
print(f"负面关系: {stats['negative_relations']}")
print(f"平均亲密度: {stats['average_intimacy']:.3f}")
print(f"最亲密的: {stats['closest_allies']}")
print(f"最敌对的: {stats['worst_enemies']}")
```

### 4. 社交画像

```python
profile = manager.get_agent_social_profile("Alice")
print(f"社交类型: {profile['social_type']}")
# 可能的类型：社交达人、友善型、孤立型、冲突型、平衡型、中立型

print(f"关系健康度: {profile['relationship_health']:.3f}")
# 0.0-1.0，越高越健康
```

### 5. 可视化

```python
# 生成关系矩阵的文本可视化
matrix_text = graph.visualize_relation_matrix()
print(matrix_text)
```

### 6. 数据导入导出

```python
# 导出到JSON
graph.export_to_json("relations.json")
manager.export_to_json("full_relations.json")

# 从字典导入
data = graph.export_to_dict()
new_graph = DirectedRelationGraph()
new_graph.import_from_dict(data)
```

## 与现有系统集成

### 从AgentPersona初始化

```python
from src.agentsim.models import AgentPersona

# 假设你有一个agents列表
agents = [...]  # List[AgentPersona]

# 初始化关系管理器
manager = RelationManager()
manager.initialize_from_agents(agents)
```

### 在模拟中使用

```python
# 在每个tick中：
# 1. 处理互动事件
manager.process_interaction_event(
    from_agent=agent1.id,
    to_agent=agent2.id,
    event_type="cooperation",
    from_emotion=agent1_emotion,
    to_emotion=agent2_emotion,
    context=interaction_context
)

# 2. 定期标准化
if tick % 10 == 0:
    manager.normalize_all_relations()

# 3. 应用时间衰减
if tick % 5 == 0:
    manager.apply_time_decay(current_time)
```

## 最佳实践

### 1. 初始化建议

- 陌生人：intimacy = 0.0
- 熟人：intimacy = 0.2 到 0.4
- 朋友：intimacy = 0.5 到 0.7
- 亲密朋友：intimacy = 0.7 到 0.9
- 对手：intimacy = -0.3 到 -0.5
- 仇敌：intimacy = -0.6 到 -1.0

### 2. 标准化时机

- 每10-20个tick标准化一次
- 在重大事件后标准化
- 避免过度频繁标准化（会抹平差异）

### 3. 时间衰减

- 建议每5-10个tick应用一次
- 衰减率可以根据模拟时间尺度调整
- 重要关系可以设置更慢的衰减率

### 4. 互动影响值

- 日常互动：impact = 0.1 到 0.3
- 重要互动：impact = 0.4 到 0.7
- 重大事件：impact = 0.7 到 1.0
- 负面事件可以使用负值

## 性能考虑

- 关系图使用字典存储，查询复杂度 O(1)
- 标准化所有agents的复杂度：O(n * m)，n=agents数量，m=平均关系数
- 建议：超过1000个agents时，考虑分批标准化

## 示例场景

### 场景1：团队合作项目

```python
# 项目开始，建立合作关系
for member in team_members:
    for other in team_members:
        if member != other:
            manager.process_interaction_event(
                member, other, "alliance",
                custom_impact=(0.5, 0.5),
                context="加入项目团队"
            )

# 项目成功
for member in team_members:
    for other in team_members:
        if member != other:
            manager.process_interaction_event(
                member, other, "cooperation",
                custom_impact=(0.8, 0.8),
                context="项目成功完成"
            )
```

### 场景2：冲突升级

```python
# 初始小冲突
manager.process_interaction_event(
    "Alice", "Bob", "criticism",
    custom_impact=(-0.3, -0.2),
    context="轻微批评"
)

# 冲突升级
manager.process_interaction_event(
    "Alice", "Bob", "conflict",
    custom_impact=(-0.7, -0.8),
    context="激烈争吵"
)

# 背叛行为
manager.process_interaction_event(
    "Alice", "Bob", "betrayal",
    custom_impact=(-1.0, -0.9),
    context="泄露秘密"
)
```

### 场景3：关系修复

```python
# 道歉
manager.process_interaction_event(
    "Alice", "Bob", "support",
    custom_impact=(0.4, 0.5),
    context="真诚道歉"
)

# 帮助
manager.process_interaction_event(
    "Alice", "Bob", "help",
    custom_impact=(0.6, 0.7),
    context="在困难时提供帮助"
)

# 重建信任
manager.process_interaction_event(
    "Alice", "Bob", "cooperation",
    custom_impact=(0.7, 0.7),
    context="共同完成任务"
)
```

## 常见问题

### Q: 如何处理单向的强烈情感？

A: 使用不同的impact值：
```python
# Alice单方面喜欢Bob
graph.add_interaction("Alice", "Bob", "conversation", impact=0.5)
graph.add_interaction("Bob", "Alice", "conversation", impact=0.1)
```

### Q: 如何表示复杂的关系（如爱恨交织）？

A: 使用关系维度的组合：
```python
relation = graph.get_relation("Alice", "Bob")
relation.affection = 0.7   # 喜爱
relation.trust = -0.3      # 不信任
relation.respect = 0.5     # 尊重
relation.update_intimacy_from_components()
```

### Q: 标准化会不会丢失信息？

A: 标准化是相对的，保留了关系的相对强弱。如果需要保留绝对值，可以：
1. 在标准化前保存原始值
2. 使用zscore方法（保留了均值和标准差信息）
3. 只在需要比较时标准化，不修改原始数据

## 总结

新的有向加权关系图系统提供了：
- 🎯 更真实的人际关系模拟
- 📊 丰富的关系分析工具
- 🔄 动态的关系演化机制
- 📈 灵活的标准化方案
- 💡 完整的社交画像系统

适用于复杂的社会模拟场景！

