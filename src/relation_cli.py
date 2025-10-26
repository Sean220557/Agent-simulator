#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关系网络归一化CLI工具
"""

import click
import json
import sys
from pathlib import Path
from agentsim.relation_normalizer import RelationNormalizer


@click.group()
def cli():
    """关系网络归一化工具"""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='输出文件路径')
@click.option('--method', '-m', default='comprehensive', 
              type=click.Choice(['degree', 'strength', 'type', 'comprehensive']),
              help='归一化方法')
@click.option('--weights', '-w', help='权重配置 (JSON格式)')
def normalize(input_file, output, method, weights):
    """归一化关系网络数据"""
    if not output:
        output = str(Path(input_file).with_suffix('_normalized.json'))
    
    # 解析权重配置
    weight_config = None
    if weights:
        try:
            weight_config = json.loads(weights)
        except json.JSONDecodeError:
            click.echo("错误: 权重配置格式不正确", err=True)
            sys.exit(1)
    
    try:
        # 读取关系数据
        with open(input_file, 'r', encoding='utf-8') as f:
            relations = json.load(f)
        
        click.echo(f"加载了 {len(relations)} 个agent的关系数据")
        
        # 创建归一化器
        normalizer = RelationNormalizer()
        
        # 分析原始网络
        click.echo("分析原始关系网络...")
        original_stats = normalizer.analyze_network(relations)
        click.echo(f"总Agent数量: {original_stats['total_agents']}")
        click.echo(f"总关系数量: {original_stats['total_relations']}")
        click.echo(f"平均度数: {original_stats['avg_degree']:.2f}")
        click.echo(f"强度范围: {original_stats['strength_stats']['min']:.3f} - {original_stats['strength_stats']['max']:.3f}")
        
        # 执行归一化
        click.echo(f"执行{method}归一化...")
        if method == 'degree':
            normalized_relations = normalizer.normalize_by_degree(relations)
        elif method == 'strength':
            normalized_relations = normalizer.normalize_by_strength(relations)
        elif method == 'type':
            normalized_relations = normalizer.normalize_by_type(relations)
        else:  # comprehensive
            normalized_relations = normalizer.comprehensive_normalize(relations, weight_config)
        
        # 分析归一化后的网络
        click.echo("分析归一化后的关系网络...")
        normalized_stats = normalizer.analyze_network(normalized_relations)
        click.echo(f"归一化后平均度数: {normalized_stats['avg_degree']:.2f}")
        
        # 导出归一化数据
        normalizer.export_normalized_relations(normalized_relations, output)
        click.echo(f"归一化数据已导出到: {output}")
        
        click.echo("✅ 归一化完成！")
        
    except Exception as e:
        click.echo(f"❌ 错误: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
def analyze(input_file):
    """分析关系网络统计信息"""
    try:
        # 读取关系数据
        with open(input_file, 'r', encoding='utf-8') as f:
            relations = json.load(f)
        
        # 创建归一化器
        normalizer = RelationNormalizer()
        
        # 分析网络
        stats = normalizer.analyze_network(relations)
        
        # 显示统计信息
        click.echo(normalizer.visualize_network_stats(relations))
        
    except Exception as e:
        click.echo(f"❌ 错误: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
def metrics(input_file):
    """计算网络指标"""
    try:
        # 读取关系数据
        with open(input_file, 'r', encoding='utf-8') as f:
            relations = json.load(f)
        
        # 创建归一化器
        normalizer = RelationNormalizer()
        
        # 计算网络指标
        metrics = normalizer.create_network_metrics(relations)
        
        click.echo("=== 网络指标 ===")
        click.echo(f"网络密度: {metrics['network_density']:.3f}")
        
        click.echo("\n中心性指标 (前10个):")
        centrality_items = sorted(
            metrics['centrality_measures'].items(),
            key=lambda x: x[1]['degree_centrality'],
            reverse=True
        )[:10]
        
        for agent_id, measures in centrality_items:
            click.echo(f"  {agent_id}:")
            click.echo(f"    度中心性: {measures['degree_centrality']}")
            click.echo(f"    强度中心性: {measures['strength_centrality']:.3f}")
            click.echo(f"    归一化度中心性: {measures['normalized_degree']:.3f}")
            click.echo()
        
    except Exception as e:
        click.echo(f"❌ 错误: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()

