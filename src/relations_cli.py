import argparse
import json
import os
import random
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

def _load_json(path_or_json: str):
    if os.path.exists(path_or_json):
        with open(path_or_json, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(path_or_json)

def _save_json(path: str, data: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def sim_relation_type(u: Dict[str, Any], v: Dict[str, Any]) -> str:
    # 简单启发式：同职业→coworker；年龄差小/描述相似→friend；默认 stranger
    if u.get("occupation") and u.get("occupation") == v.get("occupation"):
        return "coworker"
    if abs(int(u.get("age", 30)) - int(v.get("age", 30))) <= 2:
        return "friend"
    return "stranger"

def main():
    p = argparse.ArgumentParser(description="Generate social relation graph and write into agents.json")
    p.add_argument("--agents-json", required=True, help="路径或JSON字符串")
    p.add_argument("--out", default=None, help="输出路径（默认覆盖 agents-json 文件）")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--density", type=float, default=0.08, help="连边概率（0~1）")
    p.add_argument("--boost-same-occupation", type=float, default=0.15, help="同职业加成")
    args = p.parse_args()

    random.seed(args.seed)
    data = _load_json(args.agents_json)
    if not isinstance(data, list):
        raise SystemExit("agents-json 应该是数组")

    # 初始化 relations
    for it in data:
        it.setdefault("relations", {})

    ids = [it["id"] for it in data]
    by_id = {it["id"]: it for it in data}

    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            u, v = by_id[ids[i]], by_id[ids[j]]
            # 基础概率
            p_edge = args.density
            if u.get("occupation") == v.get("occupation"):
                p_edge += args.boost_same_occupation
            if random.random() < p_edge:
                t = sim_relation_type(u, v)
                s = round(random.uniform(0.4, 0.9), 2) if t != "stranger" else round(random.uniform(0.2, 0.5), 2)
                u["relations"][v["id"]] = {"type": t, "strength": s}
                v["relations"][u["id"]] = {"type": t, "strength": s}

    out_path = args.out or (args.agents_json if os.path.exists(args.agents_json) else "prompt/agents.json")
    _save_json(out_path, data)
    print(f"关系图已写入：{out_path}. 节点={len(ids)}")

if __name__ == "__main__":
    main()
