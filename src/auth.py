"""Keycard Authentication Provider for Linear MCP Server.

This module creates the AuthProvider singleton that is used by all tool modules.
The auth_provider must be initialized before tools are registered.
"""

import os
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from keycardai.mcp.integrations.fastmcp import AuthProvider, ClientSecret

if TYPE_CHECKING:
    from keycardai.mcp.integrations.fastmcp import AccessContext

# Load environment variables
load_dotenv()

# Linear API base URL for grant decorator
LINEAR_API_URL = "https://api.linear.app"

# Create Keycard authentication provider
# This is a module-level singleton used by all tools
auth_provider = AuthProvider(
    zone_id=os.getenv("KEYCARD_ZONE_ID"),
    mcp_server_name="Linear MCP Server",
    mcp_server_url=os.getenv("MCP_SERVER_URL", "http://localhost:8000/"),
    application_credential=ClientSecret((
        os.getenv("KEYCARD_CLIENT_ID"),
        os.getenv("KEYCARD_CLIENT_SECRET")
    ))
)


def get_linear_token(access_ctx: "AccessContext") -> str:
    """Extract Linear access token from Keycard AccessContext.

    Args:
        access_ctx: The AccessContext from ctx.get_state("keycardai")

    Returns:
        The Linear API access token.

    Raises:
        ValueError: If token cannot be extracted or auth errors occurred.
    """
    if access_ctx is None:
        raise ValueError("No authentication context - Keycard auth may not be configured")

    if access_ctx.has_errors():
        errors = access_ctx.get_errors()
        raise ValueError(f"Authentication errors: {errors}")

    return access_ctx.access(LINEAR_API_URL).access_token
