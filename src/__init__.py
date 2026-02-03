"""
═══════════════════════════════════════════════════════════════════════════════
                    Lean Agent - 数学家智能体
═══════════════════════════════════════════════════════════════════════════════

一个结合大语言模型与 Lean 4 形式化验证的数学研究智能体。

核心功能：
- 猜想生成：基于多步推理从已有知识推导新猜想
- 自动证明：多策略组合证明引擎
- 知识图谱：追踪定理推导关系
- 经验学习：从成功中学习优化策略
- 跨领域推理：连接不同数学分支

知识层级：
- 基础知识：公理 (Axiom) + 定义 (Definition)
- 核心定理：经典、已验证的重要定理 (Core)
- 派生定理：从其他定理推导出来 (Derived)
- 猜想：待证明的命题 (Conjecture)

支持领域：
- 代数、三角函数、平面几何（基础）
- 初等数论、立体几何、解析几何
- 组合计数、概率统计、微积分、线性代数
- 跨领域推理

快速开始：
    >>> from src import ContinuousLearningAgent
    >>> agent = ContinuousLearningAgent()
    >>> agent.run_learning_round(domain="algebra")

作者: Jiangsheng Yu
版本: 2.1.0
"""

__version__ = "2.1.0"
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
    "QwenAgent",
    "MockLLMAgent",
    "create_llm_agent",
    
    # 统一知识库
    "MathDomain",
    "KnowledgeLevel",
    "MathKnowledge",
    "MathTheorem",
    "ConjecturePattern",
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
