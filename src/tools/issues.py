"""Query Tools.

Tools for reading Linear data: my_issues, issue, search, list_projects.
"""

from __future__ import annotations

from fastmcp import FastMCP

from ..client import LinearClientError, execute_query

# GraphQL Queries
MY_ISSUES_QUERY = """
query {
    viewer {
        assignedIssues(first: 50) {
            nodes {
                id
                identifier
                title
                description
                state { name }
                priority
                project { name }
            }
        }
    }
}
"""

ISSUE_QUERY = """
query($identifier: String!) {
    issue(id: $identifier) {
        id
        identifier
        title
        description
        state { id name }
        priority
        labels { nodes { name } }
        assignee { name email }
        project { name }
        team { id name }
        comments { nodes { body user { name } createdAt } }
    }
}
"""

SEARCH_ISSUES_QUERY = """
query($query: String!) {
    issues(filter: {
        or: [
            { title: { containsIgnoreCase: $query } },
            { description: { containsIgnoreCase: $query } }
        ]
    }, first: 50) {
        nodes {
            id
            identifier
            title
            description
            state { name }
            priority
            project { name }
        }
    }
}
"""

LIST_PROJECTS_QUERY = """
query {
    projects(first: 50) {
        nodes {
            id
            name
            slugId
            state
            teams {
                nodes {
                    id
                    name
                }
            }
        }
    }
}
"""

LIST_PROJECTS_BY_TEAM_QUERY = """
query($teamId: String!) {
    projects(filter: { accessibleTeams: { id: { eq: $teamId } } }, first: 50) {
        nodes {
            id
            name
            slugId
            state
            teams {
                nodes {
                    id
                    name
                }
            }
        }
    }
}
"""

LIST_PROJECT_UPDATES_QUERY = """
query($projectId: String!, $first: Int!) {
    project(id: $projectId) {
        id
        name
        projectUpdates(first: $first) {
            nodes {
                id
                body
                health
                createdAt
                user { name email }
            }
        }
    }
}
"""


def register_issue_tools(mcp: FastMCP) -> None:
    """Register issue query tools with the MCP server."""

    @mcp.tool(
        name="my_issues",
        description="Get Linear issues assigned to the authenticated user. Returns list of issues with id, identifier, title, description, state, priority, and project.",
    )
    async def my_issues() -> dict:
        """Fetch Linear issues assigned to the current user."""
        try:
            data = await execute_query(MY_ISSUES_QUERY)
            issues = data.get("viewer", {}).get("assignedIssues", {}).get("nodes", [])
            return {"success": True, "issues": issues, "count": len(issues)}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="issue",
        description="Get details of a specific Linear issue by its identifier (e.g., 'ENG-123'). Returns full issue details including comments, labels, assignee, and team.",
    )
    async def issue(identifier: str) -> dict:
        """Fetch a specific Linear issue by identifier.

        Args:
            identifier: The issue identifier (e.g., 'ENG-123').
        """
        try:
            data = await execute_query(ISSUE_QUERY, {"identifier": identifier})
            issue_data = data.get("issue")
            if issue_data is None:
                return {
                    "success": False,
                    "error": f"Issue {identifier} not found",
                    "isError": True,
                }
            return {"success": True, "issue": issue_data}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="search",
        description="Search Linear issues by text query. Searches in issue title and description (case-insensitive). Returns matching issues with basic details.",
    )
    async def search(query: str) -> dict:
        """Search issues by text query.

        Args:
            query: Search text to match in title or description.
        """
        try:
            data = await execute_query(SEARCH_ISSUES_QUERY, {"query": query})
            issues = data.get("issues", {}).get("nodes", [])
            return {
                "success": True,
                "query": query,
                "issues": issues,
                "count": len(issues),
            }
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="list_projects",
        description="List Linear projects, optionally filtered by team. Returns project id, name, state, and associated teams.",
    )
    async def list_projects(team_id: str | None = None) -> dict:
        """List Linear projects.

        Args:
            team_id: Optional team UUID to filter projects by.
        """
        try:
            if team_id:
                data = await execute_query(
                    LIST_PROJECTS_BY_TEAM_QUERY, {"teamId": team_id}
                )
            else:
                data = await execute_query(LIST_PROJECTS_QUERY)
            projects = data.get("projects", {}).get("nodes", [])
            return {"success": True, "projects": projects, "count": len(projects)}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="list_project_updates",
        description="Get recent status updates for a Linear project. Returns updates with body, health status, date, and author.",
    )
    async def list_project_updates(project_id: str, limit: int = 10) -> dict:
        """List recent status updates for a project.

        Args:
            project_id: The project's internal UUID (get from list_projects).
            limit: Number of updates to return (default 10).
        """
        try:
            data = await execute_query(
                LIST_PROJECT_UPDATES_QUERY, {"projectId": project_id, "first": limit}
            )
            project = data.get("project")
            if project is None:
                return {
                    "success": False,
                    "error": f"Project {project_id} not found",
                    "isError": True,
                }
            updates = project.get("projectUpdates", {}).get("nodes", [])
            return {
                "success": True,
                "project": {"id": project.get("id"), "name": project.get("name")},
                "updates": updates,
                "count": len(updates),
            }
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}
