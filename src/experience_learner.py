#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    经验学习系统
═══════════════════════════════════════════════════════════════════════════════

从成功的证明中学习模式，用于指导未来的猜想生成和证明策略选择。

学习内容：
    1. 成功的证明模式（哪些策略组合有效）
    2. 定理组合规律（哪些定理经常一起使用）
    3. 领域特征（不同领域的证明风格）
    4. 难度预测（根据特征预测证明难度）

作者: Jiangsheng Yu
版本: 2.1.0
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import math


@dataclass
class ProofExperience:
    """
    证明经验记录
    
    记录一次成功证明的详细信息
    """
    conjecture_id: str                          # 猜想 ID
    statement: str                              # 形式化陈述
    statement_cn: str                           # 中文描述
    domain: str                                 # 领域
    
    # 证明信息
    tactics_used: List[str]                     # 使用的策略序列
    proof_time_ms: float                        # 证明耗时
    proof_steps: int                            # 步数
    
    # 特征
    features: Dict[str, float] = field(default_factory=dict)  # 提取的特征
    
    # 前置知识
    premises_used: List[str] = field(default_factory=list)    # 使用的前置定理
    
    # 元数据
    timestamp: str = ""
    success: bool = True
    notes: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.features:
            self.features = self._extract_features()
    
    def _extract_features(self) -> Dict[str, float]:
        """从陈述中提取特征"""
        features = {}
        
        # 符号特征
        features["has_forall"] = 1.0 if "∀" in self.statement else 0.0
        features["has_exists"] = 1.0 if "∃" in self.statement else 0.0
        features["has_implication"] = 1.0 if "→" in self.statement else 0.0
        features["has_inequality"] = 1.0 if any(op in self.statement for op in ["≥", "≤", ">", "<"]) else 0.0
        features["has_equality"] = 1.0 if "=" in self.statement else 0.0
        
        # 运算特征
        features["has_power"] = 1.0 if "^" in self.statement else 0.0
        features["has_sqrt"] = 1.0 if "sqrt" in self.statement.lower() else 0.0
        features["has_fraction"] = 1.0 if "/" in self.statement else 0.0
        features["has_trig"] = 1.0 if any(f in self.statement.lower() for f in ["sin", "cos", "tan"]) else 0.0
        
        # 复杂度特征
        features["statement_length"] = len(self.statement)
        features["num_variables"] = len(re.findall(r'\b[a-z]\b', self.statement))
        
        # 领域编码
        domain_encoding = {"algebra": 0, "trigonometry": 1, "geometry": 2}
        features["domain_code"] = domain_encoding.get(self.domain, 3)
        
        return features
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'ProofExperience':
        return cls(**d)


@dataclass
class TacticPattern:
    """
    策略模式
    
    记录有效的策略组合及其适用条件
    """
    pattern_id: str                             # 模式 ID
    tactics: List[str]                          # 策略序列
    domain: str                                 # 适用领域
    
    # 适用条件
    applicable_features: Dict[str, float] = field(default_factory=dict)
    
    # 统计
    success_count: int = 0
    fail_count: int = 0
    avg_time_ms: float = 0.0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.fail_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def confidence(self) -> float:
        """置信度（考虑样本量）"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.0
        # Wilson 分数区间下界
        z = 1.96  # 95% 置信度
        p = self.success_rate
        return (p + z*z/(2*total) - z*math.sqrt((p*(1-p) + z*z/(4*total))/total)) / (1 + z*z/total)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['success_rate'] = self.success_rate
        d['confidence'] = self.confidence
        return d
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'TacticPattern':
        # 移除计算属性
        d.pop('success_rate', None)
        d.pop('confidence', None)
        return cls(**d)


class ExperienceLearner:
    """
    经验学习器
    
    从证明历史中学习，提供策略推荐和难度预测
    
    改进特性:
        - 智能经验去重：避免重复记录相似经验
        - 经验合并：将相似经验合并以减少冗余
        - 周期性清理：自动清理低价值经验
    """
    
    def __init__(self, storage_path: str = "data/experience.json"):
        self.storage_path = Path(storage_path)
        
        # 经验库
        self.experiences: List[ProofExperience] = []
        
        # 模式库
        self.tactic_patterns: Dict[str, TacticPattern] = {}
        
        # 统计缓存
        self._domain_stats: Dict[str, Dict] = {}
        self._feature_importance: Dict[str, float] = {}
        self._tactic_cooccurrence: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # 去重配置
        self.dedup_config = {
            "similarity_threshold": 0.85,  # 相似度阈值
            "max_experiences": 20000,      # 最大经验数
            "cleanup_interval": 1000,      # 每多少条新经验后触发清理
            "min_experience_value": 0.1,   # 最小经验价值
        }
        
        # 计数器（用于触发周期性清理）
        self._experience_counter = 0
        
        # 加载
        self._load()
    
    # ========== 经验去重和相似性检测 ==========
    
    def _compute_experience_signature(self, exp: ProofExperience) -> str:
        """
        计算经验的签名（用于快速去重）
        
        签名包含：领域 + 策略序列 + 证明步数范围
        """
        tactics_str = ",".join(sorted(exp.tactics_used))
        steps_range = (exp.proof_steps // 5) * 5  # 量化到 5 步精度
        return f"{exp.domain}::{tactics_str}::{steps_range}"
    
    def _compute_experience_similarity(self, exp1: ProofExperience, 
                                       exp2: ProofExperience) -> float:
        """
        计算两个经验的相似度（0-1）
        
        考虑因素：
        1. 领域匹配（必须匹配）
        2. 策略序列相似度（Jaccard 相似度）
        3. 特征向量相似度
        4. 证明步数相近程度
        """
        # 领域必须相同
        if exp1.domain != exp2.domain:
            return 0.0
        
        # 策略序列相似度（Jaccard）
        tactics1 = set(exp1.tactics_used)
        tactics2 = set(exp2.tactics_used)
        if not tactics1 and not tactics2:
            tactic_sim = 1.0
        elif not tactics1 or not tactics2:
            tactic_sim = 0.0
        else:
            intersection = len(tactics1 & tactics2)
            union = len(tactics1 | tactics2)
            tactic_sim = intersection / union if union > 0 else 0.0
        
        # 特征相似度
        features1 = exp1.features
        features2 = exp2.features
        common_features = set(features1.keys()) & set(features2.keys())
        if common_features:
            feature_diffs = [abs(features1[f] - features2[f]) for f in common_features]
            feature_sim = 1.0 - min(1.0, sum(feature_diffs) / len(common_features))
        else:
            feature_sim = 0.5  # 无共同特征，给中等分数
        
        # 步数相近度
        max_steps = max(exp1.proof_steps, exp2.proof_steps, 1)
        steps_diff = abs(exp1.proof_steps - exp2.proof_steps)
        steps_sim = 1.0 - min(1.0, steps_diff / max_steps)
        
        # 综合相似度（加权）
        similarity = (
            tactic_sim * 0.5 +      # 策略最重要
            feature_sim * 0.3 +     # 特征次之
            steps_sim * 0.2         # 步数参考
        )
        
        return similarity
    
    def _is_duplicate_experience(self, new_exp: ProofExperience) -> bool:
        """
        检查新经验是否与已有经验重复
        
        使用两级检查：
        1. 快速签名检查
        2. 详细相似度检查
        """
        new_sig = self._compute_experience_signature(new_exp)
        
        for existing_exp in self.experiences[-500:]:  # 只检查最近 500 条
            # 快速签名检查
            existing_sig = self._compute_experience_signature(existing_exp)
            if new_sig == existing_sig:
                # 签名相同，进一步检查
                sim = self._compute_experience_similarity(new_exp, existing_exp)
                if sim >= self.dedup_config["similarity_threshold"]:
                    return True
        
        return False
    
    def _find_similar_experiences(self, exp: ProofExperience, 
                                  threshold: float = None) -> List[ProofExperience]:
        """
        查找与给定经验相似的所有经验
        """
        if threshold is None:
            threshold = self.dedup_config["similarity_threshold"]
        
        similar = []
        for existing_exp in self.experiences:
            sim = self._compute_experience_similarity(exp, existing_exp)
            if sim >= threshold:
                similar.append(existing_exp)
        
        return similar
    
    def _compute_experience_value(self, exp: ProofExperience) -> float:
        """
        计算经验的价值分数
        
        价值因素：
        1. 成功率贡献
        2. 策略多样性
        3. 时间效率
        4. 独特性
        """
        # 成功率（成功经验更有价值）
        success_value = 0.5 if exp.success else 0.2
        
        # 策略多样性（使用多种策略更有价值）
        diversity_value = min(len(exp.tactics_used) / 5.0, 1.0) * 0.3
        
        # 时间效率（快速证明更有价值）
        time_value = max(0, 1.0 - exp.proof_time_ms / 10000) * 0.2
        
        # 独特性（与其他经验不同）
        similar_count = len(self._find_similar_experiences(exp, threshold=0.9))
        uniqueness_value = 1.0 / max(1, similar_count) * 0.2
        
        return success_value + diversity_value + time_value + uniqueness_value
    
    # ========== 学习 ==========
    
    def record_experience(self, experience: ProofExperience):
        """
        记录一次证明经验
        
        改进：添加去重检查，避免重复记录相似经验
        """
        # 检查是否重复
        if self._is_duplicate_experience(experience):
            # 找到相似经验并更新（而非添加新的）
            self._merge_with_similar(experience)
            return
        
        self.experiences.append(experience)
        self._experience_counter += 1
        
        # 更新策略模式
        self._update_tactic_pattern(experience)
        
        # 更新共现统计
        self._update_cooccurrence(experience.tactics_used)
        
        # 更新领域统计
        self._update_domain_stats(experience)
        
        # 周期性清理
        if self._experience_counter >= self.dedup_config["cleanup_interval"]:
            self._cleanup_low_value_experiences()
            self._experience_counter = 0
        
        self._save()
    
    def _merge_with_similar(self, new_exp: ProofExperience):
        """
        将新经验与相似经验合并
        
        合并策略：取最优者（成功率更高、时间更短的优先）
        """
        best_existing = None
        best_sim = 0.0
        
        for existing_exp in self.experiences[-500:]:
            sim = self._compute_experience_similarity(new_exp, existing_exp)
            if sim > best_sim:
                best_sim = sim
                best_existing = existing_exp
        
        if best_existing is not None:
            # 如果新经验更好（成功且更快），更新特征
            if new_exp.success and (not best_existing.success or 
                                     new_exp.proof_time_ms < best_existing.proof_time_ms):
                # 更新现有经验的特征（取平均）
                for feat, val in new_exp.features.items():
                    if feat in best_existing.features:
                        best_existing.features[feat] = (best_existing.features[feat] + val) / 2
                    else:
                        best_existing.features[feat] = val
    
    def _cleanup_low_value_experiences(self):
        """
        清理低价值经验
        
        删除价值分数最低的经验，保持经验库大小
        """
        max_exp = self.dedup_config["max_experiences"]
        min_value = self.dedup_config["min_experience_value"]
        
        if len(self.experiences) <= max_exp:
            return
        
        # 计算所有经验的价值
        exp_values = [(exp, self._compute_experience_value(exp)) for exp in self.experiences]
        
        # 按价值排序
        exp_values.sort(key=lambda x: x[1], reverse=True)
        
        # 保留高价值经验，删除低价值经验
        keep_count = min(max_exp, len([ev for ev in exp_values if ev[1] >= min_value]))
        self.experiences = [ev[0] for ev in exp_values[:keep_count]]
        
        # 重建模式库
        self._rebuild_patterns()
    
    def _rebuild_patterns(self):
        """重建策略模式库"""
        self.tactic_patterns.clear()
        self._domain_stats.clear()
        self._tactic_cooccurrence.clear()
        
        for exp in self.experiences:
            self._update_tactic_pattern(exp)
            self._update_cooccurrence(exp.tactics_used)
            self._update_domain_stats(exp)
    
    def deduplicate_experiences(self, aggressive: bool = False):
        """
        对经验库进行批量去重
        
        参数:
            aggressive: 是否使用激进模式（更低的相似度阈值）
        
        返回:
            删除的经验数量
        """
        threshold = 0.7 if aggressive else self.dedup_config["similarity_threshold"]
        
        # 按签名分组
        signature_groups: Dict[str, List[ProofExperience]] = defaultdict(list)
        for exp in self.experiences:
            sig = self._compute_experience_signature(exp)
            signature_groups[sig].append(exp)
        
        # 对每组进行去重
        unique_experiences = []
        removed_count = 0
        
        for sig, group in signature_groups.items():
            if len(group) == 1:
                unique_experiences.append(group[0])
            else:
                # 选择最有价值的经验
                values = [(exp, self._compute_experience_value(exp)) for exp in group]
                values.sort(key=lambda x: x[1], reverse=True)
                
                # 保留最佳的，合并其他的特征
                best = values[0][0]
                for exp, _ in values[1:]:
                    # 合并特征
                    for feat, val in exp.features.items():
                        if feat in best.features:
                            best.features[feat] = (best.features[feat] + val) / 2
                        else:
                            best.features[feat] = val
                    removed_count += 1
                
                unique_experiences.append(best)
        
        self.experiences = unique_experiences
        self._rebuild_patterns()
        self._save()
        
        return removed_count
        
        # 更新共现统计
        self._update_cooccurrence(experience.tactics_used)
        
        # 更新领域统计
        self._update_domain_stats(experience)
        
        self._save()
    
    def _update_tactic_pattern(self, exp: ProofExperience):
        """更新策略模式"""
        # 生成模式 ID
        pattern_key = f"{exp.domain}::{','.join(exp.tactics_used)}"
        
        if pattern_key not in self.tactic_patterns:
            self.tactic_patterns[pattern_key] = TacticPattern(
                pattern_id=pattern_key,
                tactics=exp.tactics_used,
                domain=exp.domain,
                applicable_features=exp.features.copy()
            )
        
        pattern = self.tactic_patterns[pattern_key]
        
        if exp.success:
            pattern.success_count += 1
            # 更新平均时间
            n = pattern.success_count
            pattern.avg_time_ms = ((n - 1) * pattern.avg_time_ms + exp.proof_time_ms) / n
        else:
            pattern.fail_count += 1
        
        # 更新适用特征（取平均）
        for feat, val in exp.features.items():
            if feat in pattern.applicable_features:
                pattern.applicable_features[feat] = (pattern.applicable_features[feat] + val) / 2
            else:
                pattern.applicable_features[feat] = val
    
    def _update_cooccurrence(self, tactics: List[str]):
        """更新策略共现统计"""
        for i, t1 in enumerate(tactics):
            for t2 in tactics[i+1:]:
                self._tactic_cooccurrence[t1][t2] += 1
                self._tactic_cooccurrence[t2][t1] += 1
    
    def _update_domain_stats(self, exp: ProofExperience):
        """更新领域统计"""
        domain = exp.domain
        
        if domain not in self._domain_stats:
            self._domain_stats[domain] = {
                "total_proofs": 0,
                "successful_proofs": 0,
                "avg_steps": 0,
                "avg_time_ms": 0,
                "common_tactics": Counter(),
                "avg_difficulty": 0
            }
        
        stats = self._domain_stats[domain]
        stats["total_proofs"] += 1
        
        if exp.success:
            stats["successful_proofs"] += 1
            n = stats["successful_proofs"]
            stats["avg_steps"] = ((n - 1) * stats["avg_steps"] + exp.proof_steps) / n
            stats["avg_time_ms"] = ((n - 1) * stats["avg_time_ms"] + exp.proof_time_ms) / n
        
        for tactic in exp.tactics_used:
            stats["common_tactics"][tactic] += 1
    
    # ========== 推荐 ==========
    
    def recommend_tactics(self, domain: str, features: Dict[str, float], 
                         top_k: int = 5) -> List[Tuple[List[str], float]]:
        """
        推荐策略序列
        
        参数:
            domain: 领域
            features: 猜想特征
            top_k: 返回前 k 个推荐
        
        返回:
            [(策略序列, 置信度), ...]
        """
        candidates = []
        
        for pattern_id, pattern in self.tactic_patterns.items():
            # 领域匹配
            if pattern.domain != domain:
                continue
            
            # 计算特征相似度
            similarity = self._feature_similarity(features, pattern.applicable_features)
            
            # 综合得分 = 相似度 * 置信度
            score = similarity * pattern.confidence
            
            candidates.append((pattern.tactics, score, pattern.success_rate))
        
        # 按得分排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return [(tactics, score) for tactics, score, _ in candidates[:top_k]]
    
    def _feature_similarity(self, f1: Dict[str, float], f2: Dict[str, float]) -> float:
        """计算特征相似度（余弦相似度）"""
        common_keys = set(f1.keys()) & set(f2.keys())
        if not common_keys:
            return 0.0
        
        dot_product = sum(f1[k] * f2[k] for k in common_keys)
        norm1 = math.sqrt(sum(f1[k] ** 2 for k in common_keys))
        norm2 = math.sqrt(sum(f2[k] ** 2 for k in common_keys))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def recommend_next_tactic(self, current_tactics: List[str], domain: str) -> List[Tuple[str, float]]:
        """
        推荐下一个策略
        
        基于已使用的策略和共现统计
        """
        if not current_tactics:
            # 返回该领域最常见的开始策略
            if domain in self._domain_stats:
                common = self._domain_stats[domain]["common_tactics"]
                return common.most_common(5)
            return [("intros", 0.5)]
        
        # 基于最后一个策略的共现
        last_tactic = current_tactics[-1]
        cooccur = self._tactic_cooccurrence.get(last_tactic, {})
        
        if not cooccur:
            return []
        
        # 排除已使用的
        candidates = [(t, c) for t, c in cooccur.items() if t not in current_tactics]
        total = sum(c for _, c in candidates)
        
        if total == 0:
            return []
        
        # 转换为概率
        return [(t, c / total) for t, c in sorted(candidates, key=lambda x: -x[1])[:5]]
    
    def predict_difficulty(self, features: Dict[str, float], domain: str) -> int:
        """
        预测证明难度
        
        基于历史经验预测难度等级 (1-5)
        """
        # 简单启发式
        difficulty = 2  # 默认
        
        # 基于特征调整
        if features.get("has_inequality", 0) > 0:
            difficulty += 1
        if features.get("has_power", 0) > 0 and features.get("has_fraction", 0) > 0:
            difficulty += 1
        if features.get("num_variables", 0) > 3:
            difficulty += 1
        if features.get("statement_length", 0) > 100:
            difficulty += 1
        
        # 基于领域统计
        if domain in self._domain_stats:
            avg_steps = self._domain_stats[domain].get("avg_steps", 3)
            if avg_steps > 4:
                difficulty += 1
        
        return min(5, max(1, difficulty))
    
    # ========== 分析 ==========
    
    def get_domain_insights(self, domain: str) -> Dict:
        """
        获取领域洞察
        """
        if domain not in self._domain_stats:
            return {"error": f"No data for domain: {domain}"}
        
        stats = self._domain_stats[domain]
        
        # 找出最有效的策略模式
        domain_patterns = [
            p for p in self.tactic_patterns.values() 
            if p.domain == domain and p.success_count > 0
        ]
        domain_patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        return {
            "total_proofs": stats["total_proofs"],
            "success_rate": stats["successful_proofs"] / stats["total_proofs"] if stats["total_proofs"] > 0 else 0,
            "avg_steps": stats["avg_steps"],
            "avg_time_ms": stats["avg_time_ms"],
            "top_tactics": stats["common_tactics"].most_common(5),
            "top_patterns": [
                {
                    "tactics": p.tactics,
                    "success_rate": p.success_rate,
                    "confidence": p.confidence,
                    "count": p.success_count
                }
                for p in domain_patterns[:5]
            ]
        }
    
    def get_learning_summary(self) -> Dict:
        """获取学习总结"""
        return {
            "total_experiences": len(self.experiences),
            "total_patterns": len(self.tactic_patterns),
            "domains_covered": list(self._domain_stats.keys()),
            "domain_stats": {
                d: {
                    "proofs": s["total_proofs"],
                    "success_rate": s["successful_proofs"] / s["total_proofs"] if s["total_proofs"] > 0 else 0
                }
                for d, s in self._domain_stats.items()
            },
            "most_successful_patterns": sorted(
                [p.to_dict() for p in self.tactic_patterns.values() if p.success_count > 0],
                key=lambda x: x["confidence"],
                reverse=True
            )[:10]
        }
    
    # ========== 持久化 ==========
    
    def _save(self):
        """保存到文件"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "experiences": [e.to_dict() for e in self.experiences],
            "tactic_patterns": {k: v.to_dict() for k, v in self.tactic_patterns.items()},
            "domain_stats": {
                d: {**s, "common_tactics": dict(s["common_tactics"])}
                for d, s in self._domain_stats.items()
            },
            "tactic_cooccurrence": {
                k: dict(v) for k, v in self._tactic_cooccurrence.items()
            },
            "metadata": {
                "version": "0.9.0",
                "last_updated": datetime.now().isoformat()
            }
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load(self):
        """从文件加载"""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.experiences = [
                ProofExperience.from_dict(e) for e in data.get("experiences", [])
            ]
            
            self.tactic_patterns = {
                k: TacticPattern.from_dict(v) 
                for k, v in data.get("tactic_patterns", {}).items()
            }
            
            for d, s in data.get("domain_stats", {}).items():
                s["common_tactics"] = Counter(s.get("common_tactics", {}))
                self._domain_stats[d] = s
            
            for k, v in data.get("tactic_cooccurrence", {}).items():
                self._tactic_cooccurrence[k] = defaultdict(int, v)
            
            print(f"  ✓ 加载经验库: {len(self.experiences)} 条经验, {len(self.tactic_patterns)} 个模式")
        
        except Exception as e:
            print(f"  ⚠ 加载经验库失败: {e}")


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("经验学习系统测试")
    print("=" * 70)
    
    learner = ExperienceLearner("data/test_experience.json")
    
    # 记录一些经验
    exp1 = ProofExperience(
        conjecture_id="test1",
        statement="∀ a b : ℝ, a^2 + b^2 ≥ 2*a*b",
        statement_cn="平方和不等式",
        domain="algebra",
        tactics_used=["intros", "nlinarith [sq_nonneg (a - b)]"],
        proof_time_ms=10.5,
        proof_steps=2,
        premises_used=["sq_nonneg"]
    )
    
    exp2 = ProofExperience(
        conjecture_id="test2",
        statement="∀ a b c : ℝ, (a + b + c)^2 = a^2 + b^2 + c^2 + 2*a*b + 2*b*c + 2*c*a",
        statement_cn="三数和的平方",
        domain="algebra",
        tactics_used=["intros", "ring"],
        proof_time_ms=5.2,
        proof_steps=2,
        premises_used=[]
    )
    
    exp3 = ProofExperience(
        conjecture_id="test3",
        statement="∀ θ : ℝ, Real.sin θ ^ 2 + Real.cos θ ^ 2 = 1",
        statement_cn="三角恒等式",
        domain="trigonometry",
        tactics_used=["intros", "exact Real.sin_sq_add_cos_sq θ"],
        proof_time_ms=3.1,
        proof_steps=2,
        premises_used=["sin_sq_add_cos_sq"]
    )
    
    learner.record_experience(exp1)
    learner.record_experience(exp2)
    learner.record_experience(exp3)
    
    # 测试推荐
    print("\n策略推荐测试:")
    test_features = {
        "has_inequality": 1.0,
        "has_power": 1.0,
        "domain_code": 0
    }
    recommendations = learner.recommend_tactics("algebra", test_features)
    for tactics, score in recommendations:
        print(f"  {' → '.join(tactics)}: {score:.3f}")
    
    # 领域洞察
    print("\n领域洞察:")
    insights = learner.get_domain_insights("algebra")
    print(f"  代数领域: {insights}")
    
    # 学习总结
    print("\n学习总结:")
    summary = learner.get_learning_summary()
    print(f"  总经验: {summary['total_experiences']}")
    print(f"  总模式: {summary['total_patterns']}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
