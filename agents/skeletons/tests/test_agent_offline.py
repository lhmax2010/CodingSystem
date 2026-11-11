"""Sentinel for the repository-wide test policy in an independently packaged Agent."""

import socket

import pytest


@pytest.mark.unit
def test_agent_inherits_offline(request: pytest.FixtureRequest) -> None:
    assert "offline" in request.fixturenames
    with pytest.raises(RuntimeError, match="Network access"):
        socket.getaddrinfo("unused", 1)


@pytest.mark.intranet
def test_agent_intranet_sentinel() -> None:
    assert True
