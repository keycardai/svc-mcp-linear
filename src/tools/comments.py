"""Comment Tools.

Tools for Linear issue comment CRUD: list, create, update, delete.
"""

from fastmcp import FastMCP, Context

from ..auth import auth_provider, get_linear_token, LINEAR_API_URL
from ..client import LinearClientError, execute_query

# GraphQL Queries
LIST_COMMENTS_QUERY = """
query($issueId: String!, $first: Int!) {
    issue(id: $issueId) {
        comments(first: $first, orderBy: createdAt) {
            nodes {
                id
                body
                createdAt
                updatedAt
                editedAt
                url
                user { id name email }
                parent { id }
            }
        }
    }
}
"""

# GraphQL Mutations
CREATE_COMMENT_MUTATION = """
mutation($issueId: String!, $body: String!, $parentId: String) {
    commentCreate(input: {
        issueId: $issueId
        body: $body
        parentId: $parentId
    }) {
        success
        comment {
            id
            body
            createdAt
            url
            user { id name email }
            parent { id }
        }
    }
}
"""

UPDATE_COMMENT_MUTATION = """
mutation($id: String!, $body: String!) {
    commentUpdate(id: $id, input: { body: $body }) {
        success
        comment {
            id
            body
            createdAt
            updatedAt
            editedAt
            url
            user { id name email }
        }
    }
}
"""

DELETE_COMMENT_MUTATION = """
mutation($id: String!) {
    commentDelete(id: $id) {
        success
    }
}
"""


def register_comment_tools(mcp: FastMCP) -> None:
    """Register comment CRUD tools with the MCP server."""

    @mcp.tool(
        name="list_comments",
        description="List comments on a Linear issue, oldest first. Requires issue_id (internal UUID from issue query). Optional: first (max comments to return, default 50).",
    )
    @auth_provider.grant(LINEAR_API_URL)
    async def list_comments(ctx: Context, issue_id: str, first: int = 50) -> dict:
        """List comments on a Linear issue.

        Args:
            issue_id: The issue's internal UUID (get from issue query, not the identifier).
            first: Maximum number of comments to return (default 50).
        """
        try:
            access_ctx = await ctx.get_state("keycardai")
            token = get_linear_token(access_ctx)

            data = await execute_query(
                LIST_COMMENTS_QUERY,
                {"issueId": issue_id, "first": first},
                token=token,
            )
            issue = data.get("issue")
            if issue is None:
                return {"success": False, "error": "Issue not found", "isError": True}
            nodes = (issue.get("comments") or {}).get("nodes", [])
            return {"success": True, "comments": nodes, "count": len(nodes)}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="create_comment",
        description="Post a comment on a Linear issue. Requires issue_id (internal UUID from issue query) and body (markdown supported). Optional: parent_id (comment UUID to reply to in a thread).",
    )
    @auth_provider.grant(LINEAR_API_URL)
    async def create_comment(
        ctx: Context,
        issue_id: str,
        body: str,
        parent_id: str | None = None,
    ) -> dict:
        """Post a comment on a Linear issue.

        Args:
            issue_id: The issue's internal UUID (get from issue query).
            body: Comment body (markdown supported).
            parent_id: Optional parent comment UUID to reply in a thread.
        """
        try:
            access_ctx = await ctx.get_state("keycardai")
            token = get_linear_token(access_ctx)

            variables = {
                "issueId": issue_id,
                "body": body,
                "parentId": parent_id,
            }
            data = await execute_query(CREATE_COMMENT_MUTATION, variables, token=token)
            result = data.get("commentCreate", {})
            if result.get("success"):
                return {"success": True, "comment": result.get("comment")}
            return {"success": False, "error": "Comment creation failed", "isError": True}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="update_comment",
        description="Edit an existing Linear comment. Requires comment_id (UUID) and body (markdown supported; replaces the whole comment body).",
    )
    @auth_provider.grant(LINEAR_API_URL)
    async def update_comment(ctx: Context, comment_id: str, body: str) -> dict:
        """Edit an existing comment.

        Args:
            comment_id: The comment's internal UUID.
            body: New comment body (markdown supported; replaces the whole body).
        """
        try:
            access_ctx = await ctx.get_state("keycardai")
            token = get_linear_token(access_ctx)

            data = await execute_query(
                UPDATE_COMMENT_MUTATION,
                {"id": comment_id, "body": body},
                token=token,
            )
            result = data.get("commentUpdate", {})
            if result.get("success"):
                return {"success": True, "comment": result.get("comment")}
            return {"success": False, "error": "Comment update failed", "isError": True}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}

    @mcp.tool(
        name="delete_comment",
        description="Delete a Linear comment. Requires comment_id (UUID). Irreversible.",
    )
    @auth_provider.grant(LINEAR_API_URL)
    async def delete_comment(ctx: Context, comment_id: str) -> dict:
        """Delete a comment.

        Args:
            comment_id: The comment's internal UUID. Irreversible.
        """
        try:
            access_ctx = await ctx.get_state("keycardai")
            token = get_linear_token(access_ctx)

            data = await execute_query(
                DELETE_COMMENT_MUTATION, {"id": comment_id}, token=token
            )
            result = data.get("commentDelete", {})
            if result.get("success"):
                return {"success": True}
            return {"success": False, "error": "Comment deletion failed", "isError": True}
        except LinearClientError as e:
            return {"success": False, "error": e.message, "isError": True}
        except ValueError as e:
            return {"success": False, "error": str(e), "isError": True}
