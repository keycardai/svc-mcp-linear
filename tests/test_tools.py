"""Tests for Linear MCP tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP

from src.client import LinearClientError
from src.tools.comments import register_comment_tools
from src.tools.issues import register_issue_tools
from src.tools.milestones import register_milestone_tools
from src.tools.mutations import register_mutation_tools
from src.tools.states import register_state_tools


def make_ctx() -> MagicMock:
    """Return a mock FastMCP Context with async get_state."""
    ctx = MagicMock()
    ctx.get_state = AsyncMock(return_value=MagicMock())
    return ctx


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
            with patch("src.tools.issues.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("my_issues")
                result = await tool.fn(make_ctx())

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
            with patch("src.tools.issues.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("my_issues")
                result = await tool.fn(make_ctx())

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
            with patch("src.tools.issues.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("issue")
                result = await tool.fn(make_ctx(), identifier="ENG-123")

                assert result["success"] is True
                assert result["issue"]["identifier"] == "ENG-123"

    @pytest.mark.asyncio
    async def test_issue_handles_not_found(self, mcp: FastMCP):
        """issue should return error when issue not found."""
        mock_data = {"issue": None}

        with patch("src.tools.issues.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.issues.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("issue")
                result = await tool.fn(make_ctx(), identifier="ENG-999")

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
            with patch("src.tools.issues.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("search")
                result = await tool.fn(make_ctx(), query="bug")

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

        with patch("src.tools.mutations.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.mutations.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("create_issue")
                result = await tool.fn(make_ctx(), team_id="team-1", title="New Issue")

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
            with patch("src.tools.mutations.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("create_issue")
                await tool.fn(
                    make_ctx(),
                    team_id="team-1",
                    title="New Issue",
                    description="A description",
                    priority=2,
                )

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

        with patch("src.tools.mutations.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.mutations.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("update_issue")
                result = await tool.fn(make_ctx(), issue_id="123", title="Updated Title")

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

        with patch("src.tools.mutations.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.mutations.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("update_status")
                result = await tool.fn(make_ctx(), issue_id="123", state_id="done-state")

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
            with patch("src.tools.states.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("states")
                result = await tool.fn(make_ctx(), team_id="team-1")

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
            with patch("src.tools.states.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("states")
                result = await tool.fn(make_ctx())

                assert result["success"] is True
                assert len(result["teams"]) == 2
                assert result["teams"][0]["name"] == "Engineering"
                assert result["teams"][1]["name"] == "Design"

    @pytest.mark.asyncio
    async def test_states_handles_team_not_found(self, mcp: FastMCP):
        """states should return error when team not found."""
        mock_data = {"team": None}

        with patch("src.tools.states.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.states.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("states")
                result = await tool.fn(make_ctx(), team_id="bad-team")

                assert result["success"] is False
                assert "not found" in result["error"]


class TestMilestoneTools:
    """Tests for project milestone CRUD tools."""

    @pytest.fixture
    def mcp(self) -> FastMCP:
        """Create a FastMCP instance with milestone tools registered."""
        mcp = FastMCP("test")
        register_milestone_tools(mcp)
        return mcp

    @pytest.mark.asyncio
    async def test_list_milestones_returns_milestones(self, mcp: FastMCP):
        """list_milestones should return project milestones with count."""
        mock_data = {
            "projectMilestones": {
                "nodes": [
                    {"id": "m1", "name": "Alpha", "targetDate": "2025-06-30"},
                    {"id": "m2", "name": "Beta", "targetDate": "2025-09-30"},
                ]
            }
        }

        with patch("src.tools.milestones.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("list_milestones")
                result = await tool.fn(make_ctx(), project_id="proj-1")

                assert result["success"] is True
                assert len(result["milestones"]) == 2
                assert result["count"] == 2
                assert result["milestones"][0]["name"] == "Alpha"

    @pytest.mark.asyncio
    async def test_list_milestones_returns_empty(self, mcp: FastMCP):
        """list_milestones should return empty list when no milestones exist."""
        mock_data = {"projectMilestones": {"nodes": []}}

        with patch("src.tools.milestones.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("list_milestones")
                result = await tool.fn(make_ctx(), project_id="proj-1")

                assert result["success"] is True
                assert result["milestones"] == []
                assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_list_milestones_handles_error(self, mcp: FastMCP):
        """list_milestones should return error on API failure."""
        with patch(
            "src.tools.milestones.execute_query",
            AsyncMock(side_effect=LinearClientError("Network error")),
        ):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("list_milestones")
                result = await tool.fn(make_ctx(), project_id="proj-1")

                assert result["success"] is False
                assert "Network error" in result["error"]
                assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_get_milestone_returns_milestone(self, mcp: FastMCP):
        """get_milestone should return milestone details."""
        mock_data = {
            "projectMilestone": {
                "id": "m1",
                "name": "Alpha",
                "description": "First milestone",
                "targetDate": "2025-06-30",
                "project": {"id": "proj-1", "name": "My Project"},
            }
        }

        with patch("src.tools.milestones.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("get_milestone")
                result = await tool.fn(make_ctx(), milestone_id="m1")

                assert result["success"] is True
                assert result["milestone"]["name"] == "Alpha"
                assert result["milestone"]["project"]["name"] == "My Project"

    @pytest.mark.asyncio
    async def test_get_milestone_handles_not_found(self, mcp: FastMCP):
        """get_milestone should return error when milestone not found."""
        mock_data = {"projectMilestone": None}

        with patch("src.tools.milestones.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("get_milestone")
                result = await tool.fn(make_ctx(), milestone_id="bad-id")

                assert result["success"] is False
                assert "not found" in result["error"]
                assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_create_milestone_success(self, mcp: FastMCP):
        """create_milestone should create and return new milestone."""
        mock_data = {
            "projectMilestoneCreate": {
                "success": True,
                "projectMilestone": {
                    "id": "m-new",
                    "name": "v1.0 Launch",
                    "description": None,
                    "targetDate": "2025-12-31",
                    "project": {"id": "proj-1", "name": "My Project"},
                },
            }
        }

        with patch("src.tools.milestones.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("create_milestone")
                result = await tool.fn(
                    make_ctx(),
                    project_id="proj-1",
                    name="v1.0 Launch",
                    target_date="2025-12-31",
                )

                assert result["success"] is True
                assert result["milestone"]["name"] == "v1.0 Launch"
                assert result["milestone"]["id"] == "m-new"

    @pytest.mark.asyncio
    async def test_create_milestone_passes_optional_fields(self, mcp: FastMCP):
        """create_milestone should pass description and target_date to API."""
        mock_data = {
            "projectMilestoneCreate": {
                "success": True,
                "projectMilestone": {"id": "m-new", "name": "M1"},
            }
        }

        with patch(
            "src.tools.milestones.execute_query", AsyncMock(return_value=mock_data)
        ) as mock_query:
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("create_milestone")
                await tool.fn(
                    make_ctx(),
                    project_id="proj-1",
                    name="M1",
                    description="Key milestone",
                    target_date="2025-06-30",
                )

                call_args = mock_query.call_args
                variables = call_args[0][1]
                assert variables["description"] == "Key milestone"
                assert variables["targetDate"] == "2025-06-30"

    @pytest.mark.asyncio
    async def test_create_milestone_handles_api_failure(self, mcp: FastMCP):
        """create_milestone should return error when API reports failure."""
        mock_data = {"projectMilestoneCreate": {"success": False}}

        with patch("src.tools.milestones.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("create_milestone")
                result = await tool.fn(make_ctx(), project_id="proj-1", name="M1")

                assert result["success"] is False
                assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_update_milestone_success(self, mcp: FastMCP):
        """update_milestone should update and return milestone."""
        mock_data = {
            "projectMilestoneUpdate": {
                "success": True,
                "projectMilestone": {
                    "id": "m1",
                    "name": "Renamed Milestone",
                    "targetDate": "2026-01-15",
                    "project": {"id": "proj-1", "name": "My Project"},
                },
            }
        }

        with patch("src.tools.milestones.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("update_milestone")
                result = await tool.fn(
                    make_ctx(),
                    milestone_id="m1",
                    name="Renamed Milestone",
                    target_date="2026-01-15",
                )

                assert result["success"] is True
                assert result["milestone"]["name"] == "Renamed Milestone"

    @pytest.mark.asyncio
    async def test_update_milestone_handles_failure(self, mcp: FastMCP):
        """update_milestone should return error when update fails."""
        mock_data = {"projectMilestoneUpdate": {"success": False}}

        with patch("src.tools.milestones.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("update_milestone")
                result = await tool.fn(make_ctx(), milestone_id="m1", name="New Name")

                assert result["success"] is False
                assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_delete_milestone_success(self, mcp: FastMCP):
        """delete_milestone should delete and confirm success."""
        mock_data = {"projectMilestoneDelete": {"success": True}}

        with patch("src.tools.milestones.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("delete_milestone")
                result = await tool.fn(make_ctx(), milestone_id="m1")

                assert result["success"] is True
                assert result["deleted"] is True
                assert result["milestone_id"] == "m1"

    @pytest.mark.asyncio
    async def test_delete_milestone_handles_failure(self, mcp: FastMCP):
        """delete_milestone should return error when deletion fails."""
        mock_data = {"projectMilestoneDelete": {"success": False}}

        with patch("src.tools.milestones.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("delete_milestone")
                result = await tool.fn(make_ctx(), milestone_id="m1")

                assert result["success"] is False
                assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_delete_milestone_handles_error(self, mcp: FastMCP):
        """delete_milestone should return error on API failure."""
        with patch(
            "src.tools.milestones.execute_query",
            AsyncMock(side_effect=LinearClientError("Permission denied")),
        ):
            with patch("src.tools.milestones.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("delete_milestone")
                result = await tool.fn(make_ctx(), milestone_id="m1")

                assert result["success"] is False
                assert "Permission denied" in result["error"]
                assert result["isError"] is True


class TestCommentTools:
    """Tests for issue comment CRUD tools."""

    @pytest.fixture
    def mcp(self) -> FastMCP:
        """Create a FastMCP instance with comment tools registered."""
        mcp = FastMCP("test")
        register_comment_tools(mcp)
        return mcp

    @pytest.mark.asyncio
    async def test_list_comments_returns_comments(self, mcp: FastMCP):
        """list_comments should return comments with count."""
        mock_data = {
            "issue": {
                "comments": {
                    "nodes": [
                        {"id": "c1", "body": "first", "user": {"name": "Kiam"}},
                        {"id": "c2", "body": "second", "user": {"name": "Larry"}},
                    ]
                }
            }
        }

        with patch("src.tools.comments.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("list_comments")
                result = await tool.fn(make_ctx(), issue_id="iss-1")

                assert result["success"] is True
                assert len(result["comments"]) == 2
                assert result["count"] == 2
                assert result["comments"][0]["body"] == "first"

    @pytest.mark.asyncio
    async def test_list_comments_returns_empty(self, mcp: FastMCP):
        """list_comments should return empty list when no comments exist."""
        mock_data = {"issue": {"comments": {"nodes": []}}}

        with patch("src.tools.comments.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("list_comments")
                result = await tool.fn(make_ctx(), issue_id="iss-1")

                assert result["success"] is True
                assert result["comments"] == []
                assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_list_comments_handles_issue_not_found(self, mcp: FastMCP):
        """list_comments should return error when the issue UUID is unknown."""
        mock_data = {"issue": None}

        with patch("src.tools.comments.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("list_comments")
                result = await tool.fn(make_ctx(), issue_id="bad-id")

                assert result["success"] is False
                assert "not found" in result["error"]
                assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_list_comments_handles_error(self, mcp: FastMCP):
        """list_comments should return error on API failure."""
        with patch(
            "src.tools.comments.execute_query",
            AsyncMock(side_effect=LinearClientError("Network down")),
        ):
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("list_comments")
                result = await tool.fn(make_ctx(), issue_id="iss-1")

                assert result["success"] is False
                assert "Network down" in result["error"]
                assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_create_comment_success(self, mcp: FastMCP):
        """create_comment should create and return new comment."""
        mock_data = {
            "commentCreate": {
                "success": True,
                "comment": {
                    "id": "c-new",
                    "body": "Looks good",
                    "url": "https://linear.app/foo/c/c-new",
                    "user": {"name": "Kiam"},
                },
            }
        }

        with patch("src.tools.comments.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("create_comment")
                result = await tool.fn(make_ctx(), issue_id="iss-1", body="Looks good")

                assert result["success"] is True
                assert result["comment"]["body"] == "Looks good"
                assert result["comment"]["id"] == "c-new"

    @pytest.mark.asyncio
    async def test_create_comment_passes_parent_id(self, mcp: FastMCP):
        """create_comment should forward parent_id for threaded replies."""
        mock_data = {
            "commentCreate": {
                "success": True,
                "comment": {"id": "c-new", "body": "reply"},
            }
        }

        with patch(
            "src.tools.comments.execute_query", AsyncMock(return_value=mock_data)
        ) as mock_query:
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("create_comment")
                await tool.fn(
                    make_ctx(),
                    issue_id="iss-1",
                    body="reply",
                    parent_id="c-parent",
                )

                variables = mock_query.call_args[0][1]
                assert variables["parentId"] == "c-parent"

    @pytest.mark.asyncio
    async def test_create_comment_handles_api_failure(self, mcp: FastMCP):
        """create_comment should return error when API reports failure."""
        mock_data = {"commentCreate": {"success": False}}

        with patch("src.tools.comments.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("create_comment")
                result = await tool.fn(make_ctx(), issue_id="iss-1", body="hi")

                assert result["success"] is False
                assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_create_comment_handles_error(self, mcp: FastMCP):
        """create_comment should return error on client exception."""
        with patch(
            "src.tools.comments.execute_query",
            AsyncMock(side_effect=LinearClientError("Forbidden")),
        ):
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("create_comment")
                result = await tool.fn(make_ctx(), issue_id="iss-1", body="hi")

                assert result["success"] is False
                assert "Forbidden" in result["error"]
                assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_update_comment_success(self, mcp: FastMCP):
        """update_comment should edit and return updated comment."""
        mock_data = {
            "commentUpdate": {
                "success": True,
                "comment": {
                    "id": "c1",
                    "body": "edited body",
                    "editedAt": "2026-05-22T12:00:00Z",
                    "user": {"name": "Kiam"},
                },
            }
        }

        with patch("src.tools.comments.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("update_comment")
                result = await tool.fn(make_ctx(), comment_id="c1", body="edited body")

                assert result["success"] is True
                assert result["comment"]["body"] == "edited body"
                assert result["comment"]["editedAt"] is not None

    @pytest.mark.asyncio
    async def test_update_comment_handles_error(self, mcp: FastMCP):
        """update_comment should return error on client exception."""
        with patch(
            "src.tools.comments.execute_query",
            AsyncMock(side_effect=LinearClientError("Comment not found")),
        ):
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("update_comment")
                result = await tool.fn(make_ctx(), comment_id="bad", body="x")

                assert result["success"] is False
                assert "Comment not found" in result["error"]
                assert result["isError"] is True

    @pytest.mark.asyncio
    async def test_delete_comment_success(self, mcp: FastMCP):
        """delete_comment should succeed."""
        mock_data = {"commentDelete": {"success": True}}

        with patch("src.tools.comments.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("delete_comment")
                result = await tool.fn(make_ctx(), comment_id="c1")

                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_comment_handles_failure(self, mcp: FastMCP):
        """delete_comment should return error when API reports failure."""
        mock_data = {"commentDelete": {"success": False}}

        with patch("src.tools.comments.execute_query", AsyncMock(return_value=mock_data)):
            with patch("src.tools.comments.get_linear_token", return_value="fake-token"):
                tool = await mcp.get_tool("delete_comment")
                result = await tool.fn(make_ctx(), comment_id="c1")

                assert result["success"] is False
                assert result["isError"] is True
