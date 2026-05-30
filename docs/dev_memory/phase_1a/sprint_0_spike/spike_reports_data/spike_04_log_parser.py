#!/usr/bin/env python3
"""Spike-only generic C/C++ build log parser for S0-04.

Rules are intentionally generic GCC/Clang/LLD patterns. This is not product
code and should not be tuned to a specific pkgmgr-info log after validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


PATTERNS = [
    (
        "cannot_find_header",
        re.compile(
            r"(?:fatal error: ['<](?P<header1>[^'>]+)[>'] file not found|"
            r"fatal error: (?P<header2>[^:]+): No such file or directory)"
        ),
    ),
    (
        "undefined_reference",
        re.compile(r"undefined reference to [`'](?P<symbol>[^`']+)[`']"),
    ),
    (
        "undefined_symbol",
        re.compile(r"(?:ld(?:\.lld)?: error: )?undefined symbol: (?P<symbol>\S+)"),
    ),
    (
        "type_mismatch",
        re.compile(
            r"(?:cannot initialize (?:a )?parameter of type|"
            r"cannot convert|invalid conversion|"
            r"incompatible (?:pointer|integer)|"
            r"no matching function for call to|"
            r"no viable conversion)"
        ),
    ),
    (
        "template_error",
        re.compile(
            r"(?:template argument|template parameter|"
            r"static assertion failed.*(?:template|allocator|value_type)|"
            r"no type named .* in .*std::|"
            r"required from .*instantiation|"
            r"in instantiation of)"
        ),
    ),
]

ERROR_LINE = re.compile(r"(?:\berror:|undefined reference|undefined symbol)")
TIME_PREFIX = re.compile(r"^\[\s*\d+s\]\s*")
MAX_EXCERPT_CHARS = 3000


@dataclass(frozen=True)
class ParsedError:
    index: int
    error_type: str
    line_no: int
    message: str
    symbol: str | None
    excerpt: str


def normalize_line(line: str) -> str:
    return TIME_PREFIX.sub("", line.rstrip("\n"))


def bounded_excerpt(lines: list[str], line_index: int) -> str:
    start = max(0, line_index - 2)
    end = min(len(lines), line_index + 4)
    excerpt = "\n".join(normalize_line(line) for line in lines[start:end])
    if len(excerpt) <= MAX_EXCERPT_CHARS:
        return excerpt
    return excerpt[:MAX_EXCERPT_CHARS]


def parse_log(log_path: Path) -> dict:
    raw = log_path.read_text(errors="replace")
    lines = raw.splitlines()
    errors: list[ParsedError] = []

    for i, line in enumerate(lines):
        normalized = normalize_line(line)
        if not ERROR_LINE.search(normalized):
            continue
        for error_type, pattern in PATTERNS:
            match = pattern.search(normalized)
            if not match:
                continue
            header = match.groupdict().get("header1") or match.groupdict().get("header2")
            symbol = match.groupdict().get("symbol") or header
            errors.append(
                ParsedError(
                    index=len(errors) + 1,
                    error_type=error_type,
                    line_no=i + 1,
                    message=normalized,
                    symbol=symbol,
                    excerpt=bounded_excerpt(lines, i),
                )
            )
            break

    counts: dict[str, int] = {}
    for error in errors:
        counts[error.error_type] = counts.get(error.error_type, 0) + 1

    return {
        "parser": "spike_04_generic_v1",
        "log_path": str(log_path),
        "log_sha256": hashlib.sha256(raw.encode(errors="replace")).hexdigest(),
        "total_lines": len(lines),
        "parsed_error_count": len(errors),
        "counts_by_type": dict(sorted(counts.items())),
        "primary_candidate_policy": "first_parsed_error_only_no_cascade_analysis",
        "primary_candidate": asdict(errors[0]) if errors else None,
        "errors": [asdict(error) for error in errors],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = parse_log(args.log_path)
    encoded = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
    if args.output:
        args.output.write_text(encoded + "\n")
    else:
        print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
