"""Milestone Tools.

Tools for Linear project milestone CRUD: list, get, create, update, delete.
"""

from fastmcp import FastMCP, Context

from ..auth import auth_provider, get_linear_token, LINEAR_API_URL
from ..client import LinearClientError, execute_query

# GraphQL Queries
LIST_MILESTONES_QUERY = """
query($projectId: String!, $first: Int!) {
    projectMilestones(filter: { project: { id: { eq: $projectId } } }, first: $first) {
        nodes {
            id
            name
            description
            targetDate
            sortOrder
            archivedAt
            createdAt
            updatedAt
            project { id name }
        }
    }
}
"""

GET_MILESTONE_QUERY = """
query($id: String!) {
    projectMilestone(id: $id) {
        id
        name
        description
        targetDate
        sortOrder
        archivedAt
        createdAt
        updatedAt
        project { id name }
    }
}
"""

# GraphQL Mutations
CREATE_MILESTONE_MUTATION = """
mutation($projectId: String!, $name: String!, $description: String, $targetDate: String) {
    projectMilestoneCreate(input: {
        projectId: $projectId
        name: $name
        description: $description
        targetDate: $targetDate
    }) {
        success
        projectMilestone {
            id
            name
            description
            targetDate
            sortOrder
            project { id name }
        }
    }
}
"""

UPDATE_MILESTONE_MUTATION = """
mutation($id: String!, $name: String, $description: String, $targetDate: String) {
    projectMilestoneUpdate(id: $id, input: {
        name: $name
        description: $description
        targetDate: $targetDate
    }) {
        success
        projectMilestone {
            id
            name
            description
            targetDate
            sortOrder
            project { id name }
        }
    }
}
"""

DELETE_MILESTONE_MUTATION = """
mutation($id: String!) {
    projectMilestoneDelete(id: $id) {
        success
    }
}
"""


def register_milestone_tools(mcp: FastMCP) -> None:
    """Register milestone CRUD tools with the MCP server."""

    @mcp.tool(
        name="list_milestones",
        description="List milestones for a Linear project. Requires project_id (UUID from list_projects). Returns milestones with id, name, description, targetDate, and sortOrder.",
    )
    @auth_provider.grant(LINEAR_API_URL)
    async def list_milestones(ctx: Context, project_id: str, limit: int = 50) -> dict:
        """List milestones for a project.

        Args:
            project_id: The project's internal UUID (get from list_projects).
            limit: Number of milestones to return (default 50).
        """
        try:
            access_ctx = await ctx.get_state("keycardai")
            token = get_linear_token(access_ctx)

            data = await execute_query(
                LIST_MILESTONES_QUERY,
                {"projectId": project_id, "first": limit},
                token=token,
            )
            milestones = data.get("projectMilestones", {}).get("nodes", [])
            return {"success": True, "milestones": milestones, "count": len(milestones)}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="get_milestone",
        description="Get details of a specific Linear project milestone by its UUID. Returns full milestone details including name, description, targetDate, and associated project.",
    )
    @auth_provider.grant(LINEAR_API_URL)
    async def get_milestone(ctx: Context, milestone_id: str) -> dict:
        """Get a specific milestone by ID.

        Args:
            milestone_id: The milestone's internal UUID.
        """
        try:
            access_ctx = await ctx.get_state("keycardai")
            token = get_linear_token(access_ctx)

            data = await execute_query(
                GET_MILESTONE_QUERY, {"id": milestone_id}, token=token
            )
            milestone = data.get("projectMilestone")
            if milestone is None:
                return {
                    "success": False,
                    "error": f"Milestone {milestone_id} not found",
                    "isError": True,
                }
            return {"success": True, "milestone": milestone}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="create_milestone",
        description="Create a new milestone for a Linear project. Requires project_id and name. Optional: description (markdown supported), target_date (ISO date string, e.g. '2025-12-31').",
    )
    @auth_provider.grant(LINEAR_API_URL)
    async def create_milestone(
        ctx: Context,
        project_id: str,
        name: str,
        description: str | None = None,
        target_date: str | None = None,
    ) -> dict:
        """Create a new project milestone.

        Args:
            project_id: The project's internal UUID (get from list_projects).
            name: Milestone name (required).
            description: Optional description (markdown supported).
            target_date: Optional target completion date (ISO format, e.g. '2025-12-31').
        """
        try:
            access_ctx = await ctx.get_state("keycardai")
            token = get_linear_token(access_ctx)

            variables = {
                "projectId": project_id,
                "name": name,
                "description": description,
                "targetDate": target_date,
            }
            data = await execute_query(CREATE_MILESTONE_MUTATION, variables, token=token)
            result = data.get("projectMilestoneCreate", {})
            if result.get("success"):
                return {"success": True, "milestone": result.get("projectMilestone")}
            return {"success": False, "error": "Milestone creation failed", "isError": True}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="update_milestone",
        description="Update an existing Linear project milestone. Requires milestone_id (UUID). Optional: name, description (markdown supported), target_date (ISO date string, e.g. '2025-12-31').",
    )
    @auth_provider.grant(LINEAR_API_URL)
    async def update_milestone(
        ctx: Context,
        milestone_id: str,
        name: str | None = None,
        description: str | None = None,
        target_date: str | None = None,
    ) -> dict:
        """Update an existing project milestone.

        Args:
            milestone_id: The milestone's internal UUID.
            name: Optional new name.
            description: Optional new description (markdown supported).
            target_date: Optional new target date (ISO format, e.g. '2025-12-31').
        """
        try:
            access_ctx = await ctx.get_state("keycardai")
            token = get_linear_token(access_ctx)

            variables = {
                "id": milestone_id,
                "name": name,
                "description": description,
                "targetDate": target_date,
            }
            data = await execute_query(UPDATE_MILESTONE_MUTATION, variables, token=token)
            result = data.get("projectMilestoneUpdate", {})
            if result.get("success"):
                return {"success": True, "milestone": result.get("projectMilestone")}
            return {"success": False, "error": "Milestone update failed", "isError": True}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="delete_milestone",
        description="Delete a Linear project milestone by its UUID.",
    )
    @auth_provider.grant(LINEAR_API_URL)
    async def delete_milestone(ctx: Context, milestone_id: str) -> dict:
        """Delete a project milestone.

        Args:
            milestone_id: The milestone's internal UUID.
        """
        try:
            access_ctx = await ctx.get_state("keycardai")
            token = get_linear_token(access_ctx)

            data = await execute_query(
                DELETE_MILESTONE_MUTATION, {"id": milestone_id}, token=token
            )
            result = data.get("projectMilestoneDelete", {})
            if result.get("success"):
                return {"success": True, "deleted": True, "milestone_id": milestone_id}
            return {"success": False, "error": "Milestone deletion failed", "isError": True}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}
