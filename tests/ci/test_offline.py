"""Confirm that the default network policy fails closed."""

import socket

import pytest


@pytest.mark.unit
def test_network_denied() -> None:
    with pytest.raises(RuntimeError, match="disabled"):
        socket.getaddrinfo("example.invalid", 443)
    with socket.socket() as sock, pytest.raises(RuntimeError, match="disabled"):
        sock.connect(("example.invalid", 443))


@pytest.mark.intranet
def test_intranet_collection_sentinel() -> None:
    raise AssertionError("Must not execute on the development machine")
