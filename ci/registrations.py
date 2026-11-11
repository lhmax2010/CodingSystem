"""Match gate bypasses and provisional annotations to reviewed registrations."""

from __future__ import annotations

import ast
import configparser
import io
import json
import re
import shlex
import tokenize
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

from ci.d23 import digest


def source_bypasses(path: Path) -> list[dict[str, Any]]:
    """Inspect actual comments and pytest calls, not example strings in scanners."""
    source = path.read_text()
    tree = ast.parse(source)
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            aliases.update((a.asname or a.name, a.name) for a in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            aliases.update((a.asname or a.name, node.module + "." + a.name) for a in node.names)

    def name(node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return name(node.value) + "." + node.attr
        return ""

    hits: list[dict[str, Any]] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT and re.search(
            r"#\s*(?:type:\s*ignore|noqa\b|pragma:\s*no\s*cover)", token.string
        ):
            hits.append(hit(path, token.start[0], "code-comment", token.line.rstrip()))
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    for node in ast.walk(tree):
        if not isinstance(node, ast.expr):
            continue
        target = node.func if isinstance(node, ast.Call) else node
        if (
            isinstance(target, ast.expr)
            and name(target)
            in {
                "pytest.skip",
                "pytest.xfail",
                "pytest.mark.skip",
                "pytest.mark.skipif",
                "pytest.mark.xfail",
            }
            and not (
                isinstance(parents.get(node), ast.Call)
                and getattr(parents[node], "func", None) is node
            )
        ):
            # Include all lines of the call, so changing a condition invalidates approval.
            segment = "\n".join(source.splitlines()[node.lineno - 1 : node.end_lineno])
            hits.append(hit(path, node.lineno, "pytest-outcome", segment))
    return hits


def hit(path: Path, line: int, rule: str, text: str) -> dict[str, Any]:
    """Identify a source line or complete normalized configuration value."""
    return {"path": str(path), "line": line, "rule": rule, "line_digest": digest(text.encode())}


def config_bypasses(path: Path) -> list[dict[str, Any]]:
    """Cover configuration values including multiline arrays and INI continuations."""
    source = path.read_text()
    hits: list[dict[str, Any]] = []

    def add(section: str, key: str, value: Any) -> None:
        line = 1
        active = ""
        for i, text in enumerate(source.splitlines(), 1):
            if text.startswith("["):
                active = text.strip("[] ")
            if active == section and re.match(r"\s*" + re.escape(key) + r"\s*=", text):
                line = i
                break
        text = section + "." + key + "=" + json.dumps(value, sort_keys=True)
        hits.append(hit(path, line, section + "." + key, text))

    if path.name in {
        ".importlinter",
        ".coveragerc",
        "mypy.ini",
        ".mypy.ini",
        "pytest.ini",
        "setup.cfg",
        "tox.ini",
    }:
        config = configparser.ConfigParser()
        config.read_string(source)
        for section in config.sections():
            if config[section].get("ignore_imports", "").strip():
                add(section, "ignore_imports", config[section]["ignore_imports"])
            for key in ("omit", "exclude_lines", "exclude_also"):
                if config[section].get(key, "").strip() and (
                    section.startswith("coverage:") or path.name == ".coveragerc"
                ):
                    add(section, key, config[section][key])
            if section.startswith("mypy-"):
                add(section, "module_override", dict(config[section]))
            if section in {"pytest", "tool:pytest"}:
                value = config[section].get("addopts", "")
                if selection_options(shlex.split(value)):
                    add(section, "addopts", value)
    elif path.name in {"pyproject.toml", "ruff.toml", ".ruff.toml"}:
        data = tomllib.loads(source)
        tool = data.get("tool", {}) if path.name == "pyproject.toml" else {"ruff": data}
        for section, keys in {
            "coverage": ("omit", "exclude_lines", "exclude_also"),
            "ruff": ("per-file-ignores", "extend-per-file-ignores", "extend-exclude"),
        }.items():

            def walk(value: dict[str, Any], prefix: str, keys: tuple[str, ...] = keys) -> None:
                for key, child in value.items():
                    if key in keys and child:
                        add(prefix, key, child)
                    elif isinstance(child, dict):
                        walk(child, prefix + "." + key)

            walk(tool.get(section, {}), "tool." + section)
        for index, override in enumerate(tool.get("mypy", {}).get("overrides", [])):
            add(f"tool.mypy.overrides.{index}", "overrides", override)
        options = tool.get("pytest", {}).get("ini_options", {}).get("addopts", "")
        args = shlex.split(options) if isinstance(options, str) else options
        if selection_options(args):
            add("tool.pytest.ini_options", "addopts", options)
    return hits


def selection_options(args: list[str]) -> bool:
    """Recognize attached and separate pytest test-selection options."""
    selectors = (
        "--deselect",
        "--ignore",
        "--ignore-glob",
        "--lf",
        "--last-failed",
        "--stepwise",
        "--sw",
        "--pyargs",
    )
    return any(a.startswith(selectors) or a.startswith(("-k", "-m")) for a in args)


def check_bypass() -> int:
    """Require exact entries, nonempty reasons and removal conditions for every bypass."""
    from ci.checks import json_file, repository_files

    found: list[dict[str, Any]] = []
    for path in repository_files():
        if path.suffix in {".py", ".pyi"}:
            found.extend(source_bypasses(path))
        elif path.name in {
            "pyproject.toml",
            ".importlinter",
            ".coveragerc",
            "mypy.ini",
            ".mypy.ini",
            "pytest.ini",
            "setup.cfg",
            "tox.ini",
            "ruff.toml",
            ".ruff.toml",
        }:
            found.extend(config_bypasses(path))
    entries = json_file("ci/bypass_register.json")["entries"]
    fields = ("path", "line", "rule", "line_digest")
    wanted = Counter(tuple(item[k] for k in fields) for item in found)
    approved = Counter(tuple(item.get(k) for k in fields) for item in entries)
    invalid = any(
        not all(item.get(k) for k in ("reason", "task", "remove_when")) for item in entries
    )
    for identity in sorted((wanted - approved) + (approved - wanted)):
        print(f"BYPASS_FAIL {identity[0]}:{identity[1]} rule={identity[2]}")
    print(f"Bypass registrations: {len(entries)}; detected: {len(found)}")
    return int(invalid or wanted != approved)


def check_provisional() -> int:
    """Compare annotation locations, mapping leaves and registration rows one to one."""
    from ci.checks import repository_files

    mapping = Path("docs/dev/01_extension_mapping.md").read_text()
    rows = [
        [c.strip() for c in line.strip("|").split("|")]
        for line in mapping.splitlines()
        if line.startswith("| B7-")
    ]
    if not rows or any(len(row) < 4 for row in rows):
        raise ValueError("Invalid mapping table")
    leaves = {row[0] for row in rows if "父键" not in row[3]}
    found: list[tuple[str, str]] = []
    for path in repository_files():
        if path.suffix in {".py", ".pyi"} and path.parts[0] in {
            "framework",
            "agents",
            "conformance",
            "ci",
        }:
            for i, line in enumerate(path.read_text().splitlines(), 1):
                for match in re.finditer(r"PROVISIONAL\(([^)]*)\)", line):
                    found.append((f"{path}:{i}", match.group(1)))
    registered: list[tuple[str, str]] = []
    register_text = Path("docs/dev/provisional.md").read_text()
    if "| 位置 | 对应映射表子键 | 预计通过日期 |" not in register_text:
        raise ValueError("Missing provisional table header")
    for line in register_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if cells[0] == "位置" or all(re.fullmatch(r"[-: ]+", c) for c in cells):
            continue
        if len(cells) != 3 or not all(cells):
            raise ValueError("Invalid provisional row")
        registered.append((cells[0], cells[1]))
    bad_keys = {key for _, key in found + registered} - leaves
    mismatch = Counter(found) != Counter(registered)
    duplicate = any(count > 1 for count in Counter(found).values())
    print(f"Provisional annotations: {len(found)}; keys: {sorted({k for _, k in found})}")
    for key in sorted(bad_keys):
        print(f"PROVISIONAL_FAIL unknown_or_parent={key}")
    if mismatch or duplicate:
        print("PROVISIONAL_FAIL annotation/register locations differ or duplicate")
    return int(bool(bad_keys) or mismatch or duplicate)
