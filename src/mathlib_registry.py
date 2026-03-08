"""
═════════════════════════════════════════════════════════════
        Mathlib 模块注册表 (Mathlib Module Registry)
═════════════════════════════════════════════════════════════

从 data/mathlib_modules.txt 加载所有有效 Mathlib 模块名，提供：
Loads valid Mathlib module names and provides:
  1. import 合法性验证 (Validate imports)
  2. 模糊匹配推荐 (Fuzzy matching suggestions)
  3. 主题关键词查找 (Topic-based module search)
  4. 非法 import 自动修复 (Auto-fix deprecated imports)
  5. 黄金证明模板 (Golden proof templates)

作者 (Author): Jiangsheng Yu
版本 (Version): 3.0.0
"""

import re
from pathlib import Path
from functools import lru_cache
from difflib import get_close_matches
from typing import Optional


_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "mathlib_modules.txt"

# ── 旧模块名 → 新模块名映射（Mathlib 重组后，许多路径变化，LLM 训练数据中的旧路径需要映射） ──
# 格式："旧.模块.路径" → "新.模块.路径"
# 支持精确映射和前缀映射（以 "*" 结尾表示前缀）
DEPRECATED_MODULES: dict[str, str] = {
    # ── Subgroup: GroupTheory.Subgroup.* → Algebra.Group.Subgroup.* ──
    "Mathlib.GroupTheory.Subgroup.Basic":         "Mathlib.Algebra.Group.Subgroup.Basic",
    "Mathlib.GroupTheory.Subgroup.Defs":          "Mathlib.Algebra.Group.Subgroup.Defs",
    "Mathlib.GroupTheory.Subgroup.Pointwise":     "Mathlib.Algebra.Group.Pointwise.Finset.Basic",
    "Mathlib.GroupTheory.Subgroup.Actions":       "Mathlib.Algebra.Group.Subgroup.Actions",
    "Mathlib.GroupTheory.Subgroup.Finite":        "Mathlib.Algebra.Group.Subgroup.Finite",
    "Mathlib.GroupTheory.Subgroup.MulOpposite":   "Mathlib.Algebra.Group.Subgroup.MulOpposite",
    # ── Submonoid: GroupTheory.Submonoid.* → Algebra.Group.Submonoid.* ──
    "Mathlib.GroupTheory.Submonoid.Basic":        "Mathlib.Algebra.Group.Submonoid.Basic",
    "Mathlib.GroupTheory.Submonoid.Defs":         "Mathlib.Algebra.Group.Submonoid.Defs",
    "Mathlib.GroupTheory.Submonoid.Operations":   "Mathlib.Algebra.Group.Submonoid.Operations",
    # ── Subring: RingTheory.Subring.* → Algebra.Ring.Subring.* ──
    "Mathlib.RingTheory.Subring.Basic":           "Mathlib.Algebra.Ring.Subring.Basic",
    "Mathlib.RingTheory.Subring.Defs":            "Mathlib.Algebra.Ring.Subring.Defs",
    # ── Ideal: RingTheory.Ideal.* stays mostly but some moved ──
    "Mathlib.RingTheory.Ideal.Defs":              "Mathlib.RingTheory.Ideal.Defs",
    # ── LinearAlgebra 重组 ──
    "Mathlib.LinearAlgebra.Matrix.CharacteristicPolynomial": "Mathlib.LinearAlgebra.Matrix.Charpoly.Basic",
    "Mathlib.LinearAlgebra.Basic":                "Mathlib.LinearAlgebra.Span.Defs",
    "Mathlib.LinearAlgebra.Span":                 "Mathlib.LinearAlgebra.Span.Defs",
    "Mathlib.LinearAlgebra.Dimension":            "Mathlib.LinearAlgebra.Dimension.Constructions",
    "Mathlib.LinearAlgebra.FiniteDimensional":    "Mathlib.LinearAlgebra.Dimension.Finite",
    # ── Equiv: Data.Equiv.* → Logic.Equiv.* 或合并到其他模块 ──
    "Mathlib.Data.Equiv.Basic":                   "Mathlib.Logic.Equiv.Defs",
    "Mathlib.Data.Equiv.Perm":                    "Mathlib.GroupTheory.Perm.Basic",
    "Mathlib.Data.Equiv.Fin":                     "Mathlib.Logic.Equiv.Fin.Basic",
    "Mathlib.Data.Equiv.Ring":                    "Mathlib.Algebra.BigOperators.RingEquiv",
    "Mathlib.Logic.Equiv.Basic":                  "Mathlib.Logic.Equiv.Defs",
    # ── Analysis 重组 ──
    "Mathlib.Analysis.SpecialFunctions.Trigonometric":      "Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic",
    "Mathlib.Analysis.SpecialFunctions.Trigonometrics.Basic": "Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic",
    "Mathlib.Analysis.SpecialFunctions.Log":      "Mathlib.Analysis.SpecialFunctions.Log.Basic",
    "Mathlib.Analysis.SpecialFunctions.Exp":      "Mathlib.Analysis.SpecialFunctions.ExpDeriv",
    "Mathlib.Analysis.SpecialFunctions.Pow":      "Mathlib.Analysis.SpecialFunctions.Pow.Real",
    # ── Topology.Algebra 重组 ──
    "Mathlib.Topology.Algebra.Group":             "Mathlib.Topology.Algebra.Group.Basic",
    "Mathlib.Topology.Algebra.Ring":              "Mathlib.Topology.Algebra.Ring.Basic",
    "Mathlib.Topology.Algebra.Field":             "Mathlib.Topology.Algebra.Field",
    "Mathlib.Topology.Algebra.Module":            "Mathlib.Topology.Algebra.Module.Basic",
    # ── Algebra misc ──
    "Mathlib.Algebra.GroupPower.Basic":            "Mathlib.Algebra.GroupWithZero.Units.Lemmas",
    "Mathlib.Algebra.GeomSum":                    "Mathlib.Algebra.Ring.GeomSum",
    "Mathlib.Algebra.BigOperators.Basic":          "Mathlib.Algebra.BigOperators.Group.Finset.Basic",
    "Mathlib.Algebra.BigOperators.NatAntitone":    "Mathlib.Algebra.BigOperators.Group.Finset.Basic",
    # ── Data 重组 ──
    "Mathlib.Data.Nat.Parity":                    "Mathlib.Algebra.Ring.Parity",
    "Mathlib.Data.Nat.Factorial":                 "Mathlib.Data.Nat.Factorial.Basic",
    "Mathlib.Data.Polynomial.Basic":              "Mathlib.Algebra.Polynomial.Basic",
    "Mathlib.Data.Polynomial.Eval":               "Mathlib.Algebra.Polynomial.Eval.Defs",
    "Mathlib.Data.Polynomial.Degree.Basic":        "Mathlib.Algebra.Polynomial.Degree.Definitions",
    "Mathlib.Data.Rat.Basic":                      "Mathlib.Data.Rat.Defs",
}

# ── 前缀映射（用于整个目录的重命名） ──
DEPRECATED_PREFIXES: list[tuple[str, str]] = [
    ("Mathlib.GroupTheory.Subgroup.",   "Mathlib.Algebra.Group.Subgroup."),
    ("Mathlib.GroupTheory.Submonoid.",  "Mathlib.Algebra.Group.Submonoid."),
    ("Mathlib.RingTheory.Subring.",     "Mathlib.Algebra.Ring.Subring."),
    ("Mathlib.Data.Equiv.",             "Mathlib.Logic.Equiv."),
    ("Mathlib.Data.Polynomial.",        "Mathlib.Algebra.Polynomial."),
]

# ── 主题 → 关键词映射（用于从 7000+ 模块中筛选与当前证明最相关的子集） ──
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "自然数":     ["Nat", "Data.Nat", "Mathlib.Data.Nat"],
    "整数":       ["Int", "Data.Int", "Mathlib.Data.Int"],
    "有理数":     ["Rat", "Data.Rat", "Mathlib.Data.Rat"],
    "实数":       ["Real", "Analysis.SpecificLimits", "Mathlib.Analysis.SpecialFunctions",
                   "Mathlib.Data.Real", "Mathlib.Topology.Algebra"],
    "复数":       ["Complex", "Mathlib.Analysis.SpecialFunctions.Complex"],
    "素数":       ["Prime", "Nat.Prime", "Data.Nat.Prime", "Mathlib.Data.Nat.Prime"],
    "整除":       ["Dvd", "Divisors", "Data.Nat.GCD", "Mathlib.Data.Nat.GCD",
                   "Mathlib.Data.Nat.Factorial"],
    "奇偶":       ["Parity", "Even", "Odd", "Mathlib.Data.Nat.Parity",
                   "Mathlib.Algebra.Parity"],
    "模运算":     ["Mod", "ZMod", "Mathlib.Data.ZMod"],
    "集合":       ["Set", "Finset", "Mathlib.Data.Set", "Mathlib.Data.Finset",
                   "Mathlib.Order.Filter"],
    "列表":       ["List", "Mathlib.Data.List"],
    "函数":       ["Function", "Mathlib.Logic.Function"],
    "逻辑":       ["Logic", "Mathlib.Logic", "Mathlib.Init"],
    "等式":       ["Eq", "Mathlib.Tactic.Ring", "Mathlib.Tactic.Linarith",
                   "Mathlib.Tactic.NormNum"],
    "不等式":     ["Inequality", "Mathlib.Tactic.Linarith", "Mathlib.Tactic.Positivity",
                   "Mathlib.Tactic.NormNum", "Mathlib.Analysis.MeanInequalities"],
    "极限":       ["Limit", "Filter", "Tendsto", "Mathlib.Topology.Order",
                   "Mathlib.Topology.Basic", "Mathlib.Order.Filter"],
    "连续":       ["Continuous", "Mathlib.Topology.ContinuousOn",
                   "Mathlib.Topology.Basic"],
    "微分":       ["Deriv", "HasDeriv", "Mathlib.Analysis.Calculus.Deriv",
                   "Mathlib.Analysis.Calculus.MeanValue"],
    "积分":       ["Integral", "MeasureTheory.Integral",
                   "Mathlib.MeasureTheory.Integral"],
    "级数":       ["Series", "Summable", "HasSum", "tsum",
                   "Mathlib.Topology.Algebra.InfiniteSum"],
    "线性代数":   ["Matrix", "LinearMap", "Mathlib.LinearAlgebra",
                   "Mathlib.Data.Matrix"],
    "多项式":     ["Polynomial", "Mathlib.RingTheory.Polynomial",
                   "Mathlib.Data.Polynomial"],
    "群":         ["Group", "Mathlib.GroupTheory", "Mathlib.Algebra.Group"],
    "环":         ["Ring", "Mathlib.RingTheory", "Mathlib.Algebra.Ring"],
    "域":         ["Field", "Mathlib.FieldTheory", "Mathlib.Algebra.Field"],
    "拓扑":       ["Topology", "Mathlib.Topology"],
    "度量空间":   ["Metric", "Mathlib.Topology.MetricSpace"],
    "组合":       ["Combinatorics", "Mathlib.Combinatorics",
                   "Mathlib.Data.Nat.Choose"],
    "概率":       ["Probability", "Mathlib.Probability"],
    "数论":       ["NumberTheory", "Mathlib.NumberTheory"],
    "范数":       ["Norm", "NormedSpace", "Mathlib.Analysis.Normed"],
    "序":         ["Order", "Lattice", "Mathlib.Order"],
    "有限":       ["Finite", "Fintype", "Mathlib.Data.Fintype"],
    "tactic":     ["Mathlib.Tactic"],
}


@lru_cache(maxsize=1)
def _load_modules() -> frozenset[str]:
    """加载并缓存所有合法 Mathlib 模块名"""
    if not _DATA_FILE.exists():
        return frozenset()
    with open(_DATA_FILE, "r") as f:
        return frozenset(line.strip() for line in f if line.strip())


@lru_cache(maxsize=1)
def _load_module_list() -> list[str]:
    """返回排序后的模块列表（供 difflib 使用）"""
    return sorted(_load_modules())


def is_valid_module(module_name: str) -> bool:
    """检查模块名是否合法"""
    return module_name in _load_modules()


def suggest_module(module_name: str, n: int = 5, cutoff: float = 0.6) -> list[str]:
    """对非法模块名做模糊匹配，返回最相似的合法模块"""
    modules = _load_module_list()
    return get_close_matches(module_name, modules, n=n, cutoff=cutoff)


def validate_imports(code: str) -> list[dict]:
    """
    验证代码中所有 import 语句。
    返回: [{"module": str, "valid": bool, "suggestions": list[str]}, ...]
    """
    results = []
    for line in code.split("\n"):
        line = line.strip()
        if not line.startswith("import "):
            continue
        module = line[len("import "):].strip()
        valid = is_valid_module(module)
        suggestions = [] if valid else suggest_module(module)
        results.append({"module": module, "valid": valid, "suggestions": suggestions})
    return results


def _resolve_deprecated(module: str) -> Optional[str]:
    """
    尝试通过 deprecated 映射表修复旧模块名。
    先查精确映射，再查前缀映射，最后验证结果是否有效。
    """
    # 1) 精确映射
    if module in DEPRECATED_MODULES:
        target = DEPRECATED_MODULES[module]
        if is_valid_module(target):
            return target

    # 2) 前缀映射
    for old_prefix, new_prefix in DEPRECATED_PREFIXES:
        if module.startswith(old_prefix):
            suffix = module[len(old_prefix):]
            candidate = new_prefix + suffix
            if is_valid_module(candidate):
                return candidate

    return None


def _resolve_directory_module(module: str) -> Optional[str]:
    """
    当模块名对应一个目录而非文件时，解析为正确的子模块。
    例如 Mathlib.GroupTheory.Perm → Mathlib.GroupTheory.Perm.Basic
    """
    modules = _load_modules()
    prefix = module + "."
    children = [m for m in modules if m.startswith(prefix)]
    if not children:
        return None
    # 优先选 .Basic
    basic = module + ".Basic"
    if basic in modules:
        return basic
    # 否则选最短的子模块（最可能是主模块）
    return min(children, key=len)


def fix_imports(code: str) -> tuple[str, list[str]]:
    """
    自动修复代码中的非法 import：
    优先级：
      1. 合法 → 保留
      2. 在 deprecated 映射表中 → 按映射替换
      2.5. 目录名 → 解析为 .Basic 子模块
      3. 模糊匹配 → 替换为最佳匹配
      4. 截断到父模块 → 替换
      5. 完全无法匹配 → 删除并记录
    返回: (修复后代码, 修改日志列表)
    """
    lines = code.split("\n")
    fixed_lines = []
    changes = []

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("import "):
            fixed_lines.append(line)
            continue

        module = stripped[len("import "):].strip()
        if is_valid_module(module):
            fixed_lines.append(line)
            continue

        # 策略 1: deprecated 映射
        mapped = _resolve_deprecated(module)
        if mapped:
            fixed_lines.append(f"import {mapped}")
            changes.append(f"import {module} → import {mapped} (重命名映射)")
            continue

        # 策略 1.5: 目录名解析（如 Perm → Perm.Basic）
        dir_resolved = _resolve_directory_module(module)
        if dir_resolved:
            fixed_lines.append(f"import {dir_resolved}")
            changes.append(f"import {module} → import {dir_resolved} (目录→子模块)")
            continue

        # 策略 2: 模糊匹配
        suggestions = suggest_module(module)
        if suggestions:
            best = suggestions[0]
            fixed_lines.append(f"import {best}")
            changes.append(f"import {module} → import {best}")
            continue

        # 策略 3: 截断到父模块
        parent = _find_valid_parent(module)
        if parent:
            fixed_lines.append(f"import {parent}")
            changes.append(f"import {module} → import {parent} (父模块)")
        else:
            changes.append(f"import {module} → 已删除（无匹配）")

    return "\n".join(fixed_lines), changes


def _find_valid_parent(module: str) -> Optional[str]:
    """向上查找最近的合法父模块"""
    parts = module.split(".")
    for i in range(len(parts) - 1, 0, -1):
        candidate = ".".join(parts[:i])
        if is_valid_module(candidate):
            return candidate
    return None


def find_modules_by_topic(theorem_text: str, max_per_topic: int = 15) -> list[str]:
    """
    根据定理文本中的关键词，从注册表查找最可能需要的模块。
    返回去重排序的模块列表。
    """
    modules = _load_modules()
    result_set: set[str] = set()

    # 先检查定理专属模块
    for modules_needed in _find_theorem_specific_modules(theorem_text):
        if modules_needed in modules:
            result_set.add(modules_needed)

    for topic, keywords in TOPIC_KEYWORDS.items():
        # 检查定理文本是否包含该主题
        if topic not in theorem_text:
            # 也检查英文关键词
            if not any(kw.lower() in theorem_text.lower() for kw in keywords[:3]):
                continue

        # 根据关键词筛选模块
        count = 0
        for kw in keywords:
            if count >= max_per_topic:
                break
            for m in modules:
                if count >= max_per_topic:
                    break
                if kw in m:
                    result_set.add(m)
                    count += 1

    return sorted(result_set)


# ── 定理专属模块映射：特定数学定理常用的核心 Mathlib 模块 ──
THEOREM_MODULES: dict[str, list[str]] = {
    "凯莱": [
        "Mathlib.GroupTheory.Perm.Basic",
        "Mathlib.GroupTheory.Perm.Subgroup",
        "Mathlib.GroupTheory.GroupAction.Basic",
        "Mathlib.GroupTheory.GroupAction.Defs",
        "Mathlib.Algebra.Group.Subgroup.Basic",
        "Mathlib.Logic.Equiv.Defs",
    ],
    "Cayley": [
        "Mathlib.GroupTheory.Perm.Basic",
        "Mathlib.GroupTheory.Perm.Subgroup",
        "Mathlib.GroupTheory.GroupAction.Basic",
    ],
    "拉格朗日": [
        "Mathlib.GroupTheory.Index",
        "Mathlib.Algebra.Group.Subgroup.Basic",
        "Mathlib.Algebra.Group.Subgroup.Finite",
    ],
    "Lagrange": [
        "Mathlib.GroupTheory.Index",
    ],
    "同构": [
        "Mathlib.Algebra.Group.Equiv.Basic",
        "Mathlib.GroupTheory.QuotientGroup.Basic",
    ],
    "置换": [
        "Mathlib.GroupTheory.Perm.Basic",
        "Mathlib.GroupTheory.Perm.Subgroup",
        "Mathlib.GroupTheory.Perm.Sign",
    ],
    "群作用": [
        "Mathlib.GroupTheory.GroupAction.Basic",
        "Mathlib.GroupTheory.GroupAction.Defs",
    ],
    "正规子群": [
        "Mathlib.Algebra.Group.Subgroup.Basic",
        "Mathlib.GroupTheory.QuotientGroup.Basic",
    ],
    "商群": [
        "Mathlib.GroupTheory.QuotientGroup.Basic",
        "Mathlib.GroupTheory.QuotientGroup.Defs",
    ],
    "中值定理": [
        "Mathlib.Analysis.Calculus.MeanValue",
    ],
    "介值定理": [
        "Mathlib.Topology.Order.IntermediateValue",
    ],
    "素数": [
        "Mathlib.Data.Nat.Prime.Basic",
        "Mathlib.Data.Nat.Prime.Defs",
    ],
    "行列式": [
        "Mathlib.LinearAlgebra.Matrix.Determinant.Basic",
    ],
}


def _find_theorem_specific_modules(theorem_text: str) -> list[str]:
    """根据定理文本，返回该定理专属的核心模块列表"""
    results = []
    for keyword, modules in THEOREM_MODULES.items():
        if keyword in theorem_text:
            results.extend(modules)
    return results


def get_common_modules() -> list[str]:
    """返回最常用的 Mathlib 模块（几乎所有证明都可能用到的基础模块）"""
    common_prefixes = [
        "Mathlib.Tactic",
        "Mathlib.Data.Nat.Basic",
        "Mathlib.Data.Nat.Defs",
        "Mathlib.Data.Int.Basic",
        "Mathlib.Data.Int.Defs",
        "Mathlib.Data.Real.Basic",
        "Mathlib.Data.Rat.Basic",
        "Mathlib.Data.Set.Basic",
        "Mathlib.Data.Finset.Basic",
        "Mathlib.Data.List.Basic",
        "Mathlib.Logic.Basic",
        "Mathlib.Algebra.Group.Basic",
        "Mathlib.Algebra.Group.Defs",
        "Mathlib.Algebra.Ring.Basic",
        "Mathlib.Algebra.Ring.Defs",
        "Mathlib.Algebra.Order.Ring.Defs",
        "Mathlib.Algebra.BigOperators.Group.Finset",
        "Mathlib.Order.Basic",
        "Mathlib.Init",
    ]
    modules = _load_modules()
    result = [m for m in common_prefixes if m in modules]
    return result


def build_import_hint(theorem_text: str, max_modules: int = 40) -> str:
    """
    为 LLM prompt 生成可用 import 列表提示。
    结合常用模块 + 主题相关模块。
    """
    common = get_common_modules()
    topic_modules = find_modules_by_topic(theorem_text, max_per_topic=10)

    # 合并去重
    seen = set()
    merged = []
    for m in common + topic_modules:
        if m not in seen:
            seen.add(m)
            merged.append(m)

    if len(merged) > max_modules:
        merged = merged[:max_modules]

    lines = ["以下是可用的 Mathlib 模块（只能从中选取 import，不要编造不存在的模块）："]
    for m in merged:
        lines.append(f"  import {m}")

    lines.append("")
    lines.append("如果不确定用哪个模块，可以使用 import Mathlib.Tactic（包含所有 tactic）。")
    lines.append("绝对不要 import 不在此列表中的模块。如果需要的功能不在列表中，优先用 simp / omega / aesop 等自动化 tactic。")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# 黄金证明模板：已验证可通过 Lean 编译的经典定理证明
# ═══════════════════════════════════════════════════════════════════════════
# 用途：对于 LLM 不可能猜对 API 名的经典定理，直接提供正确的完整代码。
# 这些代码已通过 lake env lean 验证。
# 匹配规则：定理文本中包含关键词即命中。

GOLDEN_PROOFS: dict[str, dict] = {
    "凯莱定理": {
        "keywords": ["凯莱", "Cayley", "cayley"],
        "statement": "每个群都同构于某个置换群的子群",
        "code": """\
import Mathlib.GroupTheory.Perm.Subgroup
import Mathlib.GroupTheory.GroupAction.Basic

-- Cayley's theorem: every group embeds into a permutation group
-- via the left regular action
theorem cayley_theorem (G : Type*) [Group G] :
    Function.Injective (MulAction.toPermHom G G) :=
  MulAction.toPerm_injective (α := G) (β := G)
""",
        "code_exists": """\
import Mathlib.GroupTheory.Perm.Subgroup
import Mathlib.GroupTheory.GroupAction.Basic

-- Cayley's theorem (existential form)
theorem cayley_theorem (G : Type*) [Group G] :
    ∃ (f : G →* Equiv.Perm G), Function.Injective f :=
  ⟨MulAction.toPermHom G G, MulAction.toPerm_injective (α := G) (β := G)⟩
""",
        "api_hints": [
            "MulAction.toPermHom G G : G →* Equiv.Perm G（左正则群作用的置换同态）",
            "MulAction.toPerm_injective (α := G) (β := G)（需要显式标注类型参数）",
            "注意：必须写 (α := G) (β := G)，否则 typeclass 解析会卡住",
        ],
    },
}


def lookup_golden_proof(theorem_text: str) -> Optional[dict]:
    """
    在黄金证明模板库中查找匹配的定理。
    返回 None 表示未命中；命中时返回 {code, code_exists, api_hints, ...}。
    """
    for name, entry in GOLDEN_PROOFS.items():
        for kw in entry["keywords"]:
            if kw in theorem_text:
                return entry
    return None
