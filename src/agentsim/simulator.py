import asyncio
import json
from typing import Dict, List, Any

from .llm import chat_json
from .models import AgentPersona, EnvSpec, SimulationConfig, AgentTickOutput
from .logger import append_agent_log, append_event_log
from .world import group_by_location, make_local_context
from .interaction import simulate_group_interaction
from .relations import (
    build_relation_graph,
    local_relation_summary,
    pick_speakers_hard,
    pair_trust_weight,
)

AGENT_SYS_TEMPLATE = """You are simulating ONE specific agent inside a shared world.
ALL OUTPUT MUST BE IN ENGLISH ONLY.
Decide the agent's immediate intention for this tick (may include moving), then output STRICT JSON for this agent.

# Output schema (single JSON object)
{
  "action": "action in English",
  "speech": "spoken words in English; empty string if none",
  "state": { "key": "value" },
  "thoughts": "inner monologue in English",
  "location": "resulting location at the end of this tick (keep if not moving)",
  "memory": ["memory items for this tick, in English"]
}

Rules:
- English only. No code fences. Exactly one JSON object.
- Respect environment rules & local visibility.
- No secret info from other minds.
"""

AGENT_USER_TEMPLATE = """[Environment]
Title: {env_title}
Description: {env_prompt}
Rules:
{env_rules}

[Visible public context at your location last tick]
{visible_context}

[You are the agent]
ID: {agent_id}
Name: {agent_name}
Persona: {agent_desc}
Initial Memory: {initial_memory}
Accumulated Memory (previous ticks): {acc_memory}
Last State: {last_state}
Last Location: {last_location}

[Tick]
Current tick = {tick}

Output strictly the JSON per schema above (English only). You may decide to move to a reasonable place.
"""

async def simulate_step_for_agent(
    agent: AgentPersona,
    env: EnvSpec,
    config: SimulationConfig,
    tick: int,
    history: Dict[str, List[AgentTickOutput]],
) -> AgentTickOutput:
    prev_items = history.get(agent.id, [])
    last_state_dict: Dict[str, Any] = prev_items[-1].state if prev_items else agent.initial_state
    last_location = prev_items[-1].location if prev_items else agent.initial_state.get("location", "Start")
    visible = make_local_context(tick, history, focus_agent_id=agent.id, focus_location=last_location)

    acc_memory: List[str] = list(agent.initial_memory)
    for it in prev_items:
        acc_memory.extend(it.memory)

    data = await chat_json(
        system=AGENT_SYS_TEMPLATE,
        messages=[{
            "role": "user",
            "content": AGENT_USER_TEMPLATE.format(
                env_title=env.title,
                env_prompt=env.prompt,
                env_rules="\n".join(f"- {r}" for r in env.rules) if env.rules else "(none)",
                visible_context=visible or "(none)",
                agent_id=agent.id,
                agent_name=agent.name,
                agent_desc=agent.description,
                initial_memory=json.dumps(agent.initial_memory, ensure_ascii=False),
                acc_memory=json.dumps(acc_memory, ensure_ascii=False),
                last_state=json.dumps(last_state_dict, ensure_ascii=False),
                last_location=last_location,
                tick=tick,
            ),
        }],
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    out = AgentTickOutput(
        agent_id=agent.id,
        tick=tick,
        action=str(data.get("action", "")).strip(),
        speech=str(data.get("speech", "")).strip(),
        state=data.get("state") or {},
        thoughts=str(data.get("thoughts", "")).strip(),
        location=str(data.get("location", "") or last_location),
        memory=list(data.get("memory") or []),
    )

    append_agent_log(agent.name, {
        "type": "tick.intent",
        "tick": tick,
        "agent_id": agent.id,
        "action": out.action,
        "speech": out.speech,
        "location": out.location,
        "thoughts": out.thoughts,
        "state": out.state,
        "memory": out.memory,
    })
    return out


async def run_tick_with_interactions(
    agents: List[AgentPersona],
    env: EnvSpec,
    config: SimulationConfig,
    tick: int,
    history: Dict[str, List[AgentTickOutput]],
) -> List[AgentTickOutput]:
    G = build_relation_graph(agents)

    intents = await asyncio.gather(*[
        simulate_step_for_agent(a, env, config, tick, history) for a in agents
    ])

    temp_history = {aid: list(items) for aid, items in history.items()}
    for out in intents:
        temp_history[out.agent_id].append(out)

    groups = group_by_location(temp_history)
    group_results: Dict[str, Dict[str, Any]] = {}

    for location, participants in groups.items():
        ids_here = [p.agent_id for p in participants]
        rel_summary = local_relation_summary(G, ids_here)
        allowed_speakers = pick_speakers_hard(G, ids_here, alpha=config.relation_influence, base_k=min(3, len(ids_here)))
        pairs: List[List[str]] = []
        for i, u in enumerate(ids_here):
            for v in ids_here[i+1:]:
                rec = G.get(u, {}).get(v)
                if rec and pair_trust_weight(rec) >= 0.55 * config.relation_influence:
                    pairs.append([u, v])
        local_visible = make_local_context(tick, history, focus_agent_id="", focus_location=location)

        data = await simulate_group_interaction(
            env=env,
            location=location,
            tick=tick,
            local_visible=local_visible,
            participants=participants,
            relations_summary=rel_summary,
            allowed_speakers=allowed_speakers,
            allowed_pairs=pairs,
            temperature=config.temperature,
            max_tokens=max(config.max_tokens, 900),
        )
        group_results[location] = data

        note = data.get("notes")
        if note:
            append_event_log({
                "type": "encounter",
                "tick": tick,
                "location": location,
                "notes": note,
                "participants": ids_here,
            })

    final_outputs: Dict[str, AgentTickOutput] = {o.agent_id: o for o in intents}
    for location, data in group_results.items():
        for item in data.get("agents", []):
            aid = str(item.get("agent_id", ""))
            if not aid or aid not in final_outputs:
                continue
            base = final_outputs[aid]
            base.action = str(item.get("action", base.action) or base.action)
            base.speech = str(item.get("speech", base.speech) or base.speech)
            base.thoughts = str(item.get("thoughts", base.thoughts) or base.thoughts)
            base.location = str(item.get("location", base.location) or base.location)
            base.state.update(item.get("state") or {})
            new_mem = item.get("memory") or []
            if new_mem:
                base.memory.extend(list(new_mem))

            append_agent_log(aid, {
                "type": "tick.final",
                "tick": tick,
                "location": base.location,
                "action": base.action,
                "speech": base.speech,
                "state": base.state,
                "thoughts": base.thoughts,
                "memory": base.memory,
            })

    return list(final_outputs.values())
