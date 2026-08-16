from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from plan_checkpoint_ladder import build_plan, parse_budgets, parse_ladder
    from publish_model import validate_ladder_evidence
    from record_ladder_outcome import build_outcome
finally:
    sys.path.pop(0)


LADDER = (5, 250, 500, 4000)
BUDGETS = {5: 900, 250: 1800, 500: 3600, 4000: 21600}
TRAINING_TIMEOUTS = {5: 600, 250: 1500, 500: 3000, 4000: 19800}
DEADLINE = datetime(2026, 8, 17, 6, 59, tzinfo=UTC)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 8, 16, 20, 20, tzinfo=UTC), [5, 250, 500, 4000]),
        (datetime(2026, 8, 16, 20, 50, tzinfo=UTC), [5, 500, 4000]),
        (datetime(2026, 8, 16, 21, 0, tzinfo=UTC), [5, 250, 4000]),
        (datetime(2026, 8, 16, 21, 30, tzinfo=UTC), [5, 4000]),
        (datetime(2026, 8, 17, 2, 0, tzinfo=UTC), [5, 250, 500]),
        (datetime(2026, 8, 17, 3, 20, tzinfo=UTC), [5, 250]),
        (datetime(2026, 8, 17, 3, 50, tzinfo=UTC), [5]),
        (datetime(2026, 8, 17, 4, 5, tzinfo=UTC), []),
    ],
)
def test_ladder_plan_preserves_evidence_and_portal_reserves(
    now: datetime, expected: list[int]
) -> None:
    plan = build_plan(
        ladder=LADDER,
        budgets=BUDGETS,
        training_timeouts=TRAINING_TIMEOUTS,
        now=now,
        run_started=now,
        max_walltime_seconds=36000,
        deadline=DEADLINE,
        finalization_reserve_seconds=7200,
        portal_reserve_seconds=2700,
    )
    assert plan["scheduled_candidate_iterations"] == expected
    assert plan["omitted_candidate_iterations"] == [
        iteration for iteration in LADDER if iteration not in expected
    ]
    assert plan["launchable"] is bool(expected)


def test_ladder_parser_rejects_ambiguous_contracts() -> None:
    assert parse_ladder("5,250,500,4000") == LADDER
    assert parse_budgets("5:900,250:1800,500:3600,4000:21600", LADDER) == BUDGETS
    with pytest.raises(ValueError, match="strictly increasing"):
        parse_ladder("500,5")
    with pytest.raises(ValueError, match="exactly match"):
        parse_budgets("5:900,250:1800,500:3600", LADDER)
    with pytest.raises(ValueError, match="cannot exceed"):
        build_plan(
            ladder=LADDER,
            budgets=BUDGETS,
            training_timeouts={5: 600, 250: 1500, 500: 3000, 4000: 22000},
            run_started=datetime(2026, 8, 16, 20, 0, tzinfo=UTC),
            now=datetime(2026, 8, 16, 20, 0, tzinfo=UTC),
            max_walltime_seconds=36000,
            deadline=DEADLINE,
            finalization_reserve_seconds=7200,
            portal_reserve_seconds=2700,
        )


def test_ladder_outcome_binds_a_completed_prefix(tmp_path: Path) -> None:
    plan = build_plan(
        ladder=LADDER,
        budgets=BUDGETS,
        training_timeouts=TRAINING_TIMEOUTS,
        now=datetime(2026, 8, 16, 20, 20, tzinfo=UTC),
        run_started=datetime(2026, 8, 16, 20, 20, tzinfo=UTC),
        max_walltime_seconds=36000,
        deadline=DEADLINE,
        finalization_reserve_seconds=7200,
        portal_reserve_seconds=2700,
    )
    plan_path = tmp_path / "ladder-plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    outcome = build_outcome(
        plan,
        plan_path=plan_path,
        completed=[5, 250, 500],
        timed_out=4000,
        completed_utc=datetime(2026, 8, 17, 1, 0, tzinfo=UTC),
    )
    assert outcome["completed_candidate_iterations"] == [5, 250, 500]
    assert outcome["runtime_omitted_candidate_iterations"] == [4000]
    assert outcome["plan"]["sha256"] == hashlib.sha256(plan_path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="ordered prefix"):
        build_outcome(
            plan,
            plan_path=plan_path,
            completed=[5, 500],
            timed_out=None,
            completed_utc=datetime(2026, 8, 17, 1, 0, tzinfo=UTC),
        )


def test_publisher_accepts_a_quality_first_deadline_route(tmp_path: Path) -> None:
    plan = build_plan(
        ladder=LADDER,
        budgets=BUDGETS,
        training_timeouts=TRAINING_TIMEOUTS,
        now=datetime(2026, 8, 16, 21, 0, tzinfo=UTC),
        run_started=datetime(2026, 8, 16, 21, 0, tzinfo=UTC),
        max_walltime_seconds=36000,
        deadline=DEADLINE,
        finalization_reserve_seconds=7200,
        portal_reserve_seconds=2700,
    )
    assert plan["scheduled_candidate_iterations"] == [5, 250, 4000]
    plan_path = tmp_path / "ladder-plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    outcome = build_outcome(
        plan,
        plan_path=plan_path,
        completed=[5, 250, 4000],
        timed_out=None,
        completed_utc=datetime(2026, 8, 17, 3, 30, tzinfo=UTC),
    )
    (tmp_path / "ladder-outcome.json").write_text(json.dumps(outcome), encoding="utf-8")
    selection = {
        "candidates": [
            {"label": "stage-5"},
            {"label": "stage-250"},
            {"label": "stage-4000"},
        ]
    }
    assert validate_ladder_evidence(tmp_path, selection) == {
        "stage-5",
        "stage-250",
        "stage-4000",
    }


def test_ladder_plan_accounts_for_time_spent_before_the_stock_gate() -> None:
    plan = build_plan(
        ladder=LADDER,
        budgets=BUDGETS,
        training_timeouts=TRAINING_TIMEOUTS,
        run_started=datetime(2026, 8, 16, 19, 0, tzinfo=UTC),
        now=datetime(2026, 8, 16, 20, 0, tzinfo=UTC),
        max_walltime_seconds=36000,
        deadline=DEADLINE,
        finalization_reserve_seconds=7200,
        portal_reserve_seconds=2700,
    )
    assert plan["submission_candidate_budget_available_seconds"] > 27900
    assert plan["runtime_candidate_budget_available_seconds"] == 25200
    assert plan["scheduled_candidate_iterations"] == [5, 250, 4000]
