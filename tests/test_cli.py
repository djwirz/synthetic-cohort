from __future__ import annotations

import pytest

from synthetic_cohort.cli import main


def test_check_reports_patients_and_coverage_states(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert "patients: 35" in out
    assert "members covered: 23" in out
    assert "members ambiguous: 4" in out
