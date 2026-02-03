# 📚 文档目录

> Lean Agent 项目文档

---

## 📖 文档列表

| 文档 | 说明 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构设计，核心组件详解 |
| [KNOWLEDGE_SYSTEM.md](KNOWLEDGE_SYSTEM.md) | 知识系统详解，领域和层级说明 |
| [API_REFERENCE.md](API_REFERENCE.md) | 完整 API 参考手册 |

---

## 🚀 快速入门

### 1. 安装

```bash
git clone https://github.com/your-repo/Lean_Agent.git
cd Lean_Agent
pip install -r requirements.txt
```

### 2. 运行

```bash
# 命令行
python main.py learn --rounds 5

# Python API
from src import ContinuousLearningAgent
agent = ContinuousLearningAgent()
agent.run_learning_round()
```

### 3. 查看示例

```bash
python examples/01_basic_usage.py
python examples/02_learning_agent.py
python examples/03_knowledge_query.py
python examples/04_reasoning_demo.py
python examples/05_knowledge_graph.py
```

---

## 📁 文档结构

```
docs/
├── README.md              # 本文件（文档目录）
├── ARCHITECTURE.md        # 系统架构
├── KNOWLEDGE_SYSTEM.md    # 知识系统
└── API_REFERENCE.md       # API 参考
```

---

**作者**: Jiangsheng Yu  
**版本**: 2.1.0
