"""Check hard thresholds, empty modules and machine-readable coverage input."""

import json
from pathlib import Path
from typing import Any

import pytest

from ci.coverage_check import evaluate, main


@pytest.mark.unit
def test_thresholds(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config = {
        "line_minimum": 80,
        "critical_branch_minimum": 95,
        "critical_paths": ["framework/ledger", "framework/approval"],
    }
    report: dict[str, Any] = {
        "totals": {"num_statements": 100, "covered_lines": 80},
        "files": {
            "framework/ledger/x.py": {"summary": {"num_branches": 100, "covered_branches": 95}}
        },
    }
    assert not evaluate(report, config)
    report["totals"]["covered_lines"] = 79
    report["files"]["framework/ledger/x.py"]["summary"]["covered_branches"] = 94
    assert evaluate(report, config) == ["global_line_coverage", "framework/ledger"]
    report["totals"]["num_statements"] = 0
    report["files"] = {}
    assert not evaluate(report, config)
    monkeypatch.chdir(tmp_path)
    Path(".coverage.json").write_text(json.dumps(report))
    Path("pyproject.toml").write_text(
        "[tool.codingsystem.coverage]\nline_minimum=80\ncritical_branch_minimum=95\n"
        'critical_paths=["framework/ledger"]\n'
    )
    assert main() == 0
