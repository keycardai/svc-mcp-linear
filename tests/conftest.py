"""Pytest configuration for svc-mcp-linear tests."""

import pytest


@pytest.fixture(autouse=True)
def reset_fastmcp():
    """Reset any FastMCP state between tests."""
    yield
