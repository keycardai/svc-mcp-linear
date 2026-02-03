"""FastMCP Server Definition for Linear MCP.

This module creates the FastMCP instance and registers all tools.
The server receives pre-exchanged tokens from an MCP Gateway.

No Keycard SDK - the gateway handles all OAuth/token exchange.
Token is read from the Authorization header (Bearer token).
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from .tools.issues import register_issue_tools
from .tools.mutations import register_mutation_tools
from .tools.states import register_state_tools

# Load environment variables
load_dotenv()


def create_mcp_server() -> FastMCP:
    """Create and configure the FastMCP server instance.

    Returns:
        Configured FastMCP instance with all tools registered.
    """
    mcp = FastMCP(
        "Linear MCP Server",
        instructions="""Linear MCP Server for managing issues and workflow states.

This server provides tools to:
- View and search issues assigned to you
- Create new issues
- Update issue details and workflow status
- View available workflow states for teams
- Post and view project status updates

Authentication: The Linear API token should be provided in the Authorization header as a Bearer token.
""",
    )

    # Register tools from separate modules
    register_issue_tools(mcp)
    register_mutation_tools(mcp)
    register_state_tools(mcp)

    return mcp


# Create the server instance for use by Cloudflare Workers or other entry points
mcp = create_mcp_server()


# For local development and Render deployment
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting Linear MCP Server on http://0.0.0.0:{port}/mcp")

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port
    )
