"""Tests for Linear GraphQL client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.client import (
    LinearClientError,
    execute_query,
    get_bearer_token,
    sanitize_variables,
)


class TestGetBearerToken:
    """Tests for get_bearer_token function."""

    def test_extracts_valid_bearer_token(self):
        """Should extract token from valid Authorization header."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer test_token_123"

        with patch("src.client.get_http_request", return_value=mock_request):
            token = get_bearer_token()
            assert token == "test_token_123"

    def test_extracts_token_case_insensitive(self):
        """Should handle 'bearer' in any case."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "bearer test_token_456"

        with patch("src.client.get_http_request", return_value=mock_request):
            token = get_bearer_token()
            assert token == "test_token_456"

    def test_raises_on_missing_header(self):
        """Should raise ValueError when Authorization header is missing."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = ""

        with patch("src.client.get_http_request", return_value=mock_request):
            with pytest.raises(ValueError, match="Missing Authorization header"):
                get_bearer_token()

    def test_raises_on_invalid_format(self):
        """Should raise ValueError when header format is invalid."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Basic abc123"

        with patch("src.client.get_http_request", return_value=mock_request):
            with pytest.raises(ValueError, match="Invalid Authorization header format"):
                get_bearer_token()

    def test_raises_on_no_active_request(self):
        """Should raise ValueError when no active HTTP request."""
        with patch("src.client.get_http_request", side_effect=RuntimeError("No request")):
            with pytest.raises(ValueError, match="No active HTTP request"):
                get_bearer_token()


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
    """Tests for execute_query function."""

    @pytest.mark.asyncio
    async def test_successful_query(self):
        """Should return data on successful query."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"viewer": {"name": "Test User"}}}

        with patch("src.client.get_bearer_token", return_value="test_token"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                result = await execute_query("query { viewer { name } }")
                assert result == {"viewer": {"name": "Test User"}}

    @pytest.mark.asyncio
    async def test_passes_variables(self):
        """Should pass variables to the API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"issue": {"title": "Test"}}}

        with patch("src.client.get_bearer_token", return_value="test_token"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.post = mock_post

                await execute_query(
                    "query($id: String!) { issue(id: $id) { title } }",
                    {"id": "ENG-123"},
                )

                # Verify variables were passed
                call_args = mock_post.call_args
                assert call_args.kwargs["json"]["variables"] == {"id": "ENG-123"}

    @pytest.mark.asyncio
    async def test_uses_token_override(self):
        """Should use provided token instead of extracting from request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await execute_query("query { viewer { id } }", token="override_token")

            # Verify override token was used
            call_args = mock_post.call_args
            assert call_args.kwargs["headers"]["Authorization"] == "Bearer override_token"

    @pytest.mark.asyncio
    async def test_handles_graphql_errors(self):
        """Should raise LinearClientError on GraphQL errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errors": [{"message": "Issue not found"}]}

        with patch("src.client.get_bearer_token", return_value="test_token"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                with pytest.raises(LinearClientError, match="Issue not found"):
                    await execute_query("query { issue(id: \"bad\") { title } }")

    @pytest.mark.asyncio
    async def test_handles_http_errors(self):
        """Should raise LinearClientError on HTTP errors."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("src.client.get_bearer_token", return_value="test_token"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )
                with pytest.raises(LinearClientError, match="HTTP 401"):
                    await execute_query("query { viewer { id } }")

    @pytest.mark.asyncio
    async def test_sanitizes_variables(self):
        """Should remove None values from variables."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {}}

        with patch("src.client.get_bearer_token", return_value="test_token"):
            with patch("httpx.AsyncClient") as mock_client:
                mock_post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value.post = mock_post

                await execute_query(
                    "mutation { ... }",
                    {"teamId": "team-1", "title": "Test", "description": None},
                )

                call_args = mock_post.call_args
                # None value should be removed
                assert call_args.kwargs["json"]["variables"] == {
                    "teamId": "team-1",
                    "title": "Test",
                }
