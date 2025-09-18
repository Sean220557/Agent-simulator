from typing import Optional
from .llm import chat_json
from .models import EnvSpec


ENV_GEN_SYS = (
    "You are a world builder. "
    "Given a brief hint, produce a consistent, simulation-ready environment."
)

ENV_GEN_USER_TEMPLATE = """基于以下简述生成一个可仿真的环境：
【简述】
{hint}

请输出严格 JSON：
{{
  "title": "环境标题",
  "prompt": "对环境的详细描述，包含空间结构、资源、事件钩子、时间流速、危险/约束等。",
  "rules": ["规则1", "规则2", "……（可为空数组）"]
}}
"""


async def generate_env_from_hint(hint: str, temperature: float = 0.4) -> EnvSpec:
    data = await chat_json(
        system=ENV_GEN_SYS,
        messages=[
            {"role": "user", "content": ENV_GEN_USER_TEMPLATE.format(hint=hint)}
        ],
        temperature=temperature,
        max_tokens=700,
    )
    title = data.get("title") or "Generated Environment"
    prompt = data.get("prompt") or ""
    rules = data.get("rules") or []
    return EnvSpec(title=title, prompt=prompt, rules=rules)


def merge_env(base: EnvSpec, extra_prompt: Optional[str] = None) -> EnvSpec:
    if not extra_prompt:
        return base
    merged = EnvSpec(
        title=base.title,
        prompt=base.prompt + "\n\n[EXTRA]\n" + extra_prompt,
        rules=base.rules,
    )
    return merged
