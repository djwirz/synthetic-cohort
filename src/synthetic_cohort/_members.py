"""members.json: what a caller holds about each patient's insurance (spec §5, ADR 0003).

Payer, member id and period are Synthea's. The states Synthea has nothing for are assigned to
covered patients in an order fixed by hashing a seed with the patient id.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Literal, TypedDict

CoverageState = Literal["covered", "inactive", "missing", "ambiguous"]
STATES: tuple[CoverageState, ...] = ("covered", "inactive", "missing", "ambiguous")
SEED = 3311
# How many patients end up in each state other than covered.
PER_STATE = 4
NO_INSURANCE = "NO_INSURANCE"


class Member(TypedDict):
    patient_id: str
    given: list[str]
    family: str
    birth_date: str
    payer: str
    member_id: str
    coverage_start: str
    coverage_end: str
    coverage_state: CoverageState
    source: Literal["synthea", "assigned"]


@dataclass(frozen=True)
class Patient:
    id: str
    given: tuple[str, ...]
    family: str
    birth_date: str
    bundle: Path


@dataclass(frozen=True)
class Period:
    """One row of Synthea's payer_transitions.csv, with the payer's name looked up."""

    patient_id: str
    payer: str
    member_id: str
    start: str
    end: str


def read_patients(bundle_dir: Path) -> list[Patient]:
    """The Patient of every patient bundle, under their official name, ordered by id."""
    found = []
    for path in bundle_dir.glob("*.json"):
        entries = json.loads(path.read_text()).get("entry", [])
        resources = [e["resource"] for e in entries if "resource" in e]
        in_bundle = [r for r in resources if r.get("resourceType") == "Patient"]
        if len(in_bundle) != 1:
            continue  # hospital or practitioner bundle
        patient = in_bundle[0]
        (name,) = [n for n in patient["name"] if n.get("use") == "official"]
        found.append(
            Patient(
                id=patient["id"],
                given=tuple(name["given"]),
                family=name["family"],
                birth_date=patient["birthDate"],
                bundle=path,
            )
        )
    return sorted(found, key=lambda p: p.id)


def read_periods(csv_dir: Path) -> list[Period]:
    """Read one Synthea run's payers.csv and payer_transitions.csv."""
    with (csv_dir / "payers.csv").open(newline="") as f:
        payers = {row["Id"]: row["NAME"] for row in csv.DictReader(f)}
    with (csv_dir / "payer_transitions.csv").open(newline="") as f:
        return [
            Period(
                patient_id=row["PATIENT"],
                payer=payers[row["PAYER"]],
                member_id=row["MEMBERID"],
                start=row["START_DATE"],
                end=row["END_DATE"],
            )
            for row in csv.DictReader(f)
        ]


def _from_synthea(patient: Patient, periods: Iterable[Period], reference: date) -> Member:
    """The latest period with a real payer that had started by the reference date."""
    real = [
        p
        for p in periods
        if p.payer != NO_INSURANCE and date.fromisoformat(p.start[:10]) <= reference
    ]
    if not real:
        raise ValueError(f"patient {patient.id} has no payer record")
    latest = max(real, key=lambda p: (p.start, p.end, p.member_id))
    covered = date.fromisoformat(latest.end[:10]) > reference
    return Member(
        patient_id=patient.id,
        given=list(patient.given),
        family=patient.family,
        birth_date=patient.birth_date,
        payer=latest.payer,
        member_id=latest.member_id,
        coverage_start=latest.start[:10],
        coverage_end=latest.end[:10],
        coverage_state="covered" if covered else "inactive",
        source="synthea",
    )


def _order(seed: int, patient_id: str) -> str:
    return hashlib.sha256(f"{seed}:{patient_id}".encode()).hexdigest()


def derive_members(
    patients: Sequence[Patient],
    periods: Iterable[Period],
    reference: date,
    *,
    seed: int = SEED,
    per_state: int = PER_STATE,
) -> list[Member]:
    """One entry per patient, ordered by patient id."""
    by_patient: dict[str, list[Period]] = {}
    for period in periods:
        by_patient.setdefault(period.patient_id, []).append(period)
    members = [
        _from_synthea(p, by_patient.get(p.id, []), reference)
        for p in sorted(patients, key=lambda p: p.id)
    ]

    pool = sorted(
        (m for m in members if m["coverage_state"] == "covered"),
        key=lambda m: _order(seed, m["patient_id"]),
    )

    def assign(state: CoverageState, count: int, eligible: list[Member]) -> None:
        if len(eligible) < count:
            raise ValueError(f"too few covered patients to assign {count} as {state}")
        for member in eligible[:count]:
            member["coverage_state"] = state
            member["source"] = "assigned"
            pool.remove(member)

    # An assigned inactive member's coverage ends the day before the reference date, so only a
    # period that started before that day can take it.
    ended = (reference - timedelta(days=1)).isoformat()
    short = max(0, per_state - sum(m["coverage_state"] == "inactive" for m in members))
    lapsing = [m for m in pool if m["coverage_start"] < ended][:short]
    assign("inactive", short, lapsing)
    for member in lapsing:
        member["coverage_end"] = ended
    assign("missing", per_state, list(pool))
    assign("ambiguous", per_state, list(pool))
    return members


def state_counts(members: Iterable[Member]) -> dict[CoverageState, int]:
    counts = Counter(m["coverage_state"] for m in members)
    return {state: counts[state] for state in STATES}


def write_members(members: Sequence[Member], reference: date, path: Path) -> None:
    body: Mapping[str, object] = {"reference_date": reference.isoformat(), "members": members}
    path.write_text(json.dumps(body, indent=2) + "\n")


def read_members(path: Path) -> list[Member]:
    members: list[Member] = json.loads(path.read_text())["members"]
    return members
