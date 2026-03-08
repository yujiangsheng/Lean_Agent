#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
            Gauss - 数学家智能体 (Mathematician AI Agent)
═══════════════════════════════════════════════════════════════════════════════

统一命令行入口，支持多种运行模式。
Unified CLI entry point supporting multiple operation modes.

子命令 (Subcommands):
    - demo      : 基础功能演示 (Basic functionality demo)
    - learn     : 持续学习模式 (Continuous learning mode)
    - prove     : 自动证明定理 (Automated theorem proving)
    - translate : 自然语言 → Lean 4 翻译 (NL to Lean 4 translation)
    - graph     : 查看知识图谱 (View knowledge graph)
    - insights  : 查看学习洞察 (View learning insights)
    - report    : 生成知识库报告 (Generate knowledge report)

支持领域 (Supported Domains):
    Gauss 可处理 Lean 4 与 Mathlib 所支持的所有数学分支。
    内置领域: algebra, trigonometry, geometry, number_theory,
              solid_geometry, analytic_geometry, combinatorics,
              probability, calculus, linear_algebra, cross_domain

使用方式 (Usage):
    python main.py                               # 默认演示
    python main.py demo                          # 基础功能演示
    python main.py prove '对于所有自然数 n, n+0=n'  # 自动证明
    python main.py translate '1 + 1 = 2'         # 翻译为 Lean 4
    python main.py learn --rounds 5              # 学习 5 轮
    python main.py learn --minutes 30            # 学习 30 分钟
    python main.py learn --domain number_theory  # 学习数论
    python main.py learn --cross-domain          # 启用跨领域推理
    python main.py graph                         # 显示知识图谱
    python main.py insights                      # 显示学习洞察
    python main.py report --list                 # 详细报告

作者 (Author): Jiangsheng Yu
版本 (Version): 3.0.0
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
    ║              Gauss - 数学家智能体                           ║
    ║     Mathematician AI with Lean 4 & Mathlib Verification      ║
    ║                                                               ║
    ║   LLM: qwen3-coder:30b (Ollama)                              ║
    ║                                                               ║
    ║   功能:                                                       ║
    ║   • 自动证明: 自然语言 → Lean 4 翻译 → 自动证明              ║
    ║   • 猜想生成: 从已有知识推导新猜想                           ║
    ║   • 知识图谱: 追踪定理推导关系                               ║
    ║   • 经验学习: 从成功中学习优化策略                           ║
    ║   • 全数学覆盖: Lean + Mathlib 所有数学分支                 ║
    ║   • Mathlib 集成: 利用 Lean 4 + Mathlib 验证                 ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


# ============================================================================
# 学习模式
# ============================================================================

class LearningRunner:
    """学习运行器 (Learning Runner)

    管理学习循环的生命周期，支持按轮次或按时间运行。
    支持 Ctrl+C 优雅中断，自动保存状态后退出。
    """
    
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
        print("  - python main.py prove '对于所有自然数 n, n + 0 = n'  # 自动证明")
        print("  - python main.py learn --rounds 5                     # 运行学习")
        print("  - python main.py graph                                # 查看知识图谱")
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)


def cmd_prove(args):
    """自动证明定理"""
    print_banner()
    
    from src import create_lean_env, create_llm_agent
    
    # 获取定理描述
    theorem = args.theorem
    
    # 如果指定了文件，从文件读取
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                theorem = f.read().strip()
            print(f"📄 从文件读取: {args.file}")
        except FileNotFoundError:
            print(f"✗ 文件不存在: {args.file}")
            sys.exit(1)
    
    if not theorem:
        print("✗ 请提供定理描述或使用 --file 指定文件")
        sys.exit(1)
    
    print(f"📝 定理: {theorem}\n")
    
    # 初始化 LLM 和 Lean 环境
    print("🔧 初始化环境...")
    agent = create_llm_agent(
        use_mock=args.mock,
        model_name=args.model or "qwen3-coder:30b"
    )
    env = create_lean_env(
        project_dir=args.project_dir,
        timeout=args.timeout
    )
    
    # 步骤 1: 翻译（如果不是 Lean 代码）
    if not args.no_translate and not agent._is_lean_code(theorem):
        print("\n🔄 步骤 1: 将数学命题翻译为 Lean 4 ...")
        lean_code = agent.translate_to_lean4(theorem)
        print(f"📄 Lean 4 代码:\n{'─'*40}")
        print(lean_code)
        print('─'*40)
    else:
        lean_code = theorem
        print("📄 直接使用 Lean 4 代码")
    
    # 步骤 2: 自动证明
    print(f"\n🔍 步骤 2: 自动证明 (最多 {args.retries} 次尝试)...")
    result = agent.prove_theorem(
        lean_code,
        lean_env=env,
        max_retries=args.retries
    )
    
    # 输出结果
    print("\n" + "="*60)
    if result["success"]:
        print("✅ 证明成功！")
        print(f"\n最终证明:\n{'─'*40}")
        print(result["proof"])
        print('─'*40)
        
        # 保存结果
        if args.output:
            final_code = result["lean_code"].replace("sorry", result["proof"])
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(final_code)
            print(f"\n💾 已保存到: {args.output}")
    else:
        print("❌ 证明失败")
        print(f"   错误: {result.get('error', '未知')}")
        print(f"   尝试次数: {len(result['attempts'])}")
        
        if args.output:
            # 保存带 sorry 的代码供手动修改
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result["lean_code"])
            print(f"\n💾 已保存 Lean 代码 (含 sorry): {args.output}")
    
    print("="*60)


def cmd_translate(args):
    """翻译数学命题为 Lean 4"""
    from src import create_llm_agent
    
    statement = args.statement
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                statement = f.read().strip()
        except FileNotFoundError:
            print(f"✗ 文件不存在: {args.file}")
            sys.exit(1)
    
    if not statement:
        print("✗ 请提供数学命题")
        sys.exit(1)
    
    agent = create_llm_agent(
        use_mock=args.mock,
        model_name=args.model or "qwen3-coder:30b"
    )
    
    print(f"📝 输入: {statement}\n")
    print("🔄 翻译中...\n")
    
    lean_code = agent.translate_to_lean4(statement)
    
    print(f"📄 Lean 4 代码:\n{'─'*40}")
    print(lean_code)
    print('─'*40)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(lean_code)
        print(f"\n💾 已保存到: {args.output}")


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
        description="Gauss - 数学家智能体",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python main.py                                          # 运行演示
  python main.py prove '对于所有自然数 n, n + 0 = n'      # 自动证明
  python main.py prove --file theorem.lean                # 从文件读取并证明
  python main.py translate '1 + 1 = 2'                    # 翻译为 Lean 4
  python main.py learn --rounds 5                         # 学习 5 轮
  python main.py learn --minutes 30                       # 学习 30 分钟
  python main.py learn --domain algebra                   # 只学代数
  python main.py graph                                    # 显示知识图谱
  python main.py insights                                 # 显示学习洞察
  python main.py report --list                            # 生成详细报告
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # demo 子命令
    demo_parser = subparsers.add_parser('demo', help='演示模式')
    
    # prove 子命令
    prove_parser = subparsers.add_parser('prove', help='自动证明数学定理')
    prove_parser.add_argument('theorem', nargs='?', default='', help='数学定理描述（自然语言或 Lean 4）')
    prove_parser.add_argument('--file', '-f', type=str, help='从文件读取定理')
    prove_parser.add_argument('--output', '-o', type=str, help='保存结果到文件')
    prove_parser.add_argument('--model', type=str, help='LLM 模型名称 (默认: qwen3-coder:30b)')
    prove_parser.add_argument('--mock', action='store_true', help='使用 Mock 模式')
    prove_parser.add_argument('--retries', type=int, default=3, help='最大重试次数')
    prove_parser.add_argument('--timeout', type=int, default=60, help='Lean 验证超时 (秒)')
    prove_parser.add_argument('--project-dir', type=str, help='Lean/Mathlib 项目目录')
    prove_parser.add_argument('--no-translate', action='store_true', help='跳过翻译，直接作为 Lean 代码处理')
    
    # translate 子命令
    translate_parser = subparsers.add_parser('translate', help='将数学命题翻译为 Lean 4')
    translate_parser.add_argument('statement', nargs='?', default='', help='数学命题（自然语言）')
    translate_parser.add_argument('--file', '-f', type=str, help='从文件读取')
    translate_parser.add_argument('--output', '-o', type=str, help='保存结果到文件')
    translate_parser.add_argument('--model', type=str, help='LLM 模型名称')
    translate_parser.add_argument('--mock', action='store_true', help='使用 Mock 模式')
    
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
    if args.command == 'prove':
        cmd_prove(args)
    elif args.command == 'translate':
        cmd_translate(args)
    elif args.command == 'learn':
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
