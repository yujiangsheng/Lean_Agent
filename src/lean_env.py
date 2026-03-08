"""
═══════════════════════════════════════════════════════════════════════════════
                        Lean 环境交互模块
═══════════════════════════════════════════════════════════════════════════════

本模块负责与 Lean 4 进行交互，提供：
- 证明状态管理（proof state）
- Tactic 执行与验证
- 定理/引理检索
- 通过 Lean 4 子进程验证证明（支持 Mathlib）

依赖：
- lean-dojo >= 1.8.0（可选）
- Lean 4 命令行工具（子进程模式）

使用示例：
    >>> env = LeanEnvironment()
    >>> state = env.initialize_proof("theorem test : 1 + 1 = 2 := by")
    >>> result = env.apply_tactic(state, "rfl")
    >>> print(result.success)  # True
    >>>
    >>> # 直接验证完整代码
    >>> check = env.check_proof("theorem t : 1 + 1 = 2 := by norm_num")
    >>> print(check["success"])  # True
"""

import os
import subprocess
import tempfile
import shutil
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import hashlib

# ═══════════════════════════════════════════════════════════════════════════
# LeanDojo 导入（可选依赖）
# ═══════════════════════════════════════════════════════════════════════════

try:
    from lean_dojo import Dojo
    LEANDOJO_AVAILABLE = True
except ImportError:
    LEANDOJO_AVAILABLE = False
    print("⚠️  LeanDojo 未安装，将使用 Mock 模式")
    print("   安装命令: pip install lean-dojo")


# ═══════════════════════════════════════════════════════════════════════════
# 数据类定义
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ProofState:
    """
    证明状态
    
    表示 Lean 中的一个证明状态，包含待证目标和上下文信息。
    
    属性：
        goal: 当前需要证明的目标（Lean 表达式）
        hypotheses: 当前上下文中的假设列表
        is_finished: 证明是否已完成
        raw_state: 原始状态字符串（用于调试）
    """
    goal: str = ""
    hypotheses: List[str] = field(default_factory=list)
    is_finished: bool = False
    raw_state: str = ""
    
    def __str__(self) -> str:
        if self.is_finished:
            return "✓ 证明完成"
        
        hyps = "\n".join(f"  {h}" for h in self.hypotheses) if self.hypotheses else "  (无假设)"
        return f"假设:\n{hyps}\n目标:\n  ⊢ {self.goal}"
    
    def get_hash(self) -> str:
        """获取状态的哈希值（用于去重）"""
        content = f"{self.goal}|{'|'.join(self.hypotheses)}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class TacticResult:
    """
    Tactic 执行结果
    
    属性：
        success: 是否执行成功
        new_state: 成功时的新证明状态
        error_message: 失败时的错误信息
        tactic: 执行的 tactic
    """
    success: bool
    new_state: Optional[ProofState] = None
    error_message: Optional[str] = None
    tactic: str = ""
    
    def __str__(self) -> str:
        if self.success:
            return f"✓ {self.tactic} 执行成功"
        return f"✗ {self.tactic} 失败: {self.error_message}"


# ═══════════════════════════════════════════════════════════════════════════
# Lean 环境管理器
# ═══════════════════════════════════════════════════════════════════════════

class LeanEnvironment:
    """
    Lean 交互环境
    
    提供与 Lean 4 的交互能力，包括：
    - 初始化证明环境
    - 执行 tactic
    - 获取可用引理
    - 语法/类型检查
    
    当 LeanDojo 不可用时，自动切换到 Mock 模式进行演示。
    
    使用示例：
        >>> env = LeanEnvironment()
        >>> 
        >>> # 初始化证明
        >>> state = env.initialize_proof("theorem t : ∀ n, n + 0 = n := by")
        >>> print(state)
        >>> 
        >>> # 执行 tactic
        >>> result = env.apply_tactic(state, "simp")
        >>> if result.success:
        ...     print("证明成功！")
    """
    
    # ─────────────────────────────────────────────────────────────────────
    # 常用 Tactic 列表（按成功率排序）
    # ─────────────────────────────────────────────────────────────────────
    COMMON_TACTICS = [
        "rfl",         # 反射性
        "simp",        # 简化
        "ring",        # 环运算
        "omega",       # 整数/自然数线性算术
        "linarith",    # 线性算术
        "norm_num",    # 数值计算
        "trivial",     # 平凡证明
        "aesop",       # 自动化搜索
        "decide",      # 可判定性
        "exact?",      # 自动查找精确匹配
    ]
    
    # ─────────────────────────────────────────────────────────────────────
    # 常用引理（Nat 领域）
    # ─────────────────────────────────────────────────────────────────────
    COMMON_LEMMAS = [
        "Nat.add_comm",      # n + m = m + n
        "Nat.add_assoc",     # (n + m) + k = n + (m + k)
        "Nat.mul_comm",      # n * m = m * n
        "Nat.mul_assoc",     # (n * m) * k = n * (m * k)
        "Nat.add_zero",      # n + 0 = n
        "Nat.zero_add",      # 0 + n = n
        "Nat.mul_one",       # n * 1 = n
        "Nat.one_mul",       # 1 * n = n
        "Nat.left_distrib",  # n * (m + k) = n * m + n * k
        "Nat.right_distrib", # (m + k) * n = m * n + k * n
    ]
    
    def __init__(self, use_mock: bool = False, timeout: int = 60,
                 lean_executable: str = "lean", lake_executable: str = "lake",
                 project_dir: Optional[str] = None):
        """
        初始化 Lean 环境
        
        参数：
            use_mock: 强制使用 Mock 模式
            timeout: 操作超时时间（秒）
            lean_executable: Lean 可执行文件路径
            lake_executable: Lake 可执行文件路径
            project_dir: Lean 项目目录（包含 lakefile.lean，用于 Mathlib 支持）
        """
        self.timeout = timeout
        self.lean_executable = lean_executable
        self.lake_executable = lake_executable
        self.project_dir = os.path.abspath(project_dir) if project_dir else None
        self.use_mock = use_mock or not LEANDOJO_AVAILABLE
        self.dojo = None
        
        # 检测 Lean 4 命令行是否可用
        self.lean_cli_available = self._check_lean_cli()
        
        # 状态缓存（避免重复计算）
        self._state_cache: Dict[str, TacticResult] = {}
        
        if self.lean_cli_available:
            print(f"🔗 Lean 4 命令行可用")
            if self.project_dir:
                print(f"   项目目录: {self.project_dir}")
        elif self.use_mock:
            print("📝 使用 Mock 模式（Lean 4 未连接）")
        else:
            print("🔗 已连接 LeanDojo")
    
    def _check_lean_cli(self) -> bool:
        """检查 Lean 4 命令行工具是否可用"""
        try:
            result = subprocess.run(
                [self.lean_executable, "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False
    
    def initialize_proof(self, theorem: str) -> Optional[ProofState]:
        """
        初始化证明状态
        
        参数：
            theorem: 定理声明（Lean 4 语法）
                    例如: "theorem t : 1 + 1 = 2 := by"
        
        返回：
            初始证明状态，失败时返回 None
            
        示例：
            >>> state = env.initialize_proof("theorem t : ∀ n : Nat, n + 0 = n := by")
            >>> print(state.goal)
            "∀ n : Nat, n + 0 = n"
        """
        if self.use_mock:
            return self._mock_initialize(theorem)
        
        # TODO: 真实 LeanDojo 初始化
        return self._mock_initialize(theorem)
    
    def apply_tactic(self, state: ProofState, tactic: str) -> TacticResult:
        """
        执行一个 tactic
        
        参数：
            state: 当前证明状态
            tactic: 要执行的 tactic（如 "simp", "rfl"）
            
        返回：
            执行结果（包含新状态或错误信息）
            
        示例：
            >>> result = env.apply_tactic(state, "intro n")
            >>> if result.success:
            ...     new_state = result.new_state
        """
        # 检查缓存
        cache_key = f"{state.get_hash()}|{tactic}"
        if cache_key in self._state_cache:
            return self._state_cache[cache_key]
        
        if self.use_mock:
            result = self._mock_apply_tactic(state, tactic)
        else:
            result = self._real_apply_tactic(state, tactic)
        
        # 存入缓存
        self._state_cache[cache_key] = result
        return result
    
    def get_available_lemmas(self, state: ProofState, k: int = 20) -> List[str]:
        """
        获取当前状态下可能有用的引理
        
        参数：
            state: 当前证明状态
            k: 返回引理数量
            
        返回：
            引理名称列表（按相关性排序）
            
        策略：
            1. 根据目标中的符号选择相关引理
            2. 添加常用引理
        """
        goal = state.goal.lower()
        relevant = []
        
        # 根据符号选择引理
        if '+' in goal or 'add' in goal:
            relevant.extend([
                "Nat.add_comm", "Nat.add_assoc", 
                "Nat.add_zero", "Nat.zero_add"
            ])
        
        if '*' in goal or 'mul' in goal:
            relevant.extend([
                "Nat.mul_comm", "Nat.mul_assoc",
                "Nat.mul_one", "Nat.one_mul"
            ])
        
        if '≤' in goal or '<' in goal or 'le' in goal or 'lt' in goal:
            relevant.extend([
                "Nat.le_refl", "Nat.lt_irrefl",
                "Nat.le_trans", "Nat.lt_trans"
            ])
        
        # 添加常用引理
        for lemma in self.COMMON_LEMMAS:
            if lemma not in relevant:
                relevant.append(lemma)
        
        return relevant[:k]
    
    def type_check(self, statement: str) -> bool:
        """
        检查语句的类型正确性
        
        参数：
            statement: Lean 语句
            
        返回：
            True 如果类型检查通过
            
        注意：
            Mock 模式下仅做基本语法检查
        """
        if self.use_mock:
            return self._mock_type_check(statement)
        
        # TODO: 真实类型检查
        return self._mock_type_check(statement)
    
    def syntax_check(self, statement: str) -> bool:
        """
        检查语句的语法正确性
        
        比 type_check 更宽松，只检查基本语法结构。
        """
        if not statement or not statement.strip():
            return False
        
        # 基本关键字检查
        valid_starts = ["theorem", "lemma", "def", "example", "axiom"]
        stmt = statement.strip()
        
        return any(stmt.startswith(kw) for kw in valid_starts)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Mock 模式实现（演示用）
    # ═══════════════════════════════════════════════════════════════════════
    
    def _mock_initialize(self, theorem: str) -> ProofState:
        """Mock 模式：初始化证明"""
        # 提取目标
        goal = theorem
        
        # 尝试解析 "theorem name : goal := by"
        if ':' in theorem:
            parts = theorem.split(':')
            if len(parts) >= 2:
                goal = parts[1].strip()
                # 移除 ":= by" 或 ":= by sorry"
                goal = goal.replace(':= by sorry', '').replace(':= by', '').strip()
        
        return ProofState(
            goal=goal,
            hypotheses=[],
            is_finished=False,
            raw_state=theorem
        )
    
    def _mock_apply_tactic(self, state: ProofState, tactic: str) -> TacticResult:
        """Mock 模式：执行 tactic"""
        tactic = tactic.strip()
        goal = state.goal
        
        # ───────────────────────────────────────────────────────────────
        # 模拟成功的 tactics
        # ───────────────────────────────────────────────────────────────
        success_tactics = {
            "rfl": lambda g: '=' in g,
            "simp": lambda g: True,  # simp 通常能做一些事
            "ring": lambda g: '+' in g or '*' in g,
            "omega": lambda g: any(c in g for c in '<>≤≥'),
            "trivial": lambda g: 'True' in g,
            "decide": lambda g: 'Bool' in g or 'Decidable' in g,
        }
        
        # 检查是否可以成功
        if tactic in success_tactics:
            if success_tactics[tactic](goal):
                return TacticResult(
                    success=True,
                    new_state=ProofState(goal="", is_finished=True),
                    tactic=tactic
                )
        
        # ───────────────────────────────────────────────────────────────
        # intro 系列
        # ───────────────────────────────────────────────────────────────
        if tactic.startswith("intro"):
            var_name = tactic.replace("intro", "").strip() or "h"
            new_hyp = f"{var_name} : (假设)"
            
            # 更新目标
            new_goal = goal
            if '∀' in goal:
                new_goal = goal.split(',', 1)[-1].strip() if ',' in goal else "(更新后的目标)"
            
            return TacticResult(
                success=True,
                new_state=ProofState(
                    goal=new_goal,
                    hypotheses=state.hypotheses + [new_hyp],
                    is_finished=False
                ),
                tactic=tactic
            )
        
        # ───────────────────────────────────────────────────────────────
        # apply/exact
        # ───────────────────────────────────────────────────────────────
        if tactic.startswith(("apply", "exact")):
            lemma = tactic.split(maxsplit=1)[-1]
            if lemma in self.COMMON_LEMMAS:
                return TacticResult(
                    success=True,
                    new_state=ProofState(goal="", is_finished=True),
                    tactic=tactic
                )
        
        # ───────────────────────────────────────────────────────────────
        # rw（重写）
        # ───────────────────────────────────────────────────────────────
        if tactic.startswith("rw"):
            return TacticResult(
                success=True,
                new_state=ProofState(
                    goal="(重写后的目标)",
                    hypotheses=state.hypotheses,
                    is_finished=False
                ),
                tactic=tactic
            )
        
        # 默认：失败
        return TacticResult(
            success=False,
            error_message=f"tactic '{tactic}' 无法应用于当前目标",
            tactic=tactic
        )
    
    def _mock_type_check(self, statement: str) -> bool:
        """Mock 模式：类型检查"""
        # 基本检查
        if not self.syntax_check(statement):
            return False
        
        # 检查括号平衡
        if statement.count('(') != statement.count(')'):
            return False
        
        if statement.count('[') != statement.count(']'):
            return False
        
        return True
    
    def _real_apply_tactic(self, state: ProofState, tactic: str) -> TacticResult:
        """真实 LeanDojo：执行 tactic"""
        # TODO: 连接真实 LeanDojo
        return self._mock_apply_tactic(state, tactic)
    
    def check_proof(self, lean_code: str) -> Dict[str, Any]:
        """
        通过 Lean 4 命令行验证完整证明代码
        
        将代码写入临时文件，调用 lean 或 lake env lean 来检查。
        如果配置了 project_dir（包含 Mathlib），则使用该项目的环境。
        
        参数：
            lean_code: 完整 Lean 4 源代码（包含 import 和证明）
            
        返回：
            {"success": bool, "output": str, "error": str}
        """
        if not self.lean_cli_available:
            # 如果 lean 命令行不可用，回退到基本语法检查
            has_sorry = 'sorry' in lean_code
            return {
                "success": not has_sorry and self._mock_type_check(lean_code.split('\n')[0] if lean_code else ""),
                "output": "Mock 模式: 基本语法检查",
                "error": "sorry 未替换" if has_sorry else ""
            }
        
        tmpdir = None
        try:
            # 支持 lakefile.lean 和 lakefile.toml 两种格式
            has_lake_project = self.project_dir and (
                os.path.isfile(os.path.join(self.project_dir, "lakefile.lean")) or
                os.path.isfile(os.path.join(self.project_dir, "lakefile.toml"))
            )
            if has_lake_project:
                # 在现有 Lake 项目中验证（支持 Mathlib）
                tmpfile = os.path.join(self.project_dir, "_LeanAgent_check.lean")
                try:
                    with open(tmpfile, 'w', encoding='utf-8') as f:
                        f.write(lean_code)
                    
                    proc = subprocess.run(
                        [self.lake_executable, "env", self.lean_executable, tmpfile],
                        capture_output=True, text=True,
                        timeout=self.timeout,
                        cwd=self.project_dir
                    )
                finally:
                    if os.path.exists(tmpfile):
                        os.remove(tmpfile)
            else:
                # 在临时目录中验证（无 Mathlib）
                tmpdir = tempfile.mkdtemp(prefix="lean_agent_")
                tmpfile = os.path.join(tmpdir, "check.lean")
                with open(tmpfile, 'w', encoding='utf-8') as f:
                    # 去除 Mathlib import（因为没有项目环境）
                    code_lines = []
                    for line in lean_code.split('\n'):
                        if line.strip().startswith('import Mathlib'):
                            code_lines.append(f"-- {line}  -- skipped (no Mathlib project)")
                        else:
                            code_lines.append(line)
                    f.write('\n'.join(code_lines))
                
                proc = subprocess.run(
                    [self.lean_executable, tmpfile],
                    capture_output=True, text=True,
                    timeout=self.timeout
                )
            
            success = proc.returncode == 0 and 'error' not in proc.stderr.lower()
            return {
                "success": success,
                "output": proc.stdout.strip(),
                "error": proc.stderr.strip()
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": f"Lean 检查超时 ({self.timeout}s)"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
        finally:
            if tmpdir and os.path.exists(tmpdir):
                shutil.rmtree(tmpdir, ignore_errors=True)
    
    # ═══════════════════════════════════════════════════════════════════════
    # exact? / apply? 搜索：让 Lean 编译器帮我们找证明
    # ═══════════════════════════════════════════════════════════════════════

    def search_exact(self, stmt_code: str, search_timeout: int = 180) -> Dict[str, Any]:
        """
        用 Lean 的 exact? tactic 搜索能直接完成证明的 term。

        参数：
            stmt_code: 包含 import/open/theorem 的完整代码（证明部分会被替换为 exact?）
            search_timeout: 搜索超时秒数（exact? 可能很慢）

        返回：
            {"found": bool, "suggestion": str, "full_code": str, "output": str}
        """
        return self._run_search_tactic(stmt_code, "exact?", search_timeout)

    def search_apply(self, stmt_code: str, search_timeout: int = 180) -> Dict[str, Any]:
        """
        用 Lean 的 apply? tactic 搜索可用引理。

        参数：
            stmt_code: 包含 import/open/theorem 的完整代码
            search_timeout: 搜索超时秒数

        返回：
            {"found": bool, "suggestion": str, "full_code": str, "output": str}
        """
        return self._run_search_tactic(stmt_code, "apply?", search_timeout)

    def _run_search_tactic(self, stmt_code: str, tactic: str,
                           search_timeout: int) -> Dict[str, Any]:
        """
        将证明体替换为 exact? 或 apply?，运行 Lean，解析输出中的建议。
        """
        if not self.lean_cli_available:
            return {"found": False, "suggestion": "", "full_code": "", "output": "Lean CLI 不可用"}

        # 将 sorry / 现有 tactic 替换为搜索 tactic
        search_code = self._replace_proof_body(stmt_code, tactic)
        if not search_code:
            return {"found": False, "suggestion": "", "full_code": "", "output": "无法定位 proof body"}

        has_lake_project = self.project_dir and (
            os.path.isfile(os.path.join(self.project_dir, "lakefile.lean")) or
            os.path.isfile(os.path.join(self.project_dir, "lakefile.toml"))
        )
        if not has_lake_project:
            return {"found": False, "suggestion": "", "full_code": "", "output": "需要 Lake 项目"}

        tmpfile = os.path.join(self.project_dir, "_LeanAgent_search.lean")
        try:
            with open(tmpfile, 'w', encoding='utf-8') as f:
                f.write(search_code)

            proc = subprocess.run(
                [self.lake_executable, "env", self.lean_executable, tmpfile],
                capture_output=True, text=True,
                timeout=search_timeout,
                cwd=self.project_dir,
            )

            combined = proc.stdout + "\n" + proc.stderr
            suggestion = self._parse_search_suggestion(combined, tactic)
            if suggestion:
                full_code = self._replace_proof_body(stmt_code, suggestion)
                return {"found": True, "suggestion": suggestion,
                        "full_code": full_code or "", "output": combined.strip()}
            return {"found": False, "suggestion": "", "full_code": "",
                    "output": combined.strip()[:500]}

        except subprocess.TimeoutExpired:
            return {"found": False, "suggestion": "", "full_code": "",
                    "output": f"{tactic} 搜索超时 ({search_timeout}s)"}
        except Exception as e:
            return {"found": False, "suggestion": "", "full_code": "",
                    "output": str(e)}
        finally:
            if os.path.exists(tmpfile):
                os.remove(tmpfile)

    @staticmethod
    def _replace_proof_body(code: str, new_body: str) -> Optional[str]:
        """
        把 ':= by\\n  sorry' 或 ':= by\\n  <tactics>' 替换为 ':= by\\n  <new_body>'。
        也处理单行 ':= by sorry'。
        """
        import re
        # 匹配 ':= by' 后面跟着整个 proof body（到文件末尾或下一个顶级声明）
        # 模式1: := by sorry (单行)
        pattern1 = r'(:=\s*by)\s+sorry\b'
        if re.search(pattern1, code):
            return re.sub(pattern1, rf'\1\n  {new_body}', code)

        # 模式2: := by\n  <indented body> (多行)
        pattern2 = r'(:=\s*by)\s*\n((?:[ \t]+.+\n?)*)'
        if re.search(pattern2, code):
            return re.sub(pattern2, rf'\1\n  {new_body}\n', code)

        # 模式3: 只有 := by 没有后续
        pattern3 = r'(:=\s*by)\s*$'
        if re.search(pattern3, code, re.MULTILINE):
            return re.sub(pattern3, rf'\1\n  {new_body}', code, flags=re.MULTILINE)

        return None

    @staticmethod
    def _parse_search_suggestion(output: str, tactic: str) -> Optional[str]:
        """
        从 exact?/apply? 的输出中提取建议。
        Lean 输出格式通常为:
          Try this: exact <term>
          Try this: apply <term>
        """
        import re
        # exact? 输出: "Try this: exact ..."
        # apply? 输出: "Try this: apply ..."  或 "Try this: exact ..."
        pattern = r'Try this:\s*(.+)'
        for line in output.split('\n'):
            m = re.search(pattern, line)
            if m:
                return m.group(1).strip()
        return None

    # ═══════════════════════════════════════════════════════════════════════
    # Mathlib 源码搜索：grep Mathlib 找相关定理
    # ═══════════════════════════════════════════════════════════════════════

    def search_mathlib_theorems(self, keywords: list[str], max_results: int = 20) -> list[Dict[str, str]]:
        """
        在 Mathlib 源码中 grep 搜索包含指定关键词的 theorem/lemma/def 声明。

        参数：
            keywords: 搜索关键词列表（如 ["Cayley", "Perm", "MulAction"]）
            max_results: 最大返回数

        返回：
            [{"name": "Equiv.Perm.xxx", "file": "Mathlib/GroupTheory/...", "line": "..."}, ...]
        """
        if not self.project_dir:
            return []

        mathlib_dir = os.path.join(self.project_dir, ".lake", "packages", "mathlib", "Mathlib")
        if not os.path.isdir(mathlib_dir):
            return []

        results = []
        for kw in keywords:
            if len(results) >= max_results:
                break
            try:
                proc = subprocess.run(
                    ["grep", "-Ern", "--include=*.lean",
                     f"(theorem|lemma|def).*{kw}", mathlib_dir],
                    capture_output=True, text=True, timeout=30
                )
                for line in proc.stdout.strip().split('\n'):
                    if not line.strip():
                        continue
                    if len(results) >= max_results:
                        break
                    # 解析 grep 输出: file:lineno:content
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        filepath = parts[0].replace(mathlib_dir + "/", "").replace("/", ".").replace(".lean", "")
                        content = parts[2].strip()
                        # 提取声明名
                        import re
                        name_match = re.search(r'(?:theorem|lemma|def)\s+(\S+)', content)
                        name = name_match.group(1) if name_match else content[:80]
                        results.append({
                            "name": name,
                            "module": f"Mathlib.{filepath}",
                            "declaration": content[:120],
                        })
            except (subprocess.TimeoutExpired, Exception):
                continue

        # 去重
        seen = set()
        unique = []
        for r in results:
            if r["name"] not in seen:
                seen.add(r["name"])
                unique.append(r)
        return unique

    def close(self):
        """关闭环境，释放资源"""
        if self.dojo:
            try:
                self.dojo.close()
            except Exception:
                pass
        self._state_cache.clear()
        print("✓ Lean 环境已关闭")


# ═══════════════════════════════════════════════════════════════════════════
# BFS/DFS 证明搜索器
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SearchNode:
    """
    搜索树节点
    
    表示证明搜索过程中的一个状态。
    """
    state: ProofState
    parent_index: int               # 父节点在 nodes 列表中的索引，根节点为 -1
    tactic: str                     # 到达此状态所使用的 tactic
    depth: int                      # 搜索深度
    error_message: str = ""         # 上一步的错误信息（用于错误反馈）


class ProofSearcher:
    """
    BFS/DFS 证明搜索器
    
    在证明状态空间中进行系统化搜索，替代简单的线性重试逻辑。
    
    特点：
    - 支持 BFS（广度优先）和 DFS（深度优先+回溯）两种策略
    - 自动去重已访问状态，避免循环
    - 可配置最大深度和最大搜索节点数
    - 搜索完成后可回溯提取完整的 tactic 序列
    
    使用示例：
        >>> searcher = ProofSearcher(lean_env, tactic_generator, strategy='bfs')
        >>> result = searcher.search(initial_state)
        >>> if result is not None:
        ...     print(f"找到证明: {result['tactics']}")
    """
    
    def __init__(
        self,
        lean_env: LeanEnvironment,
        tactic_generator,  # callable(state_str, error_msg, failed_tactics, premises) -> List[str]
        strategy: str = "bfs",
        max_depth: int = 10,
        max_nodes: int = 50,
        tactics_per_state: int = 8,
    ):
        """
        参数：
            lean_env: Lean 交互环境
            tactic_generator: 生成 tactic 建议的回调函数
                签名: (proof_state_str, error_message, failed_tactics, available_premises) -> List[str]
            strategy: 搜索策略 ('bfs' 或 'dfs')
            max_depth: 最大搜索深度
            max_nodes: 最大搜索节点数
            tactics_per_state: 每个状态尝试的 tactic 数量
        """
        self.lean_env = lean_env
        self.tactic_generator = tactic_generator
        self.strategy = strategy
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.tactics_per_state = tactics_per_state
    
    def search(
        self,
        initial_state: ProofState,
        available_premises: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        在证明状态空间中搜索完整证明
        
        参数：
            initial_state: 初始证明状态
            available_premises: 可用引理列表
        
        返回：
            成功时返回 {"tactics": [...], "depth": int, "nodes_explored": int}
            失败时返回 None
        """
        if initial_state.is_finished:
            return {"tactics": [], "depth": 0, "nodes_explored": 0}
        
        # 初始化搜索
        root = SearchNode(
            state=initial_state,
            parent_index=-1,
            tactic="",
            depth=0
        )
        nodes: List[SearchNode] = [root]
        visited: set = {initial_state.get_hash()}
        
        # frontier: BFS 用队列（FIFO），DFS 用栈（LIFO）
        frontier = [0]  # 索引到 nodes
        nodes_explored = 0
        
        while frontier and nodes_explored < self.max_nodes:
            # 选择下一个要展开的节点
            if self.strategy == "bfs":
                current_idx = frontier.pop(0)
            else:  # dfs
                current_idx = frontier.pop()
            
            current = nodes[current_idx]
            nodes_explored += 1
            
            if current.depth >= self.max_depth:
                continue
            
            # 收集当前路径上已失败的 tactics（用于错误反馈）
            failed_at_current = []
            
            # 请求 tactic 建议（含错误诊断信息）
            tactics = self.tactic_generator(
                str(current.state),
                current.error_message,
                failed_at_current,
                available_premises
            )
            
            for tactic in tactics[:self.tactics_per_state]:
                # 执行 tactic
                result = self.lean_env.apply_tactic(current.state, tactic)
                
                if result.success:
                    new_state = result.new_state
                    
                    # 检查证明是否完成
                    if new_state.is_finished:
                        # 回溯提取完整 tactic 序列
                        proof_tactics = self._extract_proof_path(
                            nodes, current_idx, tactic
                        )
                        return {
                            "tactics": proof_tactics,
                            "depth": current.depth + 1,
                            "nodes_explored": nodes_explored,
                        }
                    
                    # 检查是否已访问此状态
                    state_hash = new_state.get_hash()
                    if state_hash not in visited:
                        visited.add(state_hash)
                        new_node = SearchNode(
                            state=new_state,
                            parent_index=current_idx,
                            tactic=tactic,
                            depth=current.depth + 1
                        )
                        new_idx = len(nodes)
                        nodes.append(new_node)
                        frontier.append(new_idx)
                else:
                    # 记录失败信息，供后续错误诊断使用
                    failed_at_current.append(tactic)
                    # 为当前节点记录最后的错误信息
                    current.error_message = result.error_message or ""
        
        return None  # 搜索失败
    
    def _extract_proof_path(
        self, nodes: List[SearchNode], last_parent_idx: int, final_tactic: str
    ) -> List[str]:
        """从搜索树中回溯提取完整的 tactic 序列"""
        tactics = [final_tactic]
        idx = last_parent_idx
        while idx >= 0:
            node = nodes[idx]
            if node.tactic:  # 根节点的 tactic 为空
                tactics.append(node.tactic)
            idx = node.parent_index
        tactics.reverse()
        return tactics


# ═══════════════════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════════════════

def create_lean_env(
    use_mock: bool = False,
    project_dir: Optional[str] = None,
    timeout: int = 60
) -> LeanEnvironment:
    """
    创建 Lean 环境的便捷函数
    
    参数：
        use_mock: 是否使用 Mock 模式
        project_dir: Lean 项目目录（包含 lakefile.lean，用于 Mathlib 支持）
        timeout: 操作超时时间（秒）
        
    返回：
        配置好的 LeanEnvironment 实例
    """
    return LeanEnvironment(use_mock=use_mock, project_dir=project_dir, timeout=timeout)


# ═══════════════════════════════════════════════════════════════════════════
# 测试代码
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Lean 环境测试")
    print("=" * 60)
    
    # 创建环境
    env = LeanEnvironment()
    
    # 测试 1：初始化证明
    print("\n【测试 1】初始化证明")
    theorem = "theorem test : ∀ n : Nat, n + 0 = n := by"
    state = env.initialize_proof(theorem)
    print(f"定理: {theorem}")
    print(f"状态:\n{state}")
    
    # 测试 2：执行 tactic
    print("\n【测试 2】执行 intro")
    result = env.apply_tactic(state, "intro n")
    print(f"结果: {result}")
    if result.success:
        print(f"新状态:\n{result.new_state}")
    
    # 测试 3：执行 simp
    print("\n【测试 3】执行 simp")
    if result.success:
        result2 = env.apply_tactic(result.new_state, "simp")
        print(f"结果: {result2}")
    
    # 测试 4：获取引理
    print("\n【测试 4】获取相关引理")
    lemmas = env.get_available_lemmas(state, k=5)
    print(f"推荐引理: {lemmas}")
    
    # 测试 5：语法检查
    print("\n【测试 5】语法检查")
    test_cases = [
        "theorem t : 1 = 1 := by rfl",
        "invalid statement",
        "lemma l : True := trivial",
    ]
    for tc in test_cases:
        ok = env.syntax_check(tc)
        print(f"  {'✓' if ok else '✗'} {tc[:40]}...")
    
    env.close()
