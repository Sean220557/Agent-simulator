"""
有向加权关系图模块
支持：
1. 有向关系（A对B的关系 ≠ B对A的关系）
2. 负值亲密度（支持敌对关系）
3. 动态关系演化（基于事件的关系变化）
4. 标准化处理（归一化每个Agent的关系值）
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class DirectedRelation:
    """有向关系类 - A对B的单向关系"""
    from_agent: str
    to_agent: str
    
    # 核心属性
    intimacy: float = 0.0  # 亲密度：-1.0（极度敌对）到 1.0（极度亲密）
    relation_type: str = "stranger"  # 关系类型
    
    # 关系历史
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)
    last_update_time: float = field(default_factory=lambda: datetime.now().timestamp())
    
    # 统计信息
    positive_interactions: int = 0  # 积极互动次数
    negative_interactions: int = 0  # 消极互动次数
    neutral_interactions: int = 0   # 中性互动次数
    
    # 关系强度分解
    trust: float = 0.0      # 信任度：-1.0 到 1.0
    respect: float = 0.0    # 尊重度：-1.0 到 1.0
    affection: float = 0.0  # 喜爱度：-1.0 到 1.0
    dependency: float = 0.0 # 依赖度：-1.0 到 1.0
    
    def update_intimacy_from_components(self):
        """从各个组成部分更新总体亲密度"""
        # 加权平均计算总体亲密度
        self.intimacy = (
            self.trust * 0.35 +
            self.respect * 0.25 +
            self.affection * 0.30 +
            self.dependency * 0.10
        )
        self.intimacy = max(-1.0, min(1.0, self.intimacy))
    
    def add_interaction(self, interaction_type: str, impact: float, context: str = ""):
        """添加互动记录并更新关系"""
        # 记录互动
        interaction = {
            "type": interaction_type,
            "impact": impact,
            "context": context,
            "timestamp": datetime.now().timestamp(),
            "intimacy_before": self.intimacy
        }
        
        # 更新统计
        if impact > 0.1:
            self.positive_interactions += 1
        elif impact < -0.1:
            self.negative_interactions += 1
        else:
            self.neutral_interactions += 1
        
        # 根据互动类型更新各个维度
        self._update_relation_components(interaction_type, impact)
        
        # 更新总体亲密度
        self.update_intimacy_from_components()
        
        # 记录互动后的状态
        interaction["intimacy_after"] = self.intimacy
        self.interaction_history.append(interaction)
        self.last_update_time = datetime.now().timestamp()
        
        # 限制历史记录长度
        if len(self.interaction_history) > 100:
            self.interaction_history = self.interaction_history[-100:]
    
    def _update_relation_components(self, interaction_type: str, impact: float):
        """根据互动类型更新关系各个维度"""
        # 定义不同互动类型对各维度的影响
        interaction_effects = {
            "cooperation": {"trust": 0.8, "respect": 0.6, "affection": 0.4, "dependency": 0.2},
            "conflict": {"trust": -0.7, "respect": -0.5, "affection": -0.8, "dependency": 0.0},
            "help": {"trust": 0.6, "respect": 0.4, "affection": 0.7, "dependency": 0.5},
            "betrayal": {"trust": -1.0, "respect": -0.6, "affection": -0.9, "dependency": -0.3},
            "praise": {"respect": 0.7, "affection": 0.5, "trust": 0.3, "dependency": 0.0},
            "criticism": {"respect": -0.4, "affection": -0.3, "trust": -0.2, "dependency": 0.0},
            "support": {"trust": 0.5, "affection": 0.6, "respect": 0.4, "dependency": 0.3},
            "rejection": {"affection": -0.8, "trust": -0.4, "respect": -0.3, "dependency": -0.2},
            "competition": {"respect": 0.3, "trust": -0.2, "affection": -0.1, "dependency": 0.0},
            "alliance": {"trust": 0.7, "dependency": 0.6, "respect": 0.5, "affection": 0.3},
            "conversation": {"affection": 0.2, "trust": 0.1, "respect": 0.1, "dependency": 0.0},
            "ignore": {"affection": -0.3, "trust": -0.2, "respect": -0.2, "dependency": -0.1},
        }
        
        # 获取互动效果
        effects = interaction_effects.get(interaction_type, {})
        
        # 应用影响（考虑impact强度）
        learning_rate = 0.1  # 学习率，控制变化速度
        
        for component, weight in effects.items():
            current_value = getattr(self, component)
            # 使用渐进式更新，避免剧烈变化
            change = impact * weight * learning_rate
            new_value = current_value + change
            setattr(self, component, max(-1.0, min(1.0, new_value)))
    
    def decay_over_time(self, time_passed: float):
        """关系随时间衰减（长时间不互动会导致关系淡化）"""
        # 计算衰减因子（基于时间）
        decay_rate = 0.01  # 每天衰减1%
        decay_factor = np.exp(-decay_rate * time_passed / 86400)  # 86400秒 = 1天
        
        # 关系向中性值（0.0）衰减
        self.intimacy *= decay_factor
        self.trust *= decay_factor
        self.respect *= decay_factor
        self.affection *= decay_factor
        self.dependency *= decay_factor
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "intimacy": round(self.intimacy, 4),
            "relation_type": self.relation_type,
            "trust": round(self.trust, 4),
            "respect": round(self.respect, 4),
            "affection": round(self.affection, 4),
            "dependency": round(self.dependency, 4),
            "positive_interactions": self.positive_interactions,
            "negative_interactions": self.negative_interactions,
            "neutral_interactions": self.neutral_interactions,
            "last_update_time": self.last_update_time,
            "interaction_count": len(self.interaction_history)
        }


class DirectedRelationGraph:
    """有向关系图管理器"""
    
    def __init__(self):
        # 关系图：{from_agent: {to_agent: DirectedRelation}}
        self.relations: Dict[str, Dict[str, DirectedRelation]] = {}
        self.agent_ids: List[str] = []
    
    def add_agent(self, agent_id: str):
        """添加Agent到图中"""
        if agent_id not in self.agent_ids:
            self.agent_ids.append(agent_id)
            self.relations[agent_id] = {}
    
    def get_relation(self, from_agent: str, to_agent: str) -> Optional[DirectedRelation]:
        """获取A对B的关系"""
        if from_agent in self.relations and to_agent in self.relations[from_agent]:
            return self.relations[from_agent][to_agent]
        return None
    
    def set_relation(self, from_agent: str, to_agent: str, intimacy: float = 0.0, 
                    relation_type: str = "stranger"):
        """设置A对B的关系"""
        # 确保两个Agent都在图中
        self.add_agent(from_agent)
        self.add_agent(to_agent)
        
        # 创建或更新关系
        if to_agent not in self.relations[from_agent]:
            self.relations[from_agent][to_agent] = DirectedRelation(
                from_agent=from_agent,
                to_agent=to_agent,
                intimacy=intimacy,
                relation_type=relation_type
            )
        else:
            relation = self.relations[from_agent][to_agent]
            relation.intimacy = max(-1.0, min(1.0, intimacy))
            relation.relation_type = relation_type
    
    def add_interaction(self, from_agent: str, to_agent: str, 
                       interaction_type: str, impact: float, context: str = ""):
        """记录A对B的互动，并更新关系"""
        # 确保关系存在
        if from_agent not in self.relations or to_agent not in self.relations[from_agent]:
            self.set_relation(from_agent, to_agent)
        
        # 更新关系
        relation = self.relations[from_agent][to_agent]
        relation.add_interaction(interaction_type, impact, context)
    
    def add_bidirectional_interaction(self, agent1: str, agent2: str,
                                     interaction_type: str, impact1: float, impact2: float,
                                     context: str = ""):
        """添加双向互动（A对B和B对A可能有不同的影响）"""
        self.add_interaction(agent1, agent2, interaction_type, impact1, context)
        self.add_interaction(agent2, agent1, interaction_type, impact2, context)
    
    def normalize_agent_relations(self, agent_id: str, method: str = "minmax"):
        """标准化某个Agent对所有其他Agent的关系值"""
        if agent_id not in self.relations:
            return
        
        relations = self.relations[agent_id]
        if not relations:
            return
        
        # 收集所有亲密度值
        intimacy_values = [rel.intimacy for rel in relations.values()]
        
        if not intimacy_values:
            return
        
        if method == "minmax":
            # Min-Max归一化到[-1, 1]
            min_val = min(intimacy_values)
            max_val = max(intimacy_values)
            
            if max_val > min_val:
                for relation in relations.values():
                    # 归一化到[-1, 1]
                    normalized = 2 * (relation.intimacy - min_val) / (max_val - min_val) - 1
                    relation.intimacy = normalized
        
        elif method == "zscore":
            # Z-score标准化
            mean_val = np.mean(intimacy_values)
            std_val = np.std(intimacy_values)
            
            if std_val > 0:
                for relation in relations.values():
                    z_score = (relation.intimacy - mean_val) / std_val
                    # 映射到[-1, 1]，使用tanh函数
                    relation.intimacy = np.tanh(z_score)
        
        elif method == "softmax":
            # Softmax归一化（保持相对大小）
            exp_values = np.exp(intimacy_values)
            sum_exp = np.sum(exp_values)
            
            for i, (to_agent, relation) in enumerate(relations.items()):
                # Softmax后映射到[-1, 1]
                softmax_val = exp_values[i] / sum_exp
                relation.intimacy = 2 * softmax_val - 1
    
    def normalize_all_agents(self, method: str = "minmax"):
        """标准化所有Agent的关系值"""
        for agent_id in self.agent_ids:
            self.normalize_agent_relations(agent_id, method)
    
    def get_mutual_intimacy(self, agent1: str, agent2: str) -> Tuple[float, float]:
        """获取双向的亲密度（A对B，B对A）"""
        intimacy_1_to_2 = 0.0
        intimacy_2_to_1 = 0.0
        
        rel_1_to_2 = self.get_relation(agent1, agent2)
        if rel_1_to_2:
            intimacy_1_to_2 = rel_1_to_2.intimacy
        
        rel_2_to_1 = self.get_relation(agent2, agent1)
        if rel_2_to_1:
            intimacy_2_to_1 = rel_2_to_1.intimacy
        
        return intimacy_1_to_2, intimacy_2_to_1
    
    def get_asymmetry_score(self, agent1: str, agent2: str) -> float:
        """计算关系的不对称性（0表示完全对称，1表示完全不对称）"""
        intimacy_1_to_2, intimacy_2_to_1 = self.get_mutual_intimacy(agent1, agent2)
        return abs(intimacy_1_to_2 - intimacy_2_to_1) / 2.0
    
    def apply_time_decay(self, current_time: float):
        """对所有关系应用时间衰减"""
        for agent_id, relations in self.relations.items():
            for to_agent, relation in relations.items():
                time_passed = current_time - relation.last_update_time
                if time_passed > 0:
                    relation.decay_over_time(time_passed)
    
    def get_agent_statistics(self, agent_id: str) -> Dict[str, Any]:
        """获取Agent的关系统计信息"""
        if agent_id not in self.relations:
            return {"error": "Agent not found"}
        
        relations = self.relations[agent_id]
        
        # 统计信息
        intimacy_values = [rel.intimacy for rel in relations.values()]
        positive_relations = [v for v in intimacy_values if v > 0.3]
        negative_relations = [v for v in intimacy_values if v < -0.3]
        neutral_relations = [v for v in intimacy_values if -0.3 <= v <= 0.3]
        
        # 找出最亲密和最敌对的关系
        sorted_relations = sorted(relations.items(), key=lambda x: x[1].intimacy, reverse=True)
        
        stats = {
            "agent_id": agent_id,
            "total_relations": len(relations),
            "positive_relations": len(positive_relations),
            "negative_relations": len(negative_relations),
            "neutral_relations": len(neutral_relations),
            "average_intimacy": np.mean(intimacy_values) if intimacy_values else 0.0,
            "intimacy_std": np.std(intimacy_values) if intimacy_values else 0.0,
            "closest_allies": [(to_agent, rel.intimacy) for to_agent, rel in sorted_relations[:3]],
            "worst_enemies": [(to_agent, rel.intimacy) for to_agent, rel in sorted_relations[-3:]],
        }
        
        return stats
    
    def export_to_dict(self) -> Dict[str, Any]:
        """导出整个关系图为字典"""
        export_data = {
            "agents": self.agent_ids,
            "relations": {}
        }
        
        for from_agent, relations in self.relations.items():
            export_data["relations"][from_agent] = {
                to_agent: relation.to_dict()
                for to_agent, relation in relations.items()
            }
        
        return export_data
    
    def export_to_json(self, filepath: str):
        """导出关系图到JSON文件"""
        data = self.export_to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_from_dict(self, data: Dict[str, Any]):
        """从字典导入关系图"""
        self.agent_ids = data.get("agents", [])
        self.relations = {}
        
        for from_agent, relations in data.get("relations", {}).items():
            self.relations[from_agent] = {}
            for to_agent, rel_data in relations.items():
                relation = DirectedRelation(
                    from_agent=from_agent,
                    to_agent=to_agent,
                    intimacy=rel_data.get("intimacy", 0.0),
                    relation_type=rel_data.get("relation_type", "stranger")
                )
                relation.trust = rel_data.get("trust", 0.0)
                relation.respect = rel_data.get("respect", 0.0)
                relation.affection = rel_data.get("affection", 0.0)
                relation.dependency = rel_data.get("dependency", 0.0)
                relation.positive_interactions = rel_data.get("positive_interactions", 0)
                relation.negative_interactions = rel_data.get("negative_interactions", 0)
                relation.neutral_interactions = rel_data.get("neutral_interactions", 0)
                
                self.relations[from_agent][to_agent] = relation
    
    def visualize_relation_matrix(self) -> str:
        """生成关系矩阵的文本可视化"""
        if not self.agent_ids:
            return "No agents in graph"
        
        # 创建矩阵
        n = len(self.agent_ids)
        matrix = np.zeros((n, n))
        
        for i, from_agent in enumerate(self.agent_ids):
            for j, to_agent in enumerate(self.agent_ids):
                if i != j:
                    relation = self.get_relation(from_agent, to_agent)
                    if relation:
                        matrix[i][j] = relation.intimacy
        
        # 生成文本表示
        lines = ["关系矩阵（行：from, 列：to）:"]
        lines.append("=" * 80)
        
        # 表头
        header = "Agent".ljust(15) + " | " + " ".join([f"{aid[:8]:>8}" for aid in self.agent_ids])
        lines.append(header)
        lines.append("-" * 80)
        
        # 矩阵内容
        for i, from_agent in enumerate(self.agent_ids):
            row = f"{from_agent[:15]:15} | "
            for j in range(n):
                if i == j:
                    row += "    -   "
                else:
                    val = matrix[i][j]
                    color = "+" if val > 0 else "-" if val < 0 else " "
                    row += f"{color}{abs(val):>6.3f} "
            lines.append(row)
        
        return "\n".join(lines)


def demonstrate_directed_relations():
    """演示有向关系图系统"""
    print("=== 有向加权关系图演示 ===\n")
    
    # 创建关系图
    graph = DirectedRelationGraph()
    
    # 添加Agents
    agents = ["Alice", "Bob", "Charlie", "David"]
    for agent in agents:
        graph.add_agent(agent)
    
    # 设置初始关系
    print("1. 设置初始关系:")
    graph.set_relation("Alice", "Bob", intimacy=0.5, relation_type="friend")
    graph.set_relation("Bob", "Alice", intimacy=0.6, relation_type="friend")  # Bob对Alice更亲密
    
    graph.set_relation("Alice", "Charlie", intimacy=0.2, relation_type="acquaintance")
    graph.set_relation("Charlie", "Alice", intimacy=-0.1, relation_type="acquaintance")  # Charlie不太喜欢Alice
    
    graph.set_relation("Alice", "David", intimacy=-0.3, relation_type="rival")
    graph.set_relation("David", "Alice", intimacy=-0.5, relation_type="rival")  # David更讨厌Alice
    
    print("初始关系矩阵:")
    print(graph.visualize_relation_matrix())
    print()
    
    # 模拟互动事件
    print("2. 模拟互动事件:")
    
    # Alice和Bob合作
    print("  - Alice和Bob合作（双方都获得正面影响）")
    graph.add_bidirectional_interaction("Alice", "Bob", "cooperation", 
                                       impact1=0.8, impact2=0.7, 
                                       context="成功完成项目")
    
    # Alice和Charlie发生冲突
    print("  - Alice和Charlie发生冲突")
    graph.add_bidirectional_interaction("Alice", "Charlie", "conflict",
                                       impact1=-0.6, impact2=-0.8,  # Charlie受影响更大
                                       context="意见不合")
    
    # David帮助Alice
    print("  - David帮助了Alice（单向正面影响）")
    graph.add_interaction("Alice", "David", "help", impact=0.5, context="David提供了帮助")
    graph.add_interaction("David", "Alice", "help", impact=0.3, context="Alice接受了帮助")
    
    print("\n互动后的关系矩阵:")
    print(graph.visualize_relation_matrix())
    print()
    
    # 标准化处理
    print("3. 标准化处理:")
    print("  对Alice的所有关系进行Min-Max标准化...")
    graph.normalize_agent_relations("Alice", method="minmax")
    
    print("\n标准化后的关系矩阵:")
    print(graph.visualize_relation_matrix())
    print()
    
    # 统计信息
    print("4. Agent统计信息:")
    for agent in agents:
        stats = graph.get_agent_statistics(agent)
        print(f"\n{agent}的关系统计:")
        print(f"  总关系数: {stats['total_relations']}")
        print(f"  正面关系: {stats['positive_relations']}, 负面关系: {stats['negative_relations']}")
        print(f"  平均亲密度: {stats['average_intimacy']:.3f}")
        print(f"  最亲密的: {stats['closest_allies']}")
        print(f"  最敌对的: {stats['worst_enemies']}")
    
    # 关系不对称性
    print("\n5. 关系不对称性分析:")
    for i, agent1 in enumerate(agents):
        for agent2 in agents[i+1:]:
            intimacy_1_to_2, intimacy_2_to_1 = graph.get_mutual_intimacy(agent1, agent2)
            asymmetry = graph.get_asymmetry_score(agent1, agent2)
            print(f"  {agent1} -> {agent2}: {intimacy_1_to_2:+.3f}")
            print(f"  {agent2} -> {agent1}: {intimacy_2_to_1:+.3f}")
            print(f"  不对称度: {asymmetry:.3f}\n")
    
    # 导出数据
    print("6. 导出关系数据:")
    export_path = "directed_relations_demo.json"
    graph.export_to_json(export_path)
    print(f"  关系图已导出到: {export_path}")
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    demonstrate_directed_relations()

