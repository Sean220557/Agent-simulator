import os
import json
import uuid
import random
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from src.agentsim.environment import generate_env_from_hint
from src.agentsim.persona_gen import generate_personas_for_environment
from src.agentsim.logger import set_exp_log_roots, init_agent_log

load_dotenv()

SCHEMA_HINT = """你是社会学实验的设计助手。基于环境背景，给出一份“群体构建约束”JSON...
（内容与之前一致，略）"""

def _mkdir(p: str):
    os.makedirs(p, exist_ok=True)

def _write(path: str, obj: Any):
    _mkdir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

async def _generate_constraints_from_env(env: Dict[str, Any]) -> Dict[str, Any]:
    from src.agentsim.llm import chat_json
    title = env.get("title") or "环境"
    prompt = env.get("prompt") or ""
    rules = env.get("rules") or []
    data = await chat_json(
        system="You design realistic population constraints for simulations.",
        messages=[{
            "role": "user",
            "content": f"【环境标题】{title}\n【环境描述】{prompt}\n【环境规则】" + "\n".join(f"- {r}" for r in rules) + "\n\n" + SCHEMA_HINT
        }],
        temperature=0.3,
        max_tokens=800,
    )
    data.setdefault("locations", [])
    data.setdefault("relation_density", 0.08)
    return data

def _slugify(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in ("_","-"))
    return safe or f"exp_{uuid.uuid4().hex[:8]}"

def _build_relations(personas: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """基于约束的简单关系生成器：同职业/家庭/同地点 加权，其他随机补足到密度"""
    density = float(constraints.get("relation_density", 0.08))
    ids = [p["id"] for p in personas]
    by_id = {p["id"]: p for p in personas}
    G: Dict[str, Dict[str, Dict[str, Any]]] = {i:{} for i in ids}

    # 简单规则：同职业→coworker；同地点→neighbor；患者-家属→family（若能从描述/occupation中判断）；其余 acquaintance/stranger
    def relation_type(u: Dict[str,Any], v: Dict[str,Any]) -> str:
        ou, ov = u.get("occupation",""), v.get("occupation","")
        if any(k in ou for k in ["病人","患者"]) and any(k in ov for k in ["家属","陪护"]):
            return "family"
        if ou == ov and ou:
            return "coworker"
        lu, lv = u.get("initial_state",{}).get("location"), v.get("initial_state",{}).get("location")
        if lu and lv and lu == lv:
            return "neighbor"
        return "acquaintance"

    def strength_for(t: str) -> float:
        if t=="family": return round(random.uniform(0.75, 0.95), 2)
        if t=="friend": return round(random.uniform(0.6, 0.85), 2)
        if t=="coworker": return round(random.uniform(0.55, 0.8), 2)
        if t=="neighbor": return round(random.uniform(0.45, 0.7), 2)
        if t=="acquaintance": return round(random.uniform(0.35, 0.6), 2)
        return round(random.uniform(0.2, 0.5), 2)

    n = len(ids)
    # 先按规则连边
    for i in range(n):
        for j in range(i+1, n):
            u, v = by_id[ids[i]], by_id[ids[j]]
            p_edge = density
            if u.get("occupation") == v.get("occupation"): p_edge += 0.15
            if u.get("initial_state",{}).get("location")==v.get("initial_state",{}).get("location"): p_edge += 0.1
            # 轻微的年龄相近加成
            if abs(int(u.get("age",30))-int(v.get("age",30)))<=2: p_edge += 0.05
            if random.random() < p_edge:
                t = relation_type(u,v)
                s = strength_for(t)
                G[u["id"]][v["id"]] = {"type": t, "strength": s}
                G[v["id"]][u["id"]] = {"type": t, "strength": s}
    return G

async def create_experiment(
    root_dir: str,
    name: str,
    env_hint: str,
    count: int,
    relation_influence: float = 0.8,
    constraints: Optional[Dict[str, Any]] = None,
) -> str:
    slug = _slugify(name)
    exp_dir = os.path.join(root_dir, slug)
    _mkdir(exp_dir)

    # 1) 环境
    env_obj = await generate_env_from_hint(env_hint)
    env = {"title": env_obj.title, "prompt": env_obj.prompt, "rules": env_obj.rules}
    _write(os.path.join(exp_dir, "env.json"), env)

    # 2) 约束
    if constraints is None:
        constraints = await _generate_constraints_from_env(env)
    _write(os.path.join(exp_dir, "constraints.json"), constraints)

    # 3) 生成 personas（修复多样性），并把 relations 注入
    hint = f"请按以下约束构建群体：{json.dumps(constraints, ensure_ascii=False)}"
    personas = await generate_personas_for_environment(count, env, diversity_hint=hint, constraints=constraints)

    # 3.1 生成关系图并注入到 persona.relations
    relations = _build_relations(personas, constraints)
    by_id = {p["id"]: p for p in personas}
    for u, neigh in relations.items():
        by_id[u]["relations"] = neigh

    agents_path = os.path.join(exp_dir, "agents.json")
    _write(agents_path, personas)
    _write(os.path.join(exp_dir, "relations.json"), relations)

    # 4) 元信息
    meta = {
        "name": name,
        "slug": slug,
        "relation_influence": relation_influence,
        "count": count,
        "paths": {
            "agents": agents_path,
            "env": os.path.join(exp_dir, "env.json"),
            "relations": os.path.join(exp_dir, "relations.json"),
            "logs_base": os.path.join(exp_dir, "logs")
        }
    }
    _write(os.path.join(exp_dir, "meta.json"), meta)

    # 5) 初始化“按实验”的日志根目录，并为每名 agent 写 init 记录
    set_exp_log_roots(os.path.join(exp_dir, "logs"))
    for p in personas:
        init_agent_log(p["name"], {"type": "init", "agent": p})

    return exp_dir
