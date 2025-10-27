import json
from typing import Dict, List, Any, Set
from .llm import chat_json
from .models import AgentTickOutput, EnvSpec

GROUP_SYS = """You simulate interactions among multiple agents at the SAME location inside a shared world.
OUTPUT MUST BE IN ENGLISH ONLY.
Output STRICT JSON ONLY per the schema. Never include code fences or extra text.
KEEP RESPONSES CONCISE TO AVOID TRUNCATION.

# Output schema (JSON object)
{
  "location": "current place",
  "notes": "brief summary (max 50 words)",
  "agents": [
    {
      "agent_id": "a1",
      "action": "brief action (max 10 words)",
      "speech": "speech (max 20 words, empty if not ALLOWED_SPEAKER)",
      "thoughts": "brief thought (max 15 words)",
      "location": "same or new",
      "memory": ["brief items (max 3)"]
    }
  ]
}

# Hard Constraints
- Only agents listed in ALLOWED_SPEAKERS may produce non-empty 'speech'.
- Prefer dialogue/coordination pairs from ALLOWED_PAIRS; avoid others unless unavoidable.
- Respect the environment rules & plausible social behavior.
- Keep each person's update coherent with their last known state.
- BREVITY IS CRITICAL: use short phrases, not full sentences.
"""

GROUP_USER_TPL = """[Environment]
Title: {env_title}
Description: {env_prompt}
Rules:
{env_rules}

[Location] {location}

[Public info from previous tick at this location]
{local_visible}

[Participants (last-tick snapshot)]
{agents_snapshot}

[Relation summary (between participants)]
{relations_summary}

[Hard constraints]
- ALLOWED_SPEAKERS: {allowed_speakers}
- ALLOWED_PAIRS: {allowed_pairs}

Simulate this tick's encounter in English only. Output the JSON object strictly as specified above.
"""

def _snapshot_line(last: AgentTickOutput) -> str:
    return (
        f"- {last.agent_id}: last_action={last.action!r}, last_speech={last.speech!r}, "
        f"state_keys={list(last.state.keys())}, location={last.location!r}"
    )

async def simulate_group_interaction(
    env: EnvSpec,
    location: str,
    tick: int,
    local_visible: str,
    participants: List[AgentTickOutput],
    relations_summary: List[str],
    allowed_speakers: List[str],
    allowed_pairs: List[List[str]],
    temperature: float = 0.7,
    max_tokens: int = 900,
) -> Dict[str, Any]:
    snapshot = "\n".join(_snapshot_line(p) for p in participants)
    rel_txt = "\n".join(relations_summary) if relations_summary else "(no direct relations known)"
    data = await chat_json(
        system=GROUP_SYS,
        messages=[{
            "role": "user",
            "content": GROUP_USER_TPL.format(
                env_title=env.title,
                env_prompt=env.prompt,
                env_rules="\n".join(f"- {r}" for r in env.rules) if env.rules else "(none)",
                location=location,
                local_visible=local_visible or "(none)",
                agents_snapshot=snapshot or "(none)",
                relations_summary=rel_txt,
                allowed_speakers=", ".join(allowed_speakers) if allowed_speakers else "(empty)",
                allowed_pairs=json.dumps(allowed_pairs, ensure_ascii=False),
            )
        }],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    # post-process: enforce hard mute
    data.setdefault("location", location)
    arr = data.get("agents") or []
    if not isinstance(arr, list):
        arr = []
    allowed: Set[str] = set(allowed_speakers or [])
    for item in arr:
        aid = str(item.get("agent_id", ""))
        if aid and aid not in allowed:
            item["speech"] = ""
    data["agents"] = arr
    return data
