"""Exercise D23 repository cases, constructing negative material only at runtime."""

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ci.d23 import check_file, decoded_marker, digest, php_package, python_fragments


def marker() -> str:
    """Assemble a signal without storing a negative program in the repository."""
    return "<" + "?" + "php"


@pytest.mark.unit
@pytest.mark.parametrize("literal", ["repr", "bytes", "adjacent", "comment", "escaped"])
def test_registered_signatures(literal: str) -> None:
    m = marker()
    forms = {
        "repr": f"x = {m!r}",
        "bytes": f"x = {m.encode()!r}",
        "adjacent": f"x = {m[:2]!r} {m[2:]!r}",
        "comment": f"#  {m}  ",
        "escaped": "x = '\\x3c?php'",
    }
    assert python_fragments(forms[literal].encode())


@pytest.mark.unit
@pytest.mark.parametrize(
    "form", ["program", "adjacent", "fstring", "plain_fstring", "comment", "syntax"]
)
def test_denied_fragments(form: str, tmp_path: Path) -> None:
    m = marker()
    program = m + " echo 1;"
    forms = {
        "program": f"x = {program!r}",
        "adjacent": f"x = {m!r} ' echo 1;'",
        "fstring": f"x = f'{m} {{1}}'",
        "plain_fstring": f"x = f'{m}'",
        "comment": f"# {program}",
        "syntax": program,
    }
    data = forms[form].encode()
    path = tmp_path / "fake.py"
    path.write_bytes(data)
    assert not python_fragments(data)
    assert check_file(path)


@pytest.mark.unit
def test_latin1_and_unicode_comment() -> None:
    assert python_fragments(("é = 1\n# " + marker()).encode())
    assert not python_fragments(("x = b'" + marker() + "\\xff'").encode())
    assert not python_fragments(b"x = '\xff'")
    assert not decoded_marker(b"x = (")
    assert not decoded_marker(b"x = 1")
    assert decoded_marker(("x = " + repr(marker().encode())).encode())


@pytest.mark.unit
@pytest.mark.parametrize(
    "name",
    [
        "x.php",
        "x.php3",
        "x.php8",
        "x.phtml",
        "x.phar",
        "x.phps",
        "composer.json",
        "composer.lock",
        "php",
        "php-cgi",
        "php-fpm",
        "libphp.so",
        "mod_php.so",
    ],
)
def test_nontext_signals(name: str, tmp_path: Path) -> None:
    path = tmp_path / name
    path.write_bytes(b"safe")
    assert check_file(path, scanner_digest=digest(b"safe"))


@pytest.mark.unit
def test_classification_and_digest(tmp_path: Path) -> None:
    path = tmp_path / "document.txt"
    data = marker().encode()
    path.write_bytes(data)
    assert check_file(path)
    assert not check_file(path, pure_data_digest=digest(data))
    assert check_file(path, pure_data_digest="wrong")
    assert check_file(path, pure_data_digest=digest(data), executable_input=True)
    path.chmod(0o755)
    assert check_file(path, pure_data_digest=digest(data))
    assert not check_file(path, scanner_digest=digest(data))
    assert check_file(path, scanner_digest="wrong")
    path.write_text("#!/usr/bin/env php\n")
    assert "php_shebang" in check_file(path, scanner_digest=digest(path.read_bytes()))
    link = tmp_path / "link"
    link.symlink_to(path)
    assert check_file(link) == ["symlink_requires_review"]
    assert check_file(tmp_path) == ["unreadable_or_nonregular"]
    assert check_file(tmp_path / "missing") == ["unreadable_or_nonregular"]


@pytest.mark.unit
def test_unregistered_language_and_no_whole_python_exemption(tmp_path: Path) -> None:
    for suffix in (".js", ".sh", ".unknown"):
        path = tmp_path / ("sample" + suffix)
        path.write_text("x = " + repr(marker()))
        assert check_file(path)
    path = tmp_path / "sample.py"
    path.write_text("x = " + repr(marker() + " echo 1;"))
    assert check_file(path, pure_data_digest=digest(path.read_bytes()))
    assert not check_file(path, scanner_digest=digest(path.read_bytes()))
    path.write_text("x = " + repr(marker()))
    path.chmod(0o755)
    assert not check_file(path)


@pytest.mark.property
@given(st.sampled_from(["php", "php8.3", "php-cli", "libphp8", "mod_php"]))
def test_package_families(name: str) -> None:
    assert php_package(name)
    assert not php_package("graph" + name)
