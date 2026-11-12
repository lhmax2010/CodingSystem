"""Verify inspection policy failures, provenance and exact classification boundaries."""

import importlib.metadata as metadata
import sys
from importlib.metadata import PathDistribution
from pathlib import Path
from typing import Any

import pytest

from ci import checks
from ci.d23 import POLICY_VERSION, SIGNALS, digest


@pytest.mark.unit
def test_repository_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    Path("one").write_text("safe")
    monkeypatch.setattr(checks, "git", lambda *args: b"one\0missing\0one\0")
    assert checks.repository_files() == [Path("one")]


@pytest.mark.unit
def test_git_and_json(tmp_path: Path) -> None:
    assert checks.git("rev-parse", "--is-inside-work-tree").strip() == b"true"
    path = tmp_path / "policy.json"
    path.write_text('{"version": "one"}')
    assert checks.json_file(str(path)) == {"version": "one"}
    path.write_text("[]")
    with pytest.raises(ValueError):
        checks.json_file(str(path))


@pytest.mark.unit
def test_content_policy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("safe\nsecret\n")
    monkeypatch.setattr(checks, "repository_files", lambda: [path])
    policy: dict[str, Any] = {"version": "v1", "rules": {"test": "secret"}}
    exceptions: dict[str, Any] = {"version": "v1", "entries": []}
    monkeypatch.setattr(
        checks, "json_file", lambda name: policy if "policy" in name else exceptions
    )
    assert checks.content_hits(path.read_bytes(), policy["rules"]) == [("test", 2)]
    assert checks.check_content() == 1
    exceptions["entries"] = [
        {
            "path": str(path),
            "rule": "test",
            "line": 2,
            "reason": "synthetic test",
            "digest": digest(path.read_bytes()),
        }
    ]
    assert checks.check_content() == 0
    path.write_text("changed\nsecret")
    assert checks.check_content() == 1
    exceptions["version"] = "other"
    with pytest.raises(ValueError):
        checks.check_content()


@pytest.mark.unit
def test_history(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def git(*args: str) -> bytes:
        if args[0] == "rev-list":
            return b"commit1\ncommit2\n"
        if args[0] == "ls-tree":
            return b"100644 blob blob1\tfile.txt\0\0160000 commit sub\tsub\0"
        return b"secret"

    monkeypatch.setattr(checks, "git", git)
    monkeypatch.setattr(checks, "json_file", lambda name: {"rules": {"test": "secret"}})
    assert checks.historical_content() == 0
    output = capsys.readouterr().out
    assert "findings: 1" in output
    assert "commit1 blob1 file.txt:1 test" in output
    assert "secret" not in output


@pytest.mark.unit
def test_d23_inventory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    Path("pyvenv.cfg").write_text("home = /usr/bin\n")
    path = Path("safe.py")
    path.write_text('"""Safe."""')
    Path("uv.lock").write_text('[[package]]\nname="safe"\n')
    policy: dict[str, Any] = {
        "version": POLICY_VERSION,
        "parsers": {".py": "python-ast-tokenize"},
        "signatures": list(SIGNALS),
        "pure_data": {},
        "executable_inputs": [],
    }
    scanner: dict[str, Any] = {"version": POLICY_VERSION, "files": {}}
    monkeypatch.setattr(checks, "json_file", lambda name: scanner if "digests" in name else policy)
    monkeypatch.setattr(checks, "repository_files", lambda: [path])
    dist = Path("safe.dist-info")
    dist.mkdir()
    (dist / "METADATA").write_text("Name: safe\nVersion: 1.0\n")
    (dist / "RECORD").write_text("safe.py,,\n")
    monkeypatch.setattr(metadata, "distributions", lambda: [PathDistribution(dist)])
    assert checks.check_d23() == 0
    (dist / "METADATA").write_text("Name: safe\nVersion: 1.0\nRequires-Dist: php-cli\n")
    assert checks.check_d23() == 1
    (dist / "RECORD").write_text("missing,,\n")
    assert checks.check_d23() == 1
    (dist / "RECORD").unlink()
    assert checks.check_d23() == 1
    (dist / "RECORD").write_text("safe.py,,\n")
    path.write_text("<" + "?" + "php echo 1;")
    Path("uv.lock").write_text('[[package]]\nname="php-cli"\n')
    assert checks.check_d23() == 1
    scanner["version"] = "other"
    with pytest.raises(ValueError):
        checks.check_d23()
    scanner["version"] = POLICY_VERSION
    policy["signatures"] = []
    with pytest.raises(ValueError):
        checks.check_d23()
    policy["parsers"] = {}
    with pytest.raises(ValueError):
        checks.check_d23()


@pytest.mark.unit
def test_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["checks", "unknown"])
    assert checks.main() == 2
    monkeypatch.setattr(sys, "argv", ["checks", "content"])
    monkeypatch.setattr(checks, "check_content", lambda: 0)
    assert checks.main() == 0


@pytest.mark.unit
def test_real_content_signals() -> None:
    rules = checks.json_file("ci/content_policy.json")["rules"]
    values = {
        "private-key": "-----BEGIN " + "RSA PRIVATE KEY-----",
        "token": "ghp_" + "a" * 36,
        "credential-assignment": 'password = "' + "a" * 24 + '"',
        "internal-host": "build." + "corp",
        "private-ipv4": "10." + "2.3.4",
        "private-ipv6": "fd" + "00::1234",
        "perforce-path": "/" + "/depot/product/file",
    }
    for rule, value in values.items():
        assert checks.content_hits(value.encode(), {rule: rules[rule]}), rule


@pytest.mark.unit
def test_expanded_content_signals() -> None:
    rules = checks.json_file("ci/content_policy.json")["rules"]
    samples = {
        "private-key": [
            "-----BEGIN " + x + " PRIVATE KEY" + tail + "-----"
            for x, tail in [("ENCRYPTED", ""), ("PGP", " BLOCK")]
        ],
        "token": [
            prefix + "a" * 40
            for prefix in [
                "sk-" + "proj-",
                "sk-" + "ant-api03-",
                "xox" + "b-",
                "gl" + "pat-",
                "AI" + "za",
            ]
        ],
        "credential-assignment": [
            key + " = " + quote + value + quote
            for key in ["pass" + "word", "client_" + "secret"]
            for quote in ["", '"', "'"]
            for value in [
                "a" * 8,
                "example" + "12345",
                "placeholder" + "123",
                "redacted" + "@!#abc",
                "a" * 12,
            ]
        ],
        "authorization-bearer": ["Authorization: " + "Bear" + "er " + "a" * 15 + "1"],
        "private-ipv4": ["10." + "2.3.4."],
        "perforce-path": [
            "/" + "/" + name + "/product/file" for name in ["SHARED", "Depot", "Other"]
        ],
    }
    for rule, values in samples.items():
        for value in values:
            assert checks.content_hits(value.encode(), {rule: rules[rule]}), rule
    for value in ["10." + "1.2.3.4", "https://example.com/product/file"]:
        assert not checks.content_hits(value.encode(), rules)


@pytest.mark.unit
def test_bearer_token_shape() -> None:
    rules = checks.json_file("ci/content_policy.json")["rules"]
    rule = "authorization-bearer"
    prefix = "bear" + "er "
    negatives = [
        prefix + "token",
        prefix + "principal",
        "(" + prefix + "principal, endpoint)",
        prefix + "a" * 14 + "1",
        prefix + "a" * 16,
        prefix + "a" * 16 + " 1",
        prefix + "a" * 15 + "\u212a" + "1",
    ]
    for sample in negatives:
        if checks.content_hits(sample.encode(), {rule: rules[rule]}):
            pytest.fail(rule, pytrace=False)
    for token in ["a" * 15 + "1", "1" + "a" * 15, "a" * 20 + "1", "a" * 8 + "._~+/=-1"]:
        for word in ["bear" + "er", "BEAR" + "ER", "BeAr" + "Er"]:
            for separator in [" ", "\t"]:
                for quote in ["", '"', "'"]:
                    sample = "Authorization: " + quote + word + separator + token + quote
                    hits = checks.content_hits(sample.encode(), {rule: rules[rule]})
                    if hits != [(rule, 1)]:
                        pytest.fail(rule, pytrace=False)
