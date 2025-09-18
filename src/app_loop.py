import argparse, asyncio, json, os
from typing import Any, Dict, List
from dotenv import load_dotenv

from src.agentsim.models import AgentPersona, EnvSpec, SimulationConfig, AgentTickOutput
from src.agentsim.environment import generate_env_from_hint, merge_env
from src.agentsim.simulator import run_tick_with_interactions
from src.agentsim.logger import append_agent_log, set_exp_log_roots
from src.agentsim.registry import set_agents_path

load_dotenv()

def parse_args():
    p = argparse.ArgumentParser(description="Multi-Agent Simulator (Experiment-aware)")
    p.add_argument("--experiment", type=str, default=None, help="实验目录")
    p.add_argument("--agents-json", type=str, default=None)
    p.add_argument("--env-hint", type=str, default=None)
    p.add_argument("--env-spec-json", type=str, default=None)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--max-tokens", type=int, default=700)
    p.add_argument("--visibility", type=str, default="local", choices=["global","local"])
    p.add_argument("--relation-influence", type=float, default=None)
    p.add_argument("--extra-env", type=str, default=None)
    p.add_argument("--interval", type=float, default=60.0)
    p.add_argument("--print-thoughts", action="store_true")
    return p.parse_args()

def _load_json(path_or_json: str) -> Any:
    if os.path.exists(path_or_json):
        with open(path_or_json,"r",encoding="utf-8") as f: return json.load(f)
    return json.loads(path_or_json)

async def main_async():
    args = parse_args()

    if args.experiment:
        exp_dir = args.experiment
        env_obj = _load_json(os.path.join(exp_dir,"env.json"))
        agents_raw = _load_json(os.path.join(exp_dir,"agents.json"))
        meta = _load_json(os.path.join(exp_dir,"meta.json"))
        # 绑定本实验的 agents 与日志根目录（含 events）
        set_agents_path(os.path.join(exp_dir,"agents.json"))
        set_exp_log_roots(os.path.join(exp_dir,"logs"))
        relation_influence = args.relation_influence if args.relation_influence is not None else meta.get("relation_influence",0.8)
    else:
        if not (args.agents_json and (args.env_spec_json or args.env_hint)):
            raise SystemExit("需提供 --experiment 或 (--agents-json 且 env)")
        agents_raw = _load_json(args.agents_json)
        if args.env_spec_json:
            env_obj = _load_json(args.env_spec_json)
        else:
            env = await generate_env_from_hint(args.env_hint or "")
            env_obj = {"title":env.title,"prompt":env.prompt,"rules":env.rules}
        relation_influence = args.relation_influence if args.relation_influence is not None else 0.8

    agents = [AgentPersona(**a) for a in agents_raw]
    env_spec = EnvSpec(**env_obj)
    if args.extra_env: env_spec = merge_env(env_spec, args.extra_env)

    config = SimulationConfig(
        steps=1, temperature=args.temperature, max_tokens=args.max_tokens,
        visibility=args.visibility, relation_influence=relation_influence
    )

    id2name = {a.id: a.name for a in agents}
    for a in agents:
        append_agent_log(a.name, {
            "type":"sim_meta","title":env_spec.title,"with_interactions":True,
            "interval_sec":args.interval,"temperature":args.temperature,
            "max_tokens":args.max_tokens,"visibility":args.visibility,
            "relation_influence":relation_influence,
        })

    history: Dict[str, List[AgentTickOutput]] = {a.id: [] for a in agents}

    tick = 0
    print(f"Loop（实验隔离，α={relation_influence}）启动：每 {args.interval}s 一个 tick（Ctrl+C 结束）")
    try:
        while True:
            results = await run_tick_with_interactions(agents, env_spec, config, tick, history)
            for out in results:
                history[out.agent_id].append(out)
            print(f"\n===== TICK {tick} =====")
            for it in results:
                print(f"- [{it.agent_id} | {id2name.get(it.agent_id,'?')}] @{it.location!r} act={it.action!r} speech={it.speech!r}")
                if args.print_thoughts: print(f"  thoughts={it.thoughts}")
            tick += 1
            await asyncio.sleep(max(0.0, args.interval))
    except KeyboardInterrupt:
        print("\n收到 Ctrl+C，结束仿真。")
    except Exception as e:
        print(f"\n仿真异常终止：{e}")

if __name__ == "__main__":
    asyncio.run(main_async())
