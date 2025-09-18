import argparse
import asyncio
import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from src.experiments.manager import create_experiment

load_dotenv()

def _json_or_file(val: Optional[str]) -> Optional[Dict[str, Any]]:
    if not val:
        return None
    if os.path.exists(val):
        with open(val, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(val)

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Experiment Manager CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("create", help="创建实验（环境必填、人数必填、约束可选）")
    s.add_argument("--name", required=True)
    s.add_argument("--env-hint", required=True)
    s.add_argument("--count", type=int, required=True)
    s.add_argument("--constraints-json", type=str, default=None)
    s.add_argument("--relation-influence", type=float, default=0.8)
    s.add_argument("--root", type=str, default="experiments")
    s.set_defaults(func="create")
    return p

async def main_async():
    parser = build_parser()
    args = parser.parse_args()
    if args.cmd == "create":
        constraints = _json_or_file(args.constraints_json)
        exp_dir = await create_experiment(
            root_dir=args.root,
            name=args.name,
            env_hint=args.env_hint,
            count=args.count,
            relation_influence=args.relation_influence,
            constraints=constraints,
        )
        print(f"实验已创建：{exp_dir}")
        print("包含：env.json, constraints.json, agents.json（总名单）, meta.json, logs/agents/（按人日志）")

if __name__ == "__main__":
    asyncio.run(main_async())
