#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关系网络归一化处理模块

提供多种关系网络归一化算法，包括：
1. 基于度的归一化
2. 基于强度的归一化
3. 基于关系类型的归一化
4. 综合归一化
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import math


class RelationNormalizer:
    """关系网络归一化器"""
    
    def __init__(self):
        self.relation_types = ["family", "friend", "coworker", "neighbor", "acquaintance", "stranger"]
        self.type_weights = {
            "family": 1.0,
            "friend": 0.8,
            "coworker": 0.6,
            "neighbor": 0.5,
            "acquaintance": 0.4,
            "stranger": 0.2
        }
    
    def analyze_network(self, relations: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """分析关系网络的基本统计信息"""
        stats = {
            "total_agents": len(relations),
            "total_relations": 0,
            "avg_degree": 0,
            "strength_distribution": defaultdict(int),
            "type_distribution": defaultdict(int),
            "degree_distribution": defaultdict(int),
            "strength_stats": {"min": float('inf'), "max": 0, "mean": 0, "std": 0}
        }
        
        strengths = []
        degrees = []
        
        for agent_id, neighbors in relations.items():
            degree = len(neighbors)
            degrees.append(degree)
            stats["degree_distribution"][degree] += 1
            stats["total_relations"] += degree
            
            for neighbor_id, relation in neighbors.items():
                strength = relation.get("strength", 0.0)
                rel_type = relation.get("type", "stranger")
                
                strengths.append(strength)
                stats["strength_distribution"][round(strength, 1)] += 1
                stats["type_distribution"][rel_type] += 1
        
        if degrees:
            stats["avg_degree"] = sum(degrees) / len(degrees)
        
        if strengths:
            stats["strength_stats"]["min"] = min(strengths)
            stats["strength_stats"]["max"] = max(strengths)
            stats["strength_stats"]["mean"] = np.mean(strengths)
            stats["strength_stats"]["std"] = np.std(strengths)
        
        return dict(stats)
    
    def normalize_by_degree(self, relations: Dict[str, Dict[str, Dict[str, Any]]], 
                           method: str = "minmax") -> Dict[str, Dict[str, Dict[str, Any]]]:
        """基于度的归一化"""
        normalized = {}
        
        # 计算所有度值
        degrees = [len(neighbors) for neighbors in relations.values()]
        min_degree = min(degrees) if degrees else 0
        max_degree = max(degrees) if degrees else 1
        
        for agent_id, neighbors in relations.items():
            degree = len(neighbors)
            normalized[agent_id] = {}
            
            for neighbor_id, relation in neighbors.items():
                if method == "minmax":
                    # Min-Max归一化
                    normalized_degree = (degree - min_degree) / (max_degree - min_degree) if max_degree > min_degree else 0.5
                elif method == "zscore":
                    # Z-score归一化
                    mean_degree = np.mean(degrees)
                    std_degree = np.std(degrees)
                    normalized_degree = (degree - mean_degree) / std_degree if std_degree > 0 else 0
                    # 将Z-score映射到[0,1]
                    normalized_degree = max(0, min(1, (normalized_degree + 3) / 6))
                else:
                    normalized_degree = degree / max_degree if max_degree > 0 else 0
                
                normalized[agent_id][neighbor_id] = {
                    "type": relation.get("type", "stranger"),
                    "strength": relation.get("strength", 0.0),
                    "normalized_degree": normalized_degree
                }
        
        return normalized
    
    def normalize_by_strength(self, relations: Dict[str, Dict[str, Dict[str, Any]]], 
                             method: str = "minmax") -> Dict[str, Dict[str, Dict[str, Any]]]:
        """基于强度的归一化"""
        normalized = {}
        
        # 收集所有强度值
        all_strengths = []
        for neighbors in relations.values():
            for relation in neighbors.values():
                all_strengths.append(relation.get("strength", 0.0))
        
        if not all_strengths:
            return relations
        
        min_strength = min(all_strengths)
        max_strength = max(all_strengths)
        mean_strength = np.mean(all_strengths)
        std_strength = np.std(all_strengths)
        
        for agent_id, neighbors in relations.items():
            normalized[agent_id] = {}
            
            for neighbor_id, relation in neighbors.items():
                strength = relation.get("strength", 0.0)
                
                if method == "minmax":
                    # Min-Max归一化
                    normalized_strength = (strength - min_strength) / (max_strength - min_strength) if max_strength > min_strength else 0.5
                elif method == "zscore":
                    # Z-score归一化
                    normalized_strength = (strength - mean_strength) / std_strength if std_strength > 0 else 0
                    # 将Z-score映射到[0,1]
                    normalized_strength = max(0, min(1, (normalized_strength + 3) / 6))
                elif method == "robust":
                    # 鲁棒归一化（使用中位数和MAD）
                    median_strength = np.median(all_strengths)
                    mad = np.median(np.abs(np.array(all_strengths) - median_strength))
                    normalized_strength = (strength - median_strength) / (1.4826 * mad) if mad > 0 else 0
                    normalized_strength = max(0, min(1, (normalized_strength + 3) / 6))
                else:
                    normalized_strength = strength
                
                normalized[agent_id][neighbor_id] = {
                    "type": relation.get("type", "stranger"),
                    "strength": relation.get("strength", 0.0),
                    "normalized_strength": normalized_strength
                }
        
        return normalized
    
    def normalize_by_type(self, relations: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """基于关系类型的归一化"""
        normalized = {}
        
        for agent_id, neighbors in relations.items():
            normalized[agent_id] = {}
            
            for neighbor_id, relation in neighbors.items():
                rel_type = relation.get("type", "stranger")
                strength = relation.get("strength", 0.0)
                
                # 根据关系类型调整强度
                type_weight = self.type_weights.get(rel_type, 0.2)
                normalized_strength = strength * type_weight
                
                normalized[agent_id][neighbor_id] = {
                    "type": rel_type,
                    "strength": strength,
                    "normalized_strength": normalized_strength,
                    "type_weight": type_weight
                }
        
        return normalized
    
    def comprehensive_normalize(self, relations: Dict[str, Dict[str, Dict[str, Any]]], 
                              weights: Dict[str, float] = None) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """综合归一化（结合度、强度和类型）"""
        if weights is None:
            weights = {"degree": 0.3, "strength": 0.5, "type": 0.2}
        
        # 先进行各种归一化
        degree_normalized = self.normalize_by_degree(relations, "minmax")
        strength_normalized = self.normalize_by_strength(relations, "minmax")
        type_normalized = self.normalize_by_type(relations)
        
        normalized = {}
        
        for agent_id, neighbors in relations.items():
            normalized[agent_id] = {}
            
            for neighbor_id, relation in neighbors.items():
                # 获取各种归一化值
                degree_score = degree_normalized[agent_id][neighbor_id]["normalized_degree"]
                strength_score = strength_normalized[agent_id][neighbor_id]["normalized_strength"]
                type_score = type_normalized[agent_id][neighbor_id]["normalized_strength"]
                
                # 综合评分
                composite_score = (
                    weights["degree"] * degree_score +
                    weights["strength"] * strength_score +
                    weights["type"] * type_score
                )
                
                # 计算影响力分数
                influence_score = self._calculate_influence_score(
                    relation.get("type", "stranger"),
                    relation.get("strength", 0.0),
                    len(neighbors)
                )
                
                normalized[agent_id][neighbor_id] = {
                    "type": relation.get("type", "stranger"),
                    "strength": relation.get("strength", 0.0),
                    "normalized_degree": degree_score,
                    "normalized_strength": strength_score,
                    "type_weight": type_normalized[agent_id][neighbor_id]["type_weight"],
                    "composite_score": composite_score,
                    "influence_score": influence_score
                }
        
        return normalized
    
    def _calculate_influence_score(self, rel_type: str, strength: float, degree: int) -> float:
        """计算影响力分数"""
        type_weight = self.type_weights.get(rel_type, 0.2)
        
        # 基于关系类型和强度的基础分数
        base_score = strength * type_weight
        
        # 基于度的调整（度越高，单个关系的影响力相对降低）
        degree_factor = 1.0 / (1.0 + math.log(1 + degree))
        
        # 综合影响力分数
        influence_score = base_score * degree_factor
        
        return min(1.0, max(0.0, influence_score))
    
    def create_network_metrics(self, relations: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """创建网络指标"""
        metrics = {
            "centrality_measures": {},
            "clustering_coefficients": {},
            "network_density": 0,
            "average_path_length": 0,
            "modularity": 0
        }
        
        # 计算中心性指标
        for agent_id, neighbors in relations.items():
            degree = len(neighbors)
            metrics["centrality_measures"][agent_id] = {
                "degree_centrality": degree,
                "strength_centrality": sum(rel.get("strength", 0) for rel in neighbors.values()),
                "normalized_degree": degree / (len(relations) - 1) if len(relations) > 1 else 0
            }
        
        # 计算网络密度
        total_possible_edges = len(relations) * (len(relations) - 1) / 2
        total_actual_edges = sum(len(neighbors) for neighbors in relations.values()) / 2
        metrics["network_density"] = total_actual_edges / total_possible_edges if total_possible_edges > 0 else 0
        
        return metrics
    
    def export_normalized_relations(self, normalized_relations: Dict[str, Dict[str, Dict[str, Any]]], 
                                   output_file: str) -> None:
        """导出归一化后的关系数据"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(normalized_relations, f, ensure_ascii=False, indent=2)
    
    def visualize_network_stats(self, relations: Dict[str, Dict[str, Dict[str, Any]]]) -> str:
        """生成网络统计信息的可视化文本"""
        stats = self.analyze_network(relations)
        
        report = f"""
=== 关系网络统计分析 ===

基本信息:
- 总Agent数量: {stats['total_agents']}
- 总关系数量: {stats['total_relations']}
- 平均度数: {stats['avg_degree']:.2f}

强度分布:
- 最小值: {stats['strength_stats']['min']:.3f}
- 最大值: {stats['strength_stats']['max']:.3f}
- 平均值: {stats['strength_stats']['mean']:.3f}
- 标准差: {stats['strength_stats']['std']:.3f}

关系类型分布:
"""
        
        for rel_type, count in stats['type_distribution'].items():
            percentage = (count / stats['total_relations']) * 100 if stats['total_relations'] > 0 else 0
            report += f"- {rel_type}: {count} ({percentage:.1f}%)\n"
        
        report += f"""
度数分布:
"""
        for degree, count in sorted(stats['degree_distribution'].items()):
            percentage = (count / stats['total_agents']) * 100 if stats['total_agents'] > 0 else 0
            report += f"- 度数 {degree}: {count} agents ({percentage:.1f}%)\n"
        
        return report


def normalize_experiment_relations(experiment_path: str, output_path: str = None) -> Dict[str, Any]:
    """归一化实验关系数据的主函数"""
    if output_path is None:
        output_path = experiment_path.replace("relations.json", "relations_normalized.json")
    
    # 读取关系数据
    with open(experiment_path, 'r', encoding='utf-8') as f:
        relations = json.load(f)
    
    # 创建归一化器
    normalizer = RelationNormalizer()
    
    # 分析原始网络
    print("分析原始关系网络...")
    original_stats = normalizer.analyze_network(relations)
    print(normalizer.visualize_network_stats(relations))
    
    # 执行综合归一化
    print("\n执行综合归一化...")
    normalized_relations = normalizer.comprehensive_normalize(relations)
    
    # 分析归一化后的网络
    print("分析归一化后的关系网络...")
    normalized_stats = normalizer.analyze_network(normalized_relations)
    print(normalizer.visualize_network_stats(normalized_relations))
    
    # 导出归一化数据
    normalizer.export_normalized_relations(normalized_relations, output_path)
    print(f"\n归一化数据已导出到: {output_path}")
    
    # 生成网络指标
    metrics = normalizer.create_network_metrics(normalized_relations)
    
    return {
        "original_stats": original_stats,
        "normalized_stats": normalized_stats,
        "normalized_relations": normalized_relations,
        "metrics": metrics
    }


if __name__ == "__main__":
    # 示例用法
    experiment_path = "experiments/第三浪潮实验/relations.json"
    result = normalize_experiment_relations(experiment_path)
    print("归一化完成！")

