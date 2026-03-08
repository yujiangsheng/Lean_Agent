# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
                    工具函数模块 (Utility Functions)
═══════════════════════════════════════════════════════════════════════════════

提供配置管理、日志设置、证明保存和策略提取等通用工具。
Provides configuration management, logging setup, proof saving,
and tactic extraction utilities.

作者 (Author): Jiangsheng Yu
版本 (Version): 3.0.0
"""

from pathlib import Path
from typing import Any, Dict, List
import json

# ─────────────────────────────────────────────────────────────────────────────
# 默认配置 (Default Configuration)
# 当 config.json 不存在或解析失败时使用此默认值
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "llm": {
        "model_name": "Qwen/Qwen2.5-7B-Instruct",
        "device": "auto",
        "max_length": 2048,
        "temperature": 0.7,
        "top_p": 0.9
    },
    "lean": {"timeout": 30, "max_tactic_depth": 50},
    "proof_search": {"beam_width": 10, "max_iterations": 500, "max_depth": 20},
    "learning": {"max_conjecture_per_round": 10, "min_difficulty": 2}
}


def setup_logging(level: str = "INFO", log_file: str = None):
    """配置日志系统 (Configure logging system)

    设置统一的日志格式，支持同时输出到控制台和文件。

    Args:
        level: 日志级别，可选 "DEBUG", "INFO", "WARNING", "ERROR"
        log_file: 日志文件路径，为 None 则仅输出到控制台
    """
    import logging
    import sys
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers
    )


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """加载配置文件 (Load configuration file)

    从指定路径读取 JSON 配置，与默认配置合并。
    如果文件不存在或格式错误，返回默认配置。

    Args:
        config_path: 配置文件路径，默认为 "config.json"

    Returns:
        合并后的配置字典
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any], config_path: str = "config.json"):
    """保存配置到文件 (Save configuration to file)

    将配置字典序列化为 JSON 并写入指定路径。

    Args:
        config: 配置字典
        config_path: 目标文件路径
    """
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def save_proof(theorem_name: str, proof: str, output_dir: str = "proofs"):
    """保存证明到 Lean 文件 (Save proof to Lean file)

    将证明内容写入到指定目录下的 .lean 文件中。
    如果证明内容不包含 import 语句，自动添加 `import Mathlib`。

    Args:
        theorem_name: 定理名称（用作文件名）
        proof: 证明内容字符串
        output_dir: 输出目录，默认为 "proofs"

    Returns:
        生成的文件路径 (Path 对象)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"{theorem_name}.lean"
    content = proof if proof.strip().startswith("import") else f"import Mathlib\n\n{proof}"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


def extract_tactics(proof: str) -> List[str]:
    """从证明脚本中提取 tactics (Extract tactics from proof script)

    支持两种格式：
    1. 分号分隔的单行 tactic 链: "simp; ring; omega"
    2. 多行 tactic 序列：每行一个 tactic

    自动过滤掉注释行 (`--`) 和声明行 (`theorem`, `lemma`, `by`)。

    Args:
        proof: 证明脚本字符串

    Returns:
        提取的 tactic 列表

    Examples:
        >>> extract_tactics("simp; ring")
        ['simp', 'ring']
        >>> extract_tactics("intro n\nsimp")
        ['intro n', 'simp']
    """
    tactics = []
    if ";" in proof:
        for part in proof.split(";"):
            part = part.strip()
            if part and not part.startswith(("theorem", "lemma", "by")):
                tactics.append(part)
        return tactics
    for line in proof.split("\n"):
        line = line.strip()
        if line and not line.startswith("--") and not line.startswith(("theorem", "lemma", "by")):
            tactics.append(line)
    return tactics
