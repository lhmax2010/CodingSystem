"""Test actual-prefix scanning without modifying the development environment."""

from pathlib import Path

import pytest

from ci.installed import unlisted_files


@pytest.mark.unit
def test_unowned_files_and_links(tmp_path: Path) -> None:
    prefix = tmp_path / "venv"
    prefix.mkdir()
    (prefix / "lib").mkdir()
    (prefix / "lib64").symlink_to("lib")
    (prefix / "bin").mkdir()
    home = tmp_path / "system"
    home.mkdir()
    (home / "python3.12").write_text("safe executable fixture")
    (prefix / "pyvenv.cfg").write_text(f"home = {home}\n")
    (prefix / "bin/python3.12").symlink_to(home / "python3.12")
    (prefix / "bin/python").symlink_to("python3.12")
    assert not unlisted_files(prefix, set())
    compiled = prefix / "lib/runtime.pyc"
    compiled.write_bytes(b"runtime")
    assert any("runtime_pyc_unlisted" in r for r in unlisted_files(prefix, set()))
    compiled.unlink()
    data = prefix / "lib/unowned.txt"
    data.write_text("<" + "?" + "PHP echo 1;")
    assert any("unclassified_text_signal" in r for r in unlisted_files(prefix, set()))
    data.unlink()
    (prefix / "bin/other").symlink_to(home / "python3.12")
    assert any("external_symlink" in r for r in unlisted_files(prefix, set()))
    (prefix / "bin/other").unlink()
    owned = prefix / "lib/installed.pyc"
    owned.write_bytes(b"installed bytecode already checked via RECORD")
    assert not unlisted_files(prefix, {owned.resolve()})
