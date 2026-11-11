"""Prove every architectural boundary using the actual import-linter CLI."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("contract", "source", "target"),
    [
        ("engine", "codingsystem.orchestration", "langgraph"),
        ("framework", "codingsystem.engine", "codingsystem_agent_skeletons"),
        ("agent", "codingsystem_agent_skeletons", "codingsystem.ledger"),
        ("contracts", "codingsystem.contracts", "codingsystem.sdk"),
        ("worker", "codingsystem.sdk", "codingsystem.approval"),
        ("root-engine", "codingsystem", "langgraph"),
    ],
)
def test_boundary_rejects_import(contract: str, source: str, target: str, tmp_path: Path) -> None:
    import configparser

    config = configparser.ConfigParser()
    config.read(ROOT / ".importlinter")
    packages = ["codingsystem", "codingsystem_agent_skeletons", "langgraph"]
    packages += [
        f"codingsystem.{path.name}"
        for path in (ROOT / "framework").iterdir()
        if (path / "__init__.py").is_file()
    ]
    for package in packages:
        directory = tmp_path.joinpath(*package.split("."))
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").write_text('"""Fixture package."""\n')
    if contract == "agent":
        (tmp_path / "codingsystem_agent_skeletons/__init__.py").write_text(
            "import codingsystem.sdk\nimport codingsystem.contracts\n"
        )
    env = dict(os.environ, PYTHONPATH=str(tmp_path), PYTHONDONTWRITEBYTECODE="1")
    command = [
        str(Path(sys.executable).parent / "lint-imports"),
        "--config",
        str(ROOT / ".importlinter"),
        "--contract",
        contract,
        "--no-cache",
    ]
    positive = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True, text=True)
    assert positive.returncode == 0, positive.stdout + positive.stderr
    tmp_path.joinpath(*source.split("."), "__init__.py").write_text(f"import {target}\n")
    negative = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True, text=True)
    assert negative.returncode == 1, negative.stdout + negative.stderr
    assert "BROKEN" in negative.stdout
