"""
═══════════════════════════════════════════════════════════════════════════════
                        LLM Agent 模块
═══════════════════════════════════════════════════════════════════════════════

本模块提供与大语言模型的交互能力，用于：
- 生成数学猜想
- 建议证明 tactics
- 选择相关引理

支持模型：
- Qwen2.5-7B-Instruct（推荐）
- 任何 Hugging Face transformers 兼容模型

使用示例：
    >>> agent = create_llm_agent()  # 自动选择 Mock 或真实模型
    >>> tactics = agent.suggest_tactics("⊢ 1 + 1 = 2")
    >>> print(tactics)  # ['rfl', 'simp', ...]
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════════════════
# 可选依赖导入
# ═══════════════════════════════════════════════════════════════════════════

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️  Transformers 未安装，将使用 Mock 模式")
    print("   安装命令: pip install transformers")


# ═══════════════════════════════════════════════════════════════════════════
# 数据类定义
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class LLMResponse:
    """
    LLM 响应结果
    
    属性：
        content: 生成的文本内容
        confidence: 置信度 (0-1)
        metadata: 额外元数据
    """
    content: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return self.content
    
    def __bool__(self) -> bool:
        return bool(self.content.strip())


# ═══════════════════════════════════════════════════════════════════════════
# LLM Agent 基类
# ═══════════════════════════════════════════════════════════════════════════

class BaseLLMAgent:
    """
    LLM Agent 基类
    
    定义所有 Agent 必须实现的接口。
    """
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """生成文本"""
        raise NotImplementedError
    
    def suggest_tactics(
        self, 
        proof_state: str, 
        available_premises: Optional[List[str]] = None,
        num_suggestions: int = 5
    ) -> List[str]:
        """建议 tactics"""
        raise NotImplementedError
    
    def generate_conjecture(
        self, 
        domain: str,
        related_theorems: Optional[List[str]] = None,
        constraints: Optional[str] = None
    ) -> str:
        """生成猜想"""
        raise NotImplementedError


# ═══════════════════════════════════════════════════════════════════════════
# Qwen Agent（真实模型）
# ═══════════════════════════════════════════════════════════════════════════

class QwenAgent(BaseLLMAgent):
    """
    Qwen LLM Agent
    
    使用 Qwen2.5-7B-Instruct 进行数学推理任务。
    
    特点：
    - 支持 Lean 4 语法生成
    - 可配置温度和采样参数
    - 自动设备选择（CUDA/MPS/CPU）
    
    使用示例：
        >>> agent = QwenAgent()  # 需要 GPU
        >>> response = agent.generate("证明 1+1=2")
    """
    
    # 系统提示模板
    SYSTEM_PROMPTS = {
        "tactics": """你是一个 Lean 4 定理证明专家。
你的任务是根据当前证明状态，建议最有可能成功的 tactics。
请直接返回 tactics，每行一个，不要解释。""",
        
        "conjecture": """你是一个创造性的数学研究者，精通 Lean 4。
你的任务是生成有趣且可能为真的数学猜想。
请使用 Lean 4 语法，直接返回 theorem 语句。""",
        
        "select": """你是一个 Lean 定理证明专家。
你的任务是从候选引理中选择最相关的，用于证明给定目标。"""
    }
    
    def __init__(
        self, 
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        device: Optional[str] = None,
        max_length: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        load_model: bool = True
    ):
        """
        初始化 Qwen Agent
        
        参数：
            model_name: 模型名称或本地路径
            device: 设备（cuda/mps/cpu/auto）
            max_length: 最大生成长度
            temperature: 温度参数（越高越随机）
            top_p: top-p 采样参数
            load_model: 是否立即加载模型
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("需要安装 transformers: pip install transformers")
        
        self.model_name = model_name
        self.max_length = max_length
        self.temperature = temperature
        self.top_p = top_p
        
        # 自动选择设备（优先级: CUDA > MPS > CPU）
        if device:
            self.device = device
        elif TORCH_AVAILABLE and torch.cuda.is_available():
            self.device = "cuda"
        elif TORCH_AVAILABLE and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        
        self.tokenizer = None
        self.model = None
        
        if load_model:
            self._load_model()
    
    def _load_model(self):
        """加载模型和分词器"""
        print(f"🔄 加载模型: {self.model_name}")
        print(f"   设备: {self.device}")
        
        try:
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # 加载模型
            # CUDA 和 MPS 使用 float16，CPU 使用 float32
            dtype = torch.float16 if self.device in ("cuda", "mps") else torch.float32
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )
            
            # MPS 和 CPU 需要手动移动模型到设备
            if self.device in ("mps", "cpu"):
                self.model = self.model.to(self.device)
            
            print("✓ 模型加载完成")
            
        except Exception as e:
            print(f"✗ 模型加载失败: {e}")
            raise
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """
        生成文本
        
        参数：
            prompt: 用户提示
            system_prompt: 系统提示
            
        返回：
            LLM 响应
        """
        if self.model is None:
            self._load_model()
        
        try:
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # 应用聊天模板
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # 编码
            inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
            
            # 生成
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_length,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    do_sample=True
                )
            
            # 解码（只取新生成的部分）
            new_tokens = outputs[0][len(inputs.input_ids[0]):]
            response = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
            
            return LLMResponse(content=response.strip())
            
        except Exception as e:
            print(f"✗ 生成失败: {e}")
            return LLMResponse(content="", confidence=0.0)
    
    def suggest_tactics(
        self, 
        proof_state: str, 
        available_premises: Optional[List[str]] = None,
        num_suggestions: int = 5
    ) -> List[str]:
        """
        建议证明 tactics
        
        参数：
            proof_state: 当前证明状态
            available_premises: 可用的引理列表
            num_suggestions: 建议数量
            
        返回：
            tactics 列表（按可能性排序）
        """
        premises_str = ""
        if available_premises:
            premises_str = "可用引理:\n" + "\n".join(f"- {p}" for p in available_premises[:10])
        
        prompt = f"""当前证明状态：
```
{proof_state}
```

{premises_str}

请建议 {num_suggestions} 个最可能成功的 tactics。
每行一个，不要编号，不要解释。
"""
        
        response = self.generate(prompt, self.SYSTEM_PROMPTS["tactics"])
        
        # 解析响应
        tactics = []
        for line in response.content.split('\n'):
            line = self._clean_tactic(line)
            if line:
                tactics.append(line)
        
        return tactics[:num_suggestions]
    
    def generate_conjecture(
        self, 
        domain: str,
        related_theorems: Optional[List[str]] = None,
        constraints: Optional[str] = None
    ) -> str:
        """
        生成数学猜想
        
        参数：
            domain: 数学领域（如 "number_theory", "group_theory"）
            related_theorems: 相关定理（用于启发）
            constraints: 约束条件
            
        返回：
            Lean 4 格式的定理语句
        """
        theorems_str = ""
        if related_theorems:
            theorems_str = "相关定理:\n" + "\n".join(f"- {t}" for t in related_theorems[:5])
        
        constraints_str = f"\n约束: {constraints}" if constraints else ""
        
        prompt = f"""领域: {domain}

{theorems_str}
{constraints_str}

请生成一个有趣的数学猜想，使用 Lean 4 语法。
格式: theorem <名称> : <命题>

只返回定理语句，不要其他内容。
"""
        
        response = self.generate(prompt, self.SYSTEM_PROMPTS["conjecture"])
        return self._extract_theorem(response.content)
    
    def select_premises(
        self, 
        goal: str,
        candidate_premises: List[str],
        k: int = 10
    ) -> List[str]:
        """
        选择相关引理
        
        参数：
            goal: 证明目标
            candidate_premises: 候选引理列表
            k: 选择数量
            
        返回：
            选中的引理列表
        """
        if len(candidate_premises) <= k:
            return candidate_premises
        
        premises_str = "\n".join(f"{i+1}. {p}" for i, p in enumerate(candidate_premises))
        
        prompt = f"""目标: {goal}

候选引理:
{premises_str}

请选择最相关的 {k} 个引理，只返回引理名称，每行一个。
"""
        
        response = self.generate(prompt, self.SYSTEM_PROMPTS["select"])
        
        # 匹配响应中的引理名
        selected = []
        for line in response.content.split('\n'):
            line = line.strip()
            for premise in candidate_premises:
                if premise in line and premise not in selected:
                    selected.append(premise)
                    break
        
        return selected[:k]
    
    # ─────────────────────────────────────────────────────────────────────
    # 辅助方法
    # ─────────────────────────────────────────────────────────────────────
    
    def _clean_tactic(self, line: str) -> str:
        """清理 tactic 字符串"""
        line = line.strip()
        
        # 移除常见前缀
        for prefix in ['- ', '* ', '• ']:
            if line.startswith(prefix):
                line = line[len(prefix):]
        
        # 移除编号
        if line and line[0].isdigit():
            for sep in ['. ', ') ', ': ']:
                if sep in line:
                    line = line.split(sep, 1)[-1]
                    break
        
        # 移除代码块标记
        line = line.replace('```', '').replace('lean', '').strip()
        
        # 过滤无效内容
        if len(line) > 200 or line.startswith('#'):
            return ""
        
        return line
    
    def _extract_theorem(self, content: str) -> str:
        """从响应中提取定理语句"""
        content = content.strip()
        
        # 处理代码块
        if '```' in content:
            for part in content.split('```'):
                part = part.replace('lean', '').strip()
                if 'theorem' in part or 'lemma' in part:
                    content = part
                    break
        
        # 提取第一个定理
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('theorem', 'lemma')):
                return line
        
        return content


# ═══════════════════════════════════════════════════════════════════════════
# Mock Agent（演示用）
# ═══════════════════════════════════════════════════════════════════════════

class MockLLMAgent(BaseLLMAgent):
    """
    Mock LLM Agent
    
    用于测试和演示，不需要真实模型。
    返回预设的合理响应。
    
    使用示例：
        >>> agent = MockLLMAgent()
        >>> tactics = agent.suggest_tactics("⊢ n + 0 = n")
        >>> print(tactics)  # ['simp', 'rfl', ...]
    """
    
    # 预设的 tactic 响应
    DEFAULT_TACTICS = [
        "simp",
        "rfl", 
        "ring",
        "omega",
        "linarith",
        "norm_num",
        "trivial",
        "decide",
    ]
    
    # 根据目标特征的 tactic 建议
    GOAL_TACTICS = {
        "∀": ["intro", "intros"],
        "∃": ["use", "existsi"],
        "→": ["intro", "apply"],
        "∧": ["constructor", "And.intro"],
        "∨": ["left", "right", "Or.inl", "Or.inr"],
        "=": ["rfl", "simp", "ring", "norm_num"],
        "+": ["ring", "omega", "simp"],
        "*": ["ring", "simp"],
        "<": ["omega", "linarith"],
        "≤": ["omega", "linarith"],
    }
    
    def __init__(self, verbose: bool = False):
        """
        初始化 Mock Agent
        
        参数：
            verbose: 是否打印日志
        """
        self.verbose = verbose
        if verbose:
            print("📝 使用 Mock LLM Agent（无真实模型）")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Mock 生成"""
        if self.verbose:
            print(f"[Mock] 收到提示: {prompt[:50]}...")
        return LLMResponse(content="Mock response", confidence=0.5)
    
    def suggest_tactics(
        self, 
        proof_state: str, 
        available_premises: Optional[List[str]] = None,
        num_suggestions: int = 5
    ) -> List[str]:
        """
        Mock tactic 建议
        
        根据证明状态特征返回合理的 tactics。
        """
        tactics = []
        
        # 根据目标特征添加 tactics
        for symbol, symbol_tactics in self.GOAL_TACTICS.items():
            if symbol in proof_state:
                tactics.extend(symbol_tactics)
        
        # 添加默认 tactics
        for t in self.DEFAULT_TACTICS:
            if t not in tactics:
                tactics.append(t)
        
        # 如果有可用引理，添加 apply/exact
        if available_premises:
            for premise in available_premises[:3]:
                tactics.append(f"apply {premise}")
                tactics.append(f"exact {premise}")
        
        return tactics[:num_suggestions]
    
    def generate_conjecture(
        self, 
        domain: str,
        related_theorems: Optional[List[str]] = None,
        constraints: Optional[str] = None
    ) -> str:
        """Mock 猜想生成"""
        conjectures = {
            "nat": "theorem mock_nat : ∀ n m : Nat, n + m = m + n",
            "int": "theorem mock_int : ∀ n : Int, n + 0 = n",
            "list": "theorem mock_list : ∀ l : List α, l.reverse.reverse = l",
            "group": "theorem mock_group : ∀ g : G, g * 1 = g",
        }
        
        domain_lower = domain.lower()
        for key, conj in conjectures.items():
            if key in domain_lower:
                return conj
        
        return f"theorem mock_{domain} : True"
    
    def select_premises(
        self, 
        goal: str,
        candidate_premises: List[str],
        k: int = 10
    ) -> List[str]:
        """Mock 引理选择"""
        # 简单的关键词匹配
        selected = []
        goal_lower = goal.lower()
        
        for premise in candidate_premises:
            premise_lower = premise.lower()
            # 如果引理名包含目标中的关键词
            for keyword in ['add', 'mul', 'comm', 'assoc', 'zero', 'one']:
                if keyword in goal_lower and keyword in premise_lower:
                    selected.append(premise)
                    break
        
        # 补充其他引理
        for premise in candidate_premises:
            if premise not in selected:
                selected.append(premise)
        
        return selected[:k]


# ═══════════════════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════════════════

def create_llm_agent(
    use_mock: bool = True,
    model_name: str = "Qwen/Qwen2.5-7B-Instruct",
    **kwargs
) -> BaseLLMAgent:
    """
    创建 LLM Agent 的便捷函数
    
    参数：
        use_mock: 是否使用 Mock 模式
        model_name: 模型名称（use_mock=False 时有效）
        **kwargs: 传递给 Agent 的其他参数
        
    返回：
        配置好的 Agent 实例
        
    示例：
        >>> agent = create_llm_agent()  # Mock 模式
        >>> agent = create_llm_agent(use_mock=False)  # 真实模型
    """
    if use_mock:
        return MockLLMAgent(verbose=kwargs.get('verbose', False))
    
    if not TRANSFORMERS_AVAILABLE:
        print("⚠️  Transformers 未安装，回退到 Mock 模式")
        return MockLLMAgent(verbose=True)
    
    return QwenAgent(model_name=model_name, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# 测试代码
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("LLM Agent 测试")
    print("=" * 60)
    
    # 使用 Mock Agent
    agent = create_llm_agent(use_mock=True)
    
    # 测试 1：Tactic 建议
    print("\n【测试 1】Tactic 建议")
    state = "⊢ ∀ n : Nat, n + 0 = n"
    premises = ["Nat.add_zero", "Nat.add_comm"]
    tactics = agent.suggest_tactics(state, premises, num_suggestions=5)
    print(f"证明状态: {state}")
    print(f"建议 tactics: {tactics}")
    
    # 测试 2：猜想生成
    print("\n【测试 2】猜想生成")
    conjecture = agent.generate_conjecture(
        domain="nat",
        related_theorems=["Nat.add_comm", "Nat.mul_comm"]
    )
    print(f"生成的猜想: {conjecture}")
    
    # 测试 3：引理选择
    print("\n【测试 3】引理选择")
    goal = "⊢ n + m = m + n"
    candidates = ["Nat.add_comm", "Nat.mul_comm", "Nat.add_assoc", "Nat.sub_zero"]
    selected = agent.select_premises(goal, candidates, k=2)
    print(f"目标: {goal}")
    print(f"选择的引理: {selected}")
    
    print("\n✓ 所有测试完成")
