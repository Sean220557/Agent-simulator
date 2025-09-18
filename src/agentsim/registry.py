import os
import json
from typing import Any, Dict, List, Optional, Callable

# 模块级可变 agents.json 路径（默认全局）
_AGENTS_PATH: str = os.getenv("AGENTS_JSON_PATH", "prompt/agents.json")

def set_agents_path(path: str) -> None:
    """设置当前进程使用的 agents.json 路径（用于按实验隔离）。"""
    global _AGENTS_PATH
    _AGENTS_PATH = path

def _ensure_dir_for(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def load_agents() -> List[Dict[str, Any]]:
    if not os.path.exists(_AGENTS_PATH):
        return []
    with open(_AGENTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{_AGENTS_PATH} 内容应为数组")
    return data

def save_agents(items: List[Dict[str, Any]]) -> None:
    _ensure_dir_for(_AGENTS_PATH)
    with open(_AGENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def find_by_name(items: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    for it in items:
        if it.get("name") == name:
            return it
    return None

def add_agent(persona: Dict[str, Any]) -> None:
    items = load_agents()
    items.append(persona)
    save_agents(items)

def upsert_agent(persona: Dict[str, Any]) -> None:
    items = load_agents()
    name = persona.get("name")
    found = False
    for i, it in enumerate(items):
        if it.get("name") == name:
            items[i] = persona
            found = True
            break
    if not found:
        items.append(persona)
    save_agents(items)

def remove_agent(name: str) -> bool:
    items = load_agents()
    n0 = len(items)
    items = [it for it in items if it.get("name") != name]
    if len(items) != n0:
        save_agents(items)
        return True
    return False
