# 📚 知识系统详解

> Lean Agent 统一知识库与推理系统的完整文档

---

## 📋 目录

- [知识表示](#知识表示)
- [知识层级](#知识层级)
- [数学领域](#数学领域)
- [跨领域推理](#跨领域推理)
- [验证机制](#验证机制)
- [查询接口](#查询接口)

---

## 知识表示

### MathKnowledge 数据类

每条数学知识都用 `MathKnowledge` 数据类表示：

```python
@dataclass
class MathKnowledge:
    """统一的数学知识表示"""
    
    # 基本信息
    id: str                    # 唯一标识符，如 "axiom_add_comm"
    statement: str             # 形式化陈述（Lean 4 语法）
    statement_cn: str          # 中文描述
    domain: MathDomain         # 所属领域
    level: KnowledgeLevel      # 知识层级
    
    # 推导关系
    dependencies: List[str]    # 依赖的其他知识 ID
    derived_from: str          # 推导来源
    
    # 跨领域支持
    related_domains: List[MathDomain]  # 关联领域
    can_use_in: List[MathDomain]       # 可应用领域
    
    # 元数据
    difficulty: int            # 难度 (1-5)
    symbols: Set[str]          # 涉及的符号
    tactics: List[str]         # 推荐的证明策略
    
    # 验证状态
    verified: bool             # 是否已验证
    confidence: float          # 置信度 (0-1)
```

### 示例

```python
# 加法交换律（公理）
add_comm = MathKnowledge(
    id="axiom_add_comm",
    statement="∀ a b : ℝ, a + b = b + a",
    statement_cn="加法交换律：两数相加，交换顺序结果不变",
    domain=MathDomain.ALGEBRA,
    level=KnowledgeLevel.AXIOM,
    difficulty=1,
    symbols={"a", "b", "+"},
    verified=True,
    confidence=1.0
)

# 勾股定理（核心定理）
pythagorean = MathKnowledge(
    id="thm_pythagorean",
    statement="∀ a b c : ℝ, right_triangle a b c → a² + b² = c²",
    statement_cn="勾股定理：直角三角形两直角边平方和等于斜边平方",
    domain=MathDomain.GEOMETRY,
    level=KnowledgeLevel.CORE,
    difficulty=3,
    related_domains=[MathDomain.ALGEBRA, MathDomain.TRIGONOMETRY],
    tactics=["rfl", "ring", "linarith"]
)
```

---

## 知识层级

### 层级金字塔

```
                    ┌─────────────┐
                    │   猜想       │  ← 待证明（学习中生成）
                    │ CONJECTURE  │
                ┌───┴─────────────┴───┐
                │      派生定理        │  ← 从已有知识推导
                │      DERIVED        │
            ┌───┴───────────────────┴───┐
            │          核心定理          │  ← 经典重要定理
            │           CORE            │
        ┌───┴───────────────────────────┴───┐
        │            定义 DEFINITION          │  ← 概念定义
    ┌───┴───────────────────────────────────┴───┐
    │               公理 AXIOM                    │  ← 基础事实
    └───────────────────────────────────────────┘
```

### 层级说明

| 层级 | 枚举值 | 说明 | 数量 |
|------|--------|------|------|
| **公理** | `AXIOM` | 不证自明的基础事实，无需证明 | 21 |
| **定义** | `DEFINITION` | 数学概念的精确描述 | 9 |
| **核心** | `CORE` | 经典、已验证的重要定理 | 37 |
| **派生** | `DERIVED` | 从其他知识推导出来 | 动态增长 |
| **猜想** | `CONJECTURE` | 待证明的命题 | 动态增长 |

### 判断方法

```python
knowledge = km.get_by_id("axiom_add_comm")

# 判断是否为基础知识
knowledge.is_fundamental()  # True (公理或定义)

# 判断层级
knowledge.level == KnowledgeLevel.AXIOM  # True
```

---

## 数学领域

### 领域枚举

```python
class MathDomain(Enum):
    """数学领域"""
    
    # 基础领域
    NAT = "nat"                    # 自然数
    ALGEBRA = "algebra"            # 代数
    TRIGONOMETRY = "trigonometry"  # 三角函数
    GEOMETRY = "geometry"          # 平面几何
    
    # 扩展领域
    NUMBER_THEORY = "number_theory"          # 初等数论
    SOLID_GEOMETRY = "solid_geometry"        # 立体几何
    ANALYTIC_GEOMETRY = "analytic_geometry"  # 解析几何
    COMBINATORICS = "combinatorics"          # 组合计数
    PROBABILITY = "probability"              # 概率统计
    CALCULUS = "calculus"                    # 微积分
    LINEAR_ALGEBRA = "linear_algebra"        # 线性代数
    
    # 跨领域
    CROSS_DOMAIN = "cross_domain"            # 跨领域
```

### 领域中文名

```python
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
    MathDomain.CROSS_DOMAIN: "跨领域",
}
```

### 各领域内置知识

| 领域 | 公理 | 定义 | 核心 | 合计 |
|------|------|------|------|------|
| 代数 | 5 | 0 | 6 | 11 |
| 三角函数 | 3 | 0 | 8 | 11 |
| 平面几何 | 3 | 2 | 5 | 10 |
| 数论 | 2 | 2 | 3 | 7 |
| 立体几何 | 0 | 0 | 4 | 4 |
| 解析几何 | 0 | 0 | 4 | 4 |
| 组合计数 | 2 | 0 | 4 | 6 |
| 概率统计 | 1 | 2 | 3 | 6 |
| 微积分 | 2 | 0 | 3 | 5 |
| 线性代数 | 1 | 1 | 2 | 4 |

---

## 跨领域推理

### 领域关联图

```
                    ┌─────────────┐
                    │   代数      │
                    │  ALGEBRA    │
                    └─────────────┘
                   ↙      ↓      ↘
         ┌─────────┐  ┌─────────┐  ┌─────────┐
         │  数论   │  │ 线代    │  │ 微积分  │
         └─────────┘  └─────────┘  └─────────┘
              ↓            ↓            ↓
         ┌─────────┐  ┌─────────┐  ┌─────────┐
         │  组合   │  │ 解析几何│  │ 三角函数│
         └─────────┘  └─────────┘  └─────────┘
              ↓            ↓            ↓
         ┌─────────┐  ┌─────────────────────┐
         │  概率   │  │    平面/立体几何     │
         └─────────┘  └─────────────────────┘
```

### 领域连接配置

```python
DOMAIN_CONNECTIONS = {
    MathDomain.ALGEBRA: [
        MathDomain.NUMBER_THEORY, 
        MathDomain.LINEAR_ALGEBRA, 
        MathDomain.CALCULUS
    ],
    MathDomain.TRIGONOMETRY: [
        MathDomain.GEOMETRY, 
        MathDomain.CALCULUS, 
        MathDomain.ANALYTIC_GEOMETRY
    ],
    MathDomain.GEOMETRY: [
        MathDomain.TRIGONOMETRY, 
        MathDomain.SOLID_GEOMETRY, 
        MathDomain.ANALYTIC_GEOMETRY
    ],
    # ...
}
```

### 跨领域推理示例

```python
# 勾股定理可以在多个领域使用
pythagorean = km.get_by_id("thm_pythagorean")

# 检查是否可在某领域使用
pythagorean.is_usable_in(MathDomain.ALGEBRA)      # True (related)
pythagorean.is_usable_in(MathDomain.TRIGONOMETRY) # True (related)
pythagorean.is_usable_in(MathDomain.CROSS_DOMAIN) # True (always)
```

---

## 验证机制

### 置信度系统

对于无法形式化证明的猜想，系统采用**不完全归纳验证**：

```python
class InductiveVerifier:
    """归纳验证器"""
    
    def verify_numerical(
        self, 
        statement: str, 
        samples: int = 1000
    ) -> Tuple[bool, float]:
        """
        数值验证
        
        返回:
            (是否通过, 置信度)
        """
        pass
```

### 置信度计算

```
置信度 = 1 - (1 / (验证样本数 + 1))

例如:
- 100 次验证通过 → 置信度 = 0.99
- 1000 次验证通过 → 置信度 = 0.999
- 发现反例 → 置信度 = 0
```

### 节点状态

```python
class NodeStatus(Enum):
    """节点状态"""
    VERIFIED = "verified"       # 已验证（严格证明）
    PENDING = "pending"         # 待验证
    FAILED = "failed"           # 验证失败
    ASSUMED = "assumed"         # 假设为真（公理）
    CONJECTURED = "conjectured" # 合情推理（有置信度但未严格证明）
```

---

## 查询接口

### UnifiedKnowledgeManager API

```python
from src import UnifiedKnowledgeManager, MathDomain, KnowledgeLevel

# 初始化
km = UnifiedKnowledgeManager()

# 1. 查看摘要
km.print_summary()

# 2. 按领域查询
algebra = km.get_by_domain(MathDomain.ALGEBRA)
print(f"代数领域: {len(algebra)} 条")

# 3. 按层级查询
axioms = km.get_by_level(KnowledgeLevel.AXIOM)
print(f"公理: {len(axioms)} 条")

# 4. 按 ID 查询
thm = km.get_by_id("axiom_add_comm")
print(thm.statement_cn)

# 5. 关键词搜索
results = km.search("交换")
for r in results:
    print(f"- {r.id}: {r.statement_cn}")

# 6. 获取跨领域知识
cross = km.get_cross_domain_knowledge(
    domain=MathDomain.GEOMETRY,
    include_related=True
)
```

### 常用查询示例

```python
# 获取某领域的公理
def get_domain_axioms(domain: MathDomain) -> List[MathKnowledge]:
    km = UnifiedKnowledgeManager()
    return [
        k for k in km.get_by_domain(domain)
        if k.level == KnowledgeLevel.AXIOM
    ]

# 获取高难度定理
def get_hard_theorems(min_difficulty: int = 4) -> List[MathKnowledge]:
    km = UnifiedKnowledgeManager()
    return [
        k for k in km.all_knowledge
        if k.difficulty >= min_difficulty
    ]

# 获取含有特定符号的知识
def get_by_symbol(symbol: str) -> List[MathKnowledge]:
    km = UnifiedKnowledgeManager()
    return [
        k for k in km.all_knowledge
        if symbol in k.symbols
    ]
```

---

## 内置知识摘要

### 代数领域 (ALGEBRA)

**公理**:
- `axiom_add_comm`: 加法交换律
- `axiom_mul_comm`: 乘法交换律
- `axiom_add_assoc`: 加法结合律
- `axiom_mul_assoc`: 乘法结合律
- `axiom_distributive`: 分配律

**核心定理**:
- `thm_am_gm`: AM-GM 不等式
- `thm_cauchy_schwarz`: Cauchy-Schwarz 不等式
- `thm_power_mean`: 幂平均不等式
- `thm_schur`: Schur 不等式
- ...

### 三角函数领域 (TRIGONOMETRY)

**公理**:
- `axiom_sin_cos_identity`: sin²x + cos²x = 1
- `axiom_sin_symmetry`: sin(-x) = -sin(x)
- `axiom_cos_symmetry`: cos(-x) = cos(x)

**核心定理**:
- `thm_double_angle_sin`: 正弦倍角公式
- `thm_double_angle_cos`: 余弦倍角公式
- `thm_sum_sin`: 正弦和差公式
- `thm_product_to_sum`: 积化和差
- ...

### 平面几何领域 (GEOMETRY)

**公理**:
- `axiom_triangle_sides`: 三角形两边之和大于第三边
- `axiom_parallel_lines`: 平行线性质

**定义**:
- `def_area_triangle`: 三角形面积公式
- `def_perimeter`: 周长定义

**核心定理**:
- `thm_pythagorean`: 勾股定理
- `thm_law_of_cosines`: 余弦定理
- `thm_law_of_sines`: 正弦定理
- `thm_heron`: 海伦公式
- ...

---

**作者**: Jiangsheng Yu  
**版本**: 2.1.0  
**更新日期**: 2024
