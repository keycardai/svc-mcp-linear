"""Linear GraphQL Client.

Provides async HTTP client for making authenticated requests to Linear API.
Token is provided by the calling tool function from Keycard AccessContext.
"""

from __future__ import annotations

from typing import Any

import httpx

LINEAR_API_URL = "https://api.linear.app/graphql"


class LinearClientError(Exception):
    """Raised when Linear API returns an error."""

    def __init__(self, message: str, errors: list[dict] | None = None):
        self.message = message
        self.errors = errors or []
        super().__init__(message)


def sanitize_variables(variables: dict[str, Any]) -> dict[str, Any]:
    """Remove None values from GraphQL variables.

    Linear GraphQL API doesn't accept null for optional fields.

    Args:
        variables: Dictionary of GraphQL variables.

    Returns:
        Dictionary with None values removed.
    """
    return {k: v for k, v in variables.items() if v is not None}


async def execute_query(
    query: str,
    variables: dict[str, Any] | None = None,
    *,
    token: str,
) -> dict[str, Any]:
    """Execute a GraphQL query against the Linear API.

    Args:
        query: GraphQL query or mutation string.
        variables: Optional dictionary of variables.
        token: Linear API access token (required).

    Returns:
        The 'data' portion of the GraphQL response.

    Raises:
        LinearClientError: If the API returns errors.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = sanitize_variables(variables)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            LINEAR_API_URL,
            headers=headers,
            json=payload,
            timeout=30.0,
        )

        # Handle HTTP errors
        if response.status_code != 200:
            raise LinearClientError(
                f"Linear API returned HTTP {response.status_code}: {response.text}"
            )

        result = response.json()

        # Handle GraphQL errors
        if "errors" in result:
            error_messages = [e.get("message", str(e)) for e in result["errors"]]
            raise LinearClientError(
                f"GraphQL errors: {'; '.join(error_messages)}",
                errors=result["errors"],
            )

        return result.get("data", {})
