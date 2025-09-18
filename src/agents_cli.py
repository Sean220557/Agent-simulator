import argparse
import asyncio
import json
import os
import uuid
from typing import Any, Dict, List

from dotenv import load_dotenv
from src.agentsim.registry import (
    load_agents, save_agents, add_agent, remove_agent, upsert_agent, find_by_name,
    set_agents_path
)
from src.agentsim.persona_gen import (
    generate_persona_default, generate_personas_diverse, generate_personas_for_environment,
    GENDER_OPTIONS, EDU_OPTIONS, INCOME_OPTIONS, OCCUPATION_SAMPLES
)
from src.agentsim.logger import init_agent_log, set_log_root

load_dotenv()

def _print_table(items: List[Dict[str, Any]]):
    if not items:
        print("(空)")
        return
    cols = ["id","name","gender","age","occupation","income_level","education"]
    widths = {c: max(len(c), max(len(str(it.get(c, ""))) for it in items)) for c in cols}
    line = " | ".join(c.ljust(widths[c]) for c in cols)
    print(line)
    print("-" * len(line))
    for it in items:
        print(" | ".join(str(it.get(c, "")).ljust(widths[c]) for c in cols))

def _json_or_file(val: str) -> Any:
    if os.path.exists(val):
        with open(val, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(val)

def _maybe_bind_experiment(exp_dir: str):
    """如果指定了实验目录，则切换该实验的 agents.json 与日志根目录。"""
    set_agents_path(os.path.join(exp_dir, "agents.json"))
    set_log_root(os.path.join(exp_dir, "logs", "agents"))

def cmd_list(args):
    if args.experiment:
        _maybe_bind_experiment(args.experiment)
    items = load_agents()
    _print_table(items)

def cmd_show(args):
    if args.experiment:
        _maybe_bind_experiment(args.experiment)
    items = load_agents()
    it = find_by_name(items, args.name)
    if not it:
        print(f"未找到：{args.name}")
        return
    print(json.dumps(it, ensure_ascii=False, indent=2))

async def _create_or_update_persona(args, is_update: bool):
    if args.experiment:
        _maybe_bind_experiment(args.experiment)

    if args.auto or not any([args.gender, args.age, args.occupation, args.income, args.education, args.description]):
        persona = await generate_persona_default(
            name=args.name,
            gender=args.gender,
            age=args.age,
            occupation=args.occupation,
            income_level=args.income,
            education=args.education,
            description=args.description,
        )
    else:
        persona = {
            "id": f"agent_{uuid.uuid4().hex}",
            "name": args.name,
            "gender": args.gender or "男",
            "age": args.age or 28,
            "occupation": args.occupation or "软件工程师",
            "income_level": args.income or "10k-20k/月",
            "education": args.education or "本科",
            "description": args.description or "普通城市居民，性格温和，工作稳定。",
            "initial_memory": ["熟悉本地道路与公交线路","大学时期参与过社团组织","最近在学习时间管理方法"],
            "initial_state": {"location": "起点", "mood": "calm"},
            "relations": {},
        }

    if is_update:
        upsert_agent(persona)
        print(f"已更新/新增：{args.name}")
    else:
        add_agent(persona)
        print(f"已新增：{args.name}")

    init_agent_log(persona["name"], {"type": "init", "agent": persona})

async def cmd_add_batch(args):
    if args.experiment:
        _maybe_bind_experiment(args.experiment)

    # 环境优先
    if args.env_spec_json or args.env_hint:
        if args.env_spec_json:
            env = _json_or_file(args.env_spec_json)
            if not isinstance(env, dict) or "prompt" not in env:
                raise SystemExit("--env-spec-json 必须是包含 {title,prompt,rules} 的对象")
        else:
            env = {"title": "生成自提示的环境", "prompt": args.env_hint, "rules": []}
        personas = await generate_personas_for_environment(args.count, env, args.diversity_hint)
    else:
        personas = await generate_personas_diverse(args.count, args.diversity_hint)

    items = load_agents()
    existing_names = {it.get("name") for it in items}

    added = 0
    for p in personas:
        nm = p["name"]
        if nm in existing_names:
            suffix = 2
            new_nm = f"{nm}{suffix}"
            while new_nm in existing_names:
                suffix += 1
                new_nm = f"{nm}{suffix}"
            p["name"] = new_nm
            nm = new_nm

        p.setdefault("id", f"agent_{uuid.uuid4().hex}")
        p.setdefault("relations", {})

        items.append(p)
        existing_names.add(nm)
        added += 1
        init_agent_log(nm, {"type": "init", "agent": p})

    save_agents(items)
    print(f"批量新增完成：生成 {added} 个；当前总数 = {len(items)}")

def cmd_remove(args):
    if args.experiment:
        _maybe_bind_experiment(args.experiment)
    ok = remove_agent(args.name)
    print("已删除" if ok else "未找到该姓名")

def cmd_bulk_import(args):
    if args.experiment:
        _maybe_bind_experiment(args.experiment)
    data = _json_or_file(args.json)
    if not isinstance(data, list):
        raise SystemExit("导入数据需为数组（列表）")
    items = load_agents()
    existing_names = {it.get("name") for it in items}
    added = 0
    for it in data:
        nm = it.get("name")
        if not nm or nm in existing_names:
            continue
        it.setdefault("id", f"agent_{uuid.uuid4().hex}")
        it.setdefault("initial_state", {"location": "起点", "mood": "calm"})
        it.setdefault("initial_memory", ["对周边较熟悉", "注重安全", "愿意与人合作"])
        it.setdefault("relations", {})
        items.append(it)
        existing_names.add(nm)
        added += 1
        init_agent_log(nm, {"type": "init", "agent": it})
    save_agents(items)
    print(f"导入完成，新增 {added} 条；现有总数 {len(items)}")

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Agents Registry CLI（支持按实验隔离）")
    sub = p.add_subparsers(dest="cmd", required=True)

    # 全部命令新增 --experiment
    def add_exp_arg(sp):
        sp.add_argument("--experiment", type=str, default=None, help="对应实验目录（使用该实验的 agents.json 与 logs/agents）")

    s = sub.add_parser("list", help="列出所有 agent（表格）"); add_exp_arg(s); s.set_defaults(func=cmd_list)
    s = sub.add_parser("show", help="查看单个 agent 详情（JSON）"); add_exp_arg(s); s.add_argument("--name", required=True); s.set_defaults(func=cmd_show)

    s = sub.add_parser("add", help="新增单个 agent（可 LLM 自动生成）"); add_exp_arg(s)
    s.add_argument("--name", required=True)
    s.add_argument("--gender", choices=GENDER_OPTIONS); s.add_argument("--age", type=int)
    s.add_argument("--occupation"); s.add_argument("--income", choices=INCOME_OPTIONS)
    s.add_argument("--education", choices=EDU_OPTIONS); s.add_argument("--description")
    s.add_argument("--auto", action="store_true")
    s.set_defaults(async_func=lambda a: _create_or_update_persona(a, is_update=False))

    s = sub.add_parser("update", help="按姓名覆盖写入"); add_exp_arg(s)
    s.add_argument("--name", required=True)
    s.add_argument("--gender", choices=GENDER_OPTIONS); s.add_argument("--age", type=int)
    s.add_argument("--occupation"); s.add_argument("--income", choices=INCOME_OPTIONS)
    s.add_argument("--education", choices=EDU_OPTIONS); s.add_argument("--description")
    s.add_argument("--auto", action="store_true")
    s.set_defaults(async_func=lambda a: _create_or_update_persona(a, is_update=True))

    s = sub.add_parser("add-batch", help="批量新增（可指定环境/多样性）"); add_exp_arg(s)
    s.add_argument("--count", type=int, required=True)
    s.add_argument("--diversity-hint", type=str, default=None)
    s.add_argument("--env-hint", type=str, default=None)
    s.add_argument("--env-spec-json", type=str, default=None)
    s.set_defaults(async_func=cmd_add_batch)

    s = sub.add_parser("remove", help="按姓名删除"); add_exp_arg(s)
    s.add_argument("--name", required=True)
    s.set_defaults(func=cmd_remove)

    s = sub.add_parser("import", help="批量导入（JSON 文件或 JSON 字符串，数组）"); add_exp_arg(s)
    s.add_argument("--json", required=True)
    s.set_defaults(func=cmd_bulk_import)
    return p

def main():
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "async_func"):
        asyncio.run(args.async_func(args))
    else:
        args.func(args)

if __name__ == "__main__":
    main()
