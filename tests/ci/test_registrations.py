"""Exercise exact bypass approvals and all provisional mismatch directions."""

import json
from pathlib import Path

import pytest

from ci import checks, registrations


def register(hits: list[dict[str, object]]) -> None:
    """Write review metadata for synthetic cases only."""
    entries = [
        dict(h, reason="synthetic fixture", task="task-test", remove_when="fixture ends")
        for h in hits
    ]
    Path("ci/bypass_register.json").write_text(json.dumps({"entries": entries}))


@pytest.mark.unit
@pytest.mark.parametrize("form", ["comment", "skip", "skipif", "xfail", "alias", "decorator"])
def test_bypass_exact_approval(form: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("ci").mkdir()
    path = Path("case.py")
    snippets = {
        "comment": "x = 1  # " + "pragma: no cover",
        "skip": "import pytest\npytest." + "skip('reason')",
        "skipif": "import pytest\n@pytest.mark."
        + "skipif(True, reason='case')\ndef test_x(): pass",
        "xfail": "import pytest\npytest." + "xfail('reason')",
        "alias": "from pytest import skip as stop\nstop('reason')",
        "decorator": "import pytest\n@pytest.mark." + "xfail\ndef test_reason(): pass",
    }
    path.write_text(snippets[form])
    monkeypatch.setattr(checks, "repository_files", lambda: [path])
    register([])
    assert registrations.check_bypass() == 1
    hits = registrations.source_bypasses(path)
    assert hits
    register(hits)
    assert registrations.check_bypass() == 0
    path.write_text(
        snippets[form]
        .replace("reason", "changed")
        .replace("x = 1", "x = 2")
        .replace("mark.xfail", "mark.skip")
    )
    assert registrations.check_bypass() == 1


@pytest.mark.unit
def test_bypass_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("ci").mkdir()
    project = Path("pyproject.toml")
    project.write_text("""[tool.coverage.run]
omit = ["hidden.py"]
[tool.coverage.report]
exclude_lines = ["hidden"]
[tool.ruff]
extend-exclude = ["hidden"]
[tool.ruff.lint.per-file-ignores]
"hidden.py" = ["F"]
[[tool.mypy.overrides]]
module = "hidden"
ignore_errors = true
[tool.pytest.ini_options]
addopts = "-k selected"
""")
    imports = Path(".importlinter")
    imports.write_text("[importlinter:contract:engine]\nignore_imports =\n    one -> two\n")
    monkeypatch.setattr(checks, "repository_files", lambda: [project, imports])
    register([])
    assert registrations.check_bypass() == 1
    hits = registrations.config_bypasses(project) + registrations.config_bypasses(imports)
    assert len(hits) == 7
    register(hits)
    assert registrations.check_bypass() == 0
    imports.write_text(imports.read_text().replace("two", "three"))
    assert registrations.check_bypass() == 1


@pytest.mark.unit
def test_provisional_exact_locations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("docs/dev").mkdir(parents=True)
    Path("framework").mkdir()
    Path("docs/dev/01_extension_mapping.md").write_text(
        "| B7-1-2 | text | type | 父键（不归批） |\n| B7-1-2-leaf | text | type | 第一批 |\n"
    )
    code = Path("framework/model.py")
    table = Path("docs/dev/provisional.md")
    head = "| 位置 | 对应映射表子键 | 预计通过日期 |\n|---|---|---|\n"
    key = "B7-1-2-leaf"
    code.write_text("# PROVISIONAL" + f"({key})\n")
    monkeypatch.setattr(checks, "repository_files", lambda: [code])
    table.write_text(head)
    assert registrations.check_provisional() == 1  # Annotation without registration.
    row = f"| framework/model.py:1 | {key} | 2026-12-11 |\n"
    table.write_text(head + row)
    assert registrations.check_provisional() == 0
    for invalid in ("B7-unknown", "B7-1-2"):
        code.write_text("# PROVISIONAL" + f"({invalid})\n")
        table.write_text(head + row.replace(key, invalid))
        assert registrations.check_provisional() == 1
    table.write_text(head + row)
    code.write_text("# no annotations\n")
    assert registrations.check_provisional() == 1  # Registration without annotation.
    code.write_text("\n# PROVISIONAL" + f"({key})\n")
    assert registrations.check_provisional() == 1  # Correct key at the wrong location.
    table.unlink()
    with pytest.raises(FileNotFoundError):
        registrations.check_provisional()


@pytest.mark.unit
@pytest.mark.parametrize(
    "filename,body",
    [
        (".coveragerc", "[run]\nomit = missing.py\n"),
        ("mypy.ini", "[mypy-missing.*]\nignore_errors = True\n"),
        ("pytest.ini", "[pytest]\naddopts = --deselect=test_missing.py\n"),
        (".ruff.toml", 'extend-exclude = ["missing.py"]\n'),
    ],
)
def test_alternative_configuration_files(filename: str, body: str, tmp_path: Path) -> None:
    path = tmp_path / filename
    path.write_text(body)
    assert registrations.config_bypasses(path)
