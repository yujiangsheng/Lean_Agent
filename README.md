# 🧮 Lean Agent - 数学家智能体

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Lean](https://img.shields.io/badge/lean-4-purple.svg)
![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> 🤖 基于大语言模型与 Lean 4 形式化验证的数学研究智能体
> 
> 一个能够自动生成数学猜想、进行智能证明并持续学习的 AI 系统

---

## 📖 项目简介

**Lean Agent** 是一个创新的数学研究智能体，它结合了大语言模型（LLM）的推理能力与 Lean 4 定理证明器的形式化验证能力。该系统能够：

- 🔍 **自动发现**：从已有数学知识中自动推导新的猜想和定理
- ✅ **形式化验证**：使用 Lean 4 对猜想进行严格的数学证明
- 📚 **持续学习**：不断积累知识，优化推理策略
- 🔗 **跨领域推理**：连接不同数学分支，发现深层联系

### 🌟 核心亮点

| 特性 | 说明 | 技术实现 |
|------|------|----------|
| 🧠 **持续学习** | 从已有定理自动推导新定理 | 多步推理链（Chain-of-Thought） |
| 📊 **知识图谱** | 追踪定理间的推导关系 | 有向无环图 + JSON 持久化 |
| 🔗 **跨领域推理** | 连接不同数学分支的知识 | 领域连接映射 + 类比推理 |
| 🎯 **统一知识库** | 11 个数学领域的公理与定理 | 层级化知识表示 |
| 📈 **经验学习** | 从证明历史优化策略 | 模式识别 + 策略权重更新 |
| 🔄 **多步推理** | 支持最多 8 步深度推理 | 组合、特化、泛化、类比、逆否、扩展 |

---

## 📚 支持的数学领域

### 基础领域（3个）
- **代数** (`algebra`)：加法/乘法交换律、结合律、分配律、AM-GM 不等式等
- **三角函数** (`trigonometry`)：基本恒等式、和差化积、倍角公式等
- **平面几何** (`geometry`)：勾股定理、三角形面积、Cauchy-Schwarz 不等式等

### 扩展领域（7个）
- **初等数论** (`number_theory`)：整除性、素数、费马小定理等
- **立体几何** (`solid_geometry`)：球体/圆锥/圆柱体积与表面积
- **解析几何** (`analytic_geometry`)：距离公式、圆锥曲线
- **组合计数** (`combinatorics`)：排列组合、二项式定理
- **概率统计** (`probability`)：期望、方差、贝叶斯定理
- **微积分** (`calculus`)：导数、积分、中值定理
- **线性代数** (`linear_algebra`)：行列式、矩阵运算、特征值

### 特殊领域（1个）
- **跨领域** (`cross_domain`)：连接不同数学分支的桥梁定理

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- （可选）Lean 4 + LeanDojo（用于真实证明验证）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/Lean_Agent.git
cd Lean_Agent

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. （可选）安装 LeanDojo 以启用真实证明
pip install lean-dojo
```

### 验证安装

```bash
python -c "from src import __version__; print(f'Lean Agent v{__version__}')"
# 输出: Lean Agent v2.1.0
```

---

## 💻 使用方法

### 方式一：命令行界面

```bash
# 运行演示（展示基本功能）
python main.py

# 学习模式 - 按轮次
python main.py learn --rounds 5              # 学习 5 轮
python main.py learn --rounds 100            # 学习 100 轮

# 学习模式 - 按时间
python main.py learn --minutes 30            # 学习 30 分钟
python main.py learn --minutes 300           # 学习 5 小时

# 学习模式 - 指定领域
python main.py learn --domain algebra        # 仅代数领域
python main.py learn --domain number_theory  # 仅数论领域

# 查看知识图谱统计
python main.py graph

# 查看学习洞察
python main.py insights
```

### 方式三：学习脚本

```bash
# 使用 run_learning.py 进行持续学习
python run_learning.py 5        # 学习 5 分钟
python run_learning.py 30       # 学习 30 分钟
python run_learning.py          # 默认 10 分钟
python run_learning.py -q 60    # 安静模式学习 60 分钟
```

### 方式二：Python API

```python
from src import (
    ContinuousLearningAgent,      # 持续学习智能体
    UnifiedKnowledgeManager,       # 统一知识库管理器
    MathDomain,                    # 数学领域枚举
    KnowledgeLevel,                # 知识层级枚举
)

# 创建并运行学习智能体
agent = ContinuousLearningAgent()
agent.run_learning_round(domain="algebra")
print(f"已发现 {agent.stats['total_proved']} 个新定理")

# 使用统一知识库
km = UnifiedKnowledgeManager()
km.print_summary()

# 按领域查询
algebra_knowledge = km.get_by_domain(MathDomain.ALGEBRA)
print(f"代数领域有 {len(algebra_knowledge)} 条知识")
```

更多示例请查看 `examples/` 目录。

---

## 📁 项目结构

```
Lean_Agent/
├── main.py                     # 统一命令行入口
├── run_learning.py             # 持续学习脚本（支持时长参数）
├── src/                        # 核心源码 (8 个模块)
│   ├── __init__.py            # 包入口与导出
│   ├── learning_agent.py      # 持续学习智能体（核心）
│   ├── unified_knowledge.py   # 统一数学知识库
│   ├── knowledge_graph.py     # 知识图谱管理
│   ├── experience_learner.py  # 经验学习系统
│   ├── lean_env.py            # Lean 环境交互
│   ├── llm_agent.py           # LLM 集成
│   └── utils.py               # 工具函数
├── data/                       # 数据存储
├── examples/                   # 使用示例 (2个)
├── docs/                       # 详细文档
├── config.json                 # 配置文件
└── requirements.txt            # 依赖列表
```

---

## 📊 知识系统

### 知识层级

| 层级 | 说明 | 示例 |
|------|------|------|
| **公理** (AXIOM) | 不证自明的基础命题 | 加法交换律 |
| **定义** (DEFINITION) | 数学概念的精确定义 | 素数的定义 |
| **核心定理** (CORE) | 经典的重要定理 | 勾股定理 |
| **派生定理** (DERIVED) | 从已有知识推导出来 | （学习过程中生成） |
| **猜想** (CONJECTURE) | 待证明的命题 | （等待验证） |

### 内置知识统计

| 类别 | 数量 |
|------|------|
| **公理** | 21 |
| **定义** | 9 |
| **核心定理** | 37 |
| **总计** | 67 |

---

## 📈 学习效果

### 20分钟学习结果示例

| 指标 | 数值 |
|------|------|
| 完成轮次 | 566 轮 |
| 新增节点 | +2037 |
| 新增推导边 | +6656 |
| 经验库 | 2179 条 |

### 发现的定理示例

- 正弦2次降幂公式
- 3次幂平均不等式推广
- 三维 Cauchy-Schwarz 复数域推广
- Schur 不等式的多种变形
- ...

---

## 🔧 配置

编辑 `config.json`：

```json
{
  "llm": {
    "model_name": "Qwen/Qwen2.5-7B-Instruct",
    "temperature": 0.7
  },
  "lean": {
    "timeout": 30
  }
}
```

---

## 📜 许可证

MIT License

---

**版本**: 2.1.0  
**作者**: Jiangsheng Yu  
**维护者**: Jiangsheng Yu

---

<p align="center">
  <i>让 AI 成为数学家的得力助手 🧮✨</i>
</p>
