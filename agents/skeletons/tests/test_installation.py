"""Verify independently installed distribution names and public imports."""

from importlib import import_module, metadata

import pytest


@pytest.mark.unit
def test_installed_packages() -> None:
    assert metadata.version("codingsystem-framework") == "0.0.1"
    assert metadata.version("codingsystem-agent-skeletons") == "0.0.1"
    assert import_module("codingsystem.sdk").__doc__
    assert import_module("codingsystem.contracts").__doc__
    assert import_module("codingsystem_agent_skeletons").__doc__
    assert "codingsystem-framework==0.0.1" in (
        metadata.requires("codingsystem-agent-skeletons") or []
    )
