"""Inspect actual virtualenv files beyond installed distribution manifests."""

import re
from pathlib import Path

from ci.d23 import check_file


def unlisted_files(prefix: Path, owned: set[Path]) -> list[str]:
    """Reject runtime bytecode and inspect unowned files without following outside links."""
    prefix = prefix.resolve(strict=True)
    cfg = dict(
        line.split("=", 1)
        for line in (prefix / "pyvenv.cfg").read_text().splitlines()
        if "=" in line
    )
    home = Path(next(value.strip() for key, value in cfg.items() if key.strip() == "home"))
    failures: list[str] = []
    for path in sorted(prefix.rglob("*")):
        relative = path.relative_to(prefix)
        if path.is_symlink():
            target = path.resolve(strict=True)
            internal = target.is_relative_to(prefix)
            interpreter = (
                path.parent == prefix / "bin"
                and re.fullmatch(r"python(?:\d+(?:\.\d+)?)?", path.name) is not None
                and target.is_file()
                and target.parent == home.resolve(strict=True)
                and re.fullmatch(r"python\d+\.\d+", target.name) is not None
            )
            if not (internal or interpreter):
                failures.append(f"installed: {relative}: external_symlink")
            continue
        if path.is_dir() or path.resolve() in owned:
            continue
        if path.suffix == ".pyc":
            failures.append(f"installed: {relative}: runtime_pyc_unlisted")
        else:
            failures.extend(f"installed: {relative}: {reason}" for reason in check_file(path))
    return failures
