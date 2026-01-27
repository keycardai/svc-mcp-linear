"""Tests for Linear MCP tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import FastMCP

from src.client import LinearClientError
from src.tools.issues import register_issue_tools
from src.tools.mutations import register_mutation_tools
from src.tools.states import register_state_tools


class TestIssueTools:
    """Tests for issue query tools."""

    @pytest.fixture
    def mcp(self) -> FastMCP:
        """Create a FastMCP instance with issue tools registered."""
        mcp = FastMCP("test")
        register_issue_tools(mcp)
        return mcp

    @pytest.mark.asyncio
    async def test_my_issues_returns_assigned_issues(self, mcp: FastMCP):
        """my_issues should return user's assigned issues."""
        mock_data = {
            "viewer": {
                "assignedIssues": {
                    "nodes": [
                        {"id": "1", "identifier": "ENG-1", "title": "Test Issue"}
                    ]
                }
            }
        }

        with patch("src.tools.issues.execute_query", AsyncMock(return_value=mock_data)):
            my_issues_fn = mcp._tool_manager._tools["my_issues"].fn
            result = await my_issues_fn()

            assert result["success"] is True
            assert len(result["issues"]) == 1
            assert result["issues"][0]["identifier"] == "ENG-1"
            assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_my_issues_handles_error(self, mcp: FastMCP):
        """my_issues should return error on failure."""
        with patch(
            "src.tools.issues.execute_query",
            AsyncMock(side_effect=LinearClientError("Auth failed")),
        ):
            my_issues_fn = mcp._tool_manager._tools["my_issues"].fn
            result = await my_issues_fn()

            assert result["success"] is False
            assert "Auth failed" in result["error"]
            assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_issue_returns_single_issue(self, mcp: FastMCP):
        """issue should return details for a specific issue."""
        mock_data = {
            "issue": {
                "id": "123",
                "identifier": "ENG-123",
                "title": "Test Issue",
                "state": {"id": "state-1", "name": "In Progress"},
            }
        }

        with patch("src.tools.issues.execute_query", AsyncMock(return_value=mock_data)):
            issue_fn = mcp._tool_manager._tools["issue"].fn
            result = await issue_fn(identifier="ENG-123")

            assert result["success"] is True
            assert result["issue"]["identifier"] == "ENG-123"

    @pytest.mark.asyncio
    async def test_issue_handles_not_found(self, mcp: FastMCP):
        """issue should return error when issue not found."""
        mock_data = {"issue": None}

        with patch("src.tools.issues.execute_query", AsyncMock(return_value=mock_data)):
            issue_fn = mcp._tool_manager._tools["issue"].fn
            result = await issue_fn(identifier="ENG-999")

            assert result["success"] is False
            assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_search_returns_matching_issues(self, mcp: FastMCP):
        """search should return issues matching the query."""
        mock_data = {
            "issues": {
                "nodes": [
                    {"id": "1", "identifier": "ENG-1", "title": "Bug fix"},
                    {"id": "2", "identifier": "ENG-2", "title": "Bug report"},
                ]
            }
        }

        with patch("src.tools.issues.execute_query", AsyncMock(return_value=mock_data)):
            search_fn = mcp._tool_manager._tools["search"].fn
            result = await search_fn(query="bug")

            assert result["success"] is True
            assert len(result["issues"]) == 2
            assert result["query"] == "bug"
            assert result["count"] == 2


class TestMutationTools:
    """Tests for issue mutation tools."""

    @pytest.fixture
    def mcp(self) -> FastMCP:
        """Create a FastMCP instance with mutation tools registered."""
        mcp = FastMCP("test")
        register_mutation_tools(mcp)
        return mcp

    @pytest.mark.asyncio
    async def test_create_issue_success(self, mcp: FastMCP):
        """create_issue should create and return new issue."""
        mock_data = {
            "issueCreate": {
                "success": True,
                "issue": {
                    "id": "new-123",
                    "identifier": "ENG-456",
                    "title": "New Issue",
                    "url": "https://linear.app/...",
                },
            }
        }

        with patch(
            "src.tools.mutations.execute_query", AsyncMock(return_value=mock_data)
        ):
            create_fn = mcp._tool_manager._tools["create_issue"].fn
            result = await create_fn(team_id="team-1", title="New Issue")

            assert result["success"] is True
            assert result["issue"]["identifier"] == "ENG-456"

    @pytest.mark.asyncio
    async def test_create_issue_with_optional_fields(self, mcp: FastMCP):
        """create_issue should accept optional fields."""
        mock_data = {
            "issueCreate": {
                "success": True,
                "issue": {"id": "new-123", "identifier": "ENG-456"},
            }
        }

        with patch(
            "src.tools.mutations.execute_query", AsyncMock(return_value=mock_data)
        ) as mock_query:
            create_fn = mcp._tool_manager._tools["create_issue"].fn
            await create_fn(
                team_id="team-1",
                title="New Issue",
                description="A description",
                priority=2,
            )

            # Verify optional fields were passed
            call_args = mock_query.call_args
            variables = call_args[0][1]
            assert variables["description"] == "A description"
            assert variables["priority"] == 2

    @pytest.mark.asyncio
    async def test_update_issue_success(self, mcp: FastMCP):
        """update_issue should update and return issue."""
        mock_data = {
            "issueUpdate": {
                "success": True,
                "issue": {
                    "id": "123",
                    "identifier": "ENG-123",
                    "title": "Updated Title",
                },
            }
        }

        with patch(
            "src.tools.mutations.execute_query", AsyncMock(return_value=mock_data)
        ):
            update_fn = mcp._tool_manager._tools["update_issue"].fn
            result = await update_fn(issue_id="123", title="Updated Title")

            assert result["success"] is True
            assert result["issue"]["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_status_success(self, mcp: FastMCP):
        """update_status should update workflow state."""
        mock_data = {
            "issueUpdate": {
                "success": True,
                "issue": {
                    "id": "123",
                    "identifier": "ENG-123",
                    "state": {"name": "Done"},
                },
            }
        }

        with patch(
            "src.tools.mutations.execute_query", AsyncMock(return_value=mock_data)
        ):
            status_fn = mcp._tool_manager._tools["update_status"].fn
            result = await status_fn(issue_id="123", state_id="done-state")

            assert result["success"] is True
            assert result["issue"]["state"]["name"] == "Done"


class TestStateTools:
    """Tests for workflow state tools."""

    @pytest.fixture
    def mcp(self) -> FastMCP:
        """Create a FastMCP instance with state tools registered."""
        mcp = FastMCP("test")
        register_state_tools(mcp)
        return mcp

    @pytest.mark.asyncio
    async def test_states_returns_team_states(self, mcp: FastMCP):
        """states should return states for a specific team."""
        mock_data = {
            "team": {
                "id": "team-1",
                "name": "Engineering",
                "states": {
                    "nodes": [
                        {"id": "s1", "name": "Backlog", "type": "backlog"},
                        {"id": "s2", "name": "In Progress", "type": "started"},
                        {"id": "s3", "name": "Done", "type": "completed"},
                    ]
                },
            }
        }

        with patch("src.tools.states.execute_query", AsyncMock(return_value=mock_data)):
            states_fn = mcp._tool_manager._tools["states"].fn
            result = await states_fn(team_id="team-1")

            assert result["success"] is True
            assert result["team"]["name"] == "Engineering"
            assert len(result["states"]) == 3

    @pytest.mark.asyncio
    async def test_states_returns_all_teams(self, mcp: FastMCP):
        """states should return states for all teams when no team_id."""
        mock_data = {
            "teams": {
                "nodes": [
                    {
                        "id": "team-1",
                        "name": "Engineering",
                        "states": {
                            "nodes": [{"id": "s1", "name": "Backlog", "type": "backlog"}]
                        },
                    },
                    {
                        "id": "team-2",
                        "name": "Design",
                        "states": {
                            "nodes": [{"id": "s2", "name": "Todo", "type": "unstarted"}]
                        },
                    },
                ]
            }
        }

        with patch("src.tools.states.execute_query", AsyncMock(return_value=mock_data)):
            states_fn = mcp._tool_manager._tools["states"].fn
            result = await states_fn()

            assert result["success"] is True
            assert len(result["teams"]) == 2
            assert result["teams"][0]["name"] == "Engineering"
            assert result["teams"][1]["name"] == "Design"

    @pytest.mark.asyncio
    async def test_states_handles_team_not_found(self, mcp: FastMCP):
        """states should return error when team not found."""
        mock_data = {"team": None}

        with patch("src.tools.states.execute_query", AsyncMock(return_value=mock_data)):
            states_fn = mcp._tool_manager._tools["states"].fn
            result = await states_fn(team_id="bad-team")

            assert result["success"] is False
            assert "not found" in result["error"]
