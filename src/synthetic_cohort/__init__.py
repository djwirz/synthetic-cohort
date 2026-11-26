"""One reproducible set of synthetic patients, shared by pinning a version (spec §4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from synthetic_cohort._manifest import read_manifest
from synthetic_cohort._members import Member, Patient, read_members, read_patients
from synthetic_cohort._paths import BUNDLE_DIR, MANIFEST, MEMBERS

__all__ = ["Member", "Patient", "bundle_dir", "manifest", "members", "patients"]


def bundle_dir() -> Path:
    return BUNDLE_DIR


def manifest() -> dict[str, Any]:
    return read_manifest(MANIFEST)


def patients() -> list[Patient]:
    """Every patient in the cohort, ordered by id."""
    return read_patients(BUNDLE_DIR)


def members() -> list[Member]:
    return read_members(MEMBERS)
