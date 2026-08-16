#!/usr/bin/env python3
"""Bind completed checkpoint candidates to a frozen deadline ladder plan."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_iterations(value: str) -> list[int]:
    if not value:
        return []
    try:
        result = [int(item) for item in value.split(",")]
    except ValueError as exc:
        raise ValueError("completed iterations must be comma-separated integers") from exc
    if any(item <= 0 for item in result) or len(set(result)) != len(result):
        raise ValueError("completed iterations must be unique and positive")
    return result


def build_outcome(
    plan: dict[str, Any],
    *,
    plan_path: Path,
    completed: list[int],
    timed_out: int | None,
    completed_utc: datetime,
) -> dict[str, object]:
    if plan.get("format") != "shadow_dance_ladder_plan_v2":
        raise ValueError("unsupported ladder plan")
    scheduled = [int(value) for value in plan.get("scheduled_candidate_iterations", [])]
    if not scheduled:
        raise ValueError("ladder plan scheduled no candidates")
    if completed != scheduled[: len(completed)]:
        raise ValueError("completed candidates must be an ordered prefix of the schedule")
    if not completed:
        raise ValueError("at least one completed candidate is required")
    next_iteration = scheduled[len(completed)] if len(completed) < len(scheduled) else None
    if timed_out is not None and timed_out != next_iteration:
        raise ValueError("timed-out candidate must be the next scheduled iteration")
    if timed_out is None and len(completed) != len(scheduled):
        raise ValueError("an incomplete schedule must identify the timed-out candidate")
    runtime_omitted = scheduled[len(completed) :]
    return {
        "format": "shadow_dance_ladder_outcome_v2",
        "plan": {
            "path": plan_path.name,
            "sha256": sha256(plan_path),
        },
        "scheduled_candidate_iterations": scheduled,
        "completed_candidate_iterations": completed,
        "runtime_omitted_candidate_iterations": runtime_omitted,
        "timed_out_candidate_iteration": timed_out,
        "deadline_truncated_before_run": bool(plan.get("deadline_truncated")),
        "completed_utc": completed_utc.astimezone(UTC).isoformat().replace("+00:00", "Z"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--completed", required=True)
    parser.add_argument("--timed-out", type=int)
    parser.add_argument("--completed-utc")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    completed_utc = (
        datetime.fromisoformat(args.completed_utc.replace("Z", "+00:00"))
        if args.completed_utc
        else datetime.now(UTC)
    )
    if completed_utc.tzinfo is None or completed_utc.utcoffset() != UTC.utcoffset(completed_utc):
        raise ValueError("completed timestamp must be explicit UTC")
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    outcome = build_outcome(
        plan,
        plan_path=args.plan,
        completed=parse_iterations(args.completed),
        timed_out=args.timed_out,
        completed_utc=completed_utc,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
