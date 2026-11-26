"""What the cohort contains, read straight from the bundle files (never through a FHIR server).

Used to keep the cohort from losing what FHIR over MCP's eval needs. The inhaler test here is a
coarse presence check on the medication's text, not a medication classification.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from synthetic_cohort._paths import BUNDLE_DIR

ASTHMA_CODES = frozenset({"195967001", "233678006"})
COPD_CODES = frozenset({"87433001", "185086009"})
# LOINC codes for lung-function readings we look for (FEV1/FVC, FEV1, FVC, peak flow).
LUNG_FUNCTION_LOINC = frozenset({"19926-5", "20150-9", "19868-9", "19935-6", "33452-4"})


@dataclass
class PatientSummary:
    ref: str
    asthma: bool = False
    copd: bool = False
    inhaler_requests: int = 0
    lung_function_obs: int = 0
    lung_function_codes: set[str] = field(default_factory=set)


@dataclass
class CohortReport:
    patients: list[PatientSummary]
    total_bytes: int

    @property
    def asthma(self) -> int:
        return sum(p.asthma for p in self.patients)

    @property
    def copd(self) -> int:
        return sum(p.copd for p in self.patients)

    @property
    def with_inhalers(self) -> int:
        return sum(p.inhaler_requests > 0 for p in self.patients)

    @property
    def with_lung_function(self) -> int:
        return sum(p.lung_function_obs > 0 for p in self.patients)

    @property
    def asthma_with_lung_function(self) -> int:
        return sum(p.asthma and p.lung_function_obs > 0 for p in self.patients)

    def lines(self) -> list[str]:
        return [
            f"patients: {len(self.patients)}",
            f"with asthma: {self.asthma}",
            f"with COPD: {self.copd}",
            f"with inhaler medication requests: {self.with_inhalers}",
            f"with lung-function observations: {self.with_lung_function}",
            f"asthma patients with lung-function observations: {self.asthma_with_lung_function}",
            f"bundle bytes: {self.total_bytes}",
        ]


def _resources(bundle: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for entry in bundle.get("entry", []):
        if "resource" in entry:
            yield entry["resource"]


def _codes(concept: dict[str, Any] | None) -> set[str]:
    return {c.get("code", "") for c in (concept or {}).get("coding", [])}


def _text(concept: dict[str, Any] | None) -> str:
    concept = concept or {}
    parts = [concept.get("text", "")] + [c.get("display", "") for c in concept.get("coding", [])]
    return " ".join(p for p in parts if p)


def summarise_bundle(bundle: dict[str, Any]) -> PatientSummary | None:
    resources = list(_resources(bundle))
    patients = [r for r in resources if r.get("resourceType") == "Patient"]
    if len(patients) != 1:
        return None  # hospital or practitioner bundle
    summary = PatientSummary(ref=f"Patient/{patients[0]['id']}")
    for r in resources:
        kind = r.get("resourceType")
        if kind == "Condition":
            codes = _codes(r.get("code"))
            summary.asthma |= bool(codes & ASTHMA_CODES)
            summary.copd |= bool(codes & COPD_CODES)
        elif kind == "MedicationRequest":
            if "inhal" in _text(r.get("medicationCodeableConcept")).lower():
                summary.inhaler_requests += 1
        elif kind == "Observation":
            hits = _codes(r.get("code")) & LUNG_FUNCTION_LOINC
            if hits:
                summary.lung_function_obs += 1
                summary.lung_function_codes |= hits
    return summary


def check(bundle_dir: Path = BUNDLE_DIR) -> CohortReport:
    patients: list[PatientSummary] = []
    total = 0
    for path in sorted(bundle_dir.glob("*.json")):
        total += path.stat().st_size
        summary = summarise_bundle(json.loads(path.read_text()))
        if summary is not None:
            patients.append(summary)
    return CohortReport(patients=patients, total_bytes=total)
