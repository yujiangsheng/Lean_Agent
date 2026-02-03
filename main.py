#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    Lean Agent - 数学家智能体
═══════════════════════════════════════════════════════════════════════════════

统一命令行入口，支持多种运行模式：
    - demo:     基础功能演示
    - learn:    持续学习模式
    - prove:    证明定理
    - graph:    查看知识图谱
    - insights: 查看学习洞察

支持领域:
    基础: algebra, trigonometry, geometry
    扩展: number_theory, solid_geometry, analytic_geometry
          combinatorics, probability, calculus, linear_algebra
    特殊: cross_domain (跨领域推理)

使用方式：
    python main.py                               # 默认演示
    python main.py learn --rounds 5              # 学习 5 轮
    python main.py learn --minutes 30            # 学习 30 分钟
    python main.py learn --domain number_theory  # 学习数论
    python main.py learn --cross-domain          # 启用跨领域推理
    python main.py graph                         # 显示知识图谱
    python main.py insights                      # 显示学习洞察

作者: Jiangsheng Yu
版本: 2.1.0
"""

import sys
import argparse
import time
import signal
from pathlib import Path
from datetime import datetime

# 添加 src 到路径
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


# 所有支持的领域
ALL_DOMAINS = [
    "algebra", "trigonometry", "geometry",
    "number_theory", "solid_geometry", "analytic_geometry",
    "combinatorics", "probability", "calculus", "linear_algebra",
    "cross_domain"
]

DOMAIN_NAMES_CN = {
    "algebra": "代数",
    "trigonometry": "三角函数",
    "geometry": "平面几何",
    "number_theory": "初等数论",
    "solid_geometry": "立体几何",
    "analytic_geometry": "解析几何",
    "combinatorics": "组合计数",
    "probability": "概率统计",
    "calculus": "微积分",
    "linear_algebra": "线性代数",
    "cross_domain": "跨领域"
}


def print_banner():
    """打印启动横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║              Lean Agent - 数学家智能体                        ║
    ║         Mathematician AI with Lean 4 Verification             ║
    ║                                                               ║
    ║   功能:                                                       ║
    ║   • 猜想生成: 从已有知识推导新猜想                           ║
    ║   • 自动证明: 多策略组合证明引擎                             ║
    ║   • 知识图谱: 追踪定理推导关系                               ║
    ║   • 经验学习: 从成功中学习优化策略                           ║
    ║   • 跨领域推理: 连接不同数学分支                             ║
    ║   • 置信度评估: 不完全归纳法验证猜想                         ║
    ║                                                               ║
    ║   支持领域:                                                   ║
    ║   代数 | 三角 | 几何 | 数论 | 组合 | 概率                    ║
    ║   微积分 | 线性代数 | 解析几何 | 立体几何                    ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


# ============================================================================
# 学习模式
# ============================================================================

class LearningRunner:
    """学习运行器"""
    
    def __init__(self, knowledge_path: str = "data/knowledge_graph.json",
                 experience_path: str = "data/experience.json"):
        self.knowledge_path = knowledge_path
        self.experience_path = experience_path
        self.running = True
        signal.signal(signal.SIGINT, self._handle_interrupt)
    
    def _handle_interrupt(self, signum, frame):
        print("\n\n⚠️  收到中断信号，正在保存并退出...")
        self.running = False
    
    def run_rounds(self, rounds: int, domain: str = None, cross_domain: bool = False, verbose: bool = True):
        """按轮次运行学习"""
        from learning_agent import ContinuousLearningAgent
        
        agent = ContinuousLearningAgent(
            knowledge_path=self.knowledge_path,
            experience_path=self.experience_path
        )
        
        # 确定领域列表
        if domain:
            domains = [domain]
        elif cross_domain:
            # 启用所有领域（含跨领域）
            domains = ALL_DOMAINS
        else:
            # 默认使用基础领域
            domains = ["algebra", "trigonometry", "geometry"]
        
        print(f"\n🎯 开始学习: {rounds} 轮")
        print(f"📂 领域: {', '.join([DOMAIN_NAMES_CN.get(d, d) for d in domains[:5]])}{'...' if len(domains) > 5 else ''}")
        if cross_domain:
            print(f"🔗 跨领域推理: 已启用")
        
        initial_stats = agent.knowledge_graph.get_statistics()
        print(f"📊 初始状态: {initial_stats['total_nodes']} 节点, {initial_stats['total_edges']} 边\n")
        
        for i in range(rounds):
            if not self.running:
                break
            
            print(f"{'─'*60}")
            print(f"🔄 轮次 {i+1}/{rounds}")
            
            current_domain = domains[i % len(domains)]
            agent.run_learning_round(domain=current_domain, verbose=verbose)
        
        # 最终报告
        self._print_summary(agent, initial_stats)
    
    def run_timed(self, minutes: int, verbose: bool = True):
        """按时间运行学习"""
        from learning_agent import ContinuousLearningAgent
        
        agent = ContinuousLearningAgent(
            knowledge_path=self.knowledge_path,
            experience_path=self.experience_path
        )
        
        print(f"\n⏱️  计划运行: {minutes} 分钟")
        print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("按 Ctrl+C 可随时中断\n")
        
        initial_stats = agent.knowledge_graph.get_statistics()
        start_time = time.time()
        end_time = start_time + minutes * 60
        
        domains = ["algebra", "trigonometry", "geometry"]
        round_num = 0
        
        while self.running and time.time() < end_time:
            round_num += 1
            elapsed = (time.time() - start_time) / 60
            remaining = (end_time - time.time()) / 60
            
            print(f"{'─'*60}")
            print(f"🔄 轮次 #{round_num} | 已运行: {elapsed:.1f}分钟 | 剩余: {remaining:.1f}分钟")
            
            domain = domains[(round_num - 1) % len(domains)]
            agent.run_learning_round(domain=domain, verbose=verbose)
        
        # 最终报告
        self._print_summary(agent, initial_stats)
    
    def _print_summary(self, agent, initial_stats):
        """打印学习摘要"""
        final_stats = agent.knowledge_graph.get_statistics()
        
        new_nodes = final_stats['total_nodes'] - initial_stats['total_nodes']
        new_edges = final_stats['total_edges'] - initial_stats['total_edges']
        
        print("\n" + "="*60)
        print("📊 学习报告")
        print("="*60)
        print(f"   新增节点: +{new_nodes}")
        print(f"   新增推导边: +{new_edges}")
        print(f"   经验库: {len(agent.experience_learner.experiences)} 条")
        print(f"   最终节点: {final_stats['total_nodes']}")
        print(f"   最终边数: {final_stats['total_edges']}")


# ============================================================================
# 命令处理
# ============================================================================

def cmd_demo(args):
    """演示模式"""
    print_banner()
    
    try:
        from src import create_lean_env, create_llm_agent
        
        print("🔧 初始化环境...")
        env = create_lean_env()
        agent = create_llm_agent(use_mock=True)
        
        # 证明演示
        print("\n【1. 证明演示】")
        theorem = "theorem test : ∀ n : Nat, n + 0 = n := by"
        print(f"定理: {theorem}")
        
        state = env.initialize_proof(theorem)
        print(f"初始状态:\n{state}\n")
        
        tactics = agent.suggest_tactics(str(state))
        print(f"建议的 tactics: {tactics[:3]}")
        
        for tactic in ["intro n", "simp"]:
            result = env.apply_tactic(state, tactic)
            print(f"执行 {tactic}: {'✓' if result.success else '✗'}")
            if result.success:
                state = result.new_state
                if state.is_finished:
                    print("✓ 证明完成！")
                    break
        
        # 猜想生成演示
        print("\n【2. 猜想生成演示】")
        conjecture = agent.generate_conjecture(domain="nat")
        print(f"生成的猜想: {conjecture}")
        
        print("\n" + "="*60)
        print("✓ 演示完成！")
        print("\n下一步:")
        print("  - python main.py learn --rounds 5  # 运行学习")
        print("  - python main.py graph              # 查看知识图谱")
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)


def cmd_learn(args):
    """学习模式"""
    print_banner()
    
    # 确定存储路径
    if args.clean:
        knowledge_path = "data/fresh_knowledge.json"
        experience_path = "data/fresh_experience.json"
        print("🧹 使用全新的知识库")
    else:
        knowledge_path = "data/knowledge_graph.json"
        experience_path = "data/experience.json"
    
    runner = LearningRunner(knowledge_path, experience_path)
    
    cross_domain = getattr(args, 'cross_domain', False) or args.domain == 'cross_domain'
    
    if args.minutes:
        runner.run_timed(args.minutes, verbose=not args.quiet)
    else:
        runner.run_rounds(args.rounds, args.domain, cross_domain=cross_domain, verbose=not args.quiet)


def cmd_graph(args):
    """显示知识图谱"""
    from learning_agent import ContinuousLearningAgent
    
    agent = ContinuousLearningAgent(
        knowledge_path="data/knowledge_graph.json",
        experience_path="data/experience.json"
    )
    
    agent.show_knowledge_graph()
    
    if args.tree:
        print(f"\n推导树 ({args.tree}):")
        agent.export_derivation_tree(args.tree)


def cmd_insights(args):
    """显示学习洞察"""
    from learning_agent import ContinuousLearningAgent
    
    agent = ContinuousLearningAgent(
        knowledge_path="data/knowledge_graph.json",
        experience_path="data/experience.json"
    )
    
    agent.show_learning_insights()


def cmd_report(args):
    """生成报告"""
    import json
    
    path = args.file or "data/knowledge_graph.json"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"✗ 文件不存在: {path}")
        return
    
    nodes = data.get('nodes', {})
    edges = data.get('edges', [])
    
    derived = [n for n in nodes.values() if n.get('node_type') == 'derived']
    axioms = [n for n in nodes.values() if n.get('node_type') == 'axiom']
    
    # 按领域分类
    by_domain = {}
    for n in derived:
        domain = n.get('domain', 'unknown')
        by_domain.setdefault(domain, []).append(n)
    
    print("="*60)
    print("📊 知识库报告")
    print("="*60)
    print(f"\n📈 总体统计:")
    print(f"   公理/基础: {len(axioms)}")
    print(f"   新推导: {len(derived)}")
    print(f"   推导边: {len(edges)}")
    
    print(f"\n📂 按领域:")
    for domain, items in sorted(by_domain.items()):
        print(f"   {domain}: {len(items)}")
    
    if args.list:
        print(f"\n📜 推导的定理:")
        print("-"*60)
        for i, n in enumerate(derived):
            name = n.get('statement_cn', n.get('name', '未命名'))
            domain = n.get('domain', '?')[:4]
            print(f"{i+1:3}. [{domain}] {name}")


# ============================================================================
# 主入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Lean Agent - 数学家智能体",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python main.py                          # 运行演示
  python main.py learn --rounds 5         # 学习 5 轮
  python main.py learn --minutes 30       # 学习 30 分钟
  python main.py learn --domain algebra   # 只学代数
  python main.py graph                    # 显示知识图谱
  python main.py insights                 # 显示学习洞察
  python main.py report --list            # 生成详细报告
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # demo 子命令
    demo_parser = subparsers.add_parser('demo', help='演示模式')
    
    # learn 子命令
    learn_parser = subparsers.add_parser('learn', help='学习模式')
    learn_parser.add_argument('--rounds', type=int, default=5, help='学习轮次')
    learn_parser.add_argument('--minutes', type=int, help='学习时间（分钟）')
    learn_parser.add_argument('--domain', choices=ALL_DOMAINS, help='指定单一领域')
    learn_parser.add_argument('--cross-domain', action='store_true', help='启用跨领域推理（使用所有领域）')
    learn_parser.add_argument('--clean', action='store_true', help='使用全新知识库')
    learn_parser.add_argument('--quiet', '-q', action='store_true', help='安静模式')
    
    # graph 子命令
    graph_parser = subparsers.add_parser('graph', help='显示知识图谱')
    graph_parser.add_argument('--tree', type=str, help='显示节点的推导树')
    
    # insights 子命令
    insights_parser = subparsers.add_parser('insights', help='显示学习洞察')
    
    # report 子命令
    report_parser = subparsers.add_parser('report', help='生成报告')
    report_parser.add_argument('--file', '-f', type=str, help='知识库文件路径')
    report_parser.add_argument('--list', '-l', action='store_true', help='列出所有定理')
    
    args = parser.parse_args()
    
    # 路由到相应命令
    if args.command == 'learn':
        cmd_learn(args)
    elif args.command == 'graph':
        cmd_graph(args)
    elif args.command == 'insights':
        cmd_insights(args)
    elif args.command == 'report':
        cmd_report(args)
    else:
        cmd_demo(args)


if __name__ == "__main__":
    main()
