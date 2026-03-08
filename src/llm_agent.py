"""
═══════════════════════════════════════════════════════════════════════════════
                        LLM Agent 模块
═══════════════════════════════════════════════════════════════════════════════

本模块提供与大语言模型的交互能力，用于：
- 生成数学猜想
- 建议证明 tactics
- 选择相关引理
- 将数学问题翻译为 Lean 4 语言
- 自动证明定理（结合 Lean 4 / Mathlib）

支持模型：
- qwen3-coder:30b（默认，通过 Ollama）
- Qwen2.5-7B-Instruct（HuggingFace transformers）
- 任何 Ollama 兼容模型

使用示例：
    >>> agent = create_llm_agent()  # 默认使用 Ollama + qwen3-coder:30b
    >>> tactics = agent.suggest_tactics("⊢ 1 + 1 = 2")
    >>> print(tactics)  # ['rfl', 'simp', ...]
    >>>
    >>> # 翻译数学问题为 Lean 4
    >>> lean_code = agent.translate_to_lean4("对于所有自然数 n，n + 0 = n")
    >>> print(lean_code)
"""

import json
import re
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════════════════
# 可选依赖导入
# ═══════════════════════════════════════════════════════════════════════════

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

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
    
    def suggest_tactics_with_error_feedback(
        self,
        proof_state: str,
        error_message: str,
        failed_tactics: List[str],
        available_premises: Optional[List[str]] = None,
        num_suggestions: int = 5
    ) -> List[str]:
        """
        根据错误诊断信息建议 tactics（增强版）
        
        与 suggest_tactics 的区别：
        - 接收上一步的 Lean 错误信息
        - 接收之前失败的 tactics 列表
        - LLM 可据此针对性地修正策略
        
        默认实现：回退到普通 suggest_tactics
        """
        return self.suggest_tactics(proof_state, available_premises, num_suggestions)
    
    def generate_conjecture(
        self, 
        domain: str,
        related_theorems: Optional[List[str]] = None,
        constraints: Optional[str] = None
    ) -> str:
        """生成猜想"""
        raise NotImplementedError

    def translate_to_lean4(self, math_statement: str) -> str:
        """将自然语言数学命题翻译为 Lean 4 代码"""
        raise NotImplementedError

    def prove_theorem(
        self,
        theorem_statement: str,
        lean_env=None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """自动证明定理（翻译 + 搜索证明）"""
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
# Ollama Agent（默认，通过本地 Ollama 服务调用 qwen3-coder:30b）
# ═══════════════════════════════════════════════════════════════════════════

class OllamaAgent(BaseLLMAgent):
    """
    Ollama LLM Agent
    
    通过 Ollama REST API 调用本地部署的大语言模型，默认使用 qwen3-coder:30b。
    
    特点：
    - 通过本地 Ollama 服务运行，无需 GPU 显存管理
    - 支持 Lean 4 语法生成与数学推理
    - 支持将自然语言翻译为 Lean 4 代码
    - 支持自动定理证明流程
    
    使用示例：
        >>> agent = OllamaAgent()
        >>> response = agent.generate("证明 1+1=2")
        >>> lean_code = agent.translate_to_lean4("对于所有自然数 n, n + 0 = n")
    """
    
    SYSTEM_PROMPTS = {
        "tactics": """你是一个 Lean 4 定理证明专家，精通 Mathlib 库。
你的任务是根据当前证明状态，建议最有可能成功的 tactics。
优先使用 Mathlib 中的 tactics（如 simp, ring, omega, linarith, norm_num, aesop, exact?, apply?）。
请直接返回 tactics，每行一个，不要编号，不要解释。""",

        "conjecture": """你是一个创造性的数学研究者，精通 Lean 4 和 Mathlib。
你的任务是生成有趣且可能为真的数学猜想。
请使用 Lean 4 语法，直接返回 theorem 语句。""",

        "select": """你是一个 Lean 定理证明专家，精通 Mathlib。
你的任务是从候选引理中选择最相关的，用于证明给定目标。""",

        "translate": """你是一个精通数学和 Lean 4 的翻译专家。
你的任务是将自然语言描述的数学命题准确翻译为 Lean 4 代码。

要求：
1. 使用标准 Lean 4 语法
2. 合理使用 Mathlib 中的类型和定义（如 Nat, Int, Real, List 等）
3. 导入必要的 Mathlib 模块
4. 输出完整可编译的 Lean 4 代码

输出格式：
```lean
import Mathlib...

theorem <名称> : <命题> := by
  sorry
```

只返回代码块，不要其他解释。""",

        "prove": """你是一个 Lean 4 定理证明专家，精通 Mathlib 库中的所有 tactics 和引理。
给定一个 Lean 4 定理和当前证明状态，请写出完整的证明。

要求：
1. 使用 Mathlib 中可用的 tactics
2. 常用 tactics 包括: simp, ring, omega, linarith, norm_num, aesop, exact?, apply?, 
   constructor, intro, cases, induction, rw, have, calc, ext, funext
3. 可以组合多个 tactics
4. 输出完整的 tactic 证明序列

输出格式（每行一个 tactic，不要编号和解释）：
tactic1
tactic2
...""",

        "error_diagnosis": """你是一个 Lean 4 定理证明诊断专家，精通 Mathlib 库。
你的任务是根据 Lean 编译器返回的错误信息，诊断问题并建议修正后的 tactics。

关键诊断能力：
- 类型不匹配：建议类型转换 tactics (norm_cast, push_cast, simp only [...])
- 未知标识符：检查命名空间，建议 exact? 或 apply? 搜索
- tactic 失败：分析失败原因，建议替代 tactic
- 未解决子目标：建议补充步骤或使用 <;> 组合子

务必避免已经失败过的 tactics，提出全新的证明方向。
每行输出一个 tactic，不要编号，不要解释。""",
    }
    
    def __init__(
        self,
        model_name: str = "qwen3-coder:30b",
        base_url: str = "http://127.0.0.1:11434",
        max_length: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.9,
        verbose: bool = False
    ):
        if not REQUESTS_AVAILABLE:
            raise ImportError("需要安装 requests: pip install requests")
        
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.max_length = max_length
        self.temperature = temperature
        self.top_p = top_p
        self.verbose = verbose
        
        # 验证 Ollama 服务连通性
        self._check_ollama()
    
    def _check_ollama(self):
        """检查 Ollama 服务是否可用"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            
            # 检查模型是否已下载（允许带/不带 :latest 后缀匹配）
            base_name = self.model_name.split(":")[0]
            found = any(base_name in m for m in models)
            if found:
                print(f"✓ Ollama 已连接，模型 {self.model_name} 可用")
            else:
                print(f"⚠️  Ollama 已连接，但模型 {self.model_name} 未找到")
                print(f"   已有模型: {', '.join(models[:5])}")
                print(f"   请运行: ollama pull {self.model_name}")
        except requests.ConnectionError:
            print(f"⚠️  无法连接 Ollama ({self.base_url})")
            print("   请确保 Ollama 正在运行: ollama serve")
        except Exception as e:
            print(f"⚠️  Ollama 检查失败: {e}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """通过 Ollama API 生成文本"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": self.max_length,
                "temperature": self.temperature,
                "top_p": self.top_p,
            }
        }
        
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300  # 大模型推理可能较慢
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            
            if self.verbose:
                print(f"[Ollama] 响应长度: {len(content)}")
            
            return LLMResponse(content=content.strip())
        except requests.ConnectionError:
            print("✗ 无法连接 Ollama 服务，请确保 ollama serve 正在运行")
            return LLMResponse(content="", confidence=0.0)
        except requests.Timeout:
            print("✗ Ollama 请求超时")
            return LLMResponse(content="", confidence=0.0)
        except Exception as e:
            print(f"✗ Ollama 生成失败: {e}")
            return LLMResponse(content="", confidence=0.0)
    
    def suggest_tactics(
        self, 
        proof_state: str, 
        available_premises: Optional[List[str]] = None,
        num_suggestions: int = 5
    ) -> List[str]:
        """建议证明 tactics"""
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
        
        tactics = []
        for line in response.content.split('\n'):
            line = self._clean_tactic(line)
            if line:
                tactics.append(line)
        return tactics[:num_suggestions]
    
    def suggest_tactics_with_error_feedback(
        self,
        proof_state: str,
        error_message: str,
        failed_tactics: List[str],
        available_premises: Optional[List[str]] = None,
        num_suggestions: int = 8
    ) -> List[str]:
        """
        根据 Lean 错误诊断信息建议修正后的 tactics
        
        将 Lean 返回的错误信息和之前失败的 tactics 一起发给 LLM，
        让其针对性地生成新的、不同的 tactics 建议。
        """
        # 如果没有错误信息，回退到普通建议
        if not error_message and not failed_tactics:
            return self.suggest_tactics(proof_state, available_premises, num_suggestions)
        
        premises_str = ""
        if available_premises:
            premises_str = "可用引理:\n" + "\n".join(f"- {p}" for p in available_premises[:10])
        
        failed_str = ""
        if failed_tactics:
            failed_str = "以下 tactics 已经尝试过但失败了，请不要再建议这些：\n" + "\n".join(f"  ✗ {t}" for t in failed_tactics)
        
        error_str = ""
        if error_message:
            # 分类错误类型并给出针对性提示
            error_type = self._classify_lean_error(error_message)
            error_str = f"Lean 报错信息：{error_message}\n错误类型分析：{error_type}"
        
        prompt = f"""当前证明状态：
```
{proof_state}
```

{error_str}

{failed_str}

{premises_str}

请根据以上错误信息，建议 {num_suggestions} 个不同的、针对此错误修正后的 tactics。
注意要避免之前失败的 tactics，尝试新的证明方向。
每行一个，不要编号，不要解释。
"""
        response = self.generate(prompt, self.SYSTEM_PROMPTS["error_diagnosis"])
        
        tactics = []
        for line in response.content.split('\n'):
            line = self._clean_tactic(line)
            if line and line not in failed_tactics:
                tactics.append(line)
        return tactics[:num_suggestions]
    
    def _classify_lean_error(self, error_message: str) -> str:
        """
        分类 Lean 错误类型并给出诊断提示
        
        帮助 LLM 理解错误本质，从而生成更有针对性的修正。
        """
        error_lower = error_message.lower()
        
        if "type mismatch" in error_lower:
            return ("类型不匹配 — 表达式的类型与目标不一致。"
                    "考虑使用 `simp`、`norm_cast`、`push_cast` 进行类型转换，"
                    "或用 `show` 明确指定目标类型。")
        
        if "unknown identifier" in error_lower or "unknown constant" in error_lower:
            return ("未知标识符 — 引用了不存在的定理或定义。"
                    "检查名称拼写，尝试用 `exact?` 或 `apply?` 自动搜索。")
        
        if "tactic 'ring' failed" in error_lower:
            return ("ring 策略失败 — 目标可能不是纯环等式。"
                    "尝试先用 `simp` 化简，或用 `field_simp` 处理分式，"
                    "或用 `nlinarith` 处理含不等式的情况。")
        
        if "tactic 'simp' made no progress" in error_lower:
            return ("simp 无效果 — 简化规则不适用于当前目标。"
                    "尝试 `simp only [...]` 指定具体引理，"
                    "或换用 `ring`、`omega`、`norm_num`。")
        
        if "tactic 'omega' failed" in error_lower:
            return ("omega 失败 — 目标可能不是线性整数算术。"
                    "尝试 `linarith` 或 `nlinarith`（支持非线性），"
                    "或先用 `have` 引入中间结论。")
        
        if "unsolved goals" in error_lower:
            return ("仍有未解决的子目标 — 当前 tactic 未完全关闭证明。"
                    "可能需要额外的 tactic 步骤，或使用 `<;>` 组合子处理所有分支。")
        
        if "expected token" in error_lower or "unexpected token" in error_lower:
            return ("语法错误 — tactic 语法不正确。"
                    "检查括号、关键字拼写，确保使用 Lean 4 语法。")
        
        if "failed to synthesize" in error_lower:
            return ("类型类合成失败 — 缺少必要的类型类实例。"
                    "尝试添加 `[instance]` 或用 `@` 显式传递实例。")
        
        if "function expected" in error_lower:
            return ("函数应用错误 — 对非函数类型进行了应用。"
                    "检查表达式结构，可能需要调整参数。")
        
        return f"其他错误 — 请根据错误信息 '{error_message[:100]}' 调整策略。"
    
    def generate_conjecture(
        self, 
        domain: str,
        related_theorems: Optional[List[str]] = None,
        constraints: Optional[str] = None
    ) -> str:
        """生成数学猜想"""
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
        """选择相关引理"""
        if len(candidate_premises) <= k:
            return candidate_premises
        
        premises_str = "\n".join(f"{i+1}. {p}" for i, p in enumerate(candidate_premises))
        prompt = f"""目标: {goal}

候选引理:
{premises_str}

请选择最相关的 {k} 个引理，只返回引理名称，每行一个。
"""
        response = self.generate(prompt, self.SYSTEM_PROMPTS["select"])
        
        selected = []
        for line in response.content.split('\n'):
            line = line.strip()
            for premise in candidate_premises:
                if premise in line and premise not in selected:
                    selected.append(premise)
                    break
        return selected[:k]
    
    def translate_to_lean4(self, math_statement: str) -> str:
        """
        将自然语言数学命题翻译为 Lean 4 代码
        
        参数：
            math_statement: 自然语言描述的数学命题
            
        返回：
            Lean 4 格式的代码（含 import 和 theorem 声明）
        """
        prompt = f"""请将以下数学命题翻译为 Lean 4 代码：

{math_statement}

要求：
- 使用 Mathlib 中的标准类型和定义
- 包含必要的 import 语句
- theorem 名称请使用有意义的英文名
- 证明部分用 sorry 占位
"""
        response = self.generate(prompt, self.SYSTEM_PROMPTS["translate"])
        return self._extract_lean_code(response.content)
    
    def prove_theorem(
        self,
        theorem_statement: str,
        lean_env=None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        自动证明定理的完整流程
        
        步骤：
        1. 将自然语言转换为 Lean 4 代码（如果输入不是 Lean 代码）
        2. 使用 LLM 生成证明 tactics
        3. 调用 Lean 验证证明
        4. 如果失败，根据错误信息修正并重试
        
        参数：
            theorem_statement: 定理描述（自然语言或 Lean 4 代码）
            lean_env: LeanEnvironment 实例（如果为 None 则创建）
            max_retries: 最大重试次数
            
        返回：
            证明结果字典
        """
        result = {
            "success": False,
            "original_statement": theorem_statement,
            "lean_code": "",
            "proof": "",
            "attempts": [],
            "error": None,
        }
        
        # 步骤 1：判断是否需要翻译
        is_lean = self._is_lean_code(theorem_statement)
        if is_lean:
            lean_code = theorem_statement
            print("📄 检测到 Lean 4 代码，直接使用")
        else:
            print("🔄 将数学命题翻译为 Lean 4 ...")
            lean_code = self.translate_to_lean4(theorem_statement)
            print(f"📄 Lean 4 代码:\n{lean_code}\n")
        
        result["lean_code"] = lean_code
        
        # 步骤 2：创建 Lean 环境（如果未提供）
        if lean_env is None:
            from .lean_env import create_lean_env
            lean_env = create_lean_env()
        
        # 步骤 3：迭代尝试证明
        for attempt in range(max_retries):
            print(f"\n{'─'*40}")
            print(f"🔍 证明尝试 {attempt + 1}/{max_retries}")
            
            attempt_result = self._attempt_proof(lean_code, lean_env, attempt)
            result["attempts"].append(attempt_result)
            
            if attempt_result["success"]:
                result["success"] = True
                result["proof"] = attempt_result["proof"]
                print(f"✓ 证明成功！")
                print(f"  证明:\n{attempt_result['proof']}")
                break
            else:
                error = attempt_result.get("error", "未知错误")
                print(f"✗ 尝试 {attempt + 1} 失败: {error}")
                
                if attempt < max_retries - 1:
                    # 根据错误信息让 LLM 修正
                    lean_code = self._fix_proof_from_error(
                        lean_code, 
                        attempt_result.get("tried_tactics", []),
                        error
                    )
                    result["lean_code"] = lean_code
        
        if not result["success"]:
            result["error"] = "所有尝试均失败"
        
        return result
    
    def _attempt_proof(self, lean_code: str, lean_env, attempt_num: int) -> Dict[str, Any]:
        """尝试一次证明"""
        # 提取 theorem 声明部分
        theorem_decl = self._extract_theorem_declaration(lean_code)
        if not theorem_decl:
            return {"success": False, "error": "无法从代码中提取 theorem 声明", "tried_tactics": []}
        
        # 初始化证明状态
        state = lean_env.initialize_proof(theorem_decl)
        if state is None:
            return {"success": False, "error": "无法初始化证明状态", "tried_tactics": []}
        
        # 用 LLM 生成完整证明策略
        proof_prompt = f"""请为以下 Lean 4 定理写出完整证明：

```lean
{lean_code}
```

当前证明状态：
{state}

请直接给出 tactic 证明序列，每行一个 tactic，不要解释。如果需要 sorry，请说明原因。
"""
        response = self.generate(proof_prompt, self.SYSTEM_PROMPTS["prove"])
        tactics = [self._clean_tactic(l) for l in response.content.split('\n') if self._clean_tactic(l)]
        
        if not tactics:
            return {"success": False, "error": "LLM 未生成有效 tactics", "tried_tactics": []}
        
        # 逐步执行 tactics
        tried = []
        current_state = state
        for tactic in tactics:
            if tactic == "sorry":
                continue
            
            result = lean_env.apply_tactic(current_state, tactic)
            tried.append({"tactic": tactic, "success": result.success})
            
            if result.success:
                current_state = result.new_state
                if current_state.is_finished:
                    proof_text = "\n".join(t["tactic"] for t in tried if t["success"])
                    return {"success": True, "proof": proof_text, "tried_tactics": tried}
            # 即使单个 tactic 失败也继续尝试后续的
        
        # 也尝试用 Lean subprocess 一次性验证完整证明
        full_proof = "\n  ".join(t for t in tactics if t != "sorry")
        proof_code = lean_code.replace("sorry", full_proof)
        
        lean_check = lean_env.check_proof(proof_code) if hasattr(lean_env, 'check_proof') else None
        if lean_check and lean_check.get("success"):
            return {"success": True, "proof": full_proof, "tried_tactics": tried}
        
        error_msg = lean_check.get("error", "tactics 执行后目标未完全关闭") if lean_check else "tactics 执行后目标未完全关闭"
        return {"success": False, "error": error_msg, "tried_tactics": tried}
    
    def _fix_proof_from_error(self, lean_code: str, tried_tactics: List[Dict], error: str) -> str:
        """根据错误信息让 LLM 修正证明"""
        tried_desc = "\n".join(
            f"  {'✓' if t['success'] else '✗'} {t['tactic']}" 
            for t in tried_tactics
        )
        
        prompt = f"""之前尝试证明以下 Lean 4 代码失败了：

```lean
{lean_code}
```

已尝试的 tactics：
{tried_desc}

错误信息：{error}

请重新生成完整的 Lean 4 代码（含证明），修正之前的问题。
注意：必须包含完整的 import 语句和 theorem 声明。证明不要用 sorry。
"""
        response = self.generate(prompt, self.SYSTEM_PROMPTS["prove"])
        new_code = self._extract_lean_code(response.content)
        return new_code if new_code.strip() else lean_code
    
    # ─────────────────────────────────────────────────────────────────────
    # 辅助方法
    # ─────────────────────────────────────────────────────────────────────
    
    def _clean_tactic(self, line: str) -> str:
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
    
    def _extract_theorem(self, content: str) -> str:
        """从响应中提取定理语句"""
        content = content.strip()
        if '```' in content:
            for part in content.split('```'):
                part = part.replace('lean', '').strip()
                if 'theorem' in part or 'lemma' in part:
                    content = part
                    break
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('theorem', 'lemma')):
                return line
        return content
    
    def _extract_lean_code(self, content: str) -> str:
        """从 LLM 响应中提取 Lean 4 代码块"""
        content = content.strip()
        # 匹配 ```lean ... ``` 代码块
        pattern = r'```(?:lean4?|Lean)?\s*\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            return matches[0].strip()
        
        # 如果没有代码块，但包含 import 或 theorem，直接返回
        if 'import' in content or 'theorem' in content or 'lemma' in content:
            # 去除可能的说明文字（只保留代码部分）
            lines = []
            in_code = False
            for line in content.split('\n'):
                stripped = line.strip()
                if stripped.startswith(('import', 'open', 'theorem', 'lemma', 'def', 'example', '#', 'namespace', 'section', 'end', 'variable', 'noncomputable')):
                    in_code = True
                if in_code:
                    lines.append(line)
            if lines:
                return '\n'.join(lines)
        return content
    
    def _extract_theorem_declaration(self, lean_code: str) -> str:
        """从 Lean 代码中提取 theorem 声明行"""
        for line in lean_code.split('\n'):
            stripped = line.strip()
            if stripped.startswith(('theorem', 'lemma')):
                # 确保有 := by 结尾
                if ':= by' not in stripped:
                    stripped = stripped.rstrip().rstrip('where').rstrip()
                    if not stripped.endswith(':= by'):
                        stripped += ' := by'
                return stripped
        return ""
    
    def _is_lean_code(self, text: str) -> bool:
        """判断输入是否已经是 Lean 4 代码"""
        text = text.strip()
        lean_keywords = ['theorem', 'lemma', 'import', 'def ', 'example', '#check']
        return any(text.startswith(kw) or f'\n{kw}' in text for kw in lean_keywords)


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
    use_mock: bool = False,
    backend: str = "ollama",
    model_name: str = "qwen3-coder:30b",
    **kwargs
) -> BaseLLMAgent:
    """
    创建 LLM Agent 的便捷函数
    
    参数：
        use_mock: 是否使用 Mock 模式
        backend: 后端类型 ("ollama" / "transformers")
        model_name: 模型名称，默认 qwen3-coder:30b
        **kwargs: 传递给 Agent 的其他参数
        
    返回：
        配置好的 Agent 实例
        
    示例：
        >>> agent = create_llm_agent()  # 默认使用 Ollama + qwen3-coder:30b
        >>> agent = create_llm_agent(use_mock=True)  # Mock 模式
        >>> agent = create_llm_agent(backend="transformers", model_name="Qwen/Qwen2.5-7B-Instruct")
    """
    if use_mock:
        return MockLLMAgent(verbose=kwargs.get('verbose', False))
    
    if backend == "ollama":
        if not REQUESTS_AVAILABLE:
            print("⚠️  requests 未安装，回退到 Mock 模式")
            print("   安装命令: pip install requests")
            return MockLLMAgent(verbose=True)
        return OllamaAgent(model_name=model_name, **kwargs)
    
    elif backend == "transformers":
        if not TRANSFORMERS_AVAILABLE:
            print("⚠️  Transformers 未安装，回退到 Mock 模式")
            return MockLLMAgent(verbose=True)
        return QwenAgent(model_name=model_name, **kwargs)
    
    else:
        print(f"⚠️  未知后端 {backend}，回退到 Mock 模式")
        return MockLLMAgent(verbose=True)


# ═══════════════════════════════════════════════════════════════════════════
# 测试代码
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("LLM Agent 测试")
    print("=" * 60)
    
    # 使用 Mock Agent 进行基本测试
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
    
    # 测试 4：Ollama Agent（需要 Ollama 服务运行）
    print("\n【测试 4】Ollama Agent (qwen3-coder:30b)")
    try:
        ollama_agent = create_llm_agent()
        lean_code = ollama_agent.translate_to_lean4("对于所有自然数 n, n + 0 = n")
        print(f"翻译结果:\n{lean_code}")
    except Exception as e:
        print(f"跳过 (Ollama 未运行): {e}")
    
    print("\n✓ 所有测试完成")
