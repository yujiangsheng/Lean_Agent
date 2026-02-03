# -*- coding: utf-8 -*-
"""
工具函数模块 - 配置管理与日志工具
"""

from pathlib import Path
from typing import Any, Dict, List
import json

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
    """Setup logging system"""
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
    """Load configuration file"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any], config_path: str = "config.json"):
    """Save configuration to file"""
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def save_proof(theorem_name: str, proof: str, output_dir: str = "proofs"):
    """Save proof to Lean file"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"{theorem_name}.lean"
    content = proof if proof.strip().startswith("import") else f"import Mathlib\n\n{proof}"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


def extract_tactics(proof: str) -> List[str]:
    """Extract tactics from proof
    
    Args:
        proof: 证明脚本字符串
        
    Returns:
        提取的策略列表
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
