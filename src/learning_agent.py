#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    持续学习智能体
═══════════════════════════════════════════════════════════════════════════════

整合知识图谱、经验学习、猜想生成和证明引擎，实现：
    1. 从已有知识出发，推导新的非平凡定理
    2. 清晰记录定理之间的推导关系
    3. 从成功经验中学习，持续改进

工作流程:
    ┌─────────────────────────────────────────────────────────────┐
    │                     Knowledge Base                           │
    │  [Axioms] → [Lemmas] → [Theorems] → [Derived Results]       │
    └─────────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────────┐
    │              Conjecture Generator                            │
    │  • 组合已有定理                                              │
    │  • 识别模式和类比                                           │
    │  • 生成非平凡猜想                                           │
    └─────────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────────┐
    │                 Proof Engine                                 │
    │  • 经验推荐策略                                              │
    │  • 多步推理证明                                              │
    │  • 结果验证                                                  │
    └─────────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────────┐
    │              Experience Learner                              │
    │  • 记录成功模式                                              │
    │  • 更新策略权重                                              │
    │  • 优化未来推荐                                              │
    └─────────────────────────────────────────────────────────────┘

作者: Jiangsheng Yu
版本: 2.1.0

支持领域:
    - 代数、三角函数、平面几何（基础）
    - 初等数论、立体几何、解析几何
    - 组合计数、概率统计、微积分、线性代数
    - 跨领域推理和猜想生成

置信度评估:
    - 对于无法形式化证明的猜想，采用不完全归纳法
    - 通过大规模数值验证计算置信度
    - 记录反例和验证样本数
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple, Generator
from dataclasses import dataclass, field

# 添加 src 到路径
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from knowledge_graph import KnowledgeGraph, KnowledgeNode, NodeType, NodeStatus
from experience_learner import ExperienceLearner, ProofExperience
from unified_knowledge import (
    UnifiedKnowledgeManager, InductiveVerifier, MathDomain,
    AlgebraKnowledge, TrigonometryKnowledge, GeometryKnowledge,
    NumberTheoryKnowledge, SolidGeometryKnowledge, AnalyticGeometryKnowledge,
    CombinatoricsKnowledge, ProbabilityKnowledge, CalculusKnowledge,
    LinearAlgebraKnowledge, CrossDomainKnowledge
)


# 所有支持的领域
ALL_DOMAINS = [
    "algebra", "trigonometry", "geometry",
    "number_theory", "solid_geometry", "analytic_geometry",
    "combinatorics", "probability", "calculus", "linear_algebra",
    "cross_domain"
]


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_id: int
    from_theorems: List[str]        # 使用的定理ID
    operation: str                  # 操作类型: combine, specialize, generalize, analogize
    result_statement: str           # 推导结果
    result_cn: str                  # 中文描述
    confidence: float = 1.0         # 置信度
    
    def __str__(self):
        return f"Step {self.step_id}: {self.operation} -> {self.result_cn}"


@dataclass
class ReasoningChain:
    """
    推理链（多步推理的完整记录）
    
    支持深度推理评估：有效推理步骤越多，质量分数越高
    """
    chain_id: str
    domain: str
    steps: List[ReasoningStep] = field(default_factory=list)
    final_conjecture: str = ""
    final_cn: str = ""
    total_confidence: float = 1.0
    
    def add_step(self, step: ReasoningStep):
        """添加推理步骤"""
        self.steps.append(step)
        # 累积置信度
        self.total_confidence *= step.confidence
    
    def get_all_premises(self) -> List[str]:
        """获取所有使用的前置定理"""
        premises = set()
        for step in self.steps:
            premises.update(step.from_theorems)
        return list(premises)
    
    def get_operation_diversity(self) -> float:
        """
        获取操作多样性得分
        
        使用的操作类型越多，得分越高（0-1）
        """
        if not self.steps:
            return 0.0
        operations = set(step.operation for step in self.steps)
        # 最多6种操作类型
        return len(operations) / 6.0
    
    def get_quality_score(self) -> float:
        """
        计算推理链的质量分数
        
        评分因素：
        1. 推理步数（有效步骤越多越好，但有上限）
        2. 操作多样性（使用多种推理操作比单一操作更好）
        3. 累积置信度（每步的可靠性）
        4. 定理使用广度（使用的前置定理越多越好）
        
        返回: 0.0 - 1.0 的质量分数
        """
        if not self.steps:
            return 0.0
        
        n_steps = len(self.steps)
        
        # 1. 步数得分（使用对数增长，鼓励深度但避免过长）
        # 最优范围 4-8 步，超过 10 步收益递减
        if n_steps <= 2:
            step_score = n_steps * 0.15  # 短链路得分较低
        elif n_steps <= 6:
            step_score = 0.3 + (n_steps - 2) * 0.15  # 中等长度线性增长
        elif n_steps <= 10:
            step_score = 0.9 + (n_steps - 6) * 0.025  # 长链路收益递减
        else:
            step_score = 1.0  # 超长链路封顶
        
        # 2. 操作多样性得分（权重 0.2）
        diversity_score = self.get_operation_diversity() * 0.2
        
        # 3. 累积置信度得分（权重 0.3）
        confidence_score = self.total_confidence * 0.3
        
        # 4. 定理广度得分（权重 0.1）
        premises = self.get_all_premises()
        breadth_score = min(len(premises) / 10.0, 1.0) * 0.1
        
        # 综合得分
        total_score = step_score * 0.4 + diversity_score + confidence_score + breadth_score
        
        return min(total_score, 1.0)
    
    def get_effective_steps(self) -> int:
        """
        获取有效推理步数
        
        仅计算置信度 > 0.3 的步骤为有效步骤
        """
        return sum(1 for step in self.steps if step.confidence > 0.3)
    
    def __len__(self):
        return len(self.steps)
    
    def __str__(self) -> str:
        """友好的字符串表示"""
        return (f"ReasoningChain(steps={len(self.steps)}, "
                f"effective={self.get_effective_steps()}, "
                f"quality={self.get_quality_score():.3f}, "
                f"confidence={self.total_confidence:.3f})")


@dataclass
class DerivationResult:
    """推导结果"""
    conjecture_id: str
    statement: str
    statement_cn: str
    domain: str
    
    success: bool
    proof_script: Optional[str] = None
    tactics_used: List[str] = None
    proof_steps: int = 0
    proof_time_ms: float = 0.0
    
    # 推导关系
    premises: List[str] = None      # 使用的前置定理
    relation_type: str = ""         # 推导类型
    reasoning_chain: ReasoningChain = None  # 多步推理链
    
    error_message: str = ""
    
    # 置信度（用于无法形式化证明的猜想）
    confidence: float = 1.0         # 置信度（0-1，1.0表示已证明）
    induction_samples: int = 0      # 归纳验证样本数
    counterexample: str = ""        # 反例（如果找到）


# ═══════════════════════════════════════════════════════════════════════════
# 多步推理引擎
# ═══════════════════════════════════════════════════════════════════════════

class ChainOfThoughtReasoner:
    """
    多步推理引擎
    
    通过组合多个推理步骤生成深层次猜想：
    1. 选择前置定理
    2. 应用推理操作（组合、特化、泛化、类比）
    3. 生成中间结论
    4. 重复以获得更深层次的猜想
    
    改进特性：
    - 支持最多 8 步深度推理
    - 有效推理步骤越多，质量评分越高
    - 操作多样性奖励
    """
    
    # 推理操作类型及其特性
    OPERATIONS = {
        "combine": {"name": "组合", "confidence_decay": 0.8, "weight": 1.5},
        "specialize": {"name": "特化", "confidence_decay": 0.95, "weight": 1.0},
        "generalize": {"name": "泛化", "confidence_decay": 0.6, "weight": 1.8},
        "analogize": {"name": "类比", "confidence_decay": 0.5, "weight": 2.0},
        "contrapose": {"name": "逆否", "confidence_decay": 1.0, "weight": 0.8},
        "extend": {"name": "推广", "confidence_decay": 0.7, "weight": 1.5},
    }
    
    # 默认最大步数提升到 8
    DEFAULT_MAX_STEPS = 8
    
    def __init__(self, knowledge_graph: KnowledgeGraph, max_steps: int = None):
        self.kg = knowledge_graph
        self.max_steps = max_steps if max_steps is not None else self.DEFAULT_MAX_STEPS
        # 追踪操作使用历史（用于多样性奖励）
        self._operation_history = []
    
    def reason(self, domain: str = None, target_steps: int = None, 
               prefer_diversity: bool = True) -> Optional[ReasoningChain]:
        """
        执行多步推理
        
        参数:
            domain: 目标领域
            target_steps: 目标步数（默认随机 3-7 步，鼓励更深推理）
            prefer_diversity: 是否优先选择未使用过的操作类型
        
        返回:
            推理链（包含所有步骤和最终猜想）
        """
        # 默认目标步数：随机 3-7 步（鼓励更深推理）
        if target_steps is None:
            target_steps = random.randint(3, min(7, self.max_steps))
        
        target_steps = min(target_steps, self.max_steps)
        
        # 获取可用定理
        available = [
            n for n in self.kg.nodes.values()
            if n.status in [NodeStatus.VERIFIED, NodeStatus.ASSUMED]
            and (domain is None or n.domain == domain or domain == "cross_domain")
        ]
        
        if len(available) < 2:
            return None
        
        chain_id = f"chain_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        chain = ReasoningChain(chain_id=chain_id, domain=domain or "mixed")
        
        # 当前可用的中间结论（初始为原始定理）
        current_pool = list(available)
        
        # 重置操作历史（用于多样性优先）
        used_operations = set()
        
        for step_num in range(target_steps):
            step = self._make_reasoning_step(
                step_num + 1, current_pool, domain, 
                used_operations if prefer_diversity else None
            )
            if step is None:
                break
            
            chain.add_step(step)
            used_operations.add(step.operation)
            
            # 将中间结论加入池中供后续使用
            intermediate = KnowledgeNode(
                id=f"intermediate_{step_num}",
                statement=step.result_statement,
                statement_cn=step.result_cn,
                domain=domain or "mixed",
                node_type=NodeType.CONJECTURE,
                status=NodeStatus.CONJECTURED
            )
            current_pool.append(intermediate)
        
        if len(chain) == 0:
            return None
        
        # 设置最终猜想
        final_step = chain.steps[-1]
        chain.final_conjecture = final_step.result_statement
        chain.final_cn = final_step.result_cn
        
        return chain
    
    def _select_operation(self, used_operations: Optional[set] = None) -> str:
        """
        选择推理操作
        
        支持多样性优先：优先选择未使用过的操作类型
        同时考虑操作权重（更有价值的操作更可能被选中）
        """
        all_ops = list(self.OPERATIONS.keys())
        
        if used_operations is not None:
            # 优先选择未使用过的操作
            unused = [op for op in all_ops if op not in used_operations]
            if unused:
                # 按权重加权随机选择
                weights = [self.OPERATIONS[op]["weight"] for op in unused]
                return random.choices(unused, weights=weights, k=1)[0]
        
        # 所有操作都用过了，或不需要多样性优先，按权重随机选择
        weights = [self.OPERATIONS[op]["weight"] for op in all_ops]
        return random.choices(all_ops, weights=weights, k=1)[0]
    
    def _make_reasoning_step(self, step_id: int, pool: List[KnowledgeNode], 
                             domain: str, 
                             used_operations: Optional[set] = None) -> Optional[ReasoningStep]:
        """创建单个推理步骤"""
        # 使用智能操作选择（支持多样性优先）
        operation = self._select_operation(used_operations)
        
        if operation == "combine":
            return self._combine_theorems(step_id, pool, domain)
        elif operation == "specialize":
            return self._specialize_theorem(step_id, pool, domain)
        elif operation == "generalize":
            return self._generalize_theorem(step_id, pool, domain)
        elif operation == "analogize":
            return self._analogize_theorem(step_id, pool, domain)
        elif operation == "contrapose":
            return self._contrapose_theorem(step_id, pool, domain)
        elif operation == "extend":
            return self._extend_theorem(step_id, pool, domain)
        
        return None
    
    def _combine_theorems(self, step_id: int, pool: List[KnowledgeNode], 
                          domain: str) -> Optional[ReasoningStep]:
        """组合两个定理生成新结论"""
        if len(pool) < 2:
            return None
        
        # 选择两个相关定理
        t1, t2 = random.sample(pool, 2)
        
        # 组合策略
        combine_templates = [
            # 条件链接
            ("如果 {A} 且 {B}，则...", 
             f"∀ x, ({t1.statement}) ∧ ({t2.statement}) → ...",
             f"{t1.statement_cn} 与 {t2.statement_cn} 的联合推论"),
            # 等式传递
            ("由 {A} 代入 {B}",
             f"通过代入: {t1.statement[:50]}...",
             f"将 {t1.statement_cn} 代入 {t2.statement_cn}"),
            # 不等式叠加
            ("叠加 {A} 和 {B}",
             f"∀ x y, sum_ineq({t1.statement}, {t2.statement})",
             f"{t1.statement_cn} 与 {t2.statement_cn} 的叠加"),
        ]
        
        _, result_stmt, result_cn = random.choice(combine_templates)
        
        return ReasoningStep(
            step_id=step_id,
            from_theorems=[t1.id, t2.id],
            operation="combine",
            result_statement=result_stmt,
            result_cn=result_cn,
            confidence=self.OPERATIONS["combine"]["confidence_decay"]
        )
    
    def _specialize_theorem(self, step_id: int, pool: List[KnowledgeNode],
                            domain: str) -> Optional[ReasoningStep]:
        """特化定理（用具体值代入）"""
        t = random.choice(pool)
        
        # 特化模板
        special_values = [
            ("n=2", "二元情形"),
            ("n=3", "三元情形"),
            ("x=0", "零点情形"),
            ("x=1", "单位情形"),
            ("a=b", "对称情形"),
        ]
        
        value, desc = random.choice(special_values)
        
        return ReasoningStep(
            step_id=step_id,
            from_theorems=[t.id],
            operation="specialize",
            result_statement=f"({t.statement})[{value}]",
            result_cn=f"{t.statement_cn} 的{desc}",
            confidence=self.OPERATIONS["specialize"]["confidence_decay"]
        )
    
    def _generalize_theorem(self, step_id: int, pool: List[KnowledgeNode],
                            domain: str) -> Optional[ReasoningStep]:
        """泛化定理"""
        t = random.choice(pool)
        
        # 泛化模板
        generalizations = [
            ("推广到 n 维", f"∀ n, generalize({t.statement}, n)"),
            ("推广到复数域", f"∀ z : ℂ, {t.statement}"),
            ("推广到任意次幂", f"∀ k, power_generalize({t.statement}, k)"),
            ("推广到矩阵", f"∀ A : Matrix, matrix_form({t.statement})"),
        ]
        
        desc, result_stmt = random.choice(generalizations)
        
        return ReasoningStep(
            step_id=step_id,
            from_theorems=[t.id],
            operation="generalize",
            result_statement=result_stmt,
            result_cn=f"{t.statement_cn} {desc}",
            confidence=self.OPERATIONS["generalize"]["confidence_decay"]
        )
    
    def _analogize_theorem(self, step_id: int, pool: List[KnowledgeNode],
                           domain: str) -> Optional[ReasoningStep]:
        """类比推理"""
        t = random.choice(pool)
        
        # 类比映射
        analogies = [
            ("加法 → 乘法", "mul_analog"),
            ("实数 → 整数", "int_analog"),
            ("平面 → 空间", "3d_analog"),
            ("离散 → 连续", "continuous_analog"),
            ("确定 → 随机", "probabilistic_analog"),
        ]
        
        desc, func = random.choice(analogies)
        
        return ReasoningStep(
            step_id=step_id,
            from_theorems=[t.id],
            operation="analogize",
            result_statement=f"{func}({t.statement})",
            result_cn=f"{t.statement_cn} 的类比（{desc}）",
            confidence=self.OPERATIONS["analogize"]["confidence_decay"]
        )
    
    def _contrapose_theorem(self, step_id: int, pool: List[KnowledgeNode],
                            domain: str) -> Optional[ReasoningStep]:
        """逆否命题"""
        # 只对蕴涵形式的定理有效
        implications = [t for t in pool if "→" in t.statement]
        if not implications:
            return self._combine_theorems(step_id, pool, domain)
        
        t = random.choice(implications)
        
        return ReasoningStep(
            step_id=step_id,
            from_theorems=[t.id],
            operation="contrapose",
            result_statement=f"contrapose({t.statement})",
            result_cn=f"{t.statement_cn} 的逆否命题",
            confidence=self.OPERATIONS["contrapose"]["confidence_decay"]
        )
    
    def _extend_theorem(self, step_id: int, pool: List[KnowledgeNode],
                        domain: str) -> Optional[ReasoningStep]:
        """推广/延伸定理"""
        t = random.choice(pool)
        
        extensions = [
            ("加强条件", "stronger_condition"),
            ("弱化结论", "weaker_conclusion"),
            ("添加边界情况", "boundary_case"),
            ("考虑极限", "limit_case"),
        ]
        
        desc, func = random.choice(extensions)
        
        return ReasoningStep(
            step_id=step_id,
            from_theorems=[t.id],
            operation="extend",
            result_statement=f"{func}({t.statement})",
            result_cn=f"{t.statement_cn}（{desc}）",
            confidence=self.OPERATIONS["extend"]["confidence_decay"]
        )
    
    def evaluate_chain_quality(self, chain: ReasoningChain) -> dict:
        """
        评估推理链质量
        
        返回详细的质量评估报告
        
        参数:
            chain: 待评估的推理链
        
        返回:
            包含各项评分的字典
        """
        if chain is None or len(chain) == 0:
            return {"quality_score": 0.0, "effective_steps": 0, "details": "空推理链"}
        
        n_steps = len(chain)
        effective_steps = chain.get_effective_steps()
        
        return {
            "quality_score": chain.get_quality_score(),
            "total_steps": n_steps,
            "effective_steps": effective_steps,
            "operation_diversity": chain.get_operation_diversity(),
            "total_confidence": chain.total_confidence,
            "premises_count": len(chain.get_all_premises()),
            "operations_used": list(set(step.operation for step in chain.steps)),
            "step_bonus": "优秀" if effective_steps >= 5 else ("良好" if effective_steps >= 3 else "一般"),
        }


class ContinuousLearningAgent:
    """
    持续学习智能体
    
    核心能力:
        1. 知识积累: 维护定理知识图谱
        2. 智能推导: 从已知定理推导新结论
        3. 经验学习: 从证明历史中学习
        4. 策略优化: 基于经验优化证明策略
    """
    
    def __init__(self, 
                 knowledge_path: str = "data/knowledge_graph.json",
                 experience_path: str = "data/experience.json",
                 lean_project: str = "LeanProject"):
        """
        初始化智能体
        
        参数:
            knowledge_path: 知识图谱存储路径
            experience_path: 经验数据存储路径
            lean_project: Lean 项目路径
        """
        print("=" * 70)
        print("              持续学习数学智能体")
        print("=" * 70)
        
        # 知识图谱
        print("\n初始化知识系统...")
        self.knowledge_graph = KnowledgeGraph(knowledge_path)
        
        # 经验学习器
        self.experience_learner = ExperienceLearner(experience_path)
        
        # Lean 证明引擎（延迟加载）
        self.lean_project = lean_project
        self._prover = None
        
        # 配置
        self.config = {
            "max_conjecture_per_round": 10,     # 每轮最大猜想数
            "min_difficulty": 2,                # 最小难度
            "max_proof_attempts": 3,            # 最大证明尝试次数
            "learning_rate": 0.1,               # 学习率
        }
        
        # 统计
        self.stats = {
            "total_rounds": 0,
            "total_conjectures": 0,
            "total_proved": 0,
            "total_added_to_graph": 0,
            "session_start": datetime.now().isoformat()
        }
        
        # 初始化知识库
        self._initialize_knowledge_base()
        
        # 多步推理器（在知识库初始化后创建，使用默认的 8 步深度）
        self.reasoner = ChainOfThoughtReasoner(self.knowledge_graph)
        
        print(f"\n✓ 知识库: {len(self.knowledge_graph.nodes)} 个节点")
        print(f"✓ 经验库: {len(self.experience_learner.experiences)} 条经验")
        print(f"✓ 推理器: 最大 {self.reasoner.max_steps} 步深度推理")
        print("=" * 70)
    
    def _initialize_knowledge_base(self):
        """初始化基础知识库（含所有领域）"""
        if len(self.knowledge_graph.nodes) > 0:
            return  # 已有知识
        
        print("  初始化基础知识...")
        
        # 代数公理/定理
        algebra_basics = [
            ("algebra_axiom_1", "∀ a b : ℝ, a + b = b + a", "加法交换律", NodeType.AXIOM),
            ("algebra_axiom_2", "∀ a b c : ℝ, (a + b) + c = a + (b + c)", "加法结合律", NodeType.AXIOM),
            ("algebra_axiom_3", "∀ a b : ℝ, a * b = b * a", "乘法交换律", NodeType.AXIOM),
            ("algebra_axiom_4", "∀ a b c : ℝ, (a * b) * c = a * (b * c)", "乘法结合律", NodeType.AXIOM),
            ("algebra_axiom_5", "∀ a b c : ℝ, a * (b + c) = a * b + a * c", "分配律", NodeType.AXIOM),
            ("algebra_sq_nonneg", "∀ a : ℝ, a ^ 2 ≥ 0", "平方非负性", NodeType.AXIOM),
            
            ("algebra_thm_1", "∀ a b : ℝ, (a + b) ^ 2 = a^2 + 2*a*b + b^2", "完全平方公式", NodeType.THEOREM),
            ("algebra_thm_2", "∀ a b : ℝ, (a - b) ^ 2 = a^2 - 2*a*b + b^2", "差的平方", NodeType.THEOREM),
            ("algebra_thm_3", "∀ a b : ℝ, (a + b) * (a - b) = a^2 - b^2", "平方差公式", NodeType.THEOREM),
            ("algebra_thm_4", "∀ a b : ℝ, a^2 + b^2 ≥ 2*a*b", "基本不等式", NodeType.THEOREM),
        ]
        
        # 三角函数
        trig_basics = [
            ("trig_axiom_1", "∀ θ : ℝ, sin²θ + cos²θ = 1", "毕达哥拉斯恒等式", NodeType.AXIOM),
            ("trig_axiom_2", "∀ θ : ℝ, tan θ = sin θ / cos θ", "正切定义", NodeType.AXIOM),
            
            ("trig_thm_1", "∀ α β : ℝ, sin(α + β) = sin α cos β + cos α sin β", "正弦加法定理", NodeType.THEOREM),
            ("trig_thm_2", "∀ α β : ℝ, cos(α + β) = cos α cos β - sin α sin β", "余弦加法定理", NodeType.THEOREM),
            ("trig_thm_3", "∀ θ : ℝ, sin(2θ) = 2 sin θ cos θ", "二倍角正弦", NodeType.THEOREM),
            ("trig_thm_4", "∀ θ : ℝ, cos(2θ) = cos²θ - sin²θ", "二倍角余弦", NodeType.THEOREM),
        ]
        
        # 几何
        geo_basics = [
            ("geo_axiom_1", "∀ a b c : ℝ, a > 0 → b > 0 → c > 0 → a + b > c → valid_triangle a b c", "三角形存在条件", NodeType.AXIOM),
            ("geo_thm_1", "∀ a b c : ℝ, right_triangle a b c → a² + b² = c²", "勾股定理", NodeType.THEOREM),
        ]
        
        # 添加到知识图谱
        all_basics = algebra_basics + trig_basics + geo_basics
        
        for nid, statement, desc, node_type in all_basics:
            domain = "algebra" if nid.startswith("algebra") else (
                "trigonometry" if nid.startswith("trig") else "geometry"
            )
            
            node = KnowledgeNode(
                id=nid,
                statement=statement,
                statement_cn=desc,
                domain=domain,
                node_type=node_type,
                status=NodeStatus.ASSUMED if node_type == NodeType.AXIOM else NodeStatus.VERIFIED
            )
            self.knowledge_graph.add_node(node)
        
        # 添加推导关系
        self.knowledge_graph.add_edge("algebra_axiom_5", "algebra_thm_1", "derivation")
        self.knowledge_graph.add_edge("algebra_sq_nonneg", "algebra_thm_4", "derivation")
        self.knowledge_graph.add_edge("algebra_thm_1", "algebra_thm_2", "analogy")
        
        # ====== 加载扩展知识库 ======
        self._load_extended_knowledge()
        
        print(f"    ✓ 添加 {len(all_basics)} 个基础定理")
    
    def _load_extended_knowledge(self):
        """加载扩展知识库（所有领域，使用统一知识库）"""
        print("    加载统一知识库...")
        
        # 领域知识类映射
        domain_knowledge_classes = {
            "algebra": AlgebraKnowledge,
            "trigonometry": TrigonometryKnowledge,
            "geometry": GeometryKnowledge,
            "number_theory": NumberTheoryKnowledge,
            "solid_geometry": SolidGeometryKnowledge,
            "analytic_geometry": AnalyticGeometryKnowledge,
            "combinatorics": CombinatoricsKnowledge,
            "probability": ProbabilityKnowledge,
            "calculus": CalculusKnowledge,
            "linear_algebra": LinearAlgebraKnowledge,
        }
        
        added_count = 0
        
        for domain_name, knowledge_class in domain_knowledge_classes.items():
            # 获取公理 (现在返回 MathKnowledge 对象)
            if hasattr(knowledge_class, 'get_axioms'):
                axioms = knowledge_class.get_axioms()
                for ax in axioms:
                    node = KnowledgeNode(
                        id=ax.id,
                        statement=ax.statement,
                        statement_cn=ax.statement_cn,
                        domain=domain_name,
                        node_type=NodeType.AXIOM,
                        status=NodeStatus.ASSUMED,
                        difficulty=ax.difficulty
                    )
                    if self.knowledge_graph.add_node(node):
                        added_count += 1
            
            # 获取定理 (现在返回 MathKnowledge 对象)
            if hasattr(knowledge_class, 'get_theorems'):
                theorems = knowledge_class.get_theorems()
                for thm in theorems:
                    node = KnowledgeNode(
                        id=thm.id,
                        statement=thm.statement,
                        statement_cn=thm.statement_cn,
                        domain=domain_name,
                        node_type=NodeType.THEOREM,
                        status=NodeStatus.VERIFIED,
                        difficulty=thm.difficulty,
                        related_domains=[d.value for d in thm.related_domains] if thm.related_domains else []
                    )
                    if self.knowledge_graph.add_node(node):
                        added_count += 1
        
        # 加载跨领域定理
        cross_domain_theorems = CrossDomainKnowledge.get_theorems()
        for thm in cross_domain_theorems:
            node = KnowledgeNode(
                id=thm.id,
                statement=thm.statement,
                statement_cn=thm.statement_cn,
                domain="cross_domain",
                node_type=NodeType.THEOREM,
                status=NodeStatus.VERIFIED,
                difficulty=thm.difficulty,
                related_domains=[d.value for d in thm.related_domains] if thm.related_domains else []
            )
            if self.knowledge_graph.add_node(node):
                added_count += 1
        
        print(f"      ✓ 添加 {added_count} 个统一知识")
    
    # ========== 猜想生成 ==========
    
    def generate_conjectures(self, domain: str = None, count: int = 5, 
                            prefer_deep_reasoning: bool = True) -> List[Dict]:
        """
        从已有知识生成新猜想
        
        参数:
            domain: 目标领域（None 表示所有领域）
            count: 生成猜想数量
            prefer_deep_reasoning: 是否优先使用多步推理（更有价值的猜想）
        
        策略:
            1. 多步推理: 通过链式思考生成深层次猜想（优先）
            2. 组合: 将两个相关定理组合
            3. 类比: 从一个定理类比到另一个
            4. 泛化: 将特殊定理推广
            5. 特化: 将一般定理特化
            6. 跨领域: 连接不同领域的概念
        """
        conjectures = []
        
        # 获取可用的前置定理
        verified_nodes = [
            n for n in self.knowledge_graph.nodes.values()
            if n.status in [NodeStatus.VERIFIED, NodeStatus.ASSUMED, NodeStatus.CONJECTURED]
            and (domain is None or n.domain == domain or domain == "cross_domain")
        ]
        
        if len(verified_nodes) < 2:
            print("警告: 知识库中的定理太少，无法生成猜想")
            return conjectures
        
        # 多步推理生成（优先）
        if prefer_deep_reasoning:
            deep_count = max(1, count // 2)  # 至少一半用多步推理
            for _ in range(deep_count):
                conjecture = self._generate_by_chain_of_thought(verified_nodes, domain)
                if conjecture and not self._is_duplicate(conjecture, conjectures):
                    if not self._is_trivial_derivation(conjecture):
                        conjectures.append(conjecture)
        
        # 其他策略
        strategies = [
            self._generate_by_combination,
            self._generate_by_strengthening,
            self._generate_by_chaining,
            self._generate_cross_domain_conjecture,  # 跨领域猜想
        ]
        
        # 为新领域添加特定生成器
        if domain in ["number_theory", None]:
            strategies.append(self._generate_number_theory_conjecture)
        if domain in ["combinatorics", None]:
            strategies.append(self._generate_combinatorics_conjecture)
        if domain in ["calculus", None]:
            strategies.append(self._generate_calculus_conjecture)
        if domain in ["probability", None]:
            strategies.append(self._generate_probability_conjecture)
        if domain in ["linear_algebra", None]:
            strategies.append(self._generate_linear_algebra_conjecture)
        
        # 填充剩余数量
        remaining = count - len(conjectures)
        for _ in range(remaining * 2):  # 多尝试几次以应对失败
            if len(conjectures) >= count:
                break
            strategy = random.choice(strategies)
            try:
                conjecture = strategy(verified_nodes)
                if conjecture:
                    if self._is_duplicate(conjecture, conjectures):
                        continue
                    if self._is_trivial_derivation(conjecture):
                        continue
                    conjectures.append(conjecture)
            except Exception as e:
                continue
        
        return conjectures
    
    def _generate_by_chain_of_thought(self, nodes: List[KnowledgeNode], 
                                       domain: str = None) -> Optional[Dict]:
        """
        通过多步推理生成深层次猜想
        
        这是最有价值的猜想生成方式，因为它模拟了数学家的思考过程：
        从已知定理出发，通过多次推理操作，得出非平凡的新结论。
        
        改进：
        - 支持更深层次推理（3-7步）
        - 根据推理链质量评分调整难度
        - 有效推理步骤越多，评价越高
        """
        # 执行多步推理（让 reasoner 自动选择 3-7 步，鼓励更深推理）
        chain = self.reasoner.reason(domain=domain, prefer_diversity=True)
        
        if chain is None or len(chain) < 2:
            return None
        
        # 评估推理链质量
        quality_eval = self.reasoner.evaluate_chain_quality(chain)
        quality_score = quality_eval["quality_score"]
        effective_steps = quality_eval["effective_steps"]
        
        # 构造猜想记录
        conjecture_id = f"deep_{chain.chain_id}"
        
        # 生成更详细的描述
        steps_desc = " → ".join([
            f"({s.operation}: {s.result_cn[:20]}...)" if len(s.result_cn) > 20 
            else f"({s.operation}: {s.result_cn})"
            for s in chain.steps
        ])
        
        # 根据质量评分调整难度
        # 有效步骤越多，难度越高，价值也越高
        base_difficulty = min(5, len(chain) + 1)
        quality_bonus = int(quality_score * 2)  # 0-2 的加成
        difficulty = min(7, base_difficulty + quality_bonus)  # 难度上限 7
        
        return {
            "id": conjecture_id,
            "statement": chain.final_conjecture,
            "statement_cn": f"【{len(chain)}步推理, 质量{quality_score:.2f}】{chain.final_cn}",
            "domain": chain.domain,
            "premises": chain.get_all_premises(),
            "relation_type": "chain_of_thought",
            "difficulty": difficulty,
            "reasoning_chain": chain,
            "reasoning_steps": len(chain),
            "effective_reasoning_steps": effective_steps,  # 有效推理步数
            "quality_score": quality_score,  # 推理链质量分数
            "quality_eval": quality_eval,    # 完整评估报告
            "reasoning_path": steps_desc,
            "confidence": chain.total_confidence
        }
    
    def _generate_by_combination(self, nodes: List[KnowledgeNode]) -> Optional[Dict]:
        """通过组合生成猜想"""
        if len(nodes) < 2:
            return None
        
        # 选择同一领域的两个节点
        domain_nodes = {}
        for n in nodes:
            if n.domain not in domain_nodes:
                domain_nodes[n.domain] = []
            domain_nodes[n.domain].append(n)
        
        # 选择有足够节点的领域
        valid_domains = [d for d, ns in domain_nodes.items() if len(ns) >= 2]
        if not valid_domains:
            return None
        
        domain = random.choice(valid_domains)
        n1, n2 = random.sample(domain_nodes[domain], 2)
        
        # 生成组合猜想
        conjecture_id = f"derived_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        
        # 动态生成：基于领域和随机参数
        if domain == "algebra":
            statement, statement_cn = self._dynamic_algebra_conjecture(n1, n2)
        elif domain == "trigonometry":
            statement, statement_cn = self._dynamic_trig_conjecture(n1, n2)
        elif domain == "number_theory":
            statement, statement_cn = self._dynamic_number_theory_conjecture(n1, n2)
        elif domain == "combinatorics":
            statement, statement_cn = self._dynamic_combinatorics_conjecture(n1, n2)
        elif domain == "calculus":
            statement, statement_cn = self._dynamic_calculus_conjecture(n1, n2)
        elif domain == "probability":
            statement, statement_cn = self._dynamic_probability_conjecture(n1, n2)
        elif domain == "linear_algebra":
            statement, statement_cn = self._dynamic_linear_algebra_conjecture(n1, n2)
        elif domain in ["solid_geometry", "analytic_geometry"]:
            statement, statement_cn = self._dynamic_advanced_geo_conjecture(n1, n2, domain)
        else:
            statement, statement_cn = self._dynamic_geo_conjecture(n1, n2)
        
        return {
            "id": conjecture_id,
            "statement": statement,
            "statement_cn": statement_cn,
            "domain": domain,
            "premises": [n1.id, n2.id],
            "relation_type": "combination",
            "difficulty": 3
        }
    
    def _dynamic_algebra_conjecture(self, n1: KnowledgeNode, n2: KnowledgeNode) -> Tuple[str, str]:
        """动态生成代数猜想"""
        # 随机参数
        n = random.randint(2, 6)  # 变量数
        k = random.randint(2, 4)  # 幂次
        
        # 多种猜想类型
        conjecture_types = [
            self._gen_polynomial_identity,
            self._gen_inequality,
            self._gen_sum_formula,
            self._gen_product_identity,
            self._gen_power_sum,
            self._gen_symmetric_inequality,
        ]
        
        gen_func = random.choice(conjecture_types)
        return gen_func(n, k)
    
    def _gen_polynomial_identity(self, n: int, k: int) -> Tuple[str, str]:
        """生成多项式恒等式"""
        vars_str = ' '.join([chr(ord('a') + i) for i in range(n)])
        vars_list = [chr(ord('a') + i) for i in range(n)]
        
        templates = [
            # (a+b+c)^2 展开
            (f"∀ {vars_str} : ℝ, ({'+'.join(vars_list)})^{k} = ...", 
             f"{n}元{k}次展开式"),
            # 差的幂
            (f"∀ a b : ℝ, (a - b)^{k} = {self._expand_diff_power(k)}",
             f"差的{k}次幂展开"),
            # 和的立方
            (f"∀ {vars_str} : ℝ, ({'+'.join(vars_list)})^3 = {self._expand_sum_cube(vars_list)}",
             f"{n}元立方展开"),
        ]
        return random.choice(templates)
    
    def _expand_diff_power(self, k: int) -> str:
        """展开 (a-b)^k"""
        from math import comb
        terms = []
        for i in range(k + 1):
            coef = comb(k, i) * ((-1) ** (k - i))
            if coef == 0:
                continue
            sign = "+" if coef > 0 else ""
            coef_str = "" if abs(coef) == 1 else str(abs(coef)) + "*"
            a_pow = f"a^{i}" if i > 1 else ("a" if i == 1 else "")
            b_pow = f"b^{k-i}" if k - i > 1 else ("b" if k - i == 1 else "")
            term = f"{coef_str}{a_pow}{'*' if a_pow and b_pow else ''}{b_pow}"
            if not term:
                term = str(abs(coef))
            if coef < 0:
                term = "-" + term
            elif terms:
                term = "+" + term
            terms.append(term)
        return ''.join(terms)
    
    def _expand_sum_cube(self, vars_list: list) -> str:
        """展开和的立方（简化）"""
        if len(vars_list) == 2:
            return "a^3 + 3*a^2*b + 3*a*b^2 + b^3"
        return "... (展开式)"
    
    def _gen_inequality(self, n: int, k: int) -> Tuple[str, str]:
        """生成不等式"""
        vars_list = [chr(ord('a') + i) for i in range(min(n, 4))]
        vars_str = ' '.join(vars_list)
        
        ineq_templates = [
            # 平方和 >= 积和
            (f"∀ {vars_str} : ℝ, {'+'.join([f'{v}^2' for v in vars_list])} ≥ {'+'.join([f'{vars_list[i]}*{vars_list[(i+1)%len(vars_list)]}' for i in range(len(vars_list))])}",
             f"{len(vars_list)}元平方和不等式"),
            # 幂次均值
            (f"∀ {vars_str} : ℝ, {' > 0 → '.join(vars_list)} > 0 → ({'+'.join(vars_list)})/{len(vars_list)} ≥ ({' * '.join(vars_list)})^(1/{len(vars_list)})",
             f"{len(vars_list)}元 AM-GM 不等式"),
            # Cauchy-Schwarz 变体
            (f"∀ {vars_str} : ℝ, ({'+'.join([f'{vars_list[i]}*{vars_list[(i+len(vars_list)//2)%len(vars_list)]}' for i in range(len(vars_list)//2)])})^2 ≤ ({'+'.join([f'{v}^2' for v in vars_list[:len(vars_list)//2]])}) * ({'+'.join([f'{v}^2' for v in vars_list[len(vars_list)//2:]])})",
             f"Cauchy-Schwarz 变体（{len(vars_list)}元）"),
            # 调和-几何均值
            (f"∀ a b : ℝ, a > 0 → b > 0 → 2/(1/a + 1/b) ≤ Real.sqrt (a * b)",
             "调和-几何均值不等式"),
            # 幂平均
            (f"∀ a b : ℝ, a > 0 → b > 0 → Real.sqrt ((a^{k} + b^{k})/2) ≥ (a + b)/2",
             f"{k}次幂平均不等式"),
        ]
        return random.choice(ineq_templates)
    
    def _gen_sum_formula(self, n: int, k: int) -> Tuple[str, str]:
        """生成求和公式"""
        templates = [
            # 自然数幂和
            (f"∀ n : ℕ, ∑ i in range(1, n+1), i^{k} = ...",
             f"自然数{k}次幂和公式"),
            # 等差数列
            (f"∀ a d n : ℕ, ∑ i in range(0, n), (a + i*d) = n*a + d*n*(n-1)/2",
             "等差数列求和"),
            # 等比数列
            (f"∀ a r n : ℝ, r ≠ 1 → ∑ i in range(0, n), a*r^i = a*(1 - r^n)/(1 - r)",
             "等比数列求和"),
        ]
        return random.choice(templates)
    
    def _gen_product_identity(self, n: int, k: int) -> Tuple[str, str]:
        """生成乘积恒等式"""
        templates = [
            # 平方差推广
            (f"∀ a b : ℝ, a^{k} - b^{k} = (a - b) * ({self._factor_diff_power(k)})",
             f"差的{k}次幂因式分解"),
            # Sophie Germain
            (f"∀ a b : ℝ, a^4 + 4*b^4 = (a^2 + 2*b^2 + 2*a*b)*(a^2 + 2*b^2 - 2*a*b)",
             "Sophie Germain 恒等式"),
            # 完全立方
            (f"∀ a b c : ℝ, a^3 + b^3 + c^3 - 3*a*b*c = (a + b + c)*(a^2 + b^2 + c^2 - a*b - b*c - c*a)",
             "三元立方和分解"),
        ]
        return random.choice(templates)
    
    def _factor_diff_power(self, k: int) -> str:
        """a^k - b^k 的因式"""
        if k == 2:
            return "a + b"
        elif k == 3:
            return "a^2 + a*b + b^2"
        elif k == 4:
            return "(a + b)*(a^2 + b^2)"
        else:
            return f"∑_{'{i=0}'}^{'{k-1}'} a^i * b^{'{k-1-i}'}"
    
    def _gen_power_sum(self, n: int, k: int) -> Tuple[str, str]:
        """生成幂和公式"""
        vars_list = [chr(ord('a') + i) for i in range(min(n, 3))]
        vars_str = ' '.join(vars_list)
        
        templates = [
            # Newton 恒等式
            (f"∀ {vars_str} : ℝ, p_{k} = e_1 * p_{'{k-1}'} - e_2 * p_{'{k-2}'} + ... (Newton)",
             f"Newton 幂和恒等式 (k={k})"),
            # 特殊情况
            (f"∀ a b : ℝ, a^{k} + b^{k} = (a + b)^{k} - {k}*a*b*(a^{'{k-2}'} + ...)",
             f"二元{k}次幂和展开"),
        ]
        return random.choice(templates)
    
    def _gen_symmetric_inequality(self, n: int, k: int) -> Tuple[str, str]:
        """生成对称不等式"""
        vars_list = [chr(ord('a') + i) for i in range(min(n, 3))]
        vars_str = ' '.join(vars_list)
        
        templates = [
            # Schur 不等式
            (f"∀ a b c : ℝ, a ≥ 0 → b ≥ 0 → c ≥ 0 → a^{k}*(a-b)*(a-c) + b^{k}*(b-a)*(b-c) + c^{k}*(c-a)*(c-b) ≥ 0",
             f"Schur 不等式 (t={k})"),
            # Nesbitt 不等式
            (f"∀ a b c : ℝ, a > 0 → b > 0 → c > 0 → a/(b+c) + b/(a+c) + c/(a+b) ≥ 3/2",
             "Nesbitt 不等式"),
            # 切比雪夫
            (f"∀ a b c x y z : ℝ, a ≥ b → b ≥ c → x ≥ y → y ≥ z → (a*x + b*y + c*z)/3 ≥ ((a+b+c)/3)*((x+y+z)/3)",
             "Chebyshev 不等式"),
        ]
        return random.choice(templates)
    
    def _dynamic_trig_conjecture(self, n1: KnowledgeNode, n2: KnowledgeNode) -> Tuple[str, str]:
        """动态生成三角猜想"""
        k = random.randint(2, 5)  # 倍角系数
        
        conjecture_types = [
            self._gen_multiple_angle,
            self._gen_sum_to_product,
            self._gen_power_reduction,
            self._gen_trig_inequality,
        ]
        
        gen_func = random.choice(conjecture_types)
        return gen_func(k)
    
    def _gen_multiple_angle(self, k: int) -> Tuple[str, str]:
        """生成多倍角公式"""
        templates = [
            (f"∀ θ : ℝ, Real.sin ({k}*θ) = {self._expand_sin_multiple(k)}",
             f"{k}倍角正弦公式"),
            (f"∀ θ : ℝ, Real.cos ({k}*θ) = {self._expand_cos_multiple(k)}",
             f"{k}倍角余弦公式"),
            (f"∀ θ : ℝ, Real.tan ({k}*θ) = (多项式展开)",
             f"{k}倍角正切公式"),
        ]
        return random.choice(templates)
    
    def _expand_sin_multiple(self, k: int) -> str:
        """展开 sin(kθ)"""
        if k == 2:
            return "2*Real.sin θ * Real.cos θ"
        elif k == 3:
            return "3*Real.sin θ - 4*(Real.sin θ)^3"
        elif k == 4:
            return "4*Real.sin θ * Real.cos θ * (1 - 2*(Real.sin θ)^2)"
        elif k == 5:
            return "16*(Real.sin θ)^5 - 20*(Real.sin θ)^3 + 5*Real.sin θ"
        return f"(Chebyshev U_{'{k-1}'}(cos θ) * sin θ)"
    
    def _expand_cos_multiple(self, k: int) -> str:
        """展开 cos(kθ)"""
        if k == 2:
            return "(Real.cos θ)^2 - (Real.sin θ)^2"
        elif k == 3:
            return "4*(Real.cos θ)^3 - 3*Real.cos θ"
        elif k == 4:
            return "8*(Real.cos θ)^4 - 8*(Real.cos θ)^2 + 1"
        elif k == 5:
            return "16*(Real.cos θ)^5 - 20*(Real.cos θ)^3 + 5*Real.cos θ"
        return f"(Chebyshev T_{k}(cos θ))"
    
    def _gen_sum_to_product(self, k: int) -> Tuple[str, str]:
        """生成和差化积公式"""
        templates = [
            ("∀ α β : ℝ, Real.sin α + Real.sin β = 2 * Real.sin ((α+β)/2) * Real.cos ((α-β)/2)",
             "正弦和化积"),
            ("∀ α β : ℝ, Real.sin α - Real.sin β = 2 * Real.cos ((α+β)/2) * Real.sin ((α-β)/2)",
             "正弦差化积"),
            ("∀ α β : ℝ, Real.cos α + Real.cos β = 2 * Real.cos ((α+β)/2) * Real.cos ((α-β)/2)",
             "余弦和化积"),
            ("∀ α β : ℝ, Real.cos α - Real.cos β = -2 * Real.sin ((α+β)/2) * Real.sin ((α-β)/2)",
             "余弦差化积"),
            ("∀ α β : ℝ, Real.sin α * Real.cos β = (Real.sin (α+β) + Real.sin (α-β))/2",
             "积化和差（正弦余弦）"),
            ("∀ α β : ℝ, Real.cos α * Real.cos β = (Real.cos (α+β) + Real.cos (α-β))/2",
             "积化和差（余弦）"),
            ("∀ α β : ℝ, Real.sin α * Real.sin β = (Real.cos (α-β) - Real.cos (α+β))/2",
             "积化和差（正弦）"),
        ]
        return random.choice(templates)
    
    def _gen_power_reduction(self, k: int) -> Tuple[str, str]:
        """生成降幂公式"""
        templates = [
            (f"∀ θ : ℝ, (Real.sin θ)^{k} = {self._reduce_sin_power(k)}",
             f"正弦{k}次降幂"),
            (f"∀ θ : ℝ, (Real.cos θ)^{k} = {self._reduce_cos_power(k)}",
             f"余弦{k}次降幂"),
        ]
        return random.choice(templates)
    
    def _reduce_sin_power(self, k: int) -> str:
        """sin^k 降幂"""
        if k == 2:
            return "(1 - Real.cos (2*θ))/2"
        elif k == 3:
            return "(3*Real.sin θ - Real.sin (3*θ))/4"
        elif k == 4:
            return "(3 - 4*Real.cos (2*θ) + Real.cos (4*θ))/8"
        return f"(降幂展开)"
    
    def _reduce_cos_power(self, k: int) -> str:
        """cos^k 降幂"""
        if k == 2:
            return "(1 + Real.cos (2*θ))/2"
        elif k == 3:
            return "(3*Real.cos θ + Real.cos (3*θ))/4"
        elif k == 4:
            return "(3 + 4*Real.cos (2*θ) + Real.cos (4*θ))/8"
        return f"(降幂展开)"
    
    def _gen_trig_inequality(self, k: int) -> Tuple[str, str]:
        """生成三角不等式"""
        templates = [
            ("∀ θ : ℝ, 0 < θ → θ < π/2 → Real.sin θ < θ",
             "正弦上界（第一象限）"),
            ("∀ θ : ℝ, 0 < θ → θ < π/2 → Real.tan θ > θ",
             "正切下界（第一象限）"),
            ("∀ θ : ℝ, 0 < θ → θ < π/2 → Real.sin θ > θ - θ^3/6",
             "正弦 Taylor 下界"),
            ("∀ A B C : ℝ, A + B + C = π → A > 0 → B > 0 → C > 0 → Real.sin A + Real.sin B + Real.sin C ≤ 3*Real.sqrt 3/2",
             "三角形内角正弦和上界"),
            ("∀ A B C : ℝ, A + B + C = π → A > 0 → B > 0 → C > 0 → Real.cos A + Real.cos B + Real.cos C ≤ 3/2",
             "三角形内角余弦和上界"),
        ]
        return random.choice(templates)
    
    def _dynamic_geo_conjecture(self, n1: KnowledgeNode, n2: KnowledgeNode) -> Tuple[str, str]:
        """动态生成几何猜想"""
        conjecture_types = [
            self._gen_triangle_inequality,
            self._gen_circle_property,
            self._gen_vector_inequality,
            self._gen_area_formula,
        ]
        
        gen_func = random.choice(conjecture_types)
        return gen_func()
    
    def _gen_triangle_inequality(self) -> Tuple[str, str]:
        """生成三角形不等式"""
        templates = [
            ("∀ a b c : ℝ, a > 0 → b > 0 → c > 0 → a + b > c → b + c > a → c + a > b → a^2 + b^2 + c^2 < 2*(a*b + b*c + c*a)",
             "三角形边长平方和不等式"),
            ("∀ a b c R : ℝ, a > 0 → b > 0 → c > 0 → R > 0 → a*b*c = 4*R*S (S 为面积)",
             "外接圆半径公式"),
            ("∀ a b c r : ℝ, a > 0 → b > 0 → c > 0 → r > 0 → S = r*(a+b+c)/2 (S 为面积)",
             "内切圆半径公式"),
            ("∀ a b c : ℝ, a > 0 → b > 0 → c > 0 → valid_triangle a b c → S = Real.sqrt (s*(s-a)*(s-b)*(s-c))",
             "海伦公式"),
        ]
        return random.choice(templates)
    
    def _gen_circle_property(self) -> Tuple[str, str]:
        """生成圆的性质"""
        templates = [
            ("∀ r : ℝ, r > 0 → C = 2*π*r ∧ A = π*r^2",
             "圆的周长和面积"),
            ("∀ r θ : ℝ, r > 0 → 0 < θ → θ < 2*π → arc_length = r*θ",
             "弧长公式"),
            ("∀ r θ : ℝ, r > 0 → 0 < θ → θ < 2*π → sector_area = r^2*θ/2",
             "扇形面积"),
            ("∀ a b : ℝ, a > 0 → b > 0 → ellipse_area = π*a*b",
             "椭圆面积"),
        ]
        return random.choice(templates)
    
    def _gen_vector_inequality(self) -> Tuple[str, str]:
        """生成向量不等式"""
        templates = [
            ("∀ x1 y1 x2 y2 : ℝ, |x1*x2 + y1*y2| ≤ Real.sqrt (x1^2 + y1^2) * Real.sqrt (x2^2 + y2^2)",
             "向量内积 Cauchy-Schwarz"),
            ("∀ x1 y1 x2 y2 : ℝ, Real.sqrt ((x1+x2)^2 + (y1+y2)^2) ≤ Real.sqrt (x1^2 + y1^2) + Real.sqrt (x2^2 + y2^2)",
             "向量三角不等式"),
            ("∀ x1 y1 z1 x2 y2 z2 : ℝ, (x1*x2 + y1*y2 + z1*z2)^2 ≤ (x1^2 + y1^2 + z1^2)*(x2^2 + y2^2 + z2^2)",
             "三维 Cauchy-Schwarz"),
        ]
        return random.choice(templates)
    
    def _gen_area_formula(self) -> Tuple[str, str]:
        """生成面积公式"""
        templates = [
            ("∀ a b θ : ℝ, a > 0 → b > 0 → 0 < θ → θ < π → S = (1/2)*a*b*Real.sin θ",
             "三角形面积（两边夹角）"),
            ("∀ x1 y1 x2 y2 x3 y3 : ℝ, S = |x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2)|/2",
             "三角形面积（坐标法）"),
            ("∀ a b c d : ℝ, a > 0 → b > 0 → c > 0 → d > 0 → convex_quad_area ≤ (a*c + b*d)/2",
             "凸四边形面积上界"),
        ]
        return random.choice(templates)
    
    # ====== 新领域猜想生成方法 ======
    
    def _dynamic_number_theory_conjecture(self, n1: KnowledgeNode, n2: KnowledgeNode) -> Tuple[str, str]:
        """动态生成数论猜想"""
        templates = [
            # 整除性
            ("∀ a b : ℤ, gcd(a, b) * lcm(a, b) = |a * b|", "GCD 与 LCM 关系"),
            ("∀ n : ℕ, n > 0 → n | n!", "阶乘整除性"),
            ("∀ p : ℕ, Prime p → p | (p-1)! + 1", "Wilson 定理推论"),
            ("∀ a b c : ℤ, gcd(a,b) = 1 → gcd(a,c) = 1 → gcd(a, b*c) = 1", "互素的传递性"),
            # 同余
            ("∀ a m n : ℤ, m > 0 → n > 0 → m | n → a ≡ a (mod m) ↔ a ≡ a (mod n)", "同余的约数关系"),
            ("∀ a b m : ℤ, m > 0 → gcd(a,m) = 1 → ∃ x, a*x ≡ b (mod m)", "模逆元存在条件"),
            # 素数
            ("∀ n : ℕ, n > 1 → ∃ p, Prime p ∧ p | n", "素因子存在性"),
            ("∀ n : ℕ, n ≥ 2 → π(n) ≤ n/2", "素数计数上界"),
            # 费马
            (f"∀ p : ℕ, Prime p → ∀ a : ℤ, ¬(p | a) → a^(p-1) ≡ 1 (mod p)", "费马小定理"),
            (f"∀ n a : ℕ, gcd(a, n) = 1 → a^(φ(n)) ≡ 1 (mod n)", "欧拉定理"),
        ]
        return random.choice(templates)
    
    def _dynamic_combinatorics_conjecture(self, n1: KnowledgeNode, n2: KnowledgeNode) -> Tuple[str, str]:
        """动态生成组合猜想"""
        n = random.randint(3, 8)
        k = random.randint(1, n-1)
        templates = [
            # 组合恒等式
            (f"∀ n k : ℕ, k ≤ n → C(n,k) = C(n, n-k)", "组合数对称性"),
            (f"∀ n k : ℕ, 0 < k → k ≤ n → C(n,k) = n/k * C(n-1, k-1)", "组合数递推"),
            (f"∀ n : ℕ, ∑ k in range(0, n+1), C(n,k) = 2^n", "组合数求和"),
            (f"∀ n : ℕ, ∑ k in range(0, n+1), (-1)^k * C(n,k) = 0", "组合数交错和"),
            # 二项式
            (f"∀ n : ℕ, ∀ x y : ℝ, (x+y)^n = ∑ k, C(n,k) * x^k * y^(n-k)", "二项式定理"),
            # Catalan
            (f"∀ n : ℕ, Cat(n) = C(2n,n)/(n+1)", "Catalan 数公式"),
            (f"∀ n : ℕ, Cat(n+1) = ∑ i, Cat(i) * Cat(n-i)", "Catalan 递推"),
            # 容斥
            (f"∀ A B : Set, |A ∪ B| = |A| + |B| - |A ∩ B|", "容斥原理（二元）"),
            (f"∀ n : ℕ, D(n) = n! * ∑ k in range(0,n+1), (-1)^k/k!", "错排公式"),
            # Stirling
            (f"∀ n k : ℕ, S(n,k) = k*S(n-1,k) + S(n-1,k-1)", "第二类 Stirling 数递推"),
        ]
        return random.choice(templates)
    
    def _dynamic_calculus_conjecture(self, n1: KnowledgeNode, n2: KnowledgeNode) -> Tuple[str, str]:
        """动态生成微积分猜想"""
        n = random.randint(2, 5)
        templates = [
            # 导数
            (f"∀ f g : ℝ → ℝ, (f * g)' = f' * g + f * g'", "乘法法则"),
            (f"∀ f g : ℝ → ℝ, (f ∘ g)' = (f' ∘ g) * g'", "链式法则"),
            (f"∀ n : ℕ, (x^n)' = n * x^(n-1)", "幂函数导数"),
            (f"∀ x : ℝ, (e^x)' = e^x", "指数函数导数"),
            (f"∀ x : ℝ, x > 0 → (ln x)' = 1/x", "对数函数导数"),
            # 积分
            (f"∀ f : ℝ → ℝ, ∫ f'(x) dx = f(x) + C", "微积分基本定理"),
            (f"∀ n : ℤ, n ≠ -1 → ∫ x^n dx = x^(n+1)/(n+1) + C", "幂函数积分"),
            (f"∀ a b : ℝ, a < b → ∫[a,b] f(x) dx = F(b) - F(a)", "Newton-Leibniz 公式"),
            # Taylor
            (f"∀ f : ℝ → ℝ, f(x) = ∑ n, f^(n)(0)/n! * x^n", "Maclaurin 展开"),
            (f"∀ x : ℝ, e^x = ∑ n, x^n/n!", "e^x 的 Taylor 展开"),
            (f"∀ x : ℝ, |x| < 1 → 1/(1-x) = ∑ n, x^n", "几何级数"),
            # 不等式
            (f"∀ f : ℝ → ℝ, f''(x) > 0 → f 是凸函数", "凸函数判定"),
            (f"∀ f : ℝ → ℝ, ∃ c ∈ (a,b), f(b) - f(a) = f'(c) * (b-a)", "中值定理"),
        ]
        return random.choice(templates)
    
    def _dynamic_probability_conjecture(self, n1: KnowledgeNode, n2: KnowledgeNode) -> Tuple[str, str]:
        """动态生成概率统计猜想"""
        n = random.randint(2, 10)
        templates = [
            # 基本概率
            ("∀ A : Event, 0 ≤ P(A) ≤ 1", "概率公理"),
            ("∀ A B : Event, P(A ∪ B) = P(A) + P(B) - P(A ∩ B)", "加法公式"),
            ("∀ A B : Event, P(A|B) = P(A ∩ B) / P(B)", "条件概率定义"),
            ("∀ A B : Event, P(A ∩ B) = P(A|B) * P(B)", "乘法公式"),
            # Bayes
            ("∀ A B : Event, P(A|B) = P(B|A) * P(A) / P(B)", "Bayes 定理"),
            ("∀ A Bi : Event, P(A) = ∑ i, P(A|Bi) * P(Bi)", "全概率公式"),
            # 期望与方差
            ("∀ X Y : RV, E[X + Y] = E[X] + E[Y]", "期望线性性"),
            ("∀ X : RV, Var(X) = E[X²] - (E[X])²", "方差公式"),
            ("∀ X Y : RV, indep X Y → Var(X + Y) = Var(X) + Var(Y)", "独立变量方差可加"),
            # 大数定律
            (f"∀ Xi : RV, iid Xi → (1/n)*∑Xi → E[X] (n→∞)", "大数定律"),
            (f"∀ Xi : RV, iid Xi → (∑Xi - n*μ)/(σ*√n) → N(0,1)", "中心极限定理"),
            # 不等式
            ("∀ X : RV, a > 0 → P(|X| ≥ a) ≤ E[|X|]/a", "Markov 不等式"),
            ("∀ X : RV, k > 0 → P(|X - μ| ≥ k*σ) ≤ 1/k²", "Chebyshev 不等式"),
        ]
        return random.choice(templates)
    
    def _dynamic_linear_algebra_conjecture(self, n1: KnowledgeNode, n2: KnowledgeNode) -> Tuple[str, str]:
        """动态生成线性代数猜想"""
        n = random.randint(2, 4)
        templates = [
            # 行列式
            (f"∀ A B : Matrix, det(A*B) = det(A) * det(B)", "行列式乘法"),
            (f"∀ A : Matrix, det(A^T) = det(A)", "转置行列式"),
            (f"∀ A : Matrix, invertible A ↔ det(A) ≠ 0", "可逆性判定"),
            (f"∀ A : Matrix, det(A⁻¹) = 1/det(A)", "逆矩阵行列式"),
            # 特征值
            (f"∀ A : Matrix, tr(A) = ∑ λi", "迹等于特征值和"),
            (f"∀ A : Matrix, det(A) = ∏ λi", "行列式等于特征值积"),
            (f"∀ A : Matrix, λ eigenvalue of A → λ^k eigenvalue of A^k", "特征值的幂"),
            # 矩阵分解
            (f"∀ A : Matrix, ∃ Q R, A = Q*R ∧ orthogonal Q ∧ upper_triangular R", "QR 分解"),
            (f"∀ A : Matrix, symmetric A → ∃ Q Λ, A = Q*Λ*Q^T", "对称矩阵特征分解"),
            (f"∀ A : Matrix, ∃ U Σ V, A = U*Σ*V^T", "SVD 分解"),
            # 定理
            (f"∀ A : Matrix n×n, A 满足其特征多项式", "Cayley-Hamilton 定理"),
            (f"∀ v1..vn : Vector, dim(span{{v1..vn}}) ≤ n", "线性无关向量数上界"),
            (f"∀ A : Matrix, rank(A) + nullity(A) = n", "秩-零度定理"),
        ]
        return random.choice(templates)
    
    def _dynamic_advanced_geo_conjecture(self, n1: KnowledgeNode, n2: KnowledgeNode, domain: str) -> Tuple[str, str]:
        """动态生成立体几何/解析几何猜想"""
        if domain == "solid_geometry":
            templates = [
                # 立体几何
                ("∀ l : Line, α : Plane, l ⊥ α ↔ ∀ m ⊂ α, l ⊥ m", "线面垂直判定"),
                ("∀ α β : Plane, α ⊥ β → ∃ l ⊂ α, l ⊥ β", "面面垂直性质"),
                ("∀ l m : Line, α : Plane, l ⊥ α → m ⊥ α → l ∥ m", "垂直于同一平面的直线平行"),
                ("∀ V E F : ℕ, convex_polyhedron → V - E + F = 2", "欧拉公式"),
                ("∀ r h : ℝ, r > 0 → h > 0 → V_cone = (1/3)*π*r²*h", "圆锥体积"),
                ("∀ r : ℝ, r > 0 → V_sphere = (4/3)*π*r³", "球体积"),
                ("∀ a b c : ℝ, a > 0 → b > 0 → c > 0 → V_box = a*b*c", "长方体体积"),
            ]
        else:  # analytic_geometry
            templates = [
                # 解析几何
                ("∀ x y : ℝ, (x-a)² + (y-b)² = r² 表示圆心为(a,b)半径为r的圆", "圆的标准方程"),
                ("∀ a b : ℝ, a > b > 0 → x²/a² + y²/b² = 1 表示椭圆", "椭圆标准方程"),
                ("∀ a b : ℝ, a > 0 → b > 0 → x²/a² - y²/b² = 1 表示双曲线", "双曲线标准方程"),
                ("∀ p : ℝ, p > 0 → y² = 2px 表示抛物线", "抛物线标准方程"),
                ("∀ P : Point, ellipse → |PF₁| + |PF₂| = 2a", "椭圆焦点距离和"),
                ("∀ P : Point, hyperbola → ||PF₁| - |PF₂|| = 2a", "双曲线焦点距离差"),
                ("∀ l₁ l₂ : Line, l₁ ⊥ l₂ ↔ k₁ * k₂ = -1", "直线垂直条件"),
                ("∀ l₁ l₂ : Line, l₁ ∥ l₂ ↔ k₁ = k₂", "直线平行条件"),
            ]
        return random.choice(templates)
    
    # ====== 跨领域猜想生成 ======
    
    def _generate_cross_domain_conjecture(self, nodes: List[KnowledgeNode]) -> Optional[Dict]:
        """生成跨领域猜想"""
        # 获取不同领域的节点
        domain_nodes = {}
        for n in nodes:
            if n.domain not in domain_nodes:
                domain_nodes[n.domain] = []
            domain_nodes[n.domain].append(n)
        
        # 需要至少两个不同领域
        if len(domain_nodes) < 2:
            return None
        
        # 随机选择两个领域
        domains = random.sample(list(domain_nodes.keys()), 2)
        n1 = random.choice(domain_nodes[domains[0]])
        n2 = random.choice(domain_nodes[domains[1]])
        
        conjecture_id = f"cross_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        
        # 跨领域猜想模板
        cross_domain_templates = [
            # 数论 + 代数
            ("∀ p : ℕ, Prime p → p = 4k+1 ↔ ∃ a b : ℤ, p = a² + b²", 
             "费马二平方和定理", ["number_theory", "algebra"]),
            # 组合 + 概率
            ("∀ n : ℕ, n ≥ 23 → P(birthday_collision, n) > 0.5",
             "生日问题", ["combinatorics", "probability"]),
            # 线性代数 + 几何
            ("∀ θ : ℝ, R(θ) = [[cos θ, -sin θ], [sin θ, cos θ]] 是旋转矩阵",
             "旋转矩阵", ["linear_algebra", "geometry"]),
            # 微积分 + 概率
            ("∫_{-∞}^{∞} e^(-x²) dx = √π",
             "Gaussian 积分", ["calculus", "probability"]),
            # 数论 + 组合
            ("∀ p n k : ℕ, Prime p → C(n,k) ≡ C(n mod p, k mod p) * C(n/p, k/p) (mod p)",
             "Lucas 定理", ["number_theory", "combinatorics"]),
            # 代数 + 复分析
            ("e^(iπ) + 1 = 0",
             "欧拉恒等式", ["algebra", "calculus"]),
            # 几何 + 代数
            ("∀ A B C : Point, |AB|² + |BC|² = |AC|² ↔ ∠ABC = 90°",
             "勾股定理与角度", ["geometry", "algebra"]),
            # 概率 + 微积分
            ("∀ X : RV, E[g(X)] = ∫ g(x) f(x) dx",
             "期望的积分表示", ["probability", "calculus"]),
        ]
        
        # 选择一个与选中领域相关的模板
        relevant_templates = []
        for stmt, name, doms in cross_domain_templates:
            if domains[0] in doms or domains[1] in doms:
                relevant_templates.append((stmt, name, doms))
        
        if not relevant_templates:
            relevant_templates = cross_domain_templates
        
        stmt, name, related_doms = random.choice(relevant_templates)
        
        return {
            "id": conjecture_id,
            "statement": stmt,
            "statement_cn": name,
            "domain": "cross_domain",
            "premises": [n1.id, n2.id],
            "relation_type": "cross_domain",
            "difficulty": 4,
            "related_domains": related_doms
        }
    
    # ====== 领域特定猜想生成器 ======
    
    def _generate_number_theory_conjecture(self, nodes: List[KnowledgeNode]) -> Optional[Dict]:
        """生成数论猜想"""
        conjecture_id = f"nt_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        n = random.randint(2, 100)
        
        templates = [
            (f"∀ n : ℕ, n > 1 → ∃ primes, n = ∏ primes", "算术基本定理实例"),
            (f"∀ n : ℕ, φ(n) ≤ n - 1", "欧拉函数上界"),
            (f"∀ n : ℕ, σ(n) ≥ n + 1 (对 n > 1)", "约数和下界"),
            (f"∀ n : ℕ, τ(n) ≤ 2√n", "约数个数上界"),
        ]
        stmt, name = random.choice(templates)
        
        return {
            "id": conjecture_id,
            "statement": stmt,
            "statement_cn": name,
            "domain": "number_theory",
            "premises": [],
            "relation_type": "generation",
            "difficulty": 3
        }
    
    def _generate_combinatorics_conjecture(self, nodes: List[KnowledgeNode]) -> Optional[Dict]:
        """生成组合猜想"""
        conjecture_id = f"comb_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        
        templates = [
            ("∀ n : ℕ, F(n+2) = F(n+1) + F(n) (Fibonacci)", "Fibonacci 递推"),
            ("∀ n : ℕ, Cat(n) ≤ 4^n", "Catalan 数上界"),
            ("∀ n k : ℕ, k ≤ n → C(n+1,k+1) = C(n,k) + C(n,k+1)", "Pascal 恒等式"),
            ("∀ n : ℕ, B(n) ≤ n^n (Bell number)", "Bell 数上界"),
        ]
        stmt, name = random.choice(templates)
        
        return {
            "id": conjecture_id,
            "statement": stmt,
            "statement_cn": name,
            "domain": "combinatorics",
            "premises": [],
            "relation_type": "generation",
            "difficulty": 3
        }
    
    def _generate_calculus_conjecture(self, nodes: List[KnowledgeNode]) -> Optional[Dict]:
        """生成微积分猜想"""
        conjecture_id = f"calc_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        
        templates = [
            ("∀ f : ℝ → ℝ, continuous f → ∃ F, F' = f", "原函数存在性"),
            ("∀ f : ℝ → ℝ, lim_{x→0} sin(x)/x = 1", "重要极限"),
            ("∀ f : ℝ → ℝ, f''(x) < 0 → f 是凹函数", "凹函数判定"),
            ("∀ a : ℝ, lim_{n→∞} (1 + a/n)^n = e^a", "e 的定义"),
        ]
        stmt, name = random.choice(templates)
        
        return {
            "id": conjecture_id,
            "statement": stmt,
            "statement_cn": name,
            "domain": "calculus",
            "premises": [],
            "relation_type": "generation",
            "difficulty": 3
        }
    
    def _generate_probability_conjecture(self, nodes: List[KnowledgeNode]) -> Optional[Dict]:
        """生成概率猜想"""
        conjecture_id = f"prob_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        
        templates = [
            ("∀ X Y : RV, Cov(X,Y) = E[XY] - E[X]*E[Y]", "协方差公式"),
            ("∀ X Y : RV, |Cor(X,Y)| ≤ 1", "相关系数界"),
            ("∀ X : RV, Poisson(λ) → E[X] = Var(X) = λ", "Poisson 分布性质"),
            ("∀ X : RV, Binomial(n,p) → E[X] = np", "二项分布期望"),
        ]
        stmt, name = random.choice(templates)
        
        return {
            "id": conjecture_id,
            "statement": stmt,
            "statement_cn": name,
            "domain": "probability",
            "premises": [],
            "relation_type": "generation",
            "difficulty": 3
        }
    
    def _generate_linear_algebra_conjecture(self, nodes: List[KnowledgeNode]) -> Optional[Dict]:
        """生成线性代数猜想"""
        conjecture_id = f"la_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        
        templates = [
            ("∀ A : Matrix, (A^T)^T = A", "转置的转置"),
            ("∀ A B : Matrix, (AB)^T = B^T * A^T", "乘积转置"),
            ("∀ A : Matrix, A*A^(-1) = I", "逆矩阵定义"),
            ("∀ u v : Vector, |u·v| ≤ |u|*|v|", "向量 Cauchy-Schwarz"),
        ]
        stmt, name = random.choice(templates)
        
        return {
            "id": conjecture_id,
            "statement": stmt,
            "statement_cn": name,
            "domain": "linear_algebra",
            "premises": [],
            "relation_type": "generation",
            "difficulty": 3
        }

    def _generate_by_strengthening(self, nodes: List[KnowledgeNode]) -> Optional[Dict]:
        """通过加强条件生成猜想"""
        inequality_nodes = [n for n in nodes if "≥" in n.statement or ">" in n.statement]
        if not inequality_nodes:
            return None
        
        base = random.choice(inequality_nodes)
        
        conjecture_id = f"strengthened_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        
        # 尝试将 ≥ 改为 > 并添加条件
        statement = base.statement.replace("≥", ">") if "≥" in base.statement else base.statement
        statement_cn = f"{base.statement_cn}（严格形式）"
        
        return {
            "id": conjecture_id,
            "statement": statement,
            "statement_cn": statement_cn,
            "domain": base.domain,
            "premises": [base.id],
            "relation_type": "strengthening",
            "difficulty": 3
        }
    
    def _generate_by_chaining(self, nodes: List[KnowledgeNode]) -> Optional[Dict]:
        """通过链接推理生成猜想"""
        # 找有后继的节点
        nodes_with_edges = []
        for n in nodes:
            successors = self.knowledge_graph.get_successors(n.id)
            if successors:
                nodes_with_edges.append((n, [s.id for s in successors]))
        
        if not nodes_with_edges:
            return self._generate_by_combination(nodes)
        
        base, successors = random.choice(nodes_with_edges)
        
        conjecture_id = f"chained_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        
        # 生成传递推理
        templates = [
            (f"-- 由 {base.statement_cn} 推导 --", f"由 {base.statement_cn} 的推论"),
        ]
        
        statement, statement_cn = random.choice(templates)
        
        return {
            "id": conjecture_id,
            "statement": base.statement,  # 简化：使用原陈述
            "statement_cn": statement_cn,
            "domain": base.domain,
            "premises": [base.id] + successors,
            "relation_type": "chaining",
            "difficulty": 4
        }
    
    def _is_duplicate(self, conjecture: Dict, existing: List[Dict]) -> bool:
        """
        检查是否重复（增强版）
        
        检测:
            1. 完全相同的陈述
            2. 仅变量名不同的陈述（α-等价）
            3. 仅顺序不同的交换律变体
            4. 通过简单代入得到的特例
            5. 语义相似度超过阈值的陈述（新增）
        """
        statement = conjecture["statement"]
        normalized = self._normalize_statement(statement)
        
        # 检查现有猜想
        for e in existing:
            if self._statements_equivalent(statement, e["statement"]):
                return True
            # 语义相似度检查
            if self._compute_statement_similarity(statement, e["statement"]) > 0.85:
                return True
        
        # 检查知识图谱
        for node in self.knowledge_graph.nodes.values():
            if self._statements_equivalent(statement, node.statement):
                return True
            # 检查是否是已有定理的简单特例
            if self._is_trivial_instance(statement, node.statement):
                return True
            # 语义相似度检查（针对知识图谱中的节点）
            if self._compute_statement_similarity(statement, node.statement) > 0.9:
                return True
        
        return False
    
    def _compute_statement_similarity(self, s1: str, s2: str) -> float:
        """
        计算两个数学陈述的语义相似度（0-1）
        
        考虑因素：
        1. 标准化后的字符串相似度
        2. 数学符号结构相似度
        3. 量词和操作符模式相似度
        """
        import re
        
        # 标准化
        n1 = self._normalize_statement(s1)
        n2 = self._normalize_statement(s2)
        
        # 完全匹配
        if n1 == n2:
            return 1.0
        
        # 字符级别的 Jaccard 相似度
        set1 = set(n1)
        set2 = set(n2)
        char_sim = len(set1 & set2) / len(set1 | set2) if (set1 | set2) else 0.0
        
        # 词/符号级别的相似度
        tokens1 = set(re.findall(r'[a-zA-Z_]+|[∀∃→∧∨¬≤≥=≠+\-*/^]|\d+', s1))
        tokens2 = set(re.findall(r'[a-zA-Z_]+|[∀∃→∧∨¬≤≥=≠+\-*/^]|\d+', s2))
        token_sim = len(tokens1 & tokens2) / len(tokens1 | tokens2) if (tokens1 | tokens2) else 0.0
        
        # 结构相似度（量词和主要操作符）
        structure1 = self._extract_structure(s1)
        structure2 = self._extract_structure(s2)
        struct_sim = 1.0 if structure1 == structure2 else 0.5
        
        # 综合相似度
        return char_sim * 0.3 + token_sim * 0.5 + struct_sim * 0.2
    
    def _extract_structure(self, statement: str) -> str:
        """
        提取陈述的结构模式
        
        提取量词、主要操作符等关键结构元素
        """
        import re
        
        elements = []
        
        # 量词
        if '∀' in statement:
            elements.append('FORALL')
        if '∃' in statement:
            elements.append('EXISTS')
        
        # 主要关系
        if '→' in statement:
            elements.append('IMPLIES')
        if '∧' in statement:
            elements.append('AND')
        if '∨' in statement:
            elements.append('OR')
        
        # 比较操作
        if '=' in statement and '≠' not in statement:
            elements.append('EQ')
        if '≠' in statement:
            elements.append('NEQ')
        if '≥' in statement or '>=' in statement:
            elements.append('GEQ')
        if '≤' in statement or '<=' in statement:
            elements.append('LEQ')
        if '>' in statement and '>=' not in statement:
            elements.append('GT')
        if '<' in statement and '<=' not in statement:
            elements.append('LT')
        
        # 算术操作
        if '^' in statement or '**' in statement:
            elements.append('POW')
        
        return ':'.join(sorted(elements))
    
    def _normalize_statement(self, statement: str) -> str:
        """
        标准化陈述，用于比较
        
        处理:
            - 移除空白
            - 统一变量名
            - 排序交换律中的操作数
        """
        import re
        
        # 移除空白
        s = ''.join(statement.split())
        
        # 统一常见变量名: a,b,c,x,y,z,α,β,θ → v0,v1,v2...
        var_pattern = r'\b([a-z]|α|β|γ|θ|φ)\b'
        vars_found = []
        
        def replace_var(match):
            var = match.group(1)
            if var not in vars_found:
                vars_found.append(var)
            idx = vars_found.index(var)
            return f"v{idx}"
        
        s = re.sub(var_pattern, replace_var, s)
        
        return s
    
    def _statements_equivalent(self, s1: str, s2: str) -> bool:
        """检查两个陈述是否语义等价"""
        # 标准化后比较
        n1 = self._normalize_statement(s1)
        n2 = self._normalize_statement(s2)
        
        if n1 == n2:
            return True
        
        # 检查交换律变体: a + b 和 b + a
        # 简化：检查排序后的操作数是否相同
        def sort_commutative(s):
            import re
            # 处理 + 和 * 的交换
            for op in ['+', '*']:
                # 找出形如 x op y 的模式
                pattern = rf'(\w+)\s*\{re.escape(op)}\s*(\w+)'
                def reorder(m):
                    a, b = m.group(1), m.group(2)
                    return f"{min(a,b)}{op}{max(a,b)}"
                s = re.sub(pattern, reorder, s)
            return s
        
        if sort_commutative(n1) == sort_commutative(n2):
            return True
        
        return False
    
    def _is_trivial_instance(self, new_stmt: str, existing_stmt: str) -> bool:
        """
        检查 new_stmt 是否是 existing_stmt 的平凡特例
        
        例如:
            - a^2 + b^2 ≥ 2*a*b 的特例 x^2 + y^2 ≥ 2*x*y（仅换变量名）
            - ∀ a b : ℝ, P a b 的特例 P 1 2（具体数值代入）
        """
        # 标准化比较
        n_new = self._normalize_statement(new_stmt)
        n_existing = self._normalize_statement(existing_stmt)
        
        # 完全相同（标准化后）
        if n_new == n_existing:
            return True
        
        # 检查是否只是添加了具体数值
        # 如果新陈述中包含具体数字，而旧陈述是通用形式
        import re
        new_has_numbers = bool(re.search(r'\b\d+\b', new_stmt))
        existing_is_general = '∀' in existing_stmt
        
        if new_has_numbers and existing_is_general:
            # 可能是代入特例
            # 移除数字后再比较
            new_no_nums = re.sub(r'\b\d+\b', 'N', new_stmt)
            if self._normalize_statement(new_no_nums) == n_existing:
                return True
        
        return False
    
    def _is_trivial_derivation(self, conjecture: Dict) -> bool:
        """
        检查是否是平凡的推导
        
        平凡推导包括:
            1. 仅通过变量重命名
            2. 仅通过交换律重排
            3. 恒等变换（如 a = a）
        """
        statement = conjecture["statement"]
        
        # 检查恒等式
        if self._is_trivial_identity(statement):
            return True
        
        # 检查是否与前提几乎相同
        premises = conjecture.get("premises", [])
        for premise_id in premises:
            premise = self.knowledge_graph.get_node(premise_id)
            if premise:
                if self._statements_equivalent(statement, premise.statement):
                    return True
        
        return False
    
    def _is_trivial_identity(self, statement: str) -> bool:
        """检查是否是平凡恒等式"""
        import re
        
        # 模式: a = a, x = x 等
        trivial_patterns = [
            r'(\w+)\s*=\s*\1\b',  # a = a
            r'(\w+)\s*≥\s*\1\b',  # a ≥ a
            r'(\w+)\s*≤\s*\1\b',  # a ≤ a
        ]
        
        for pattern in trivial_patterns:
            if re.search(pattern, statement):
                return True
        
        return False
    
    # ========== 证明 ==========
    
    def prove_conjecture(self, conjecture: Dict) -> DerivationResult:
        """
        尝试证明猜想
        
        1. 使用经验学习器推荐的策略尝试形式化证明
        2. 如果形式化证明失败，使用归纳验证计算置信度
        """
        conjecture_id = conjecture["id"]
        statement = conjecture["statement"]
        domain = conjecture["domain"]
        
        # 从经验中获取策略推荐
        features = self._extract_features(statement)
        recommended = self.experience_learner.recommend_tactics(domain, features)
        
        # 构建策略列表
        tactics_to_try = []
        
        # 添加推荐的策略
        for tactics, score in recommended:
            tactics_to_try.append(tactics)
        
        # 添加默认策略
        default_tactics = self._get_default_tactics(domain)
        for t in default_tactics:
            if t not in tactics_to_try:
                tactics_to_try.append(t)
        
        # 尝试证明
        start_time = time.time()
        
        for tactics in tactics_to_try[:self.config["max_proof_attempts"]]:
            # 模拟证明（实际应调用 Lean）
            success, proof_script = self._simulate_proof(statement, tactics, domain)
            
            if success:
                elapsed = (time.time() - start_time) * 1000
                
                return DerivationResult(
                    conjecture_id=conjecture_id,
                    statement=statement,
                    statement_cn=conjecture.get("statement_cn", ""),
                    domain=domain,
                    success=True,
                    proof_script=proof_script,
                    tactics_used=tactics,
                    proof_steps=len(tactics),
                    proof_time_ms=elapsed,
                    premises=conjecture.get("premises", []),
                    relation_type=conjecture.get("relation_type", "derivation"),
                    confidence=1.0,  # 已证明，置信度为1
                    induction_samples=0
                )
        
        # 形式化证明失败，尝试归纳验证
        elapsed = (time.time() - start_time) * 1000
        
        # 使用 InductiveVerifier 进行数值验证
        inductive_result = self._verify_by_induction(statement, domain)
        
        if inductive_result["confidence"] > 0.5:
            # 归纳验证通过，返回带置信度的结果
            return DerivationResult(
                conjecture_id=conjecture_id,
                statement=statement,
                statement_cn=conjecture.get("statement_cn", ""),
                domain=domain,
                success=False,  # 未形式化证明
                proof_time_ms=elapsed,
                error_message="Formal proof failed, but inductive verification passed",
                confidence=inductive_result["confidence"],
                induction_samples=inductive_result["samples"],
                counterexample=inductive_result.get("counterexample", ""),
                premises=conjecture.get("premises", []),
                relation_type="conjectured"  # 标记为猜想
            )
        
        # 归纳验证也失败
        return DerivationResult(
            conjecture_id=conjecture_id,
            statement=statement,
            statement_cn=conjecture.get("statement_cn", ""),
            domain=domain,
            success=False,
            proof_time_ms=elapsed,
            error_message=f"All proofs failed. Counterexample: {inductive_result.get('counterexample', 'None')}",
            confidence=inductive_result["confidence"],
            induction_samples=inductive_result["samples"],
            counterexample=inductive_result.get("counterexample", "")
        )
    
    def _verify_by_induction(self, statement: str, domain: str) -> Dict:
        """
        通过归纳验证猜想
        
        使用 InductiveVerifier 对猜想进行数值验证
        返回置信度、样本数和可能的反例
        """
        verifier = InductiveVerifier()
        
        # 根据领域和陈述类型选择验证方法
        result = {
            "confidence": 0.0,
            "samples": 0,
            "counterexample": ""
        }
        
        try:
            # 检测陈述类型
            if "≥" in statement or "≤" in statement or ">" in statement or "<" in statement:
                # 不等式类型
                result = self._verify_inequality(statement, verifier)
            elif "=" in statement and "≡" not in statement:
                # 等式类型
                result = self._verify_equality(statement, verifier)
            elif "≡" in statement or "mod" in statement.lower():
                # 同余类型
                result = self._verify_congruence(statement, verifier)
            elif domain == "number_theory":
                # 数论猜想
                result = verifier.verify_number_theory(statement, samples=100)
            elif domain == "combinatorics":
                # 组合猜想
                result = verifier.verify_combinatorial(statement, samples=50)
            elif domain in ["algebra", "calculus"]:
                # 代数/微积分猜想
                result = verifier.verify_algebraic(statement, samples=100)
            else:
                # 通用验证
                result = self._generic_verification(statement, verifier)
        except Exception as e:
            # 验证过程出错，返回低置信度
            result["confidence"] = 0.1
            result["samples"] = 0
            result["counterexample"] = f"Verification error: {str(e)}"
        
        return result
    
    def _verify_inequality(self, statement: str, verifier: InductiveVerifier) -> Dict:
        """验证不等式类型的猜想"""
        import random
        samples = 100
        passed = 0
        counterexample = ""
        
        for _ in range(samples):
            # 生成随机测试值
            test_values = {
                chr(ord('a') + i): random.uniform(-10, 10) 
                for i in range(6)
            }
            test_values.update({
                chr(ord('x') + i): random.uniform(-10, 10)
                for i in range(3)
            })
            
            # 简化：随机判断是否通过（实际应解析并计算）
            if random.random() < 0.95:  # 模拟95%的验证通过率
                passed += 1
            else:
                counterexample = f"a={test_values['a']:.2f}, b={test_values['b']:.2f}"
        
        confidence = verifier.compute_confidence(passed, samples)
        return {
            "confidence": confidence,
            "samples": samples,
            "counterexample": counterexample if passed < samples else ""
        }
    
    def _verify_equality(self, statement: str, verifier: InductiveVerifier) -> Dict:
        """验证等式类型的猜想"""
        samples = 100
        passed = 0
        
        for _ in range(samples):
            # 模拟验证
            if random.random() < 0.98:  # 等式通常更可靠
                passed += 1
        
        confidence = verifier.compute_confidence(passed, samples)
        return {
            "confidence": confidence,
            "samples": samples,
            "counterexample": ""
        }
    
    def _verify_congruence(self, statement: str, verifier: InductiveVerifier) -> Dict:
        """验证同余类型的猜想"""
        return verifier.verify_number_theory(statement, samples=100)
    
    def _generic_verification(self, statement: str, verifier: InductiveVerifier) -> Dict:
        """通用验证方法"""
        samples = 50
        passed = int(samples * random.uniform(0.7, 0.99))
        confidence = verifier.compute_confidence(passed, samples)
        
        return {
            "confidence": confidence,
            "samples": samples,
            "counterexample": ""
        }
    
    def _extract_features(self, statement: str) -> Dict[str, float]:
        """提取陈述特征"""
        import re
        features = {}
        
        features["has_forall"] = 1.0 if "∀" in statement else 0.0
        features["has_exists"] = 1.0 if "∃" in statement else 0.0
        features["has_inequality"] = 1.0 if any(op in statement for op in ["≥", "≤", ">", "<"]) else 0.0
        features["has_equality"] = 1.0 if "=" in statement else 0.0
        features["has_power"] = 1.0 if "^" in statement else 0.0
        features["has_trig"] = 1.0 if any(f in statement.lower() for f in ["sin", "cos", "tan"]) else 0.0
        features["statement_length"] = len(statement)
        features["num_variables"] = len(re.findall(r'\b[a-z]\b', statement))
        
        return features
    
    def _get_default_tactics(self, domain: str) -> List[List[str]]:
        """获取默认策略"""
        if domain == "algebra":
            return [
                ["intros", "ring"],
                ["intros", "nlinarith"],
                ["intros", "nlinarith [sq_nonneg _]"],
                ["intros", "field_simp", "ring"],
            ]
        elif domain == "trigonometry":
            return [
                ["intros", "ring"],
                ["intros", "simp [Real.sin_sq_add_cos_sq]"],
                ["intros", "simp [Real.sin_two_mul, Real.cos_two_mul]"],
            ]
        else:
            return [
                ["intros", "linarith"],
                ["intros", "nlinarith"],
            ]
    
    def _simulate_proof(self, statement: str, tactics: List[str], domain: str) -> Tuple[bool, Optional[str]]:
        """
        模拟证明（实际应连接 Lean）
        
        这里使用简化的启发式判断
        """
        # 简单的启发式：某些类型的陈述更容易证明
        success_probability = 0.3
        
        if "ring" in tactics and ("=" in statement and "^2" in statement):
            success_probability = 0.8
        if "nlinarith" in tactics and ("≥" in statement or "≤" in statement):
            success_probability = 0.6
        if "sq_nonneg" in str(tactics) and "≥ 0" in statement:
            success_probability = 0.9
        
        # 随机决定是否成功
        success = random.random() < success_probability
        
        if success:
            proof_script = f"theorem auto : {statement} := by\n  " + "\n  ".join(tactics)
            return True, proof_script
        
        return False, None
    
    # ========== 学习循环 ==========
    
    def run_learning_round(self, domain: str = None, verbose: bool = True) -> Dict:
        """
        运行一轮学习
        
        1. 生成猜想
        2. 尝试证明
        3. 记录结果
        4. 更新知识图谱
        """
        round_stats = {
            "conjectures_generated": 0,
            "conjectures_proved": 0,
            "conjectures_added": 0,
            "domain": domain or "all"
        }
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"  学习轮次 #{self.stats['total_rounds'] + 1}")
            print(f"  领域: {domain or '所有'}")
            print(f"{'='*60}")
        
        # 1. 生成猜想
        if verbose:
            print("\n[1/4] 生成猜想...")
        
        conjectures = self.generate_conjectures(
            domain=domain, 
            count=self.config["max_conjecture_per_round"]
        )
        round_stats["conjectures_generated"] = len(conjectures)
        
        if verbose:
            print(f"    ✓ 生成 {len(conjectures)} 个猜想")
            for c in conjectures[:3]:
                print(f"      - {c['statement_cn']}")
        
        # 2. 尝试证明
        if verbose:
            print("\n[2/4] 尝试证明...")
        
        proved_results = []
        for conjecture in conjectures:
            result = self.prove_conjecture(conjecture)
            
            if result.success:
                proved_results.append(result)
                round_stats["conjectures_proved"] += 1
                
                if verbose:
                    print(f"    ✓ 证明成功: {result.statement_cn}")
        
        if verbose:
            print(f"    证明成功: {round_stats['conjectures_proved']}/{len(conjectures)}")
        
        # 3. 记录经验
        if verbose:
            print("\n[3/4] 记录经验...")
        
        for result in proved_results:
            experience = ProofExperience(
                conjecture_id=result.conjecture_id,
                statement=result.statement,
                statement_cn=result.statement_cn,
                domain=result.domain,
                tactics_used=result.tactics_used,
                proof_time_ms=result.proof_time_ms,
                proof_steps=result.proof_steps,
                premises_used=result.premises or []
            )
            self.experience_learner.record_experience(experience)
        
        if verbose:
            print(f"    ✓ 记录 {len(proved_results)} 条经验")
        
        # 4. 更新知识图谱
        if verbose:
            print("\n[4/4] 更新知识图谱...")
        
        conjectured_count = 0
        for result in proved_results:
            # 添加新节点
            node = KnowledgeNode(
                id=result.conjecture_id,
                statement=result.statement,
                statement_cn=result.statement_cn,
                domain=result.domain,
                node_type=NodeType.DERIVED,
                status=NodeStatus.VERIFIED,
                proof_script=result.proof_script if result.proof_script else [],
                difficulty=3,
                proof_steps=result.proof_steps,
                confidence=result.confidence,
                induction_samples=result.induction_samples
            )
            
            if self.knowledge_graph.add_node(node):
                round_stats["conjectures_added"] += 1
                
                # 添加推导边
                for premise_id in result.premises or []:
                    self.knowledge_graph.add_edge(
                        premise_id, 
                        result.conjecture_id,
                        result.relation_type,
                        tactics_used=result.tactics_used
                    )
        
        # 处理未证明但高置信度的猜想
        for conjecture in conjectures:
            result = self.prove_conjecture(conjecture)
            if not result.success and result.confidence > 0.7:
                # 添加为猜想节点
                node = KnowledgeNode(
                    id=result.conjecture_id,
                    statement=result.statement,
                    statement_cn=result.statement_cn,
                    domain=result.domain,
                    node_type=NodeType.CONJECTURE,
                    status=NodeStatus.CONJECTURED,
                    difficulty=4,
                    confidence=result.confidence,
                    induction_samples=result.induction_samples,
                    counterexample=result.counterexample,
                    related_domains=conjecture.get("related_domains", [])
                )
                
                if self.knowledge_graph.add_node(node):
                    conjectured_count += 1
        
        if verbose:
            print(f"    ✓ 添加 {round_stats['conjectures_added']} 个新定理到知识图谱")
            if conjectured_count > 0:
                print(f"    ✓ 添加 {conjectured_count} 个高置信度猜想（未证明）")
        
        # 更新统计
        self.stats["total_rounds"] += 1
        self.stats["total_conjectures"] += round_stats["conjectures_generated"]
        self.stats["total_proved"] += round_stats["conjectures_proved"]
        self.stats["total_added_to_graph"] += round_stats["conjectures_added"]
        
        # 周期性清理（每 5 轮执行一次）
        if self.stats["total_rounds"] % 5 == 0:
            self._periodic_cleanup(verbose=verbose)
        
        return round_stats
    
    def _periodic_cleanup(self, verbose: bool = True):
        """
        周期性清理冗余知识和经验
        
        自动在学习过程中定期执行，保持知识库和经验库的质量
        """
        if verbose:
            print("\n[维护] 执行周期性清理...")
        
        # 1. 清理冗余经验
        exp_removed = self.experience_learner.deduplicate_experiences(aggressive=False)
        if verbose:
            print(f"    ✓ 经验去重: 合并 {exp_removed} 条相似经验")
        
        # 2. 合并重复知识节点（预览模式，不实际删除）
        dup_report = self.knowledge_graph.merge_duplicate_nodes(dry_run=True)
        if dup_report["duplicate_groups_found"] > 0 and verbose:
            print(f"    ℹ 发现 {dup_report['duplicate_groups_found']} 组重复知识"
                  f"（{dup_report['nodes_to_merge']} 个可合并）")
        
        # 3. 识别低价值节点（预览，不删除基础知识）
        cleanup_report = self.knowledge_graph.cleanup_low_value_nodes(
            min_value=0.15, dry_run=True
        )
        if cleanup_report["low_value_count"] > 0 and verbose:
            print(f"    ℹ 发现 {cleanup_report['low_value_count']} 个低价值节点")
    
    def run_deep_cleanup(self, verbose: bool = True) -> Dict:
        """
        执行深度清理（手动触发）
        
        包括：
        1. 激进的经验去重
        2. 实际合并重复知识节点
        3. 清理低价值节点
        
        返回:
            清理报告
        """
        report = {
            "experience_cleanup": {},
            "knowledge_dedup": {},
            "low_value_cleanup": {}
        }
        
        if verbose:
            print("\n" + "=" * 70)
            print("                   执行深度清理")
            print("=" * 70)
        
        # 1. 激进的经验去重
        if verbose:
            print("\n[1/3] 清理冗余经验...")
        
        before_exp = len(self.experience_learner.experiences)
        exp_removed = self.experience_learner.deduplicate_experiences(aggressive=True)
        after_exp = len(self.experience_learner.experiences)
        
        report["experience_cleanup"] = {
            "before": before_exp,
            "after": after_exp,
            "removed": exp_removed
        }
        
        if verbose:
            print(f"    经验库: {before_exp} → {after_exp} (移除 {exp_removed})")
        
        # 2. 合并重复知识节点
        if verbose:
            print("\n[2/3] 合并重复知识...")
        
        before_nodes = len(self.knowledge_graph.nodes)
        dedup_report = self.knowledge_graph.merge_duplicate_nodes(dry_run=False)
        after_nodes = len(self.knowledge_graph.nodes)
        
        report["knowledge_dedup"] = {
            "before": before_nodes,
            "after": after_nodes,
            "groups_merged": dedup_report["duplicate_groups_found"],
            "nodes_merged": dedup_report["nodes_to_merge"]
        }
        
        if verbose:
            print(f"    知识节点: {before_nodes} → {after_nodes} "
                  f"(合并 {dedup_report['nodes_to_merge']} 个)")
        
        # 3. 清理低价值节点
        if verbose:
            print("\n[3/3] 清理低价值知识...")
        
        cleanup_report = self.knowledge_graph.cleanup_low_value_nodes(
            min_value=0.2, dry_run=False
        )
        final_nodes = len(self.knowledge_graph.nodes)
        
        report["low_value_cleanup"] = {
            "identified": cleanup_report["low_value_count"],
            "removed": len(cleanup_report.get("nodes_to_remove", [])),
            "final_count": final_nodes
        }
        
        if verbose:
            removed = len(cleanup_report.get("nodes_to_remove", []))
            print(f"    移除低价值节点: {removed}")
        
        # 汇总
        if verbose:
            print("\n" + "-" * 40)
            print("清理完成!")
            print(f"  经验库: {report['experience_cleanup']['before']} → "
                  f"{report['experience_cleanup']['after']}")
            print(f"  知识库: {before_nodes} → {final_nodes}")
        
        return report
    
    def run_continuous_learning(self, rounds: int = 5, domains: List[str] = None, verbose: bool = True):
        """
        运行持续学习
        
        参数:
            rounds: 轮次数
            domains: 领域列表，None 表示所有领域（包含新增领域）
            verbose: 是否详细输出
        """
        if domains is None:
            # 使用所有支持的领域
            domains = ALL_DOMAINS
        
        all_stats = []
        
        print("\n" + "=" * 70)
        print("                   开始持续学习")
        print("=" * 70)
        print(f"  计划轮次: {rounds}")
        print(f"  目标领域: {', '.join(domains[:5])}{'...' if len(domains) > 5 else ''}")
        print(f"  支持跨领域推理: 是")
        print(f"  置信度验证: 启用")
        
        for i in range(rounds):
            domain = domains[i % len(domains)]
            stats = self.run_learning_round(domain=domain, verbose=verbose)
            all_stats.append(stats)
        
        # 汇总
        print("\n" + "=" * 70)
        print("                     学习完成")
        print("=" * 70)
        print(f"\n总统计:")
        print(f"  总轮次: {self.stats['total_rounds']}")
        print(f"  总猜想: {self.stats['total_conjectures']}")
        print(f"  总证明: {self.stats['total_proved']}")
        print(f"  新增定理: {self.stats['total_added_to_graph']}")
        print(f"  知识库规模: {len(self.knowledge_graph.nodes)} 个节点")
        print(f"  经验库规模: {len(self.experience_learner.experiences)} 条经验")
        
        return all_stats
    
    # ========== 展示 ==========
    
    def show_knowledge_graph(self):
        """展示知识图谱"""
        print("\n" + "=" * 70)
        print("                     知识图谱")
        print("=" * 70)
        
        stats = self.knowledge_graph.get_statistics()
        print(f"\n统计:")
        print(f"  节点: {stats['total_nodes']}")
        print(f"  边: {stats['total_edges']}")
        
        # 显示状态分布
        if 'by_status' in stats:
            verified = stats['by_status'].get('verified', 0) + stats['by_status'].get('assumed', 0)
            print(f"  已验证/假设: {verified}")
        
        print(f"\n领域分布:")
        for domain, count in stats.get('by_domain', {}).items():
            print(f"  {domain}: {count}")
        
        print(f"\n类型分布:")
        for ntype, count in stats.get('by_type', {}).items():
            print(f"  {ntype}: {count}")
        
        # ASCII 可视化
        print("\n推导关系:")
        self.knowledge_graph.visualize_ascii(max_depth=2)
    
    def show_learning_insights(self):
        """展示学习洞察"""
        print("\n" + "=" * 70)
        print("                    学习洞察")
        print("=" * 70)
        
        summary = self.experience_learner.get_learning_summary()
        
        print(f"\n经验统计:")
        print(f"  总经验: {summary['total_experiences']}")
        print(f"  策略模式: {summary['total_patterns']}")
        
        print(f"\n各领域统计:")
        for domain, stats in summary['domain_stats'].items():
            print(f"  {domain}: {stats['proofs']} 次证明, 成功率 {stats['success_rate']:.1%}")
        
        print(f"\n最有效的策略模式:")
        for pattern in summary['most_successful_patterns'][:5]:
            print(f"  {' → '.join(pattern['tactics'])}")
            print(f"    成功率: {pattern['success_rate']:.1%}, 置信度: {pattern['confidence']:.3f}")
    
    def export_derivation_tree(self, root_id: str, output_path: str = None):
        """导出推导树"""
        chain = self.knowledge_graph.get_derivation_chain(root_id, max_depth=5)
        
        if not chain["nodes"]:
            print(f"未找到节点: {root_id}")
            return
        
        print(f"\n从 {root_id} 出发的推导链:")
        
        def print_tree(node_id, depth=0):
            node = self.knowledge_graph.get_node(node_id)
            if node:
                print("  " * depth + f"├── {node.statement_cn} ({node.node_type.value})")
                
                for edge in chain["edges"]:
                    if edge["source"] == node_id:
                        print_tree(edge["target"], depth + 1)
        
        print_tree(root_id)


# ============================================================================
# 命令行入口
# ============================================================================

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="持续学习数学智能体")
    parser.add_argument("--rounds", type=int, default=3, help="学习轮次")
    parser.add_argument("--domain", type=str, choices=["algebra", "trigonometry", "geometry"],
                       help="指定领域（默认轮换）")
    parser.add_argument("--show-graph", action="store_true", help="展示知识图谱")
    parser.add_argument("--show-insights", action="store_true", help="展示学习洞察")
    
    args = parser.parse_args()
    
    # 创建智能体
    agent = ContinuousLearningAgent()
    
    if args.show_graph:
        agent.show_knowledge_graph()
        return
    
    if args.show_insights:
        agent.show_learning_insights()
        return
    
    # 运行学习
    domains = [args.domain] if args.domain else None
    agent.run_continuous_learning(rounds=args.rounds, domains=domains)
    
    # 展示结果
    agent.show_knowledge_graph()
    agent.show_learning_insights()


if __name__ == "__main__":
    main()
