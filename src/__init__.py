"""
═══════════════════════════════════════════════════════════════════════════════
                    Gauss - 数学家智能体
        Mathematical AI Agent with Lean 4 & Mathlib Formal Verification
═══════════════════════════════════════════════════════════════════════════════

Gauss 是一个结合大语言模型（LLM）与 Lean 4 + Mathlib 形式化验证的数学研究智能体，
能够处理 Lean 与 Mathlib 所覆盖的所有数学分支。
Gauss is an AI-powered mathematical research agent combining LLMs with
Lean 4 + Mathlib formal verification, capable of handling all branches
of mathematics covered by Lean and Mathlib.

核心功能 (Core Features):
    - 猜想生成 (Conjecture Generation):
        基于多步推理链 (Chain-of-Thought) 从已有知识推导新猜想
    - 自动证明 (Automated Proving):
        多策略组合证明引擎，支持 Mathlib 库中的 tactics
    - 知识图谱 (Knowledge Graph):
        追踪定理间的推导关系，支持路径查询与可视化
    - 经验学习 (Experience Learning):
        从成功的证明中学习模式，智能去重与策略推荐
    - 全数学覆盖 (Full Math Coverage):
        处理 Lean 4 与 Mathlib 所支持的所有数学分支

快速开始 (Quick Start):
    >>> from src import ContinuousLearningAgent
    >>> agent = ContinuousLearningAgent()
    >>> agent.run_learning_round(domain="algebra")

    >>> from src import UnifiedKnowledgeManager, MathDomain
    >>> km = UnifiedKnowledgeManager()
    >>> km.print_summary()

作者 (Author): Jiangsheng Yu
版本 (Version): 3.0.0
"""

__version__ = "3.0.0"
__author__ = "Jiangsheng Yu"

# ═══════════════════════════════════════════════════════════════════════════
# 核心模块
# ═══════════════════════════════════════════════════════════════════════════

# 持续学习智能体（核心入口）
from .learning_agent import (
    ContinuousLearningAgent,
    DerivationResult,
    ALL_DOMAINS,
    # 多步推理
    ChainOfThoughtReasoner,
    ReasoningChain,
    ReasoningStep
)

# 知识图谱
from .knowledge_graph import (
    KnowledgeGraph,
    KnowledgeNode,
    NodeType,
    NodeStatus
)

# 经验学习
from .experience_learner import (
    ExperienceLearner,
    ProofExperience,
    TacticPattern
)

# Lean 环境
from .lean_env import (
    LeanEnvironment,
    ProofState,
    TacticResult,
    create_lean_env
)

# LLM Agent
from .llm_agent import (
    BaseLLMAgent,
    OllamaAgent,
    QwenAgent,
    MockLLMAgent,
    create_llm_agent
)

# 统一知识库（合并了 math_knowledge 和 extended_knowledge）
from .unified_knowledge import (
    # 枚举
    MathDomain,
    KnowledgeLevel,
    
    # 知识表示
    MathKnowledge,
    MathTheorem,
    ConjecturePattern,
    DomainKnowledge,
    
    # 领域知识类
    AlgebraKnowledge,
    TrigonometryKnowledge,
    GeometryKnowledge,
    NumberTheoryKnowledge,
    SolidGeometryKnowledge,
    AnalyticGeometryKnowledge,
    CombinatoricsKnowledge,
    ProbabilityKnowledge,
    CalculusKnowledge,
    LinearAlgebraKnowledge,
    RingTheoryKnowledge,
    GroupTheoryKnowledge,
    FieldTheoryKnowledge,
    TopologyKnowledge,
    MeasureTheoryKnowledge,
    CategoryTheoryKnowledge,
    OrderTheoryKnowledge,
    SetTheoryKnowledge,
    LogicKnowledge,
    AlgebraicGeometryKnowledge,
    AlgebraicTopologyKnowledge,
    RepresentationTheoryKnowledge,
    DynamicsKnowledge,
    InformationTheoryKnowledge,
    CrossDomainKnowledge,
    
    # 管理器
    UnifiedKnowledgeManager,
    
    # 验证器
    InductiveVerifier,
    
    # 工具函数
    get_unified_manager,
    DOMAIN_NAMES,
    DOMAIN_CONNECTIONS
)

# 工具函数
from .utils import (
    load_config,
    save_config,
    setup_logging
)

# ═══════════════════════════════════════════════════════════════════════════
# 导出列表
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # 版本
    "__version__",
    "__author__",
    
    # 核心
    "ContinuousLearningAgent",
    "DerivationResult",
    "ALL_DOMAINS",
    "ChainOfThoughtReasoner",
    "ReasoningChain",
    "ReasoningStep",
    
    # 知识图谱
    "KnowledgeGraph",
    "KnowledgeNode",
    "NodeType",
    "NodeStatus",
    
    # 经验学习
    "ExperienceLearner",
    "ProofExperience",
    "TacticPattern",
    
    # Lean 环境
    "LeanEnvironment",
    "ProofState",
    "TacticResult",
    "create_lean_env",
    
    # LLM
    "BaseLLMAgent",
    "OllamaAgent",
    "QwenAgent",
    "MockLLMAgent",
    "create_llm_agent",
    
    # 统一知识库
    "MathDomain",
    "KnowledgeLevel",
    "MathKnowledge",
    "MathTheorem",
    "ConjecturePattern",
    "DomainKnowledge",
    "AlgebraKnowledge",
    "TrigonometryKnowledge",
    "GeometryKnowledge",
    "NumberTheoryKnowledge",
    "SolidGeometryKnowledge",
    "AnalyticGeometryKnowledge",
    "CombinatoricsKnowledge",
    "ProbabilityKnowledge",
    "CalculusKnowledge",
    "LinearAlgebraKnowledge",
    "RingTheoryKnowledge",
    "GroupTheoryKnowledge",
    "FieldTheoryKnowledge",
    "TopologyKnowledge",
    "MeasureTheoryKnowledge",
    "CategoryTheoryKnowledge",
    "OrderTheoryKnowledge",
    "SetTheoryKnowledge",
    "LogicKnowledge",
    "AlgebraicGeometryKnowledge",
    "AlgebraicTopologyKnowledge",
    "RepresentationTheoryKnowledge",
    "DynamicsKnowledge",
    "InformationTheoryKnowledge",
    "CrossDomainKnowledge",
    "UnifiedKnowledgeManager",
    "InductiveVerifier",
    "get_unified_manager",
    "DOMAIN_NAMES",
    "DOMAIN_CONNECTIONS",
    
    # 工具
    "load_config",
    "save_config",
    "setup_logging",
]
