#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    数学知识图谱系统
═══════════════════════════════════════════════════════════════════════════════

管理定理之间的推导关系，支持：
    1. 知识节点管理（定理、引理、猜想）
    2. 推导边管理（A → B 表示 A 用于证明 B）
    3. 图谱查询（前驱、后继、路径）
    4. 持久化存储

作者: Jiangsheng Yu
版本: 2.1.0
"""

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime
from enum import Enum
from collections import defaultdict


class NodeType(Enum):
    """知识节点类型"""
    AXIOM = "axiom"           # 公理（无需证明）
    THEOREM = "theorem"       # 已证明的定理
    LEMMA = "lemma"           # 引理
    CONJECTURE = "conjecture" # 待证猜想
    DERIVED = "derived"       # 推导得到的新定理


class NodeStatus(Enum):
    """节点状态"""
    VERIFIED = "verified"     # 已验证
    PENDING = "pending"       # 待验证
    FAILED = "failed"         # 验证失败
    ASSUMED = "assumed"       # 假设为真（公理）
    CONJECTURED = "conjectured"  # 合情推理（有置信度但未严格证明）


@dataclass
class KnowledgeNode:
    """
    知识节点
    
    表示知识图谱中的一个定理/引理/猜想
    """
    id: str                                    # 唯一标识符
    statement: str                             # Lean 4 形式化陈述
    statement_cn: str                          # 中文描述
    domain: str                                # 所属领域
    node_type: NodeType = NodeType.THEOREM     # 节点类型
    status: NodeStatus = NodeStatus.PENDING    # 状态
    
    # 元数据
    difficulty: int = 2                        # 难度 (1-5)
    proof_steps: int = 0                       # 证明步数
    proof_script: List[str] = field(default_factory=list)  # 证明脚本
    
    # 置信度（合情推理）
    confidence: float = 1.0                    # 置信度 (0-1)，1.0 表示严格证明
    induction_samples: int = 0                 # 归纳验证的样本数
    counterexample: str = ""                   # 反例（如果有）
    
    # 跨领域信息
    related_domains: List[str] = field(default_factory=list)  # 相关领域
    
    # 时间戳
    created_at: str = ""                       # 创建时间
    verified_at: str = ""                      # 验证时间
    
    # 标签和注释
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def __post_init__(self):
        if not self.id:
            normalized = ''.join(self.statement.split())
            self.id = hashlib.md5(normalized.encode()).hexdigest()[:12]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        d = asdict(self)
        d['node_type'] = self.node_type.value
        d['status'] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'KnowledgeNode':
        """从字典创建"""
        d['node_type'] = NodeType(d['node_type'])
        d['status'] = NodeStatus(d['status'])
        # 处理新字段的向后兼容
        if 'confidence' not in d:
            d['confidence'] = 1.0
        if 'induction_samples' not in d:
            d['induction_samples'] = 0
        if 'counterexample' not in d:
            d['counterexample'] = ""
        if 'related_domains' not in d:
            d['related_domains'] = []
        return cls(**d)


@dataclass
class DerivationEdge:
    """
    推导边
    
    表示从前提节点到结论节点的推导关系
    """
    source_id: str              # 前提节点 ID
    target_id: str              # 结论节点 ID
    relation_type: str          # 关系类型 (direct_use, generalization, specialization, combination)
    description: str = ""       # 推导说明
    tactics_used: List[str] = field(default_factory=list)  # 使用的策略
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'DerivationEdge':
        return cls(**d)


class KnowledgeGraph:
    """
    数学知识图谱
    
    管理定理之间的推导关系，支持查询和分析
    """
    
    def __init__(self, storage_path: str = "data/knowledge_graph.json"):
        self.storage_path = Path(storage_path)
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[DerivationEdge] = []
        
        # 索引
        self._predecessors: Dict[str, Set[str]] = defaultdict(set)  # 前驱节点
        self._successors: Dict[str, Set[str]] = defaultdict(set)    # 后继节点
        self._by_domain: Dict[str, Set[str]] = defaultdict(set)     # 按领域索引
        self._by_type: Dict[NodeType, Set[str]] = defaultdict(set)  # 按类型索引
        
        # 加载已有数据
        self._load()
    
    # ========== 节点操作 ==========
    
    def add_node(self, node: KnowledgeNode) -> bool:
        """
        添加知识节点
        
        返回: 是否成功添加（已存在则返回 False）
        """
        if node.id in self.nodes:
            return False
        
        self.nodes[node.id] = node
        self._by_domain[node.domain].add(node.id)
        self._by_type[node.node_type].add(node.id)
        
        self._save()
        return True
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def update_node(self, node_id: str, **kwargs) -> bool:
        """更新节点属性"""
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        for key, value in kwargs.items():
            if hasattr(node, key):
                setattr(node, key, value)
        
        self._save()
        return True
    
    def mark_verified(self, node_id: str, proof_script: List[str]) -> bool:
        """标记节点为已验证"""
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        node.status = NodeStatus.VERIFIED
        node.proof_script = proof_script
        node.proof_steps = len(proof_script)
        node.verified_at = datetime.now().isoformat()
        
        # 如果是猜想，升级为定理
        if node.node_type == NodeType.CONJECTURE:
            node.node_type = NodeType.DERIVED
        
        self._save()
        return True
    
    # ========== 边操作 ==========
    
    def add_edge(self, source_id: str, target_id: str, 
                 relation_type: str = "direct_use",
                 description: str = "",
                 tactics_used: List[str] = None) -> bool:
        """
        添加推导边
        
        参数:
            source_id: 前提节点 ID
            target_id: 结论节点 ID
            relation_type: 关系类型
            description: 推导说明
            tactics_used: 使用的策略
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return False
        
        # 检查是否已存在
        for edge in self.edges:
            if edge.source_id == source_id and edge.target_id == target_id:
                return False
        
        edge = DerivationEdge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            description=description,
            tactics_used=tactics_used or []
        )
        
        self.edges.append(edge)
        self._predecessors[target_id].add(source_id)
        self._successors[source_id].add(target_id)
        
        self._save()
        return True
    
    def add_derivation(self, premises: List[str], conclusion_id: str,
                       description: str = "",
                       tactics_used: List[str] = None) -> int:
        """
        添加多前提推导
        
        返回: 成功添加的边数
        """
        count = 0
        for premise_id in premises:
            if self.add_edge(premise_id, conclusion_id, "direct_use", 
                            description, tactics_used):
                count += 1
        return count
    
    # ========== 查询操作 ==========
    
    def get_predecessors(self, node_id: str) -> List[KnowledgeNode]:
        """获取前驱节点（证明该节点所依赖的定理）"""
        pred_ids = self._predecessors.get(node_id, set())
        return [self.nodes[pid] for pid in pred_ids if pid in self.nodes]
    
    def get_successors(self, node_id: str) -> List[KnowledgeNode]:
        """获取后继节点（依赖该节点的定理）"""
        succ_ids = self._successors.get(node_id, set())
        return [self.nodes[sid] for sid in succ_ids if sid in self.nodes]
    
    def get_derivation_chain(self, node_id: str, max_depth: int = 5) -> Dict:
        """
        获取推导链（从公理到该节点的路径）
        
        返回: 树形结构表示的推导链
        """
        visited = set()
        
        def _build_chain(nid: str, depth: int) -> Dict:
            if depth > max_depth or nid in visited:
                return {"id": nid, "truncated": True}
            
            visited.add(nid)
            node = self.nodes.get(nid)
            if not node:
                return {"id": nid, "error": "not found"}
            
            predecessors = self.get_predecessors(nid)
            
            return {
                "id": nid,
                "statement_cn": node.statement_cn,
                "type": node.node_type.value,
                "status": node.status.value,
                "premises": [_build_chain(p.id, depth + 1) for p in predecessors]
            }
        
        return _build_chain(node_id, 0)
    
    def get_nodes_by_domain(self, domain: str) -> List[KnowledgeNode]:
        """按领域获取节点"""
        node_ids = self._by_domain.get(domain, set())
        return [self.nodes[nid] for nid in node_ids]
    
    def get_verified_nodes(self) -> List[KnowledgeNode]:
        """获取所有已验证节点"""
        return [n for n in self.nodes.values() if n.status == NodeStatus.VERIFIED]
    
    def get_leaf_nodes(self) -> List[KnowledgeNode]:
        """获取叶子节点（没有后继的已验证节点，可作为新推导的起点）"""
        leaves = []
        for node in self.nodes.values():
            if node.status == NodeStatus.VERIFIED:
                if node.id not in self._successors or not self._successors[node.id]:
                    leaves.append(node)
        return leaves
    
    def find_related_nodes(self, node_id: str, max_hops: int = 2) -> List[KnowledgeNode]:
        """查找相关节点（N 跳以内）"""
        related = set()
        current = {node_id}
        
        for _ in range(max_hops):
            next_level = set()
            for nid in current:
                next_level.update(self._predecessors.get(nid, set()))
                next_level.update(self._successors.get(nid, set()))
            related.update(next_level)
            current = next_level - related
        
        related.discard(node_id)
        return [self.nodes[nid] for nid in related if nid in self.nodes]
    
    # ========== 统计与分析 ==========
    
    def get_statistics(self) -> Dict:
        """获取图谱统计信息"""
        stats = {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "by_type": {},
            "by_status": {},
            "by_domain": {},
            "avg_predecessors": 0,
            "avg_successors": 0,
            "max_depth": 0
        }
        
        for node_type in NodeType:
            stats["by_type"][node_type.value] = len(self._by_type.get(node_type, set()))
        
        status_counts = defaultdict(int)
        for node in self.nodes.values():
            status_counts[node.status.value] += 1
        stats["by_status"] = dict(status_counts)
        
        for domain, node_ids in self._by_domain.items():
            stats["by_domain"][domain] = len(node_ids)
        
        if self.nodes:
            total_pred = sum(len(preds) for preds in self._predecessors.values())
            total_succ = sum(len(succs) for succs in self._successors.values())
            stats["avg_predecessors"] = total_pred / len(self.nodes)
            stats["avg_successors"] = total_succ / len(self.nodes)
        
        return stats
    
    def visualize_ascii(self, node_id: str = None, max_depth: int = 3) -> str:
        """生成 ASCII 可视化"""
        lines = []
        
        if node_id:
            chain = self.get_derivation_chain(node_id, max_depth)
            lines.append(f"推导链: {self.nodes[node_id].statement_cn}")
            lines.append("=" * 60)
            
            def _print_chain(chain, indent=0):
                prefix = "  " * indent
                node_info = f"{chain.get('statement_cn', chain['id'])}"
                status = f"[{chain.get('status', '?')}]"
                lines.append(f"{prefix}├─ {node_info} {status}")
                
                for premise in chain.get('premises', []):
                    _print_chain(premise, indent + 1)
            
            _print_chain(chain)
        else:
            lines.append("知识图谱概览")
            lines.append("=" * 60)
            stats = self.get_statistics()
            lines.append(f"节点数: {stats['total_nodes']}, 边数: {stats['total_edges']}")
            lines.append(f"按类型: {stats['by_type']}")
            lines.append(f"按状态: {stats['by_status']}")
        
        return "\n".join(lines)
    
    # ========== 知识去重和清理 ==========
    
    def _normalize_statement(self, statement: str) -> str:
        """
        标准化陈述用于比较
        """
        import re
        
        # 移除空白
        s = ''.join(statement.split())
        
        # 统一变量名
        var_pattern = r'\b([a-z]|α|β|γ|θ|φ)\b'
        vars_found = []
        
        def replace_var(match):
            var = match.group(1)
            if var not in vars_found:
                vars_found.append(var)
            idx = vars_found.index(var)
            return f"v{idx}"
        
        s = re.sub(var_pattern, replace_var, s)
        
        return s
    
    def _compute_node_similarity(self, node1: KnowledgeNode, 
                                  node2: KnowledgeNode) -> float:
        """
        计算两个节点的相似度（0-1）
        
        考虑因素：
        1. 领域匹配
        2. 陈述相似度
        3. 类型匹配
        """
        import re
        
        # 领域不同，相似度低
        if node1.domain != node2.domain:
            return 0.0
        
        # 标准化陈述
        n1 = self._normalize_statement(node1.statement)
        n2 = self._normalize_statement(node2.statement)
        
        # 完全匹配
        if n1 == n2:
            return 1.0
        
        # 词/符号级别相似度
        tokens1 = set(re.findall(r'[a-zA-Z_]+|[∀∃→∧∨¬≤≥=≠+\-*/^]|\d+', node1.statement))
        tokens2 = set(re.findall(r'[a-zA-Z_]+|[∀∃→∧∨¬≤≥=≠+\-*/^]|\d+', node2.statement))
        
        if not tokens1 or not tokens2:
            token_sim = 0.0
        else:
            token_sim = len(tokens1 & tokens2) / len(tokens1 | tokens2)
        
        # 类型匹配加成
        type_bonus = 0.1 if node1.node_type == node2.node_type else 0.0
        
        return min(token_sim + type_bonus, 1.0)
    
    def find_duplicate_nodes(self, threshold: float = 0.9) -> List[List[str]]:
        """
        查找重复或高度相似的节点
        
        参数:
            threshold: 相似度阈值
        
        返回:
            重复节点组列表，每组包含相似节点的 ID
        """
        # 按领域分组处理（提高效率）
        duplicate_groups = []
        processed = set()
        
        for domain, node_ids in self._by_domain.items():
            nodes_list = [self.nodes[nid] for nid in node_ids]
            
            for i, node1 in enumerate(nodes_list):
                if node1.id in processed:
                    continue
                
                similar_ids = [node1.id]
                
                for node2 in nodes_list[i+1:]:
                    if node2.id in processed:
                        continue
                    
                    sim = self._compute_node_similarity(node1, node2)
                    if sim >= threshold:
                        similar_ids.append(node2.id)
                        processed.add(node2.id)
                
                if len(similar_ids) > 1:
                    duplicate_groups.append(similar_ids)
                    processed.add(node1.id)
        
        return duplicate_groups
    
    def _compute_node_value(self, node: KnowledgeNode) -> float:
        """
        计算节点的价值分数
        
        价值因素：
        1. 节点类型（公理 > 定理 > 猜想）
        2. 验证状态
        3. 被引用次数（作为前提的次数）
        4. 证明信息完整性
        """
        # 类型价值
        type_values = {
            NodeType.AXIOM: 1.0,
            NodeType.DEFINITION: 0.9,
            NodeType.THEOREM: 0.8,
            NodeType.LEMMA: 0.7,
            NodeType.CORE: 0.85,
            NodeType.DERIVED: 0.6,
            NodeType.CONJECTURE: 0.4,
        }
        type_value = type_values.get(node.node_type, 0.5)
        
        # 状态价值
        status_values = {
            NodeStatus.VERIFIED: 0.3,
            NodeStatus.ASSUMED: 0.25,
            NodeStatus.CONJECTURED: 0.1,
            NodeStatus.REFUTED: 0.0,
        }
        status_value = status_values.get(node.status, 0.1)
        
        # 引用价值（被多少其他节点使用）
        successor_count = len(self._successors.get(node.id, set()))
        reference_value = min(successor_count / 10.0, 0.3)
        
        # 证明完整性
        proof_value = 0.1 if node.proof_script else 0.0
        
        return type_value * 0.4 + status_value + reference_value + proof_value
    
    def merge_duplicate_nodes(self, dry_run: bool = True) -> Dict:
        """
        合并重复节点
        
        参数:
            dry_run: 是否只预览（不实际修改）
        
        返回:
            合并报告
        """
        duplicate_groups = self.find_duplicate_nodes(threshold=0.9)
        
        report = {
            "duplicate_groups_found": len(duplicate_groups),
            "nodes_to_merge": sum(len(g) - 1 for g in duplicate_groups),
            "details": []
        }
        
        if dry_run:
            for group in duplicate_groups:
                group_info = {
                    "node_ids": group,
                    "statements": [self.nodes[nid].statement_cn for nid in group],
                }
                report["details"].append(group_info)
            return report
        
        # 实际合并
        for group in duplicate_groups:
            # 选择价值最高的节点作为保留节点
            values = [(nid, self._compute_node_value(self.nodes[nid])) for nid in group]
            values.sort(key=lambda x: x[1], reverse=True)
            
            keep_id = values[0][0]
            keep_node = self.nodes[keep_id]
            
            for remove_id, _ in values[1:]:
                remove_node = self.nodes[remove_id]
                
                # 合并特征
                if remove_node.proof_script and not keep_node.proof_script:
                    keep_node.proof_script = remove_node.proof_script
                if remove_node.confidence > keep_node.confidence:
                    keep_node.confidence = remove_node.confidence
                
                # 迁移边
                for edge in list(self.edges):
                    if edge.source_id == remove_id:
                        edge.source_id = keep_id
                    if edge.target_id == remove_id:
                        edge.target_id = keep_id
                
                # 更新索引
                for pred_id in self._predecessors.get(remove_id, set()):
                    self._successors[pred_id].discard(remove_id)
                    self._successors[pred_id].add(keep_id)
                    self._predecessors[keep_id].add(pred_id)
                
                for succ_id in self._successors.get(remove_id, set()):
                    self._predecessors[succ_id].discard(remove_id)
                    self._predecessors[succ_id].add(keep_id)
                    self._successors[keep_id].add(succ_id)
                
                # 删除节点
                del self.nodes[remove_id]
                self._by_domain[remove_node.domain].discard(remove_id)
                self._by_type[remove_node.node_type].discard(remove_id)
                del self._predecessors[remove_id]
                del self._successors[remove_id]
                
                report["details"].append({
                    "merged": remove_id,
                    "into": keep_id
                })
        
        self._save()
        return report
    
    def cleanup_low_value_nodes(self, min_value: float = 0.2, 
                                 dry_run: bool = True) -> Dict:
        """
        清理低价值节点
        
        参数:
            min_value: 最小价值阈值
            dry_run: 是否只预览
        
        返回:
            清理报告
        """
        # 计算所有节点的价值
        node_values = [(nid, self._compute_node_value(node)) 
                       for nid, node in self.nodes.items()]
        
        # 找出低价值节点
        low_value_nodes = [(nid, val) for nid, val in node_values if val < min_value]
        
        report = {
            "total_nodes": len(self.nodes),
            "low_value_count": len(low_value_nodes),
            "nodes_to_remove": [],
        }
        
        # 不能删除被其他节点依赖的节点
        removable = []
        for nid, val in low_value_nodes:
            successors = self._successors.get(nid, set())
            if not successors:  # 没有被其他节点依赖
                removable.append(nid)
                report["nodes_to_remove"].append({
                    "id": nid,
                    "statement_cn": self.nodes[nid].statement_cn,
                    "value": val
                })
        
        if dry_run:
            return report
        
        # 实际删除
        for nid in removable:
            node = self.nodes[nid]
            
            # 删除相关边
            self.edges = [e for e in self.edges 
                         if e.source_id != nid and e.target_id != nid]
            
            # 更新索引
            for pred_id in self._predecessors.get(nid, set()):
                self._successors[pred_id].discard(nid)
            
            del self.nodes[nid]
            self._by_domain[node.domain].discard(nid)
            self._by_type[node.node_type].discard(nid)
            if nid in self._predecessors:
                del self._predecessors[nid]
            if nid in self._successors:
                del self._successors[nid]
        
        self._save()
        return report
    
    # ========== 持久化 ==========
    
    def _save(self):
        """保存到文件"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
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
            
            # 加载节点
            for nid, node_dict in data.get("nodes", {}).items():
                node = KnowledgeNode.from_dict(node_dict)
                self.nodes[nid] = node
                self._by_domain[node.domain].add(nid)
                self._by_type[node.node_type].add(nid)
            
            # 加载边
            for edge_dict in data.get("edges", []):
                edge = DerivationEdge.from_dict(edge_dict)
                self.edges.append(edge)
                self._predecessors[edge.target_id].add(edge.source_id)
                self._successors[edge.source_id].add(edge.target_id)
            
            print(f"  ✓ 加载知识图谱: {len(self.nodes)} 节点, {len(self.edges)} 边")
        
        except Exception as e:
            print(f"  ⚠ 加载知识图谱失败: {e}")
    
    def export_dot(self, output_path: str = "data/knowledge_graph.dot"):
        """导出为 DOT 格式（可用 Graphviz 可视化）"""
        lines = ["digraph KnowledgeGraph {"]
        lines.append('  rankdir=BT;')  # 从下到上
        lines.append('  node [shape=box, style=rounded];')
        
        # 按领域着色
        colors = {
            "algebra": "lightblue",
            "trigonometry": "lightgreen", 
            "geometry": "lightyellow"
        }
        
        for nid, node in self.nodes.items():
            color = colors.get(node.domain, "white")
            label = node.statement_cn[:20] + "..." if len(node.statement_cn) > 20 else node.statement_cn
            status_mark = "✓" if node.status == NodeStatus.VERIFIED else "?"
            lines.append(f'  "{nid}" [label="{label} {status_mark}", fillcolor={color}, style=filled];')
        
        for edge in self.edges:
            lines.append(f'  "{edge.source_id}" -> "{edge.target_id}";')
        
        lines.append("}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        print(f"导出 DOT 文件: {output_path}")


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("知识图谱测试")
    print("=" * 70)
    
    graph = KnowledgeGraph("data/test_graph.json")
    
    # 添加一些节点
    node1 = KnowledgeNode(
        id="sq_nonneg",
        statement="∀ x : ℝ, x^2 ≥ 0",
        statement_cn="平方非负",
        domain="algebra",
        node_type=NodeType.AXIOM,
        status=NodeStatus.ASSUMED,
        difficulty=1
    )
    
    node2 = KnowledgeNode(
        id="am_gm_two",
        statement="∀ a b : ℝ, a ≥ 0 → b ≥ 0 → (a + b) / 2 ≥ (a * b).sqrt",
        statement_cn="两数的算术-几何平均不等式",
        domain="algebra",
        node_type=NodeType.THEOREM,
        status=NodeStatus.VERIFIED,
        difficulty=2,
        proof_script=["intros", "nlinarith [sq_nonneg (a.sqrt - b.sqrt)]"]
    )
    
    node3 = KnowledgeNode(
        id="cauchy_schwarz",
        statement="∀ a b c d : ℝ, (a*c + b*d)^2 ≤ (a^2 + b^2) * (c^2 + d^2)",
        statement_cn="柯西-施瓦茨不等式",
        domain="algebra",
        node_type=NodeType.DERIVED,
        status=NodeStatus.VERIFIED,
        difficulty=4,
        proof_script=["intros", "nlinarith [sq_nonneg (a*d - b*c)]"]
    )
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    
    # 添加推导关系
    graph.add_edge("sq_nonneg", "am_gm_two", "direct_use", "用 (√a - √b)² ≥ 0")
    graph.add_edge("sq_nonneg", "cauchy_schwarz", "direct_use", "用 (ad - bc)² ≥ 0")
    
    # 显示统计
    stats = graph.get_statistics()
    print(f"\n统计: {stats}")
    
    # 显示推导链
    print(f"\n{graph.visualize_ascii('cauchy_schwarz')}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
