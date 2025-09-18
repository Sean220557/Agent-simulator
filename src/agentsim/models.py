from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class AgentPersona(BaseModel):
    id: str = Field(..., description="agent 唯一 ID")
    name: str = Field(..., description="agent 昵称（作为唯一键）")
    description: str = Field(..., description="画像/设定/背景/目标")
    initial_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="初始状态（如位置、心情、体力、道具等）"
    )
    initial_memory: List[str] = Field(
        default_factory=list,
        description="初始记忆（若为空可由 LLM 自动生成）"
    )
    # 社会关系：以 agent_id 为键
    relations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @validator("relations")
    def _no_self_loop(cls, v, values):
        aid = values.get("id")
        if aid and aid in v:
            v.pop(aid, None)
        for k, rec in v.items():
            s = rec.get("strength", 0.0)
            try:
                s = float(s)
            except Exception:
                s = 0.0
            rec["strength"] = max(0.0, min(1.0, s))
            rec["type"] = str(rec.get("type", "stranger"))
        return v


class EnvSpec(BaseModel):
    title: str = "Default Environment"
    prompt: str = Field(..., description="对世界的详细描述/规则/资源/空间布局等")
    rules: List[str] = Field(default_factory=list, description="补充规则，如安全/距离/视野/胜负条件等")


class AgentTickOutput(BaseModel):
    agent_id: str
    tick: int
    action: str
    speech: str
    state: Dict[str, Any]
    thoughts: str
    location: str
    memory: List[str] = Field(default_factory=list, description="本 tick 的记忆（新增或强化点）")


class SimulationConfig(BaseModel):
    steps: int = 5
    temperature: float = 0.7
    max_tokens: int = 512
    visibility: str = Field(
        default="local",
        description="可见性：'global' 或 'local'"
    )
    relation_influence: float = Field(
        default=0.8,
        description="关系硬约束强度 0~1；1 表示严格按关系决定谁发声/互动"
    )

    @validator("steps")
    def _steps_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("steps 必须 > 0")
        return v

    @validator("relation_influence")
    def _alpha_range(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError("relation_influence 必须在 [0,1]")
        return v


class SimulationInput(BaseModel):
    agents: List[AgentPersona]
    env_hint: Optional[str] = Field(
        default=None,
        description="若提供，则用 LLM 生成完整 Env；否则需要直接给 env_spec"
    )
    env_spec: Optional[EnvSpec] = None
    config: SimulationConfig = SimulationConfig()

    @validator("agents")
    def _agents_non_empty(cls, v: List[AgentPersona]) -> List[AgentPersona]:
        if not v:
            raise ValueError("至少需要一个 agent")
        return v

    @validator("env_spec")
    def _env_or_hint(cls, v, values):
        if not v and not values.get("env_hint"):
            raise ValueError("必须提供 env_spec 或 env_hint")
        return v
