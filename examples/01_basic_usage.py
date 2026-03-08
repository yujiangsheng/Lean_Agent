#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
        示例 1：基础用法 (Example 1: Basic Usage)
═══════════════════════════════════════════════════════════════════════════════

演示 Gauss 的基础功能（Mock 模式，无需 Lean 4 / LLM 服务）。
Demonstrates Gauss basic functionality in Mock mode
(no Lean 4 or LLM service required).

演示内容 (Demo Contents):
    1. 创建 Lean 环境和 LLM Agent
    2. 初始化证明状态 (ProofState)
    3. 获取 Tactic 建议
    4. 执行 Tactic 序列完成证明
    5. 获取可用引理列表
    6. 语法检查示例

运行 (Run):
    python examples/01_basic_usage.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import create_lean_env, create_llm_agent


def main():
    print("=" * 60)
    print("  示例 1：基础用法")
    print("=" * 60)
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 1. 创建环境
    # ─────────────────────────────────────────────────────────────
    print("【1. 创建环境】")
    env = create_lean_env()        # Lean 环境
    agent = create_llm_agent()     # LLM Agent (Mock 模式)
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 2. 初始化证明
    # ─────────────────────────────────────────────────────────────
    print("【2. 初始化证明】")
    theorem = "theorem test : ∀ n : Nat, n + 0 = n := by"
    print(f"定理: {theorem}")
    
    state = env.initialize_proof(theorem)
    print(f"\n初始状态:\n{state}")
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 3. 获取 Tactic 建议
    # ─────────────────────────────────────────────────────────────
    print("【3. 获取 Tactic 建议】")
    tactics = agent.suggest_tactics(str(state), num_suggestions=5)
    print(f"建议的 tactics: {tactics}")
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 4. 执行 Tactic
    # ─────────────────────────────────────────────────────────────
    print("【4. 执行 Tactic】")
    
    # 步骤 1: intro n
    print("步骤 1: intro n")
    result = env.apply_tactic(state, "intro n")
    print(f"  结果: {result}")
    
    if result.success:
        state = result.new_state
        print(f"  新状态:\n{state}")
        
        # 步骤 2: simp
        print("\n步骤 2: simp")
        result2 = env.apply_tactic(state, "simp")
        print(f"  结果: {result2}")
        
        if result2.success and result2.new_state.is_finished:
            print("\n🎉 证明完成！")
    
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 5. 获取可用引理
    # ─────────────────────────────────────────────────────────────
    print("【5. 获取可用引理】")
    lemmas = env.get_available_lemmas(state, k=5)
    print(f"推荐的引理: {lemmas}")
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 6. 语法检查
    # ─────────────────────────────────────────────────────────────
    print("【6. 语法检查】")
    test_stmts = [
        "theorem t1 : 1 + 1 = 2 := by rfl",
        "invalid syntax here",
        "lemma l : True := trivial"
    ]
    
    for stmt in test_stmts:
        ok = env.syntax_check(stmt)
        status = "✓" if ok else "✗"
        print(f"  {status} {stmt[:40]}...")
    
    print()
    
    # ─────────────────────────────────────────────────────────────
    # 清理
    # ─────────────────────────────────────────────────────────────
    env.close()
    
    print("=" * 60)
    print("  示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
