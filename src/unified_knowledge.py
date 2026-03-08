#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    统一数学知识库
═══════════════════════════════════════════════════════════════════════════════

合并所有数学领域的知识，支持：
    - 统一的知识表示
    - 跨领域知识利用
    - 推导关系追踪
    - 不完全归纳验证

知识层级：
    ┌─────────────────────────────────────────────────────────────┐
    │  AXIOM (公理)      │ 无需证明的基础事实                      │
    │  DEFINITION (定义) │ 概念的精确描述                          │
    ├─────────────────────────────────────────────────────────────┤
    │  CORE (核心定理)   │ 经典、已验证的重要定理                  │
    ├─────────────────────────────────────────────────────────────┤
    │  DERIVED (派生)    │ 从其他定理推导出来                      │
    │  CONJECTURE (猜想) │ 待证明的命题                            │
    └─────────────────────────────────────────────────────────────┘

支持领域：
    内置领域：代数、三角函数、平面几何、数论、立体几何、解析几何、组合、概率、微积分、线性代数
    扩展能力：Gauss 可处理 Lean 4 与 Mathlib 覆盖的所有数学分支

作者 (Author): Jiangsheng Yu
版本 (Version): 3.0.0
"""

import hashlib
import json
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum
from pathlib import Path


# ============================================================================
# 基础枚举
# ============================================================================

class MathDomain(Enum):
    """数学领域"""
    # 基础领域
    NAT = "nat"
    ALGEBRA = "algebra"
    TRIGONOMETRY = "trigonometry"
    GEOMETRY = "geometry"
    
    # 扩展领域
    NUMBER_THEORY = "number_theory"
    SOLID_GEOMETRY = "solid_geometry"
    ANALYTIC_GEOMETRY = "analytic_geometry"
    COMBINATORICS = "combinatorics"
    PROBABILITY = "probability"
    CALCULUS = "calculus"
    LINEAR_ALGEBRA = "linear_algebra"
    
    # 高等数学领域
    RING_THEORY = "ring_theory"
    GROUP_THEORY = "group_theory"
    FIELD_THEORY = "field_theory"
    TOPOLOGY = "topology"
    MEASURE_THEORY = "measure_theory"
    CATEGORY_THEORY = "category_theory"
    ORDER_THEORY = "order_theory"
    SET_THEORY = "set_theory"
    LOGIC = "logic"
    ALGEBRAIC_GEOMETRY = "algebraic_geometry"
    ALGEBRAIC_TOPOLOGY = "algebraic_topology"
    REPRESENTATION_THEORY = "representation_theory"
    DYNAMICS = "dynamics"
    INFORMATION_THEORY = "information_theory"
    
    # 跨领域
    CROSS_DOMAIN = "cross_domain"


class KnowledgeLevel(Enum):
    """知识层级"""
    AXIOM = "axiom"           # 公理
    DEFINITION = "definition"  # 定义
    CORE = "core"             # 核心定理
    DERIVED = "derived"       # 派生定理
    CONJECTURE = "conjecture" # 猜想


# 领域中文名称
DOMAIN_NAMES = {
    MathDomain.NAT: "自然数",
    MathDomain.ALGEBRA: "代数",
    MathDomain.TRIGONOMETRY: "三角函数",
    MathDomain.GEOMETRY: "平面几何",
    MathDomain.NUMBER_THEORY: "数论",
    MathDomain.SOLID_GEOMETRY: "立体几何",
    MathDomain.ANALYTIC_GEOMETRY: "解析几何",
    MathDomain.COMBINATORICS: "组合计数",
    MathDomain.PROBABILITY: "概率统计",
    MathDomain.CALCULUS: "微积分",
    MathDomain.LINEAR_ALGEBRA: "线性代数",
    MathDomain.RING_THEORY: "环论",
    MathDomain.GROUP_THEORY: "群论",
    MathDomain.FIELD_THEORY: "域论",
    MathDomain.TOPOLOGY: "拓扑学",
    MathDomain.MEASURE_THEORY: "测度论",
    MathDomain.CATEGORY_THEORY: "范畴论",
    MathDomain.ORDER_THEORY: "序论",
    MathDomain.SET_THEORY: "集合论",
    MathDomain.LOGIC: "逻辑学",
    MathDomain.ALGEBRAIC_GEOMETRY: "代数几何",
    MathDomain.ALGEBRAIC_TOPOLOGY: "代数拓扑",
    MathDomain.REPRESENTATION_THEORY: "表示论",
    MathDomain.DYNAMICS: "动力系统",
    MathDomain.INFORMATION_THEORY: "信息论",
    MathDomain.CROSS_DOMAIN: "跨领域",
}

# 领域之间的关联（用于跨领域推理）
DOMAIN_CONNECTIONS = {
    MathDomain.ALGEBRA: [MathDomain.NUMBER_THEORY, MathDomain.LINEAR_ALGEBRA, MathDomain.CALCULUS, MathDomain.RING_THEORY, MathDomain.GROUP_THEORY],
    MathDomain.TRIGONOMETRY: [MathDomain.GEOMETRY, MathDomain.CALCULUS, MathDomain.ANALYTIC_GEOMETRY],
    MathDomain.GEOMETRY: [MathDomain.TRIGONOMETRY, MathDomain.SOLID_GEOMETRY, MathDomain.ANALYTIC_GEOMETRY, MathDomain.ALGEBRAIC_GEOMETRY, MathDomain.TOPOLOGY],
    MathDomain.NUMBER_THEORY: [MathDomain.ALGEBRA, MathDomain.COMBINATORICS, MathDomain.RING_THEORY, MathDomain.FIELD_THEORY],
    MathDomain.SOLID_GEOMETRY: [MathDomain.GEOMETRY, MathDomain.LINEAR_ALGEBRA, MathDomain.TOPOLOGY],
    MathDomain.ANALYTIC_GEOMETRY: [MathDomain.GEOMETRY, MathDomain.LINEAR_ALGEBRA, MathDomain.CALCULUS, MathDomain.ALGEBRAIC_GEOMETRY],
    MathDomain.COMBINATORICS: [MathDomain.PROBABILITY, MathDomain.NUMBER_THEORY, MathDomain.ORDER_THEORY],
    MathDomain.PROBABILITY: [MathDomain.COMBINATORICS, MathDomain.CALCULUS, MathDomain.MEASURE_THEORY, MathDomain.INFORMATION_THEORY],
    MathDomain.CALCULUS: [MathDomain.ALGEBRA, MathDomain.TRIGONOMETRY, MathDomain.PROBABILITY, MathDomain.MEASURE_THEORY, MathDomain.TOPOLOGY],
    MathDomain.LINEAR_ALGEBRA: [MathDomain.ALGEBRA, MathDomain.ANALYTIC_GEOMETRY, MathDomain.CALCULUS, MathDomain.REPRESENTATION_THEORY],
    MathDomain.RING_THEORY: [MathDomain.ALGEBRA, MathDomain.NUMBER_THEORY, MathDomain.FIELD_THEORY, MathDomain.ALGEBRAIC_GEOMETRY],
    MathDomain.GROUP_THEORY: [MathDomain.ALGEBRA, MathDomain.REPRESENTATION_THEORY, MathDomain.TOPOLOGY, MathDomain.NUMBER_THEORY],
    MathDomain.FIELD_THEORY: [MathDomain.RING_THEORY, MathDomain.NUMBER_THEORY, MathDomain.ALGEBRAIC_GEOMETRY],
    MathDomain.TOPOLOGY: [MathDomain.CALCULUS, MathDomain.GEOMETRY, MathDomain.ALGEBRAIC_TOPOLOGY, MathDomain.DYNAMICS],
    MathDomain.MEASURE_THEORY: [MathDomain.CALCULUS, MathDomain.PROBABILITY, MathDomain.TOPOLOGY],
    MathDomain.CATEGORY_THEORY: [MathDomain.ALGEBRA, MathDomain.TOPOLOGY, MathDomain.ALGEBRAIC_GEOMETRY, MathDomain.ALGEBRAIC_TOPOLOGY],
    MathDomain.ORDER_THEORY: [MathDomain.ALGEBRA, MathDomain.COMBINATORICS, MathDomain.TOPOLOGY, MathDomain.SET_THEORY],
    MathDomain.SET_THEORY: [MathDomain.LOGIC, MathDomain.ORDER_THEORY, MathDomain.CATEGORY_THEORY],
    MathDomain.LOGIC: [MathDomain.SET_THEORY, MathDomain.CATEGORY_THEORY],
    MathDomain.ALGEBRAIC_GEOMETRY: [MathDomain.RING_THEORY, MathDomain.GEOMETRY, MathDomain.CATEGORY_THEORY, MathDomain.FIELD_THEORY],
    MathDomain.ALGEBRAIC_TOPOLOGY: [MathDomain.TOPOLOGY, MathDomain.ALGEBRA, MathDomain.CATEGORY_THEORY],
    MathDomain.REPRESENTATION_THEORY: [MathDomain.GROUP_THEORY, MathDomain.LINEAR_ALGEBRA, MathDomain.CATEGORY_THEORY],
    MathDomain.DYNAMICS: [MathDomain.TOPOLOGY, MathDomain.MEASURE_THEORY, MathDomain.CALCULUS],
    MathDomain.INFORMATION_THEORY: [MathDomain.PROBABILITY, MathDomain.CALCULUS],
}


# ============================================================================
# 统一知识表示
# ============================================================================

@dataclass
class MathKnowledge:
    """
    统一的数学知识表示
    
    支持跨领域利用：
    - related_domains: 关联的其他领域
    - can_use_in: 可以在哪些领域中使用
    - dependencies: 依赖的其他知识
    """
    id: str
    statement: str
    statement_cn: str
    domain: MathDomain
    level: KnowledgeLevel
    
    # 推导关系
    dependencies: List[str] = field(default_factory=list)
    derived_from: str = ""
    
    # 跨领域支持
    related_domains: List[MathDomain] = field(default_factory=list)
    can_use_in: List[MathDomain] = field(default_factory=list)
    
    # 元数据
    difficulty: int = 1
    symbols: Set[str] = field(default_factory=set)
    tactics: List[str] = field(default_factory=list)
    
    # 验证
    verified: bool = True
    confidence: float = 1.0
    
    def is_fundamental(self) -> bool:
        return self.level in [KnowledgeLevel.AXIOM, KnowledgeLevel.DEFINITION]
    
    def is_usable_in(self, domain: MathDomain) -> bool:
        """判断是否可在指定领域使用"""
        if self.domain == domain:
            return True
        if domain in self.can_use_in:
            return True
        if domain in self.related_domains:
            return True
        if domain == MathDomain.CROSS_DOMAIN:
            return True
        return False
    
    def get_hash(self) -> str:
        normalized = ''.join(self.statement.split())
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "statement": self.statement,
            "statement_cn": self.statement_cn,
            "domain": self.domain.value,
            "level": self.level.value,
            "dependencies": self.dependencies,
            "derived_from": self.derived_from,
            "related_domains": [d.value for d in self.related_domains],
            "can_use_in": [d.value for d in self.can_use_in],
            "difficulty": self.difficulty,
            "symbols": list(self.symbols),
            "tactics": self.tactics,
            "verified": self.verified,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MathKnowledge":
        return cls(
            id=data["id"],
            statement=data["statement"],
            statement_cn=data["statement_cn"],
            domain=MathDomain(data["domain"]),
            level=KnowledgeLevel(data["level"]),
            dependencies=data.get("dependencies", []),
            derived_from=data.get("derived_from", ""),
            related_domains=[MathDomain(d) for d in data.get("related_domains", [])],
            can_use_in=[MathDomain(d) for d in data.get("can_use_in", [])],
            difficulty=data.get("difficulty", 1),
            symbols=set(data.get("symbols", [])),
            tactics=data.get("tactics", []),
            verified=data.get("verified", True),
            confidence=data.get("confidence", 1.0),
        )


# 兼容旧接口
@dataclass
class MathTheorem:
    """数学定理 (兼容旧接口)"""
    name: str
    statement: str
    difficulty: int = 1
    dependencies: List[str] = field(default_factory=list)
    symbols: Set[str] = field(default_factory=set)
    tactics: List[str] = field(default_factory=list)


@dataclass
class ConjecturePattern:
    """猜想生成模式"""
    name: str
    description: str
    domain: MathDomain
    template: str
    variables: Dict[str, List[str]] = field(default_factory=dict)
    applicable_domains: List[MathDomain] = field(default_factory=list)


# ============================================================================
# 领域知识基类（消除 get_all_theorems 重复代码）
# ============================================================================

class DomainKnowledge:
    """领域知识基类，提供通用的 get_all_theorems 方法"""

    @classmethod
    def get_all_theorems(cls) -> Dict[str, MathTheorem]:
        items = []
        if hasattr(cls, 'get_axioms'):
            items.extend(cls.get_axioms())
        if hasattr(cls, 'get_theorems'):
            items.extend(cls.get_theorems())
        return {
            k.id: MathTheorem(
                name=k.statement_cn, statement=k.statement, difficulty=k.difficulty,
                dependencies=k.dependencies, symbols=k.symbols, tactics=k.tactics
            ) for k in items
        }


# ============================================================================
# 代数知识库
# ============================================================================

class AlgebraKnowledge(DomainKnowledge):
    """代数知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="alg_ax_add_comm", statement="∀ a b : ℝ, a + b = b + a",
                statement_cn="加法交换律", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                symbols={'+', '='}, tactics=["ring"],
                can_use_in=[MathDomain.NUMBER_THEORY, MathDomain.LINEAR_ALGEBRA, MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="alg_ax_add_assoc", statement="∀ a b c : ℝ, (a + b) + c = a + (b + c)",
                statement_cn="加法结合律", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                symbols={'+', '='}, tactics=["ring"],
                can_use_in=[MathDomain.NUMBER_THEORY, MathDomain.LINEAR_ALGEBRA]
            ),
            MathKnowledge(
                id="alg_ax_mul_comm", statement="∀ a b : ℝ, a * b = b * a",
                statement_cn="乘法交换律", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                symbols={'*', '='}, tactics=["ring"],
                can_use_in=[MathDomain.NUMBER_THEORY]
            ),
            MathKnowledge(
                id="alg_ax_mul_assoc", statement="∀ a b c : ℝ, (a * b) * c = a * (b * c)",
                statement_cn="乘法结合律", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                symbols={'*', '='}, tactics=["ring"],
                can_use_in=[MathDomain.NUMBER_THEORY, MathDomain.LINEAR_ALGEBRA]
            ),
            MathKnowledge(
                id="alg_ax_distrib", statement="∀ a b c : ℝ, a * (b + c) = a * b + a * c",
                statement_cn="分配律", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                symbols={'+', '*', '='}, tactics=["ring"],
                can_use_in=[MathDomain.NUMBER_THEORY, MathDomain.LINEAR_ALGEBRA, MathDomain.COMBINATORICS]
            ),
            MathKnowledge(
                id="alg_ax_sq_nonneg", statement="∀ a : ℝ, a² ≥ 0",
                statement_cn="平方非负性", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                symbols={'^', '≥'}, tactics=["nlinarith", "positivity"],
                can_use_in=[MathDomain.PROBABILITY, MathDomain.LINEAR_ALGEBRA]
            ),
            MathKnowledge(
                id="alg_ax_zero_identity", statement="∀ a : ℝ, a + 0 = a",
                statement_cn="加法单位元", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                symbols={'+', '='}, tactics=["ring", "simp"]
            ),
            MathKnowledge(
                id="alg_ax_one_identity", statement="∀ a : ℝ, a * 1 = a",
                statement_cn="乘法单位元", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                symbols={'*', '='}, tactics=["ring", "simp"]
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            # 平方公式
            MathKnowledge(
                id="alg_thm_sq_add", statement="∀ a b : ℝ, (a + b)² = a² + 2ab + b²",
                statement_cn="完全平方公式（和）", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["alg_ax_distrib"], tactics=["ring"],
                can_use_in=[MathDomain.NUMBER_THEORY, MathDomain.GEOMETRY]
            ),
            MathKnowledge(
                id="alg_thm_sq_sub", statement="∀ a b : ℝ, (a - b)² = a² - 2ab + b²",
                statement_cn="完全平方公式（差）", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["alg_ax_distrib"], tactics=["ring"],
                can_use_in=[MathDomain.NUMBER_THEORY, MathDomain.GEOMETRY]
            ),
            MathKnowledge(
                id="alg_thm_sq_diff", statement="∀ a b : ℝ, (a + b)(a - b) = a² - b²",
                statement_cn="平方差公式", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["alg_ax_distrib"], tactics=["ring"],
                can_use_in=[MathDomain.NUMBER_THEORY]
            ),
            # 立方公式
            MathKnowledge(
                id="alg_thm_cube_sum", statement="∀ a b : ℝ, a³ + b³ = (a + b)(a² - ab + b²)",
                statement_cn="立方和公式", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=2, tactics=["ring"]
            ),
            MathKnowledge(
                id="alg_thm_cube_diff", statement="∀ a b : ℝ, a³ - b³ = (a - b)(a² + ab + b²)",
                statement_cn="立方差公式", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=2, tactics=["ring"]
            ),
            # 不等式
            MathKnowledge(
                id="alg_thm_am_gm", statement="∀ a b : ℝ, a ≥ 0 → b ≥ 0 → (a + b)/2 ≥ √(ab)",
                statement_cn="AM-GM 不等式", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=3,
                dependencies=["alg_ax_sq_nonneg"], tactics=["nlinarith", "positivity"],
                can_use_in=[MathDomain.PROBABILITY, MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="alg_thm_am_gm_n", statement="∀ a_i : ℝ, (∑a_i)/n ≥ (∏a_i)^(1/n)",
                statement_cn="AM-GM 不等式（n元）", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=4,
                dependencies=["alg_thm_am_gm"],
                can_use_in=[MathDomain.COMBINATORICS, MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="alg_thm_cauchy", statement="∀ a b c d : ℝ, (ac + bd)² ≤ (a² + b²)(c² + d²)",
                statement_cn="柯西-施瓦茨不等式", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=4,
                dependencies=["alg_ax_sq_nonneg"], tactics=["nlinarith", "polyrith"],
                can_use_in=[MathDomain.LINEAR_ALGEBRA, MathDomain.PROBABILITY]
            ),
            # 指数对数
            MathKnowledge(
                id="alg_thm_exp_add", statement="∀ a b : ℝ, e^(a+b) = e^a * e^b",
                statement_cn="指数加法性质", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.CALCULUS, MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="alg_thm_log_mul", statement="∀ a b : ℝ, a > 0 → b > 0 → ln(ab) = ln(a) + ln(b)",
                statement_cn="对数乘法性质", domain=MathDomain.ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.CALCULUS, MathDomain.NUMBER_THEORY]
            ),
        ]


# ============================================================================
# 三角函数知识库
# ============================================================================

class TrigonometryKnowledge(DomainKnowledge):
    """三角函数知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="trig_ax_pythagorean", statement="∀ θ : ℝ, sin²θ + cos²θ = 1",
                statement_cn="毕达哥拉斯恒等式", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                symbols={'sin', 'cos', '^', '+', '='}, tactics=["exact Real.sin_sq_add_cos_sq"],
                can_use_in=[MathDomain.GEOMETRY, MathDomain.ANALYTIC_GEOMETRY, MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="trig_def_tan", statement="∀ θ : ℝ, cos θ ≠ 0 → tan θ = sin θ / cos θ",
                statement_cn="正切定义", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.DEFINITION, difficulty=1,
                symbols={'tan', 'sin', 'cos', '/', '='}
            ),
            MathKnowledge(
                id="trig_def_cot", statement="∀ θ : ℝ, sin θ ≠ 0 → cot θ = cos θ / sin θ",
                statement_cn="余切定义", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.DEFINITION, difficulty=1
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            # 和差公式
            MathKnowledge(
                id="trig_thm_sin_add", statement="∀ α β : ℝ, sin(α + β) = sin α cos β + cos α sin β",
                statement_cn="正弦加法定理", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                tactics=["exact Real.sin_add"],
                can_use_in=[MathDomain.GEOMETRY, MathDomain.ANALYTIC_GEOMETRY]
            ),
            MathKnowledge(
                id="trig_thm_sin_sub", statement="∀ α β : ℝ, sin(α - β) = sin α cos β - cos α sin β",
                statement_cn="正弦减法定理", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["trig_thm_sin_add"]
            ),
            MathKnowledge(
                id="trig_thm_cos_add", statement="∀ α β : ℝ, cos(α + β) = cos α cos β - sin α sin β",
                statement_cn="余弦加法定理", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                tactics=["exact Real.cos_add"],
                can_use_in=[MathDomain.GEOMETRY, MathDomain.ANALYTIC_GEOMETRY]
            ),
            MathKnowledge(
                id="trig_thm_cos_sub", statement="∀ α β : ℝ, cos(α - β) = cos α cos β + sin α sin β",
                statement_cn="余弦减法定理", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["trig_thm_cos_add"]
            ),
            # 倍角公式
            MathKnowledge(
                id="trig_thm_sin_2x", statement="∀ θ : ℝ, sin(2θ) = 2 sin θ cos θ",
                statement_cn="正弦倍角公式", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["trig_thm_sin_add"]
            ),
            MathKnowledge(
                id="trig_thm_cos_2x", statement="∀ θ : ℝ, cos(2θ) = cos²θ - sin²θ",
                statement_cn="余弦倍角公式", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["trig_thm_cos_add"]
            ),
            MathKnowledge(
                id="trig_thm_cos_2x_cos", statement="∀ θ : ℝ, cos(2θ) = 2cos²θ - 1",
                statement_cn="余弦倍角公式（余弦形式）", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["trig_thm_cos_2x", "trig_ax_pythagorean"]
            ),
            MathKnowledge(
                id="trig_thm_cos_2x_sin", statement="∀ θ : ℝ, cos(2θ) = 1 - 2sin²θ",
                statement_cn="余弦倍角公式（正弦形式）", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["trig_thm_cos_2x", "trig_ax_pythagorean"]
            ),
            # 半角公式
            MathKnowledge(
                id="trig_thm_sin_half", statement="∀ θ : ℝ, sin²(θ/2) = (1 - cos θ)/2",
                statement_cn="正弦半角公式", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=3,
                dependencies=["trig_thm_cos_2x_sin"]
            ),
            MathKnowledge(
                id="trig_thm_cos_half", statement="∀ θ : ℝ, cos²(θ/2) = (1 + cos θ)/2",
                statement_cn="余弦半角公式", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=3,
                dependencies=["trig_thm_cos_2x_cos"]
            ),
            # 和差化积
            MathKnowledge(
                id="trig_thm_sum_to_prod", statement="∀ α β : ℝ, sin α + sin β = 2 sin((α+β)/2) cos((α-β)/2)",
                statement_cn="和差化积（正弦）", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            # 正弦定理
            MathKnowledge(
                id="trig_thm_law_of_sines", statement="a/sin A = b/sin B = c/sin C = 2R",
                statement_cn="正弦定理", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.GEOMETRY],
                related_domains=[MathDomain.GEOMETRY]
            ),
            # 余弦定理
            MathKnowledge(
                id="trig_thm_law_of_cosines", statement="c² = a² + b² - 2ab cos C",
                statement_cn="余弦定理", domain=MathDomain.TRIGONOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.GEOMETRY],
                related_domains=[MathDomain.GEOMETRY]
            ),
        ]


# ============================================================================
# 几何知识库
# ============================================================================

class GeometryKnowledge(DomainKnowledge):
    """平面几何知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="geo_ax_point_line", statement="∀ P Q : Point, P ≠ Q → ∃! l : Line, P ∈ l ∧ Q ∈ l",
                statement_cn="两点确定一直线", domain=MathDomain.GEOMETRY,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                can_use_in=[MathDomain.SOLID_GEOMETRY, MathDomain.ANALYTIC_GEOMETRY]
            ),
            MathKnowledge(
                id="geo_ax_triangle", statement="∀ a b c : ℝ, a > 0 → b > 0 → c > 0 → a + b > c → valid_triangle(a,b,c)",
                statement_cn="三角形存在条件", domain=MathDomain.GEOMETRY,
                level=KnowledgeLevel.AXIOM, difficulty=1
            ),
            MathKnowledge(
                id="geo_ax_parallel", statement="∀ l : Line, P : Point, P ∉ l → ∃! m : Line, P ∈ m ∧ m ∥ l",
                statement_cn="平行公理", domain=MathDomain.GEOMETRY,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                can_use_in=[MathDomain.SOLID_GEOMETRY]
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="geo_thm_pythagoras", statement="∀ a b c : ℝ, right_triangle(a,b,c) → a² + b² = c²",
                statement_cn="勾股定理", domain=MathDomain.GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.TRIGONOMETRY, MathDomain.ANALYTIC_GEOMETRY],
                related_domains=[MathDomain.ALGEBRA]
            ),
            MathKnowledge(
                id="geo_thm_angle_sum", statement="∀ △ABC, ∠A + ∠B + ∠C = π",
                statement_cn="三角形内角和", domain=MathDomain.GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.TRIGONOMETRY]
            ),
            MathKnowledge(
                id="geo_thm_ext_angle", statement="∀ △ABC, ext∠A = ∠B + ∠C",
                statement_cn="三角形外角定理", domain=MathDomain.GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["geo_thm_angle_sum"]
            ),
            MathKnowledge(
                id="geo_thm_similar", statement="∀ △ABC △DEF, ∠A = ∠D ∧ ∠B = ∠E → △ABC ∼ △DEF",
                statement_cn="AA相似判定", domain=MathDomain.GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="geo_thm_thales", statement="∀ △ABC, l ∥ BC → AB/AD = AC/AE",
                statement_cn="平行线等分定理", domain=MathDomain.GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="geo_thm_circle_inscribed", statement="∀ ∠ABC inscribed in circle, ∠ABC = arc(AC)/2",
                statement_cn="圆周角定理", domain=MathDomain.GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="geo_thm_area_triangle", statement="S = (1/2) * base * height",
                statement_cn="三角形面积公式", domain=MathDomain.GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=1,
                can_use_in=[MathDomain.SOLID_GEOMETRY, MathDomain.ANALYTIC_GEOMETRY]
            ),
        ]


# ============================================================================
# 数论知识库
# ============================================================================

class NumberTheoryKnowledge(DomainKnowledge):
    """数论知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="nt_ax_div", statement="∀ a b : ℤ, b ≠ 0 → ∃ q r : ℤ, a = b*q + r ∧ 0 ≤ r < |b|",
                statement_cn="带余除法", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=2
            ),
            MathKnowledge(
                id="nt_ax_gcd", statement="∀ a b : ℤ, ∃ d : ℤ, d = gcd(a, b) ∧ d | a ∧ d | b",
                statement_cn="最大公约数存在性", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=2
            ),
            MathKnowledge(
                id="nt_def_prime", statement="∀ p : ℕ, prime(p) ↔ p > 1 ∧ ∀ d : ℕ, d | p → d = 1 ∨ d = p",
                statement_cn="素数定义", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=2
            ),
            MathKnowledge(
                id="nt_def_congruence", statement="∀ a b n : ℤ, a ≡ b (mod n) ↔ n | (a - b)",
                statement_cn="同余定义", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=2,
                can_use_in=[MathDomain.COMBINATORICS]
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="nt_thm_euclid", statement="∀ a b : ℤ, gcd(a, b) = gcd(b, a mod b)",
                statement_cn="欧几里得算法", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["nt_ax_div"]
            ),
            MathKnowledge(
                id="nt_thm_bezout", statement="∀ a b : ℤ, ∃ x y : ℤ, a*x + b*y = gcd(a, b)",
                statement_cn="裴蜀定理", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3,
                can_use_in=[MathDomain.ALGEBRA]
            ),
            MathKnowledge(
                id="nt_thm_fta", statement="∀ n > 1, n 可唯一分解为素数乘积",
                statement_cn="算术基本定理", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="nt_thm_fermat_little", statement="∀ a p : ℕ, prime(p) → a^p ≡ a (mod p)",
                statement_cn="费马小定理", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="nt_thm_euler", statement="∀ a n : ℕ, gcd(a,n) = 1 → a^φ(n) ≡ 1 (mod n)",
                statement_cn="欧拉定理", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3,
                dependencies=["nt_thm_fermat_little"]
            ),
            MathKnowledge(
                id="nt_thm_wilson", statement="∀ p : ℕ, prime(p) ↔ (p-1)! ≡ -1 (mod p)",
                statement_cn="威尔逊定理", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="nt_thm_crt", statement="gcd(m,n)=1 → ∃! x, x ≡ a (mod m) ∧ x ≡ b (mod n)",
                statement_cn="中国剩余定理", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="nt_thm_legendre", statement="∀ n p : ℕ, prime(p) → ν_p(n!) = ∑_{k≥1} ⌊n/p^k⌋",
                statement_cn="勒让德定理", domain=MathDomain.NUMBER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3,
                can_use_in=[MathDomain.COMBINATORICS]
            ),
        ]


# ============================================================================
# 立体几何知识库
# ============================================================================

class SolidGeometryKnowledge(DomainKnowledge):
    """立体几何知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="sg_ax_plane", statement="∀ A B C : Point, ¬collinear(A,B,C) → ∃! π : Plane, A ∈ π ∧ B ∈ π ∧ C ∈ π",
                statement_cn="三点确定一平面", domain=MathDomain.SOLID_GEOMETRY,
                level=KnowledgeLevel.AXIOM, difficulty=2,
                can_use_in=[MathDomain.LINEAR_ALGEBRA]
            ),
            MathKnowledge(
                id="sg_ax_line_plane", statement="∀ l : Line, π : Plane, |l ∩ π| ≥ 2 → l ⊂ π",
                statement_cn="直线在平面内", domain=MathDomain.SOLID_GEOMETRY,
                level=KnowledgeLevel.AXIOM, difficulty=2
            ),
            MathKnowledge(
                id="sg_def_parallel", statement="∀ l m : Line, l ∥ m ↔ l ∩ m = ∅ ∧ coplanar(l, m)",
                statement_cn="平行线定义", domain=MathDomain.SOLID_GEOMETRY,
                level=KnowledgeLevel.DEFINITION, difficulty=2
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="sg_thm_line_perp_plane", statement="l ⊥ π ↔ ∀ m ⊂ π, l ⊥ m",
                statement_cn="线面垂直判定", domain=MathDomain.SOLID_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=3,
                can_use_in=[MathDomain.LINEAR_ALGEBRA]
            ),
            MathKnowledge(
                id="sg_thm_three_perp", statement="l ⊥ π ∧ PA ⊂ π ∧ O = l ∩ π → (PO ⊥ PA ↔ OA ⊥ PA)",
                statement_cn="三垂线定理", domain=MathDomain.SOLID_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="sg_thm_plane_parallel", statement="π₁ ∥ π₂ ↔ ∃ l, m ⊂ π₁, l ∦ m ∧ l ∥ π₂ ∧ m ∥ π₂",
                statement_cn="面面平行判定", domain=MathDomain.SOLID_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="sg_thm_euler_polyhedron", statement="∀ P : ConvexPolyhedron, V - E + F = 2",
                statement_cn="欧拉多面体公式", domain=MathDomain.SOLID_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.COMBINATORICS]
            ),
            MathKnowledge(
                id="sg_thm_pyramid_volume", statement="V = (1/3) * S_base * h",
                statement_cn="棱锥体积公式", domain=MathDomain.SOLID_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="sg_thm_sphere_volume", statement="V = (4/3) * π * r³",
                statement_cn="球体积公式", domain=MathDomain.SOLID_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                related_domains=[MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="sg_thm_sphere_surface", statement="S = 4 * π * r²",
                statement_cn="球表面积公式", domain=MathDomain.SOLID_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                related_domains=[MathDomain.CALCULUS]
            ),
        ]


# ============================================================================
# 解析几何知识库
# ============================================================================

class AnalyticGeometryKnowledge(DomainKnowledge):
    """解析几何知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="ag_ax_dist", statement="d(P, Q) = √((x₂-x₁)² + (y₂-y₁)²)",
                statement_cn="两点距离公式", domain=MathDomain.ANALYTIC_GEOMETRY,
                level=KnowledgeLevel.DEFINITION, difficulty=2,
                related_domains=[MathDomain.GEOMETRY],
                can_use_in=[MathDomain.LINEAR_ALGEBRA]
            ),
            MathKnowledge(
                id="ag_ax_midpoint", statement="midpoint(P, Q) = ((x₁+x₂)/2, (y₁+y₂)/2)",
                statement_cn="中点公式", domain=MathDomain.ANALYTIC_GEOMETRY,
                level=KnowledgeLevel.DEFINITION, difficulty=2
            ),
            MathKnowledge(
                id="ag_def_slope", statement="slope(P, Q) = (y₂-y₁)/(x₂-x₁), x₁ ≠ x₂",
                statement_cn="斜率定义", domain=MathDomain.ANALYTIC_GEOMETRY,
                level=KnowledgeLevel.DEFINITION, difficulty=2
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="ag_thm_perp_slope", statement="l₁ ⊥ l₂ ↔ k₁ * k₂ = -1",
                statement_cn="垂直线斜率关系", domain=MathDomain.ANALYTIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="ag_thm_parallel_slope", statement="l₁ ∥ l₂ ↔ k₁ = k₂",
                statement_cn="平行线斜率关系", domain=MathDomain.ANALYTIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="ag_thm_circle_eq", statement="(x-a)² + (y-b)² = r²",
                statement_cn="圆的标准方程", domain=MathDomain.ANALYTIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2,
                related_domains=[MathDomain.GEOMETRY]
            ),
            MathKnowledge(
                id="ag_thm_ellipse_eq", statement="x²/a² + y²/b² = 1",
                statement_cn="椭圆标准方程", domain=MathDomain.ANALYTIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="ag_thm_hyperbola_eq", statement="x²/a² - y²/b² = 1",
                statement_cn="双曲线标准方程", domain=MathDomain.ANALYTIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="ag_thm_parabola_eq", statement="y² = 4px",
                statement_cn="抛物线标准方程", domain=MathDomain.ANALYTIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="ag_thm_ellipse_focal", statement="c² = a² - b²",
                statement_cn="椭圆焦距公式", domain=MathDomain.ANALYTIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="ag_thm_tangent_ellipse", statement="x*x₀/a² + y*y₀/b² = 1",
                statement_cn="椭圆切线方程", domain=MathDomain.ANALYTIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.CALCULUS]
            ),
        ]


# ============================================================================
# 组合知识库
# ============================================================================

class CombinatoricsKnowledge(DomainKnowledge):
    """组合计数知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="comb_ax_add", statement="∀ A B : Set, A ∩ B = ∅ → |A ∪ B| = |A| + |B|",
                statement_cn="加法原理", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                can_use_in=[MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="comb_ax_mult", statement="∀ A B : Set, |A × B| = |A| * |B|",
                statement_cn="乘法原理", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                can_use_in=[MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="comb_def_factorial", statement="n! = n * (n-1) * ... * 1",
                statement_cn="阶乘定义", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.DEFINITION, difficulty=1,
                can_use_in=[MathDomain.PROBABILITY, MathDomain.CALCULUS]
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="comb_thm_perm", statement="P(n, k) = n!/(n-k)!",
                statement_cn="排列数公式", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="comb_thm_comb", statement="C(n, k) = n!/(k!(n-k)!)",
                statement_cn="组合数公式", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.PROBABILITY, MathDomain.NUMBER_THEORY]
            ),
            MathKnowledge(
                id="comb_thm_binomial", statement="(x+y)^n = ∑_{k=0}^{n} C(n,k) x^k y^{n-k}",
                statement_cn="二项式定理", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.CORE, difficulty=3,
                can_use_in=[MathDomain.ALGEBRA, MathDomain.PROBABILITY, MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="comb_thm_pascal", statement="C(n+1, k+1) = C(n, k) + C(n, k+1)",
                statement_cn="帕斯卡恒等式", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="comb_thm_vandermonde", statement="C(m+n, r) = ∑_{k=0}^{r} C(m,k) C(n,r-k)",
                statement_cn="范德蒙德恒等式", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="comb_thm_inclusion_exclusion", statement="|∪A_i| = ∑|A_i| - ∑|A_i∩A_j| + ...",
                statement_cn="容斥原理", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.CORE, difficulty=3,
                can_use_in=[MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="comb_thm_pigeonhole", statement="n > k → ∃ box, |box| > 1",
                statement_cn="鸽巢原理", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.NUMBER_THEORY]
            ),
            MathKnowledge(
                id="comb_thm_catalan", statement="C_n = C(2n,n)/(n+1)",
                statement_cn="卡特兰数公式", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="comb_thm_stirling", statement="n! ≈ √(2πn) * (n/e)^n",
                statement_cn="斯特林公式", domain=MathDomain.COMBINATORICS,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.CALCULUS]
            ),
        ]


# ============================================================================
# 概率知识库
# ============================================================================

class ProbabilityKnowledge(DomainKnowledge):
    """概率统计知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="prob_ax_nonneg", statement="∀ A : Event, P(A) ≥ 0",
                statement_cn="非负性", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.AXIOM, difficulty=1
            ),
            MathKnowledge(
                id="prob_ax_total", statement="P(Ω) = 1",
                statement_cn="规范性", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.AXIOM, difficulty=1
            ),
            MathKnowledge(
                id="prob_ax_add", statement="A ∩ B = ∅ → P(A ∪ B) = P(A) + P(B)",
                statement_cn="可加性", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                related_domains=[MathDomain.COMBINATORICS]
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="prob_thm_complement", statement="P(Ā) = 1 - P(A)",
                statement_cn="补事件概率", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.CORE, difficulty=2,
                dependencies=["prob_ax_total"]
            ),
            MathKnowledge(
                id="prob_thm_inclusion", statement="P(A ∪ B) = P(A) + P(B) - P(A ∩ B)",
                statement_cn="加法公式", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.CORE, difficulty=2,
                related_domains=[MathDomain.COMBINATORICS]
            ),
            MathKnowledge(
                id="prob_thm_conditional", statement="P(A|B) = P(A ∩ B)/P(B)",
                statement_cn="条件概率", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="prob_thm_bayes", statement="P(A|B) = P(B|A) P(A) / P(B)",
                statement_cn="贝叶斯定理", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.CORE, difficulty=3,
                dependencies=["prob_thm_conditional"]
            ),
            MathKnowledge(
                id="prob_thm_total", statement="P(A) = ∑ P(A|B_i) P(B_i)",
                statement_cn="全概率公式", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="prob_thm_expectation", statement="E[X] = ∑ x P(X=x)",
                statement_cn="期望定义", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.COMBINATORICS]
            ),
            MathKnowledge(
                id="prob_thm_variance", statement="Var(X) = E[X²] - E[X]²",
                statement_cn="方差公式", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.CORE, difficulty=2,
                related_domains=[MathDomain.ALGEBRA]
            ),
            MathKnowledge(
                id="prob_thm_binomial", statement="P(X=k) = C(n,k) p^k (1-p)^{n-k}",
                statement_cn="二项分布", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.CORE, difficulty=2,
                related_domains=[MathDomain.COMBINATORICS]
            ),
            MathKnowledge(
                id="prob_thm_chebyshev", statement="P(|X-μ| ≥ kσ) ≤ 1/k²",
                statement_cn="切比雪夫不等式", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.ALGEBRA]
            ),
            MathKnowledge(
                id="prob_thm_lln", statement="X̄_n → E[X] as n → ∞",
                statement_cn="大数定律", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="prob_thm_clt", statement="√n(X̄_n - μ)/σ → N(0,1)",
                statement_cn="中心极限定理", domain=MathDomain.PROBABILITY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.CALCULUS]
            ),
        ]


# ============================================================================
# 微积分知识库
# ============================================================================

class CalculusKnowledge(DomainKnowledge):
    """微积分知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="calc_def_limit", statement="lim_{x→a} f(x) = L ↔ ∀ε>0, ∃δ>0, |x-a|<δ → |f(x)-L|<ε",
                statement_cn="极限定义（ε-δ）", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
            MathKnowledge(
                id="calc_def_deriv", statement="f'(x) = lim_{h→0} (f(x+h)-f(x))/h",
                statement_cn="导数定义", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.DEFINITION, difficulty=3,
                can_use_in=[MathDomain.ANALYTIC_GEOMETRY]
            ),
            MathKnowledge(
                id="calc_def_integral", statement="∫_a^b f(x)dx = lim_{n→∞} ∑ f(x_i) Δx",
                statement_cn="定积分定义", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            # 求导法则
            MathKnowledge(
                id="calc_thm_sum", statement="(f+g)' = f' + g'",
                statement_cn="和的导数", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="calc_thm_product", statement="(fg)' = f'g + fg'",
                statement_cn="积的导数", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="calc_thm_quotient", statement="(f/g)' = (f'g - fg')/g²",
                statement_cn="商的导数", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="calc_thm_chain", statement="(f∘g)' = (f'∘g) · g'",
                statement_cn="链式法则", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            # 基本函数导数
            MathKnowledge(
                id="calc_thm_power", statement="(x^n)' = n x^{n-1}",
                statement_cn="幂函数导数", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.ALGEBRA]
            ),
            MathKnowledge(
                id="calc_thm_exp", statement="(e^x)' = e^x",
                statement_cn="指数函数导数", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="calc_thm_log", statement="(ln x)' = 1/x",
                statement_cn="对数函数导数", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="calc_thm_sin", statement="(sin x)' = cos x",
                statement_cn="正弦函数导数", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=2,
                related_domains=[MathDomain.TRIGONOMETRY]
            ),
            MathKnowledge(
                id="calc_thm_cos", statement="(cos x)' = -sin x",
                statement_cn="余弦函数导数", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=2,
                related_domains=[MathDomain.TRIGONOMETRY]
            ),
            # 定理
            MathKnowledge(
                id="calc_thm_mvt", statement="∃ c ∈ (a,b), f'(c) = (f(b)-f(a))/(b-a)",
                statement_cn="中值定理", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="calc_thm_ftc", statement="∫_a^b f'(x)dx = f(b) - f(a)",
                statement_cn="微积分基本定理", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="calc_thm_ibp", statement="∫ u dv = uv - ∫ v du",
                statement_cn="分部积分", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="calc_thm_taylor", statement="f(x) = ∑ f^{(n)}(a)/n! · (x-a)^n",
                statement_cn="泰勒展开", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=4,
                can_use_in=[MathDomain.ALGEBRA, MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="calc_thm_lhopital", statement="lim f/g = lim f'/g'",
                statement_cn="洛必达法则", domain=MathDomain.CALCULUS,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
        ]


# ============================================================================
# 线性代数知识库
# ============================================================================

class LinearAlgebraKnowledge(DomainKnowledge):
    """线性代数知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="la_ax_vec_add", statement="∀ u v : V, u + v ∈ V",
                statement_cn="向量加法封闭", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.AXIOM, difficulty=2
            ),
            MathKnowledge(
                id="la_ax_scalar", statement="∀ c : F, v : V, c·v ∈ V",
                statement_cn="数乘封闭", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.AXIOM, difficulty=2
            ),
            MathKnowledge(
                id="la_def_det", statement="det(A) = ∑_{σ} sgn(σ) ∏ a_{i,σ(i)}",
                statement_cn="行列式定义", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
            MathKnowledge(
                id="la_def_inner", statement="⟨u,v⟩ = ∑ u_i v_i",
                statement_cn="内积定义", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.DEFINITION, difficulty=2,
                can_use_in=[MathDomain.GEOMETRY, MathDomain.ANALYTIC_GEOMETRY]
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="la_thm_det_mult", statement="det(AB) = det(A) det(B)",
                statement_cn="行列式乘法", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="la_thm_det_transpose", statement="det(A^T) = det(A)",
                statement_cn="转置行列式", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="la_thm_det_inverse", statement="det(A^{-1}) = 1/det(A)",
                statement_cn="逆矩阵行列式", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="la_thm_cramer", statement="x_i = det(A_i)/det(A)",
                statement_cn="克莱默法则", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="la_thm_rank_nullity", statement="dim(V) = rank(T) + nullity(T)",
                statement_cn="秩-零化度定理", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="la_thm_eigenvalue", statement="det(A - λI) = 0",
                statement_cn="特征值定义", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="la_thm_trace", statement="tr(A) = ∑ λ_i",
                statement_cn="迹等于特征值和", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="la_thm_det_eigenproduct", statement="det(A) = ∏ λ_i",
                statement_cn="行列式等于特征值积", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="la_thm_cayley_hamilton", statement="p(A) = 0",
                statement_cn="凯莱-哈密顿定理", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="la_thm_cauchy_schwarz", statement="|⟨u,v⟩| ≤ ‖u‖ ‖v‖",
                statement_cn="柯西-施瓦茨不等式", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.ALGEBRA]
            ),
            MathKnowledge(
                id="la_thm_gram_schmidt", statement="正交化过程",
                statement_cn="格拉姆-施密特正交化", domain=MathDomain.LINEAR_ALGEBRA,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
        ]


# ============================================================================
# 环论知识库
# ============================================================================

class RingTheoryKnowledge(DomainKnowledge):
    """环论知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="rt_ax_ring", statement="(R, +, ·) 满足加法 Abel 群 + 乘法半群 + 分配律",
                statement_cn="环的定义", domain=MathDomain.RING_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=2,
                can_use_in=[MathDomain.ALGEBRA, MathDomain.FIELD_THEORY]
            ),
            MathKnowledge(
                id="rt_ax_ideal", statement="I ⊆ R, ∀ a ∈ I, r ∈ R, ra ∈ I ∧ ar ∈ I",
                statement_cn="理想定义", domain=MathDomain.RING_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=3,
                can_use_in=[MathDomain.ALGEBRAIC_GEOMETRY]
            ),
            MathKnowledge(
                id="rt_def_pid", statement="R 是 PID ↔ R 是整环且每个理想都是主理想",
                statement_cn="主理想整环定义", domain=MathDomain.RING_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="rt_thm_quotient", statement="R/I 在自然运算下构成环",
                statement_cn="商环定理", domain=MathDomain.RING_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3,
                dependencies=["rt_ax_ideal"]
            ),
            MathKnowledge(
                id="rt_thm_isomorphism1", statement="R/ker(φ) ≅ im(φ)",
                statement_cn="环同构第一定理", domain=MathDomain.RING_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="rt_thm_chinese_remainder", statement="R/(I∩J) ≅ R/I × R/J (I+J=R)",
                statement_cn="中国剩余定理（环论形式）", domain=MathDomain.RING_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.NUMBER_THEORY]
            ),
            MathKnowledge(
                id="rt_thm_noetherian", statement="R 是 Noether 环 ↔ 每个理想有限生成",
                statement_cn="Noether 环等价条件", domain=MathDomain.RING_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                can_use_in=[MathDomain.ALGEBRAIC_GEOMETRY]
            ),
            MathKnowledge(
                id="rt_thm_hilbert_basis", statement="R 是 Noether 环 → R[x] 是 Noether 环",
                statement_cn="Hilbert 基定理", domain=MathDomain.RING_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                can_use_in=[MathDomain.ALGEBRAIC_GEOMETRY]
            ),
            MathKnowledge(
                id="rt_thm_krull", statement="交换 Noether 环中每个极大理想为素理想",
                statement_cn="Krull 定理", domain=MathDomain.RING_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="rt_thm_localization", statement="S⁻¹R 是 R 关于 S 的局部化",
                statement_cn="局部化理论", domain=MathDomain.RING_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                can_use_in=[MathDomain.ALGEBRAIC_GEOMETRY]
            ),
            MathKnowledge(
                id="rt_thm_dedekind", statement="Dedekind 整环中每个非零理想唯一分解为素理想之积",
                statement_cn="Dedekind 整环唯一分解", domain=MathDomain.RING_THEORY,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.NUMBER_THEORY]
            ),
        ]


# ============================================================================
# 群论知识库
# ============================================================================

class GroupTheoryKnowledge(DomainKnowledge):
    """群论知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="gt_ax_group", statement="(G, ·) 满足封闭性、结合律、单位元、逆元",
                statement_cn="群的定义", domain=MathDomain.GROUP_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=2,
                can_use_in=[MathDomain.ALGEBRA, MathDomain.RING_THEORY]
            ),
            MathKnowledge(
                id="gt_def_subgroup", statement="H ≤ G ↔ H ≠ ∅ ∧ ∀ a,b ∈ H, ab⁻¹ ∈ H",
                statement_cn="子群定义", domain=MathDomain.GROUP_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=2
            ),
            MathKnowledge(
                id="gt_def_normal", statement="N ◁ G ↔ ∀ g ∈ G, gNg⁻¹ = N",
                statement_cn="正规子群定义", domain=MathDomain.GROUP_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="gt_thm_lagrange", statement="|H| | |G| (H ≤ G, G 有限)",
                statement_cn="Lagrange 定理", domain=MathDomain.GROUP_THEORY,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.NUMBER_THEORY]
            ),
            MathKnowledge(
                id="gt_thm_cayley", statement="每个群同构于某个置换群的子群",
                statement_cn="Cayley 定理", domain=MathDomain.GROUP_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="gt_thm_isomorphism1", statement="G/ker(φ) ≅ im(φ)",
                statement_cn="群同构第一定理", domain=MathDomain.GROUP_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="gt_thm_sylow1", statement="p^k | |G| → G 有 p^k 阶子群",
                statement_cn="Sylow 第一定理", domain=MathDomain.GROUP_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="gt_thm_sylow2", statement="G 的所有 Sylow p-子群共轭",
                statement_cn="Sylow 第二定理", domain=MathDomain.GROUP_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="gt_thm_sylow3", statement="n_p ≡ 1 (mod p) ∧ n_p | |G|/p^k",
                statement_cn="Sylow 第三定理", domain=MathDomain.GROUP_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="gt_thm_burnside", statement="|X/G| = (1/|G|) ∑_{g∈G} |Fix(g)|",
                statement_cn="Burnside 引理", domain=MathDomain.GROUP_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.COMBINATORICS]
            ),
            MathKnowledge(
                id="gt_thm_jordan_holder", statement="有限群的合成列本质唯一",
                statement_cn="Jordan-Hölder 定理", domain=MathDomain.GROUP_THEORY,
                level=KnowledgeLevel.CORE, difficulty=5
            ),
        ]


# ============================================================================
# 域论知识库
# ============================================================================

class FieldTheoryKnowledge(DomainKnowledge):
    """域论知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="ft_ax_field", statement="(F, +, ·) 满足交换环 + F* 构成乘法群",
                statement_cn="域的定义", domain=MathDomain.FIELD_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=2,
                can_use_in=[MathDomain.LINEAR_ALGEBRA, MathDomain.RING_THEORY]
            ),
            MathKnowledge(
                id="ft_def_extension", statement="L/K 是域扩张 ↔ K ⊆ L 且 L 是域",
                statement_cn="域扩张定义", domain=MathDomain.FIELD_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
            MathKnowledge(
                id="ft_def_galois", statement="L/K 是 Galois 扩张 ↔ L/K 正规且可分",
                statement_cn="Galois 扩张定义", domain=MathDomain.FIELD_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=4
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="ft_thm_tower", statement="[L:K] = [L:F][F:K]",
                statement_cn="度数乘法塔定理", domain=MathDomain.FIELD_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="ft_thm_galois", statement="L/K Galois ↔ 中间域格与 Gal(L/K) 子群格反同构",
                statement_cn="Galois 基本定理", domain=MathDomain.FIELD_THEORY,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.GROUP_THEORY]
            ),
            MathKnowledge(
                id="ft_thm_splitting", statement="∀ f ∈ K[x], ∃ L/K, f 在 L 中完全分裂",
                statement_cn="分裂域存在性", domain=MathDomain.FIELD_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="ft_thm_primitive", statement="有限可分扩张是单扩张",
                statement_cn="本原元素定理", domain=MathDomain.FIELD_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="ft_thm_artin", statement="G ≤ Aut(L) → [L:L^G] = |G|",
                statement_cn="Artin 定理", domain=MathDomain.FIELD_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="ft_thm_finite_field", statement="有限域的阶为素数幂 p^n",
                statement_cn="有限域分类", domain=MathDomain.FIELD_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.NUMBER_THEORY]
            ),
        ]


# ============================================================================
# 拓扑学知识库
# ============================================================================

class TopologyKnowledge(DomainKnowledge):
    """拓扑学知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="top_ax_open", statement="τ 满足：X,∅ ∈ τ; 有限交封闭; 任意并封闭",
                statement_cn="拓扑空间公理", domain=MathDomain.TOPOLOGY,
                level=KnowledgeLevel.AXIOM, difficulty=2,
                can_use_in=[MathDomain.CALCULUS, MathDomain.ALGEBRAIC_TOPOLOGY]
            ),
            MathKnowledge(
                id="top_def_continuous", statement="f : X → Y 连续 ↔ ∀ V ∈ τ_Y, f⁻¹(V) ∈ τ_X",
                statement_cn="连续映射定义", domain=MathDomain.TOPOLOGY,
                level=KnowledgeLevel.DEFINITION, difficulty=2
            ),
            MathKnowledge(
                id="top_def_compact", statement="X 紧 ↔ 每个开覆盖有有限子覆盖",
                statement_cn="紧致性定义", domain=MathDomain.TOPOLOGY,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="top_thm_tychonoff", statement="∏ X_i 紧 ↔ 每个 X_i 紧",
                statement_cn="Tychonoff 定理", domain=MathDomain.TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=5
            ),
            MathKnowledge(
                id="top_thm_heine_borel", statement="ℝⁿ 中紧致 ↔ 有界闭集",
                statement_cn="Heine-Borel 定理", domain=MathDomain.TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="top_thm_urysohn", statement="正规空间中不相交闭集可被连续函数分离",
                statement_cn="Urysohn 引理", domain=MathDomain.TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="top_thm_baire", statement="完备度量空间是 Baire 空间",
                statement_cn="Baire 纲定理", domain=MathDomain.TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="top_thm_ivt", statement="连续函数保持连通性",
                statement_cn="连通性保持定理", domain=MathDomain.TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=2,
                can_use_in=[MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="top_thm_extreme_value", statement="紧集上连续函数达到最值",
                statement_cn="极值定理", domain=MathDomain.TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=3,
                can_use_in=[MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="top_thm_homeomorphism", statement="f 同胚 ↔ f 连续双射且 f⁻¹ 连续",
                statement_cn="同胚定义定理", domain=MathDomain.TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="top_thm_brouwer", statement="Dⁿ → Dⁿ 的连续映射有不动点",
                statement_cn="Brouwer 不动点定理", domain=MathDomain.TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.ALGEBRAIC_TOPOLOGY, MathDomain.DYNAMICS]
            ),
        ]


# ============================================================================
# 测度论知识库
# ============================================================================

class MeasureTheoryKnowledge(DomainKnowledge):
    """测度论知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="mt_ax_sigma", statement="σ-代数 Σ 对补、可数并封闭",
                statement_cn="σ-代数定义", domain=MathDomain.MEASURE_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=3,
                can_use_in=[MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="mt_ax_measure", statement="μ : Σ → [0,∞], μ(∅)=0, σ-可加性",
                statement_cn="测度公理", domain=MathDomain.MEASURE_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=3,
                can_use_in=[MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="mt_def_lebesgue", statement="Lebesgue 测度是 ℝⁿ 上的完备正则 Borel 测度",
                statement_cn="Lebesgue 测度定义", domain=MathDomain.MEASURE_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="mt_thm_monotone_convergence", statement="0 ≤ f_n ↑ f → ∫f_n → ∫f",
                statement_cn="单调收敛定理", domain=MathDomain.MEASURE_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                can_use_in=[MathDomain.CALCULUS, MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="mt_thm_dominated_convergence", statement="f_n → f a.e., |f_n| ≤ g ∈ L¹ → ∫f_n → ∫f",
                statement_cn="控制收敛定理", domain=MathDomain.MEASURE_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                can_use_in=[MathDomain.CALCULUS, MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="mt_thm_fatou", statement="∫ lim inf f_n ≤ lim inf ∫ f_n",
                statement_cn="Fatou 引理", domain=MathDomain.MEASURE_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="mt_thm_fubini", statement="可积函数的重积分可交换积分次序",
                statement_cn="Fubini 定理", domain=MathDomain.MEASURE_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                can_use_in=[MathDomain.CALCULUS, MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="mt_thm_radon_nikodym", statement="ν ≪ μ → ∃ f ≥ 0, ν(A) = ∫_A f dμ",
                statement_cn="Radon-Nikodym 定理", domain=MathDomain.MEASURE_THEORY,
                level=KnowledgeLevel.CORE, difficulty=5,
                can_use_in=[MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="mt_thm_riesz", statement="L^p 空间在 1 ≤ p < ∞ 时是 Banach 空间",
                statement_cn="Riesz-Fischer 定理", domain=MathDomain.MEASURE_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.CALCULUS, MathDomain.TOPOLOGY]
            ),
        ]


# ============================================================================
# 范畴论知识库
# ============================================================================

class CategoryTheoryKnowledge(DomainKnowledge):
    """范畴论知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="cat_ax_category", statement="范畴 C = (Ob(C), Mor(C), ∘, id) 满足结合律和单位律",
                statement_cn="范畴定义", domain=MathDomain.CATEGORY_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=3
            ),
            MathKnowledge(
                id="cat_def_functor", statement="F : C → D 保持复合和恒等态射",
                statement_cn="函子定义", domain=MathDomain.CATEGORY_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
            MathKnowledge(
                id="cat_def_natural", statement="η : F → G 是对每个 X 的态射 η_X 且满足自然性方块",
                statement_cn="自然变换定义", domain=MathDomain.CATEGORY_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=4
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="cat_thm_yoneda", statement="Hom(h_A, F) ≅ F(A) (自然同构)",
                statement_cn="Yoneda 引理", domain=MathDomain.CATEGORY_THEORY,
                level=KnowledgeLevel.CORE, difficulty=5
            ),
            MathKnowledge(
                id="cat_thm_adjunction", statement="F ⊣ G ↔ Hom(FA, B) ≅ Hom(A, GB)",
                statement_cn="伴随函子定理", domain=MathDomain.CATEGORY_THEORY,
                level=KnowledgeLevel.CORE, difficulty=5
            ),
            MathKnowledge(
                id="cat_thm_limit", statement="完备范畴中任意小图有极限",
                statement_cn="极限存在定理", domain=MathDomain.CATEGORY_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="cat_thm_equivalence", statement="F : C → D 等价 ↔ F 全忠实且本质满",
                statement_cn="范畴等价判定", domain=MathDomain.CATEGORY_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="cat_thm_abelian", statement="Abel 范畴中每个态射有核和余核",
                statement_cn="Abel 范畴性质", domain=MathDomain.CATEGORY_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.ALGEBRA]
            ),
            MathKnowledge(
                id="cat_thm_freyd", statement="Freyd: 有余等化子的完备范畴有伴随函子",
                statement_cn="Freyd 伴随函子定理", domain=MathDomain.CATEGORY_THEORY,
                level=KnowledgeLevel.CORE, difficulty=5
            ),
        ]


# ============================================================================
# 序论知识库
# ============================================================================

class OrderTheoryKnowledge(DomainKnowledge):
    """序论知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="ord_ax_poset", statement="(P, ≤) 满足自反、反对称、传递",
                statement_cn="偏序集定义", domain=MathDomain.ORDER_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                can_use_in=[MathDomain.SET_THEORY, MathDomain.COMBINATORICS]
            ),
            MathKnowledge(
                id="ord_def_lattice", statement="格 = 每对元素有上确界和下确界的偏序集",
                statement_cn="格定义", domain=MathDomain.ORDER_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=2,
                can_use_in=[MathDomain.ALGEBRA, MathDomain.TOPOLOGY]
            ),
            MathKnowledge(
                id="ord_def_well_order", statement="良序 = 每个非空子集有最小元的全序",
                statement_cn="良序定义", domain=MathDomain.ORDER_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=2,
                can_use_in=[MathDomain.SET_THEORY]
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="ord_thm_zorn", statement="每条链有上界的偏序集有极大元",
                statement_cn="Zorn 引理", domain=MathDomain.ORDER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3,
                can_use_in=[MathDomain.ALGEBRA, MathDomain.TOPOLOGY, MathDomain.SET_THEORY]
            ),
            MathKnowledge(
                id="ord_thm_knaster_tarski", statement="完备格上的保序映射有不动点",
                statement_cn="Knaster-Tarski 不动点定理", domain=MathDomain.ORDER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="ord_thm_dilworth", statement="最长反链长 = 最少链覆盖数",
                statement_cn="Dilworth 定理", domain=MathDomain.ORDER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.COMBINATORICS]
            ),
            MathKnowledge(
                id="ord_thm_birkhoff", statement="有限分配格同构于某集族上的并/交格",
                statement_cn="Birkhoff 表示定理", domain=MathDomain.ORDER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="ord_thm_complete_lattice", statement="完备格中每个子集有上确界和下确界",
                statement_cn="完备格性质", domain=MathDomain.ORDER_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
        ]


# ============================================================================
# 集合论知识库
# ============================================================================

class SetTheoryKnowledge(DomainKnowledge):
    """集合论知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="set_ax_ext", statement="∀ A B, (∀ x, x ∈ A ↔ x ∈ B) → A = B",
                statement_cn="外延公理", domain=MathDomain.SET_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                can_use_in=[MathDomain.LOGIC]
            ),
            MathKnowledge(
                id="set_ax_power", statement="∀ A, ∃ P, ∀ B, B ∈ P ↔ B ⊆ A",
                statement_cn="幂集公理", domain=MathDomain.SET_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=2
            ),
            MathKnowledge(
                id="set_ax_choice", statement="∀ 非空集族, ∃ 选择函数",
                statement_cn="选择公理", domain=MathDomain.SET_THEORY,
                level=KnowledgeLevel.AXIOM, difficulty=3,
                can_use_in=[MathDomain.ORDER_THEORY, MathDomain.ALGEBRA, MathDomain.TOPOLOGY]
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="set_thm_cantor", statement="|A| < |P(A)|",
                statement_cn="Cantor 定理", domain=MathDomain.SET_THEORY,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="set_thm_schroder_bernstein", statement="|A| ≤ |B| ∧ |B| ≤ |A| → |A| = |B|",
                statement_cn="Schröder-Bernstein 定理", domain=MathDomain.SET_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="set_thm_well_ordering", statement="每个集合可良序化",
                statement_cn="良序定理", domain=MathDomain.SET_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3,
                dependencies=["set_ax_choice"],
                related_domains=[MathDomain.ORDER_THEORY]
            ),
            MathKnowledge(
                id="set_thm_cardinal_arithmetic", statement="ℵ₀ · ℵ₀ = ℵ₀; |ℝ| = 2^ℵ₀",
                statement_cn="基数算术", domain=MathDomain.SET_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="set_thm_ordinal_arithmetic", statement="每个良序集同构于唯一序数",
                statement_cn="序数表示定理", domain=MathDomain.SET_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.ORDER_THEORY]
            ),
        ]


# ============================================================================
# 逻辑学知识库
# ============================================================================

class LogicKnowledge(DomainKnowledge):
    """逻辑学知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="log_ax_identity", statement="⊢ P → P",
                statement_cn="同一律", domain=MathDomain.LOGIC,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                can_use_in=[MathDomain.SET_THEORY]
            ),
            MathKnowledge(
                id="log_ax_excluded_middle", statement="⊢ P ∨ ¬P",
                statement_cn="排中律", domain=MathDomain.LOGIC,
                level=KnowledgeLevel.AXIOM, difficulty=1,
                can_use_in=[MathDomain.SET_THEORY]
            ),
            MathKnowledge(
                id="log_ax_modus_ponens", statement="P, P → Q ⊢ Q",
                statement_cn="Modus Ponens", domain=MathDomain.LOGIC,
                level=KnowledgeLevel.AXIOM, difficulty=1
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="log_thm_deduction", statement="Γ, P ⊢ Q ↔ Γ ⊢ P → Q",
                statement_cn="演绎定理", domain=MathDomain.LOGIC,
                level=KnowledgeLevel.CORE, difficulty=2
            ),
            MathKnowledge(
                id="log_thm_completeness", statement="⊨ φ ↔ ⊢ φ (一阶逻辑)",
                statement_cn="Gödel 完备性定理", domain=MathDomain.LOGIC,
                level=KnowledgeLevel.CORE, difficulty=5
            ),
            MathKnowledge(
                id="log_thm_incompleteness1", statement="一致的递归公理化系统不能证明所有真算术命题",
                statement_cn="Gödel 不完备性第一定理", domain=MathDomain.LOGIC,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.NUMBER_THEORY]
            ),
            MathKnowledge(
                id="log_thm_incompleteness2", statement="一致的系统不能证明自身的一致性",
                statement_cn="Gödel 不完备性第二定理", domain=MathDomain.LOGIC,
                level=KnowledgeLevel.CORE, difficulty=5
            ),
            MathKnowledge(
                id="log_thm_compactness", statement="Σ 有模型 ↔ Σ 的每个有限子集有模型",
                statement_cn="紧致性定理", domain=MathDomain.LOGIC,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="log_thm_lowenheim_skolem", statement="可数一阶理论有模型 → 有可数模型",
                statement_cn="Löwenheim-Skolem 定理", domain=MathDomain.LOGIC,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
        ]


# ============================================================================
# 代数几何知识库
# ============================================================================

class AlgebraicGeometryKnowledge(DomainKnowledge):
    """代数几何知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="ag2_def_variety", statement="V(I) = {x ∈ kⁿ : ∀ f ∈ I, f(x) = 0}",
                statement_cn="仿射簇定义", domain=MathDomain.ALGEBRAIC_GEOMETRY,
                level=KnowledgeLevel.DEFINITION, difficulty=3,
                related_domains=[MathDomain.RING_THEORY]
            ),
            MathKnowledge(
                id="ag2_def_scheme", statement="概形 = 局部环化空间，局部同构于 Spec(R)",
                statement_cn="概形定义", domain=MathDomain.ALGEBRAIC_GEOMETRY,
                level=KnowledgeLevel.DEFINITION, difficulty=5,
                related_domains=[MathDomain.RING_THEORY, MathDomain.TOPOLOGY]
            ),
            MathKnowledge(
                id="ag2_def_sheaf", statement="层 = 满足粘合条件的预层",
                statement_cn="层定义", domain=MathDomain.ALGEBRAIC_GEOMETRY,
                level=KnowledgeLevel.DEFINITION, difficulty=4,
                can_use_in=[MathDomain.ALGEBRAIC_TOPOLOGY, MathDomain.TOPOLOGY]
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="ag2_thm_nullstellensatz", statement="I(V(J)) = √J",
                statement_cn="Hilbert 零点定理", domain=MathDomain.ALGEBRAIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.RING_THEORY]
            ),
            MathKnowledge(
                id="ag2_thm_bezout", statement="deg(C₁ ∩ C₂) = deg(C₁) · deg(C₂)",
                statement_cn="Bézout 定理", domain=MathDomain.ALGEBRAIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="ag2_thm_riemann_roch", statement="l(D) - l(K-D) = deg(D) - g + 1",
                statement_cn="Riemann-Roch 定理", domain=MathDomain.ALGEBRAIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.TOPOLOGY]
            ),
            MathKnowledge(
                id="ag2_thm_serre_duality", statement="H^i(X, F) ≅ H^{n-i}(X, ω ⊗ F∨)∨",
                statement_cn="Serre 对偶定理", domain=MathDomain.ALGEBRAIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.CATEGORY_THEORY]
            ),
            MathKnowledge(
                id="ag2_thm_spec_functor", statement="Spec : CRing^op → Sch 是反变函子",
                statement_cn="Spec 函子性", domain=MathDomain.ALGEBRAIC_GEOMETRY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.CATEGORY_THEORY, MathDomain.RING_THEORY]
            ),
        ]


# ============================================================================
# 代数拓扑知识库
# ============================================================================

class AlgebraicTopologyKnowledge(DomainKnowledge):
    """代数拓扑知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="at_def_fundamental_group", statement="π₁(X, x₀) = 基于 x₀ 的环路同伦类",
                statement_cn="基本群定义", domain=MathDomain.ALGEBRAIC_TOPOLOGY,
                level=KnowledgeLevel.DEFINITION, difficulty=3,
                related_domains=[MathDomain.GROUP_THEORY, MathDomain.TOPOLOGY]
            ),
            MathKnowledge(
                id="at_def_homology", statement="H_n(X) = ker(∂_n)/im(∂_{n+1})",
                statement_cn="奇异同调群定义", domain=MathDomain.ALGEBRAIC_TOPOLOGY,
                level=KnowledgeLevel.DEFINITION, difficulty=4,
                related_domains=[MathDomain.GROUP_THEORY]
            ),
            MathKnowledge(
                id="at_def_homotopy", statement="f ≃ g ↔ ∃ H : X×I → Y, H(·,0)=f, H(·,1)=g",
                statement_cn="同伦定义", domain=MathDomain.ALGEBRAIC_TOPOLOGY,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="at_thm_seifert_van_kampen", statement="π₁(X₁ ∪ X₂) ≅ π₁(X₁) *_{π₁(X₁∩X₂)} π₁(X₂)",
                statement_cn="Seifert-van Kampen 定理", domain=MathDomain.ALGEBRAIC_TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="at_thm_hurewicz", statement="X (n-1)-连通 → π_n(X) ≅ H_n(X)",
                statement_cn="Hurewicz 定理", domain=MathDomain.ALGEBRAIC_TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=5
            ),
            MathKnowledge(
                id="at_thm_mayer_vietoris", statement="... → H_n(A∩B) → H_n(A)⊕H_n(B) → H_n(X) → ...",
                statement_cn="Mayer-Vietoris 长正合列", domain=MathDomain.ALGEBRAIC_TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="at_thm_euler_characteristic", statement="χ(X) = ∑ (-1)^i rank(H_i(X))",
                statement_cn="Euler 示性数", domain=MathDomain.ALGEBRAIC_TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.COMBINATORICS]
            ),
            MathKnowledge(
                id="at_thm_covering", statement="覆叠空间与 π₁ 的子群一一对应",
                statement_cn="覆叠空间分类定理", domain=MathDomain.ALGEBRAIC_TOPOLOGY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.GROUP_THEORY]
            ),
        ]


# ============================================================================
# 表示论知识库
# ============================================================================

class RepresentationTheoryKnowledge(DomainKnowledge):
    """表示论知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="rep_def_representation", statement="ρ : G → GL(V) 是群同态",
                statement_cn="群表示定义", domain=MathDomain.REPRESENTATION_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=3,
                related_domains=[MathDomain.GROUP_THEORY, MathDomain.LINEAR_ALGEBRA]
            ),
            MathKnowledge(
                id="rep_def_character", statement="χ_ρ(g) = tr(ρ(g))",
                statement_cn="特征标定义", domain=MathDomain.REPRESENTATION_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
            MathKnowledge(
                id="rep_def_irreducible", statement="V 不可约 ↔ V 没有非平凡不变子空间",
                statement_cn="不可约表示定义", domain=MathDomain.REPRESENTATION_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="rep_thm_maschke", statement="特征不整除 |G| 时，有限群的表示完全可约",
                statement_cn="Maschke 定理", domain=MathDomain.REPRESENTATION_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.GROUP_THEORY]
            ),
            MathKnowledge(
                id="rep_thm_schur", statement="不可约表示间的 G-映射要么零要么同构",
                statement_cn="Schur 引理", domain=MathDomain.REPRESENTATION_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="rep_thm_character_orthogonality", statement="⟨χ_i, χ_j⟩ = δ_{ij}",
                statement_cn="特征标正交关系", domain=MathDomain.REPRESENTATION_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
            MathKnowledge(
                id="rep_thm_class_count", statement="不可约表示个数 = 共轭类个数",
                statement_cn="不可约表示分类", domain=MathDomain.REPRESENTATION_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.GROUP_THEORY]
            ),
            MathKnowledge(
                id="rep_thm_regular", statement="正则表示分解包含每个不可约表示，重数等于维数",
                statement_cn="正则表示分解", domain=MathDomain.REPRESENTATION_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
        ]


# ============================================================================
# 动力系统知识库
# ============================================================================

class DynamicsKnowledge(DomainKnowledge):
    """动力系统知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="dyn_def_flow", statement="φ : ℝ × X → X, φ(0,x)=x, φ(s+t,x)=φ(s,φ(t,x))",
                statement_cn="流定义", domain=MathDomain.DYNAMICS,
                level=KnowledgeLevel.DEFINITION, difficulty=3,
                related_domains=[MathDomain.TOPOLOGY]
            ),
            MathKnowledge(
                id="dyn_def_fixed_point", statement="x* 是不动点 ↔ f(x*) = x*",
                statement_cn="不动点定义", domain=MathDomain.DYNAMICS,
                level=KnowledgeLevel.DEFINITION, difficulty=2
            ),
            MathKnowledge(
                id="dyn_def_ergodic", statement="T 遍历 ↔ T⁻¹(A) = A 蕴含 μ(A)=0 或 μ(A)=1",
                statement_cn="遍历性定义", domain=MathDomain.DYNAMICS,
                level=KnowledgeLevel.DEFINITION, difficulty=4,
                related_domains=[MathDomain.MEASURE_THEORY]
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="dyn_thm_banach", statement="完备度量空间上的压缩映射有唯一不动点",
                statement_cn="Banach 不动点定理", domain=MathDomain.DYNAMICS,
                level=KnowledgeLevel.CORE, difficulty=3,
                can_use_in=[MathDomain.CALCULUS, MathDomain.TOPOLOGY]
            ),
            MathKnowledge(
                id="dyn_thm_birkhoff", statement="遍历系统中时间平均等于空间平均",
                statement_cn="Birkhoff 遍历定理", domain=MathDomain.DYNAMICS,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.MEASURE_THEORY]
            ),
            MathKnowledge(
                id="dyn_thm_poincare", statement="保测映射下几乎每个点无穷次回归",
                statement_cn="Poincaré 回归定理", domain=MathDomain.DYNAMICS,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.MEASURE_THEORY]
            ),
            MathKnowledge(
                id="dyn_thm_lyapunov", statement="V(x) > 0, V̇(x) < 0 → x* 渐近稳定",
                statement_cn="Lyapunov 稳定性定理", domain=MathDomain.DYNAMICS,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="dyn_thm_sarkovskii", statement="连续映射的周期轨道存在性由 Šarkovskiĭ 序决定",
                statement_cn="Šarkovskiĭ 定理", domain=MathDomain.DYNAMICS,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.TOPOLOGY]
            ),
        ]


# ============================================================================
# 信息论知识库
# ============================================================================

class InformationTheoryKnowledge(DomainKnowledge):
    """信息论知识库"""
    
    @staticmethod
    def get_axioms() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="it_def_entropy", statement="H(X) = -∑ p(x) log p(x)",
                statement_cn="Shannon 熵定义", domain=MathDomain.INFORMATION_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=2,
                related_domains=[MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="it_def_mutual", statement="I(X;Y) = H(X) + H(Y) - H(X,Y)",
                statement_cn="互信息定义", domain=MathDomain.INFORMATION_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=3,
                related_domains=[MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="it_def_kl", statement="D_KL(P‖Q) = ∑ p(x) log(p(x)/q(x))",
                statement_cn="KL 散度定义", domain=MathDomain.INFORMATION_THEORY,
                level=KnowledgeLevel.DEFINITION, difficulty=3
            ),
        ]
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="it_thm_source_coding", statement="无损压缩平均码长 ≥ H(X)",
                statement_cn="Shannon 无损信源编码定理", domain=MathDomain.INFORMATION_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="it_thm_channel_coding", statement="C = max_{p(x)} I(X;Y), 速率 < C 时可靠传输",
                statement_cn="Shannon 信道编码定理", domain=MathDomain.INFORMATION_THEORY,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="it_thm_gibbs", statement="D_KL(P‖Q) ≥ 0, 等号当且仅当 P = Q",
                statement_cn="Gibbs 不等式", domain=MathDomain.INFORMATION_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="it_thm_data_processing", statement="X → Y → Z 蕴含 I(X;Z) ≤ I(X;Y)",
                statement_cn="数据处理不等式", domain=MathDomain.INFORMATION_THEORY,
                level=KnowledgeLevel.CORE, difficulty=3
            ),
            MathKnowledge(
                id="it_thm_fano", statement="P_e ≥ (H(X|Y) - 1)/log(|X| - 1)",
                statement_cn="Fano 不等式", domain=MathDomain.INFORMATION_THEORY,
                level=KnowledgeLevel.CORE, difficulty=4
            ),
        ]


# ============================================================================
# 跨领域知识
# ============================================================================

class CrossDomainKnowledge(DomainKnowledge):
    """跨领域定理 - 连接不同数学分支"""
    
    @staticmethod
    def get_theorems() -> List[MathKnowledge]:
        return [
            MathKnowledge(
                id="cross_euler_formula", statement="e^{iθ} = cos θ + i sin θ",
                statement_cn="欧拉公式", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.TRIGONOMETRY, MathDomain.CALCULUS, MathDomain.ALGEBRA]
            ),
            MathKnowledge(
                id="cross_rotation_matrix", statement="R(θ) = [[cos θ, -sin θ], [sin θ, cos θ]]",
                statement_cn="旋转矩阵", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=2,
                related_domains=[MathDomain.LINEAR_ALGEBRA, MathDomain.GEOMETRY, MathDomain.TRIGONOMETRY]
            ),
            MathKnowledge(
                id="cross_gaussian_integral", statement="∫_{-∞}^{∞} e^{-x²/2} dx = √(2π)",
                statement_cn="高斯积分", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.CALCULUS, MathDomain.PROBABILITY]
            ),
            MathKnowledge(
                id="cross_fermat_sum_sq", statement="p = 2 ∨ p ≡ 1 (mod 4) → p = a² + b²",
                statement_cn="费马二平方和定理", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.NUMBER_THEORY, MathDomain.ALGEBRA]
            ),
            MathKnowledge(
                id="cross_lucas", statement="C(m,n) ≡ ∏ C(m_i, n_i) (mod p)",
                statement_cn="卢卡斯定理", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.NUMBER_THEORY, MathDomain.COMBINATORICS]
            ),
            MathKnowledge(
                id="cross_conic_matrix", statement="x^T A x + b^T x + c = 0",
                statement_cn="圆锥曲线矩阵形式", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.ANALYTIC_GEOMETRY, MathDomain.LINEAR_ALGEBRA]
            ),
            MathKnowledge(
                id="cross_jacobian", statement="J_f = [∂f_i/∂x_j]",
                statement_cn="雅可比矩阵", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.CALCULUS, MathDomain.LINEAR_ALGEBRA]
            ),
            MathKnowledge(
                id="cross_covariance", statement="Cov(X) = E[(X-μ)(X-μ)^T]",
                statement_cn="协方差矩阵", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=3,
                related_domains=[MathDomain.PROBABILITY, MathDomain.LINEAR_ALGEBRA]
            ),
            MathKnowledge(
                id="cross_atiyah_singer", statement="ind(D) = ∫_M ch(σ(D)) td(TM⊗ℂ)",
                statement_cn="Atiyah-Singer 指标定理", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.ALGEBRAIC_TOPOLOGY, MathDomain.CALCULUS, MathDomain.GEOMETRY]
            ),
            MathKnowledge(
                id="cross_class_field_theory", statement="Gal(K^ab/K) ≅ C_K/K*",
                statement_cn="类域论基本定理", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.NUMBER_THEORY, MathDomain.FIELD_THEORY, MathDomain.GROUP_THEORY]
            ),
            MathKnowledge(
                id="cross_stone_duality", statement="Bool^op ≃ Stone (Stone 空间范畴)",
                statement_cn="Stone 对偶", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.ORDER_THEORY, MathDomain.TOPOLOGY, MathDomain.CATEGORY_THEORY]
            ),
            MathKnowledge(
                id="cross_riesz_representation", statement="C(X)* ≅ M(X) (测度空间)",
                statement_cn="Riesz 表示定理", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.TOPOLOGY, MathDomain.MEASURE_THEORY, MathDomain.CALCULUS]
            ),
            MathKnowledge(
                id="cross_peter_weyl", statement="紧群的不可约表示构成 L²(G) 的正交基",
                statement_cn="Peter-Weyl 定理", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=5,
                related_domains=[MathDomain.REPRESENTATION_THEORY, MathDomain.GROUP_THEORY, MathDomain.MEASURE_THEORY]
            ),
            MathKnowledge(
                id="cross_entropy_measure", statement="H(μ) = -∫ (dμ/dλ) log(dμ/dλ) dλ",
                statement_cn="测度论熵", domain=MathDomain.CROSS_DOMAIN,
                level=KnowledgeLevel.CORE, difficulty=4,
                related_domains=[MathDomain.INFORMATION_THEORY, MathDomain.MEASURE_THEORY, MathDomain.DYNAMICS]
            ),
        ]


# ============================================================================
# 统一知识库管理器
# ============================================================================

class UnifiedKnowledgeManager:
    """
    统一数学知识库管理器
    
    支持：
    1. 统一管理所有领域知识
    2. 跨领域知识查询
    3. 推导关系追踪
    4. 知识层级区分
    """
    
    # 所有领域知识类
    DOMAIN_KNOWLEDGE = {
        MathDomain.ALGEBRA: AlgebraKnowledge,
        MathDomain.TRIGONOMETRY: TrigonometryKnowledge,
        MathDomain.GEOMETRY: GeometryKnowledge,
        MathDomain.NUMBER_THEORY: NumberTheoryKnowledge,
        MathDomain.SOLID_GEOMETRY: SolidGeometryKnowledge,
        MathDomain.ANALYTIC_GEOMETRY: AnalyticGeometryKnowledge,
        MathDomain.COMBINATORICS: CombinatoricsKnowledge,
        MathDomain.PROBABILITY: ProbabilityKnowledge,
        MathDomain.CALCULUS: CalculusKnowledge,
        MathDomain.LINEAR_ALGEBRA: LinearAlgebraKnowledge,
        MathDomain.RING_THEORY: RingTheoryKnowledge,
        MathDomain.GROUP_THEORY: GroupTheoryKnowledge,
        MathDomain.FIELD_THEORY: FieldTheoryKnowledge,
        MathDomain.TOPOLOGY: TopologyKnowledge,
        MathDomain.MEASURE_THEORY: MeasureTheoryKnowledge,
        MathDomain.CATEGORY_THEORY: CategoryTheoryKnowledge,
        MathDomain.ORDER_THEORY: OrderTheoryKnowledge,
        MathDomain.SET_THEORY: SetTheoryKnowledge,
        MathDomain.LOGIC: LogicKnowledge,
        MathDomain.ALGEBRAIC_GEOMETRY: AlgebraicGeometryKnowledge,
        MathDomain.ALGEBRAIC_TOPOLOGY: AlgebraicTopologyKnowledge,
        MathDomain.REPRESENTATION_THEORY: RepresentationTheoryKnowledge,
        MathDomain.DYNAMICS: DynamicsKnowledge,
        MathDomain.INFORMATION_THEORY: InformationTheoryKnowledge,
        MathDomain.CROSS_DOMAIN: CrossDomainKnowledge,
    }
    
    def __init__(self, data_path: str = "data/unified_knowledge.json"):
        self.data_path = Path(data_path)
        self.knowledge: Dict[str, MathKnowledge] = {}
        
        # 索引
        self._by_domain: Dict[MathDomain, List[str]] = {}
        self._by_level: Dict[KnowledgeLevel, List[str]] = {}
        self._usable_in: Dict[MathDomain, List[str]] = {}  # 可在该领域使用的知识
        
        self._initialize()
    
    def _initialize(self):
        """初始化知识库"""
        if self.data_path.exists():
            self._load_from_file()
        else:
            self._load_builtin_knowledge()
        self._build_indices()
    
    def _load_builtin_knowledge(self):
        """加载内置知识"""
        for domain, knowledge_class in self.DOMAIN_KNOWLEDGE.items():
            # 公理
            if hasattr(knowledge_class, 'get_axioms'):
                for k in knowledge_class.get_axioms():
                    self.knowledge[k.id] = k
            # 定理
            if hasattr(knowledge_class, 'get_theorems'):
                for k in knowledge_class.get_theorems():
                    self.knowledge[k.id] = k
    
    def _load_from_file(self):
        """从文件加载"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for item in data.get("knowledge", []):
                k = MathKnowledge.from_dict(item)
                self.knowledge[k.id] = k
        except Exception as e:
            print(f"加载失败: {e}, 使用内置知识")
            self._load_builtin_knowledge()
    
    def _build_indices(self):
        """构建索引"""
        self._by_domain.clear()
        self._by_level.clear()
        self._usable_in.clear()
        
        for kid, k in self.knowledge.items():
            # 按领域
            if k.domain not in self._by_domain:
                self._by_domain[k.domain] = []
            self._by_domain[k.domain].append(kid)
            
            # 按层级
            if k.level not in self._by_level:
                self._by_level[k.level] = []
            self._by_level[k.level].append(kid)
            
            # 可使用的领域
            usable_domains = [k.domain] + list(k.can_use_in) + list(k.related_domains)
            for d in usable_domains:
                if d not in self._usable_in:
                    self._usable_in[d] = []
                if kid not in self._usable_in[d]:
                    self._usable_in[d].append(kid)
    
    def save(self):
        """保存知识库"""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "2.0.0",
            "knowledge": [k.to_dict() for k in self.knowledge.values()]
        }
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # ========== 查询方法 ==========
    
    def get(self, kid: str) -> Optional[MathKnowledge]:
        return self.knowledge.get(kid)
    
    def get_by_domain(self, domain: MathDomain, include_usable: bool = False) -> List[MathKnowledge]:
        """
        按领域获取知识
        
        参数：
            domain: 目标领域
            include_usable: 是否包含可在该领域使用的其他领域知识
        """
        if include_usable:
            kids = self._usable_in.get(domain, [])
        else:
            kids = self._by_domain.get(domain, [])
        return [self.knowledge[kid] for kid in kids]
    
    def get_by_level(self, level: KnowledgeLevel) -> List[MathKnowledge]:
        kids = self._by_level.get(level, [])
        return [self.knowledge[kid] for kid in kids]
    
    def get_fundamental(self) -> List[MathKnowledge]:
        """获取基础知识"""
        result = []
        result.extend(self.get_by_level(KnowledgeLevel.AXIOM))
        result.extend(self.get_by_level(KnowledgeLevel.DEFINITION))
        return result
    
    def get_core_theorems(self) -> List[MathKnowledge]:
        """获取核心定理"""
        return self.get_by_level(KnowledgeLevel.CORE)
    
    def get_usable_knowledge(self, domain: MathDomain) -> List[MathKnowledge]:
        """获取在指定领域可用的所有知识（包括跨领域）"""
        return self.get_by_domain(domain, include_usable=True)
    
    def get_related_domains(self, domain: MathDomain) -> List[MathDomain]:
        """获取与指定领域关联的其他领域"""
        return DOMAIN_CONNECTIONS.get(domain, [])
    
    def search(self, query: str) -> List[MathKnowledge]:
        """搜索知识"""
        query_lower = query.lower()
        return [
            k for k in self.knowledge.values()
            if query_lower in k.id.lower() or query in k.statement_cn
        ]
    
    # ========== 兼容旧接口 ==========
    
    def get_all_theorems(self, domain: MathDomain = None) -> Dict[str, MathTheorem]:
        """兼容旧接口"""
        if domain and domain in self.DOMAIN_KNOWLEDGE:
            return self.DOMAIN_KNOWLEDGE[domain].get_all_theorems()
        
        result = {}
        for domain_class in self.DOMAIN_KNOWLEDGE.values():
            if hasattr(domain_class, 'get_all_theorems'):
                result.update(domain_class.get_all_theorems())
        return result
    
    # ========== 添加知识 ==========
    
    def add(self, knowledge: MathKnowledge) -> bool:
        if knowledge.id in self.knowledge:
            return False
        self.knowledge[knowledge.id] = knowledge
        self._build_indices()
        return True
    
    def add_derived(self, kid: str, statement: str, statement_cn: str,
                    domain: MathDomain, dependencies: List[str],
                    difficulty: int = 3, verified: bool = False,
                    confidence: float = 0.5) -> MathKnowledge:
        """添加派生知识"""
        k = MathKnowledge(
            id=kid,
            statement=statement,
            statement_cn=statement_cn,
            domain=domain,
            level=KnowledgeLevel.DERIVED if verified else KnowledgeLevel.CONJECTURE,
            dependencies=dependencies,
            difficulty=difficulty,
            verified=verified,
            confidence=confidence
        )
        self.add(k)
        return k
    
    # ========== 统计 ==========
    
    def get_statistics(self) -> Dict:
        stats = {
            "total": len(self.knowledge),
            "by_level": {},
            "by_domain": {},
        }
        for level in KnowledgeLevel:
            count = len(self._by_level.get(level, []))
            if count > 0:
                stats["by_level"][level.value] = count
        for domain in MathDomain:
            count = len(self._by_domain.get(domain, []))
            if count > 0:
                stats["by_domain"][domain.value] = count
        return stats
    
    def print_summary(self):
        stats = self.get_statistics()
        print("=" * 60)
        print("          统一数学知识库")
        print("=" * 60)
        print(f"\n总知识数: {stats['total']}")
        
        print("\n按层级:")
        level_names = {"axiom": "公理", "definition": "定义", "core": "核心定理", 
                       "derived": "派生", "conjecture": "猜想"}
        for level, count in stats["by_level"].items():
            print(f"  {level_names.get(level, level)}: {count}")
        
        print("\n按领域:")
        for domain, count in stats["by_domain"].items():
            name = DOMAIN_NAMES.get(MathDomain(domain), domain)
            print(f"  {name}: {count}")


# ============================================================================
# 不完全归纳验证器
# ============================================================================

class InductiveVerifier:
    """通过数值验证计算置信度"""
    
    def __init__(self, sample_size: int = 1000):
        self.sample_size = sample_size
    
    def verify(self, knowledge: MathKnowledge, params: Dict = None) -> Tuple[float, int, Optional[str]]:
        domain = knowledge.domain
        statement = knowledge.statement_cn
        
        if domain == MathDomain.NUMBER_THEORY:
            return self._verify_number_theory(statement, params or {})
        elif domain in [MathDomain.ALGEBRA, MathDomain.LINEAR_ALGEBRA]:
            return self._verify_algebraic(statement, params or {})
        elif domain in [MathDomain.COMBINATORICS, MathDomain.PROBABILITY]:
            return self._verify_combinatorial(statement, params or {})
        return (0.5, 0, None)
    
    def _verify_number_theory(self, statement: str, params: Dict) -> Tuple[float, int, Optional[str]]:
        if "整除" in statement:
            return self._verify_divisibility(params)
        return (0.5, 0, None)
    
    def _verify_divisibility(self, params: Dict) -> Tuple[float, int, Optional[str]]:
        divisor = params.get('divisor', 6)
        expr_type = params.get('expr_type', 'n*(n+1)')
        passed, tested = 0, min(self.sample_size, 10000)
        
        for n in range(1, tested + 1):
            if expr_type == 'n*(n+1)':
                value = n * (n + 1)
            elif expr_type == 'n*(n+1)*(n+2)':
                value = n * (n + 1) * (n + 2)
            else:
                value = n * (n + 1)
            
            if value % divisor == 0:
                passed += 1
            else:
                return (passed / tested, tested, f"n={n}")
        
        return (min(0.99, passed / tested), tested, None)
    
    def _verify_algebraic(self, statement: str, params: Dict) -> Tuple[float, int, Optional[str]]:
        passed, tested = 0, self.sample_size
        for _ in range(tested):
            a, b = random.uniform(-100, 100), random.uniform(-100, 100)
            if a**2 + b**2 >= 0:
                passed += 1
        return (min(0.99, passed / tested), tested, None)
    
    def _verify_combinatorial(self, statement: str, params: Dict) -> Tuple[float, int, Optional[str]]:
        if "帕斯卡" in statement:
            passed, count = 0, 0
            for n in range(1, 50):
                for k in range(n):
                    if math.comb(n, k) + math.comb(n, k+1) == math.comb(n+1, k+1):
                        passed += 1
                    count += 1
            return (min(0.99, passed / count), count, None)
        return (0.5, 0, None)


# ============================================================================
# 工具函数
# ============================================================================

def get_unified_manager() -> UnifiedKnowledgeManager:
    """获取单例"""
    if not hasattr(get_unified_manager, '_instance'):
        get_unified_manager._instance = UnifiedKnowledgeManager()
    return get_unified_manager._instance


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    manager = UnifiedKnowledgeManager()
    manager.print_summary()
    
    print("\n跨领域知识利用示例:")
    print("-" * 40)
    
    # 代数领域可用的所有知识
    algebra_usable = manager.get_usable_knowledge(MathDomain.ALGEBRA)
    print(f"\n代数领域可用知识: {len(algebra_usable)} 条")
    
    # 显示来自其他领域的可用知识
    other_domain = [k for k in algebra_usable if k.domain != MathDomain.ALGEBRA]
    print(f"  其中来自其他领域: {len(other_domain)} 条")
    for k in other_domain[:3]:
        print(f"    - [{DOMAIN_NAMES[k.domain]}] {k.statement_cn}")
    
    manager.save()
    print(f"\n✓ 已保存到 {manager.data_path}")
