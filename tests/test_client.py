"""Tests for Linear GraphQL client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.client import (
    LinearClientError,
    execute_query,
    sanitize_variables,
)


class TestSanitizeVariables:
    """Tests for sanitize_variables function."""

    def test_removes_none_values(self):
        """Should remove None values from dictionary."""
        variables = {
            "teamId": "team-123",
            "title": "Test",
            "description": None,
            "priority": None,
        }
        result = sanitize_variables(variables)
        assert result == {"teamId": "team-123", "title": "Test"}

    def test_keeps_falsy_but_not_none(self):
        """Should keep falsy values that are not None."""
        variables = {
            "teamId": "team-123",
            "priority": 0,
            "title": "",
            "enabled": False,
        }
        result = sanitize_variables(variables)
        assert result == {
            "teamId": "team-123",
            "priority": 0,
            "title": "",
            "enabled": False,
        }

    def test_empty_dict(self):
        """Should handle empty dictionary."""
        assert sanitize_variables({}) == {}

    def test_all_none(self):
        """Should return empty dict when all values are None."""
        variables = {"a": None, "b": None}
        assert sanitize_variables(variables) == {}


class TestExecuteQuery:
    """Tests for execute_query function.

    The token is passed explicitly by the caller (the tool resolves it from the
    Keycard AccessContext); execute_query no longer extracts it from the request.
    """

    @pytest.mark.asyncio
    async def test_successful_query(self):
        """Should return data on successful query."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"viewer": {"name": "Test User"}}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await execute_query("query { viewer { name } }", token="test_token")
            assert result == {"viewer": {"name": "Test User"}}

    @pytest.mark.asyncio
    async def test_passes_variables(self):
        """Should pass variables to the API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"issue": {"title": "Test"}}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await execute_query(
                "query($id: String!) { issue(id: $id) { title } }",
                {"id": "ENG-123"},
                token="test_token",
            )

            call_args = mock_post.call_args
            assert call_args.kwargs["json"]["variables"] == {"id": "ENG-123"}

    @pytest.mark.asyncio
    async def test_uses_provided_token(self):
        """Should send the provided token as a Bearer Authorization header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await execute_query("query { viewer { id } }", token="override_token")

            call_args = mock_post.call_args
            assert call_args.kwargs["headers"]["Authorization"] == "Bearer override_token"

    @pytest.mark.asyncio
    async def test_handles_graphql_errors(self):
        """Should raise LinearClientError on GraphQL errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errors": [{"message": "Issue not found"}]}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            with pytest.raises(LinearClientError, match="Issue not found"):
                await execute_query(
                    'query { issue(id: "bad") { title } }', token="test_token"
                )

    @pytest.mark.asyncio
    async def test_handles_http_errors(self):
        """Should raise LinearClientError on HTTP errors."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            with pytest.raises(LinearClientError, match="HTTP 401"):
                await execute_query("query { viewer { id } }", token="test_token")

    @pytest.mark.asyncio
    async def test_sanitizes_variables(self):
        """Should remove None values from variables."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await execute_query(
                "mutation { placeholder }",
                {"teamId": "team-1", "title": "Test", "description": None},
                token="test_token",
            )

            call_args = mock_post.call_args
            assert call_args.kwargs["json"]["variables"] == {
                "teamId": "team-1",
                "title": "Test",
            }
