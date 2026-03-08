#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
            Gauss Web Server (证明可视化服务)
═══════════════════════════════════════════════════════════════════════════════

为 Gauss 提供 Web API 和实时证明可视化界面。
Provides a Web API and real-time proof visualization interface.

核心功能 (Core Features):
    - SSE (Server-Sent Events) 实时流式推送证明过程
    - 双侧事件流: LLM 推理过程 + Lean 4 验证过程
    - 自动翻译: 自然语言 / Lean 4 代码自动检测
    - 错误诊断: Lean 编译错误分析与自动修复
    - Mathlib 导入验证: 自动检查和修复过时的模块路径

架构 (Architecture):
    ProofEvent  →  ProofSession  →  StreamingProver  →  Web Handler
      事件          会话管理       证明引擎封装       HTTP服务

启动方式 (Start):
    python web/server.py
    # 然后访问 http://127.0.0.1:5000

作者 (Author): Jiangsheng Yu
版本 (Version): 3.0.0
"""

import sys
import json
import time
import queue
import threading
import traceback
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import io

# 添加项目根目录到 sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))


# ═══════════════════════════════════════════════════════════════════════════
# 事件系统：记录 LLM 和 Lean 双侧的证明过程
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ProofEvent:
    """证明过程中的一个事件"""
    side: str          # "llm" 或 "lean"
    event_type: str    # "info" / "step" / "code" / "tactic" / "success" / "error" / "done"
    content: str       # 事件内容（文本或代码）
    detail: str = ""   # 附加详情
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def to_sse(self) -> str:
        """转为 SSE 格式"""
        data = json.dumps(asdict(self), ensure_ascii=False)
        return f"data: {data}\n\n"


class ProofSession:
    """
    一次证明会话，收集 LLM 和 Lean 双侧的事件流。
    """
    def __init__(self):
        self.events: list[ProofEvent] = []
        self.event_queue: queue.Queue = queue.Queue()
        self.done = False

    def emit(self, side: str, event_type: str, content: str, detail: str = ""):
        evt = ProofEvent(side=side, event_type=event_type, content=content, detail=detail)
        self.events.append(evt)
        self.event_queue.put(evt)

    def finish(self):
        self.done = True
        self.event_queue.put(None)  # sentinel


# ═══════════════════════════════════════════════════════════════════════════
# 证明引擎：封装 OllamaAgent + LeanEnvironment，输出事件流
# ═══════════════════════════════════════════════════════════════════════════

class StreamingProver:
    """
    与 OllamaAgent / LeanEnvironment 交互，产出 ProofEvent 流。
    """

    def __init__(self, session: ProofSession, config: dict):
        self.session = session
        self.config = config

    @staticmethod
    def _is_lean_code(text: str) -> bool:
        """判断输入是否为 Lean 4 代码"""
        text = text.strip()
        lean_keywords = ['theorem', 'lemma', 'import', 'def ', 'example', '#check']
        return any(text.startswith(kw) or f'\n{kw}' in text for kw in lean_keywords)

    @staticmethod
    def _extract_theorem_declaration(lean_code: str) -> str:
        """从 Lean 代码中提取 theorem 声明行"""
        for line in lean_code.split('\n'):
            stripped = line.strip()
            if stripped.startswith(('theorem', 'lemma')):
                if ':= by' not in stripped:
                    stripped = stripped.rstrip().rstrip('where').rstrip()
                    if not stripped.endswith(':= by'):
                        stripped += ' := by'
                return stripped
        return ""

    @staticmethod
    def _clean_tactic(line: str) -> str:
        """清理 tactic 字符串"""
        line = line.strip()
        for prefix in ['- ', '* ', '• ']:
            if line.startswith(prefix):
                line = line[len(prefix):]
        if line and line[0].isdigit():
            for sep in ['. ', ') ', ': ']:
                if sep in line:
                    line = line.split(sep, 1)[-1]
                    break
        line = line.replace('```', '').replace('lean', '').strip()
        if len(line) > 200 or line.startswith('#') or line.startswith('--'):
            return ""
        return line

    @staticmethod
    def _extract_lean_code(content: str) -> str:
        """从 LLM 响应中提取 Lean 4 代码块"""
        import re
        content = content.strip()
        pattern = r'```(?:lean4?|Lean)?\s*\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            return matches[0].strip()
        if 'import' in content or 'theorem' in content or 'lemma' in content:
            lines = []
            in_code = False
            for line in content.split('\n'):
                stripped = line.strip()
                if stripped.startswith(('import', 'open', 'theorem', 'lemma', 'def',
                                       'example', '#', 'namespace', 'section', 'end',
                                       'variable', 'noncomputable')):
                    in_code = True
                if in_code:
                    lines.append(line)
            if lines:
                return '\n'.join(lines)
        return content

    def run(self, theorem_statement: str):
        """在后台线程中执行完整的证明流程"""
        try:
            self._do_prove(theorem_statement)
        except Exception as e:
            self.session.emit("llm", "error", f"内部错误: {e}", traceback.format_exc())
        finally:
            self.session.finish()

    @staticmethod
    def _get_lean_error(check: dict) -> str:
        """从 check_proof 结果中提取完整错误信息（Lean 错误可能在 stdout 或 stderr）"""
        err = check.get("error", "")
        out = check.get("output", "")
        if out and "error" in out.lower():
            err = f"{out}\n{err}" if err else out
        return err.strip()

    @staticmethod
    def _extract_search_keywords(theorem_text: str, proof_plan: str) -> list[str]:
        """
        从定理文本和证明计划中提取用于 Mathlib grep 搜索的英文关键词。
        """
        import re
        # 中文数学概念 → 英文搜索关键词
        concept_map = {
            "凯莱": ["Cayley", "Perm", "MulAction", "subgroupOfMulAction"],
            "拉格朗日": ["Lagrange", "card_subgroup"],
            "欧拉": ["Euler", "totient"],
            "费马": ["Fermat", "ZMod.pow_card"],
            "中值": ["MeanValue", "exists_ratio_deriv"],
            "介值": ["Intermediate", "IsPreconnected"],
            "贝祖": ["Bezout", "gcd_eq_gcd_ab"],
            "同构": ["Isomorphism", "MulEquiv", "RingEquiv"],
            "正规子群": ["Normal", "Subgroup.Normal"],
            "商群": ["Quotient", "QuotientGroup"],
            "置换": ["Perm", "Equiv.Perm"],
            "群作用": ["MulAction", "smul"],
            "同态": ["Hom", "MonoidHom", "MulHom"],
            "不动点": ["FixedPoints", "fixedBy"],
            "轨道": ["Orbit", "MulAction.orbit"],
            "素数": ["Prime", "Nat.Prime"],
            "唯一分解": ["UniqueFactorizationDomain", "factorization"],
            "行列式": ["det", "Matrix.det"],
            "特征值": ["Eigenvalue", "Module.End.eigenvalue"],
            "秩": ["rank", "Module.rank"],
            "连续": ["Continuous", "continuous_def"],
            "可微": ["Differentiable", "HasDerivAt"],
            "积分": ["Integral", "intervalIntegral"],
        }
        keywords = []
        combined = theorem_text + " " + proof_plan[:500]
        for zh, en_list in concept_map.items():
            if zh in combined:
                keywords.extend(en_list)

        # 从证明计划中提取 PascalCase 标识符（可能是 Mathlib API 名）
        identifiers = re.findall(r'\b([A-Z][a-zA-Z]+(?:\.[A-Z][a-zA-Z]+)+)', proof_plan)
        for ident in identifiers[:5]:
            last_part = ident.split('.')[-1]
            if last_part not in keywords and len(last_part) > 3:
                keywords.append(last_part)

        return keywords[:8]  # 限制数量避免搜索过多

    def _validate_lean_syntax(self, lean_code, agent, lean_env, theorem_statement, context_text="", max_fix=2):
        """
        用 Lean 编译器验证代码语法，如果有错则让 LLM 修正，最多 max_fix 次。
        返回修正后的代码。
        """
        for fix_round in range(max_fix + 1):
            check = lean_env.check_proof(lean_code) if hasattr(lean_env, 'check_proof') else None
            if check is None:
                break  # 无法检查，跳过
            if check.get("success"):
                break  # 语法正确

            error_msg = self._get_lean_error(check)
            if fix_round >= max_fix:
                break  # 已用完修正次数

            # 让 LLM 根据编译错误修正代码
            fix_prompt = (
                f"以下 Lean 4 代码存在语法或类型错误，请修正。只输出代码，不要解释。\n\n"
                f"原始命题：{theorem_statement}\n\n"
                f"当前代码：\n```lean\n{lean_code}\n```\n\n"
                f"Lean 编译器报错：\n{error_msg}\n\n"
                f"要求：\n"
                f"1. 修正所有语法和类型错误，确保代码能通过 Lean 4 编译\n"
                f"2. 保持 theorem 声明的数学含义不变\n"
                f"3. 检查 import 是否正确（很多 tactic/lemma 需要正确 import）\n"
                f"4. 注意 Nat/Int/Real coercion，类型不匹配时先 show 明确目标\n"
                f"5. 区分 ↔ (Iff) 与 = (Eq)\n"
                f"6. 只输出修正后的 ```lean ... ``` 代码块"
            )
            fix_system = (
                "你是 Lean 4 + Mathlib 专家。只输出代码，不要解释。"
                "修正语法和类型错误，注意 import、coercion、↔ vs =。"
            )
            fix_resp = agent.generate(fix_prompt, fix_system)
            new_code = self._extract_lean_code(fix_resp.content)
            if new_code.strip():
                from mathlib_registry import fix_imports
                new_code, _ = fix_imports(new_code)
                lean_code = new_code

        return lean_code

    def _validate_statement(self, stmt_code, agent, lean_env, theorem_statement, max_fix=3):
        """
        验证定理陈述（带 sorry）能否通过 Lean 编译。
        陈述搞对了，证明往往就顺了；陈述不对，再聪明也会绕。
        返回修正后的陈述代码。
        """
        for fix_round in range(max_fix + 1):
            check = lean_env.check_proof(stmt_code) if hasattr(lean_env, 'check_proof') else None
            if check is None:
                break
            if check.get("success"):
                break

            error_msg = self._get_lean_error(check)
            if fix_round >= max_fix:
                break

            fix_prompt = (
                f"以下 Lean 4 定理陈述无法通过编译，请修正 theorem 声明使其类型正确。\n"
                f"只输出代码，不要解释。\n\n"
                f"原始数学命题：{theorem_statement}\n\n"
                f"当前代码：\n```lean\n{stmt_code}\n```\n\n"
                f"Lean 编译器报错：\n{error_msg}\n\n"
                f"要求：\n"
                f"1. 只修正定理陈述（类型签名），保持数学含义不变\n"
                f"2. 证明部分保留 sorry\n"
                f"3. 注意以下常见陈述问题：\n"
                f"   - import 缺失：加上需要的 import Mathlib.xxx\n"
                f"   - 命名空间：函数必须带完整前缀（如 Real.sin 而非 sin），或在 import 后加 open Real\n"
                f"   - 量词/类型层级：∀ ∃ Subtype Set Finset 写法\n"
                f"   - 等价 ↔ 与 相等 = 的区分\n"
                f"   - Nat/Int/Real 之间的 coercion\n"
                f"4. 只输出修正后的 ```lean ... ``` 代码块"
            )
            fix_system = (
                "你是 Lean 4 类型系统专家。只输出代码，不要解释。"
                "修正定理陈述使之通过编译，证明留 sorry。"
                "注意 import、量词、coercion、↔ vs =。"
            )
            fix_resp = agent.generate(fix_prompt, fix_system)
            new_code = self._extract_lean_code(fix_resp.content)
            if new_code.strip():
                from mathlib_registry import fix_imports
                new_code, _ = fix_imports(new_code)
                stmt_code = new_code

        return stmt_code

    def _do_prove(self, theorem_statement: str):
        llm_cfg = self.config.get("llm", {})
        lean_cfg = self.config.get("lean", {})
        proof_cfg = self.config.get("proof_search", {})

        # ── 初始化 LLM Agent ──
        from llm_agent import OllamaAgent, MockLLMAgent, LLMResponse

        use_mock = llm_cfg.get("backend") == "mock"
        if use_mock:
            agent = MockLLMAgent(verbose=True)
        else:
            try:
                agent = OllamaAgent(
                    model_name=llm_cfg.get("model_name", "qwen3-coder:30b"),
                    base_url=llm_cfg.get("ollama_base_url", "http://127.0.0.1:11434"),
                    max_length=llm_cfg.get("max_length", 4096),
                    temperature=llm_cfg.get("temperature", 0.2),
                    top_p=llm_cfg.get("top_p", 0.9),
                    verbose=True,
                )
            except Exception as e:
                self.session.emit("llm", "error", f"LLM 初始化失败: {e}")
                return

        # ── 初始化 Lean 环境 ──
        from lean_env import LeanEnvironment
        lean_env = LeanEnvironment(
            timeout=lean_cfg.get("timeout", 120),
            lean_executable=lean_cfg.get("lean_executable", "lean"),
            lake_executable=lean_cfg.get("lake_executable", "lake"),
            project_dir=lean_cfg.get("project_dir"),
        )

        max_retries = proof_cfg.get("max_retries", 3)

        # ══════════════════════════════════════════════════════════
        # 如果用户直接输入 Lean 代码，跳过左面板
        # ══════════════════════════════════════════════════════════
        is_lean = self._is_lean_code(theorem_statement)

        if is_lean:
            lean_code = theorem_statement
            self.session.emit("lean", "lean-stmt", lean_code, "用户提供的 Lean 代码")
            # 直接验证用户提供的代码
            check = lean_env.check_proof(lean_code) if hasattr(lean_env, 'check_proof') else None
            if check and check.get("success"):
                self.session.emit("llm", "success", "✅ 证明成功！")
                self.session.emit("lean", "success", "✅ Lean 编译验证通过")
                self.session.emit("lean", "code", lean_code, "验证通过的完整代码")
            else:
                error_msg = (check.get("error", "") or check.get("output", "")) if check else "无法检查"
                self.session.emit("lean", "error", "❌ 验证失败", error_msg[:300])
            return

        # ══════════════════════════════════════════════════════════
        # 阶段 1: 左面板 — LLM 生成自然语言证明
        # ══════════════════════════════════════════════════════════

        nl_proof_prompt = f"""请用严谨的数学语言给出以下命题的完整证明。

命题：{theorem_statement}

要求：
1. 用自然语言写出完整的数学证明，逻辑清晰、步骤严谨
2. 标明关键的推理步骤
3. 指出用到的定理或引理"""

        nl_system = "你是一位数学家，擅长给出清晰严谨的数学证明。请直接给出证明，不要添加与证明无关的内容。"
        nl_response = agent.generate(nl_proof_prompt, nl_system)
        nl_proof_text = nl_response.content.strip()

        # 左面板：显示自然语言证明（只做一次，之后不再变动）
        self.session.emit("llm", "nl-proof", nl_proof_text, "自然语言证明")

        # ══════════════════════════════════════════════════════════
        # 阶段 2–5: 计划级迭代闭环
        #   计划 → 陈述 → 证明 → Lean 验证
        #   失败 → 带反馈重新生成计划 → 再走一轮
        # ══════════════════════════════════════════════════════════
        self._plan_driven_prove(
            nl_proof_text, theorem_statement, agent, lean_env, max_retries)

    # ──────────────────────────────────────────────────────────────
    # 计划级迭代：Plan → Statement → Proof → Verify → (fail? → re-plan)
    # ──────────────────────────────────────────────────────────────

    def _plan_driven_prove(self, nl_proof_text, theorem_statement,
                           agent, lean_env, max_retries):
        """
        外层循环：每轮重新生成结构化证明计划 → 陈述 → 证明 → 验证。
        验证失败时，先调用 LLM 分析 Lean 报错原因，再用分析结果指导下一轮修订。
        """
        # ── 0. 黄金证明模板：对已知经典定理直接提供验证过的正确代码 ──
        from mathlib_registry import build_import_hint, fix_imports, lookup_golden_proof
        golden = lookup_golden_proof(theorem_statement)
        if golden:
            self.session.emit("lean", "info", "🏆 检测到经典定理，使用已验证的证明模板")
            # 优先尝试直接形式的证明
            for code_key in ("code", "code_exists"):
                code = golden.get(code_key, "")
                if not code:
                    continue
                self.session.emit("lean", "code", code, f"黄金模板 ({code_key})")
                check = lean_env.check_proof(code)
                if check and check.get("success"):
                    self.session.emit("llm", "success", "✅ 黄金模板证明通过！")
                    self.session.emit("lean", "success", "✅ Lean 编译验证通过（黄金模板）")
                    self.session.emit("lean", "code", code, "验证通过的完整代码")
                    return
                else:
                    error_msg = self._get_lean_error(check) if check else "无法检查"
                    self.session.emit("lean", "info",
                                      f"黄金模板 {code_key} 未通过: {error_msg[:200]}")
            # 模板未通过，但仍将 API hints 注入后续 prompt
            self.session.emit("lean", "info", "黄金模板未直接通过，将 API 提示注入 LLM prompt")

        prev_plan = ""
        prev_error = ""
        prev_code = ""
        error_analysis = ""   # LLM 对 Lean 报错的诊断

        # 构建合法 import 提示
        import_hint = build_import_hint(theorem_statement)

        # 如果有黄金模板的 API hints，追加到 import hint 中
        if golden and golden.get("api_hints"):
            api_lines = ["\n\n以下是该定理在 Mathlib 中的关键 API（已验证存在）："]
            for hint in golden["api_hints"]:
                api_lines.append(f"  - {hint}")
            api_lines.append("请优先使用上述 API 构建证明，不要编造不存在的函数名。")
            import_hint += "\n".join(api_lines)

        for plan_round in range(max_retries):
            # ── 2. 生成 / 修订结构化证明计划 ──
            if plan_round == 0:
                plan_prompt = f"""请根据以下自然语言证明，给出面向 Lean 4 形式化的结构化证明计划。

命题：{theorem_statement}

自然语言证明：
{nl_proof_text}

{import_hint}

请按以下格式输出（不要输出其他内容）：

## 定理（Lean 4 形式）
一行写出 theorem 的完整类型签名（包含 import 和 open）

## import 与 open
```lean
import Mathlib.xxx
open Real  -- 或其他需要的命名空间
```

## 证明路线（3–8 步）
每步一行，格式：
`步骤N: have hN : <类型> := by <tactic>  -- 引理: <Mathlib名>`

规则：
- 函数必须带命名空间（Real.sin 而非 sin），或写 open Real
- import 必须从上面的合法模块列表中选取
- 引理名不确定时写 `simp / omega / aesop` 自动收尾
- 优先 simp / rw / linarith / nlinarith / omega / aesop
- 区分 ↔ 与 =，注意 Nat/Int/Real coercion"""
            else:
                # 基于 LLM 错误分析修订计划
                plan_prompt = f"""上一轮 Lean 4 验证失败，请根据错误分析修订证明计划。

命题：{theorem_statement}

上一轮计划：
{prev_plan}

上一轮代码：
```lean
{prev_code}
```

Lean 报错：
{prev_error[:800]}

错误分析：
{error_analysis}

{import_hint}

请根据以上分析，修订证明计划。按以下格式输出（不要输出其他内容）：

## 定理（Lean 4 形式）
一行写出 theorem 的完整类型签名（包含 import 和 open）

## import 与 open
```lean
import Mathlib.xxx
open Real
```

## 证明路线（3–8 步）
每步一行，格式：
`步骤N: have hN : <类型> := by <tactic>  -- 引理: <Mathlib名>`

规则：
- 针对错误分析中指出的问题逐一修正
- import 必须从上面的合法模块列表中选取
- 函数必须带命名空间或 open
- 引理名不确定时写 simp / omega / aesop
- 优先 simp / rw / linarith / nlinarith / omega / aesop"""

            plan_system = (
                "你是 Lean 4 + Mathlib 专家。输出简洁的结构化证明计划。"
                "计划必须全面覆盖证明的每个逻辑步骤，同时保持简洁——每步一行。"
                "直接输出计划，不要添加无关内容。"
            )
            plan_response = agent.generate(plan_prompt, plan_system)
            proof_plan = plan_response.content.strip()

            # 中间面板：显示结构化证明计划
            round_label = "结构化证明计划" if plan_round == 0 else f"修订计划（第 {plan_round + 1} 轮）"
            self.session.emit("plan", "nl-proof", proof_plan, round_label)

            # ── 3. 形式化定理陈述（statement first）──
            stmt_prompt = (
                f"请将以下数学命题写成 Lean 4 的 theorem 声明，证明部分用 sorry。\n\n"
                f"命题：{theorem_statement}\n\n"
                f"参考证明计划：\n{proof_plan.split('## 证明路线')[0] if '## 证明路线' in proof_plan else proof_plan[:600]}\n\n"
                f"{import_hint}\n\n"
                f"要求：\n"
                f"1. 只输出 Lean 4 + Mathlib 代码，不要解释\n"
                f"2. 写 theorem 声明 + := by sorry\n"
                f"3. import 必须从上面的合法模块列表中选取\n"
                f"4. 在 import 之后加 open Real（或其他需要的命名空间），避免裸名\n"
                f"5. 类型正确：区分 Nat/Int/Real coercion，区分 ↔ 与 =\n"
                f"6. 只输出 ```lean ... ``` 代码块"
            )
            stmt_system = (
                "你是 Lean 4 类型系统专家。只输出代码，不要解释。"
                "函数名必须带命名空间（如 Real.sin），或 import 后加 open Real。"
                "绝对不要 import 不存在的模块，只能使用用户提供的合法模块列表。"
            )
            stmt_resp = agent.generate(stmt_prompt, stmt_system)
            stmt_code = self._extract_lean_code(stmt_resp.content)
            if not stmt_code:
                stmt_code = f"-- {theorem_statement}\ntheorem auto_theorem : sorry := by\n  sorry"

            # 自动修复非法 import
            stmt_code, stmt_fixes = fix_imports(stmt_code)
            if stmt_fixes:
                self.session.emit("lean", "info",
                                  "\ud83d\udd27 自动修复 import: " + "; ".join(stmt_fixes))

            # 用 Lean 编译器验证陈述
            stmt_code = self._validate_statement(stmt_code, agent, lean_env, theorem_statement)

            # 显示定理陈述
            theorem_decl = self._extract_theorem_declaration(stmt_code)
            if theorem_decl:
                self.session.emit("lean", "lean-stmt", theorem_decl,
                                  "定理陈述" if plan_round == 0 else f"定理陈述（第 {plan_round + 1} 轮）")
            else:
                self.session.emit("lean", "lean-stmt", stmt_code, "定理陈述")

            # ── 3.5 exact? 搜索：让 Lean 编译器找现成证明 ──
            self.session.emit("lean", "info", "🔍 正在用 exact? 搜索 Mathlib 中的现成证明…")
            exact_result = lean_env.search_exact(stmt_code)
            if exact_result.get("found"):
                suggestion = exact_result["suggestion"]
                full_code = exact_result["full_code"]
                self.session.emit("lean", "info", f"✨ exact? 找到建议: {suggestion}")
                # 验证 exact? 建议的代码
                if full_code:
                    full_code, _ = fix_imports(full_code)
                    check = lean_env.check_proof(full_code)
                    if check and check.get("success"):
                        self.session.emit("llm", "success", f"✅ exact? 直接找到证明: {suggestion}")
                        self.session.emit("lean", "success", "✅ Lean 编译验证通过（exact? 搜索）")
                        self.session.emit("lean", "code", full_code, "验证通过的完整代码")
                        return
                    else:
                        self.session.emit("lean", "info", f"exact? 建议未通过验证，继续使用 LLM 证明")
            else:
                self.session.emit("lean", "info",
                                  f"exact? 未找到直接证明 ({exact_result.get('output', '')[:100]})")

            # ── 3.6 Mathlib 搜索：找相关定理注入 prompt ──
            mathlib_hints = ""
            api_keywords = self._extract_search_keywords(theorem_statement, proof_plan)
            if api_keywords:
                self.session.emit("lean", "info", f"🔍 Mathlib 搜索关键词: {', '.join(api_keywords)}")
                api_results = lean_env.search_mathlib_theorems(api_keywords, max_results=15)
                if api_results:
                    hint_lines = ["以下是 Mathlib 中可能相关的定理/引理（由 grep 搜索得到）："]
                    for r in api_results:
                        hint_lines.append(f"  - {r['name']}  (in {r['module']})")
                    mathlib_hints = "\n".join(hint_lines)
                    self.session.emit("lean", "info",
                                      f"📚 找到 {len(api_results)} 个相关 Mathlib 定理")

            # ── 3.7 apply? 搜索：找可用引理 ──
            apply_hint = ""
            apply_result = lean_env.search_apply(stmt_code)
            if apply_result.get("found"):
                apply_hint = f"\napply? 建议: {apply_result['suggestion']}\n请优先尝试使用此建议。"
                self.session.emit("lean", "info", f"💡 apply? 建议: {apply_result['suggestion']}")

            # ── 4. 基于证明计划构建证明 ──
            skeleton_prompt = (
                f"请基于以下结构化证明计划，写出完整的 Lean 4 + Mathlib 证明代码。\n\n"
                f"命题：{theorem_statement}\n\n"
                f"定理陈述（已通过 Lean 编译验证）：\n```lean\n{stmt_code}\n```\n\n"
                f"证明计划：\n{proof_plan}\n\n"
                f"{import_hint}\n\n"
            )
            if mathlib_hints:
                skeleton_prompt += f"{mathlib_hints}\n\n"
            if apply_hint:
                skeleton_prompt += f"{apply_hint}\n\n"
            skeleton_prompt += (
                f"要求：\n"
                f"1. 只输出完整 Lean 4 代码（包含 import / open / theorem），不要解释\n"
                f"2. import 必须从上面的合法模块列表中选取\n"
                f"3. 严格按照证明计划的步骤顺序写 tactic\n"
                f"4. 每 3–6 行一个 have，显式声明中间结论\n"
                f"5. 优先 simp / rw / linarith / nlinarith / omega / aesop\n"
                f"6. 不要用 sorry\n"
                f"7. 只输出 ```lean ... ``` 代码块"
            )
            skeleton_system = (
                "你是 Lean 4 + Mathlib 证明专家。只输出代码，不要解释。"
                "保留定理陈述中的 import 和 open 语句。"
                "严格按照证明计划写出 tactic 证明。"
                "绝对不要 import 不存在的模块，只能使用用户提供的合法模块列表。"
            )
            skeleton_resp = agent.generate(skeleton_prompt, skeleton_system)
            lean_code = self._extract_lean_code(skeleton_resp.content)
            if not lean_code:
                lean_code = stmt_code

            # 自动修复非法 import
            lean_code, proof_fixes = fix_imports(lean_code)
            if proof_fixes:
                self.session.emit("lean", "info",
                                  "\ud83d\udd27 自动修复 import: " + "; ".join(proof_fixes))

            # 显示证明代码
            self.session.emit("lean", "code", lean_code,
                              "证明代码" if plan_round == 0 else f"证明代码（第 {plan_round + 1} 轮）")

            # ── 5. Lean 验证 ──
            check = lean_env.check_proof(lean_code) if hasattr(lean_env, 'check_proof') else None
            if check and check.get("success"):
                self.session.emit("llm", "success", "✅ 证明成功！")
                self.session.emit("lean", "success", "✅ Lean 编译验证通过")
                self.session.emit("lean", "code", lean_code, "验证通过的完整代码")
                return

            # ── 6. 验证失败 → LLM 分析错误原因 ──
            error_msg = self._get_lean_error(check) if check else "无法检查"
            if not error_msg:
                error_msg = "编译失败（无详细错误信息）"

            self.session.emit("lean", "tactic",
                              f"✗ 第 {plan_round + 1} 轮验证失败",
                              error_msg[:500])

            # 调用 LLM 诊断错误，生成针对性的修改建议
            if plan_round < max_retries - 1:
                diag_prompt = (
                    f"以下 Lean 4 代码未通过编译。请分析错误原因并给出修改建议。\n\n"
                    f"命题：{theorem_statement}\n\n"
                    f"代码：\n```lean\n{lean_code}\n```\n\n"
                    f"Lean 报错：\n{error_msg[:1000]}\n\n"
                    f"请逐条分析每个报错，输出：\n"
                    f"1. **报错位置**：哪一行、哪个表达式\n"
                    f"2. **根因**：为什么报错（如引理不存在、类型不匹配、缺少 import/open 等）\n"
                    f"3. **修正方案**：给出具体的替换代码片段\n"
                    f"4. **对证明计划的影响**：是否需要修改证明路线\n\n"
                    f"简洁输出，不要重复代码全文。"
                )
                diag_system = (
                    "你是 Lean 4 + Mathlib 错误诊断专家。"
                    "逐条分析 Lean 编译报错，给出根因和具体修正方案。简洁明了。"
                )
                diag_resp = agent.generate(diag_prompt, diag_system)
                error_analysis = diag_resp.content.strip()

                # 左面板显示错误分析
                self.session.emit("llm", "info",
                                  f"🔍 第 {plan_round + 1} 轮错误分析：\n{error_analysis}",
                                  "智能体诊断")

            # 保存本轮信息
            prev_plan = proof_plan
            prev_error = error_msg[:1500]
            prev_code = lean_code

        # 所有轮次用完
        self.session.emit("llm", "error", "❌ 证明未通过验证")
        self.session.emit("lean", "error",
                          f"❌ {max_retries} 轮计划迭代均未通过验证",
                          prev_error[:300])


# ═══════════════════════════════════════════════════════════════════════════
# HTTP 服务器
# ═══════════════════════════════════════════════════════════════════════════

# 全局会话存储
_sessions: dict[str, ProofSession] = {}
_session_lock = threading.Lock()


class GaussHandler(SimpleHTTPRequestHandler):
    """处理 API 请求和静态文件"""

    # 静态文件根目录
    STATIC_DIR = Path(__file__).parent / "static"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._serve_file(self.STATIC_DIR / "index.html", "text/html")
        elif path == "/style.css":
            self._serve_file(self.STATIC_DIR / "style.css", "text/css")
        elif path == "/app.js":
            self._serve_file(self.STATIC_DIR / "app.js", "application/javascript")
        elif path == "/api/config":
            self._handle_config()
        elif path.startswith("/api/prove/stream"):
            self._handle_stream(parsed)
        elif path == "/api/health":
            self._json_response({"status": "ok"})
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/prove":
            self._handle_prove()

        else:
            self.send_error(404)

    # ─── API 处理 ───

    def _handle_config(self):
        """返回当前配置"""
        config = _load_config()
        # 不暴露敏感信息
        safe = {
            "llm": {
                "model_name": config.get("llm", {}).get("model_name", "qwen3-coder:30b"),
                "backend": config.get("llm", {}).get("backend", "ollama"),
            },
            "lean": {
                "timeout": config.get("lean", {}).get("timeout", 60),
                "use_mathlib": config.get("lean", {}).get("use_mathlib", True),
            },
            "proof_search": config.get("proof_search", {}),
        }
        self._json_response(safe)

    def _handle_prove(self):
        """启动证明任务，返回 session_id"""
        body = self._read_body()
        theorem = body.get("theorem", "").strip()
        if not theorem:
            self._json_response({"error": "请提供 theorem 参数"}, status=400)
            return

        session_id = f"s_{int(time.time()*1000)}"
        session = ProofSession()

        with _session_lock:
            _sessions[session_id] = session

        config = _load_config()
        prover = StreamingProver(session, config)
        thread = threading.Thread(target=prover.run, args=(theorem,), daemon=True)
        thread.start()

        self._json_response({"session_id": session_id})

    def _handle_stream(self, parsed):
        """SSE 流式推送证明事件"""
        params = parse_qs(parsed.query)
        session_id = params.get("session_id", [None])[0]

        if not session_id:
            self.send_error(400, "缺少 session_id")
            return

        with _session_lock:
            session = _sessions.get(session_id)

        if session is None:
            self.send_error(404, "会话不存在")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            while True:
                try:
                    evt = session.event_queue.get(timeout=120)
                except queue.Empty:
                    # 心跳
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
                    continue

                if evt is None:
                    # 结束信号
                    self.wfile.write(b"data: {\"event_type\":\"done\"}\n\n")
                    self.wfile.flush()
                    break

                sse = evt.to_sse().encode("utf-8")
                self.wfile.write(sse)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            # 清理会话
            with _session_lock:
                _sessions.pop(session_id, None)

    # ─── 工具方法 ───

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _json_response(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, filepath: Path, content_type: str):
        if not filepath.exists():
            self.send_error(404)
            return
        data = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        """简化日志"""
        msg = format % args
        if "/api/prove/stream" not in msg:
            sys.stderr.write(f"[web] {msg}\n")


def _load_config() -> dict:
    config_path = ROOT_DIR / "config.json"
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main():
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    server = HTTPServer(("127.0.0.1", port), GaussHandler)
    print(f"""
    ╔═════════════════════════════════════════════════════════╗
    ║         Gauss Web UI                                    ║
    ║         http://127.0.0.1:{port}                            ║
    ║                                                           ║
    ║   左面板: LLM 推理过程                                    ║
    ║   右面板: Lean 验证过程                                   ║
    ║                                                           ║
    ║   按 Ctrl+C 停止                                          ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ 服务已停止")
        server.server_close()


if __name__ == "__main__":
    main()
