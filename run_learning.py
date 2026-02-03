#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lean Agent 持续学习脚本

用法:
    python run_learning.py [分钟数]
    
示例:
    python run_learning.py 5      # 学习5分钟
    python run_learning.py 30     # 学习30分钟
    python run_learning.py        # 默认学习10分钟
"""

import sys
import time
import argparse

sys.path.insert(0, 'src')
from learning_agent import ContinuousLearningAgent, ALL_DOMAINS


def run_learning(duration_minutes: int = 10, verbose: bool = True):
    """运行持续学习
    
    Args:
        duration_minutes: 学习时长（分钟）
        verbose: 是否显示详细输出
    """
    print('=' * 60)
    print(f'     Lean Agent v2.1.0 - 持续学习 ({duration_minutes}分钟)')
    print('=' * 60)
    
    agent = ContinuousLearningAgent()
    start_time = time.time()
    duration_seconds = duration_minutes * 60
    round_num = 0
    
    while time.time() - start_time < duration_seconds:
        round_num += 1
        domain = ALL_DOMAINS[round_num % len(ALL_DOMAINS)]
        
        elapsed = int(time.time() - start_time)
        remaining = duration_seconds - elapsed
        print(f'\n[{elapsed//60}:{elapsed%60:02d}] 剩余 {remaining//60}:{remaining%60:02d} - 领域: {domain}')
        
        try:
            agent.run_learning_round(domain=domain, verbose=verbose)
        except Exception as e:
            print(f'  警告: {e}')
        
        # 每5轮显示统计
        if round_num % 5 == 0:
            print(f'\n--- 统计 (轮次 {round_num}) ---')
            print(f'  知识节点: {len(agent.knowledge_graph.nodes)}')
            print(f'  经验数量: {len(agent.experience_learner.experiences)}')
    
    # 最终统计
    print('\n' + '=' * 60)
    print('                 学习完成!')
    print('=' * 60)
    print(f'总轮次: {round_num}')
    print(f'总猜想: {agent.stats.get("total_conjectures", 0)}')
    print(f'总证明: {agent.stats.get("successful_proofs", 0)}')
    print(f'新定理: {agent.stats.get("new_theorems", 0)}')
    print(f'知识节点: {len(agent.knowledge_graph.nodes)}')
    print(f'经验数量: {len(agent.experience_learner.experiences)}')
    
    # 保存状态
    try:
        agent.knowledge_graph._save()
        agent.experience_learner._save()
        print('\n状态已保存!')
    except Exception as e:
        print(f'\n保存状态时出错: {e}')
    
    return agent


def main():
    parser = argparse.ArgumentParser(
        description='Lean Agent 持续学习',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python run_learning.py 5       # 学习5分钟
  python run_learning.py 30      # 学习30分钟
  python run_learning.py -q 10   # 安静模式学习10分钟
        '''
    )
    parser.add_argument('minutes', type=int, nargs='?', default=10,
                        help='学习时长（分钟），默认10分钟')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='安静模式，减少输出')
    
    args = parser.parse_args()
    
    if args.minutes <= 0:
        print('错误: 时长必须大于0')
        sys.exit(1)
    
    run_learning(args.minutes, verbose=not args.quiet)


if __name__ == '__main__':
    main()
