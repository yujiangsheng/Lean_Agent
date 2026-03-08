# 🧮 Gauss - 数学家智能体

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Lean](https://img.shields.io/badge/lean-4.29-purple.svg)
![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Mathlib](https://img.shields.io/badge/mathlib-latest-orange.svg)

> 🤖 基于大语言模型与 Lean 4 + Mathlib 形式化验证的数学研究智能体，覆盖 Lean 与 Mathlib 所支持的所有数学分支
> 
> An AI-powered mathematical research agent combining LLMs with Lean 4 + Mathlib formal verification, covering all branches of mathematics supported by Lean and Mathlib

---

## 📖 项目简介 | Overview

**Gauss** 是一个创新的数学研究智能体，它结合了大语言模型（LLM）的推理能力与 Lean 4 + Mathlib 定理证明器的形式化验证能力。系统能够自动发现新的数学猜想、进行形式化证明验证、并持续学习积累知识。Gauss 能处理 Lean 与 Mathlib 所覆盖的所有数学分支。

**Gauss** is an innovative mathematical research agent combining LLM reasoning with Lean 4 + Mathlib formal verification. It can automatically discover new conjectures, perform formal proof verification, and continuously learn. Gauss handles all branches of mathematics covered by Lean and Mathlib.

### 🌟 核心亮点 | Key Features

| 特性 | 说明 | 技术实现 |
|------|------|----------|
| 🧠 **持续学习** | 从已有定理自动推导新定理 | 多步推理链 (Chain-of-Thought，最多 8 步) |
| 📊 **知识图谱** | 追踪定理间的推导关系 | 有向无环图 (DAG) + JSON 持久化 |
| 🔗 **跨领域推理** | 连接不同数学分支的知识 | 领域连接映射 + 类比推理 |
| 🎯 **全数学覆盖** | Lean + Mathlib 所有数学分支 | 动态知识库 + Mathlib 注册表 |
| 📈 **经验学习** | 从证明历史优化策略 | 智能去重 + Wilson 置信区间 + 模式提取 |
| 🔄 **多步推理** | 支持 6 种推理操作 | 组合、特化、泛化、类比、逆否、扩展 |
| ✅ **形式验证** | Lean 4 + Mathlib 严格证明 | 子进程验证 + 错误诊断自动修复 |
| 🌐 **Web 可视化** | 实时流式展示证明过程 | SSE 双侧事件流 + 五面板布局 |

---

## 📚 支持的数学领域 | Supported Domains

Gauss 基于 Lean 4 与 Mathlib（7,743 个模块），覆盖以下所有数学分支：

Gauss is powered by Lean 4 and Mathlib (7,743 modules), covering all the following branches of mathematics:

### 核心代数与数论 | Algebra & Number Theory

| 分支 | Branch | Mathlib 模块数 | 说明 |
|------|--------|:--------------:|------|
| **代数** | Algebra | 1,280 | 群/环/域、交换代数、同调代数、李代数、仿射幺半群等 |
| **环论** | Ring Theory | 654 | 理想、局部化、Dedekind 整环、赋值环、多项式环等 |
| **群论** | Group Theory | 157 | 有限群、Abel 群、Sylow 定理、自由群、群作用等 |
| **域论** | Field Theory | 78 | Galois 理论、域扩张、分裂域、可分性等 |
| **数论** | Number Theory | 222 | 素数分布、二次互反律、p-adic 数、模形式、算术函数等 |

### 分析与测度 | Analysis & Measure Theory

| 分支 | Branch | Mathlib 模块数 | 说明 |
|------|--------|:--------------:|------|
| **分析** | Analysis | 774 | 实/复分析、泛函分析、调和分析、特殊函数、ODE 等 |
| **测度论** | Measure Theory | 299 | Lebesgue 测度、积分、Radon-Nikodym、遍历理论等 |
| **概率论** | Probability | 120 | 概率空间、条件期望、鞅论、大数定律、核等 |

### 几何与拓扑 | Geometry & Topology

| 分支 | Branch | Mathlib 模块数 | 说明 |
|------|--------|:--------------:|------|
| **拓扑学** | Topology | 623 | 一般拓扑、一致空间、度量空间、紧致性、连通性等 |
| **几何** | Geometry | 123 | 仿射几何、欧氏几何、流形、微分几何等 |
| **代数几何** | Algebraic Geometry | 123 | 概形、层论、态射、上同调等 |
| **代数拓扑** | Algebraic Topology | 118 | 基本群、单纯对象、Dold-Kan 对应、神经等 |

### 结构与抽象 | Structure & Abstraction

| 分支 | Branch | Mathlib 模块数 | 说明 |
|------|--------|:--------------:|------|
| **范畴论** | Category Theory | 1,022 | 函子、自然变换、极限、Abelian 范畴、单子等 |
| **序论** | Order Theory | 300 | 格论、偏序集、完备格、Galois 连接等 |
| **线性代数** | Linear Algebra | 348 | 向量空间、矩阵、特征值、张量积、外代数等 |
| **表示论** | Representation Theory | 33 | 群表示、模表示、Maschke 定理等 |

### 离散与组合 | Discrete & Combinatorics

| 分支 | Branch | Mathlib 模块数 | 说明 |
|------|--------|:--------------:|------|
| **组合数学** | Combinatorics | 168 | 图论、极值组合、排列组合、Ramsey 理论等 |
| **集合论** | Set Theory | 45 | ZFC 公理、序数、基数、连续统等 |
| **数据结构** | Data Structures | 639 | 列表、有限集、多重集、树、有限映射等 |

### 逻辑与计算 | Logic & Computation

| 分支 | Branch | Mathlib 模块数 | 说明 |
|------|--------|:--------------:|------|
| **逻辑** | Logic | 57 | 命题逻辑、一阶逻辑、可定义性、编码等 |
| **模型论** | Model Theory | 34 | 语言、结构、超积、量词消去等 |
| **可计算性** | Computability | 28 | 图灵机、递归函数、可判定性等 |
| **信息论** | Information Theory | 5 | 熵、互信息等 |

### 其他分支 | Other Branches

| 分支 | Branch | Mathlib 模块数 | 说明 |
|------|--------|:--------------:|------|
| **动力系统** | Dynamics | 31 | 遍历理论、不动点、周期轨道等 |
| **凝聚数学** | Condensed Math | 33 | 凝聚集、凝聚 Abel 群（前沿方向）等 |

### 内置知识库 | Built-in Knowledge Base (25 领域, 全覆盖)

Gauss 内建了覆盖所有数学分支的精选中文知识库，为推理和猜想生成提供种子知识：

> **基础领域**: 代数 (18) · 三角函数 (16) · 平面几何 (10)
>
> **扩展领域**: 数论 (12) · 立体几何 (10) · 解析几何 (11) · 组合计数 (12) · 概率统计 (14) · 微积分 (17) · 线性代数 (15)
>
> **高等代数**: 环论 (11) · 群论 (11) · 域论 (9) · 表示论 (8)
>
> **分析与测度**: 拓扑学 (11) · 测度论 (9)
>
> **结构与抽象**: 范畴论 (9) · 序论 (8) · 集合论 (8) · 逻辑学 (9)
>
> **高等几何/拓扑**: 代数几何 (8) · 代数拓扑 (8)
>
> **其他分支**: 动力系统 (8) · 信息论 (8) · 跨领域 (14)

---

## 🚀 快速开始 | Quick Start

### 环境要求 | Requirements

- **Python 3.9+**
- **（推荐）** [Ollama](https://ollama.com) + qwen3-coder:30b 模型
- **（可选）** Lean 4 + Mathlib（用于真实证明验证）
- **（可选）** LeanDojo >= 1.8.0（用于 Lean 4 交互）

### 安装步骤 | Installation

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

### 验证安装 | Verify

```bash
python -c "from src import __version__; print(f'Gauss v{__version__}')"
# 输出: Gauss v3.0.0
```

---

## 💻 使用方法 | Usage

### 方式一：命令行界面 | CLI

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

### 方式二：Python API

```python
from src import (
    ContinuousLearningAgent,      # 持续学习智能体
    UnifiedKnowledgeManager,       # 统一知识库管理器
    MathDomain,                    # 数学领域枚举
    KnowledgeLevel,                # 知识层级枚举
)

# ── 创建并运行学习智能体 ──
agent = ContinuousLearningAgent()
agent.run_learning_round(domain="algebra")
print(f"已发现 {agent.stats['total_proved']} 个新定理")

# ── 使用统一知识库 ──
km = UnifiedKnowledgeManager()
km.print_summary()

# ── 按领域查询 ──
algebra_knowledge = km.get_by_domain(MathDomain.ALGEBRA)
print(f"代数领域有 {len(algebra_knowledge)} 条知识")

# ── 搜索知识 ──
results = km.search("交换")
for k in results:
    print(f"  {k.id}: {k.statement_cn}")
```

### 方式三：持续学习脚本 | Learning Script

更多示例请查看 `examples/` 目录。

---

## 📁 项目结构 | Project Structure

```
Lean_Agent/
├── main.py                     # 统一命令行入口 (CLI entry point)
├── run_learning.py             # 持续学习脚本 (Learning script)
├── config.json                 # 配置文件 (Configuration)
├── requirements.txt            # Python 依赖 (Dependencies)
│
├── src/                        # 核心源码 (Core source, 8 modules)
│   ├── __init__.py            #   包入口与 API 导出
│   ├── learning_agent.py      #   🧠 持续学习智能体 + 多步推理引擎
│   ├── unified_knowledge.py   #   📚 统一数学知识库 (11 领域)
│   ├── knowledge_graph.py     #   📊 知识图谱 DAG 管理
│   ├── experience_learner.py  #   📈 经验学习 + 智能去重
│   ├── lean_env.py            #   🔗 Lean 4 环境交互
│   ├── llm_agent.py           #   🤖 LLM 集成 (Ollama/Qwen/Mock)
│   ├── mathlib_registry.py    #   📦 Mathlib 模块注册表
│   └── utils.py               #   🔧 工具函数
├── web/                        # Web 可视化服务
│   ├── server.py              #   HTTP + SSE 服务器
│   └── static/                #   前端资源 (HTML/JS/CSS)
├── data/                       # 数据存储
├── examples/                   # 使用示例 (2 个)
├── docs/                       # 详细文档 (3 篇)
└── lean_project/               # Lean 4 项目 (含 Mathlib 依赖)
```

---

## 📊 知识系统 | Knowledge System

### 知识层级 | Knowledge Hierarchy

| 层级 | Level | 说明 | 数量 |
|------|-------|------|------|
| **公理** | AXIOM | 不证自明的基础命题 | 21 |
| **定义** | DEFINITION | 数学概念的精确定义 | 9 |
| **核心定理** | CORE | 经典的重要定理 | 37 |
| **派生定理** | DERIVED | 学习过程中推导生成 | 动态增长 |
| **猜想** | CONJECTURE | 待验证的命题 | 动态增长 |
| **总计** | Total | 内置知识 | **67** |

---

## 📈 学习效果 | Learning Results

### 20 分钟学习结果示例 | 20-minute Example

| 指标 | Metric | 数值 |
|------|--------|------|
| 完成轮次 | Rounds | 566 |
| 新增节点 | New nodes | +2037 |
| 新增推导边 | New edges | +6656 |
| 经验库 | Experiences | 2179 条 |

### 发现的定理示例

- 正弦2次降幂公式
- 3次幂平均不等式推广
- 三维 Cauchy-Schwarz 复数域推广
- Schur 不等式的多种变形
- ...

---

## 🔧 配置 | Configuration

编辑 `config.json` 进行自定义（Edit `config.json` for customization）：

```json
{
  "llm": {
    "backend": "ollama",
    "model_name": "qwen3-coder:30b",
    "ollama_base_url": "http://127.0.0.1:11434",
    "temperature": 0.2
  },
  "lean": {
    "project_dir": "lean_project",
    "timeout": 120,
    "use_mathlib": true
  },
  "proof_search": {
    "beam_width": 10,
    "max_iterations": 500
  }
}
```

### 配置说明 | Config Reference

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `llm.backend` | LLM 后端 (`ollama` / `transformers`) | `ollama` |
| `llm.model_name` | 模型名称 | `qwen3-coder:30b` |
| `llm.temperature` | 温度（越低越确定） | `0.2` |
| `lean.project_dir` | Lean 项目目录 | `lean_project` |
| `lean.timeout` | 验证超时（秒） | `120` |
| `proof_search.beam_width` | 束搜索宽度 | `10` |

---

## 📚 文档 | Documentation

| 文档 | 说明 |
|------|------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系统架构设计 (System Architecture) |
| [docs/KNOWLEDGE_SYSTEM.md](docs/KNOWLEDGE_SYSTEM.md) | 知识系统详解 (Knowledge System) |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | 完整 API 参考 (API Reference) |

---

## 📜 许可证 | License

MIT License

---

**版本 (Version)**: 3.0.0  
**作者 (Author)**: Jiangsheng Yu  
**维护者 (Maintainer)**: Jiangsheng Yu

---

<p align="center">
  <i>让 AI 成为数学家的得力助手 🧮✨ — Gauss</i>
  <br/>
  <i>Making AI a mathematician's powerful assistant — Gauss</i>
</p>
