import os
import json
from typing import Any, Dict

# ---- Agents 日志根目录（每个实验会覆盖） ----
_AGENT_LOG_ROOT: str = os.getenv("AGENT_LOG_DIR", "logs/agents")
# ---- Events 日志根目录（每个实验会覆盖） ----
_EVENT_LOG_ROOT: str = os.getenv("EVENT_LOG_DIR", "logs/events")

def set_log_root(root: str) -> None:
    """兼容旧接口：只设置 agent 日志根目录"""
    global _AGENT_LOG_ROOT
    _AGENT_LOG_ROOT = root

def set_event_log_root(root: str) -> None:
    """设置事件日志根目录（实验粒度）"""
    global _EVENT_LOG_ROOT
    _EVENT_LOG_ROOT = root

def set_exp_log_roots(base: str) -> None:
    """一次性把 agent/event 日志根目录都切到实验目录下"""
    set_log_root(os.path.join(base, "agents"))
    set_event_log_root(os.path.join(base, "events"))

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def _safe_name(name: str) -> str:
    return "".join(c for c in str(name) if c.isalnum() or c in ("_", "-", "."))

# ------------ Agent 日志 ------------
def _agent_log_path(name: str) -> str:
    _ensure_dir(_AGENT_LOG_ROOT)
    return os.path.join(_AGENT_LOG_ROOT, f"{_safe_name(name)}.jsonl")

def init_agent_log(name: str, initial_record: Dict[str, Any]) -> None:
    path = _agent_log_path(name)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(initial_record, ensure_ascii=False) + "\n")

def append_agent_log(name_or_id: str, record: Dict[str, Any]) -> None:
    path = _agent_log_path(name_or_id)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# ------------ 事件日志（集中存放） ------------
def _event_log_path() -> str:
    path = os.path.join(_EVENT_LOG_ROOT, "encounters.jsonl")
    _ensure_dir(os.path.dirname(path))
    return path

def append_event_log(record: Dict[str, Any]) -> None:
    """记录地点级相遇/冲突/协作等事件"""
    path = _event_log_path()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
