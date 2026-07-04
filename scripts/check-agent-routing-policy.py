#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "policy" / "agent-routing.json"
EXPECTED_SCHEMA = "cabinet.agent-routing-policy.v1"
REQUIRED_ROUTE_KEYS = {
    "id",
    "task_class",
    "data_class",
    "default_agents",
    "second_review",
    "evidence",
    "stop",
}


def fail(message: str) -> None:
    print(f"agent-routing-policy: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{label} must be a non-empty string")
    return value


def require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        fail(f"{label} must be a non-empty list")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(require_string(item, f"{label}[{index}]"))
    if len(set(result)) != len(result):
        fail(f"{label} must not contain duplicates")
    return result


def main() -> int:
    try:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing policy file: {POLICY}")
    except json.JSONDecodeError as exc:
        fail(f"invalid json: {exc}")

    policy = require_object(policy, "policy")
    if policy.get("schema") != EXPECTED_SCHEMA:
        fail("unexpected schema")
    require_string(policy.get("default_posture"), "default_posture")

    data_classes = require_object(policy.get("data_classes"), "data_classes")
    agents = require_object(policy.get("agents"), "agents")
    routes = policy.get("routes")
    if not isinstance(routes, list) or not routes:
        fail("routes must be a non-empty list")
    global_rules = require_string_list(policy.get("global_rules"), "global_rules")
    if len(global_rules) < 2:
        fail("global_rules must contain at least two entries")

    for name, data_class in data_classes.items():
        require_string(name, "data class id")
        data_class = require_object(data_class, f"data_classes.{name}")
        require_string(data_class.get("description"), f"data_classes.{name}.description")
        if not isinstance(data_class.get("external_allowed"), bool):
            fail(f"data_classes.{name}.external_allowed must be boolean")

    for name, agent in agents.items():
        require_string(name, "agent id")
        agent = require_object(agent, f"agents.{name}")
        require_string(agent.get("role"), f"agents.{name}.role")
        if not isinstance(agent.get("may_mutate"), bool):
            fail(f"agents.{name}.may_mutate must be boolean")
        if not isinstance(agent.get("requires_local_evidence"), bool):
            fail(f"agents.{name}.requires_local_evidence must be boolean")

    seen_route_ids: set[str] = set()
    for index, route in enumerate(routes):
        route = require_object(route, f"routes[{index}]")
        missing = REQUIRED_ROUTE_KEYS - set(route)
        if missing:
            fail(f"routes[{index}] missing keys: {sorted(missing)}")
        route_id = require_string(route["id"], f"routes[{index}].id")
        if route_id in seen_route_ids:
            fail(f"duplicate route id: {route_id}")
        seen_route_ids.add(route_id)
        data_class = require_string(route["data_class"], f"routes[{index}].data_class")
        if data_class not in data_classes:
            fail(f"route {route_id} references unknown data_class {data_class!r}")
        for agent in require_string_list(route["default_agents"], f"routes[{index}].default_agents"):
            if agent not in agents:
                fail(f"route {route_id} references unknown agent {agent!r}")
        require_string(route["task_class"], f"routes[{index}].task_class")
        require_string(route["second_review"], f"routes[{index}].second_review")
        require_string_list(route["evidence"], f"routes[{index}].evidence")
        require_string(route["stop"], f"routes[{index}].stop")
        if data_classes[data_class]["external_allowed"] is False:
            for agent in route["default_agents"]:
                if agent not in {"grabowski", "cabinet", "bureau"}:
                    fail(f"route {route_id} exposes local-only data to external agent {agent!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
