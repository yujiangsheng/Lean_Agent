#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    示例 2：持续学习智能体
═══════════════════════════════════════════════════════════════════════════════

演示持续学习智能体的核心功能：
- 知识库管理
- 猜想推导
- 多步推理

运行：python examples/02_learning_agent.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    ContinuousLearningAgent,
    UnifiedKnowledgeManager,
    MathDomain,
    KnowledgeLevel,
    DOMAIN_NAMES,
    __version__,
    __author__
)


def main():
    print("=" * 60)
    print(f"  Lean Agent v{__version__}")
    print(f"  作者: {__author__}")
    print("=" * 60)
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 1. 初始化知识库
    # ─────────────────────────────────────────────────────────────
    print("【1. 初始化知识库】")
    km = UnifiedKnowledgeManager()
    km.print_summary()
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 2. 查询知识
    # ─────────────────────────────────────────────────────────────
    print("【2. 知识查询示例】")
    
    # 按领域查询
    algebra_knowledge = km.get_by_domain(MathDomain.ALGEBRA)
    print(f"\n代数领域知识数: {len(algebra_knowledge)}")
    for k in algebra_knowledge[:3]:
        print(f"  - {k.id}: {k.statement_cn}")
    
    # 按层级查询
    axioms = km.get_by_level(KnowledgeLevel.AXIOM)
    print(f"\n公理数量: {len(axioms)}")
    for k in axioms[:3]:
        print(f"  - {k.id}: {k.statement_cn}")
    
    # 搜索
    results = km.search("交换")
    print(f"\n搜索「交换」: 找到 {len(results)} 条")
    for k in results[:3]:
        print(f"  - {k.id}: {k.statement_cn}")
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 3. 创建学习智能体
    # ─────────────────────────────────────────────────────────────
    print("【3. 创建学习智能体】")
    
    learning_agent = ContinuousLearningAgent()
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 4. 运行学习轮次
    # ─────────────────────────────────────────────────────────────
    print("【4. 运行学习轮次（代数领域）】")
    
    # 在代数领域进行一轮学习
    result = learning_agent.run_learning_round(domain="algebra")
    
    print(f"\n学习统计:")
    print(f"  总轮数: {learning_agent.stats['total_rounds']}")
    print(f"  总猜想数: {learning_agent.stats['total_conjectures']}")
    print(f"  已证明数: {learning_agent.stats['total_proved']}")
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 5. 查看知识图谱
    # ─────────────────────────────────────────────────────────────
    print("【5. 查看知识图谱】")
    kg = learning_agent.knowledge_graph
    print(f"知识图谱节点数: {len(kg.nodes)}")
    
    # 显示部分节点
    for node_id, node in list(kg.nodes.items())[:5]:
        print(f"  - {node_id}: {node.statement_cn}")
    
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 清理
    # ─────────────────────────────────────────────────────────────
    
    print("=" * 60)
    print("  示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
