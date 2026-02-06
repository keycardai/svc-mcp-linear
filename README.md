# svc-mcp-linear

Linear MCP Server with Keycard Authentication.

This server uses the Keycard SDK to handle OAuth authentication, providing secure per-user access to the Linear API.

## Architecture

```
┌─────────────┐     ┌─────────────┐
│  MCP Client │────▶│ This Server │────▶ Linear API
└─────────────┘     └─────────────┘
                          │
                   ┌──────▼──────┐
                   │   Keycard   │
                   │   (OAuth)   │
                   └─────────────┘
```

Keycard handles OAuth token exchange. Each user authenticates through Keycard, and the server receives user-specific tokens via the `@auth_provider.grant()` decorator.

## Tools

| Tool | Type | Description |
|------|------|-------------|
| `my_issues` | Query | Get issues assigned to authenticated user |
| `issue` | Query | Get details of a specific issue by identifier (e.g., ENG-123) |
| `search` | Query | Search issues by text query (searches title and description) |
| `list_projects` | Query | List projects, optionally filtered by team |
| `list_project_updates` | Query | Get recent status updates for a project |
| `create_issue` | Mutation | Create a new issue (requires team_id and title, optional project_id) |
| `update_issue` | Mutation | Update issue fields (title, description, priority, etc.) |
| `update_status` | Mutation | Change issue workflow state |
| `create_project` | Mutation | Create a new project (requires name and team_id) |
| `create_project_update` | Mutation | Post a status update for a project |
| `states` | Query | List available workflow states for a team |

### Tool Details

#### `my_issues`
Returns issues assigned to the authenticated user.

**Response:**
```json
{
  "success": true,
  "issues": [
    {
      "id": "uuid",
      "identifier": "ENG-123",
      "title": "Fix login bug",
      "description": "...",
      "state": { "name": "In Progress" },
      "priority": 2,
      "project": { "name": "Backend" }
    }
  ],
  "count": 1
}
```

#### `issue`
Get details of a specific issue.

**Parameters:**
- `identifier` (required): Issue identifier like "ENG-123"

**Response:**
```json
{
  "success": true,
  "issue": {
    "id": "uuid",
    "identifier": "ENG-123",
    "title": "Fix login bug",
    "description": "...",
    "state": { "id": "state-uuid", "name": "In Progress" },
    "priority": 2,
    "labels": { "nodes": [{ "name": "bug" }] },
    "assignee": { "name": "John Doe", "email": "john@example.com" },
    "team": { "id": "team-uuid", "name": "Engineering" },
    "comments": { "nodes": [...] }
  }
}
```

#### `search`
Search issues by text query.

**Parameters:**
- `query` (required): Search text (case-insensitive, searches title and description)

#### `list_projects`
List Linear projects.

**Parameters:**
- `team_id` (optional): Team UUID to filter projects by

**Response:**
```json
{
  "success": true,
  "projects": [
    {
      "id": "project-uuid",
      "name": "Backend Refactor",
      "slugId": "backend-refactor",
      "state": "started",
      "teams": {
        "nodes": [
          { "id": "team-uuid", "name": "Engineering" }
        ]
      }
    }
  ],
  "count": 1
}
```

#### `list_project_updates`
Get recent status updates for a project.

**Parameters:**
- `project_id` (required): Project UUID (get from list_projects)
- `limit` (optional): Number of updates to return (default 10)

#### `create_issue`
Create a new issue.

**Parameters:**
- `team_id` (required): Team UUID
- `title` (required): Issue title
- `description` (optional): Issue description (markdown supported)
- `priority` (optional): 0=none, 1=urgent, 2=high, 3=medium, 4=low
- `state_id` (optional): Initial workflow state UUID
- `assignee_id` (optional): Assignee user UUID
- `project_id` (optional): Project UUID to assign issue to (get from `list_projects`)

#### `update_issue`
Update an existing issue.

**Parameters:**
- `issue_id` (required): Issue UUID (from issue query, not the identifier)
- `title` (optional): New title
- `description` (optional): New description
- `priority` (optional): New priority
- `state_id` (optional): New workflow state UUID
- `assignee_id` (optional): New assignee UUID

#### `update_status`
Change issue workflow state.

**Parameters:**
- `issue_id` (required): Issue UUID
- `state_id` (required): Target workflow state UUID (get from `states` tool)

#### `create_project`
Create a new Linear project.

**Parameters:**
- `name` (required): Project name
- `team_id` (required): Team UUID to associate with project
- `description` (optional): Project description
- `state` (optional): Project state (planned, started, paused, completed, canceled)

**Response:**
```json
{
  "success": true,
  "project": {
    "id": "project-uuid",
    "name": "New Project",
    "slugId": "new-project",
    "url": "https://linear.app/team/project/new-project"
  }
}
```

#### `create_project_update`
Post a status update for a project.

**Parameters:**
- `project_id` (required): Project UUID (get from list_projects)
- `body` (required): Update content (markdown supported)
- `health` (optional): Health status (onTrack, atRisk, offTrack)

#### `states`
Get available workflow states.

**Parameters:**
- `team_id` (optional): Team UUID. If not provided, returns states for all teams.

**Response (single team):**
```json
{
  "success": true,
  "team": { "id": "team-uuid", "name": "Engineering" },
  "states": [
    { "id": "state-1", "name": "Backlog", "type": "backlog" },
    { "id": "state-2", "name": "In Progress", "type": "started" },
    { "id": "state-3", "name": "Done", "type": "completed" }
  ]
}
```

## Local Development

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Keycard application credentials (zone_id, client_id, client_secret)

### Setup

1. Clone and enter the directory:
   ```bash
   cd svc-mcp-linear
   ```

2. Create virtual environment and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate
   uv sync
   ```

3. Create `.env` from example:
   ```bash
   cp .env.example .env
   ```

4. Configure Keycard credentials in `.env`:
   ```bash
   KEYCARD_ZONE_ID=your_zone_id
   KEYCARD_CLIENT_ID=your_client_id
   KEYCARD_CLIENT_SECRET=your_client_secret
   MCP_SERVER_URL=http://localhost:8000
   PORT=8000
   ```

   Get these credentials from your Keycard dashboard:
   - Create a Zone at keycard.cloud
   - Add Linear as a credential provider
   - Register an application and copy the credentials

### Run Locally

```bash
uv run python -m src.server
```

Server starts at `http://localhost:8000/mcp`

### Testing

The server requires Keycard authentication. To test, use an MCP client configured with Keycard auth pointing to your server URL.

## Running Tests

```bash
uv run pytest
```

With coverage:
```bash
uv run pytest --cov=src --cov-report=term-missing
```

## Render Deployment

The server is deployed on Render at `https://svc-mcp-linear.onrender.com/mcp`.

### Configuration

Environment variables required on Render:
- `KEYCARD_ZONE_ID`
- `KEYCARD_CLIENT_ID`
- `KEYCARD_CLIENT_SECRET`
- `MCP_SERVER_URL` (set to your Render URL)
- `PORT` (Render provides this automatically)

### Deploy

1. Connect your repo to Render
2. Set the start command: `uv run python -m src.server`
3. Add environment variables in Render dashboard

### Manual Deploy

```bash
git push origin main  # Auto-deploys if connected to Render
```

## Error Handling

All tools return a consistent response structure:

**Success:**
```json
{
  "success": true,
  "issues": [...],
  "count": 5
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message describing what went wrong",
  "isError": true
}
```

Common errors:
- `No authentication context` - Keycard auth not configured
- `Authentication errors: [...]` - User not authenticated or token expired
- `Linear API returned HTTP 401` - Token invalid or revoked
- `Issue ENG-999 not found` - Issue doesn't exist or no access

## Project Structure

```
svc-mcp-linear/
├── src/
│   ├── __init__.py
│   ├── auth.py            # Keycard AuthProvider singleton
│   ├── server.py          # FastMCP entry point
│   ├── client.py          # Linear GraphQL client
│   └── tools/
│       ├── __init__.py
│       ├── issues.py      # my_issues, issue, search, list_projects, list_project_updates
│       ├── mutations.py   # create_issue, update_issue, update_status, create_project, create_project_update
│       └── states.py      # states
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_client.py
│   └── test_tools.py
├── pyproject.toml
├── .env.example
└── README.md
```

## License

Internal use only.
