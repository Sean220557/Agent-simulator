import argparse
import asyncio
import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

from src.agentsim.models import AgentPersona, EnvSpec, SimulationConfig, SimulationInput
from src.agentsim.environment import generate_env_from_hint, merge_env
from src.agentsim.simulator import run_simulation

load_dotenv()

DEFAULT_SYSTEM = os.getenv("SYSTEM_PROMPT", "You are a helpful multi-agent environment simulator.")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="DeepSeek Multi-Agent Simulator")
    p.add_argument("--agents-json", type=str, required=True,
                   help="Agents 配置的 JSON 字符串或文件路径（自动识别）；见 README 示例")
    p.add_argument("--env-hint", type=str, default=None,
                   help="给 LLM 的环境简述（将自动生成完整环境）")
    p.add_argument("--env-spec-json", type=str, default=None,
                   help="直接提供完整环境 JSON（与 --env-hint 二选一）")
    p.add_argument("--steps", type=int, default=5, help="仿真步数")
    p.add_argument("--temperature", type=float, default=0.7, help="采样温度")
    p.add_argument("--max-tokens", type=int, default=512, help="单次生成最大 tokens")
    p.add_argument("--visibility", type=str, default="global", choices=["global", "local"],
                   help="可见性（示例中 local 仍以全局实现，规则可引导约束）")
    p.add_argument("--extra-env", type=str, default=None,
                   help="追加到环境描述的补充文本")
    p.add_argument("--out", type=str, default=None,
                   help="将完整结果保存为 JSON 文件路径")
    return p.parse_args()


def _load_json_maybe_file(s: str) -> Any:
    if os.path.exists(s):
        with open(s, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(s)


def _pretty_print(history: Dict[str, List[Dict[str, Any]]]) -> None:
    for aid, items in history.items():
        print(f"\n=== Agent {aid} ===")
        for it in items:
            print(
                f"[tick {it['tick']}]"
                f"\n- action : {it['action']}"
                f"\n- speech : {it['speech']}"
                f"\n- location : {it['location']}"
                f"\n- thoughts : {it['thoughts']}"
                f"\n- state : {json.dumps(it['state'], ensure_ascii=False)}"
                "\n"
            )


async def main_async():
    args = parse_args()

    agents_raw = _load_json_maybe_file(args.agents_json)
    agents = [AgentPersona(**a) for a in agents_raw]

    env_spec = None
    if args.env_spec_json:
        env_obj = _load_json_maybe_file(args.env_spec_json)
        env_spec = EnvSpec(**env_obj)

    if not env_spec and not args.env_hint:
        raise SystemExit("必须提供 --env-spec-json 或 --env-hint 之一")

    if not env_spec:
        env_spec = await generate_env_from_hint(args.env_hint or "")

    if args.extra_env:
        env_spec = merge_env(env_spec, args.extra_env)

    config = SimulationConfig(
        steps=args.steps,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        visibility=args.visibility,
    )

    history_objs = await run_simulation(agents, env_spec, config)

    # 序列化为纯 dict 便于保存/打印
    history_dict: Dict[str, List[Dict[str, Any]]] = {
        aid: [it.model_dump() for it in items] for aid, items in history_objs.items()
    }

    _pretty_print(history_dict)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(history_dict, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存：{args.out}")


if __name__ == "__main__":
    asyncio.run(main_async())
