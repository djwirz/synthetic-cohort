"""The member derivation, on small made-up inputs."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from synthetic_cohort._members import (
    Member,
    Patient,
    Period,
    derive_members,
    read_periods,
    state_counts,
)

REFERENCE = date(2026, 11, 1)


def patient(n: int) -> Patient:
    return Patient(f"p{n:02}", ("Test",), f"Family{n}", "1980-01-01", Path(f"p{n:02}.json"))


def period(
    n: int,
    *,
    start: str = "2026-01-01",
    end: str = "2027-01-01",
    payer: str = "Acme",
    member_id: str = "",
) -> Period:
    return Period(
        f"p{n:02}", payer, member_id or f"m{n:02}", f"{start}T10:00:00Z", f"{end}T10:00:00Z"
    )


PATIENTS = [patient(n) for n in range(10)]
PERIODS = [period(n) for n in range(10)]


def derive(patients: list[Patient], periods: list[Period], per_state: int = 2) -> list[Member]:
    return derive_members(patients, periods, REFERENCE, per_state=per_state)


def only(periods: list[Period]) -> Member:
    (member,) = derive([patient(0)], periods, per_state=0)
    return member


def test_every_state_is_assigned() -> None:
    members = derive(PATIENTS, PERIODS)
    assert state_counts(members) == {"covered": 4, "inactive": 2, "missing": 2, "ambiguous": 2}
    assert all((m["source"] == "synthea") == (m["coverage_state"] == "covered") for m in members)


def test_same_input_same_output_in_any_order() -> None:
    again = derive(PATIENTS[::-1], PERIODS[::-1])
    assert derive(PATIENTS, PERIODS) == again
    assert [m["patient_id"] for m in again] == [p.id for p in PATIENTS]


def test_another_seed_picks_other_patients() -> None:
    other = derive_members(PATIENTS, PERIODS, REFERENCE, seed=1, per_state=2)
    assert other != derive(PATIENTS, PERIODS)


def test_latest_real_period_wins_and_uninsured_rows_are_ignored() -> None:
    member = only(
        [
            period(0, start="2024-01-01", end="2025-01-01", member_id="old"),
            period(0, start="2025-01-01", end="2026-01-01", member_id="latest"),
            period(0, start="2026-01-01", end="2027-01-01", payer="NO_INSURANCE"),
            period(0, start="2026-11-02", end="2027-11-02", member_id="future"),
        ]
    )
    assert (member["member_id"], member["coverage_state"], member["source"]) == (
        "latest",
        "inactive",
        "synthea",
    )
    assert (member["coverage_start"], member["coverage_end"]) == ("2025-01-01", "2026-01-01")


@pytest.mark.parametrize(
    ("start", "end", "state"),
    [
        ("2026-11-01", "2027-11-01", "covered"),  # starts on the reference date
        ("2025-11-01", "2026-11-01", "inactive"),  # ends on it
        ("2025-11-02", "2026-11-02", "covered"),
    ],
)
def test_coverage_boundaries(start: str, end: str, state: str) -> None:
    assert only([period(0, start=start, end=end)])["coverage_state"] == state


def test_synthea_inactive_counts_towards_the_total() -> None:
    periods = [period(0, start="2024-01-01", end="2025-01-01"), *PERIODS[1:]]
    inactive = [m for m in derive(PATIENTS, periods) if m["coverage_state"] == "inactive"]
    assert sorted(m["source"] for m in inactive) == ["assigned", "synthea"]


def test_assigned_inactive_ends_the_day_before_and_needs_an_earlier_start() -> None:
    # Only p00 and p01 started before 2026-10-31, so they are the only ones who can lapse.
    periods = [period(0), period(1)] + [period(n, start="2026-10-31") for n in range(2, 10)]
    inactive = [m for m in derive(PATIENTS, periods) if m["coverage_state"] == "inactive"]
    assert [m["patient_id"] for m in inactive] == ["p00", "p01"]
    assert {m["coverage_end"] for m in inactive} == {"2026-10-31"}


def test_patient_without_a_payer_record_stops() -> None:
    with pytest.raises(ValueError, match="p00 has no payer record"):
        only([period(0, payer="NO_INSURANCE")])


def test_too_few_covered_patients_stops() -> None:
    with pytest.raises(ValueError, match="too few covered patients"):
        derive(PATIENTS[:5], PERIODS[:5])


def test_reads_synthea_csv_files(tmp_path: Path) -> None:
    (tmp_path / "payers.csv").write_text("Id,NAME\nx,Acme\n")
    (tmp_path / "payer_transitions.csv").write_text(
        "PATIENT,MEMBERID,START_DATE,END_DATE,PAYER\n"
        "p00,m00,2026-01-01T10:00:00Z,2027-01-01T10:00:00Z,x\n"
    )
    assert read_periods(tmp_path) == [period(0)]
