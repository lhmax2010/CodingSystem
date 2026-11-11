"""Enforce the development machine's offline and intranet test policies."""

import os
from collections.abc import Iterator
from typing import Any

import pytest
from hypothesis import settings

settings.register_profile("gate", max_examples=40, derandomize=True, deadline=None)
settings.load_profile("gate")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Keep intranet cases visible as explicitly authorized skips."""
    for item in items:
        if (
            os.environ.get("CODINGSYSTEM_INTRANET") != "1"
            and item.get_closest_marker("intranet") is not None
        ):
            item.add_marker(pytest.mark.skip(reason="intranet: disabled on development machine"))


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Turn non-intranet skips and expected failures (including XPASS) into failures."""
    if "intranet" not in report.keywords and (report.skipped or hasattr(report, "wasxfail")):
        raise pytest.UsageError("Non-intranet skip/xfail is forbidden: " + report.nodeid)


def pytest_collectreport(report: pytest.CollectReport) -> None:
    """Prevent module-level skips from silently removing tests before marking."""
    if report.skipped:
        raise pytest.UsageError("Collection skip is forbidden: " + report.nodeid)


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> Iterator[None]:
    """Block socket network access, including DNS and datagrams."""

    if (
        os.environ.get("CODINGSYSTEM_INTRANET") == "1"
        and request.node.get_closest_marker("intranet") is not None
    ):
        yield
        return

    def deny(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Network access is disabled in tests")

    for name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "create_connection"):
        monkeypatch.setattr(f"socket.{name}", deny)
    for name in ("connect", "connect_ex", "sendto", "sendmsg"):
        monkeypatch.setattr(f"socket.socket.{name}", deny)
    yield
