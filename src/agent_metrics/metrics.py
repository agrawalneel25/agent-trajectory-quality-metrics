from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable
from urllib.request import urlopen


COUNTED_ROLES = ("system", "user", "assistant", "tool")


class TrajectoryError(ValueError):
    """Raised when a JSON file is not a supported trajectory shape."""


@dataclass(frozen=True)
class MessageMetrics:
    source: str
    total_messages: int
    system_messages: int
    user_messages: int
    assistant_messages: int
    tool_messages: int
    other_messages: int = 0
    other_roles: dict[str, int] = field(default_factory=dict)
    instance_id: str | None = None
    api_calls: int | None = None
    cost: float | None = None
    resolved: bool | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "instance_id": self.instance_id,
            "system_messages": self.system_messages,
            "user_messages": self.user_messages,
            "assistant_messages": self.assistant_messages,
            "tool_messages": self.tool_messages,
            "other_messages": self.other_messages,
            "other_roles": dict(self.other_roles),
            "total_messages": self.total_messages,
            "api_calls": self.api_calls,
            "cost": self.cost,
            "resolved": self.resolved,
        }


def load_json(location: str) -> Any:
    if location == "-":
        import sys

        return json.load(sys.stdin)
    if location.startswith(("http://", "https://")):
        with urlopen(location, timeout=60) as response:
            return json.load(response)
    with Path(location).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_input_files(inputs: Iterable[str]) -> list[str]:
    paths: list[str] = []
    for item in inputs:
        if item == "-" or item.startswith(("http://", "https://")):
            paths.append(item)
            continue
        path = Path(item)
        if path.is_dir():
            paths.extend(str(candidate) for candidate in sorted(path.rglob("*.json")))
        else:
            paths.append(str(path))
    return paths


def compute_metrics(document: Any, source: str = "<memory>") -> MessageMetrics:
    messages = _extract_messages(document)
    counts = {role: 0 for role in COUNTED_ROLES}
    other_roles: dict[str, int] = {}

    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise TrajectoryError(f"message at index {index} is not an object")
        normalized = _message_role(message, index)
        if normalized in counts:
            counts[normalized] += 1
        else:
            other_roles[normalized] = other_roles.get(normalized, 0) + 1

    info = document.get("info", {}) if isinstance(document, dict) else {}
    model_stats = info.get("model_stats", {}) if isinstance(info, dict) else {}

    return MessageMetrics(
        source=source,
        instance_id=_string_or_none(document.get("instance_id")) if isinstance(document, dict) else None,
        system_messages=counts["system"],
        user_messages=counts["user"],
        assistant_messages=counts["assistant"],
        tool_messages=counts["tool"],
        other_messages=sum(other_roles.values()),
        other_roles=dict(sorted(other_roles.items())),
        total_messages=len(messages),
        api_calls=_int_or_none(model_stats.get("api_calls")),
        cost=_float_or_none(model_stats.get("instance_cost")),
        resolved=_bool_or_none(document.get("resolved")) if isinstance(document, dict) else None,
    )


def format_metrics(metrics: MessageMetrics) -> str:
    lines = [
        f"System messages:    {metrics.system_messages:>4}",
        f"User messages:      {metrics.user_messages:>4}",
        f"Assistant messages: {metrics.assistant_messages:>4}",
        f"Tool messages:      {metrics.tool_messages:>4}",
    ]
    for role, count in metrics.other_roles.items():
        lines.append(f"{role.title()} messages:      {count:>4}")
    lines.extend(
        [
            "======================",
            f"Total messages:     {metrics.total_messages:>4}",
        ]
    )
    return "\n".join(lines)


def _extract_messages(document: Any) -> list[dict[str, Any]]:
    if isinstance(document, list):
        return document
    if not isinstance(document, dict):
        raise TrajectoryError("trajectory JSON must be an object or a list of messages")
    messages = document.get("messages")
    if isinstance(messages, list):
        return messages
    raise TrajectoryError("trajectory JSON must contain a messages array")


def _message_role(message: dict[str, Any], index: int) -> str:
    role = message.get("role")
    if isinstance(role, str):
        return role.lower()

    message_type = message.get("type")
    if message_type == "function_call_output":
        return "tool"

    if message.get("object") == "response" and isinstance(message.get("output"), list):
        return "assistant"

    if isinstance(message_type, str):
        return message_type.lower()

    raise TrajectoryError(f"message at index {index} has no recognizable role")


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (float, int)):
        return float(value)
    return None


def _bool_or_none(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None
