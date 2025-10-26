# 快速参考卡片

## 情绪系统速查

### 创建情绪
```python
from src.agentsim.emotion_model import EmotionProfile, EmotionGenerator

# 方式1: 直接创建
emotion = EmotionProfile(valence=0.8, arousal=0.7, joy=0.9)

# 方式2: 从模板创建
emotion = EmotionGenerator.generate_from_template("excited")

# 方式3: 从上下文生成
emotion = EmotionGenerator.generate_from_context(
    "在公园遇到朋友", 
    {"description": "乐观外向"}
)
```

### 情绪维度范围
| 维度 | 范围 | 说明 |
|-----|------|-----|
| valence | -1.0 ~ 1.0 | 愉悦度 |
| arousal | -1.0 ~ 1.0 | 唤醒度 |
| dominance | -1.0 ~ 1.0 | 支配感 |
| joy, sadness, anger, fear, disgust | -0.5 ~ 1.0 | 基本情绪 |
| trust, surprise | -1.0 ~ 1.0 | 社会情绪 |
| 其他复合情绪 | -0.5 ~ 1.0 | 复合情绪 |

### 常用方法
```python
# 获取主要情绪
emotion.get_primary_emotion()  # "joy"

# 获取情绪描述
emotion.get_mood_description()  # "very joy"

# 获取情绪象限
emotion.get_emotion_quadrant()  # "excited"

# 计算相似度
similarity = emotion1.similarity(emotion2)  # 0.0 ~ 1.0

# 混合情绪
blended = emotion1.blend_with(emotion2, weight=0.5)
```

## 关系系统速查

### 创建关系图
```python
from src.agentsim.directed_relations import DirectedRelationGraph

graph = DirectedRelationGraph()
graph.add_agent("Alice")
graph.add_agent("Bob")

# 设置有向关系
graph.set_relation("Alice", "Bob", intimacy=0.5, relation_type="friend")
graph.set_relation("Bob", "Alice", intimacy=0.7, relation_type="friend")
```

### 亲密度范围
| 范围 | 关系类型 |
|-----|---------|
| 0.7 ~ 1.0 | 非常亲密 |
| 0.3 ~ 0.7 | 亲密 |
| -0.3 ~ 0.3 | 中性 |
| -0.7 ~ -0.3 | 敌对 |
| -1.0 ~ -0.7 | 极度敌对 |

### 互动事件
```python
# 单向互动
graph.add_interaction("Alice", "Bob", "help", impact=0.6, context="帮助")

# 双向互动
graph.add_bidirectional_interaction(
    "Alice", "Bob", "cooperation",
    impact1=0.8, impact2=0.7,
    context="合作"
)
```

### 互动类型速查
| 类型 | 影响 | 说明 |
|-----|------|-----|
| cooperation | +0.8 | 合作 |
| conflict | -0.7 | 冲突 |
| help | +0.6 | 帮助 |
| betrayal | -1.0 | 背叛 |
| praise | +0.5 | 赞美 |
| criticism | -0.4 | 批评 |
| support | +0.6 | 支持 |
| rejection | -0.6 | 拒绝 |
| alliance | +0.7 | 结盟 |

### 标准化
```python
# 标准化单个Agent
graph.normalize_agent_relations("Alice", method="minmax")

# 标准化所有Agent
graph.normalize_all_agents(method="minmax")

# 方法选项: "minmax", "zscore", "softmax"
```

### 查询关系
```python
# 获取关系
relation = graph.get_relation("Alice", "Bob")
print(relation.intimacy)  # 0.65
print(relation.trust)     # 0.7
print(relation.respect)   # 0.6

# 获取双向亲密度
intimacy_a_to_b, intimacy_b_to_a = graph.get_mutual_intimacy("Alice", "Bob")

# 计算不对称性
asymmetry = graph.get_asymmetry_score("Alice", "Bob")  # 0.0 ~ 1.0
```

## 关系管理器速查

### 初始化
```python
from src.agentsim.relation_manager import RelationManager

manager = RelationManager()
manager.directed_graph.add_agent("Alice")
manager.directed_graph.add_agent("Bob")
```

### 处理带情绪的互动
```python
from src.agentsim.emotion_model import EmotionGenerator

alice_emotion = EmotionGenerator.generate_from_template("excited")
bob_emotion = EmotionGenerator.generate_from_template("hopeful")

manager.process_interaction_event(
    from_agent="Alice",
    to_agent="Bob",
    event_type="cooperation",
    from_emotion=alice_emotion,
    to_emotion=bob_emotion,
    context="完成项目"
)
```

### 获取摘要
```python
# 单向关系摘要
summary = manager.get_relation_summary("Alice", "Bob")

# 双向关系摘要
mutual = manager.get_mutual_relation_summary("Alice", "Bob")
print(mutual['asymmetry_score'])  # 不对称度

# 社交画像
profile = manager.get_agent_social_profile("Alice")
print(profile['social_type'])          # "社交达人"
print(profile['relationship_health'])  # 0.85
```

### 生成报告
```python
# 关系报告
report = manager.generate_relation_report("Alice")
print(report)

# 情绪报告
from src.agentsim.emotion_model import EmotionAnalytics
emotions = [...]  # List[EmotionProfile]
report = EmotionAnalytics.generate_emotion_report(emotions, "Alice")
print(report)
```

## 常用工作流

### 工作流1: 初始化模拟
```python
# 1. 创建管理器
manager = RelationManager()

# 2. 添加所有agents
for agent in agents:
    manager.directed_graph.add_agent(agent.id)

# 3. 设置初始关系
for agent in agents:
    for other_id, rel_data in agent.relations.items():
        manager.directed_graph.set_relation(
            agent.id, other_id,
            intimacy=rel_data['strength'] * 2 - 1,
            relation_type=rel_data['type']
        )
```

### 工作流2: 模拟循环
```python
for tick in range(steps):
    # 1. 处理互动
    for interaction in tick_interactions:
        manager.process_interaction_event(
            from_agent=interaction.from_agent,
            to_agent=interaction.to_agent,
            event_type=interaction.type,
            from_emotion=interaction.from_emotion,
            to_emotion=interaction.to_emotion,
            context=interaction.context
        )
    
    # 2. 定期标准化
    if tick % 10 == 0:
        manager.normalize_all_relations()
    
    # 3. 应用时间衰减
    if tick % 5 == 0:
        manager.apply_time_decay(current_time)
```

### 工作流3: 数据导出
```python
# 导出关系数据
manager.export_to_json("relations.json")

# 导出关系矩阵
matrix_text = manager.directed_graph.visualize_relation_matrix()
with open("relation_matrix.txt", 'w') as f:
    f.write(matrix_text)

# 导出所有报告
for agent_id in agent_ids:
    report = manager.generate_relation_report(agent_id)
    with open(f"reports/{agent_id}_report.txt", 'w') as f:
        f.write(report)
```

## 调试技巧

### 检查情绪状态
```python
emotion = agent.emotion
print(f"情绪: {emotion.get_mood_description()}")
print(f"强度: {emotion.intensity:.3f}")
print(f"主要情绪: {emotion.get_primary_emotions()}")
print(f"象限: {emotion.get_emotion_quadrant()}")
```

### 检查关系状态
```python
relation = graph.get_relation("Alice", "Bob")
print(f"亲密度: {relation.intimacy:+.3f}")
print(f"信任: {relation.trust:+.3f}")
print(f"尊重: {relation.respect:+.3f}")
print(f"喜爱: {relation.affection:+.3f}")
print(f"互动: +{relation.positive_interactions} -{relation.negative_interactions}")
```

### 检查不对称性
```python
asymmetry = graph.get_asymmetry_score("Alice", "Bob")
if asymmetry > 0.5:
    print("⚠️ 关系高度不对称！")
    intimacy_a_to_b, intimacy_b_to_a = graph.get_mutual_intimacy("Alice", "Bob")
    print(f"Alice → Bob: {intimacy_a_to_b:+.3f}")
    print(f"Bob → Alice: {intimacy_b_to_a:+.3f}")
```

## 性能优化建议

### 标准化频率
```python
# ❌ 太频繁
if tick % 1 == 0:  # 每个tick都标准化
    manager.normalize_all_relations()

# ✅ 合适
if tick % 10 == 0:  # 每10个tick标准化一次
    manager.normalize_all_relations()
```

### 大规模Agent处理
```python
# 分批标准化
batch_size = 100
for i in range(0, len(agent_ids), batch_size):
    batch = agent_ids[i:i+batch_size]
    for agent_id in batch:
        graph.normalize_agent_relations(agent_id)
```

### 历史记录限制
```python
# 限制互动历史长度（在DirectedRelation.add_interaction中）
if len(self.interaction_history) > 100:
    self.interaction_history = self.interaction_history[-100:]
```

## 常见错误

### 错误1: 忘记标准化
```python
# ❌ 关系值可能超出范围
graph.add_interaction("Alice", "Bob", "cooperation", impact=0.8)
graph.add_interaction("Alice", "Bob", "cooperation", impact=0.8)
# intimacy 可能 > 1.0

# ✅ 定期标准化
graph.normalize_agent_relations("Alice")
```

### 错误2: 混淆单向和双向
```python
# ❌ 只更新了一个方向
graph.add_interaction("Alice", "Bob", "cooperation", impact=0.8)

# ✅ 使用双向互动
graph.add_bidirectional_interaction(
    "Alice", "Bob", "cooperation",
    impact1=0.8, impact2=0.7
)
```

### 错误3: 情绪维度超出范围
```python
# ❌ 手动设置可能超出范围
emotion.joy = 1.5  # 超出范围

# ✅ 使用normalize()
emotion.joy = 1.5
emotion.normalize()  # 自动限制到有效范围
```

## 测试命令

```bash
# 测试情绪系统
python -m src.agentsim.emotion_model

# 测试关系图
python -m src.agentsim.directed_relations

# 测试关系管理器
python -m src.agentsim.relation_manager
```

## 更多信息

- 详细文档: `docs/directed_relations_guide.md`
- 升级总结: `docs/emotion_and_relation_upgrade_summary.md`
- 源代码: `src/agentsim/`


