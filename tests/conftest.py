"""Enforce the development machine's offline and intranet test policies."""

from collections.abc import Iterator
from typing import Any

import pytest
from hypothesis import settings

settings.register_profile("gate", max_examples=40, derandomize=True, deadline=None)
settings.load_profile("gate")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Keep intranet cases visible as explicitly authorized skips."""
    for item in items:
        if item.get_closest_marker("intranet") is not None:
            item.add_marker(pytest.mark.skip(reason="intranet: disabled on development machine"))


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Block socket network access, including DNS and datagrams."""

    def deny(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Network access is disabled in tests")

    for name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "create_connection"):
        monkeypatch.setattr(f"socket.{name}", deny)
    for name in ("connect", "connect_ex", "sendto", "sendmsg"):
        monkeypatch.setattr(f"socket.socket.{name}", deny)
    yield
