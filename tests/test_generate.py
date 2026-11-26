"""The parts of generate that don't need Docker or the network."""

from __future__ import annotations

from pathlib import Path

import pytest

from synthetic_cohort.generate import (
    RUNS,
    SYNTHEA_VERSION,
    checkout_root,
    ensure_jar,
    synthea_command,
)


def test_runs_from_this_checkout() -> None:
    assert checkout_root() == Path(__file__).resolve().parents[1]


def test_refuses_from_an_installed_copy(tmp_path: Path) -> None:
    installed = tmp_path / "site-packages" / "synthetic_cohort"
    installed.mkdir(parents=True)
    with pytest.raises(RuntimeError, match="only runs from a checkout"):
        checkout_root(installed)


def test_a_wrong_jar_is_deleted(tmp_path: Path) -> None:
    jar = tmp_path / f"synthea-{SYNTHEA_VERSION}.jar"
    jar.write_bytes(b"not synthea")
    with pytest.raises(RuntimeError, match="sha256 mismatch"):
        ensure_jar(tmp_path)
    assert not jar.exists()


def test_csv_export_is_on_and_only_resp_is_filtered(tmp_path: Path) -> None:
    general, resp = (synthea_command(r, tmp_path / "s.jar", tmp_path) for r in RUNS)
    assert "--exporter.csv.export=true" in general
    assert "--exporter.csv.export=true" in resp
    assert "-k" not in general
    assert "/cohort/keep_respiratory.json" in resp
