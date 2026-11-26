"""The committed data: unchanged since its manifest, and still has what the consumers need."""

from __future__ import annotations

import synthetic_cohort
from synthetic_cohort._manifest import file_hashes, members_entry, sha256_file
from synthetic_cohort._paths import BUNDLE_DIR, DATA_DIR, KEEP_MODULE, MEMBERS, PROPERTIES
from synthetic_cohort.check import check
from tests.cohort_files import patient_resources


def test_bundles_match_the_manifest() -> None:
    """A changed, added or missing bundle fails here: regenerate and review it on purpose."""
    assert file_hashes(BUNDLE_DIR) == synthetic_cohort.manifest()["files"]


def test_other_data_files_match_the_manifest() -> None:
    manifest = synthetic_cohort.manifest()
    assert members_entry(MEMBERS) == manifest["members"]
    assert sha256_file(PROPERTIES) == manifest["generation"]["properties_sha256"]
    assert sha256_file(KEEP_MODULE) == manifest["generation"]["keep_module_sha256"]


def test_data_holds_nothing_the_manifest_does_not_cover() -> None:
    found = {p.relative_to(DATA_DIR).as_posix() for p in DATA_DIR.rglob("*") if p.is_file()}
    expected = {f"bundles/{name}" for name in synthetic_cohort.manifest()["files"]} | {
        "manifest.json",
        "members.json",
        PROPERTIES.name,
        KEEP_MODULE.name,
    }
    assert found - {".DS_Store", "bundles/.DS_Store"} == expected


def test_cohort_has_what_the_eval_needs() -> None:
    # Minimums, not exact counts, set a little under what the pinned cohort has
    # (FHIR over MCP's ADR 0007, carried over by ADR 0002 here).
    report = check()
    assert len(report.patients) >= 30
    assert report.asthma >= 5
    assert report.copd >= 10
    assert report.with_inhalers >= 15
    assert report.with_lung_function >= 10
    # Size guard: the bundles are committed.
    assert report.total_bytes < 40_000_000


def test_every_coverage_state_occurs() -> None:
    members = synthetic_cohort.members()
    counts = {
        state: sum(m["coverage_state"] == state for m in members)
        for state in ("covered", "inactive", "missing", "ambiguous")
    }
    assert counts == {"covered": 23, "inactive": 4, "missing": 4, "ambiguous": 4}


def test_members_are_the_same_people_as_the_bundles() -> None:
    from_bundles = {}
    for patient in patient_resources():
        (name,) = [n for n in patient["name"] if n["use"] == "official"]
        from_bundles[patient["id"]] = (name["given"], name["family"], patient["birthDate"])
    members = synthetic_cohort.members()
    assert len(members) == len(from_bundles) == 35
    assert {
        m["patient_id"]: (m["given"], m["family"], m["birth_date"]) for m in members
    } == from_bundles


def test_member_dates_agree_with_the_state() -> None:
    reference = "2026-11-01"
    for m in synthetic_cohort.members():
        assert m["coverage_start"] <= reference
        assert (m["coverage_end"] > reference) == (m["coverage_state"] != "inactive")


def test_patients_point_at_their_bundles() -> None:
    patients = synthetic_cohort.patients()
    assert [p.id for p in patients] == [m["patient_id"] for m in synthetic_cohort.members()]
    for p in patients:
        assert p.bundle.parent == synthetic_cohort.bundle_dir()
        assert p.id in p.bundle.name
