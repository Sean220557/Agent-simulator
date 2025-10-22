import random
from typing import Dict, List, Tuple, Any
from .models import AgentPersona

RELATION_BASE_TRUST = {
    "family": 0.9,
    "friend": 0.75,
    "coworker": 0.6,
    "neighbor": 0.55,
    "acquaintance": 0.45,
    "stranger": 0.3,
}

def build_relation_graph(agents: List[AgentPersona]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    order = ["family","friend","coworker","neighbor","acquaintance","stranger"]
    rank = {t: i for i, t in enumerate(order)}
    g: Dict[str, Dict[str, Dict[str, Any]]] = {a.id: {} for a in agents}
    tmp = {a.id: a.relations or {} for a in agents}
    for i in tmp:
        for j, rec in tmp[i].items():
            t_i = str(rec.get("type", "stranger"))
            s_i = float(rec.get("strength", 0.0))
            rec2 = tmp.get(j, {}).get(i, {})
            t_j = str(rec2.get("type", t_i))
            s_j = float(rec2.get("strength", s_i))
            s = max(s_i, s_j)
            t = t_i if rank.get(t_i, 99) <= rank.get(t_j, 99) else t_j
            g[i][j] = {"type": t, "strength": max(0.0, min(1.0, s))}
            g.setdefault(j, {})[i] = {"type": t, "strength": max(0.0, min(1.0, s))}
    return g

def pair_trust_weight(rec: Dict[str, Any]) -> float:
    t = str(rec.get("type", "stranger"))
    s = float(rec.get("strength", 0.0))
    base = RELATION_BASE_TRUST.get(t, 0.35)
    return max(0.05, min(1.0, base * 0.6 + s * 0.4))

def local_relation_summary(
    graph: Dict[str, Dict[str, Dict[str, Any]]],
    participants_ids: List[str]
) -> List[str]:
    lines: List[str] = []
    n = len(participants_ids)
    for i in range(n):
        for j in range(i+1, n):
            u, v = participants_ids[i], participants_ids[j]
            rec = graph.get(u, {}).get(v)
            if not rec:
                continue
            trust = pair_trust_weight(rec)
            lines.append(f"{u}<->{v}: type={rec['type']} strength={rec['strength']:.2f} (trust≈{trust:.2f})")
    return lines

def pick_speakers_hard(
    graph: Dict[str, Dict[str, Dict[str, Any]]],
    participants_ids: List[str],
    alpha: float,
    base_k: int = 3
) -> List[str]:
    """
    硬约束许可发声名单（允许说话的人），alpha 控制关系影响强度：
    - 得分 = (1-alpha)*均匀 + alpha*关系均值
    - 取 top-k 作为“许可发声”
    """
    if not participants_ids:
        return []
    k = min(base_k, len(participants_ids))
    uniform = 1.0 / len(participants_ids)
    scores: Dict[str, float] = {}
    for u in participants_ids:
        neigh = graph.get(u, {})
        acc = 0.0
        cnt = 0
        for v in participants_ids:
            if v == u:
                continue
            rec = neigh.get(v)
            if rec:
                acc += pair_trust_weight(rec)
                cnt += 1
        rel = acc / cnt if cnt else 0.2
        scores[u] = (1 - alpha) * uniform + alpha * rel
    sorted_ids = sorted(participants_ids, key=lambda x: scores.get(x, 0.0), reverse=True)
    return sorted_ids[:k]
