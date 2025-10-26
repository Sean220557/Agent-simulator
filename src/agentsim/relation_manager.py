"""
关系管理器 - 整合有向关系图和情绪关系系统
提供统一的接口来管理Agent之间的复杂关系
"""

from typing import Dict, List, Any, Optional, Tuple
from .directed_relations import DirectedRelationGraph, DirectedRelation
from .emotion_model import EmotionProfile
from .models import AgentPersona
import json
import numpy as np


class RelationManager:
    """关系管理器 - 统一管理有向关系和情绪关系"""
    
    def __init__(self):
        self.directed_graph = DirectedRelationGraph()
        self.emotion_history: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    
    def initialize_from_agents(self, agents: List[AgentPersona]):
        """从Agent列表初始化关系图"""
        # 添加所有agents
        for agent in agents:
            self.directed_graph.add_agent(agent.id)
        
        # 导入现有关系（转换为有向关系）
        for agent in agents:
            if not agent.relations:
                continue
            
            for other_id, relation_data in agent.relations.items():
                # 获取关系类型和强度
                rel_type = relation_data.get("type", "stranger")
                strength = float(relation_data.get("strength", 0.0))
                
                # 将strength (0-1) 映射到intimacy (-1 to 1)
                # 假设原始strength是正面关系，映射到[0, 1]
                intimacy = strength * 2 - 1  # 0->-1, 0.5->0, 1->1
                
                # 设置有向关系
                self.directed_graph.set_relation(
                    agent.id, other_id, 
                    intimacy=intimacy,
                    relation_type=rel_type
                )
    
    def process_interaction_event(
        self,
        from_agent: str,
        to_agent: str,
        event_type: str,
        from_emotion: Optional[EmotionProfile] = None,
        to_emotion: Optional[EmotionProfile] = None,
        context: str = "",
        custom_impact: Optional[Tuple[float, float]] = None
    ):
        """
        处理互动事件，更新双向关系
        
        Args:
            from_agent: 发起者
            to_agent: 接收者
            event_type: 事件类型 (cooperation, conflict, help, etc.)
            from_emotion: 发起者的情绪
            to_emotion: 接收者的情绪
            context: 事件上下文
            custom_impact: 自定义影响值 (impact1, impact2)，如果为None则自动计算
        """
        # 计算影响值
        if custom_impact:
            impact1, impact2 = custom_impact
        else:
            impact1, impact2 = self._calculate_interaction_impact(
                event_type, from_emotion, to_emotion
            )
        
        # 更新有向关系
        self.directed_graph.add_bidirectional_interaction(
            from_agent, to_agent,
            event_type, impact1, impact2,
            context
        )
        
        # 记录情绪历史
        if from_emotion and to_emotion:
            key = (from_agent, to_agent)
            if key not in self.emotion_history:
                self.emotion_history[key] = []
            
            self.emotion_history[key].append({
                "event_type": event_type,
                "context": context,
                "from_emotion": from_emotion.to_dict(),
                "to_emotion": to_emotion.to_dict(),
                "impact1": impact1,
                "impact2": impact2
            })
    
    def _calculate_interaction_impact(
        self,
        event_type: str,
        from_emotion: Optional[EmotionProfile],
        to_emotion: Optional[EmotionProfile]
    ) -> Tuple[float, float]:
        """根据事件类型和情绪计算互动影响"""
        # 基础影响值
        base_impacts = {
            "cooperation": (0.8, 0.8),
            "conflict": (-0.7, -0.7),
            "help": (0.6, 0.5),
            "betrayal": (-1.0, -0.9),
            "praise": (0.5, 0.6),
            "criticism": (-0.4, -0.5),
            "support": (0.6, 0.7),
            "rejection": (-0.6, -0.8),
            "competition": (0.2, 0.2),
            "alliance": (0.7, 0.7),
            "conversation": (0.2, 0.2),
            "ignore": (-0.3, -0.4),
        }
        
        impact1, impact2 = base_impacts.get(event_type, (0.0, 0.0))
        
        # 根据情绪调整影响
        if from_emotion and to_emotion:
            # 情绪一致性增强正面影响
            emotion_similarity = from_emotion.similarity(to_emotion)
            
            if impact1 > 0:
                impact1 *= (1 + emotion_similarity * 0.3)
            else:
                impact1 *= (1 + (1 - emotion_similarity) * 0.3)
            
            if impact2 > 0:
                impact2 *= (1 + emotion_similarity * 0.3)
            else:
                impact2 *= (1 + (1 - emotion_similarity) * 0.3)
            
            # 情绪强度影响
            avg_intensity = (from_emotion.intensity + to_emotion.intensity) / 2
            impact1 *= (0.7 + avg_intensity * 0.3)
            impact2 *= (0.7 + avg_intensity * 0.3)
        
        return impact1, impact2
    
    def get_relation_summary(self, from_agent: str, to_agent: str) -> Dict[str, Any]:
        """获取A对B的关系摘要"""
        relation = self.directed_graph.get_relation(from_agent, to_agent)
        
        if not relation:
            return {"exists": False}
        
        summary = relation.to_dict()
        summary["exists"] = True
        
        # 添加情绪历史摘要
        key = (from_agent, to_agent)
        if key in self.emotion_history:
            history = self.emotion_history[key]
            summary["emotion_interactions"] = len(history)
            
            # 最近的情绪互动
            if history:
                recent = history[-1]
                summary["last_emotion_interaction"] = {
                    "event_type": recent["event_type"],
                    "context": recent["context"],
                    "from_emotion": recent["from_emotion"]["primary_emotions"] if "primary_emotions" in recent["from_emotion"] else "unknown",
                    "to_emotion": recent["to_emotion"]["primary_emotions"] if "primary_emotions" in recent["to_emotion"] else "unknown"
                }
        
        return summary
    
    def get_mutual_relation_summary(self, agent1: str, agent2: str) -> Dict[str, Any]:
        """获取双向关系摘要"""
        rel_1_to_2 = self.get_relation_summary(agent1, agent2)
        rel_2_to_1 = self.get_relation_summary(agent2, agent1)
        
        intimacy_1_to_2, intimacy_2_to_1 = self.directed_graph.get_mutual_intimacy(agent1, agent2)
        asymmetry = self.directed_graph.get_asymmetry_score(agent1, agent2)
        
        return {
            f"{agent1}_to_{agent2}": rel_1_to_2,
            f"{agent2}_to_{agent1}": rel_2_to_1,
            "mutual_intimacy": {
                f"{agent1}_to_{agent2}": intimacy_1_to_2,
                f"{agent2}_to_{agent1}": intimacy_2_to_1
            },
            "asymmetry_score": asymmetry,
            "relationship_balance": "symmetric" if asymmetry < 0.2 else "slightly_asymmetric" if asymmetry < 0.5 else "highly_asymmetric"
        }
    
    def normalize_all_relations(self, method: str = "minmax"):
        """标准化所有Agent的关系"""
        self.directed_graph.normalize_all_agents(method)
    
    def apply_time_decay(self, current_time: float):
        """应用时间衰减"""
        self.directed_graph.apply_time_decay(current_time)
    
    def get_agent_social_profile(self, agent_id: str) -> Dict[str, Any]:
        """获取Agent的社交画像"""
        stats = self.directed_graph.get_agent_statistics(agent_id)
        
        if "error" in stats:
            return stats
        
        # 扩展社交画像
        profile = {
            **stats,
            "social_type": self._determine_social_type(stats),
            "relationship_health": self._calculate_relationship_health(stats)
        }
        
        return profile
    
    def _determine_social_type(self, stats: Dict[str, Any]) -> str:
        """根据统计数据判断社交类型"""
        avg_intimacy = stats["average_intimacy"]
        positive_ratio = stats["positive_relations"] / max(stats["total_relations"], 1)
        negative_ratio = stats["negative_relations"] / max(stats["total_relations"], 1)
        
        if positive_ratio > 0.7:
            return "社交达人" if avg_intimacy > 0.5 else "友善型"
        elif negative_ratio > 0.5:
            return "孤立型" if avg_intimacy < -0.3 else "冲突型"
        elif positive_ratio > 0.4 and negative_ratio < 0.2:
            return "平衡型"
        else:
            return "中立型"
    
    def _calculate_relationship_health(self, stats: Dict[str, Any]) -> float:
        """计算关系健康度 (0-1)"""
        # 基于正面关系比例、平均亲密度和标准差
        positive_ratio = stats["positive_relations"] / max(stats["total_relations"], 1)
        avg_intimacy_normalized = (stats["average_intimacy"] + 1) / 2  # 归一化到[0,1]
        stability = 1 - min(stats["intimacy_std"], 1.0)  # 标准差越小越稳定
        
        health = (positive_ratio * 0.4 + avg_intimacy_normalized * 0.4 + stability * 0.2)
        return max(0.0, min(1.0, health))
    
    def export_to_json(self, filepath: str):
        """导出完整的关系数据"""
        data = {
            "directed_graph": self.directed_graph.export_to_dict(),
            "emotion_history": {
                f"{k[0]}->{k[1]}": v for k, v in self.emotion_history.items()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def generate_relation_report(self, agent_id: str) -> str:
        """生成Agent的关系报告"""
        profile = self.get_agent_social_profile(agent_id)
        
        if "error" in profile:
            return f"无法生成报告: {profile['error']}"
        
        report = []
        report.append(f"=== {agent_id} 的关系报告 ===")
        report.append("=" * 60)
        report.append("")
        
        # 基本统计
        report.append("基本统计:")
        report.append(f"  总关系数: {profile['total_relations']}")
        report.append(f"  正面关系: {profile['positive_relations']} ({profile['positive_relations']/max(profile['total_relations'],1)*100:.1f}%)")
        report.append(f"  负面关系: {profile['negative_relations']} ({profile['negative_relations']/max(profile['total_relations'],1)*100:.1f}%)")
        report.append(f"  中性关系: {profile['neutral_relations']} ({profile['neutral_relations']/max(profile['total_relations'],1)*100:.1f}%)")
        report.append("")
        
        # 社交特征
        report.append("社交特征:")
        report.append(f"  平均亲密度: {profile['average_intimacy']:+.3f}")
        report.append(f"  亲密度标准差: {profile['intimacy_std']:.3f}")
        report.append(f"  社交类型: {profile['social_type']}")
        report.append(f"  关系健康度: {profile['relationship_health']:.3f} ({'健康' if profile['relationship_health'] > 0.7 else '一般' if profile['relationship_health'] > 0.4 else '需要改善'})")
        report.append("")
        
        # 最亲密的关系
        report.append("最亲密的关系:")
        for to_agent, intimacy in profile['closest_allies']:
            relation = self.directed_graph.get_relation(agent_id, to_agent)
            if relation:
                report.append(f"  → {to_agent}: {intimacy:+.3f} ({relation.relation_type})")
                report.append(f"    信任: {relation.trust:+.3f}, 尊重: {relation.respect:+.3f}, 喜爱: {relation.affection:+.3f}")
        report.append("")
        
        # 最敌对的关系
        if profile['worst_enemies'] and profile['worst_enemies'][0][1] < -0.1:
            report.append("最敌对的关系:")
            for to_agent, intimacy in profile['worst_enemies']:
                if intimacy < -0.1:
                    relation = self.directed_graph.get_relation(agent_id, to_agent)
                    if relation:
                        report.append(f"  → {to_agent}: {intimacy:+.3f} ({relation.relation_type})")
                        report.append(f"    信任: {relation.trust:+.3f}, 尊重: {relation.respect:+.3f}, 喜爱: {relation.affection:+.3f}")
            report.append("")
        
        return "\n".join(report)


def demonstrate_relation_manager():
    """演示关系管理器"""
    print("=== 关系管理器演示 ===\n")
    
    # 创建关系管理器
    manager = RelationManager()
    
    # 模拟agents
    from .emotion_model import EmotionGenerator
    
    agents = ["Alice", "Bob", "Charlie", "David", "Eve"]
    for agent in agents:
        manager.directed_graph.add_agent(agent)
    
    # 设置初始关系
    print("1. 设置初始关系...")
    manager.directed_graph.set_relation("Alice", "Bob", 0.6, "friend")
    manager.directed_graph.set_relation("Bob", "Alice", 0.5, "friend")
    manager.directed_graph.set_relation("Alice", "Charlie", -0.2, "rival")
    manager.directed_graph.set_relation("Charlie", "Alice", -0.4, "rival")
    manager.directed_graph.set_relation("Alice", "David", 0.3, "coworker")
    manager.directed_graph.set_relation("David", "Alice", 0.7, "coworker")
    print("完成\n")
    
    # 模拟互动事件
    print("2. 模拟互动事件...")
    
    # Alice和Bob合作
    alice_emotion = EmotionGenerator.generate_from_template("excited", context="合作项目")
    bob_emotion = EmotionGenerator.generate_from_template("hopeful", context="合作项目")
    
    manager.process_interaction_event(
        "Alice", "Bob", "cooperation",
        alice_emotion, bob_emotion,
        "成功完成重要项目"
    )
    print("  ✓ Alice和Bob合作")
    
    # Alice和Charlie冲突
    alice_emotion = EmotionGenerator.generate_from_template("angry", context="争论")
    charlie_emotion = EmotionGenerator.generate_from_template("angry", context="争论")
    
    manager.process_interaction_event(
        "Alice", "Charlie", "conflict",
        alice_emotion, charlie_emotion,
        "在会议上发生激烈争论"
    )
    print("  ✓ Alice和Charlie冲突")
    
    # David帮助Alice
    david_emotion = EmotionGenerator.generate_from_template("supportive", context="提供帮助")
    alice_emotion = EmotionGenerator.generate_from_template("grateful", context="接受帮助")
    
    manager.process_interaction_event(
        "David", "Alice", "help",
        david_emotion, alice_emotion,
        "David在困难时刻帮助了Alice"
    )
    print("  ✓ David帮助Alice\n")
    
    # 查看关系摘要
    print("3. 关系摘要:")
    print("\nAlice和Bob的双向关系:")
    summary = manager.get_mutual_relation_summary("Alice", "Bob")
    print(f"  Alice → Bob: 亲密度 {summary['mutual_intimacy']['Alice_to_Bob']:+.3f}")
    print(f"  Bob → Alice: 亲密度 {summary['mutual_intimacy']['Bob_to_Alice']:+.3f}")
    print(f"  不对称度: {summary['asymmetry_score']:.3f} ({summary['relationship_balance']})")
    
    print("\nAlice和Charlie的双向关系:")
    summary = manager.get_mutual_relation_summary("Alice", "Charlie")
    print(f"  Alice → Charlie: 亲密度 {summary['mutual_intimacy']['Alice_to_Charlie']:+.3f}")
    print(f"  Charlie → Alice: 亲密度 {summary['mutual_intimacy']['Charlie_to_Alice']:+.3f}")
    print(f"  不对称度: {summary['asymmetry_score']:.3f} ({summary['relationship_balance']})")
    print()
    
    # 标准化处理
    print("4. 标准化所有关系...")
    manager.normalize_all_relations(method="minmax")
    print("完成\n")
    
    # 生成报告
    print("5. 生成关系报告:")
    print(manager.generate_relation_report("Alice"))
    
    # 导出数据
    print("6. 导出关系数据...")
    manager.export_to_json("relation_manager_demo.json")
    print("  数据已导出到: relation_manager_demo.json")
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    demonstrate_relation_manager()

