"""Apply separate global line and critical-module branch coverage requirements."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any


def evaluate(report: dict[str, Any], config: dict[str, Any]) -> list[str]:
    """Return failures without changing thresholds for empty or branchless modules."""
    failures = []
    totals = report["totals"]
    statements = totals["num_statements"]
    lines = 100.0 * totals["covered_lines"] / statements if statements else 100.0
    print(f"Global line coverage: {lines:.2f}% >= {config['line_minimum']}%")
    if lines < config["line_minimum"]:
        failures.append("global_line_coverage")
    for prefix in config["critical_paths"]:
        selected = [
            value["summary"]
            for name, value in report["files"].items()
            if name == prefix or name.startswith(prefix + "/")
        ]
        branches = sum(item["num_branches"] for item in selected)
        covered = sum(item["covered_branches"] for item in selected)
        if not branches:
            print(f"Critical {prefix}: N/A (no measured branches; threshold remains 95%)")
            continue
        percent = 100.0 * covered / branches
        print(f"Critical {prefix}: {percent:.2f}% >= {config['critical_branch_minimum']}%")
        if percent < config["critical_branch_minimum"]:
            failures.append(prefix)
    return failures


def main() -> int:
    """Read coverage's machine-readable evidence and the checked-in thresholds."""
    report = json.loads(Path(".coverage.json").read_text())
    config = tomllib.loads(Path("pyproject.toml").read_text())["tool"]["codingsystem"]["coverage"]
    return int(bool(evaluate(report, config)))


if __name__ == "__main__":
    raise SystemExit(main())
