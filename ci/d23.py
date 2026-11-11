"""Check repository files and installed dependency files against the D23 policy."""

from __future__ import annotations

import ast
import codecs
import hashlib
import io
import re
import tokenize
from pathlib import Path

MARKER = "<?php"
SIGNALS = (MARKER, "composer.lock", "composer.json", ".phar")
POLICY_VERSION = "task-004-d23-v2"
MARKER_RE = re.compile(re.escape(MARKER.encode()), re.IGNORECASE)


def digest(data: bytes) -> str:
    """Return the content identity used in reviewed policy entries."""
    return hashlib.sha256(data).hexdigest()


def php_package(name: str) -> bool:
    """Recognize PHP runtime package families without substring matching prose."""
    return re.match(r"^(?:php|libphp|mod[-_]php)(?:$|[-_.0-9])", name.lower()) is not None


def python_fragments(data: bytes) -> bool:
    """Approve only registered constant values or normalized tokenizer comments."""
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
        if codecs.lookup(encoding).name not in {"utf-8", "utf-8-sig"}:
            return False
        source = data.decode(encoding)
        tree = ast.parse(source)
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (SyntaxError, UnicodeError, tokenize.TokenError):
        return False
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line.encode("utf-8")))
    raw = data.removeprefix(codecs.BOM_UTF8)
    approved: list[tuple[int, int]] = []
    interpolated = {
        id(child)
        for node in ast.walk(tree)
        if isinstance(node, ast.JoinedStr)
        for child in ast.walk(node)
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, (str, bytes)):
            continue
        value = node.value.decode("latin-1") if isinstance(node.value, bytes) else node.value
        if MARKER.lower() not in value.lower():
            continue
        if id(node) in interpolated or value not in SIGNALS:
            return False
        if node.end_lineno is None or node.end_col_offset is None:
            return False
        approved.append(
            (
                offsets[node.lineno - 1] + node.col_offset,
                offsets[node.end_lineno - 1] + node.end_col_offset,
            )
        )
    for token in tokens:
        if token.type != tokenize.COMMENT or MARKER.lower() not in token.string.lower():
            continue
        if token.string.removeprefix("#").strip() not in SIGNALS:
            return False
        row, col = token.start
        start = offsets[row - 1] + len(lines[row - 1][:col].encode("utf-8"))
        approved.append((start, start + len(token.string.encode("utf-8"))))
    return all(
        any(start <= match.start() and match.end() <= end for start, end in approved)
        for match in MARKER_RE.finditer(raw)
    )


def check_file(
    path: Path,
    *,
    pure_data_digest: str | None = None,
    scanner_digest: str | None = None,
    executable_input: bool = False,
) -> list[str]:
    """Return all applicable reasons; classification exempts only the text signal."""
    reasons: list[str] = []
    if path.is_symlink():
        return ["symlink_requires_review"]
    if not path.is_file():
        return ["unreadable_or_nonregular"]
    data = path.read_bytes()
    name = path.name.lower()
    if re.search(r"\.(?:php[3-8]?|phar|phtml|phps)$", name):
        reasons.append("php_extension")
    if name in {"composer.json", "composer.lock"}:
        reasons.append("composer_manifest")
    if re.fullmatch(r"php(?:-cgi|-fpm)?(?:[0-9.]*)?(?:\.exe)?", name):
        reasons.append("php_executable")
    if name.startswith(("libphp", "mod_php")):
        reasons.append("php_library")
    first = data.split(b"\n", 1)[0]
    if first.startswith(b"#!") and re.search(rb"\bphp(?:[0-9.]*)?\b", first.lower()):
        reasons.append("php_shebang")
    if executable_input and pure_data_digest is not None:
        reasons.append("data_used_as_executable_input")
    if scanner_digest is not None and digest(data) != scanner_digest:
        reasons.append("scanner_digest_mismatch")
    if pure_data_digest is not None and (
        digest(data) != pure_data_digest or path.stat().st_mode & 0o111
    ):
        reasons.append("data_classification_invalid")
    marker_present = MARKER_RE.search(data) is not None
    if path.suffix == ".py":
        # Parsing is also necessary for escaped or implicitly concatenated constants.
        fragments_ok = python_fragments(data)
        if not fragments_ok and (marker_present or decoded_marker(data)):
            reasons.append("unapproved_python_fragment")
    elif marker_present:
        allowed = scanner_digest == digest(data) or (
            pure_data_digest == digest(data)
            and not path.stat().st_mode & 0o111
            and not executable_input
            and not first.startswith(b"#!")
        )
        if not allowed:
            reasons.append("unclassified_text_signal")
    # Python sources always require fragment classification, including scanner sources.
    return reasons


def decoded_marker(data: bytes) -> bool:
    """Detect markers represented by escapes and adjacent Python literals."""
    try:
        tree = ast.parse(data)
    except (SyntaxError, UnicodeError):
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, bytes):
                value = value.decode("latin-1")
            if isinstance(value, str) and MARKER.lower() in value.lower():
                return True
    return False
