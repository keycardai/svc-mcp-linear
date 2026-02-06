"""FastMCP Server Definition for Linear MCP.

This module creates the FastMCP instance with Keycard authentication
and registers all tools. Uses the Keycard SDK for OAuth token management.
"""

import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from .auth import auth_provider
from .tools.issues import register_issue_tools
from .tools.mutations import register_mutation_tools
from .tools.states import register_state_tools

# Load environment variables
load_dotenv()


def create_mcp_server() -> FastMCP:
    """Create and configure the FastMCP server instance.

    Returns:
        Configured FastMCP instance with Keycard auth and all tools registered.
    """
    # Get RemoteAuthProvider from Keycard AuthProvider
    auth = auth_provider.get_remote_auth_provider()

    mcp = FastMCP(
        "Linear MCP Server",
        auth=auth,
        instructions="""Linear MCP Server for managing issues and workflow states.

This server provides tools to:
- View and search issues assigned to you
- Create new issues
- Update issue details and workflow status
- View available workflow states for teams
- Post and view project status updates

Authentication is handled via Keycard OAuth.
""",
    )

    # Register tools from separate modules
    register_issue_tools(mcp)
    register_mutation_tools(mcp)
    register_state_tools(mcp)

    return mcp


# Create the server instance
mcp = create_mcp_server()


# For local development and Render deployment
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Linear MCP Server on http://0.0.0.0:{port}/mcp")

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port
    )
