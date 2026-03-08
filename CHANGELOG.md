# 📋 更新日志 | Changelog

本文件记录 Gauss 各版本的主要变更。
All notable changes to Gauss are documented here.

---

## [3.0.0] - 2025

### 🎉 新增 | Added

- **Web 可视化服务** (`web/server.py`): SSE 实时流式双面板证明可视化
- **自动定理证明** (`main.py prove`): 支持自然语言输入 → Lean 4 翻译 → 自动证明
- **自然语言翻译** (`main.py translate`): 数学命题自动翻译为 Lean 4 代码
- **Mathlib 模块注册表** (`src/mathlib_registry.py`): 7000+ 模块验证、模糊匹配、自动修复
- **错误诊断反馈**: LLM 根据 Lean 编译错误自动调整 tactic 建议
- **黄金证明模板**: 内置经典定理的验证过证明模板
- **OllamaAgent**: 支持通过 Ollama REST API 调用本地大模型 (默认 qwen3-coder:30b)
- **Report 子命令**: 生成知识库详细统计报告
- **双语文档**: 所有文档和注释均添加中英双语说明

### 🔧 改进 | Improved

- **版本号统一**: 全部文件统一为 v3.0.0
- **代码注释增强**: 所有模块文件添加详尽的中英双语 docstring
- **requirements.txt 文档化**: 添加分层说明和安装指引
- **config.json 版本同步**: 配置文件版本与项目版本一致
- **README.md 全面改版**: 双语 README，增加配置说明、Web UI 用法
- **docs/ 全面更新**: ARCHITECTURE.md、KNOWLEDGE_SYSTEM.md、API_REFERENCE.md 均升级
- **examples/ 注释增强**: 示例文件添加详细演示内容说明
- **lean_project/README.md**: 补充完整的项目说明和使用方法
- **__init__.py 导出修复**: 添加缺失的 `OllamaAgent` 到 `__all__`

### 🐛 修复 | Fixed

- **dead code 清理**: 移除 `experience_learner.py` 中 `return` 后的不可达代码
- **文档引用修正**: `docs/README.md` 移除不存在的示例文件引用 (03/04/05)
- **方式排序修正**: README.md 中方式二/方式三的顺序问题

---

## [2.1.0] - 2024

### 新增

- 持续学习智能体 (ContinuousLearningAgent)
- 多步推理引擎 (ChainOfThoughtReasoner)，最多 8 步
- 统一知识库 (UnifiedKnowledgeManager)，11 个数学领域
- 经验学习系统，智能去重与 Wilson 置信区间
- 知识图谱管理，推导链追踪
- 不完全归纳验证器 (InductiveVerifier)
- Mock 模式支持，无需 Lean 4 即可演示

### 改进

- 推理操作增加到 6 种：组合、特化、泛化、类比、逆否、扩展
- 推理链质量评分系统
- 经验去重：签名快速检查 + 详细相似度检查
- 周期性经验清理，保持库大小可控

---

## [1.0.0] - 2024

### 新增

- 基础 Lean 4 环境交互
- LLM Agent (Qwen) 集成
- 简单的猜想生成与证明尝试
- 基础知识图谱
