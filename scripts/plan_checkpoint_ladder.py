#!/usr/bin/env python3
"""Freeze a checkpoint ladder that leaves time to finish and submit evidence."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

SCHEDULE_POLICY = "smoke_then_largest_feasible_v1"


def parse_utc(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"expected an explicit UTC timestamp, got {value!r}")
    return parsed.astimezone(UTC)


def parse_ladder(value: str) -> tuple[int, ...]:
    try:
        ladder = tuple(int(item) for item in value.split(","))
    except ValueError as exc:
        raise ValueError("ladder must be a comma-separated list of positive integers") from exc
    if not ladder or any(item <= 0 for item in ladder) or len(set(ladder)) != len(ladder):
        raise ValueError("ladder must contain unique positive integers")
    if tuple(sorted(ladder)) != ladder:
        raise ValueError("ladder iterations must be strictly increasing")
    return ladder


def parse_budgets(value: str, ladder: tuple[int, ...]) -> dict[int, int]:
    budgets: dict[int, int] = {}
    for entry in value.split(","):
        try:
            iteration_text, seconds_text = entry.split(":", maxsplit=1)
            iteration = int(iteration_text)
            seconds = int(seconds_text)
        except ValueError as exc:
            raise ValueError("stage budgets must use ITERATIONS:SECONDS entries") from exc
        if iteration in budgets or seconds <= 0:
            raise ValueError("stage budgets must be unique and positive")
        budgets[iteration] = seconds
    if set(budgets) != set(ladder):
        raise ValueError("stage-budget iterations must exactly match the ladder")
    return budgets


def choose_schedule(
    ladder: tuple[int, ...], budgets: dict[int, int], available_seconds: int
) -> list[int]:
    """Keep the smoke stage, then spend the remaining budget on strongest candidates."""
    smoke_iteration = ladder[0]
    if budgets[smoke_iteration] > available_seconds:
        return []

    selected = {smoke_iteration}
    remaining = available_seconds - budgets[smoke_iteration]
    for iteration in reversed(ladder[1:]):
        if budgets[iteration] <= remaining:
            selected.add(iteration)
            remaining -= budgets[iteration]
    return [iteration for iteration in ladder if iteration in selected]


def build_plan(
    *,
    ladder: tuple[int, ...],
    budgets: dict[int, int],
    training_timeouts: dict[int, int],
    now: datetime,
    run_started: datetime,
    max_walltime_seconds: int,
    deadline: datetime,
    finalization_reserve_seconds: int,
    portal_reserve_seconds: int,
) -> dict[str, object]:
    if finalization_reserve_seconds < 0 or portal_reserve_seconds < 0:
        raise ValueError("reserve values cannot be negative")
    if max_walltime_seconds <= 0:
        raise ValueError("max walltime must be positive")
    if now < run_started:
        raise ValueError("ladder computation cannot precede the run start")
    if set(training_timeouts) != set(ladder):
        raise ValueError("training-timeout iterations must exactly match the ladder")
    for iteration in ladder:
        if training_timeouts[iteration] > budgets[iteration]:
            raise ValueError("training timeout cannot exceed its stage walltime budget")
    seconds_until_deadline = max(0, int((deadline - now).total_seconds()))
    submission_candidate_budget_available = max(
        0,
        seconds_until_deadline - finalization_reserve_seconds - portal_reserve_seconds,
    )
    runtime_deadline = run_started + timedelta(seconds=max_walltime_seconds)
    runtime_seconds_remaining = max(0, int((runtime_deadline - now).total_seconds()))
    runtime_candidate_budget_available = max(
        0, runtime_seconds_remaining - finalization_reserve_seconds
    )
    candidate_budget_available = min(
        submission_candidate_budget_available, runtime_candidate_budget_available
    )
    scheduled = choose_schedule(ladder, budgets, candidate_budget_available)
    scheduled_budget = sum(budgets[iteration] for iteration in scheduled)
    omitted = [iteration for iteration in ladder if iteration not in scheduled]
    return {
        "format": "shadow_dance_ladder_plan_v2",
        "schedule_policy": SCHEDULE_POLICY,
        "planned_candidate_iterations": list(ladder),
        "scheduled_candidate_iterations": scheduled,
        "omitted_candidate_iterations": omitted,
        "stage_walltime_budget_seconds": {
            str(iteration): budgets[iteration] for iteration in ladder
        },
        "training_timeout_seconds": {
            str(iteration): training_timeouts[iteration] for iteration in ladder
        },
        "computed_utc": now.isoformat().replace("+00:00", "Z"),
        "run_started_utc": run_started.isoformat().replace("+00:00", "Z"),
        "max_walltime_seconds": max_walltime_seconds,
        "runtime_deadline_utc": runtime_deadline.isoformat().replace("+00:00", "Z"),
        "submission_deadline_utc": deadline.isoformat().replace("+00:00", "Z"),
        "seconds_until_deadline": seconds_until_deadline,
        "runtime_seconds_remaining": runtime_seconds_remaining,
        "finalization_reserve_seconds": finalization_reserve_seconds,
        "portal_reserve_seconds": portal_reserve_seconds,
        "submission_candidate_budget_available_seconds": (
            submission_candidate_budget_available
        ),
        "runtime_candidate_budget_available_seconds": runtime_candidate_budget_available,
        "candidate_budget_available_seconds": candidate_budget_available,
        "scheduled_candidate_budget_seconds": scheduled_budget,
        "deadline_truncated": bool(omitted),
        "launchable": bool(scheduled),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ladder", default="5,250,500,2000,4000")
    parser.add_argument(
        "--stage-budgets", default="5:900,250:1800,500:3600,2000:12600,4000:21600"
    )
    parser.add_argument(
        "--training-timeouts", default="5:600,250:1500,500:3000,2000:10800,4000:19800"
    )
    parser.add_argument("--run-started-utc", required=True)
    parser.add_argument("--max-walltime-seconds", type=int, default=36000)
    parser.add_argument("--deadline-utc", required=True)
    parser.add_argument("--now-utc")
    parser.add_argument("--finalization-reserve-seconds", type=int, default=7200)
    parser.add_argument("--portal-reserve-seconds", type=int, default=2700)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--print-scheduled-csv", action="store_true")
    args = parser.parse_args()

    ladder = parse_ladder(args.ladder)
    budgets = parse_budgets(args.stage_budgets, ladder)
    training_timeouts = parse_budgets(args.training_timeouts, ladder)
    now = parse_utc(args.now_utc) if args.now_utc else datetime.now(UTC)
    plan = build_plan(
        ladder=ladder,
        budgets=budgets,
        training_timeouts=training_timeouts,
        now=now,
        run_started=parse_utc(args.run_started_utc),
        max_walltime_seconds=args.max_walltime_seconds,
        deadline=parse_utc(args.deadline_utc),
        finalization_reserve_seconds=args.finalization_reserve_seconds,
        portal_reserve_seconds=args.portal_reserve_seconds,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    if args.print_scheduled_csv:
        print(",".join(str(value) for value in plan["scheduled_candidate_iterations"]))
    else:
        print(json.dumps(plan, indent=2))
    return 0 if plan["launchable"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
