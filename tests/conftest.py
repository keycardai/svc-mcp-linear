"""Pytest configuration for svc-mcp-linear tests."""

import sys
from unittest.mock import MagicMock

import pytest

# Stub the keycardai SDK before any src module is imported. auth.py creates
# AuthProvider at module level which makes a network call — this prevents that.
_provider_instance = MagicMock()
_provider_instance.grant.return_value = lambda f: f  # passthrough decorator

_sdk_stub = MagicMock()
_sdk_stub.AuthProvider.return_value = _provider_instance
_sdk_stub.ClientSecret.return_value = MagicMock()

for _mod in [
    "keycardai",
    "keycardai.mcp",
    "keycardai.mcp.integrations",
    "keycardai.mcp.integrations.fastmcp",
    "keycardai.mcp.server",
    "keycardai.mcp.server.auth",
    "keycardai.mcp.server.auth.application_credentials",
    "keycardai.mcp.server.exceptions",
    "keycardai.oauth",
    "keycardai.oauth.exceptions",
]:
    sys.modules.setdefault(_mod, _sdk_stub)


@pytest.fixture(autouse=True)
def reset_fastmcp():
    """Reset any FastMCP state between tests."""
    yield
