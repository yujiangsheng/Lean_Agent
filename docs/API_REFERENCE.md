# 📖 API 参考手册

> Lean Agent 完整 API 文档

---

## 📋 目录

- [快速导入](#快速导入)
- [ContinuousLearningAgent](#continuouslearningagent)
- [UnifiedKnowledgeManager](#unifiedknowledgemanager)
- [KnowledgeGraph](#knowledgegraph)
- [ExperienceLearner](#experiencelearner)
- [LeanEnvironment](#leanenvironment)
- [LLMAgent](#llmagent)
- [数据类](#数据类)
- [枚举类型](#枚举类型)

---

## 快速导入

```python
from src import (
    # 核心智能体
    ContinuousLearningAgent,
    
    # 知识管理
    UnifiedKnowledgeManager,
    MathKnowledge,
    MathDomain,
    KnowledgeLevel,
    DOMAIN_NAMES,
    
    # 知识图谱
    KnowledgeGraph,
    KnowledgeNode,
    NodeType,
    NodeStatus,
    
    # 经验学习
    ExperienceLearner,
    ProofExperience,
    TacticPattern,
    
    # Lean 环境
    LeanEnvironment,
    ProofState,
    TacticResult,
    create_lean_env,
    
    # LLM
    BaseLLMAgent,
    QwenAgent,
    MockLLMAgent,
    create_llm_agent,
    
    # 多步推理
    ChainOfThoughtReasoner,
    ReasoningChain,
    ReasoningStep,
    
    # 版本信息
    __version__,
    __author__,
)
```

---

## ContinuousLearningAgent

### 类签名

```python
class ContinuousLearningAgent:
    """
    持续学习智能体
    
    整合知识图谱、经验学习、猜想生成和证明引擎，
    从已有知识出发推导新的非平凡定理。
    """
```

### 构造函数

```python
def __init__(
    self,
    data_dir: str = "data",
    verbose: bool = True
) -> None:
    """
    初始化持续学习智能体
    
    参数:
        data_dir: 数据目录路径，用于存储知识图谱和经验库
        verbose: 是否输出详细日志
    
    示例:
        >>> agent = ContinuousLearningAgent()
        >>> agent = ContinuousLearningAgent(data_dir="my_data", verbose=False)
    """
```

### 核心方法

#### run_learning_round

```python
def run_learning_round(
    self,
    domain: str = None
) -> Dict[str, Any]:
    """
    执行一轮学习
    
    参数:
        domain: 指定学习领域，可选值:
            - "algebra": 代数
            - "trigonometry": 三角函数
            - "geometry": 平面几何
            - "number_theory": 数论
            - "solid_geometry": 立体几何
            - "analytic_geometry": 解析几何
            - "combinatorics": 组合计数
            - "probability": 概率统计
            - "calculus": 微积分
            - "linear_algebra": 线性代数
            - "cross_domain": 跨领域
            - None: 随机选择（默认）
    
    返回:
        Dict 包含:
            - success: bool - 是否成功
            - domain: str - 实际学习的领域
            - conjecture: str - 生成的猜想
            - proved: bool - 是否证明成功
            - reasoning_chain: List[Dict] - 推理链
    
    示例:
        >>> result = agent.run_learning_round(domain="algebra")
        >>> print(f"成功: {result['success']}")
    """
```

#### run_learning_loop

```python
def run_learning_loop(
    self,
    rounds: int = None,
    minutes: float = None,
    domain: str = None
) -> Dict[str, Any]:
    """
    执行多轮学习
    
    参数:
        rounds: 学习轮数（与 minutes 二选一）
        minutes: 学习时间（分钟）
        domain: 指定领域，None 表示随机
    
    返回:
        Dict 包含学习统计信息
    
    示例:
        >>> # 学习 10 轮
        >>> agent.run_learning_loop(rounds=10)
        >>> 
        >>> # 学习 30 分钟
        >>> agent.run_learning_loop(minutes=30)
        >>> 
        >>> # 在代数领域学习 5 轮
        >>> agent.run_learning_loop(rounds=5, domain="algebra")
    """
```

### 属性

```python
# 统计信息
agent.stats: Dict[str, int]
# {
#     'total_rounds': 100,
#     'total_conjectures': 95,
#     'total_proved': 80,
#     'total_failed': 15,
# }

# 知识图谱
agent.knowledge_graph: KnowledgeGraph

# 经验学习器
agent.experience_learner: ExperienceLearner

# 知识管理器
agent.knowledge_manager: UnifiedKnowledgeManager
```

---

## UnifiedKnowledgeManager

### 类签名

```python
class UnifiedKnowledgeManager:
    """
    统一知识库管理器
    
    管理 11 个数学领域的知识，提供查询、检索、过滤功能。
    """
```

### 构造函数

```python
def __init__(self) -> None:
    """
    初始化知识库管理器
    
    自动加载所有内置知识（67 条）
    
    示例:
        >>> km = UnifiedKnowledgeManager()
        >>> km.print_summary()
    """
```

### 查询方法

#### get_by_domain

```python
def get_by_domain(
    self,
    domain: MathDomain
) -> List[MathKnowledge]:
    """
    按领域获取知识
    
    参数:
        domain: MathDomain 枚举值
    
    返回:
        该领域的所有知识列表
    
    示例:
        >>> algebra = km.get_by_domain(MathDomain.ALGEBRA)
        >>> print(f"代数领域: {len(algebra)} 条")
    """
```

#### get_by_level

```python
def get_by_level(
    self,
    level: KnowledgeLevel
) -> List[MathKnowledge]:
    """
    按层级获取知识
    
    参数:
        level: KnowledgeLevel 枚举值
    
    返回:
        该层级的所有知识列表
    
    示例:
        >>> axioms = km.get_by_level(KnowledgeLevel.AXIOM)
        >>> print(f"公理: {len(axioms)} 条")
    """
```

#### get_by_id

```python
def get_by_id(
    self,
    id: str
) -> Optional[MathKnowledge]:
    """
    按 ID 获取知识
    
    参数:
        id: 知识唯一标识符
    
    返回:
        MathKnowledge 对象或 None
    
    示例:
        >>> thm = km.get_by_id("thm_pythagorean")
        >>> print(thm.statement_cn)  # 勾股定理
    """
```

#### search

```python
def search(
    self,
    keyword: str
) -> List[MathKnowledge]:
    """
    关键词搜索
    
    参数:
        keyword: 搜索关键词（匹配 ID、陈述、中文描述）
    
    返回:
        匹配的知识列表
    
    示例:
        >>> results = km.search("交换")
        >>> for r in results:
        ...     print(f"- {r.id}: {r.statement_cn}")
    """
```

#### get_cross_domain_knowledge

```python
def get_cross_domain_knowledge(
    self,
    domain: MathDomain,
    include_related: bool = True
) -> List[MathKnowledge]:
    """
    获取跨领域可用的知识
    
    参数:
        domain: 目标领域
        include_related: 是否包含相关领域的知识
    
    返回:
        可在目标领域使用的知识列表
    
    示例:
        >>> cross = km.get_cross_domain_knowledge(
        ...     MathDomain.GEOMETRY,
        ...     include_related=True
        ... )
    """
```

### 实用方法

```python
# 打印统计摘要
km.print_summary()

# 获取所有知识
all_knowledge = km.all_knowledge  # List[MathKnowledge]

# 获取领域名称
name = km.get_domain_name(MathDomain.ALGEBRA)  # "代数"
```

---

## KnowledgeGraph

### 类签名

```python
class KnowledgeGraph:
    """
    数学知识图谱
    
    管理定理之间的推导关系，支持图查询和持久化。
    """
```

### 构造函数

```python
def __init__(
    self,
    data_path: str = "data/knowledge_graph.json"
) -> None:
    """
    初始化知识图谱
    
    参数:
        data_path: 数据文件路径
    
    示例:
        >>> kg = KnowledgeGraph()
        >>> kg = KnowledgeGraph(data_path="my_data/kg.json")
    """
```

### 节点操作

```python
# 添加节点
kg.add_node(node: KnowledgeNode) -> None

# 获取节点
node = kg.get_node(node_id: str) -> Optional[KnowledgeNode]

# 删除节点
kg.remove_node(node_id: str) -> bool

# 更新节点
kg.update_node(node_id: str, **kwargs) -> bool
```

### 边操作

```python
# 添加推导边 (A → B 表示 A 用于证明 B)
kg.add_edge(from_id: str, to_id: str) -> None

# 获取前驱（哪些定理用于证明此定理）
predecessors = kg.get_predecessors(node_id: str) -> List[str]

# 获取后继（此定理用于证明哪些定理）
successors = kg.get_successors(node_id: str) -> List[str]
```

### 图查询

```python
# 获取所有节点
nodes = kg.nodes  # Dict[str, KnowledgeNode]

# 获取所有边
edges = kg.edges  # List[Tuple[str, str]]

# 统计信息
print(f"节点数: {len(kg.nodes)}")
print(f"边数: {len(kg.edges)}")
```

### 持久化

```python
# 保存到文件
kg.save()

# 从文件加载（构造时自动调用）
kg.load()
```

---

## ExperienceLearner

### 类签名

```python
class ExperienceLearner:
    """
    经验学习系统
    
    从成功的证明中学习模式，优化策略推荐。
    """
```

### 构造函数

```python
def __init__(
    self,
    data_path: str = "data/experience.json"
) -> None:
    """
    初始化经验学习器
    
    参数:
        data_path: 经验数据文件路径
    """
```

### 核心方法

```python
# 添加证明经验
def add_experience(self, exp: ProofExperience) -> None:
    """记录一次证明经验"""

# 推荐策略
def recommend_tactics(
    self,
    statement: str,
    domain: str,
    k: int = 5
) -> List[str]:
    """
    基于经验推荐证明策略
    
    参数:
        statement: 待证明的陈述
        domain: 领域
        k: 返回策略数量
    
    返回:
        推荐的策略列表
    """

# 获取领域统计
def get_domain_stats(self) -> Dict[str, Dict]:
    """返回各领域的证明统计"""

# 获取常用模式
def get_common_patterns(self, min_count: int = 3) -> List[TacticPattern]:
    """返回常用的证明模式"""
```

---

## LeanEnvironment

### 类签名

```python
class LeanEnvironment:
    """
    Lean 4 环境交互
    
    提供与 Lean 4 证明器的交互接口。
    """
```

### 工厂函数

```python
def create_lean_env(use_mock: bool = True) -> LeanEnvironment:
    """
    创建 Lean 环境
    
    参数:
        use_mock: 是否使用模拟环境（无需真实 Lean 安装）
    
    返回:
        LeanEnvironment 实例
    
    示例:
        >>> env = create_lean_env()
        >>> env = create_lean_env(use_mock=False)  # 需要 Lean 4
    """
```

### 核心方法

```python
# 初始化证明
def initialize_proof(self, theorem: str) -> ProofState:
    """
    初始化定理证明
    
    参数:
        theorem: Lean 4 定理陈述
    
    返回:
        初始证明状态
    """

# 应用策略
def apply_tactic(
    self,
    state: ProofState,
    tactic: str
) -> TacticResult:
    """
    应用证明策略
    
    参数:
        state: 当前证明状态
        tactic: 策略名称（如 "intro", "simp", "ring"）
    
    返回:
        TacticResult 包含成功标志和新状态
    """

# 语法检查
def syntax_check(self, statement: str) -> bool:
    """检查 Lean 语法是否正确"""

# 获取可用引理
def get_available_lemmas(
    self,
    state: ProofState,
    k: int = 5
) -> List[str]:
    """推荐可能有用的引理"""

# 关闭环境
def close(self) -> None:
    """释放资源"""
```

---

## LLMAgent

### 类签名

```python
class BaseLLMAgent:
    """LLM 代理基类"""

class QwenAgent(BaseLLMAgent):
    """Qwen 模型代理"""

class MockLLMAgent(BaseLLMAgent):
    """模拟 LLM（用于测试）"""
```

### 工厂函数

```python
def create_llm_agent(
    model_name: str = None,
    use_mock: bool = True
) -> BaseLLMAgent:
    """
    创建 LLM 代理
    
    参数:
        model_name: 模型名称
        use_mock: 是否使用模拟
    
    返回:
        LLM 代理实例
    """
```

### 核心方法

```python
# 建议策略
def suggest_tactics(
    self,
    proof_state: str,
    num_suggestions: int = 5
) -> List[str]:
    """
    基于当前证明状态建议策略
    
    参数:
        proof_state: 当前证明状态（字符串）
        num_suggestions: 建议数量
    
    返回:
        策略列表
    """

# 生成猜想
def generate_conjecture(
    self,
    premises: List[str],
    domain: str
) -> str:
    """
    基于前提生成猜想
    
    参数:
        premises: 前提列表
        domain: 数学领域
    
    返回:
        生成的猜想陈述
    """
```

---

## 数据类

### MathKnowledge

```python
@dataclass
class MathKnowledge:
    id: str                    # 唯一标识符
    statement: str             # 形式化陈述
    statement_cn: str          # 中文描述
    domain: MathDomain         # 所属领域
    level: KnowledgeLevel      # 知识层级
    dependencies: List[str]    # 依赖的知识 ID
    difficulty: int            # 难度 (1-5)
    verified: bool             # 是否已验证
    confidence: float          # 置信度 (0-1)
```

### KnowledgeNode

```python
@dataclass
class KnowledgeNode:
    id: str                    # 唯一标识符
    statement: str             # 形式化陈述
    statement_cn: str          # 中文描述
    domain: str                # 所属领域
    node_type: NodeType        # 节点类型
    status: NodeStatus         # 状态
    difficulty: int            # 难度
    confidence: float          # 置信度
    proof_steps: int           # 证明步数
    created_at: str            # 创建时间
```

### ProofExperience

```python
@dataclass
class ProofExperience:
    conjecture_id: str         # 猜想 ID
    statement: str             # 形式化陈述
    statement_cn: str          # 中文描述
    domain: str                # 领域
    tactics_used: List[str]    # 使用的策略
    proof_time_ms: float       # 证明耗时
    proof_steps: int           # 步数
    success: bool              # 是否成功
```

### ProofState

```python
@dataclass
class ProofState:
    goals: List[str]           # 待证目标
    is_finished: bool          # 是否完成
    hypotheses: List[str]      # 假设列表
```

### TacticResult

```python
@dataclass
class TacticResult:
    success: bool              # 是否成功
    new_state: ProofState      # 新状态
    error_message: str         # 错误信息（如果失败）
```

---

## 枚举类型

### MathDomain

```python
class MathDomain(Enum):
    NAT = "nat"
    ALGEBRA = "algebra"
    TRIGONOMETRY = "trigonometry"
    GEOMETRY = "geometry"
    NUMBER_THEORY = "number_theory"
    SOLID_GEOMETRY = "solid_geometry"
    ANALYTIC_GEOMETRY = "analytic_geometry"
    COMBINATORICS = "combinatorics"
    PROBABILITY = "probability"
    CALCULUS = "calculus"
    LINEAR_ALGEBRA = "linear_algebra"
    CROSS_DOMAIN = "cross_domain"
```

### KnowledgeLevel

```python
class KnowledgeLevel(Enum):
    AXIOM = "axiom"           # 公理
    DEFINITION = "definition" # 定义
    CORE = "core"             # 核心定理
    DERIVED = "derived"       # 派生定理
    CONJECTURE = "conjecture" # 猜想
```

### NodeType

```python
class NodeType(Enum):
    AXIOM = "axiom"           # 公理
    THEOREM = "theorem"       # 定理
    LEMMA = "lemma"           # 引理
    CONJECTURE = "conjecture" # 猜想
    DERIVED = "derived"       # 派生
```

### NodeStatus

```python
class NodeStatus(Enum):
    VERIFIED = "verified"     # 已验证
    PENDING = "pending"       # 待验证
    FAILED = "failed"         # 验证失败
    ASSUMED = "assumed"       # 假设为真
    CONJECTURED = "conjectured"  # 合情推理
```

---

**作者**: Jiangsheng Yu  
**版本**: 2.1.0  
**更新日期**: 2024
