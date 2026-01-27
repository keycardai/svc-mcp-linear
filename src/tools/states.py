"""Workflow State Tools.

Tools for reading Linear workflow states.
"""

from __future__ import annotations

from fastmcp import FastMCP

from ..client import LinearClientError, execute_query

# GraphQL Queries
TEAM_STATES_QUERY = """
query($teamId: String!) {
    team(id: $teamId) {
        id
        name
        states {
            nodes {
                id
                name
                type
            }
        }
    }
}
"""

ALL_TEAMS_STATES_QUERY = """
query {
    teams {
        nodes {
            id
            name
            states {
                nodes {
                    id
                    name
                    type
                }
            }
        }
    }
}
"""


def register_state_tools(mcp: FastMCP) -> None:
    """Register workflow state tools with the MCP server."""

    @mcp.tool(
        name="states",
        description="Get available workflow states for a Linear team. If team_id is not provided, returns states for all teams. Use this to get state_id values for update_status tool. State types: backlog, unstarted, started, completed, canceled.",
    )
    async def states(team_id: str | None = None) -> dict:
        """Get workflow states for a team or all teams.

        Args:
            team_id: Optional team ID. If not provided, returns states for all teams.
        """
        try:
            if team_id:
                data = await execute_query(TEAM_STATES_QUERY, {"teamId": team_id})
                team_data = data.get("team")
                if team_data is None:
                    return {
                        "success": False,
                        "error": f"Team {team_id} not found",
                        "isError": True,
                    }
                return {
                    "success": True,
                    "team": {
                        "id": team_data["id"],
                        "name": team_data["name"],
                    },
                    "states": team_data.get("states", {}).get("nodes", []),
                }
            else:
                data = await execute_query(ALL_TEAMS_STATES_QUERY)
                teams = data.get("teams", {}).get("nodes", [])
                return {
                    "success": True,
                    "teams": [
                        {
                            "id": team["id"],
                            "name": team["name"],
                            "states": team.get("states", {}).get("nodes", []),
                        }
                        for team in teams
                    ],
                }
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}
