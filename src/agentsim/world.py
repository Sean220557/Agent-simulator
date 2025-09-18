from typing import Dict, List, Tuple
from .models import AgentTickOutput

def group_by_location(latest: Dict[str, List[AgentTickOutput]]) -> Dict[str, List[AgentTickOutput]]:
    """按位置把当前可见的最后一条输出分组。"""
    groups: Dict[str, List[AgentTickOutput]] = {}
    for aid, items in latest.items():
        if not items:
            continue
        last = items[-1]
        loc = last.location or "未知地点"
        groups.setdefault(loc, []).append(last)
    return groups

def make_local_context(
    tick: int,
    history: Dict[str, List[AgentTickOutput]],
    focus_agent_id: str,
    focus_location: str,
) -> str:
    """
    生成“本地可见”上下文：仅同地点（上一个tick）的公开信息。
    """
    if tick == 0 or not history:
        return "（暂无历史信息）"
    lines: List[str] = []
    for aid, items in history.items():
        if not items: continue
        last = items[-1]
        if last.location != focus_location:
            continue
        # 只给公开信息（不含 thoughts/memory）
        lines.append(
            f"[tick {last.tick}] {aid}: action={last.action!r}, speech={last.speech!r}, location={last.location!r}"
        )
    if not lines:
        return "（同地点无人公开信息）"
    return "\n".join(lines)
