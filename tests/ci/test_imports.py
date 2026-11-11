"""Prove every architectural boundary using the actual import-linter CLI."""

import configparser
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
        ("engine", "codingsystem", "langgraph"),
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
    if contract == "engine":
        (tmp_path / "codingsystem/engine/__init__.py").write_text("import langgraph\n")
        (tmp_path / "codingsystem/engine/helper.py").write_text("import langgraph\n")
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


def complete_lists(root: Path) -> None:
    """Require all installed roots and every framework subpackage in boundary lists."""
    config = configparser.ConfigParser()
    config.read(root / ".importlinter")
    subpackages = {p.name for p in (root / "framework").iterdir() if (p / "__init__.py").is_file()}
    agents = {
        p.name
        for d in (root / "agents").glob("*/src")
        for p in d.iterdir()
        if (p / "__init__.py").is_file()
    }
    assert set(config["importlinter"]["root_packages"].split()) == agents | {"codingsystem"}
    assert set(config["importlinter:contract:engine"]["source_modules"].split()) == agents | {
        "codingsystem"
    }
    for name, field in (
        ("framework", "forbidden_modules"),
        ("agent", "source_modules"),
        ("worker", "source_modules"),
    ):
        assert agents <= set(config[f"importlinter:contract:{name}"][field].split())
    forbidden = set(config["importlinter:contract:contracts"]["forbidden_modules"].split())
    assert forbidden == {f"codingsystem.{n}" for n in subpackages - {"contracts"}}


@pytest.mark.unit
def test_contract_lists_complete_and_detect_new_packages(tmp_path: Path) -> None:
    import shutil

    complete_lists(ROOT)
    shutil.copy(ROOT / ".importlinter", tmp_path / ".importlinter")
    for directory in ("framework", "agents"):
        shutil.copytree(
            ROOT / directory,
            tmp_path / directory,
            ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"),
        )
    added = tmp_path / "framework/new_subpackage"
    added.mkdir()
    (added / "__init__.py").touch()
    with pytest.raises(AssertionError):
        complete_lists(tmp_path)
    (added / "__init__.py").unlink()
    added.rmdir()
    added = tmp_path / "agents/new/src/new_agent"
    added.mkdir(parents=True)
    (added / "__init__.py").touch()
    with pytest.raises(AssertionError):
        complete_lists(tmp_path)
