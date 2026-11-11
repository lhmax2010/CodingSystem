"""Prove shared test policy in both test trees without making external requests."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
@pytest.mark.parametrize("intranet", [False, True])
def test_both_trees_and_intranet_switch(intranet: bool, tmp_path: Path) -> None:
    (tmp_path / "conftest.py").write_bytes((ROOT / "conftest.py").read_bytes())
    (tmp_path / "pytest.ini").write_text("[pytest]\nmarkers =\n    intranet: internal only\n")
    for name in ("tests/test_root.py", "agents/probe/tests/test_agent.py"):
        path = tmp_path / name
        path.parent.mkdir(parents=True)
        path.write_text(
            "import pytest\nimport socket\n"
            "def test_offline(request):\n"
            "    assert 'offline' in request.fixturenames\n"
            "    with pytest.raises(RuntimeError): socket.getaddrinfo('unused', 1)\n"
            "@pytest.mark." + "intranet\n"
            "def test_intranet():\n"
            "    assert True\n"
        )
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if intranet:
        env["CODINGSYSTEM_INTRANET"] = "1"
    else:
        env.pop("CODINGSYSTEM_INTRANET", None)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert ("4 passed" if intranet else "2 passed, 2 skipped") in result.stdout


@pytest.mark.unit
@pytest.mark.parametrize("outcome", ["skip", "skipif", "xfail", "xpass", "module"])
def test_unmarked_skips_and_xfails_fail(outcome: str, tmp_path: Path) -> None:
    (tmp_path / "conftest.py").write_bytes((ROOT / "conftest.py").read_bytes())
    code = "import pytest\n"
    if outcome == "skip":
        code += "def test_bad(): pytest." + "skip('fixture')\n"
    elif outcome == "module":
        code += "pytest." + "skip('fixture', allow_module_level=True)\n"
    else:
        decorator = "skipif(True, reason='fixture')" if outcome == "skipif" else "xfail"
        code += "@pytest.mark." + decorator + "\ndef test_bad():\n    assert "
        code += "False\n" if outcome == "xfail" else "True\n"
    (tmp_path / "test_bad.py").write_text(code)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q"], cwd=tmp_path, capture_output=True
    )
    assert result.returncode != 0


@pytest.mark.unit
def test_subprocess_namespace_sentinel() -> None:
    """Check the kernel's routes in a child rather than relying on socket monkeypatches."""
    mode = os.environ.get("CODINGSYSTEM_TEST_NETNS", "off")
    child = subprocess.check_output(
        [
            sys.executable,
            "-B",
            "-c",
            "from pathlib import Path; print(Path('/proc/net/route').read_text())",
        ],
        text=True,
    )
    if mode == "on":
        assert len(child.strip().splitlines()) == 1  # No route outside the isolated namespace.
    else:
        assert mode == "off"  # The gate explicitly records the unsupported kernel mode.
