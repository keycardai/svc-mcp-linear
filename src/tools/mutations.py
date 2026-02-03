"""Mutation Tools.

Tools for modifying Linear: create_issue, update_issue, update_status, create_project.
"""

from __future__ import annotations

from fastmcp import FastMCP

from ..client import LinearClientError, execute_query

# GraphQL Mutations
CREATE_ISSUE_MUTATION = """
mutation($teamId: String!, $title: String!, $description: String, $priority: Int, $stateId: String, $assigneeId: String, $projectId: String) {
    issueCreate(input: {
        teamId: $teamId
        title: $title
        description: $description
        priority: $priority
        stateId: $stateId
        assigneeId: $assigneeId
        projectId: $projectId
    }) {
        success
        issue {
            id
            identifier
            title
            url
            state { name }
            assignee { name }
            project { id name }
        }
    }
}
"""

UPDATE_ISSUE_MUTATION = """
mutation($id: String!, $title: String, $description: String, $priority: Int, $stateId: String, $assigneeId: String) {
    issueUpdate(id: $id, input: {
        title: $title
        description: $description
        priority: $priority
        stateId: $stateId
        assigneeId: $assigneeId
    }) {
        success
        issue {
            id
            identifier
            title
            url
            state { name }
            assignee { name }
        }
    }
}
"""

UPDATE_STATUS_MUTATION = """
mutation($id: String!, $stateId: String!) {
    issueUpdate(id: $id, input: { stateId: $stateId }) {
        success
        issue {
            id
            identifier
            state { name }
        }
    }
}
"""

CREATE_PROJECT_MUTATION = """
mutation($name: String!, $teamIds: [String!]!, $description: String, $state: String) {
    projectCreate(input: {
        name: $name
        teamIds: $teamIds
        description: $description
        state: $state
    }) {
        success
        project {
            id
            name
            slugId
            url
        }
    }
}
"""

CREATE_PROJECT_UPDATE_MUTATION = """
mutation($projectId: String!, $body: String!, $health: ProjectUpdateHealthType) {
    projectUpdateCreate(input: {
        projectId: $projectId
        body: $body
        health: $health
    }) {
        success
        projectUpdate {
            id
            body
            health
            createdAt
            user { name email }
            project { id name }
        }
    }
}
"""


def register_mutation_tools(mcp: FastMCP) -> None:
    """Register issue mutation tools with the MCP server."""

    @mcp.tool(
        name="create_issue",
        description="Create a new Linear issue. Requires team_id and title. Optional: description, priority (0=none, 1=urgent, 2=high, 3=medium, 4=low), state_id, assignee_id, project_id.",
    )
    async def create_issue(
        team_id: str,
        title: str,
        description: str | None = None,
        priority: int | None = None,
        state_id: str | None = None,
        assignee_id: str | None = None,
        project_id: str | None = None,
    ) -> dict:
        """Create a new Linear issue.

        Args:
            team_id: The team ID to create the issue in (required).
            title: Issue title (required).
            description: Optional issue description (markdown supported).
            priority: Optional priority (0=none, 1=urgent, 2=high, 3=medium, 4=low).
            state_id: Optional workflow state ID (get from states tool).
            assignee_id: Optional assignee user ID.
            project_id: Optional project ID to assign issue to (get from list_projects tool).
        """
        try:
            variables = {
                "teamId": team_id,
                "title": title,
                "description": description,
                "priority": priority,
                "stateId": state_id,
                "assigneeId": assignee_id,
                "projectId": project_id,
            }
            data = await execute_query(CREATE_ISSUE_MUTATION, variables)
            result = data.get("issueCreate", {})
            if result.get("success"):
                return {"success": True, "issue": result.get("issue")}
            return {"success": False, "error": "Issue creation failed", "isError": True}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="update_issue",
        description="Update an existing Linear issue. Requires issue_id (internal UUID from issue query). Optional: title, description, priority, state_id, assignee_id.",
    )
    async def update_issue(
        issue_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: int | None = None,
        state_id: str | None = None,
        assignee_id: str | None = None,
    ) -> dict:
        """Update an existing Linear issue.

        Args:
            issue_id: The issue's internal UUID (get from issue query, not the identifier).
            title: Optional new title.
            description: Optional new description (markdown supported).
            priority: Optional new priority (0=none, 1=urgent, 2=high, 3=medium, 4=low).
            state_id: Optional new workflow state ID.
            assignee_id: Optional new assignee user ID.
        """
        try:
            variables = {
                "id": issue_id,
                "title": title,
                "description": description,
                "priority": priority,
                "stateId": state_id,
                "assigneeId": assignee_id,
            }
            data = await execute_query(UPDATE_ISSUE_MUTATION, variables)
            result = data.get("issueUpdate", {})
            if result.get("success"):
                return {"success": True, "issue": result.get("issue")}
            return {"success": False, "error": "Issue update failed", "isError": True}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="update_status",
        description="Update the workflow status of a Linear issue. Requires issue_id and state_id (get state_id from states tool).",
    )
    async def update_status(issue_id: str, state_id: str) -> dict:
        """Update the workflow status of an issue.

        Args:
            issue_id: The issue's internal UUID (get from issue query).
            state_id: The target workflow state ID (get from states tool).
        """
        try:
            data = await execute_query(
                UPDATE_STATUS_MUTATION, {"id": issue_id, "stateId": state_id}
            )
            result = data.get("issueUpdate", {})
            if result.get("success"):
                return {"success": True, "issue": result.get("issue")}
            return {"success": False, "error": "Status update failed", "isError": True}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="create_project",
        description="Create a new Linear project. Requires name and team_id. Optional: description, state (planned, started, paused, completed, canceled).",
    )
    async def create_project(
        name: str,
        team_id: str,
        description: str | None = None,
        state: str | None = None,
    ) -> dict:
        """Create a new Linear project.

        Args:
            name: Project name (required).
            team_id: Team UUID to associate with project (required).
            description: Optional project description.
            state: Optional project state (planned, started, paused, completed, canceled).
        """
        try:
            variables = {
                "name": name,
                "teamIds": [team_id],  # API expects array
                "description": description,
                "state": state,
            }
            data = await execute_query(CREATE_PROJECT_MUTATION, variables)
            result = data.get("projectCreate", {})
            if result.get("success"):
                return {"success": True, "project": result.get("project")}
            return {"success": False, "error": "Project creation failed", "isError": True}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="create_project_update",
        description="Post a status update for a Linear project. Requires project_id (UUID from list_projects) and body. Optional: health (onTrack, atRisk, offTrack).",
    )
    async def create_project_update(
        project_id: str,
        body: str,
        health: str | None = None,
    ) -> dict:
        """Post a status update for a Linear project.

        Args:
            project_id: The project's internal UUID (get from list_projects).
            body: The update content (markdown supported).
            health: Optional health status (onTrack, atRisk, offTrack).
        """
        try:
            variables = {
                "projectId": project_id,
                "body": body,
                "health": health,
            }
            data = await execute_query(CREATE_PROJECT_UPDATE_MUTATION, variables)
            result = data.get("projectUpdateCreate", {})
            if result.get("success"):
                return {"success": True, "projectUpdate": result.get("projectUpdate")}
            return {"success": False, "error": "Project update failed", "isError": True}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}
